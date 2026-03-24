from flask import jsonify, request

from auth import token_required, role_required
from models import db_connection
from cleaner_helpers import _to_float

from cleaner_blueprint import cleaner_bp

def get_reviews():
    """Get all reviews received from citizens"""
    try:
        user_id = request.current_user['id']
        
        # Get query parameters
        rating = request.args.get('rating', type=int)
        limit = request.args.get('limit', type=int, default=20)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query
        where_clause = "WHERE cr.cleaner_id = %s"
        params = [user_id]
        
        if rating:
            where_clause += " AND cr.rating = %s"
            params.append(rating)
        
        with db_connection.get_cursor() as cursor:
            # Get reviews
            cursor.execute(f"""
                SELECT 
                    cr.id, cr.rating, cr.comment, cr.created_at,
                    u.name as citizen_name,
                    r.id as report_id,
                    t.description as task_description
                FROM cleanup_reviews cr
                JOIN users u ON cr.citizen_id = u.id
                JOIN reports r ON cr.report_id = r.id
                JOIN tasks t ON r.id = t.report_id
                {where_clause}
                ORDER BY cr.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [limit, offset])
            reviews = cursor.fetchall()
            
            # Get summary
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(rating) as average_rating
                FROM cleanup_reviews
                WHERE cleaner_id = %s
            """, (user_id,))
            summary = cursor.fetchone()
        
        # Convert timestamps to ISO format
        for review in reviews:
            review['created_at'] = review['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'total': summary['total'],
            'average_rating': float(summary['average_rating']) if summary['average_rating'] else 0,
            'data': reviews
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cleaner_bp.route('/leaderboard', methods=['GET'])
@token_required
@role_required('CLEANER')
def get_leaderboard():
    """Get cleaner leaderboard rankings (live, period-aware)."""
    try:
        user_id = request.current_user['id']

        period = request.args.get('period', default='all_time')
        limit = request.args.get('limit', type=int, default=20)

        valid_periods = ['all_time', 'month', 'week']
        if period not in valid_periods:
            return jsonify({'success': False, 'error': f'Period must be one of: {", ".join(valid_periods)}'}), 400

        if limit < 1:
            limit = 20
        if limit > 100:
            limit = 100

        period_paid_filter = ""
        period_task_filter = ""
        if period == 'month':
            period_paid_filter = "AND COALESCE(et.paid_at, et.created_at) >= DATE_TRUNC('month', CURRENT_DATE)"
            period_task_filter = "AND t.completed_at >= DATE_TRUNC('month', CURRENT_DATE)"
        elif period == 'week':
            period_paid_filter = "AND COALESCE(et.paid_at, et.created_at) >= DATE_TRUNC('week', CURRENT_DATE)"
            period_task_filter = "AND t.completed_at >= DATE_TRUNC('week', CURRENT_DATE)"

        ranking_earnings_col = 'COALESCE(pb.period_earnings, 0)' if period != 'all_time' else 'COALESCE(pb.total_earnings, 0)'
        ranking_completed_col = 'COALESCE(cb.period_completed_tasks, 0)' if period != 'all_time' else 'COALESCE(cb.total_completed_tasks, 0)'

        with db_connection.get_cursor() as cursor:
            cursor.execute(f"""
                WITH paid_by_cleaner AS (
                    SELECT
                        et.cleaner_id AS user_id,
                        COALESCE(SUM(et.amount), 0) AS total_earnings,
                        COALESCE(SUM(CASE WHEN 1=1 {period_paid_filter} THEN et.amount ELSE 0 END), 0) AS period_earnings
                    FROM earnings_transactions et
                    WHERE et.status = 'PAID'
                    GROUP BY et.cleaner_id
                ),
                completed_by_cleaner AS (
                    SELECT
                        t.cleaner_id AS user_id,
                        COUNT(*) FILTER (WHERE t.status = 'COMPLETED') AS total_completed_tasks,
                        COUNT(*) FILTER (WHERE t.status = 'COMPLETED' {period_task_filter}) AS period_completed_tasks
                    FROM tasks t
                    GROUP BY t.cleaner_id
                ),
                ranked AS (
                    SELECT
                        u.id AS user_id,
                        u.name AS user_name,
                        u.avatar_url,
                        COALESCE(pb.total_earnings, 0) AS total_earnings,
                        COALESCE(pb.period_earnings, 0) AS period_earnings,
                        CASE WHEN %s = 'all_time'
                             THEN COALESCE(cb.total_completed_tasks, 0)
                             ELSE COALESCE(cb.period_completed_tasks, 0)
                        END AS completed_tasks,
                        COALESCE(cp.rating, 0) AS rating,
                        ROW_NUMBER() OVER (
                            ORDER BY {ranking_earnings_col} DESC,
                                     {ranking_completed_col} DESC,
                                     COALESCE(cp.rating, 0) DESC,
                                     u.created_at ASC
                        ) AS rank
                    FROM users u
                    JOIN cleaner_profiles cp ON cp.user_id = u.id
                    LEFT JOIN paid_by_cleaner pb ON pb.user_id = u.id
                    LEFT JOIN completed_by_cleaner cb ON cb.user_id = u.id
                    WHERE u.is_active = true
                )
                SELECT
                    rank,
                    user_id,
                    user_name,
                    avatar_url,
                    total_earnings,
                    period_earnings,
                    completed_tasks,
                    rating,
                    (user_id = %s) AS is_current_user
                FROM ranked
                ORDER BY rank
                LIMIT %s
            """, (period, user_id, limit))
            leaderboard = cursor.fetchall()

        my_rank = None
        for entry in leaderboard:
            entry['rank'] = int(entry['rank'])
            entry['total_earnings'] = _to_float(entry.get('total_earnings'))
            entry['period_earnings'] = _to_float(entry.get('period_earnings'))
            entry['completed_tasks'] = int(entry.get('completed_tasks') or 0)
            entry['rating'] = _to_float(entry.get('rating'))
            entry['is_current_user'] = bool(entry.get('is_current_user'))
            if entry['is_current_user']:
                my_rank = entry['rank']

        return jsonify({
            'success': True,
            'period': period,
            'my_rank': my_rank,
            'data': leaderboard
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cleaner_bp.route('/notifications', methods=['GET'])
@token_required
@role_required('CLEANER')
def get_notifications():
    """Get cleaner notifications"""
    try:
        user_id = request.current_user['id']
        
        # Get query parameters
        is_read = request.args.get('is_read')
        limit = request.args.get('limit', type=int, default=20)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query
        where_clause = "WHERE n.user_id = %s"
        params = [user_id]
        
        if is_read is not None:
            where_clause += " AND n.is_read = %s"
            params.append(is_read.lower() == 'true')
        
        with db_connection.get_cursor() as cursor:
            # Get notifications
            cursor.execute(f"""
                SELECT 
                    n.id, n.type, n.title, n.message, n.is_read, 
                    n.related_report_id, n.related_task_id, n.created_at
                FROM notifications n
                {where_clause}
                ORDER BY n.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [limit, offset])
            notifications = cursor.fetchall()
            
            # Get unread count
            cursor.execute("""
                SELECT COUNT(*) as unread_count
                FROM notifications
                WHERE user_id = %s AND is_read = false
            """, (user_id,))
            unread_result = cursor.fetchone()
            unread_count = unread_result['unread_count'] if unread_result else 0
        
        # Convert timestamps to ISO format
        for notification in notifications:
            notification['created_at'] = notification['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'unread_count': unread_count,
            'data': notifications
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


