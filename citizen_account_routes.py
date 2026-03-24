from flask import jsonify, request
from datetime import datetime

from auth import token_required, role_required
from models import db_connection

from citizen_blueprint import citizen_bp

@citizen_bp.route('/change-password', methods=['POST'])
@token_required
@role_required('CITIZEN')
def change_password():
    """Change user password"""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        user_id = request.current_user['id']
        
        # Validate required fields
        if not data.get('currentPassword') or not data.get('newPassword'):
            return jsonify({'success': False, 'error': 'Current password and new password are required'}), 400
        
        import bcrypt
        
        with db_connection.get_cursor(commit=True) as cursor:
            # Get current password hash
            cursor.execute("""
                SELECT password_hash FROM users WHERE id = %s
            """, (user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            
            # Verify current password
            if not bcrypt.checkpw(data['currentPassword'].encode('utf-8'), user['password_hash'].encode('utf-8')):
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
            
            # Hash new password
            new_password_hash = bcrypt.hashpw(data['newPassword'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Update password
            cursor.execute("""
                UPDATE users 
                SET password_hash = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (new_password_hash, user_id))
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@citizen_bp.route('/download-data', methods=['GET'])
@token_required
@role_required('CITIZEN')
def download_user_data():
    """Download all user data (GDPR compliance)"""
    try:
        user_id = request.current_user['id']
        
        with db_connection.get_cursor() as cursor:
            # Get user data
            cursor.execute("""
                SELECT id, email, name, phone, address, avatar_url, language,
                       email_notifications, push_notifications, created_at, last_login_at
                FROM users WHERE id = %s
            """, (user_id,))
            user_data = cursor.fetchone()
            
            # Get citizen profile
            cursor.execute("""
                SELECT * FROM citizen_profiles WHERE user_id = %s
            """, (user_id,))
            profile_data = cursor.fetchone()
            
            # Get reports
            cursor.execute("""
                SELECT r.*, z.name as zone_name
                FROM reports r
                LEFT JOIN zones z ON r.zone_id = z.id
                WHERE r.user_id = %s
                ORDER BY r.created_at DESC
            """, (user_id,))
            reports_data = cursor.fetchall()
            
            # Get badges
            cursor.execute("""
                SELECT b.name, b.description, ub.earned_at
                FROM user_badges ub
                JOIN badges b ON ub.badge_id = b.id
                WHERE ub.user_id = %s
            """, (user_id,))
            badges_data = cursor.fetchall()
            
            # Get points history
            cursor.execute("""
                SELECT green_points, reason, created_at
                FROM green_points_transactions
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            points_data = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        def convert_dates(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if hasattr(value, 'isoformat'):
                        obj[key] = value.isoformat()
            return obj
        
        user_export = {
            'user': convert_dates(dict(user_data)) if user_data else None,
            'profile': convert_dates(dict(profile_data)) if profile_data else None,
            'reports': [convert_dates(dict(report)) for report in reports_data],
            'badges': [convert_dates(dict(badge)) for badge in badges_data],
            'points_history': [convert_dates(dict(point)) for point in points_data],
            'exported_at': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': user_export
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@citizen_bp.route('/delete-account', methods=['DELETE'])
@token_required
@role_required('CITIZEN')
def delete_account():
    """Delete user account (GDPR compliance)"""
    try:
        user_id = request.current_user['id']
        
        with db_connection.get_cursor(commit=True) as cursor:
            # Check if user has any active reports or tasks
            cursor.execute("""
                SELECT COUNT(*) as active_count
                FROM reports 
                WHERE user_id = %s AND status IN ('SUBMITTED', 'APPROVED', 'IN_PROGRESS')
            """, (user_id,))
            active_reports = cursor.fetchone()
            
            if active_reports and active_reports['active_count'] > 0:
                return jsonify({
                    'success': False, 
                    'error': 'Cannot delete account with active reports. Please wait for them to be completed.'
                }), 400
            
            # Soft delete - deactivate account instead of hard delete to maintain data integrity
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
            
            # Create deletion log
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, details)
                VALUES (%s, 'ACCOUNT_DELETED', 'User requested account deletion')
            """, (user_id,))
        
        return jsonify({
            'success': True,
            'message': 'Account deletion initiated. Your account has been deactivated.'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


