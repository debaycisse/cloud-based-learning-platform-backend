from datetime import datetime
from app import db

assessments_collection = db.assessments
results_collection = db.results

'''
Assessment Model
- Represents an assessment in the system
- Contains methods to create, find, and update assessments
- Fields in a typical document:
    - title: Title of the assessment
    - course_id: ID of the course associated with the assessment
    - questions: List of questions in the assessment
    - created_at: Timestamp when the assessment was created
    - updated_at: Timestamp when the assessment was last updated
'''
class Assessment:
    @staticmethod
    def create(title, course_id, questions):
        """Create a new assessment"""
        assessment = {
            'title': title,
            'course_id': course_id,
            'questions': questions,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = assessments_collection.insert_one(assessment)
        assessment['_id'] = result.inserted_id
        return assessment
    
    @staticmethod
    def find_by_id(assessment_id):
        """Find an assessment by ID"""
        return assessments_collection.find_one({'_id': assessment_id})
    
    @staticmethod
    def find_by_course_id(course_id):
        """Find assessments for a specific course"""
        cursor = assessments_collection.find({'course_id': course_id})
        return list(cursor)
    
    @staticmethod
    def update(assessment_id, update_data):
        """Update an assessment"""
        update_data['updated_at'] = datetime.utcnow()
        assessments_collection.update_one(
            {'_id': assessment_id},
            {'$set': update_data}
        )
        return assessments_collection.find_one({'_id': assessment_id})

'''
Assessment Result Model
- Represents a user's result for an assessment
- Contains methods to create, find, and update assessment results
- Fields in a typical document:
    - user_id: ID of the user who took the assessment
    - assessment_id: ID of the assessment
    - answers: List of answers provided by the user
    - score: Score obtained by the user
    - passed: Boolean indicating if the user passed the assessment
    - knowledge_gaps: List of knowledge gaps identified in the assessment
    - created_at: Timestamp when the result was created
'''
class AssessmentResult:
    @staticmethod
    def create(user_id, assessment_id, answers, score, passed, knowledge_gaps=None, demonstrated_strengths=None):
        """Create a new assessment result with demonstrated strengths"""
        result = {
            'user_id': user_id,
            'assessment_id': assessment_id,
            'answers': answers,
            'score': score,
            'passed': passed,
            'knowledge_gaps': knowledge_gaps or [],
            'demonstrated_strengths': demonstrated_strengths or [],
            'created_at': datetime.utcnow()
        }
        result_id = results_collection.insert_one(result).inserted_id
        result['_id'] = result_id
        return result
    
    @staticmethod
    def find_by_user(user_id, limit=20, skip=0):
        """Find assessment results for a specific user"""
        cursor = results_collection.find({'user_id': user_id}).sort(
            'created_at', -1
        ).skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def find_by_assessment(assessment_id, limit=20, skip=0):
        """Find results for a specific assessment"""
        cursor = results_collection.find({'assessment_id': assessment_id}).sort(
            'created_at', -1
        ).skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def find_latest_by_user_and_assessment(user_id, assessment_id):
        """Find the latest result for a user and assessment"""
        return results_collection.find_one(
            {'user_id': user_id, 'assessment_id': assessment_id},
            sort=[('created_at', -1)]
        )
