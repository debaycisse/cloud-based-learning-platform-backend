from datetime import datetime, timezone
from bson import ObjectId
from app import db

questions_collection = db.questions

'''
Question Model
- Represents a question in the system
- Contains methods to create, find, and update questions
- Fields in a typical document:
    - question_text: Text of the question
    - options: List of answer options
    - correct_answer: Correct answer for the question
    - tags: List of tags associated with the question
    - assessment_ids: List of assessment IDs where the question is used
    - created_at: Timestamp when the question was created
    - updated_at: Timestamp when the question was last updated
'''
class Question:
    @staticmethod
    def create(question_text, options, correct_answer, tags=None):
        """Create a new question"""
        question = {
            'question_text': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'tags': tags or [],
            'assessment_ids': [],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        result = questions_collection.insert_one(question)
        question['_id'] = result.inserted_id
        return question
    
    @staticmethod
    def find_by_id(question_id):
        """Find a question by ID"""
        return questions_collection.find_one({'_id': ObjectId(question_id)})
    
    @staticmethod
    def find_by_tags(tags, limit=20, skip=0):
        """Find questions by tags"""
        cursor = questions_collection.find(
            {'tags': {'$in': tags}}
        ).skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def find_by_assessment_id(assessment_id):
        """Find questions by assessment ID"""
        return questions_collection.find({'assessment_ids': assessment_id})
    
    @staticmethod
    def find_all(limit=20, skip=0):
        """Find all questions with pagination"""
        cursor = questions_collection.find().sort('created_at', -1).skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def update(question_id, update_data):
        """Update a question"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        questions_collection.update_one(
            {'_id': ObjectId(question_id)},
            {'$set': update_data}
        )
        return questions_collection.find_one({'_id': ObjectId(question_id)})
    
    @staticmethod
    def delete(question_id):
        """Delete a question"""
        questions_collection.delete_one({'_id': ObjectId(question_id)})
        # Confirm question deletion was successful
        if questions_collection.find_one({'_id': ObjectId(question_id)}):
            return False
        return True

    @staticmethod
    def add_assessment_id(question_id, assessment_id):
        """Add an assessment ID to a question"""
        questions_collection.update_one(
            {'_id': ObjectId(question_id)},
            {'$addToSet': {'assessment_ids': assessment_id}}
        )
        # Confirm assessment ID was added successfully
        if questions_collection.find_one({'_id': ObjectId(question_id), 'assessment_ids': assessment_id}):
            return True
        return False
    
    @staticmethod
    def remove_assessment_id(question_id, assessment_id):
        """Remove an assessment ID from a question"""
        questions_collection.update_one(
            {'_id': ObjectId(question_id)},
            {'$pull': {'assessment_ids': assessment_id}}
        )
        # Confirm assessment ID was removed successfully
        if not questions_collection.find_one({'_id': ObjectId(question_id), 'assessment_ids': assessment_id}):
            return True
        return False
    
    @staticmethod
    def find_by_assessment_ids(assessment_ids, limit=20, skip=0):
        """Find questions by multiple assessment IDs"""
        cursor = questions_collection.find(
            {'assessment_ids': {'$in': assessment_ids}}
        ).skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def find_by_assessment_id_and_tags(assessment_id, tags, limit=20, skip=0):
        """Find questions by assessment ID and tags"""
        cursor = questions_collection.find(
            {'assessment_ids': assessment_id, 'tags': {'$in': tags}}
        ).skip(skip).limit(limit)
        return list(cursor)
    