from flask import Blueprint, jsonify, request
from app import users_model

citizen_app = Blueprint('citizen', __name__)

@citizen_app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users."""
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

