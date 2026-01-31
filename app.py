from flask import Flask, jsonify, request
from datetime import datetime
from models import db_connection, setup_database, Model
from dotenv import load_dotenv
import os
import bcrypt
import jwt
from auth import token_required, role_required

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize database connection pool and setup database
db_connection.create_pool()


# Create model instances
users_model = Model(db_connection, 'users')
citizen_profiles_model = Model(db_connection, 'citizen_profiles')
cleaner_profiles_model = Model(db_connection, 'cleaner_profiles')
admin_profiles_model = Model(db_connection, 'admin_profiles')

# Import blueprints after models are created
from citizen import citizen_bp
from admin import admin_bp
from cleaner import cleaner_bp

# Register blueprints
app.register_blueprint(citizen_bp, url_prefix='/api/citizen')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(cleaner_bp, url_prefix='/api/cleaner')


# Basic Routes
@app.route('/')
def home():
    """API documentation endpoint."""
    return jsonify({
        "message": "Zero Waste Management System API",
        "version": "1.0.0",
        "database": "PostgreSQL with 3NF normalization",
        "endpoints": {
            "auth": {
                "POST /api/auth/register": "Register new user",
                "POST /api/auth/login": "Login user",
                "GET /api/auth/me": "Get current user profile"
            },
            "citizen": {
                "GET /api/citizen/profile": "Get citizen profile",
                "PUT /api/citizen/profile": "Update citizen profile"
            },
            "cleaner": {
                "GET /api/cleaner/profile": "Get cleaner profile",
                "PUT /api/cleaner/profile": "Update cleaner profile"
            },
            "admin": {
                "GET /api/admin/profile": "Get admin profile",
                "PUT /api/admin/profile": "Update admin profile",
                "GET /api/admin/users": "Get all users (admin only)"
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
        users_model.execute_raw("SELECT 1")
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
