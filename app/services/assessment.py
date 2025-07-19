from dateutil import parser
from datetime import datetime, timedelta, timezone
from app import db
from app.models.assessment import Assessment, AssessmentResult
from app.models.question import Question
from app.models.concept_link import ConceptLinks
from app.utils.validation import html_tags_unconverter
from app.utils.json_conversion import json_converter
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
        - Failed assessments whose cooldown period has not expired cannot be retaken
        """
        latest_result = AssessmentResult.find_latest_by_user_and_assessment(
            user_id, assessment_id
        )
        
        if latest_result is None:
            return True, None

        if latest_result.get('passed', False):
            return False, "You have already passed this assessment"
        
        cooldown_hours = Config.ASSESSMENT_COOLDOWN_HOURS
        cooldown_time = datetime.fromisoformat(
            latest_result['created_at']
        ) + timedelta(hours=cooldown_hours)
        
        if datetime.now(timezone.utc) < cooldown_time:
            hours_remaining = (
                cooldown_time - datetime.now(timezone.utc)
            ).total_seconds() / 3600
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
            # find the question
            question = Question.find_by_id(question_id=question)
            if i < len(answers) and answers[i] == question.get('correct_answer'):
                correct_answers += 1
                demonstrated_strengths.extend(question.get('tags', []))
            else:
                knowledge_gaps.extend(question.get('tags', []))
        
        # Remove duplicates
        knowledge_gaps = list(
            set(
                [html_tags_unconverter(kw_gap) for kw_gap in knowledge_gaps]
            )
        )
        
        demonstrated_strengths = list(
            set(
                [html_tags_unconverter(ds) for ds in demonstrated_strengths]
            )
        )
        
        score = correct_answers / total_questions if total_questions > 0 else 0
        passed = score >= Config.ASSESSMENT_PASS_THRESHOLD
        
        return {
            'score': score,
            'passed': passed,
            'knowledge_gaps': knowledge_gaps,
            'demonstrated_strengths': demonstrated_strengths
        }
    
    @staticmethod
    def submit_assessment(user_id, assessment_id, answers, started_at, questions_id):
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
        
        questions = [Question.find_by_id(question_id) for question_id in questions_id]

        # Store the result
        assessment_result = AssessmentResult.create(
            user_id=user_id,
            assessment_id=assessment_id,
            answers=answers,
            score=result['score'],
            passed=result['passed'],
            knowledge_gaps=result['knowledge_gaps'],
            demonstrated_strengths=result['demonstrated_strengths'],
            started_at=parser.isoparse(started_at).isoformat(),
            questions=questions,
        )
        
        return assessment_result, None
    
    @staticmethod
    def add_question(assessment_id, question_id):
        '''
        Adds question to assessment
        - CHecks if the question exists
        - Checks if the assessment exists
        '''
        assessment = Assessment.find_by_id(assessment_id)

        if not assessment:
            return None

        question = Question.find_by_id(question_id)

        if not question:
            return None
        
        # Update the questions (array) field of the assessment
        updated_data = {
            'questions': assessment.get('questions', []) + [question_id]
        }

        # Update the assessment with the updated data
        updated_assessment = Assessment.update(assessment_id, updated_data)

        if updated_assessment:
            return True
        return False

    @staticmethod
    def obtain_advice_links(knowledge_gaps):
        """
        Obtains advice links for knowledge gaps using each
        given knowledge gap in the list.
        Args:
            knowledge_gaps: A list of knowledge gaps to find resources for.
        Returns:
            A list of dictionaries containing the description, URL, title,
            and tags for each knowledge gap. Returns None if an error occurs.
        """
        links = []
        try:
            for gap in knowledge_gaps:
                link_data = ConceptLinks.search(
                    query=gap,
                    skip=0,
                    limit=1
                )
                link_data_formatted = {}
                if link_data:
                    for k, v in link_data.items():
                        if isinstance(v, str):
                            link_data_formatted[k] = html_tags_unconverter(v)
                        elif isinstance(v, list):
                            link_data_formatted[k] = [
                                html_tags_unconverter(item) for item in v
                            ]
                        else:
                            link_data_formatted[k] = str(v)
                    link_obj = {
                        'description': link_data_formatted.get('description', ''),
                        'url': link_data_formatted.get('links', ['']),
                        'title': gap,
                        'tags': link_data_formatted.get('concepts', [])
                    }
                    links.append(link_obj)
                else:
                    links.append({
                        'description': f'No resources found for {gap}',
                        'url': '',
                        'title': gap,
                        'tags': [gap]
                    })
            return links
        except Exception as e:
            return None
