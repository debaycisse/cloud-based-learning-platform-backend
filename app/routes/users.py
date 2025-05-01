from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.user import User
from app.models.assessment import AssessmentResult
from app.utils.validation import validate_json, sanitize_input
from app.utils.swagger_utils import yaml_from_file
from app.utils.auth import admin_required

users_bp = Blueprint('users', __name__)

'''
User Management routes for profile retrieval, update, and progress tracking.
These routes include JWT authentication, input validation, and data sanitization.
'''

@users_bp.route('/all', methods=['GET'])
@jwt_required()
@admin_required()
@yaml_from_file('docs/swagger/users/get_all_users.yaml')
def get_all_users():
    """
    Retrieves all users
    - GET /api/users/all
    - Response: JSON with list of users
    - JWT required
    """
    users = User.find_all_users()

    if not users:
        return jsonify({"error": "No users found"}), 404
    
    # Remove sensitive information
    for user in users:
        user.pop('password_hash', None)
    
    return jsonify({"users": users}), 200

'''
Retrieves user profile
- GET /api/users/profile
- Response: JSON with user profile information
- JWT required
'''
@users_bp.route('/profile', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/users/get_profile.yaml')
def get_profile():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Remove sensitive information
    user.pop('password_hash', None)
    
    return jsonify({
        "profile": {
            "id": str(user['_id']),
            "email": user['email'],
            "username": user['username'],
            "role": user.get('role', 'user'),
            "created_at": user.get('created_at').isoformat() if user.get('created_at') else None,
            "updated_at": user.get('updated_at').isoformat() if user.get('updated_at') else None
        }
    }), 200

'''
Updates user profile
- PUT /api/users/profile
- Request body: JSON with fields to update (excluding sensitive fields)
- Response: JSON with success message and updated profile information
- JWT required
'''
@users_bp.route('/profile', methods=['PUT'])
@jwt_required()
@validate_json()
@yaml_from_file('docs/swagger/users/update_profile.yaml')
def update_profile():
    user_id = get_jwt_identity()
    data = sanitize_input(request.get_json())
    
    # Prevent updating sensitive fields
    data.pop('password_hash', None)
    data.pop('role', None)
    data.pop('_id', None)
    
    # Update user profile
    updated_user = User.update_profile(user_id, data)
    
    if not updated_user:
        return jsonify({"error": "User not found"}), 404
    
    # Remove sensitive information
    updated_user.pop('password_hash', None)
    
    return jsonify({
        "message": "Profile updated successfully",
        "profile": updated_user
    }), 200

'''
Retrieves user progress
- GET /api/users/progress
- Response: JSON with user progress information
- JWT required
'''
@users_bp.route('/progress', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/users/get_progress.yaml')
def get_progress():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get assessment results
    assessment_results = AssessmentResult.find_by_user(user_id)
    
    # Get user progress from user document
    progress = user.get('progress', {
        'completed_courses': [],
        'in_progress_courses': [],
        'completed_assessments': []
    })
    
    return jsonify({
        "progress": progress,
        "assessment_results": assessment_results
    }), 200


'''
Retrieves user preferences
- GET /api/users/preferences
- Response: JSON with user preferences
- JWT required
'''
@users_bp.route('/preferences', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/users/get_preferences.yaml')
def get_preferences():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get user preferences
    preferences = user.get('preferences', {
        'categories': [],
        'skills': [],
        'difficulty': 'beginner',
        'learning_style': 'visual',
        'time_commitment': 'medium',
        'goals': []
    })
    
    return jsonify({
        "preferences": preferences
    }), 200

'''
Updates user preferences
- PUT /api/users/preferences
- Request body: JSON with fields to update
- Response: JSON with success message and updated preferences
- JWT required
'''
@users_bp.route('/preferences', methods=['PUT'])
@jwt_required()
@validate_json()
@yaml_from_file('docs/swagger/users/update_preferences.yaml')
def update_preferences():
    user_id = get_jwt_identity()
    data = sanitize_input(request.get_json())
    
    # Update user preferences
    updated_user = User.update_preferences(user_id, data)
    
    if not updated_user:
        return jsonify({"error": "User not found"}), 404
    
    # Get updated preferences
    preferences = updated_user.get('preferences', {})
    
    return jsonify({
        "message": "Preferences updated successfully",
        "preferences": preferences
    }), 200
