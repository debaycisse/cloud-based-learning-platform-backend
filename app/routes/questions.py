from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.swagger_utils import yaml_from_file
from app.models.question import Question
from app.services.assessment import AssessmentService
from app.services.question import QuestionService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/<question_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/questions/get_question.yaml')
def get_a_question(question_id):
    question = QuestionService.find_question_by_id(question_id)
    
    if not question:
        return jsonify({"error": "No question found for the given ID"}), 404
    
    # For security, remove correct answer from the response
    # question.pop('correct_answer', None)
    
    return jsonify({
        "question": {
            "_id": str(question['_id']),
            "question_text": question['question_text'],
            "options": question['options'],
            "correct_answer": question['correct_answer'],
            "tags": question.get('tags', []),
            "assessment_ids": question.get('assessment_ids', []),
            "created_at": question.get('created_at'),
            "updated_at": question.get('updated_at')
        }
    }), 200 

@questions_bp.route('/bulk', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('question_ids')  # Ensure 'question_ids' is present in the request body
# @yaml_from_file('docs/swagger/questions/get_questions_bulk.yaml')
def get_questions_bulk():
    """
    Fetch a list of questions by their IDs.
    """
    data = sanitize_input(request.get_json())  # Sanitize input data
    question_ids = data.get('question_ids')  # Extract the array of question IDs

    # Validate input
    if not question_ids or not isinstance(question_ids, list):
        return jsonify({"error": "question_ids must be a non-empty array"}), 400

    # Fetch questions by their IDs
    questions = QuestionService.find_questions_by_ids(question_ids)

    # If no questions are found
    if not questions:
        return jsonify({"error": "No questions found for the given IDs"}), 404

    # Format the response
    formatted_questions = [
        {
            "_id": str(question['_id']),
            "question_text": question['question_text'],
            "options": question['options'],
            "correct_answer": question['correct_answer'],
            "tags": question.get('tags', []),
            "assessment_ids": question.get('assessment_ids', []),
            "created_at": question.get('created_at'),
            "updated_at": question.get('updated_at')
        }
        for question in questions
    ]

    return jsonify({
        "questions": formatted_questions,
        "count": len(formatted_questions)
    }), 200

'''
Get all questions with pagination
- Parameters:
    - limit: Number of questions to return (default: 20)
    - skip: Number of questions to skip (default: 0)
- Returns:
    - questions: List of questions
    - count: Total number of questions
    - skip: Number of questions skipped
    - limit: Number of questions returned
'''
@questions_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/questions/get_questions_admin.yaml')
def get_questions():
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    # Get all questions with pagination
    questions = QuestionService.find_all_questions(limit, skip)

    if not questions:
        return jsonify({"error": "No questions found"}), 404
    
    return jsonify({
        "questions": questions,
        "count": len(questions),
        "skip": skip,
        "limit": limit
    }), 200

@questions_bp.route('/tags', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/questions/get_questions_by_tags.yaml')
def get_questions_by_tags():
    tags = request.args.getlist('tags')
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    # Validate tags
    if not tags:
        return jsonify({"error": "Tags are required"}), 400
    
    # Get questions by tags with pagination
    questions = QuestionService.find_questions_by_tags(tags, limit, skip)
    
    if not questions:
        return jsonify({"error": "No questions found for the given tags"}), 404
    
    return jsonify({
        "questions": questions,
        "count": len(questions),
        "skip": skip,
        "limit": limit
    }), 200

@questions_bp.route('/assessment/<assessment_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/questions/get_questions_by_assessment.yaml')
def get_questions_by_assessment(assessment_id):
    # limit = int(request.args.get('limit', 20))
    # skip = int(request.args.get('skip', 0))
    questions = QuestionService.find_questions_by_assessment_id(assessment_id)
    # questions = []
    # for question in cursor:
    #     question['_id'] = str(question['_id'])
    #     questions.append(question)
    
    if not questions:
        return jsonify({"error": "No questions found for the given assessment ID"}), 404
    
    return jsonify({
        "questions": questions
    }), 200

'''Gets questions by assessment id and tags
- Parameters:
    - assessment_id: ID of the assessment
    - tags: List of tags to filter questions
- Returns:
    - questions: List of questions that match the assessment ID and tags
    - count: Total number of questions
    - skip: Number of questions skipped
    - limit: Number of questions returned
'''
@questions_bp.route('/assessment/<assessment_id>/tags', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/questions/get_questions_by_assessment_and_tags.yaml')
def get_questions_by_assessment_and_tags(assessment_id):
    tags = request.args.getlist('tags')
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    
    # Validate tags
    if not tags:
        return jsonify({"error": "Tags are required"}), 400
    
    # Get questions by assessment ID and tags with pagination
    questions = QuestionService.find_questions_by_assessment_id(assessment_id)
    
    if not questions:
        return jsonify({"error": "No questions found for the given assessment ID"}), 404
    
    # Filter questions by tags
    filtered_questions = [q for q in questions if any(tag in q.get('tags', []) for tag in tags)]
    
    return jsonify({
        "questions": filtered_questions,
        "count": len(filtered_questions),
        "skip": skip,
        "limit": limit
    }), 200

@questions_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('question')
@yaml_from_file('docs/swagger/questions/create_question.yaml')
def create_question():
    data = sanitize_input(request.get_json())
    question_text = data.get('question_text')
    options = data.get('options')
    correct_answer = data.get('correct_answer')
    tags = data.get('tags', [])
    
    # Validate input
    if not question_text or not options or not correct_answer:
        return jsonify({"error": "Question text, options, and correct answer are required"}), 400
    
    # Create a new question
    question = QuestionService.create_question(
        question_text=question_text,
        options=options,
        correct_answer=correct_answer,
        tags=tags
    )
    
    return jsonify({
        "message": "Question created successfully",
        "question": {
            "id": str(question['_id']),
            "question_text": question['question_text'],
            "options": question['options'],
            "correct_answer": question['correct_answer'],
            "tags": question.get('tags', []),
            "assessment_ids": question.get('assessment_ids', []),
            "created_at": question.get('created_at').isoformat() if question.get('created_at') else None,
            "updated_at": question.get('updated_at').isoformat() if question.get('updated_at') else None
        }
    }), 201

# endpoint that creates questions by interating over a list of questions
@questions_bp.route('/bulk/<assessment_id>', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('questions')
@yaml_from_file('docs/swagger/questions/create_questions.yaml')
def create_questions(assessment_id):
    data = sanitize_input(request.get_json())
    questions_data = data.get('questions')
    
    # Validate input
    if not questions_data:
        return jsonify({"error": "Questions data is required"}), 400
    
    # Create multiple questions
    questions = []
    for question_data in questions_data:
        question_text = question_data.get('question_text')
        options = question_data.get('options')
        correct_answer = question_data.get('correct_answer')
        tags = question_data.get('tags', [])
        
        # Validate input
        if not question_text or not options or not correct_answer:
            return jsonify({"error": "Question text, options, and correct answer are required"}), 400
        
        question = QuestionService.create_question(
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            tags=tags,
            assessment_ids=[assessment_id],
        )
        questions.append(question)
    # Add assessment's id to multiple questions
    for question in questions:
        if not AssessmentService.add_question(assessment_id, str(question['_id'])):
            return jsonify({
                "error": "Error occured while adding questions to assessment"
            })
        question['_id'] = str(question['_id'])

    return jsonify({
        "message": "Questions created successfully",
        "questions": questions,
    }), 201

@questions_bp.route('/<question_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('question')
@yaml_from_file('docs/swagger/questions/update_question.yaml')
def update_question(question_id):
    data = sanitize_input(request.get_json())
    question_text = data.get('question_text')
    options = data.get('options')
    correct_answer = data.get('correct_answer')
    tags = data.get('tags', [])
    
    # Validate input
    if not question_text or not options or not correct_answer:
        return jsonify({"error": "Question text, options, and correct answer are required"}), 400
    
    # Update the question
    question = QuestionService.update_question(
        question_id=question_id,
        update_data={
            'question_text': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'tags': tags
        }
    )
    
    if not question:
        return jsonify({"error": "No question found for the given ID"}), 404
    
    return jsonify({
        "message": "Question updated successfully",
        "question": {
            "id": str(question['_id']),
            "question_text": question['question_text'],
            "options": question['options'],
            "correct_answer": question['correct_answer'],
            "tags": question.get('tags', []),
            "assessment_ids": question.get('assessment_ids', []),
            "created_at": question.get('created_at').isoformat() if question.get('created_at') else None,
            "updated_at": question.get('updated_at').isoformat() if question.get('updated_at') else None
        }
    }), 200

@questions_bp.route('/<question_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/questions/delete_question.yaml')
def delete_question(question_id):
    # Delete the question
    result = QuestionService.delete_question(question_id)
    
    if not result:
        return jsonify({"error": "No question found for the given ID"}), 404
    
    return jsonify({
        "message": "Question deleted successfully"
    }), 200

@questions_bp.route('/<question_id>/assessments/<assessment_id>', methods=['POST'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/questions/add_question_to_assessment.yaml')
def add_question_to_assessment(question_id, assessment_id):
    # Add question to assessment
    result = QuestionService.add_question_to_assessment(question_id, assessment_id)
    
    if not result:
        return jsonify({"error": "No question found for the given ID"}), 404
    
    # Find the given assessment and add the question id to its questions attribute, which is an array that contains quetions' ids
    assessment = AssessmentService.add_question(assessment_id, question_id)

    if not assessment:
        return jsonify({
            "error": "Question or assessment does not exist"
        })
    
    return jsonify({
        "message": "Question added to assessment successfully"
    }), 200

@questions_bp.route('/<question_id>/assessment/<assessment_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/questions/remove_question_from_assessment.yaml')
def remove_question_from_assessment(question_id, assessment_id):
    # Remove question from assessment
    result = QuestionService.remove_question_from_assessment(question_id, assessment_id)
    
    if not result:
        return jsonify({"error": "No question found for the given ID"}), 404
    
    return jsonify({
        "message": "Question removed from assessment successfully"
    }), 200
