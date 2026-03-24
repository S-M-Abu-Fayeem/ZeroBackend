from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from models import db_connection, setup_database, apply_runtime_schema_patches, Model
from dotenv import load_dotenv
import os
import importlib
import bcrypt
import jwt
import json
from auth import token_required, role_required, superadmin_required

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise RuntimeError('Missing required SECRET_KEY environment variable. Set it in ZeroBackend/.env')

# Configure CORS
CORS(app, 
     resources={r"/api/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:3000"]}},
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization'],
     supports_credentials=True)

# Initialize database connection pool and setup database
db_connection.create_pool()
apply_runtime_schema_patches()


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


ensure_default_superadmin()


def _parse_json_details(raw_details):
    if isinstance(raw_details, dict):
        return raw_details
    if isinstance(raw_details, str):
        try:
            return json.loads(raw_details)
        except Exception:
            return {}
    return {}

# Create model instances
users_model = Model(db_connection, 'users')
citizen_profiles_model = Model(db_connection, 'citizen_profiles')
cleaner_profiles_model = Model(db_connection, 'cleaner_profiles')
admin_profiles_model = Model(db_connection, 'admin_profiles')

# Route modules attach endpoints onto blueprint objects via decorators.
ROUTE_MODULES = [
        # Citizen route modules
        'citizen_profile_routes',
        'citizen_report_routes',
        'citizen_engagement_routes',
        'citizen_notification_routes',
        'citizen_account_routes',

        # Cleaner route modules
        'cleaner_profile_routes',
        'cleaner_task_routes',
        'cleaner_payment_routes',
        'cleaner_community_routes',
        
        # Admin route modules
        'admin_profile_routes',
        'admin_management_routes',
        'admin_report_routes',
]


def load_required_route_modules():
    """Import route modules so decorators attach endpoints to blueprint objects."""
    for module_name in ROUTE_MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            raise RuntimeError(f"Failed to load route module '{module_name}': {exc}") from exc


load_required_route_modules()

# Every registered blueprint now follows one module+symbol+prefix pattern.
BLUEPRINT_SPECS = [
    ('citizen_blueprint', 'citizen_bp', '/api/citizen'),
    ('admin_blueprint', 'admin_bp', '/api/admin'),
    ('cleaner_blueprint', 'cleaner_bp', '/api/cleaner'),
    ('admin_tasks', 'admin_tasks_bp', '/api/admin'),
    ('admin_zones', 'admin_zones_bp', '/api/admin'),
    ('admin_payments', 'admin_payments_bp', '/api/admin'),
    ('shared_endpoints', 'shared_bp', '/api'),
    ('notifications', 'notifications_bp', '/api'),
    ('leaderboards', 'leaderboards_bp', '/api'),
    ('ai_analysis', 'ai_bp', '/api'),
]


def load_and_register_blueprints(flask_app: Flask):
    """Import blueprint symbols from modules and register them with prefixes."""
    for module_name, blueprint_attr, prefix in BLUEPRINT_SPECS:
        try:
            module = importlib.import_module(module_name)
            blueprint = getattr(module, blueprint_attr)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load blueprint '{blueprint_attr}' from '{module_name}': {exc}"
            ) from exc

        flask_app.register_blueprint(blueprint, url_prefix=prefix)


load_and_register_blueprints(app)


# Basic Routes
@app.route('/')
def home():
    """API documentation endpoint."""
    return jsonify({
        "message": "Zero Waste Management System API",
        "version": "1.0.0",
        "database": "PostgreSQL with 3NF normalization",
        "total_endpoints": 63,
        "endpoints": {
            "auth": {
                "POST /api/auth/register": "Register new user",
                "POST /api/auth/login": "Login user",
                "GET /api/auth/me": "Get current user profile",
                "POST /api/auth/logout": "Logout user"
            },
            "citizen": {
                "GET /api/citizen/profile": "Get citizen profile",
                "PUT /api/citizen/profile": "Update citizen profile",
                "GET /api/citizen/stats": "Get citizen statistics",
                "POST /api/citizen/reports": "Submit waste report",
                "GET /api/citizen/reports": "Get my reports",
                "GET /api/citizen/reports/<id>": "Get report details",
                "POST /api/citizen/reports/<id>/review": "Submit cleanup review",
                "GET /api/citizen/badges": "Get my badges",
                "GET /api/citizen/points": "Get points history",
                "GET /api/citizen/leaderboard": "Get citizen leaderboard",
                "GET /api/citizen/notifications": "Get notifications"
            },
            "cleaner": {
                "GET /api/cleaner/profile": "Get cleaner profile",
                "PUT /api/cleaner/profile": "Update cleaner profile",
                "GET /api/cleaner/stats": "Get cleaner statistics",
                "GET /api/cleaner/tasks/available": "Get available tasks",
                "POST /api/cleaner/tasks/<id>/take": "Take task",
                "GET /api/cleaner/tasks": "Get my tasks",
                "POST /api/cleaner/tasks/<id>/complete": "Complete task",
                "GET /api/cleaner/tasks/<id>": "Get task details",
                "GET /api/cleaner/earnings": "Get earnings history",
                "GET /api/cleaner/reviews": "Get reviews",
                "GET /api/cleaner/leaderboard": "Get cleaner leaderboard"
            },
            "admin": {
                "GET /api/admin/profile": "Get admin profile",
                "PUT /api/admin/profile": "Update admin profile",
                "GET /api/admin/users": "Get all users",
                "GET /api/admin/users/<id>": "Get user details",
                "GET /api/admin/stats": "Get system stats",
                "GET /api/admin/reports/pending": "Get pending reports",
                "POST /api/admin/reports/<id>/approve": "Approve report",
                "POST /api/admin/reports/<id>/decline": "Decline report",
                "GET /api/admin/reports": "Get all reports",
                "GET /api/admin/tasks": "Get all tasks",
                "POST /api/admin/tasks": "Create manual task",
                "PUT /api/admin/tasks/<id>": "Update task",
                "DELETE /api/admin/tasks/<id>": "Delete task",
                "GET /api/admin/zones": "Get zones",
                "POST /api/admin/zones": "Create zone",
                "PUT /api/admin/zones/<id>": "Update zone",
                "GET /api/admin/zones/<id>": "Get zone details",
                "DELETE /api/admin/zones/<id>": "Delete zone",
                "GET /api/admin/payments/pending": "Get pending payments",
                "POST /api/admin/payments/process": "Process payments"
            },
            "ai": {
                "POST /api/ai/analyze-waste": "Analyze waste image",
                "POST /api/ai/compare-cleanup": "Compare before/after images",
                "POST /api/ai/analyze-report/<id>": "Analyze existing report"
            },
            "notifications": {
                "GET /api/notifications": "Get notifications (all roles)",
                "PUT /api/notifications/<id>/read": "Mark notification read",
                "PUT /api/notifications/read-all": "Mark all notifications read",
                "POST /api/admin/notifications/bulk": "Send bulk notification (admin)"
            },
            "leaderboards": {
                "GET /api/leaderboards/citizens": "Get citizen leaderboard",
                "GET /api/leaderboards/cleaners": "Get cleaner leaderboard",
                "POST /api/admin/leaderboards/recalculate": "Recalculate leaderboards (admin)"
            },
            "shared": {
                "GET /api/zones": "Get all zones",
                "GET /api/zones/by-location": "Find zone by coordinates",
                "GET /api/zones/<id>/stats": "Get zone statistics",
                "GET /api/reports/<id>": "Get report details (any role)",
                "GET /api/tasks/<id>": "Get task details (any role)"
            },
            "health": {
                "GET /api/health": "Check API health"
            }
        }
    })


@app.route('/api/health')
def health():
    """Check if API and database are running."""
    try:
        with db_connection.get_cursor() as cursor:
            cursor.execute("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }), 200



# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user
    Required JSON body:
        - email: User's email
        - password: User's password
        - name: User's name
        - role: User role (CITIZEN, CLEANER, ADMIN)
        - phone: User's phone (optional)
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Validate role
        valid_roles = ['CITIZEN', 'CLEANER', 'ADMIN']
        if data['role'] not in valid_roles:
            return jsonify({'success': False, 'error': f'Role must be one of: {", ".join(valid_roles)}'}), 400
        
        # Check if email already exists
        existing = users_model.execute_raw(
            "SELECT id FROM users WHERE email = %s",
            [data['email']]
        )
        
        if existing:
            return jsonify({'success': False, 'error': 'Email already exists'}), 409
        
        # Hash password
        password_hash = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user_data = {
            'email': data['email'],
            'password_hash': password_hash,
            'name': data['name'],
            'role': data['role'],
            'phone': data.get('phone'),
            'is_active': True
        }
        
        new_user = users_model.create(user_data)
        
        # Remove password hash from response
        new_user.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': new_user
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login user
    Required JSON body:
        - email: User's email
        - password: User's password
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Email and password are required'}), 400
        
        # Find user by email
        users = users_model.execute_raw(
            "SELECT * FROM users WHERE email = %s",
            [data['email']]
        )
        
        if not users:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        user = users[0]
        
        # Check if user is active
        if not user.get('is_active'):
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 401
        
        # Verify password
        if not bcrypt.checkpw(data['password'].encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Update last login
        users_model.execute_raw(
            "UPDATE users SET last_login_at = CURRENT_TIMESTAMP WHERE id = %s",
            [user['id']]
        )
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'email': user['email'],
            'role': user['role']
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        # Remove password hash from response
        user.pop('password_hash', None)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': user
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/me', methods=['GET'])
@token_required
def get_current_user():
    """Get current authenticated user profile"""
    try:
        user = request.current_user.copy()
        user.pop('password_hash', None)
        
        # Get role-specific profile
        profile = None
        if user['role'] == 'CITIZEN':
            profiles = citizen_profiles_model.execute_raw(
                "SELECT * FROM citizen_profiles WHERE user_id = %s",
                [user['id']]
            )
            profile = profiles[0] if profiles else None
        elif user['role'] == 'CLEANER':
            profiles = cleaner_profiles_model.execute_raw(
                "SELECT * FROM cleaner_profiles WHERE user_id = %s",
                [user['id']]
            )
            profile = profiles[0] if profiles else None
        elif user['role'] == 'ADMIN':
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


@app.route('/api/superadmin/dashboard', methods=['GET'])
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


@app.route('/api/superadmin/users', methods=['GET'])
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


@app.route('/api/superadmin/activity-logs', methods=['GET'])
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


@app.route('/api/superadmin/users/<user_id>/block', methods=['POST'])
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


@app.route('/api/superadmin/users/<user_id>/unblock', methods=['POST'])
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


@app.route('/api/superadmin/users/<user_id>', methods=['DELETE'])
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


@app.route('/api/superadmin/actions/<action_id>/revert', methods=['POST'])
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


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "success": False,
        "error": "Endpoint not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500


@app.teardown_appcontext
def cleanup(error):
    """Cleanup resources."""
    pass


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Zero Waste Management System API")
    print("="*70)
    if os.getenv('RERUN_MIGRATIONS', 'true').lower() == 'true':
        print("\nSetting up database...")
        setup_database()
    else:
        print("\nDatabase already setup...")
    print("\nAvailable endpoints:")
    print("  POST   http://127.0.0.1:5000/api/auth/register")
    print("  POST   http://127.0.0.1:5000/api/auth/login")
    print("  GET    http://127.0.0.1:5000/api/auth/me")
    print("  GET    http://127.0.0.1:5000/api/citizen/profile")
    print("  GET    http://127.0.0.1:5000/api/cleaner/profile")
    print("  GET    http://127.0.0.1:5000/api/admin/profile")
    print("  GET    http://127.0.0.1:5000/api/health")
    print("\nTip: Use Postman, curl, or Thunder Client to test the API")
    print("="*70 + "\n")
    
    try:
        app.run(debug=True, port=5000)
    finally:
        db_connection.close_pool()
