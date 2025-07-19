from dateutil import parser
from datetime import datetime, timedelta, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.utils.swagger_utils import yaml_from_file
from app.utils.cooldown_manager import manage_cooldown
from app.models.assessment import Assessment, AssessmentResult
from app.models.cooldown_history import CooldownHistory
from app.models.user import User
from app.services.assessment import AssessmentService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input
from config import Config

assessments_bp = Blueprint('assessments', __name__)

@assessments_bp.route('/<assessment_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/assessments/get_assessment.yaml')
def get_an_assessment(assessment_id):
    try:
        user_id = get_jwt_identity()
        if user_id:
            manage_cooldown(user_id=user_id)

        assessments = Assessment.find_by_id(assessment_id)
        
        if not assessments:
            return jsonify({"error": "No assessments found for the given ID"}), 404
        
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
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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

        user_id = get_jwt_identity()
        if user_id:
            manage_cooldown(user_id=user_id)
        
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
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@assessments_bp.route('/course/<course_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/assessments/get_course_assessments.yaml')
def get_assessment_for_course(course_id):
    try:
        user_id = get_jwt_identity()
        if user_id:
            manage_cooldown(user_id=user_id)

        assessments = Assessment.find_by_course_id(course_id)
        
        if not assessments:
            return jsonify({"error": "No assessments found for this course"}), 404
        
        
        return jsonify({"assessments": assessments}), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


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
        
        # Place cooldown object in the user's document if the score is less than 50%
        if result['score'] < 50:
            cool_down_hour = timedelta(hours=Config.ASSESSMENT_COOLDOWN_HOURS)
            current_time = datetime.now(timezone.utc)
            cooldown_duration = current_time + cool_down_hour
            knowledge_gaps = result.get('knowledge_gaps', [])
            assessment = Assessment.find_by_id(assessment_id)
            course_id = assessment.get('course_id')

            # Add the cooldown history for the user and add the cooldown object to the user's document
            if CooldownHistory.find_by_user(user_id) is None:
                cooldown_history = CooldownHistory.create(
                    user_id=user_id,
                    course_id=course_id,
                    cooldown_duration=cooldown_duration,
                    knowledge_gaps=knowledge_gaps
                )

                if cooldown_history is None:
                    return jsonify({"error": "Failed to create cooldown history"}), 500

            else:
                cooldown_history = CooldownHistory.update_cooldown_history(
                    user_id=user_id,
                    course_id=course_id,
                    knowledge_gaps=knowledge_gaps
                )

                if not cooldown_history:
                    return jsonify({"error": "Failed to update cooldown history"}), 500

            # Insert the cooldown object in the user document
            User.update_profile(user_id=user_id, update_data={
                'cooldown': {
                    'duration': cooldown_duration.isoformat(),
                    'course_id': course_id,
                    'concepts': knowledge_gaps,
                },
            })
        
        return jsonify({
            "message": "Assessment submitted successfully",
            "result": {
                "_id": str(result['_id']),
                "score": result['score'],
                "passed": result['passed'],
                "knowledge_gaps": result['knowledge_gaps']
            }
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
        
        manage_cooldown(user_id=user_id)

        # Get assessment results for the user
        results = AssessmentResult.find_by_user(user_id, limit, skip)
        
        return jsonify({
            "results": results,
            "count": len(results),
            "skip": skip,
            "limit": limit
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@assessments_bp.route('/results/<course_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/assessments/get_assessment_result_by_course_id.yaml')
def get_assessment_result_by_course_id(course_id):
    try:
        user_id = get_jwt_identity()

        if not user_id:
            return jsonify({"error": "Invalid or missing user ID"}), 400
        
        manage_cooldown(user_id=user_id)
        
        result = AssessmentResult.find_by_course_and_user_id(course_id=course_id, user_id=user_id)

        if result is None:
            return jsonify({
                "result": None,
                "count": 0
            }), 200

        return jsonify({
            "result": result,
            "count": len(result),
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@assessments_bp.route('/<assessment_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/assessments/delete_assessment_admin_only.yaml')
def delete_assessment(assessment_id):
    try:
        # Delete assessment    
        if not Assessment.delete(assessment_id):
            return jsonify({"error": "Assessment not found"}), 404
        
        # After an assessment has been deleted, delete all results and questions associated with it.
        if not AssessmentResult.delete_by_assessment_id(assessment_id):
            return jsonify({"error": "Failed to delete associated assessment results"}), 500
        
        return jsonify({
            "message": "Assessment deleted successfully"
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

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
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
Gets link for each concept in the knowledge gaps of an assessment result
- Parameters:
    - course_id: course ID of the course that uses the assessment
- Returns:
    - links: List of links for each concept in the knowledge gaps
'''    
@assessments_bp.route('/<course_id>/advice', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/assessments/get_assessment_advice.yaml')
def get_assessment_advice(course_id):
    try:
        user_id = get_jwt_identity()

        manage_cooldown(user_id=user_id)

        # Get the assessment result
        assessment_result = AssessmentResult.find_by_course_and_user_id(course_id=course_id, user_id=user_id)

        if not assessment_result:
            return jsonify({"error": "Assessment result not found"}), 404
        
        # Get the knowledge gaps from the assessment result
        knowledge_gaps = assessment_result.get('knowledge_gaps', [])
        
        if not knowledge_gaps:
            return jsonify({"message": "No knowledge gaps found"}), 200
        
        # Get advice links for the knowledge gaps
        link_data_list = AssessmentService.obtain_advice_links(knowledge_gaps=knowledge_gaps)
        if not link_data_list:
            return jsonify({"message": "No links found for the knowledge gaps"}), 404
        
        return jsonify({
            "links": link_data_list
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
