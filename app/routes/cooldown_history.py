from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.utils.swagger_utils import yaml_from_file
from app.models.cooldown_history import CooldownHistory
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input

cooldown_history_bp = Blueprint('cooldown_history', __name__)

@cooldown_history_bp.route('', methods=['POST'])
@jwt_required()
@validate_json('course_id', 'cooldown_duration', 'knowledge_gaps')
def create_cooldown_history():
    """Create a new cooldown history entry"""
    try:

        user_id = get_jwt_identity()
        data = sanitize_input(request.get_json())

        course_id = data.get('course_id')
        cooldown_duration = data.get('cooldown_duration')
        knowledge_gaps = data.get('knowledge_gaps', [])


        cooldown_entry = CooldownHistory.create(
            user_id=user_id,
            course_id=course_id,
            cooldown_duration=cooldown_duration,
            knowledge_gaps=knowledge_gaps
        )

        cooldown_entry['_id'] = str(cooldown_entry['_id'])

        return jsonify(cooldown_entry), 201
    except requests.RequestException as e:
        return jsonify({"error": f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({"error": f'Internal server error: {str(e)}'}), 500
    
@cooldown_history_bp.route('/<string:user_id>', methods=['GET'])
@jwt_required()
def get_cooldown_history_by_user_id(user_id):
    """Get cooldown history by user ID"""
    try:
        user_id = get_jwt_identity()
        cooldown_history = CooldownHistory.find_by_user(user_id)

        if not cooldown_history:
            return jsonify({"error": "No cooldown history found for this user"}), 404

        # Convert ObjectId to string for JSON serialization
        cooldown_history['_id'] = str(cooldown_history['_id'])
        return jsonify({'cooldown': cooldown_history}), 200

    except requests.RequestException as e:
        return jsonify({"error": f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({"error": f'Internal server error: {str(e)}'}), 500
    
@cooldown_history_bp.route('/<string:user_id>/<string:course_id>', methods=['PUT'])
@jwt_required()
@validate_json('knowledge_gaps')
@admin_required
def update_cooldown_history(user_id, course_id):
    """Update cooldown history for a user and course"""
    try:
        data = sanitize_input(request.get_json())
        knowledge_gaps = data.get('knowledge_gaps', [])

        updated = CooldownHistory.update_cooldown_history(
            user_id=user_id,
            course_id=course_id,
            knowledge_gaps=knowledge_gaps
        )

        if not updated:
            return jsonify({"error": "Cooldown history not found or not updated"}), 404

        return jsonify({"message": "Cooldown history updated successfully"}), 200

    except requests.RequestException as e:
        return jsonify({"error": f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({"error": f'Internal server error: {str(e)}'}), 500
    
@cooldown_history_bp.route('/<string:_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_cooldown_history(_id):
    """Delete cooldown history by ID"""
    try:
        deleted_count = CooldownHistory.delete_cooldown_history(_id)

        if deleted_count == 0:
            return jsonify({"error": "Cooldown history not found"}), 404

        return jsonify({"message": "Cooldown history deleted successfully"}), 200

    except requests.RequestException as e:
        return jsonify({"error": f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({"error": f'Internal server error: {str(e)}'}), 500
