from flask import Flask, jsonify, request
from datetime import datetime
from models import db_connection, setup_database
from dotenv import load_dotenv
import os
from citizen import citizen_app
from admin import admin_app
from cleaner import cleaner_app

load_dotenv()

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False


# Modular Blueprints can be registered here if needed
app.register_blueprint(citizen_app, url_prefix='/citizen')
app.register_blueprint(admin_app, url_prefix='/admin')
app.register_blueprint(cleaner_app, url_prefix='/cleaner')


# Initialize database connection pool and setup database
db_connection.create_pool()
if os.getenv('RERUN_MIGRATIONS', 'true').lower() == 'true':
    setup_database()
users_model = Model(db_connection, 'users')






# Basic Routes
@app.route('/')
def home():
    """API documentation endpoint."""
    return jsonify({
        "message": "Flask REST API with Custom Database Helper",
        "version": "1.0.0",
        "database": "PostgreSQL with custom helper library",
        "endpoints": {
            "GET /api/users": "Get all users",
            "GET /api/users/<id>": "Get user by ID",
            "POST /api/users": "Create new user",
            "PUT /api/users/<id>": "Update user by ID",
            "DELETE /api/users/<id>": "Delete user by ID",
            "GET /api/health": "Check API health"
        }
    })


@app.route('/api/health')
def health():
    """Check if API and database are running."""
    try:
        # Test database connection
        users_model.execute_raw("SELECT 1")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return jsonify({
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }), 200



@app.route('/api/users', methods=['GET'])
def get_users():
    """
    Get all users with optional filtering.
    Query Parameters:
        - name: Filter by name (partial match)
        - limit: Limit number of results
        - order_by: Sort by column (e.g., 'name', 'created_at DESC')
    """
    try:
        name_filter = request.args.get('name')
        limit = request.args.get('limit', type=int)
        order_by = request.args.get('order_by', 'id')
        
        # If name filter is provided, use raw SQL for LIKE search
        if name_filter:
            query = "SELECT * FROM users WHERE name ILIKE %s ORDER BY " + order_by
            params = [f"%{name_filter}%"]
            if limit:
                query += f" LIMIT {limit}"
            users = users_model.execute_raw(query, params)
        else:
            users = users_model.find_all(order_by=order_by, limit=limit)
        
        return jsonify({
            "success": True,
            "count": len(users),
            "data": users
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Get a specific user by ID."""
    try:
        user = users_model.find_by_id(user_id)
        
        if user:
            return jsonify({
                "success": True,
                "data": user
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



@app.route('/api/users', methods=['POST'])
def create_user():
    """
    Create a new user.
    Required JSON body:
        - name: User's name
        - email: User's email
    """
    try:
        # Check if request contains JSON
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name') or not data.get('email'):
            return jsonify({
                "success": False,
                "error": "Name and email are required"
            }), 400
        
        # Check if email already exists
        existing = users_model.execute_raw(
            "SELECT id FROM users WHERE email = %s",
            [data['email']]
        )
        
        if existing:
            return jsonify({
                "success": False,
                "error": "Email already exists"
            }), 409
        
        # Create new user
        new_user = users_model.create({
            'name': data['name'],
            'email': data['email']
        })
        
        return jsonify({
            "success": True,
            "message": "User created successfully",
            "data": new_user
        }), 201
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """
    Update an existing user.
    JSON body can contain:
        - name: New name
        - email: New email
    """
    try:
        # Check if user exists
        user = users_model.find_by_id(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        if not request.is_json:
            return jsonify({
                "success": False,
                "error": "Content-Type must be application/json"
            }), 400
        
        data = request.get_json()
        update_data = {}
        
        # Prepare update data
        if 'name' in data:
            update_data['name'] = data['name']
        
        if 'email' in data:
            # Check if email is taken by another user
            existing = users_model.execute_raw(
                "SELECT id FROM users WHERE email = %s AND id != %s",
                [data['email'], user_id]
            )
            if existing:
                return jsonify({
                    "success": False,
                    "error": "Email already exists"
                }), 409
            update_data['email'] = data['email']
        
        if not update_data:
            return jsonify({
                "success": False,
                "error": "No fields to update"
            }), 400
        
        # Update user
        updated_user = users_model.update(update_data, {'id': user_id})
        
        return jsonify({
            "success": True,
            "message": "User updated successfully",
            "data": updated_user
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user by ID."""
    try:
        # Check if user exists
        user = users_model.find_by_id(user_id)
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Delete user
        deleted_count = users_model.delete({'id': user_id})
        
        return jsonify({
            "success": True,
            "message": f"User {user_id} deleted successfully",
            "deleted_count": deleted_count
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500



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
    print("Flask REST API with Custom Database Helper")
    print("="*70)
    print("\nSetting up database...")
    setup_database()
    print("\nAvailable endpoints:")
    print("  GET    http://127.0.0.1:5000/")
    print("  GET    http://127.0.0.1:5000/api/health")
    print("  GET    http://127.0.0.1:5000/api/users")
    print("  GET    http://127.0.0.1:5000/api/users/<id>")
    print("  POST   http://127.0.0.1:5000/api/users")
    print("  PUT    http://127.0.0.1:5000/api/users/<id>")
    print("  DELETE http://127.0.0.1:5000/api/users/<id>")
    print("\nTip: Use Postman, curl, or Thunder Client to test the API")
    print("="*70 + "\n")
    
    try:
        app.run(debug=True, port=5000)
    finally:
        # Close database connection pool when application shuts down
        db_connection.close_pool()
