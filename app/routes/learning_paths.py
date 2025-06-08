from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.models.learning_path import LearningPath
from app.services.recommendation import RecommendationService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input
from app.utils.swagger_utils import yaml_from_file

learning_paths_bp = Blueprint('learning_paths', __name__)

@learning_paths_bp.route('/recommended', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/learning_paths/get_recommended_paths.yaml')
def get_recommended_paths():
    try:

        user_id = get_jwt_identity()
        
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
        print(f"Error fetching learning paths: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
