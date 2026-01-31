from flask import Blueprint, jsonify, request
from auth import token_required, role_required
from models import users_model, cleaner_profiles_model

cleaner_bp = Blueprint('cleaner', __name__)


@cleaner_bp.route('/profile', methods=['GET'])
@token_required
@role_required('CLEANER')
def get_profile():
    """Get cleaner profile with user details"""
    try:
        user = request.current_user.copy()
        user.pop('password_hash', None)
        
        # Get cleaner profile
        profiles = cleaner_profiles_model.execute_raw(
            """
            SELECT cp.*,
                   (SELECT COUNT(*) FROM cleanup_reviews WHERE cleaner_id = cp.user_id) as total_reviews
            FROM cleaner_profiles cp
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


@cleaner_bp.route('/profile', methods=['PUT'])
@token_required
@role_required('CLEANER')
def update_profile():
    """Update cleaner user details (name, phone, avatar, settings)"""
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
        profiles = cleaner_profiles_model.execute_raw(
            """
            SELECT cp.*,
                   (SELECT COUNT(*) FROM cleanup_reviews WHERE cleaner_id = cp.user_id) as total_reviews
            FROM cleaner_profiles cp
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


@cleaner_bp.route('/stats', methods=['GET'])
@token_required
@role_required('CLEANER')
def get_stats():
    """Get cleaner statistics"""
    try:
        user_id = request.current_user['id']
        
        # Get comprehensive stats
        stats = cleaner_profiles_model.execute_raw(
            """
            SELECT 
                cp.*,
                (SELECT COUNT(*) FROM tasks WHERE cleaner_id = %s AND status = 'IN_PROGRESS') as active_tasks,
                (SELECT COUNT(*) FROM cleanup_reviews WHERE cleaner_id = %s) as total_reviews,
                (SELECT AVG(rating) FROM cleanup_reviews WHERE cleaner_id = %s) as average_review_rating,
                (SELECT SUM(amount) FROM earnings_transactions 
                 WHERE cleaner_id = %s AND status = 'PENDING') as pending_amount,
                (SELECT SUM(amount) FROM earnings_transactions 
                 WHERE cleaner_id = %s AND status = 'PAID') as paid_amount
            FROM cleaner_profiles cp
            WHERE cp.user_id = %s
            """,
            [user_id, user_id, user_id, user_id, user_id, user_id]
        )
        
        return jsonify({
            'success': True,
            'data': stats[0] if stats else None
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
