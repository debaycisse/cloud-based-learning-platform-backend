from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from bson import ObjectId

users_collection = db.users

'''
User model for managing user data and operations.
This model provides methods for creating, finding, updating,
and managing user profiles, including authentication and preferences.
'''
class User:
    '''
    Create a new user with the provided details.
    Args:
        name (str): The name of the user.
        email (str): The email address of the user.
        username (str): The username of the user.
        password (str): The password for the user.
    Returns:
        dict: The created user object with an auto-generated ID.
        The user object includes fields for name, email, username,
        password hash, creation and update timestamps, role, progress,
        and preferences.
        The progress field includes completed and in-progress courses,
        and completed assessments.
        The preferences field includes categories, skills, difficulty,
        learning style, time commitment, and goals.
        The created_at and updated_at fields are set to the current UTC time.
    '''
    @staticmethod
    def create(name, email, username, password):
        """Create a new user"""
        user = {
            'name': name,
            'email': email,
            'username': username,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'role': 'user',
            'progress': {
                'completed_courses': [],
                'in_progress_courses': '',
                'completed_assessments': []
            },
            'preferences': {
                'categories': [],
                'skills': [],
                'difficulty': 'beginner',
                'learning_style': 'textual',
                'time_commitment': 'medium',
                'goals': []
            }
        }
        result = users_collection.insert_one(user)
        user['_id'] = result.inserted_id
        return user
    
    '''
    Find a user by email.
    Args:
        email (str): The email address of the user to find.
    Returns:
        dict: The user object if found, None otherwise.
        The user object includes fields for name, email,
        username, password hash, creation and
        update timestamps, role, progress, and preferences.
        The progress field includes completed and
        in-progress courses, and completed assessments.
        The preferences field includes categories, skills,
        difficulty, learning style, time commitment, and goals.
        The created_at and updated_at fields are set to
        the current UTC time.
    '''
    @staticmethod
    def find_by_email(email):
        """Find a user by email"""
        return users_collection.find_one({'email': email})
    
    '''
    Find a user by username.
    Args:
        username (str): The username of the user to find.
    Returns:
        dict: The user object if found, None otherwise.
        The user object includes fields for name, email,
        username, password hash, creation and
        update timestamps, role, progress, and preferences.
        The progress field includes completed and
        in-progress courses, and completed assessments.
        The preferences field includes categories, skills,
        difficulty, learning style, time commitment, and goals.
        The created_at and updated_at fields are set to
        the current UTC time.
    '''
    @staticmethod
    def find_by_username(username):
        """Find a user by username"""
        return users_collection.find_one({'username': username})
    
    '''
    Find a user by ID.
    Args:
        user_id (str): The ID of the user to find.
    Returns:
        dict: The user object if found, None otherwise.
        The user object includes fields for name, email,
        username, password hash, creation and
        update timestamps, role, progress, and preferences.
        The progress field includes completed and
        in-progress courses, and completed assessments.
        The preferences field includes categories, skills,
        difficulty, learning style, time commitment, and goals.
        The created_at and updated_at fields are set to
        the current UTC time.
    '''
    @staticmethod
    def find_by_id(user_id):
        """Find a user by ID"""
        return users_collection.find_one({'_id': ObjectId(user_id)})
    
    '''
    Find all users with optional filters, limit, and skip.
    Args:
        filters (dict): Optional filters to apply to the query.
        limit (int): The maximum number of users to return.
        skip (int): The number of users to skip before
        returning results.
    Returns:
        list: A list of user objects matching the filters.
        Each user object includes fields for name, email,
        username, password hash, creation and
        update timestamps, role, progress, and preferences.
        The progress field includes completed and in-progress courses,
        and completed assessments.
        The preferences field includes categories, skills,
        difficulty, learning style, time commitment, and goals.
        The created_at and updated_at fields are set to
        the current UTC time.
        If no users match the filters, an empty list is returned.
        The user IDs are converted to strings for easier handling.
    '''
    @staticmethod
    def find_all_users(filters=None, limit=20, skip=0):
        """Find all users"""
        filters = filters or {}
        limit = int(limit)
        skip = int(skip)
        cursor = users_collection.find(filters).limit(limit).skip(skip)
        
        results =[]

        if cursor is not None:
            for user in cursor:
                user['_id'] = str(user['_id'])
                results.append(user)

        return results
    
    '''
    Update a user's profile by user ID.
    Args:
        user_id (str): The ID of the user to update.
        update_data (dict): A dictionary containing the fields to update.
    Returns:
        dict: The updated user object if the update was successful
    '''
    @staticmethod
    def update_profile(user_id, update_data):
        """Update user profile"""

        # Prevent updating sensitive fields
        update_data.pop('password_hash', None)
        update_data.pop('created_at', None)
        update_data.pop('progress', None)
        update_data.pop('course_progress', None)
        update_data.pop('role', None)
        update_data.pop('_id', None)

        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        return users_collection.find_one({'_id': ObjectId(user_id)})
    
    '''
    Update user course progress.
    Args:
        user_id (str): The ID of the user to update.
        progress_data (dict): A dictionary containing the course
        progress data.
        The progress_data should include:
            - course_id (str): The ID of the course.
            - completed_course_id (str): The ID of the completed course.
            - completed_course (str): The name of the completed course.
    Returns:
        dict: The updated user object if the update was successful.
        If the course progress is updated, the completed_course_id
        is added to the user's completed courses.
        If the course is in progress, it updates the course_progress
        field with the provided progress_data.
        If the course is completed, it updates the course_progress
        field and adds the completed_course_id to the user's
        completed courses.
        The updated_at field is set to the current UTC time.
        If the update is successful, it returns the updated user object.
        If no changes are made, it returns None.
    '''
    @staticmethod
    def update_course_progress(user_id, progress_data):
        """Update user course progress"""

        if progress_data.get('completed_course_id'):
            result = users_collection.update_one(
                {
                    '_id': ObjectId(user_id), 
                    'course_progress.course_id': str(progress_data.get('course_id'))
                },
                {
                    '$set': {
                        'updated_at': datetime.now(timezone.utc).isoformat(),
                        'course_progress.$': progress_data,
                        'course_progress.$.completed_course_id': progress_data.get('completed_course'),
                        'progress.in_progress_courses': ''
                    },
                    '$addToSet': {
                        'progress.completed_courses': progress_data.get('completed_course_id')
                    }
                }
            )
        else:
            result = users_collection.update_one(
                {
                    '_id': ObjectId(user_id), 
                    'course_progress.course_id': str(progress_data.get('course_id'))
                },
                {
                    '$set': {
                        'updated_at': datetime.now(timezone.utc).isoformat(),
                        'course_progress.$': progress_data,
                    }
                }
            )

        if result.modified_count > 0:
            return users_collection.find_one({'_id': ObjectId(user_id)})
        return None
    
    '''
    Update user learning preferences.
    Args:
        user_id (str): The ID of the user to update.
        preferences_data (dict): A dictionary containing the learning
        preferences data.
        The preferences_data should include:
            - categories (list): A list of preferred categories.
            - skills (list): A list of preferred skills.
            - difficulty (str): The preferred difficulty level.
            - learning_style (str): The preferred learning style.
            - time_commitment (str): The preferred time commitment.
            - goals (list): A list of learning goals.
    Returns:
        dict: The updated user object if the update was successful.
        The updated preferences are stored in the user's preferences field.
        The updated_at field is set to the current UTC time.
        If the preferences_data is valid, it updates the user's preferences
        and returns the updated user object.
        If no valid preferences are provided, it does not update the user.
        If the update is successful, it returns the updated user object.
        If no changes are made, it returns None.
    '''
    @staticmethod
    def update_preferences(user_id, preferences_data):
        """Update user learning preferences"""
        # Ensure we only update valid preference fields
        valid_preferences = {}
        
        if 'categories' in preferences_data and isinstance(preferences_data.get('categories'), list):
            valid_preferences['preferences.categories'] = preferences_data.get('categories')
            
        if 'skills' in preferences_data and isinstance(preferences_data.get('skills'), list):
            valid_preferences['preferences.skills'] = preferences_data.get('skills')
            
        if 'difficulty' in preferences_data:
            valid_preferences['preferences.difficulty'] = preferences_data.get('difficulty')
            
        if 'learning_style' in preferences_data:
            valid_preferences['preferences.learning_style'] = preferences_data.get('learning_style')
            
        if 'time_commitment' in preferences_data:
            valid_preferences['preferences.time_commitment'] = preferences_data.get('time_commitment')
            
        if 'goals' in preferences_data and isinstance(preferences_data.get('goals'), list):
            valid_preferences['preferences.goals'] = preferences_data.get('goals')
        
        # Only update if preferences data is valid
        if valid_preferences:
            valid_preferences['updated_at'] = datetime\
                .now(timezone.utc).isoformat()
            
            users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': valid_preferences}
            )
        
        return users_collection.find_one({'_id': ObjectId(user_id)})

    @staticmethod
    def check_password(user, password):
        """Check if password is correct"""
        if not user or not user.get('password_hash'):
            return False
        return check_password_hash(user['password_hash'], password)
    
    @staticmethod
    def update_password(user, new_password):
        """Update user password"""
        hashed_password = generate_password_hash(new_password)
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {
                'password_hash': hashed_password,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        return users_collection.find_one({'_id': user['_id']})
    
    @staticmethod
    def remove_cooldown_field(user_id):
        """Removes the cooldown field in a given user's record"""
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$unset': {'cooldown': ''}}
        )
