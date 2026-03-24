from flask import jsonify, request
from datetime import datetime

from auth import token_required, role_required
from models import db_connection

from cleaner_blueprint import cleaner_bp

@cleaner_bp.route('/profile', methods=['GET'])
@token_required
@role_required('CLEANER')
def get_profile():
    """Get cleaner profile with user details"""
    try:
        user = request.current_user.copy()
        user.pop('password_hash', None)
        
        # Get cleaner profile with comprehensive data
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT cp.*,
                       (SELECT COUNT(*) FROM cleanup_reviews WHERE cleaner_id = cp.user_id) as total_reviews
                FROM cleaner_profiles cp
                WHERE cp.user_id = %s
            """, (user['id'],))
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
        with db_connection.get_cursor(commit=True) as cursor:
            # Build dynamic update query
            set_clause = ', '.join([f"{field} = %s" for field in user_update.keys()])
            values = list(user_update.values()) + [user_id]
            
            cursor.execute(f"""
                UPDATE users 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                RETURNING id, email, name, phone, avatar_url, role, address, language,
                         email_notifications, push_notifications, dark_mode, is_active
            """, values)
            updated_user = cursor.fetchone()
            
            # Get updated profile
            cursor.execute("""
                SELECT cp.*,
                       (SELECT COUNT(*) FROM cleanup_reviews WHERE cleaner_id = cp.user_id) as total_reviews
                FROM cleaner_profiles cp
                WHERE cp.user_id = %s
            """, (user_id,))
            profile = cursor.fetchone()
        
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
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
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
            """, (user_id, user_id, user_id, user_id, user_id, user_id))
            stats = cursor.fetchone()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cleaner_bp.route('/change-password', methods=['POST'])
@token_required
@role_required('CLEANER')
def change_password():
    """Change cleaner password"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        user_id = request.current_user['id']

        if not data.get('currentPassword') or not data.get('newPassword'):
            return jsonify({'success': False, 'error': 'Current password and new password are required'}), 400

        import bcrypt

        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT password_hash FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()

            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404

            if not bcrypt.checkpw(data['currentPassword'].encode('utf-8'), user['password_hash'].encode('utf-8')):
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400

            new_password_hash = bcrypt.hashpw(data['newPassword'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            cursor.execute("""
                UPDATE users
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_password_hash, user_id))

        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cleaner_bp.route('/download-data', methods=['GET'])
@token_required
@role_required('CLEANER')
def download_user_data():
    """Download cleaner account data"""
    try:
        user_id = request.current_user['id']

        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, email, name, phone, address, avatar_url, language,
                       email_notifications, push_notifications, created_at, last_login_at
                FROM users WHERE id = %s
            """, (user_id,))
            user_data = cursor.fetchone()

            cursor.execute("""
                SELECT * FROM cleaner_profiles WHERE user_id = %s
            """, (user_id,))
            profile_data = cursor.fetchone()

            cursor.execute("""
                SELECT t.id, t.status, t.priority, t.reward, t.due_date, t.taken_at, t.completed_at,
                       z.name as zone_name, t.description
                FROM tasks t
                LEFT JOIN zones z ON z.id = t.zone_id
                WHERE t.cleaner_id = %s
                ORDER BY t.created_at DESC
            """, (user_id,))
            tasks_data = cursor.fetchall()

            cursor.execute("""
                SELECT amount, status, created_at, paid_at
                FROM earnings_transactions
                WHERE cleaner_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            earnings_data = cursor.fetchall()

            cursor.execute("""
                SELECT rating, comment, reviewed_at, report_id
                FROM cleanup_reviews
                WHERE cleaner_id = %s
                ORDER BY reviewed_at DESC
            """, (user_id,))
            reviews_data = cursor.fetchall()

        def convert_dates(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if hasattr(value, 'isoformat'):
                        obj[key] = value.isoformat()
            return obj

        user_export = {
            'user': convert_dates(dict(user_data)) if user_data else None,
            'profile': convert_dates(dict(profile_data)) if profile_data else None,
            'tasks': [convert_dates(dict(item)) for item in tasks_data],
            'earnings': [convert_dates(dict(item)) for item in earnings_data],
            'reviews': [convert_dates(dict(item)) for item in reviews_data],
            'exported_at': datetime.now().isoformat(),
        }

        return jsonify({'success': True, 'data': user_export}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cleaner_bp.route('/delete-account', methods=['DELETE'])
@token_required
@role_required('CLEANER')
def delete_account():
    """Deactivate cleaner account"""
    try:
        user_id = request.current_user['id']

        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as active_count
                FROM tasks
                WHERE cleaner_id = %s AND status = 'IN_PROGRESS'
            """, (user_id,))
            active_tasks = cursor.fetchone()

            if active_tasks and active_tasks['active_count'] > 0:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete account while tasks are in progress. Complete or release tasks first.'
                }), 400

            cursor.execute("""
                UPDATE users
                SET is_active = false,
                    email = CONCAT('deleted_', id, '@deleted.local'),
                    name = 'Deleted User',
                    phone = NULL,
                    address = NULL,
                    avatar_url = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))

            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details)
                VALUES (%s, 'ACCOUNT_DELETED', 'Cleaner requested account deletion')
            """, (user_id,))

        return jsonify({
            'success': True,
            'message': 'Account deletion initiated. Your account has been deactivated.'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@cleaner_bp.route('/notification-settings', methods=['PUT'])
@token_required
@role_required('CLEANER')
def update_notification_settings():
    """Update notification preferences (which notifications to show in UI)"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        user_id = request.current_user['id']
        
        # Get existing preferences
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT notify_report_updates, notify_news_updates
                FROM users
                WHERE id = %s
            """, (user_id,))
            existing = cursor.fetchone()

        if not existing:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Map frontend fields to notification preference columns
        notify_report_updates = data.get('reportUpdates', existing.get('notify_report_updates', True))
        notify_news_updates = data.get('promotions', existing.get('notify_news_updates', False))
        
        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                UPDATE users 
                SET notify_report_updates = %s, notify_news_updates = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (notify_report_updates, notify_news_updates, user_id))
        
        return jsonify({
            'success': True,
            'message': 'Notification preferences updated successfully',
            'data': {
                'reportUpdates': notify_report_updates,
                'promotions': notify_news_updates
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



