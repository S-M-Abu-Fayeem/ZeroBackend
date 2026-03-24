from flask import Blueprint, jsonify, request
from datetime import datetime
from models import db_connection
from auth import token_required, superadmin_required
import json
import bcrypt
import os

superadmin_bp = Blueprint('superadmin', __name__)


def _parse_json_details(raw_details):
    """Parse JSON details from activity logs."""
    if isinstance(raw_details, dict):
        return raw_details
    if isinstance(raw_details, str):
        try:
            return json.loads(raw_details)
        except Exception:
            return {}
    return {}


def ensure_default_superadmin():
    """Ensure a default superadmin account exists for emergency control access."""
    email = os.getenv('SUPERADMIN_EMAIL', 'superadmin@zero.local').strip().lower()
    password = os.getenv('SUPERADMIN_PASSWORD', '').strip()
    name = os.getenv('SUPERADMIN_NAME', 'Super Admin').strip()
    should_reset_password = os.getenv('SUPERADMIN_RESET_PASSWORD', 'false').lower() == 'true'

    if not password:
        raise RuntimeError('Missing required SUPERADMIN_PASSWORD environment variable. Set it in ZeroBackend/.env')

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    with db_connection.get_cursor(commit=True) as cursor:
        cursor.execute("""
            SELECT id, password_hash
            FROM users
            WHERE LOWER(email) = LOWER(%s)
            LIMIT 1
        """, (email,))
        existing = cursor.fetchone()

        if existing:
            if should_reset_password:
                cursor.execute("""
                    UPDATE users
                    SET password_hash = %s,
                        role = 'ADMIN',
                        is_superadmin = true,
                        is_active = true,
                        name = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (password_hash, name, existing['id']))
            else:
                cursor.execute("""
                    UPDATE users
                    SET role = 'ADMIN',
                        is_superadmin = true,
                        is_active = true,
                        name = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """, (name, existing['id']))
            user_id = existing['id']
        else:
            cursor.execute("""
                INSERT INTO users (email, password_hash, name, role, is_active, is_superadmin)
                VALUES (%s, %s, %s, 'ADMIN', true, true)
                RETURNING id
            """, (email, password_hash, name))
            user_id = cursor.fetchone()['id']

        cursor.execute("""
            INSERT INTO admin_profiles (user_id, role_title)
            VALUES (%s, 'Super Administrator')
            ON CONFLICT (user_id) DO NOTHING
        """, (user_id,))


@superadmin_bp.route('/superadmin/dashboard', methods=['GET'])
@token_required
@superadmin_required
def superadmin_dashboard():
    """Return high-level superadmin dashboard metrics."""
    try:
        with db_connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM users WHERE role = 'CITIZEN') AS total_citizens,
                    (SELECT COUNT(*) FROM users WHERE role = 'CLEANER') AS total_cleaners,
                    (SELECT COUNT(*) FROM users WHERE role = 'ADMIN' AND COALESCE(is_superadmin, false) = false) AS total_admins,
                    (SELECT COUNT(*) FROM users WHERE COALESCE(is_superadmin, false) = true) AS total_superadmins,
                    (SELECT COUNT(*) FROM users WHERE is_active = false) AS blocked_or_inactive_users,
                    (SELECT COUNT(*) FROM activity_logs WHERE created_at >= NOW() - INTERVAL '24 hours') AS actions_last_24h
            """)
            stats = cursor.fetchone()

        return jsonify({'success': True, 'data': stats}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@superadmin_bp.route('/superadmin/users', methods=['GET'])
@token_required
@superadmin_required
def superadmin_get_users():
    """List users with moderation-ready fields for superadmin."""
    try:
        role = request.args.get('role')
        is_active = request.args.get('is_active')
        search = request.args.get('search')
        limit = request.args.get('limit', type=int, default=50)
        offset = request.args.get('offset', type=int, default=0)

        limit = max(1, min(limit, 200))
        offset = max(0, offset)

        where = ["id != '00000000-0000-0000-0000-000000000000'"]
        params = []

        if role:
            where.append("role = %s")
            params.append(role)
        if is_active is not None:
            where.append("is_active = %s")
            params.append(is_active.lower() == 'true')
        if search:
            where.append("(name ILIKE %s OR email ILIKE %s)")
            search_like = f"%{search}%"
            params.extend([search_like, search_like])

        where_clause = " AND ".join(where)

        with db_connection.get_cursor() as cursor:
            cursor.execute(f"""
                SELECT id, email, name, phone, role, is_active, COALESCE(is_superadmin, false) AS is_superadmin,
                       created_at, last_login_at
                FROM users
                WHERE {where_clause}
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """, params + [limit, offset])
            users = cursor.fetchall()

            cursor.execute(f"""
                SELECT COUNT(*) AS total
                FROM users
                WHERE {where_clause}
            """, params)
            total = cursor.fetchone()['total']

        return jsonify({'success': True, 'total': total, 'count': len(users), 'data': users}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@superadmin_bp.route('/superadmin/activity-logs', methods=['GET'])
@token_required
@superadmin_required
def superadmin_get_activity_logs():
    """Get audit logs across all user roles."""
    try:
        user_id = request.args.get('user_id')
        action = request.args.get('action')
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)

        limit = max(1, min(limit, 300))
        offset = max(0, offset)

        where = ["1=1"]
        params = []
        if user_id:
            where.append("al.user_id = %s")
            params.append(user_id)
        if action:
            where.append("al.action = %s")
            params.append(action)

        where_clause = " AND ".join(where)

        with db_connection.get_cursor() as cursor:
            cursor.execute(f"""
                SELECT al.id, al.user_id, u.name AS user_name, u.role AS user_role,
                       al.action, al.entity_type, al.entity_id, al.details, al.created_at
                FROM activity_logs al
                LEFT JOIN users u ON u.id = al.user_id
                WHERE {where_clause}
                ORDER BY al.created_at DESC
                LIMIT %s OFFSET %s
            """, params + [limit, offset])
            logs = cursor.fetchall()

        return jsonify({'success': True, 'count': len(logs), 'data': logs}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@superadmin_bp.route('/superadmin/users/<user_id>/block', methods=['POST'])
@token_required
@superadmin_required
def superadmin_block_user(user_id):
    """Block a user account (sets is_active=false)."""
    try:
        actor_id = request.current_user['id']
        if user_id == actor_id:
            return jsonify({'success': False, 'error': 'You cannot block your own account'}), 400

        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT id, name, role, is_active, COALESCE(is_superadmin, false) AS is_superadmin
                FROM users
                WHERE id = %s
            """, (user_id,))
            target = cursor.fetchone()
            if not target:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            if target['is_superadmin']:
                return jsonify({'success': False, 'error': 'Cannot block another superadmin'}), 403

            cursor.execute("""
                UPDATE users
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))

            details = {
                'previous_is_active': bool(target.get('is_active')),
                'target_name': target.get('name'),
                'target_role': target.get('role'),
                'reverted': False,
            }
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details)
                VALUES (%s, 'SUPERADMIN_BLOCK_USER', 'USER', %s, %s::jsonb)
            """, (actor_id, user_id, json.dumps(details)))

        return jsonify({'success': True, 'message': 'User blocked successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@superadmin_bp.route('/superadmin/users/<user_id>/unblock', methods=['POST'])
@token_required
@superadmin_required
def superadmin_unblock_user(user_id):
    """Unblock a user account (sets is_active=true)."""
    try:
        actor_id = request.current_user['id']

        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT id, name, role, is_active, COALESCE(is_superadmin, false) AS is_superadmin
                FROM users
                WHERE id = %s
            """, (user_id,))
            target = cursor.fetchone()
            if not target:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            if target['is_superadmin'] and user_id != actor_id:
                return jsonify({'success': False, 'error': 'Cannot modify another superadmin'}), 403

            cursor.execute("""
                UPDATE users
                SET is_active = true, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (user_id,))

            details = {
                'previous_is_active': bool(target.get('is_active')),
                'target_name': target.get('name'),
                'target_role': target.get('role'),
                'reverted': False,
            }
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details)
                VALUES (%s, 'SUPERADMIN_UNBLOCK_USER', 'USER', %s, %s::jsonb)
            """, (actor_id, user_id, json.dumps(details)))

        return jsonify({'success': True, 'message': 'User unblocked successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@superadmin_bp.route('/superadmin/users/<user_id>', methods=['DELETE'])
@token_required
@superadmin_required
def superadmin_delete_user(user_id):
    """Soft-delete user account by deactivating and anonymizing key identity fields."""
    try:
        actor_id = request.current_user['id']
        if user_id == actor_id:
            return jsonify({'success': False, 'error': 'You cannot delete your own account'}), 400

        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT id, email, name, phone, address, avatar_url, role, is_active,
                       COALESCE(is_superadmin, false) AS is_superadmin
                FROM users
                WHERE id = %s
            """, (user_id,))
            target = cursor.fetchone()
            if not target:
                return jsonify({'success': False, 'error': 'User not found'}), 404
            if target['is_superadmin']:
                return jsonify({'success': False, 'error': 'Cannot delete another superadmin'}), 403

            deleted_email = f"deleted_{user_id}@deleted.local"
            cursor.execute("""
                UPDATE users
                SET is_active = false,
                    email = %s,
                    name = 'Deleted User',
                    phone = NULL,
                    address = NULL,
                    avatar_url = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            """, (deleted_email, user_id))

            details = {
                'previous_email': target.get('email'),
                'previous_name': target.get('name'),
                'previous_phone': target.get('phone'),
                'previous_address': target.get('address'),
                'previous_avatar_url': target.get('avatar_url'),
                'previous_is_active': bool(target.get('is_active')),
                'target_role': target.get('role'),
                'reverted': False,
            }
            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details)
                VALUES (%s, 'SUPERADMIN_DELETE_USER', 'USER', %s, %s::jsonb)
            """, (actor_id, user_id, json.dumps(details)))

        return jsonify({'success': True, 'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@superadmin_bp.route('/superadmin/actions/<action_id>/revert', methods=['POST'])
@token_required
@superadmin_required
def superadmin_revert_action(action_id):
    """Revert moderation actions and audited domain actions."""
    try:
        actor_id = request.current_user['id']

        with db_connection.get_cursor(commit=True) as cursor:
            cursor.execute("""
                SELECT id, action, entity_id, details
                FROM activity_logs
                WHERE id = %s
                LIMIT 1
            """, (action_id,))
            log = cursor.fetchone()
            if not log:
                return jsonify({'success': False, 'error': 'Action log not found'}), 404

            action = log.get('action')
            details = _parse_json_details(log.get('details'))
            if details.get('reverted'):
                return jsonify({'success': False, 'error': 'Action already reverted'}), 400

            target_user_id = log.get('entity_id')
            reverted_context = {'reverted_action': action, 'source_action_id': action_id}

            if action in ('SUPERADMIN_BLOCK_USER', 'SUPERADMIN_UNBLOCK_USER', 'SUPERADMIN_DELETE_USER'):
                cursor.execute("SELECT id FROM users WHERE id = %s", (target_user_id,))
                target_exists = cursor.fetchone()
                if not target_exists:
                    return jsonify({'success': False, 'error': 'Target user no longer exists'}), 404

                if action in ('SUPERADMIN_BLOCK_USER', 'SUPERADMIN_UNBLOCK_USER'):
                    previous_is_active = bool(details.get('previous_is_active', True))
                    cursor.execute("""
                        UPDATE users
                        SET is_active = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (previous_is_active, target_user_id))
                else:
                    cursor.execute("""
                        UPDATE users
                        SET email = %s,
                            name = %s,
                            phone = %s,
                            address = %s,
                            avatar_url = %s,
                            is_active = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        details.get('previous_email'),
                        details.get('previous_name'),
                        details.get('previous_phone'),
                        details.get('previous_address'),
                        details.get('previous_avatar_url'),
                        bool(details.get('previous_is_active', True)),
                        target_user_id,
                    ))

                reverted_context['target_user_id'] = target_user_id
            elif action and action.startswith('AUDIT_'):
                allowed_tables = {
                    'reports', 'tasks', 'zones', 'bulk_notifications', 'notifications',
                    'citizen_profiles', 'cleaner_profiles', 'admin_profiles',
                    'cleanup_reviews', 'users'
                }
                table_name = (details.get('table') or '').strip()
                operation = (details.get('operation') or '').upper().strip()
                entity_id = log.get('entity_id')

                if table_name not in allowed_tables:
                    return jsonify({'success': False, 'error': 'This audited table is not revertible'}), 400
                if operation not in ('INSERT', 'UPDATE', 'DELETE'):
                    return jsonify({'success': False, 'error': 'Unsupported audited operation'}), 400
                if not entity_id:
                    return jsonify({'success': False, 'error': 'Missing target entity for revert'}), 400

                # Use only a fixed table whitelist and snapshot payload columns from DB audit data.
                if operation == 'INSERT':
                    if table_name == 'users':
                        cursor.execute("SELECT is_superadmin FROM users WHERE id = %s", (entity_id,))
                        target_user = cursor.fetchone()
                        if target_user and bool(target_user.get('is_superadmin')):
                            return jsonify({'success': False, 'error': 'Cannot auto-revert superadmin user insert'}), 400

                    cursor.execute(f"DELETE FROM {table_name} WHERE id = %s", (entity_id,))
                    if cursor.rowcount == 0:
                        return jsonify({'success': False, 'error': 'Target row already removed'}), 400

                elif operation == 'UPDATE':
                    old_row = details.get('old') or {}
                    if not isinstance(old_row, dict) or not old_row:
                        return jsonify({'success': False, 'error': 'Missing snapshot for audited update revert'}), 400

                    if table_name == 'users' and bool(old_row.get('is_superadmin')) and str(entity_id) != str(actor_id):
                        return jsonify({'success': False, 'error': 'Cannot modify another superadmin via automatic revert'}), 403

                    update_values = {k: v for k, v in old_row.items() if k != 'id'}
                    if not update_values:
                        return jsonify({'success': False, 'error': 'No fields available to restore'}), 400

                    set_clause = ', '.join([f'"{column}" = %s' for column in update_values.keys()])
                    params = list(update_values.values()) + [entity_id]
                    cursor.execute(f"UPDATE {table_name} SET {set_clause} WHERE id = %s", tuple(params))
                    if cursor.rowcount == 0:
                        return jsonify({'success': False, 'error': 'Target row not found for update revert'}), 404

                else:  # DELETE
                    old_row = details.get('old') or {}
                    if table_name == 'users':
                        return jsonify({'success': False, 'error': 'Deleted users cannot be auto-restored safely'}), 400
                    if not isinstance(old_row, dict) or not old_row:
                        return jsonify({'success': False, 'error': 'Missing snapshot for audited delete revert'}), 400

                    columns = list(old_row.keys())
                    quoted_columns = ', '.join([f'"{column}"' for column in columns])
                    placeholders = ', '.join(['%s'] * len(columns))
                    update_columns = [column for column in columns if column != 'id']

                    if update_columns:
                        update_clause = ', '.join([f'"{column}" = EXCLUDED."{column}"' for column in update_columns])
                        query = f"INSERT INTO {table_name} ({quoted_columns}) VALUES ({placeholders}) ON CONFLICT (id) DO UPDATE SET {update_clause}"
                    else:
                        query = f"INSERT INTO {table_name} ({quoted_columns}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"

                    cursor.execute(query, tuple(old_row[column] for column in columns))

                reverted_context['table'] = table_name
                reverted_context['operation'] = operation
                reverted_context['entity_id'] = entity_id
            else:
                return jsonify({'success': False, 'error': 'This action type cannot be reverted'}), 400

            details['reverted'] = True
            details['reverted_at'] = datetime.now().isoformat()
            details['reverted_by'] = actor_id
            cursor.execute("""
                UPDATE activity_logs
                SET details = %s::jsonb
                WHERE id = %s
            """, (json.dumps(details), action_id))

            cursor.execute("""
                INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details)
                VALUES (%s, 'SUPERADMIN_REVERT_ACTION', 'ACTIVITY_LOG', %s, %s::jsonb)
            """, (actor_id, action_id, json.dumps(reverted_context)))

        return jsonify({'success': True, 'message': 'Action reverted successfully'}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
