from datetime import datetime, timedelta, timezone
from app import db
from app.models.assessment import Assessment, AssessmentResult
from config import Config

class AssessmentService:
    @staticmethod
    def get_assessment_for_course(course_id):
        """Get the prerequisite assessment for a course"""
        return Assessment.find_by_course_id(course_id)
    
    @staticmethod
    def can_take_assessment(user_id, assessment_id):
        """
        Check if a user can take an assessment
        - Users can't retake a passed assessment
        - Failed assessments have a cooldown period
        """
        latest_result = AssessmentResult.find_latest_by_user_and_assessment(
            user_id, assessment_id
        )
        
        if not latest_result:
            return True, None
        
        if latest_result.get('passed', False):
            return False, "You have already passed this assessment"
        
        cooldown_hours = Config.ASSESSMENT_COOLDOWN_HOURS
        cooldown_time = latest_result['created_at'] + timedelta(hours=cooldown_hours)
        
        if datetime.now(timezone.utc) < cooldown_time:
            hours_remaining = (cooldown_time - datetime.now(timezone.utc)).total_seconds() / 3600
            return False, f"You can retake this assessment in {int(hours_remaining)} hours"
        
        return True, None
    
    @staticmethod
    def score_assessment(assessment_id, answers):
        """
        Score an assessment based on submitted answers
        Returns:
        - score: percentage of correct answers
        - passed: boolean indicating if the score meets the passing threshold
        - knowledge_gaps: list of concepts the user needs to improve on
        - demonstrated_strengths: list of concepts the user has demonstrated proficiency in
        """
        assessment = Assessment.find_by_id(assessment_id)
        if not assessment:
            return None
        
        questions = assessment.get('questions', [])
        total_questions = len(questions)
        correct_answers = 0
        knowledge_gaps = []
        demonstrated_strengths = []
        
        for i, question in enumerate(questions):
            if i < len(answers) and answers[i] == question.get('correct_answer'):
                correct_answers += 1
                # Add the concepts related to this question to demonstrated strengths
                demonstrated_strengths.extend(question.get('concepts', []))
            else:
                # Add the concepts related to this question to knowledge gaps
                knowledge_gaps.extend(question.get('concepts', []))
        
        # Remove duplicates
        knowledge_gaps = list(set(knowledge_gaps))
        demonstrated_strengths = list(set(demonstrated_strengths))
        
        score = correct_answers / total_questions if total_questions > 0 else 0
        passed = score >= Config.ASSESSMENT_PASS_THRESHOLD
        
        return {
            'score': score,
            'passed': passed,
            'knowledge_gaps': knowledge_gaps,
            'demonstrated_strengths': demonstrated_strengths
        }
    
    @staticmethod
    def submit_assessment(user_id, assessment_id, answers):
        """
        Submit and score an assessment
        - Checks if the user can take the assessment
        - Scores the assessment
        - Stores the result
        - Returns the result with recommendations
        """
        can_take, message = AssessmentService.can_take_assessment(user_id, assessment_id)
        if not can_take:
            return None, message
        
        result = AssessmentService.score_assessment(assessment_id, answers)
        if not result:
            return None, "Assessment not found"
        
        # Store the result
        assessment_result = AssessmentResult.create(
            user_id=user_id,
            assessment_id=assessment_id,
            answers=answers,
            score=result['score'],
            passed=result['passed'],
            knowledge_gaps=result['knowledge_gaps'],
            demonstrated_strengths=result['demonstrated_strengths']
        )
        
        return assessment_result, None
