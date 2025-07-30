from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.models.learning_path import LearningPath
from app.services.recommendation import RecommendationService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input
from app.utils.swagger_utils import yaml_from_file
from app.utils.cooldown_manager import manage_cooldown

learning_paths_bp = Blueprint('learning_paths', __name__)

'''
GET /api/learning_paths/recommended
- Retrieves personalized learning path recommendations for the authenticated user.
- Returns a list of recommended learning paths or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
- If the user does not have access to the learning paths, returns an error message.
- If the user is authenticated, manages cooldown for the user.
- If the user does not have access to the learning paths, returns an error message.
'''
@learning_paths_bp.route('/recommended', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/learning_paths/get_recommended_paths.yaml')
def get_recommended_paths():
    try:

        user_id = get_jwt_identity()

        manage_cooldown(user_id=user_id)
        
        # Get personalized learning path recommendations
        recommended_paths = RecommendationService.get_learning_path_recommendations(user_id)
        
        return jsonify({
            "recommended_paths": recommended_paths,
            "count": len(recommended_paths)
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
GET /api/learning_paths/<path_id>
- Retrieves a specific learning path by its ID.
- Returns the learning path or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
- If the user does not have access to the learning path, returns an error message.
- If the user is authenticated, manages cooldown for the user.
- If the user does not have access to the learning path, returns an error message.
'''
@learning_paths_bp.route('/<path_id>', methods=['GET'])
@yaml_from_file('docs/swagger/learning_paths/get_learning_path.yaml')
def get_learning_path(path_id):
    try:
            
        path = LearningPath.find_by_id(path_id)
        
        if not path:
            return jsonify({"error": "Learning path not found"}), 404
        
        path['_id'] = str(path['_id'])
        
        return jsonify(path), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
GET /api/learning_paths
- Retrieves all learning paths with optional filtering by skill.
- Returns a list of learning paths or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
'''
@learning_paths_bp.route('', methods=['GET'])
@yaml_from_file('docs/swagger/learning_paths/get_learning_paths.yaml')
def get_learning_paths():
    try:

        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        skill = request.args.get('skill')
        
        if skill is not None:
            paths = LearningPath.find_by_skill(skill=skill, limit=limit, skip=skip)
        else:
            paths = LearningPath.find_all(limit=limit, skip=skip)

        for path in paths:
            path['_id'] = str(path['_id'])
        
        return jsonify({
            "learning_paths": paths,
            "count": len(paths),
            "skip": skip,
            "limit": limit
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
POST /api/learning_paths
- Creates a new learning path.
- Expects a JSON payload with 'title', 'description', 'courses', and optional 'target_skills'.
- Returns a success message or an error message if creation fails.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires admin privileges.
- If the user is not authenticated, returns an error message.
- If the user does not have admin privileges, returns an error message.
- If the user is authenticated, manages cooldown for the user.
- If the user does not have access to the learning paths, returns an error message.
'''
@learning_paths_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title', 'description', 'courses')
@yaml_from_file('docs/swagger/learning_paths/create_learning_path_admin_only.yaml')
def create_learning_path():
    try:

        data = sanitize_input(request.get_json())
        
        # Create new learning path
        path = LearningPath.create(
            title=data.get('title'),
            description=data.get('description'),
            courses=data.get('courses'),
            target_skills=data.get('target_skills', [])
        )
        
        return jsonify({
            "message": "Learning path created successfully",
            "learning_path": path
        }), 201

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
PUT /api/learning_paths/<path_id>
- Updates an existing learning path by its ID.
- Expects a JSON payload with 'title', 'description', 'courses', and optional 'target_skills'.
- Returns a success message or an error message if the update fails.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires admin privileges.
- If the user is not authenticated, returns an error message.
- If the user does not have admin privileges, returns an error message.
- If the user is authenticated, manages cooldown for the user.
- If the user does not have access to the learning paths, returns an error message.
'''
@learning_paths_bp.route('/<path_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('title', 'description', 'courses')
@yaml_from_file('docs/swagger/learning_paths/update_learning_path_admin_only.yaml')
def update_learning_path(path_id):
    try:

        data = sanitize_input(request.get_json())
        
        # Update learning path
        updated_path = LearningPath.update(
            path_id=path_id,
            update_data={
                'title': data.get('title'),
                'description': data.get('description'),
                'courses': data.get('courses'),
                'target_skills': data.get('target_skills', [])
            }
        )
        
        if not updated_path:
            return jsonify({"error": "Learning path not found"}), 404
        
        updated_path['_id'] = str(updated_path['_id'])
        
        return jsonify({
            "message": "Learning path updated successfully",
            "learning_path": updated_path
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
