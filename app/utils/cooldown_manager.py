from app.models.user import User
from datetime import datetime, timezone

def manage_cooldown(user_id):
    '''
    Manages cooldown field in a user's or leaner's record.
    Args:
        user_id (str): the user ID of the learner or user whose
        record is to be chacked and updated, it required.
    Returns:
        Nothing is returned.
    '''
    user = User.find_by_id(user_id=user_id)
    
    if user is not None:
        cooldown = user.get('cooldown', {})

    if cooldown and cooldown.get('duration'):
        today = datetime.now(timezone.utc)
        cooldown_duration = datetime.fromisoformat(
            cooldown.get('duration')
        )

        if cooldown_duration < today:
            User.remove_cooldown_field(user_id=user_id)
