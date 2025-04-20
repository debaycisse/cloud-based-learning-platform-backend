from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.assessment import Assessment, AssessmentResult
from app.services.assessment import AssessmentService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input

assessments_bp = Blueprint('assessments', __name__)

@assessments_bp.route('/<course_id>', methods=['GET'])
@jwt_required()
def get_assessment_for_course(course_id):
    assessments = Assessment.find_by_course_id(course_id)
    
    if not assessments:
        return jsonify({"error": "No assessments found for this course"}), 404
    
    # For security, remove correct answers from the response
    for assessment in assessments:
        for question in assessment.get('questions', []):
            question.pop('correct_answer', None)
    
    return jsonify({"assessments": assessments}), 200

@assessments_bp.route('/<assessment_id>/submit', methods=['POST'])
@jwt_required()
@validate_json('answers')
def submit_assessment(assessment_id):
    user_id = get_jwt_identity()
    data = sanitize_input(request.get_json())
    answers = data.get('answers', [])
    
    # Submit and score the assessment
    result, error_message = AssessmentService.submit_assessment(
        user_id, assessment_id, answers
    )
    
    if error_message:
        return jsonify({"error": error_message}), 400
    
    return jsonify({
        "message": "Assessment submitted successfully",
        "result": {
            "score": result['score'],
            "passed": result['passed'],
            "knowledge_gaps": result['knowledge_gaps']
        }
    }), 200

@assessments_bp.route('/results', methods=['GET'])
@jwt_required()
def get_assessment_results():
    user_id = get_jwt_identity()
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    # Get assessment results for the user
    results = AssessmentResult.find_by_user(user_id, limit, skip)
    
    return jsonify({
        "results": results,
        "count": len(results),
        "skip": skip,
        "limit": limit
    }), 200

@assessments_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title', 'course_id', 'questions')
def create_assessment():
    data = sanitize_input(request.get_json())
    
    # Create new assessment
    assessment = Assessment.create(
        title=data.get('title'),
        course_id=data.get('course_id'),
        questions=data.get('questions')
    )
    
    return jsonify({
        "message": "Assessment created successfully",
        "assessment": assessment
    }), 201
