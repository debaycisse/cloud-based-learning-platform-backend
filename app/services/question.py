from datetime import datetime, timezone
from bson import ObjectId
from app import db
from app.models.question import Question
from app.models.assessment import Assessment, AssessmentResult
from app.utils.validation import html_tags_converter, html_tags_unconverter
from config import Config

class QuestionService:
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
    
    @staticmethod
    def find_questions_by_ids(question_ids):
        """
        Find multiple questions by their IDs.

        Args:
            question_ids (list): List of question IDs.

        Returns:
            list: List of question objects.
        """
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
    
    @staticmethod
    def count_questions():
        """Count total number of all questions"""
        return Question.count()
    
    @staticmethod
    def update_question(question_id, update_data):
        """Update a question and replace it in the assessment result if it exists"""
        updated_question = Question.update(question_id, update_data)
        if updated_question is not None:
            assessment_result = AssessmentResult.find_by_question_id(question_id)
        if assessment_result is not None:
            AssessmentResult.update_question(updated_question)
        return updated_question
    
    @staticmethod
    def delete_question(question_id):
        """Delete a question"""
        return Question.delete(question_id)
    
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
