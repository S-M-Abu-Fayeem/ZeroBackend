from flask import jsonify, request

from auth import token_required, role_required
from models import db_connection

from citizen_blueprint import citizen_bp

@citizen_bp.route('/badges', methods=['GET'])
@token_required
@role_required('CITIZEN')
def get_my_badges():
    """Get all badges earned by the citizen"""
    try:
        user_id = request.current_user['id']
        
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    b.id, b.name, b.description, b.icon,
                    ub.earned_at
                FROM user_badges ub
                JOIN badges b ON ub.badge_id = b.id
                WHERE ub.user_id = %s
                ORDER BY ub.earned_at DESC
            """, (user_id,))
            badges = cursor.fetchall()
        
        # Convert earned_at to ISO format
        for badge in badges:
            badge['earned_at'] = badge['earned_at'].isoformat()
        
        return jsonify({
            'success': True,
            'data': badges
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@citizen_bp.route('/points', methods=['GET'])
@token_required
@role_required('CITIZEN')
def get_points_history():
    """Get green points transaction history"""
    try:
        user_id = request.current_user['id']
        
        # Get query parameters
        limit = request.args.get('limit', type=int, default=20)
        offset = request.args.get('offset', type=int, default=0)
        
        with db_connection.get_cursor() as cursor:
            # Get transactions
            cursor.execute("""
                SELECT 
                    gpt.id, gpt.green_points, gpt.reason, gpt.created_at,
                    gpt.report_id
                FROM green_points_transactions gpt
                WHERE gpt.user_id = %s
                ORDER BY gpt.created_at DESC
                LIMIT %s OFFSET %s
            """, (user_id, limit, offset))
            transactions = cursor.fetchall()
            
            # Get total count and current balance
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    (SELECT green_points_balance FROM citizen_profiles WHERE user_id = %s) as current_balance
                FROM green_points_transactions
                WHERE user_id = %s
            """, (user_id, user_id))
            summary = cursor.fetchone()
        
        # Convert timestamps to ISO format
        for transaction in transactions:
            transaction['created_at'] = transaction['created_at'].isoformat()
        
        return jsonify({
            'success': True,
            'total': summary['total'],
            'current_balance': summary['current_balance'],
            'data': transactions
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@citizen_bp.route('/leaderboard', methods=['GET'])
@token_required
@role_required('CITIZEN')
def get_leaderboard():
    """Get citizen leaderboard rankings"""
    try:
        user_id = request.current_user['id']
        
        # Get query parameters
        period = request.args.get('period', default='all_time')
        limit = request.args.get('limit', type=int, default=10)

        valid_periods = ['all_time', 'month', 'week']
        if period not in valid_periods:
            return jsonify({'success': False, 'error': f'Period must be one of: {", ".join(valid_periods)}'}), 400

        if limit < 1:
            limit = 10
        if limit > 100:
            limit = 100

        date_filter_sql = ""
        if period == 'month':
            date_filter_sql = "AND gpt.created_at >= DATE_TRUNC('month', CURRENT_DATE)"
        elif period == 'week':
            date_filter_sql = "AND gpt.created_at >= DATE_TRUNC('week', CURRENT_DATE)"
        
        with db_connection.get_cursor() as cursor:
            # Build a live, period-aware leaderboard from points transactions and report stats.
            cursor.execute(f"""
                WITH points_by_user AS (
                    SELECT gpt.user_id, COALESCE(SUM(gpt.green_points), 0) AS total_green_points
                    FROM green_points_transactions gpt
                    WHERE 1=1 {date_filter_sql}
                    GROUP BY gpt.user_id
                ),
                approved_by_user AS (
                    SELECT r.user_id,
                           COUNT(*) FILTER (WHERE r.status IN ('APPROVED', 'COMPLETED')) AS approved_reports
                    FROM reports r
                    GROUP BY r.user_id
                ),
                badges_by_user AS (
                    SELECT ub.user_id, COUNT(*) AS badges_count
                    FROM user_badges ub
                    GROUP BY ub.user_id
                ),
                ranked AS (
                    SELECT
                        u.id AS user_id,
                        u.name AS user_name,
                        u.avatar_url,
                        COALESCE(p.total_green_points, 0) AS total_green_points,
                        COALESCE(a.approved_reports, 0) AS approved_reports,
                        COALESCE(b.badges_count, 0) AS badges_count,
                        ROW_NUMBER() OVER (
                            ORDER BY COALESCE(p.total_green_points, 0) DESC,
                                     COALESCE(a.approved_reports, 0) DESC,
                                     u.created_at ASC
                        ) AS rank
                    FROM users u
                    JOIN citizen_profiles cp ON cp.user_id = u.id
                    LEFT JOIN points_by_user p ON p.user_id = u.id
                    LEFT JOIN approved_by_user a ON a.user_id = u.id
                    LEFT JOIN badges_by_user b ON b.user_id = u.id
                    WHERE u.is_active = true
                )
                SELECT rank, user_id, user_name, avatar_url, total_green_points, approved_reports, badges_count
                FROM ranked
                ORDER BY rank
                LIMIT %s
            """, (limit,))
            leaderboard = cursor.fetchall()
            
            # Get current user's rank
            cursor.execute(f"""
                WITH points_by_user AS (
                    SELECT gpt.user_id, COALESCE(SUM(gpt.green_points), 0) AS total_green_points
                    FROM green_points_transactions gpt
                    WHERE 1=1 {date_filter_sql}
                    GROUP BY gpt.user_id
                ),
                approved_by_user AS (
                    SELECT r.user_id,
                           COUNT(*) FILTER (WHERE r.status IN ('APPROVED', 'COMPLETED')) AS approved_reports
                    FROM reports r
                    GROUP BY r.user_id
                ),
                ranked AS (
                    SELECT
                        u.id AS user_id,
                        ROW_NUMBER() OVER (
                            ORDER BY COALESCE(p.total_green_points, 0) DESC,
                                     COALESCE(a.approved_reports, 0) DESC,
                                     u.created_at ASC
                        ) AS rank
                    FROM users u
                    JOIN citizen_profiles cp ON cp.user_id = u.id
                    LEFT JOIN points_by_user p ON p.user_id = u.id
                    LEFT JOIN approved_by_user a ON a.user_id = u.id
                    WHERE u.is_active = true
                )
                SELECT rank FROM ranked WHERE user_id = %s
            """, (user_id,))
            my_rank_result = cursor.fetchone()
            my_rank = my_rank_result['rank'] if my_rank_result else None
        
        return jsonify({
            'success': True,
            'period': period,
            'my_rank': my_rank,
            'data': leaderboard
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


