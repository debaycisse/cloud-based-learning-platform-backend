from datetime import datetime, timezone
from bson import ObjectId
from app import db
from app.utils.validation import html_tags_converter

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
    '''
    Create a new question.
    Args:
        question_text (str): The text of the question.
        options (list): A list of answer options for the question.
        correct_answer (str): The correct answer for the question.
        tags (list, optional): A list of tags associated with the
        question.
        assessment_ids (list, optional): A list of assessment IDs
        where the question is used.
    Returns:
        dict: The created question object with its ID.
    '''
    @staticmethod
    def create(question_text, options, correct_answer, tags=None, assessment_ids=None):
        """Create a new question"""
        question = {
            'question_text': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'tags': tags or [],
            'assessment_ids': assessment_ids or [],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        result = questions_collection.insert_one(question)
        question['_id'] = result.inserted_id
        return question
    
    '''
    Find all questions with optional filters, limit, and skip.
    Args:
        filters (dict, optional): Filters to apply to the query.
        limit (int, optional): Maximum number of questions to
        return. Defaults to 20.
        skip (int, optional): Number of questions to skip.
        Defaults to 0.
    Returns:
        list: A list of questions that match the filters.
        Each question will have its '_id' field converted to a string.
    '''
    @staticmethod
    def find_by_id(question_id):
        """Find a question by ID"""
        return questions_collection.find_one({'_id': ObjectId(question_id)})
    
    '''
    Counts the total number of questions in the collection.
    Returns:
        int: The total number of questions.
    '''
    @staticmethod
    def count():
        """Count the total number of questions"""
        return questions_collection.count_documents({})
    
    '''
    Find multiple questions by their ObjectIds.
    Args:
        object_ids (list): List of ObjectId instances.
    Returns:
        list: List of question objects.
    '''
    @staticmethod
    def find_by_ids(object_ids):
        pipeline = [
        {'$match': {'_id': {'$in': object_ids}}},
        {'$sample': {'size': len(object_ids)}}
        ]

        cursor = questions_collection.aggregate(pipeline=pipeline)
        
        # Convert the cursor to a list and format the _id field as a string
        questions = []
        for question in cursor:
            question['_id'] = str(question['_id'])  # Convert ObjectId to string
            questions.append(question)
        
        return questions

    '''
    Find questions by tags.
    Args:
        tags (list): A list of tags to filter questions by.
        limit (int, optional): Maximum number of questions to return.
        Defaults to 20.
        skip (int, optional): Number of questions to skip.
        Defaults to 0.
    Returns:
        list: A list of questions that match the tags.
        Each question will have its '_id' field converted to a string.
        If no questions are found, an empty list is returned.
    '''
    @staticmethod
    def find_by_tags(tags, limit=20, skip=0):
        """Find questions by tags"""
        limit = int(limit)
        
        skip = int(skip)

        query = {
            '$or': [
                {
                    'tags': {
                        '$regex': html_tags_converter(tag),
                        '$options': 'i'
                    }
                } for tag in tags
            ]
        }

        cursor = questions_collection.find(
            query
        ).skip(skip).limit(limit)
        
        results = []
        
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results

    '''
    Find questions by assessment ID.
    Args:
        assessment_id (str): The ID of the assessment to
        filter questions by.
    Returns:
        list: A list of questions that are associated with
        the specified assessment ID.
        Each question will have its '_id' field
        converted to a string.
        If no questions are found, an empty list is returned.
    '''
    @staticmethod
    def find_by_assessment_id(assessment_id):
        """Find questions by assessment ID"""
        cursor = questions_collection.find({'assessment_ids': str(assessment_id)})
        questions = []
        for question in cursor:
            question['_id'] = str(question['_id'])
            questions.append(question)
        return questions
    
    '''
    Find all questions with pagination.
    Args:
        limit (int, optional): Maximum number of questions
        to return. Defaults to 20.
        skip (int, optional): Number of questions to skip.
        Defaults to 0.
    Returns:
        list: A list of questions, each with its '_id'
        field converted to a string.
        If no questions are found, an empty list is returned.
    '''
    @staticmethod
    def find_all(limit=20, skip=0):
        """Find all questions with pagination"""
        limit = int(limit)
        skip = int(skip)
        cursor = questions_collection.find().sort('created_at', -1).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    Update a question by its ID.
    Args:
        question_id (str): The ID of the question to update.
        update_data (dict): A dictionary containing the
        fields to update.
    Returns:
        dict: The updated question object.
        If the question does not exist, returns None.
    '''
    @staticmethod
    def update(question_id, update_data):
        """Update a question"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        questions_collection.update_one(
            {'_id': ObjectId(question_id)},
            {'$set': update_data}
        )
        return questions_collection.find_one({'_id': ObjectId(question_id)})
    
    '''
    Delete a question by its ID.
    Args:
        question_id (str): The ID of the question to delete.
    Returns:
        bool: True if the question was deleted successfully,
        False if the question was not found.
        If the question is not found, it returns False.
    '''
    @staticmethod
    def delete(question_id):
        """Delete a question"""
        questions_collection.delete_one({'_id': ObjectId(question_id)})
        # Confirm question deletion was successful
        if questions_collection.find_one({'_id': ObjectId(question_id)}):
            return False
        return True

    '''
    Add an assessment ID to a question.
    Args:
        question_id (str): The ID of the question to update.
        assessment_id (str): The ID of the assessment to add.
    Returns:
        bool: True if the assessment ID was added successfully,
        False if the question was not found or the assessment
        ID already exists.
    '''
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
    
    '''
    Remove an assessment ID from a question.
    Args:
        question_id (str): The ID of the question to update.
        assessment_id (str): The ID of the assessment to remove.
    Returns:
        bool: True if the assessment ID was removed successfully,
        False if the question was not found or the assessment
        ID does not exist.
    '''
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
    
    '''
    Find questions by multiple assessment IDs.
    Args:
        assessment_ids (list): A list of assessment IDs to
        filter questions by.
        limit (int, optional): Maximum number of questions to
        return. Defaults to 20.
        skip (int, optional): Number of questions to skip.
        Defaults to 0.
    Returns:
        list: A list of questions that match the assessment IDs.
        Each question will have its '_id' field converted to a string.
        If no questions are found, an empty list is returned.
    '''
    @staticmethod
    def find_by_assessment_ids(assessment_ids, limit=20, skip=0):
        """Find questions by multiple assessment IDs"""
        limit = int(limit)
        skip = int(skip)
        cursor = questions_collection.find(
            {'assessment_ids': {'$in': assessment_ids}}
        ).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    Find questions by assessment ID and tags.
    Args:
        assessment_id (str): The ID of the assessment to
        filter questions by.
        tags (list): A list of tags to filter questions by.
        limit (int, optional): Maximum number of questions to return.
        Defaults to 20.
        skip (int, optional): Number of questions to skip. Defaults to 0.
    Returns:
        list: A list of questions that match the assessment ID and tags.
        Each question will have its '_id' field converted to a string.
        If no questions are found, an empty list is returned.
    '''
    @staticmethod
    def find_by_assessment_id_and_tags(assessment_id, tags, limit=20, skip=0):
        """Find questions by assessment ID and tags"""
        limit = int(limit)
        skip = int(skip)

        cursor = questions_collection.find(
            {'assessment_ids': assessment_id, 'tags': {'$in': tags}}
        ).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    