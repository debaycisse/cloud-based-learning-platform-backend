from dateutil import parser
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.utils.swagger_utils import yaml_from_file
from app.models.assessment import Assessment, AssessmentResult
from app.services.assessment import AssessmentService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input

assessments_bp = Blueprint('assessments', __name__)

@assessments_bp.route('/<assessment_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/assessments/get_assessment.yaml')
def get_an_assessment(assessment_id):
    try:
        assessments = Assessment.find_by_id(assessment_id)
        
        if not assessments:
            return jsonify({"error": "No assessments found for the given ID"}), 404
        
        # For security, remove correct answers from the response
        # for assessment in assessments:
        #     for question in assessment.get('questions', []):
        #         question.pop('correct_answer', None)
        
        return jsonify({
            "assessment": {
                "_id": str(assessments['_id']),
                "title": assessments['title'],
                "course_id": assessments['course_id'],
                "questions": assessments.get('questions', []),
                "time_limit": assessments.get('time_limit', 25),  # Default time limit in minutes
                "created_at": assessments.get('created_at'),
                "updated_at": assessments.get('updated_at')
            }
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

'''
Get all assessments with pagination
- Parameters:
    - limit: Number of assessments to return (default: 20)
    - skip: Number of assessments to skip (default: 0)
- Returns:
    - assessments: List of assessments
    - count: Total number of assessments
    - skip: Number of assessments skipped
    - limit: Number of assessments returned
'''
@assessments_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/assessments/get_assessments_admin.yaml')
def get_assessments():
    try:
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        
        # Get all assessments with pagination
        assessments = Assessment.find_all(limit, skip)
        
        return jsonify({
            "assessments": assessments,
            "count": len(assessments),
            "skip": skip,
            "limit": limit
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@assessments_bp.route('/course/<course_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/assessments/get_course_assessments.yaml')
def get_assessment_for_course(course_id):
    try:
        assessments = Assessment.find_by_course_id(course_id)
        
        if not assessments:
            return jsonify({"error": "No assessments found for this course"}), 404
        
        
        return jsonify({"assessments": assessments}), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@assessments_bp.route('/<assessment_id>/submit', methods=['POST'])
@jwt_required()
@validate_json('answers', 'started_at', 'questions_id')
@yaml_from_file('docs/swagger/assessments/submit_assessment.yaml')
def submit_assessment(assessment_id):
    try:
        user_id = get_jwt_identity()
        data = sanitize_input(request.get_json())
        answers = data.get('answers')
        started_at = data.get('started_at')
        questions_id = data.get('questions_id')

        # Submit and score the assessment
        result, error_message = AssessmentService.submit_assessment(
            user_id, assessment_id, answers, started_at, questions_id
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

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@assessments_bp.route('/results', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/assessments/get_assessment_results.yaml')
def get_assessment_results():
    try:
        user_id = get_jwt_identity()
        limit = int(request.args.get('limit', 20))
        skip = request.args.get('skip', 0)
        
        if not user_id:
            return jsonify({"error": "Invalid or missing user ID"}), 400

        # Get assessment results for the user
        results = AssessmentResult.find_by_user(user_id, limit, skip)
        if results is None or len(results) < 1:
            return jsonify({
                'error': 'No result found'
            }), 404
        
        return jsonify({
            "results": results,
            "count": len(results),
            "skip": skip,
            "limit": limit
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# # Get a single assessment result
# @assessments_bp.route('/results/<assessment_result_id>', methods=['GET'])
# @jwt_required()
# @yaml_from_file('docs/swagger/assessments/get_assessment_result.yaml')
# def get_assessment_result(assessment_result_id):

#     result = AssessmentResult.find_by_id(assessment_result_id)
    
#     if not result:
#         return jsonify({"error": "Assessment result not found"}), 404
    
#     return jsonify({"result": result}), 200

@assessments_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title', 'time_limit', 'course_id')
@yaml_from_file('docs/swagger/assessments/create_assessment_admin_only.yaml')
def create_assessment():
    try:
        data = sanitize_input(request.get_json())

        # Create new assessment
        assessment = Assessment.create(
            title=data.get('title'),
            time_limit=data.get('time_limit', 25),
            course_id=data.get('course_id'),
        )
        assessment['_id'] = str(assessment['_id'])
        
        return jsonify({
            "message": "Assessment created successfully",
            "assessment": assessment
        }), 201
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@assessments_bp.route('/<assessment_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('title', 'course_id')
@yaml_from_file('docs/swagger/assessments/update_assessment_admin_only.yaml')
def update_assessment(assessment_id):
    try:
        data = sanitize_input(request.get_json())
        
        update_data = {
            'title': data.get('title'),
            'time_limit': data.get('time_limit', 25),
            'course_id': data.get('course_id'),
        }

        # Update assessment
        assessment = Assessment.update(
            assessment_id,
            update_data,
        )
        
        if assessment is None:
            return jsonify({"error": "Assessment not found"}), 404
        
        return jsonify({
            "message": "Assessment updated successfully",
            "assessment": assessment
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500


@assessments_bp.route('/<assessment_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/assessments/delete_assessment_admin_only.yaml')
def delete_assessment(assessment_id):
    try:
        # Delete assessment    
        if not Assessment.delete(assessment_id):
            return jsonify({"error": "Assessment not found"}), 404
        
        # After an assessment has been deleted, delete all results associated with it and confirm deletion
        if not AssessmentResult.delete_by_assessment_id(assessment_id):
            return jsonify({"error": "Failed to delete associated assessment results"}), 500
        
        return jsonify({
            "message": "Assessment deleted successfully"
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

'''
Gets assessment result"s average score
- Parameters:
    - assessment_id: ID of the assessment result
- Returns:
    - average_score: Average score of the assessment result
'''
@assessments_bp.route('/<assessment_id>/average_score', methods=['GET'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/assessments/get_assessment_average_score.yaml')
def get_assessment_average_score(assessment_id):
    try:
        # Get average score for the assessment
        average_score = AssessmentResult.find_average_score(assessment_id)
        
        if average_score is None:
            return jsonify({"error": "No results found for this assessment"}), 404
        
        return jsonify({
            "average_score": average_score
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
