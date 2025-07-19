from datetime import datetime, timezone
from bson import ObjectId
from app import db

cooldowns_collection = db.cooldown_history

'''
This module defines the CooldownHistory model for keeping cooldown history of a typical user.
- It allows creating and finding based on the user ID and course ID.
'''
class CooldownHistory:
    """Model for keeping cooldown history of a user for a specific course."""

    @staticmethod
    def create(user_id, course_id, cooldown_duration, knowledge_gaps=None):
        """Create a new cooldown history entry"""
        cooldown_entry = {
            'user_id': str(user_id),
            'cooldown_end': cooldown_duration,
            'created_at': datetime.now(timezone.utc),
            'cool_downs': [
                {
                    'course_id': str(course_id),
                    'concepts': knowledge_gaps or [],
                    'created_at': datetime.now(timezone.utc)
                }
            ]
        }

        result = cooldowns_collection.insert_one(cooldown_entry)
        cooldown_entry['_id'] = result.inserted_id

        return cooldown_entry
    
    @staticmethod
    def update_cooldown_history(user_id, course_id, knowledge_gaps=None):
        """Update cooldown history for a user and course"""
        return cooldowns_collection.update_one(
            {'user_id': str(user_id)},
            {
                '$set': {
                    'updated_at': datetime.now(timezone.utc)
                },
                '$push': {
                    'cool_downs': {
                        'course_id': str(course_id),
                        'concepts': knowledge_gaps or [],
                        'created_at': datetime.now(timezone.utc)
                    }
                }
            }
        ).modified_count > 0

    @staticmethod
    def find_by_user(user_id):
        """Find cooldown history by user and assessment"""
        return cooldowns_collection.find_one({
            'user_id': ObjectId(user_id),
        })

    @staticmethod
    def delete_cooldown_history(id):
        """Delete cooldown history by user and assessment"""
        return cooldowns_collection.delete_one({
            '_id': ObjectId(id),
        }).deleted_count > 0