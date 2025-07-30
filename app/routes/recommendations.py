from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.services.recommendation import RecommendationService
from app.utils.validation import validate_json, sanitize_input
from app.utils.cooldown_manager import manage_cooldown
from app.utils.swagger_utils import yaml_from_file

recommendations_bp = Blueprint('recommendations', __name__)

'''
GET /api/recommendations/courses
- Retrieves personalized course recommendations for the authenticated user.
- Returns a list of recommended courses or an error message if not found.
- If the request fails, returns a network error message.
'''
@recommendations_bp.route('/courses', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/recommendations/get_courses_recommendations.yaml')
def get_course_recommendations():
    try:
        """Get personalized course recommendations"""
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 4))

        manage_cooldown(user_id=user_id)
        
        # Get course recommendations
        recommended_courses = RecommendationService.get_course_recommendations(user_id, limit)
        parsed_rec_cos =[]
        if recommended_courses is not None and len(recommended_courses) > 0:
            for rec_course in recommended_courses:
                rec_course['_id'] = str(rec_course['_id'])
                parsed_rec_cos.append(rec_course)
        
        return jsonify({
            "recommended_courses": parsed_rec_cos,
            "count": len(parsed_rec_cos)
        }), 200
    
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
GET /api/recommendations/learning_paths
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
@recommendations_bp.route('/learning_paths', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/recommendations/get_learning_paths_recommendations.yaml')
def get_learning_path_recommendations():
    try:
        """Get personalized learning path recommendations"""
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 3))

        manage_cooldown(user_id=user_id)
                
        # Get learning path recommendations
        recommended_paths = RecommendationService.get_learning_path_recommendations(user_id, limit)
        
        return jsonify({
            "recommended_paths": recommended_paths,
            "count": len(recommended_paths)
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
POST /api/recommendations/personalized
- Retrieves personalized recommendations based on user preferences.
- Expects a JSON payload with user preferences.
- Returns a list of recommended courses or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
- If the user does not have access to the recommendations, returns an error message.
- If the user is authenticated, manages cooldown for the user.
- If the user does not have access to the recommendations, returns an error message.
'''
@recommendations_bp.route('/personalized', methods=['POST'])
@jwt_required()
@yaml_from_file('docs/swagger/recommendations/get_personalized_recommendations.yaml')
def get_personalized_recommendations():
    try:
        """Get recommendations based on user preferences"""
        user_id = get_jwt_identity()
        data = sanitize_input(request.get_json() or {})
        limit = int(request.args.get('limit', 4))

        manage_cooldown(user_id=user_id)
        
        # Get personalized recommendations
        recommended_courses = RecommendationService.get_personalized_recommendations(
            user_id=user_id, preference_data=data, limit=limit
        )
        
        return jsonify({
            "recommended_courses": recommended_courses,
            "count": len(recommended_courses)
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
GET /api/recommendations/similar/<course_id>
- Retrieves courses similar to a given course ID.
- Returns a list of similar courses or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
- If the user does not have access to the similar courses, returns an error message.
- If the user is authenticated, manages cooldown for the user.
- If the user does not have access to the similar courses, returns an error message.
'''
@recommendations_bp.route('/similar/<course_id>', methods=['GET'])
@yaml_from_file('docs/swagger/recommendations/get_similar_courses.yaml')
def get_similar_courses(course_id):
    try:
            
        """Get courses similar to a given course"""
        limit = int(request.args.get('limit', 3))
        
        # Get similar courses
        similar_courses = RecommendationService.get_similar_courses(course_id, limit)
        
        return jsonify({
            "similar_courses": similar_courses,
            "count": len(similar_courses)
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
