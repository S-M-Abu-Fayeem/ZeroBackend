from flask import Blueprint, jsonify, request
from auth import token_required, role_required
from models import users_model, admin_profiles_model

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/profile', methods=['GET'])
@token_required
@role_required('ADMIN')
def get_profile():
    """Get admin profile with user details"""
    try:
        user = request.current_user.copy()
        user.pop('password_hash', None)
        
        # Get admin profile
        profiles = admin_profiles_model.execute_raw(
            "SELECT * FROM admin_profiles WHERE user_id = %s",
            [user['id']]
        )
        
        profile = profiles[0] if profiles else None
        
        return jsonify({
            'success': True,
            'data': {
                'user': user,
                'profile': profile
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/profile', methods=['PUT'])
@token_required
@role_required('ADMIN')
def update_profile():
    """Update admin user details and profile"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        user_id = request.current_user['id']
        
        # Prepare update data for users table
        user_update = {}
        user_allowed_fields = ['name', 'phone', 'avatar_url', 'address', 'language', 
                              'email_notifications', 'push_notifications', 'dark_mode']
        
        for field in user_allowed_fields:
            if field in data:
                user_update[field] = data[field]
        
        # Update user if there are user fields
        if user_update:
            updated_user = users_model.update(user_update, {'id': user_id})
            updated_user.pop('password_hash', None)
        else:
            user = request.current_user.copy()
            user.pop('password_hash', None)
            updated_user = user
        
        # Prepare update data for admin_profiles table
        profile_update = {}
        profile_allowed_fields = ['department', 'role_title']
        
        for field in profile_allowed_fields:
            if field in data:
                profile_update[field] = data[field]
        
        # Update admin profile if there are profile fields
        if profile_update:
            # Get profile id first
            profiles = admin_profiles_model.execute_raw(
                "SELECT id FROM admin_profiles WHERE user_id = %s",
                [user_id]
            )
            
            if profiles:
                admin_profiles_model.update(profile_update, {'user_id': user_id})
        
        # Get updated profile
        profiles = admin_profiles_model.execute_raw(
            "SELECT * FROM admin_profiles WHERE user_id = %s",
            [user_id]
        )
        
        profile = profiles[0] if profiles else None
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'user': updated_user,
                'profile': profile
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
        
        users = users_model.execute_raw(query, params if params else None)
        
        # Get total count
        count_query = "SELECT COUNT(*) as total FROM users WHERE 1=1"
        if role:
            count_query += " AND role = %s"
        if is_active is not None:
            count_query += " AND is_active = %s"
        
        count_result = users_model.execute_raw(count_query, params if params else None)
        total = count_result[0]['total'] if count_result else 0
        
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
        user = users_model.find_by_id(user_id)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.pop('password_hash', None)
        
        # Get role-specific profile
        profile = None
        if user['role'] == 'CITIZEN':
            profiles = users_model.execute_raw(
                """
                SELECT cp.*, 
                       (SELECT COUNT(*) FROM user_badges WHERE user_id = cp.user_id) as badges_count,
                       (SELECT COUNT(*) FROM reports WHERE user_id = cp.user_id) as total_reports_count
                FROM citizen_profiles cp
                WHERE cp.user_id = %s
                """,
                [user_id]
            )
            profile = profiles[0] if profiles else None
        elif user['role'] == 'CLEANER':
            profiles = users_model.execute_raw(
                """
                SELECT cp.*,
                       (SELECT COUNT(*) FROM cleanup_reviews WHERE cleaner_id = cp.user_id) as total_reviews,
                       (SELECT COUNT(*) FROM tasks WHERE cleaner_id = cp.user_id) as total_tasks_count
                FROM cleaner_profiles cp
                WHERE cp.user_id = %s
                """,
                [user_id]
            )
            profile = profiles[0] if profiles else None
        elif user['role'] == 'ADMIN':
            profiles = admin_profiles_model.execute_raw(
                "SELECT * FROM admin_profiles WHERE user_id = %s",
                [user_id]
            )
            profile = profiles[0] if profiles else None
        
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
        stats = users_model.execute_raw("""
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
        
        return jsonify({
            'success': True,
            'data': stats[0] if stats else None
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
