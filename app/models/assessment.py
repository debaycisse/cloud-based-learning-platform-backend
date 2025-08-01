from datetime import datetime, timezone
from bson import ObjectId
from app import db
from app.utils.validation import html_tags_unconverter

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
    '''
    This method is used for creating a new assessmsent.
    It takes the title, course_id, and an optional time_limit parameter.
    The time_limit defaults to 25 minutes if not provided.
    It returns the created assessment document with its ID.
    Args:
        title (str): Title of the assessment
        course_id (str): ID of the course associated with the assessment
        time_limit (int, optional): Time limit for the assessment in minutes. Defaults to 25.
    Returns:
        dict: The created assessment document with its ID
    '''
    @staticmethod
    def create(title, course_id, time_limit=25):
        """Create a new assessment"""
        assessment = {
            'title': title,
            'course_id': course_id,
            'time_limit': time_limit,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        result = assessments_collection.insert_one(assessment)
        assessment['_id'] = result.inserted_id
        return assessment

    '''
    Finds an assessment by its ID.
    Args:
        assessment_id (str): ID of the assessment to find
    Returns:
        dict: The assessment document if found, None otherwise
    '''
    @staticmethod
    def find_by_id(assessment_id):
        """Find an assessment by ID"""
        return assessments_collection.find_one(
            {'_id': ObjectId(assessment_id)}
        )

    '''
    Finds assessments by course ID.
    Args:
        course_id (str): ID of the course to find assessments for
    Returns:
        list: List of assessment documents for the specified course
    '''
    @staticmethod
    def find_by_course_id(course_id):
        """Find assessments for a specific course"""
        cursor = assessments_collection.find({'course_id': course_id})
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results

    '''
    Finds all assessments with pagination.
    Args:
        limit (int): Maximum number of assessments to return
        skip (int): Number of assessments to skip for pagination
    Returns:
        list: List of assessment documents with pagination applied
    '''
    @staticmethod
    def find_all(limit=20, skip=0):
        """Find all assessments with pagination"""
        limit = int(limit)
        skip = int(skip)
        cursor = assessments_collection.find().sort('created_at', -1).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results

    '''
    Updates an assessment by its ID.
    Args:
        assessment_id (str): ID of the assessment to update
        update_data (dict): Dictionary containing fields to update
    Returns:
        dict: The updated assessment document
    '''
    @staticmethod
    def update(assessment_id, update_data):
        """Update an assessment"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        assessments_collection.update_one(
            {'_id': ObjectId(assessment_id)},
            {'$set': update_data}
        )
        result = assessments_collection.find_one({'_id': ObjectId(assessment_id)})
        result['_id'] = str(result['_id'])
        return result

    '''
    Deletes an assessment by its ID.
    Args:
        assessment_id (str): ID of the assessment to delete
    Returns:
        bool: True if the assessment was deleted, False otherwise
    '''
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
    '''
    Creates a new assessment result with demonstrated strengths.
    Args:
        user_id (str): ID of the user who took the assessment
        assessment_id (str): ID of the assessment
        answers (list): List of answers provided by the user
        score (float): Score obtained by the user
        passed (bool): Boolean indicating if the user passed the assessment
        started_at (str): Timestamp when the assessment was started
        questions (list): List of questions in the assessment
        knowledge_gaps (list, optional): List of knowledge gaps identified in the assessment
        demonstrated_strengths (list, optional): List of demonstrated strengths in the assessment
    Returns:
        dict: The created assessment result document with its ID
    '''
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
            'time_spent': 30 - (
                (
                    datetime.now(timezone.utc) - datetime.fromisoformat(started_at)
                ).total_seconds() / 60
            ),
            'questions': questions,
        }

        result_id = results_collection.insert_one(result).inserted_id

        result['_id'] = result_id
        return result

    '''
    Finds assessment results for a specific user.
    Args:
        user_id (str): ID of the user to find results for
        limit (int, optional): Maximum number of results to return. Defaults to 20.
        skip (int, optional): Number of results to skip for pagination. Defaults to 0
    Returns:
        list: List of assessment result documents for the specified user
    '''
    @staticmethod
    def find_by_user(user_id, limit=20, skip=0):
        """Find assessment results for a specific user"""
        try:
            limit = int(limit)
            skip = int(skip)
            if not isinstance(user_id, str):
                user_id = str(user_id)

            assessment_results_cursor = results_collection.find({'user_id': user_id}).sort(
                'created_at', -1
            ).skip(skip).limit(limit)
            results = []
            for assessment_result in assessment_results_cursor:
                assessment_result['_id'] = str(assessment_result['_id'])
                questions = []
                for question in assessment_result.get('questions', []):
                    if isinstance(question.get('_id', ''), ObjectId):
                        question['_id'] = str(question['_id'])
                    for field in question:
                        if field == 'question_text' or field == 'correct_answer':
                            question[field] = html_tags_unconverter(question[field])
                        elif field == 'options' or field == 'tags':
                            question[field] = [html_tags_unconverter(option) for option in question[field]]
                    questions.append(question)
                answers = []
                for answer in assessment_result.get('answers', []):
                    if isinstance(answer, str):
                        answer = html_tags_unconverter(answer)
                    answers.append(answer)
                assessment_result['answers'] = answers
                assessment_result['questions'] = questions
                results.append(assessment_result)
            return results
        except Exception as e:
            return None

    '''
    Finds Assessment result by course id
    Args:
        course_id (str): ID of the course to find assessment results for
        user_id (str): ID of the user to find assessment results for
    Returns:
        dict: Assessment result document for the specified course and user, or None if not found
    '''
    @staticmethod
    def find_by_course_and_user_id(course_id, user_id):
        "Finds Assessment result by course id"
        try:
            assessment = (Assessment.find_by_course_id(course_id=course_id))[0]

            assessment_id = assessment.get('_id')

            result = results_collection.find_one({
                'user_id': str(user_id),
                'assessment_id': str(assessment_id)
            })
            result['answers'] = [html_tags_unconverter(answer) for answer in result.get('answers', [])]
            questions = []
            for question in result.get('questions', []):
                question['_id'] = str(question.get('_id'))
                question['question_text'] = html_tags_unconverter(question.get('question_text'))
                question['tags'] = [html_tags_unconverter(tag) for tag in question.get('tags', [])]
                question['options'] = [html_tags_unconverter(opt) for opt in question.get('options', [])]
                questions.append(question)
            result['questions'] = questions
            result['_id'] = str(result.get('_id'))
            return result
        except Exception as e:
            return None

    '''
    Finds results for a specific assessment
    Args:
        assessment_id (str): ID of the assessment to find results for
        limit (int, optional): Maximum number of results to return. Defaults to 20.
        skip (int, optional): Number of results to skip for pagination. Defaults to 0
    Returns:
        list: List of assessment result documents for the specified assessment
    '''
    @staticmethod
    def find_by_assessment(assessment_id, limit=20, skip=0):
        """Find results for a specific assessment"""
        limit = int(limit)
        skip = int(skip)
        cursor = results_collection.find({'assessment_id': assessment_id}).sort(
            'created_at', -1
        ).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results

    '''
    Finds the latest result for a user and assessment
    Args:
        user_id (str): ID of the user to find the result for
        assessment_id (str): ID of the assessment to find the result for
    Returns:
        dict: The latest assessment result document for the specified user and assessment, or None if not
    '''
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

    '''
    Deletes an assessment result by its assessment ID.
    Args:
        assessment_id (str): ID of the assessment to delete results for
    Returns:
        bool: True if the assessment result was deleted, False otherwise
    '''
    @staticmethod
    def delete_by_assessment_id(assessment_id):
        """Delete an assessment result"""
        results_collection.delete_one({'assessment_id': str(assessment_id)})

        # Update all questions that have the same assessment ID by removing the
        # assessment id from the questions
        questions = questions_collection.find({'assessment_ids': str(assessment_id)})

        clean_questions = questions_collection.update_many(
            {'assessment_ids': str(assessment_id)},
            {'$pull': {'assessment_ids': str(assessment_id)}}
        )

        if questions is not None and clean_questions.matched_count < 1:
            return False

        return True

    '''
    Updates a question in the assessment result if it exists
    Args:
        updated_question (dict): Dictionary containing the updated question data
    Returns:
        result: The result of the update operation
    '''
    @staticmethod
    def update_question(updated_question):
        """Update a question in the assessment result if it exists"""

        question_obj = {
            'question_text': updated_question.get('question_text'),
            'options': updated_question.get('options'),
            'correct_answer': updated_question.get('correct_answer'),
            'tags': updated_question.get('tags', []),
            'assessment_ids': updated_question.get('assessment_ids', []),
            'created_at': updated_question.get('created_at'),
            'updated_at': updated_question.get('updated_at')
        }
        result = results_collection.update_one(
            {'questions._id': updated_question.get('_id')},
            {'$set': {'questions.$': question_obj}}
        )
        return result

    '''
    Finds assessment results by question ID
    Args:
        question_id (str): ID of the question to find results for
    Returns:
        dict: Assessment result document containing the question, or None if not found
    '''
    @staticmethod
    def find_by_question_id(question_id):
        """Find assessment results by question ID"""
        if not isinstance(question_id, ObjectId):
            question_id = ObjectId(question_id)
        found_question = results_collection.find_one({'questions._id': question_id}) 
        if found_question is not None:
            found_question['id'] = str(found_question['_id'])
            for field in found_question:
                if field == 'question_text' or field == 'correct_answer':
                    found_question[field] = html_tags_unconverter(found_question[field])
                elif field == 'options' or field == 'tags':
                    found_question[field] = [html_tags_unconverter(option) for option in found_question[field]]
        return found_question
