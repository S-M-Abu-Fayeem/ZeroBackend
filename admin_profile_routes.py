from flask import jsonify, request
from datetime import datetime

from auth import token_required, role_required
from models import db_connection

from admin_blueprint import admin_bp

@admin_bp.route('/profile', methods=['GET'])
@token_required
@role_required('ADMIN')
def get_profile():
    """Get admin profile with user details"""
    try:
        user = request.current_user.copy()
        user.pop('password_hash', None)
        
        # Get admin profile
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM admin_profiles WHERE user_id = %s
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
        
        with db_connection.get_cursor(commit=True) as cursor:
            # Prepare update data for users table
            user_update = {}
            user_allowed_fields = ['name', 'phone', 'avatar_url', 'address', 'language', 
                                  'email_notifications', 'push_notifications', 'dark_mode']
            
            for field in user_allowed_fields:
                if field in data:
                    user_update[field] = data[field]
            
            # Update user if there are user fields
            if user_update:
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
            else:
                cursor.execute("""
                    SELECT id, email, name, phone, avatar_url, role, address, language,
                           email_notifications, push_notifications, dark_mode, is_active
                    FROM users WHERE id = %s
                """, (user_id,))
                updated_user = cursor.fetchone()
            
            # Prepare update data for admin_profiles table
            profile_update = {}
            profile_allowed_fields = ['role_title']
            
            for field in profile_allowed_fields:
                if field in data:
                    profile_update[field] = data[field]
            
            # Update admin profile if there are profile fields
            if profile_update:
                set_clause = ', '.join([f"{field} = %s" for field in profile_update.keys()])
                values = list(profile_update.values()) + [user_id]
                
                cursor.execute(f"""
                    UPDATE admin_profiles 
                    SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = %s
                """, values)
            
            # Get updated profile
            cursor.execute("""
                SELECT * FROM admin_profiles WHERE user_id = %s
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


@admin_bp.route('/change-password', methods=['POST'])
@token_required
@role_required('ADMIN')
def change_password():
    """Change admin password"""
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


@admin_bp.route('/download-data', methods=['GET'])
@token_required
@role_required('ADMIN')
def download_user_data():
    """Download admin account data"""
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
                SELECT * FROM admin_profiles WHERE user_id = %s
            """, (user_id,))
            profile_data = cursor.fetchone()

            cursor.execute("""
                SELECT audience, type, title, message, created_at
                FROM bulk_notifications
                WHERE sent_by = %s
                ORDER BY created_at DESC
            """, (user_id,))
            sent_notifications = cursor.fetchall()

            cursor.execute("""
                SELECT action, entity_type, entity_id, details, created_at
                FROM activity_logs
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT 500
            """, (user_id,))
            activity = cursor.fetchall()

        def convert_dates(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if hasattr(value, 'isoformat'):
                        obj[key] = value.isoformat()
            return obj

        user_export = {
            'user': convert_dates(dict(user_data)) if user_data else None,
            'profile': convert_dates(dict(profile_data)) if profile_data else None,
            'bulk_notifications': [convert_dates(dict(item)) for item in sent_notifications],
            'activity_logs': [convert_dates(dict(item)) for item in activity],
            'exported_at': datetime.now().isoformat(),
        }

        return jsonify({'success': True, 'data': user_export}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/delete-account', methods=['DELETE'])
@token_required
@role_required('ADMIN')
def delete_account():
    """Deactivate admin account"""
    try:
        user_id = request.current_user['id']

        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT COUNT(*) as active_admins
                FROM users
                WHERE role = 'ADMIN' AND is_active = true AND id != %s
            """, (user_id,))
            result = cursor.fetchone()

            if not result or result['active_admins'] < 1:
                return jsonify({
                    'success': False,
                    'error': 'Cannot delete the last active admin account.'
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
                VALUES (%s, 'ACCOUNT_DELETED', 'Admin requested account deletion')
            """, (user_id,))

        return jsonify({
            'success': True,
            'message': 'Account deletion initiated. Your account has been deactivated.'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/notification-settings', methods=['PUT'])
@token_required
@role_required('ADMIN')
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


