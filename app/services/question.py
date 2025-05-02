from datetime import datetime, timezone
from app import db
from app.models.question import Question
from app.models.assessment import Assessment
from config import Config

class QuestionService:
    @staticmethod
    def create_question(question_text, options, correct_answer, tags=None):
        """Create a new question"""
        question = Question.create(
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            tags=tags
        )
        return question

    @staticmethod
    def find_question_by_id(question_id):
        """Find a question by ID"""
        return Question.find_by_id(question_id)

    @staticmethod
    def find_questions_by_tags(tags, limit=20, skip=0):
        """Find questions by tags"""
        return Question.find_by_tags(tags, limit, skip)

    @staticmethod
    def find_questions_by_assessment_id(assessment_id):
        """Find questions by assessment ID"""
        return Question.find_by_assessment_id(assessment_id)
    
    @staticmethod
    def find_all_questions(limit=20, skip=0):
        """Find all questions with pagination"""
        return Question.find_all(limit, skip)
    
    @staticmethod
    def update_question(question_id, update_data):
        """Update a question"""
        return Question.update(question_id, update_data)
    
    @staticmethod
    def delete_question(question_id):
        """Delete a question"""
        return Question.delete(question_id)
    
    @staticmethod
    def add_question_to_assessment(question_id, assessment_id):
        """Add a question to an assessment"""
        question = Question.find_by_id(question_id)
        if not question:
            return None
        assessment = Assessment.find_by_id(assessment_id)
        if not assessment:
            return None
        return Question.add_assessment_id(question_id, assessment_id)
    
    @staticmethod
    def remove_question_from_assessment(question_id, assessment_id):
        """Remove a question from an assessment"""
        question = Question.find_by_id(question_id)
        if not question:
            return None
        assessment = Assessment.find_by_id(assessment_id)
        if not assessment:
            return None
        return Question.remove_assessment_id(question_id, assessment_id)
