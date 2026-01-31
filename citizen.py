from flask import Blueprint, jsonify, request
from auth import token_required, role_required
from models import users_model, citizen_profiles_model

citizen_bp = Blueprint('citizen', __name__)


@citizen_bp.route('/profile', methods=['GET'])
@token_required
@role_required('CITIZEN')
def get_profile():
    """Get citizen profile with user details"""
    try:
        user = request.current_user.copy()
        user.pop('password_hash', None)
        
        # Get citizen profile
        profiles = citizen_profiles_model.execute_raw(
            """
            SELECT cp.*, 
                   (SELECT COUNT(*) FROM user_badges WHERE user_id = cp.user_id) as badges_count
            FROM citizen_profiles cp
            WHERE cp.user_id = %s
            """,
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


@citizen_bp.route('/profile', methods=['PUT'])
@token_required
@role_required('CITIZEN')
def update_profile():
    """Update citizen user details (name, phone, avatar, settings)"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        user_id = request.current_user['id']
        
        # Prepare update data for users table
        user_update = {}
        allowed_fields = ['name', 'phone', 'avatar_url', 'address', 'language', 
                         'email_notifications', 'push_notifications', 'dark_mode']
        
        for field in allowed_fields:
            if field in data:
                user_update[field] = data[field]
        
        if not user_update:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400
        
        # Update user
        updated_user = users_model.update(user_update, {'id': user_id})
        updated_user.pop('password_hash', None)
        
        # Get updated profile
        profiles = citizen_profiles_model.execute_raw(
            """
            SELECT cp.*, 
                   (SELECT COUNT(*) FROM user_badges WHERE user_id = cp.user_id) as badges_count
            FROM citizen_profiles cp
            WHERE cp.user_id = %s
            """,
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


@citizen_bp.route('/stats', methods=['GET'])
@token_required
@role_required('CITIZEN')
def get_stats():
    """Get citizen statistics"""
    try:
        user_id = request.current_user['id']
        
        # Get comprehensive stats
        stats = citizen_profiles_model.execute_raw(
            """
            SELECT 
                cp.*,
                (SELECT COUNT(*) FROM reports WHERE user_id = %s AND status = 'SUBMITTED') as pending_reports,
                (SELECT COUNT(*) FROM reports WHERE user_id = %s AND status = 'COMPLETED') as completed_reports,
                (SELECT COUNT(*) FROM user_badges WHERE user_id = %s) as total_badges,
                (SELECT COUNT(*) FROM cleanup_reviews WHERE citizen_id = %s) as reviews_given
            FROM citizen_profiles cp
            WHERE cp.user_id = %s
            """,
            [user_id, user_id, user_id, user_id, user_id]
        )
        
        return jsonify({
            'success': True,
            'data': stats[0] if stats else None
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
