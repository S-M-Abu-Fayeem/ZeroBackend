from flask import jsonify, request

from auth import token_required, role_required
from models import db_connection

from admin_blueprint import admin_bp

@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required('ADMIN')
def get_all_users():
    """Get all users (admin only)"""
    try:
        # Get query parameters
        role = request.args.get('role')
        is_active = request.args.get('is_active')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', type=int, default=0)
        
        # Build query
        query = "SELECT id, email, name, phone, role, is_active, created_at, last_login_at FROM users WHERE 1=1"
        params = []
        
        if role:
            query += " AND role = %s"
            params.append(role)
        
        if is_active is not None:
            query += " AND is_active = %s"
            params.append(is_active.lower() == 'true')
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += f" LIMIT {limit} OFFSET {offset}"
        
        with db_connection.get_cursor() as cursor:
            cursor.execute(query, params if params else None)
            users = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM users WHERE 1=1"
        count_params = []
        if role:
            count_query += " AND role = %s"
            count_params.append(role)
        if is_active is not None:
            count_query += " AND is_active = %s"
            count_params.append(is_active.lower() == 'true')
        
        with db_connection.get_cursor() as cursor:
            cursor.execute(count_query, count_params if count_params else None)
            count_result = cursor.fetchone()
            total = count_result['total'] if count_result else 0
        
        return jsonify({
            'success': True,
            'total': total,
            'count': len(users),
            'data': users
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<user_id>', methods=['GET'])
@token_required
@role_required('ADMIN')
def get_user_details(user_id):
    """Get detailed user information (admin only)"""
    try:
        # Get user
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, email, name, phone, avatar_url, role, address, language,
                       email_notifications, push_notifications, dark_mode, is_active,
                       created_at, last_login_at
                FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Get role-specific profile
        profile = None
        with db_connection.get_cursor() as cursor:
            if user['role'] == 'CITIZEN':
                cursor.execute("""
                    SELECT cp.*, 
                           (SELECT COUNT(*) FROM user_badges WHERE user_id = cp.user_id) as badges_count,
                           (SELECT COUNT(*) FROM reports WHERE user_id = cp.user_id) as total_reports_count
                    FROM citizen_profiles cp
                    WHERE cp.user_id = %s
                """, (user_id,))
                profile = cursor.fetchone()
            elif user['role'] == 'CLEANER':
                cursor.execute("""
                    SELECT cp.*,
                           (SELECT COUNT(*) FROM cleanup_reviews WHERE cleaner_id = cp.user_id) as total_reviews,
                           (SELECT COUNT(*) FROM tasks WHERE cleaner_id = cp.user_id) as total_tasks_count
                    FROM cleaner_profiles cp
                    WHERE cp.user_id = %s
                """, (user_id,))
                profile = cursor.fetchone()
            elif user['role'] == 'ADMIN':
                cursor.execute("""
                    SELECT * FROM admin_profiles WHERE user_id = %s
                """, (user_id,))
                profile = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'profile': profile
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/stats', methods=['GET'])
@token_required
@role_required('ADMIN')
def get_system_stats():
    """Get system-wide statistics (admin only)"""
    try:
        # Get comprehensive system stats
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM users WHERE role = 'CITIZEN') as total_citizens,
                    (SELECT COUNT(*) FROM users WHERE role = 'CLEANER') as total_cleaners,
                    (SELECT COUNT(*) FROM users WHERE role = 'ADMIN') as total_admins,
                    (SELECT COUNT(*) FROM reports) as total_reports,
                    (SELECT COUNT(*) FROM reports WHERE status = 'SUBMITTED') as pending_reports,
                    (SELECT COUNT(*) FROM reports WHERE status = 'COMPLETED') as completed_reports,
                    (SELECT COUNT(*) FROM tasks) as total_tasks,
                    (SELECT COUNT(*) FROM tasks WHERE status = 'APPROVED' AND cleaner_id IS NULL) as available_tasks,
                    (SELECT COUNT(*) FROM zones) as total_zones,
                    (SELECT AVG(cleanliness_score) FROM zones) as avg_zone_cleanliness,
                    (SELECT COUNT(*) FROM alerts WHERE status = 'OPEN') as open_alerts
            """)
            stats = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'data': stats if stats else None
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



