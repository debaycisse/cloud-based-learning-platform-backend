from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.models.user import User
from app.models.assessment import AssessmentResult
from app.utils.validation import validate_json, sanitize_input
from app.utils.swagger_utils import yaml_from_file
from app.utils.cooldown_manager import manage_cooldown
from app.utils.auth import admin_required

users_bp = Blueprint('users', __name__)

'''
User Management routes for profile retrieval, update, and progress tracking.
These routes include JWT authentication, input validation, and data sanitization.
'''

'''
Retrieves all users
- GET /api/users/all
- Response: JSON with list of users
- JWT required
- Admin role required
'''
@users_bp.route('/all', methods=['GET'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/users/get_all_users.yaml')
def get_all_users():
    try:
        limit = request.args.get('limit', 100)
        skip = request.args.get('skip', 0)

        users = User.find_all_users(limit=limit, skip=skip)

        if not users:
            return jsonify({"error": "No users found"}), 404
        
        # Remove sensitive information
        for user in users:
            user['_id'] = str(user['_id'])
            user.pop('password_hash', None)

        return jsonify({
            "users": users,
            "count": len(users),
            "limit": limit,
            "skip": skip
            }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
Retrieves a specific user by ID
- GET /api/users/<user_id>
- Response: JSON with user information
- JWT required
- Admin role required
'''
@users_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/users/get_user.yaml')
def get_user(user_id):
    try:
            
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Remove sensitive information
        user.pop('password_hash', None)
    
        return jsonify({
            "user": {
                "_id": str(user.get('_id', '')),
                "name": user.get('name', ''),
                "email": user.get('email', ''),
                "username": user.get('username', ''),
                "role": user.get('role', 'user'),
                "progress": user.get('progress', {
                    'completed_courses': [],
                    'in_progress_courses': [],
                    'completed_assessments': []
                }),
                "preferences": user.get('preferences', {
                    'categories': [],
                    'skills': [],
                    'difficulty': 'beginner',
                    'learning_style': 'textual',
                    'time_commitment': 'medium',
                    'goals': []
                }),
                "created_at": user.get('created_at', None),
                "updated_at": user.get('updated_at', None)
            }
        }), 200
    
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
Retrieves user's profile
- GET /api/users/profile
- Response: JSON with user profile information
- JWT required
'''
@users_bp.route('/profile', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/users/get_profile.yaml')
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        manage_cooldown(user_id=user_id)
        
        # Remove sensitive information
        user.pop('password_hash', None)
        
        return jsonify({
            "profile": {
                "_id": str(user['_id']),
                "name": str(user['name']),
                "email": user.get('email'),
                "username": user.get('username'),
                "role": user.get('role', 'user'),
                "created_at": user.get('created_at', None),
                "updated_at": user.get('updated_at', None),
                "progress": user.get('progress', [],),
                "preferences": user.get('preferences', [],),
            }
        }), 200
    
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
'''
Retrives user's cooldown field
- GET /api/users/cooldown
- Response: cooldown data in JSON format
- JWT required 
'''
@users_bp.route('/cooldown', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/users/get_cooldown.yaml')
def get_cooldown():
    try:
        user_id = get_jwt_identity()
        
        manage_cooldown(user_id=user_id)

        user = User.find_by_id(user_id=user_id)

        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_cooldwon = user.get('cooldown', {})

        if user_cooldwon:   
            return jsonify({
                'course_id': user_cooldwon.get('course_id', ''),
                'duration': user_cooldwon.get('duration', ''),
                'concepts': user_cooldwon.get('concepts', []),
            }), 200
        
        return jsonify({'message': 'No cooldown data found for this user'}), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
    try:
        user_id = get_jwt_identity()
        data = sanitize_input(request.get_json())

        manage_cooldown(user_id=user_id)

        # Update user profile
        updated_user = User.update_profile(
            user_id=user_id,
            update_data=data
        )
        
        if not updated_user:
            return jsonify({"error": "User not found"}), 404
        
        # Remove sensitive information
        updated_user.pop('password_hash', None)

        # Convert the id to string
        updated_user['_id'] = str(updated_user.get('_id', None))
        
        return jsonify({
            "message": "Profile updated successfully",
            "profile": updated_user
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
    try:
            
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)

        manage_cooldown(user_id=user_id)
        
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

        course_progress = user.get('course_progress', {
            'course_id': '',
            'percentage': 0,
            'completed_course_id': ''
        })

        
        return jsonify({
            "progress": progress,
            "course_progress": course_progress,
            "assessment_results": assessment_results
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
Updates course progress for a user
- PUT /api/users/progress
- Request body: JSON with course_id and percentage
- Response: JSON with success message and updated progress
- JWT required
'''
@users_bp.route('/progress', methods=['PUT'])
@jwt_required()
@validate_json('course_id', 'percentage')
@yaml_from_file('docs/swagger/users/update_progress.yaml')
def update_progress():
    try:
        user_id = get_jwt_identity()
        data = sanitize_input(request.get_json())

        manage_cooldown(user_id=user_id)
        
        course_id = data.get('course_id')
        percentage = data.get('percentage', 0)
        
        if not course_id or not isinstance(percentage, (int, float)):
            return jsonify({"error": "Invalid input"}), 400
        
        progress_data = {
            'course_id': course_id,
            'percentage': percentage
        }

        # Update course progress
        course_progress_update = User.update_course_progress(user_id, progress_data)
        
        if course_progress_update is None:
            return jsonify({"error": "Course update failure"}), 404

        return jsonify({
            "message": "Progress updated successfully",
            "progress": course_progress_update.get('progress', {}),
            "course_progress": course_progress_update.get('course_progress', {})
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)

        manage_cooldown(user_id=user_id)
        
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

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
    try:    
        user_id = get_jwt_identity()
        data = sanitize_input(request.get_json())

        manage_cooldown(user_id=user_id)
        
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

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
