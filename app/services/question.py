from datetime import datetime, timezone
from bson import ObjectId
from app import db
from app.models.question import Question
from app.models.assessment import Assessment, AssessmentResult
from app.utils.validation import html_tags_converter, html_tags_unconverter
from config import Config

'''
Service class for managing questions and their association with assessments.
Provides methods to create, retrieve, update, delete, and manage questions,
as well as link/unlink questions to assessments.
'''
class QuestionService:
    '''
    Creates a new question and optionally associate it with assessments.
    Args:
        question_text (str): The text of the question.
        options (list): List of possible answer options.
        correct_answer (str): The correct answer.
        tags (list, optional): Tags for categorizing the question.
        assessment_ids (list, optional): List of assessment IDs to associate.
    Returns:
        dict: The created question object.
    '''
    @staticmethod
    def create_question(question_text, options, correct_answer, tags=None, assessment_ids=None):
        """Create a new question"""
        question = Question.create(
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            tags=tags,
            assessment_ids=assessment_ids,
        )
        return question

    '''
    Retrieves a question by its ID and convert HTML tags for display.
    Args:
        question_id (str): The ID of the question.
    Returns:
        dict or None: The question object if found, else None.
    '''
    @staticmethod
    def find_question_by_id(question_id):
        """Find a question by ID"""
        question = Question.find_by_id(question_id)

        if question is not None:
            for k, v in question.items():
                if k == '_id':
                    question[k] = str(v)
                elif k == 'correct_answer' or k == 'question_text':
                    question[k] = html_tags_unconverter(v)
                elif k == 'options' or k == 'tags':
                    question[k] = [html_tags_unconverter(option) for option in v]
            return question

        return None
    
    '''
    Retrieves multiple questions by their IDs.
    Args:
        question_ids (list): List of question IDs.
    Returns:
        list: List of question objects.
    '''
    @staticmethod
    def find_questions_by_ids(question_ids):
        # Convert string IDs to ObjectId
        object_ids = [ObjectId(qid) for qid in question_ids]

        # Use the Question model to fetch questions
        questions =  Question.find_by_ids(object_ids)

        if questions is not None or len(questions) > 0:
            for question in questions:
                for k, v in question.items():
                    if k == '_id':
                        question[k] = str(v)
                    elif k == 'correct_answer' or k == 'question_text':
                        question[k] = html_tags_unconverter(v)
                    elif k == 'options' or k == 'tags':
                        question[k] = [html_tags_unconverter(option) for option in v]
            
            return questions

        return []

    '''
    Retrieves questions that match any of the provided tags.
    Args:
        tags (list): List of tags to filter questions.
        limit (int, optional): Maximum number of questions to return.
        skip (int, optional): Number of questions to skip.
    Returns:
        list: List of question objects.
    '''
    @staticmethod
    def find_questions_by_tags(tags, limit=20, skip=0):
        """Find questions by tags"""
        questions = Question.find_by_tags(tags, limit, skip)

        if questions is not None or len(questions) > 0:
            for question in questions:
                for k, v in question.items():
                    if k == '_id':
                        question[k] = str(v)
                    elif k == 'correct_answer' or k == 'question_text':
                        question[k] = html_tags_unconverter(v)
                    elif k == 'options' or k == 'tags':
                        question[k] = [html_tags_unconverter(option) for option in v]
            
            return questions

        return []

    '''
    Retrieves all questions associated with a specific assessment.
    Args:
        assessment_id (str): The ID of the assessment.
    Returns:
        list: List of question objects.
    '''
    @staticmethod
    def find_questions_by_assessment_id(assessment_id):
        """Find questions by assessment ID"""
        questions = Question.find_by_assessment_id(assessment_id)

        if len(questions) > 0:
            for question in questions:
                for k, v in question.items():
                    if k == '_id':
                        question[k] = str(v)
                    elif k == 'correct_answer' or k == 'question_text':
                        question[k] = html_tags_unconverter(v)
                    elif k == 'options' or k == 'tags':
                        question[k] = [html_tags_unconverter(option) for option in v]
            return questions

        return []

    '''
    Retrieves all questions with pagination.
    Args:
        limit (int, optional): Maximum number of questions to return.
        skip (int, optional): Number of questions to skip.
    Returns:
        list: List of question objects.
    '''
    @staticmethod
    def find_all_questions(limit=20, skip=0):
        """Find all questions with pagination"""
        questions = Question.find_all(limit, skip)
        
        if questions is not None or len(questions) > 0:
            for question in questions:
                for k, v in question.items():
                    if k == '_id':
                        question[k] = str(v)
                    elif k == 'correct_answer' or k == 'question_text':
                        question[k] = html_tags_unconverter(v)
                    elif k == 'options' or k == 'tags':
                        question[k] = [html_tags_unconverter(option) for option in v]
      
            return questions

        return []

    '''
    Counts the total number of questions in the database.
    Returns:
        int: Total number of questions.
    '''
    @staticmethod
    def count_questions():
        return Question.count()

    '''
    Updates a question and update it in any assessment results if present.
    Args:
        question_id (str): The ID of the question to update.
        update_data (dict): Fields to update.
    Returns:
        dict or None: The updated question object if successful, else None.
    '''    
    @staticmethod
    def update_question(question_id, update_data):
        """Update a question and replace it in the assessment result if it exists"""
        updated_question = Question.update(question_id, update_data)
        if updated_question is not None:
            assessment_result = AssessmentResult.find_by_question_id(question_id)
        if assessment_result is not None:
            AssessmentResult.update_question(updated_question)
        return updated_question

    '''
    Deletes a question by its ID.
    Args:
        question_id (str): The ID of the question to delete.
    Returns:
        bool: True if deleted, False otherwise.
    '''
    @staticmethod
    def delete_question(question_id):
        """Delete a question"""
        return Question.delete(question_id)

    '''
    Associates a question with an assessment.
    Args:
        question_id (str): The ID of the question.
        assessment_id (str): The ID of the assessment.
    Returns:
        bool or None: True if added, None if question or assessment not found.
    '''
    @staticmethod
    def add_question_to_assessment(question_id, assessment_id):
        """Add a question to an assessment"""
        question = Question.find_by_id(question_id)
        if question is None:
            return None
        assessment = Assessment.find_by_id(assessment_id)
        if assessment is None:
            return None
        return Question.add_assessment_id(question_id, assessment_id)

    '''
    Removes the association between a question and an assessment.
    Args:
        question_id (str): The ID of the question.
        assessment_id (str): The ID of the assessment.
    Returns:
        bool or None: True if removed, None if question or assessment not found.
    '''
    @staticmethod
    def remove_question_from_assessment(question_id, assessment_id):
        """Remove a question from an assessment"""
        question = Question.find_by_id(question_id)
        if question is None:
            return None
        assessment = Assessment.find_by_id(assessment_id)
        if assessment is None:
            return None
        return Question.remove_assessment_id(question_id, assessment_id)
