from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.recommendation import RecommendationService
from app.utils.validation import validate_json, sanitize_input

recommendations_bp = Blueprint('recommendations', __name__)

@recommendations_bp.route('/courses', methods=['GET'])
@jwt_required()
def get_course_recommendations():
    """Get personalized course recommendations"""
    user_id = get_jwt_identity()
    limit = int(request.args.get('limit', 4))
    
    # Get course recommendations
    recommended_courses = RecommendationService.get_course_recommendations(user_id, limit)
    
    return jsonify({
        "recommended_courses": recommended_courses,
        "count": len(recommended_courses)
    }), 200

@recommendations_bp.route('/learning-paths', methods=['GET'])
@jwt_required()
def get_learning_path_recommendations():
    """Get personalized learning path recommendations"""
    user_id = get_jwt_identity()
    limit = int(request.args.get('limit', 3))
    
    # Get learning path recommendations
    recommended_paths = RecommendationService.get_learning_path_recommendations(user_id, limit)
    
    return jsonify({
        "recommended_paths": recommended_paths,
        "count": len(recommended_paths)
    }), 200

@recommendations_bp.route('/personalized', methods=['POST'])
@jwt_required()
def get_personalized_recommendations():
    """Get recommendations based on user preferences"""
    user_id = get_jwt_identity()
    data = sanitize_input(request.get_json() or {})
    limit = int(request.args.get('limit', 4))
    
    # Get personalized recommendations
    recommended_courses = RecommendationService.get_personalized_recommendations(
        user_id, data, limit
    )
    
    return jsonify({
        "recommended_courses": recommended_courses,
        "count": len(recommended_courses)
    }), 200

@recommendations_bp.route('/similar/<course_id>', methods=['GET'])
def get_similar_courses(course_id):
    """Get courses similar to a given course"""
    limit = int(request.args.get('limit', 3))
    
    # Get similar courses
    similar_courses = RecommendationService.get_similar_courses(course_id, limit)
    
    return jsonify({
        "similar_courses": similar_courses,
        "count": len(similar_courses)
    }), 200
