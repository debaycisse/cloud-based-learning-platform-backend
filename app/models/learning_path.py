from datetime import datetime, timezone
from bson import ObjectId
from app import db

learning_paths_collection = db.learning_paths

'''
This is a model for magaging learning paths.
It allows for creating, finding, and updating learning paths.
It includes methods to create a new learning path, find all paths,
find a path by ID, find paths by target skill, and update a path.
'''
class LearningPath:
    '''
    Create a new learning path.
    Args:
        title (str): The title of the learning path.
        description (str): A brief description of the learning path.
        courses (list): A list of course IDs that are part of the learning path.
        target_skills (list, optional): A list of skills that the learning path targets.
    Returns:
        dict: The created learning path object with its ID.
    '''
    @staticmethod
    def create(title, description, courses, target_skills=None):
        """Create a new learning path"""
        path = {
            'title': title,
            'description': description,
            'courses': courses,
            'target_skills': target_skills or [],
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        result = learning_paths_collection.insert_one(path)
        path['_id'] = str(result.inserted_id)
        return path
    
    '''
    Find all learning paths with optional filters, limit, and skip.
    Args:
        filters (dict, optional): Filters to apply to the query.
        limit (int, optional): Maximum number of paths to return. Defaults to 20.
        skip (int, optional): Number of paths to skip. Defaults to 0.
    Returns:
        list: A list of learning paths that match the filters.
        Each path will have its '_id' field converted to a string.
    '''
    @staticmethod
    def find_all(filters={}, limit=20, skip=0):
        """Find all learning paths"""
        limit = int(limit)
        skip = int(skip)

        cursor = learning_paths_collection.find(filters).skip(skip).limit(limit)
        
        results = []
        
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    Find a learning path by its ID.
    Args:
        path_id (str): The ID of the learning path to find.
    Returns:
        dict: The learning path object if found, or None if not found.
        The '_id' field will be an ObjectId if found.
        If the path is not found, None is returned.
    '''
    @staticmethod
    def find_by_id(path_id):
        """Find a learning path by ID"""
        return learning_paths_collection.find_one({'_id': ObjectId(path_id)})
    
    '''
    Find learning paths by target skill.
    Args:
        skill (str): The skill to filter learning paths by.
        limit (int, optional): Maximum number of paths to return. Defaults to 20.
        skip (int, optional): Number of paths to skip. Defaults to 0.
    Returns:
        list: A list of learning paths that target the specified skill.
        Each path will have its '_id' field converted to a string.
        If no paths are found, an empty list is returned.
    '''
    @staticmethod
    def find_by_skill(skill, limit=20, skip=0):
        limit = int(limit)
        skip = int(skip)
        """Find learning paths by target skill"""
        cursor = learning_paths_collection.find(
            {'target_skills': skill}
        ).skip(skip).limit(limit)
        results = []
        for course in cursor:
            course['_id'] = str(course['_id'])
            results.append(course)
        return results
    
    '''
    Update a learning path by its ID.
    Args:
        path_id (str): The ID of the learning path to update.
        update_data (dict): A dictionary containing the fields to update.
    Returns:
        dict: The updated learning path object.
        The '_id' field will be an ObjectId.
        If the path is not found, None is returned.
    '''
    @staticmethod
    def update(path_id, update_data):
        """Update a learning path"""
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        learning_paths_collection.update_one(
            {'_id': ObjectId(path_id)},
            {'$set': update_data}
        )
        return learning_paths_collection.find_one({'_id': ObjectId(path_id)})
