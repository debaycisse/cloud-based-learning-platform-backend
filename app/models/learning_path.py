from datetime import datetime
from bson import ObjectId
from app import db

learning_paths_collection = db.learning_paths

class LearningPath:
    @staticmethod
    def create(title, description, courses, target_skills=None):
        """Create a new learning path"""
        path = {
            'title': title,
            'description': description,
            'courses': courses,
            'target_skills': target_skills or [],
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = learning_paths_collection.insert_one(path)
        path['_id'] = result.inserted_id
        return path
    
    @staticmethod
    def find_all(limit=20, skip=0):
        """Find all learning paths"""
        cursor = learning_paths_collection.find().skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def find_by_id(path_id):
        """Find a learning path by ID"""
        return learning_paths_collection.find_one({'_id': ObjectId(path_id)})
    
    @staticmethod
    def find_by_skill(skill, limit=20, skip=0):
        """Find learning paths by target skill"""
        cursor = learning_paths_collection.find(
            {'target_skills': skill}
        ).skip(skip).limit(limit)
        return list(cursor)
    
    @staticmethod
    def update(path_id, update_data):
        """Update a learning path"""
        update_data['updated_at'] = datetime.utcnow()
        learning_paths_collection.update_one(
            {'_id': ObjectId(path_id)},
            {'$set': update_data}
        )
        return learning_paths_collection.find_one({'_id': ObjectId(path_id)})
