from datetime import datetime, timezone
from bson import ObjectId
from app import db

cooldowns_collection = db.cooldown_history

'''
This is a model for managing cooldown history of users in a course.
It allows creating, updating, finding, and deleting cooldown
history entries.
Cooldown history is used to track the cooldown periods
for users in a specific course, including the concepts they
have knowledge gaps in.
'''
class CooldownHistory:

    '''
    Creates a new cooldown history entry
    Args:
        user_id - the ID of the user
        course_id - the ID of the course
        cooldown_duration - the duration of the cooldown
        knowledge_gaps - optional list of concepts the user has
        knowledge gaps in
    Returns:
        The created cooldown history entry
    '''
    @staticmethod
    def create(user_id, course_id, cooldown_duration, knowledge_gaps=None):
        """Create a new cooldown history entry"""
        cooldown_entry = {
            'user_id': str(user_id),
            'cooldown_end': cooldown_duration,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'cool_downs': [
                {
                    'course_id': str(course_id),
                    'concepts': knowledge_gaps or [],
                    'created_at': datetime.now(timezone.utc).isoformat()
                }
            ]
        }

        result = cooldowns_collection.insert_one(cooldown_entry)
        cooldown_entry['_id'] = result.inserted_id

        return cooldown_entry
    
    '''
    Updates the cooldown history for a user and course
    Args:
        user_id - the ID of the user
        course_id - the ID of the course
        knowledge_gaps - optional list of concepts the user has
        knowledge gaps in
    Returns:
        True if the update was successful, False otherwise
        If an error occurs, it returns None
    '''
    @staticmethod
    def update_cooldown_history(user_id, course_id, knowledge_gaps=None):
        """Update cooldown history for a user and course"""
        return cooldowns_collection.update_one(
            {'user_id': str(user_id)},
            {
                '$set': {
                    'updated_at': datetime.now(timezone.utc).isoformat()
                },
                '$push': {
                    'cool_downs': {
                        'course_id': str(course_id),
                        'concepts': knowledge_gaps or [],
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                }
            }
        ).modified_count > 0

    '''
    Finds cooldown history by user ID
    Args:
        user_id - the ID of the user
    Returns:
        The cooldown history entry for the user, or None if not found
    '''
    @staticmethod
    def find_by_user(user_id):
        """Find cooldown history by user and assessment"""
        return cooldowns_collection.find_one({
            'user_id': ObjectId(user_id),
        })

    '''
    Deletes cooldown history by ID
    Args:
        id - the ID of the cooldown history entry to be deleted
    Returns:
        True if the deletion was successful, False otherwise
        If an error occurs, it returns None
    '''
    @staticmethod
    def delete_cooldown_history(id):
        """Delete cooldown history by user and assessment"""
        return cooldowns_collection.delete_one({
            '_id': ObjectId(id),
        }).deleted_count > 0