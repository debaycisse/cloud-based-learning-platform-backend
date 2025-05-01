from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from bson import ObjectId

users_collection = db.users

class User:
    @staticmethod
    def create(email, username, password):
        """Create a new user"""
        user = {
            'email': email,
            'username': username,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
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
    def find_all_users():
        """Find all users"""
        return list(users_collection.find())
    
    @staticmethod
    def update_profile(user_id, update_data):
        """Update user profile"""
        update_data['updated_at'] = datetime.utcnow()
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
                'updated_at': datetime.utcnow()
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
            valid_preferences['updated_at'] = datetime.utcnow()
            
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
