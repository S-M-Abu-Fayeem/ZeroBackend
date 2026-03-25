"""
Authentication middleware and decorators
"""
from flask import request, jsonify
from functools import wraps
import jwt
import os
from dotenv import load_dotenv

load_dotenv()


def _get_secret_key() -> str:
    """Load JWT secret from environment after dotenv is initialized."""
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key:
        raise RuntimeError('Missing required SECRET_KEY environment variable. Set it in ZeroBackend/.env')
    return secret_key


def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Import here to avoid circular import
        from models import db_connection
        from db_helper import Model
        users_model = Model(db_connection, 'users')
        
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'success': False, 'error': 'Token is missing'}), 401
        
        try:
            # Decode token
            secret_key = _get_secret_key()
            data = jwt.decode(token, secret_key, algorithms=["HS256"])
            current_user = users_model.find_by_id(data['user_id'])
            
            if not current_user:
                return jsonify({'success': False, 'error': 'User not found'}), 401
            
            # Add user to request context
            request.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'error': 'Invalid token'}), 401
        except Exception as e:
            # Protect API routes from raw DB/connection failures during auth lookup.
            print(f"Token validation failed due to backend error: {e}")
            return jsonify({'success': False, 'error': 'Authentication service temporarily unavailable'}), 503
        
        return f(*args, **kwargs)
    
    return decorated


def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            if request.current_user['role'] not in roles:
                return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def superadmin_required(f):
    """Decorator to ensure current user is marked as superadmin."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(request, 'current_user'):
            return jsonify({'success': False, 'error': 'Authentication required'}), 401

        if request.current_user.get('role') != 'ADMIN' or not request.current_user.get('is_superadmin', False):
            return jsonify({'success': False, 'error': 'Superadmin permissions required'}), 403

        return f(*args, **kwargs)

    return decorated_function
