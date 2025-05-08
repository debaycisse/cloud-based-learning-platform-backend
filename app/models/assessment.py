from datetime import datetime, timezone
from bson import ObjectId
from app import db

assessments_collection = db.assessments
results_collection = db.results
questions_collection = db.questions

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
    def create(title, course_id, time_limit=25):
        """Create a new assessment"""
        assessment = {
            'title': title,
            'course_id': course_id,
            'time_limit': time_limit,  # Default time limit in minutes
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        result = assessments_collection.insert_one(assessment)
        assessment['_id'] = result.inserted_id
        return assessment
    
    @staticmethod
    def find_by_id(assessment_id):
        """Find an assessment by ID"""
        return assessments_collection.find_one({'_id': ObjectId(assessment_id)})
    
    @staticmethod
    def find_by_course_id(course_id):
        """Find assessments for a specific course"""
        cursor = assessments_collection.find({'course_id': course_id})
        return list(cursor)
    
    @staticmethod
    def find_all(limit=20, skip=0):
        """Find all assessments with pagination"""
        cursor = assessments_collection.find().sort('created_at', -1).skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def update(assessment_id, update_data):
        """Update an assessment"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        assessments_collection.update_one(
            {'_id': ObjectId(assessment_id)},
            {'$set': update_data}
        )
        return assessments_collection.find_one({'_id': ObjectId(assessment_id)})
    
    @staticmethod
    def delete(assessment_id):
        """Delete an assessment"""
        result = assessments_collection.delete_one({'_id': ObjectId(assessment_id)})
        return result.deleted_count > 0

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
    def create(user_id, assessment_id, answers, score, passed, started_at,
               questions, knowledge_gaps=None, demonstrated_strengths=None):
        """Create a new assessment result with demonstrated strengths"""
        result = {
            'user_id': user_id,
            'assessment_id': assessment_id,
            'answers': answers,
            'score': score,
            'passed': passed,
            'knowledge_gaps': knowledge_gaps or [],
            'demonstrated_strengths': demonstrated_strengths or [],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': datetime.now(timezone.utc).isoformat(),
            'started_at': datetime.fromisoformat(started_at).isoformat(),
            'time_spent': (datetime.now(timezone.utc) - datetime.fromisoformat(started_at)).total_seconds() / 60,
            'questions': questions,
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
    
    '''
    Finds the average score for a specific assessment
    Args:
        assessment_id (str): ID of the assessment
    Returns:
        float: Average score of the assessment
    '''
    @staticmethod
    def find_average_score(assessment_id):
        """Find the average score for a specific assessment"""
        pipeline = [
            {'$match': {'assessment_id': assessment_id}},
            {'$group': {
                '_id': None,
                'average_score': {'$avg': '$score'}
            }}
        ]
        result = results_collection.aggregate(pipeline)
        return list(result)[0]['average_score'] if result else 0.0
    
    # Delete an assessment result
    @staticmethod
    def delete_by_assessment_id(assessment_result_id):
        """Delete an assessment result"""
        result = results_collection.delete_one({'_id': ObjectId(assessment_result_id)})
        if result.deleted_count > 0:
            # Update all questions that have the same assessment ID by removing the
            # assessment id from the questions
            clean_questions = questions_collection.update_many(
                {'assessment_id': ObjectId(assessment_result_id)},
                {'$pull': {'assessment_ids': ObjectId(assessment_result_id)}}
            )
            if clean_questions.modified_count > 0:
                return True
        return False
