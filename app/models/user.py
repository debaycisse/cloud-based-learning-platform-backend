from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from bson import ObjectId

users_collection = db.users

class User:
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
                'in_progress_courses': [],
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
    
    @staticmethod
    def find_by_email(email):
        """Find a user by email"""
        return users_collection.find_one({'email': email})
    
    @staticmethod
    def find_by_username(username):
        """Find a user by username"""
        return users_collection.find_one({'username': username})
    
    @staticmethod
    def find_by_id(user_id):
        """Find a user by ID"""
        return users_collection.find_one({'_id': ObjectId(user_id)})
    
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
    
    @staticmethod
    def update_profile(user_id, update_data):
        """Update user profile"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': update_data}
        )
        return users_collection.find_one({'_id': ObjectId(user_id)})
    
    @staticmethod
    def update_progress(user_id, progress_data):
        """Update user learning progress"""
        users_collection.update_one(
            {'_id': ObjectId(user_id)},
            {'$set': {
                'progress': progress_data,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
        return users_collection.find_one({'_id': ObjectId(user_id)})
    
    @staticmethod
    def update_preferences(user_id, preferences_data):
        """Update user learning preferences"""
        # Ensure we only update valid preference fields
        valid_preferences = {}
        
        if 'categories' in preferences_data and isinstance(preferences_data['categories'], list):
            valid_preferences['preferences.categories'] = preferences_data['categories']
            
        if 'skills' in preferences_data and isinstance(preferences_data['skills'], list):
            valid_preferences['preferences.skills'] = preferences_data['skills']
            
        if 'difficulty' in preferences_data:
            valid_preferences['preferences.difficulty'] = preferences_data['difficulty']
            
        if 'learning_style' in preferences_data:
            valid_preferences['preferences.learning_style'] = preferences_data['learning_style']
            
        if 'time_commitment' in preferences_data:
            valid_preferences['preferences.time_commitment'] = preferences_data['time_commitment']
            
        if 'goals' in preferences_data and isinstance(preferences_data['goals'], list):
            valid_preferences['preferences.goals'] = preferences_data['goals']
        
        # Only update if we have valid preferences
        if valid_preferences:
            valid_preferences['updated_at'] = datetime.now(timezone.utc).isoformat()
            
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
