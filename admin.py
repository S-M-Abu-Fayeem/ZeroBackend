from flask import Blueprint, jsonify, request
from app import users_model

admin_app = Blueprint('admin', __name__)

@admin_app.route('/users', methods=['GET'])
def get_all_users_admin():
    """Admin endpoint to get all users."""
    try:
        users = users_model.find_all()
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