from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from bson import ObjectId
from app.utils.swagger_utils import yaml_from_file
from app.utils.cooldown_manager import manage_cooldown
from app.models.concept_link import ConceptLinks
from app.utils.auth import admin_required
from app.utils.validation import (
    validate_json,
    sanitize_input,
    html_tags_unconverter
)


concept_bp = Blueprint('concepts', __name__)

'''
POST /api/concepts
- Creates a new concept with associated links and description.
- Expects a JSON payload with 'concepts', 'links', and 'description'.
- Returns the created concept or an error message.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires admin privileges.
- If the user is not authenticated, returns an error message.
- If the user does not have admin privileges, returns an error message.
'''
@concept_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('concepts', 'links', 'description')
@yaml_from_file('docs/swagger/concepts/create_concept.yaml')
def create_concept():
    try:
        data = sanitize_input(request.get_json())

        # Create a new concept
        concept = ConceptLinks.create(
            concepts=data.get('concepts'),
            links=data.get('links'),
            description=data.get('description')
        )
        concept['_id'] = str(concept['_id'])

        return jsonify({
            'message': 'Concept created successfully',
            'concept': concept
        }), 201

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
'''
GET /api/concepts/<concept_link_id>
- Retrieves a concept by its ID.
- Returns the concept object with its ID and details.
- If the concept is not found, returns an error message.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
- If the user does not have access to the concept, returns an error message.
'''
@concept_bp.route('/<concept_link_id>', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/concepts/get_concept_by_id.yaml')
def get_by_id(concept_link_id):
    try:
        user_id = get_jwt_identity()

        if not user_id:
            return jsonify({"error": "Invalid or missing user ID"}), 400
        
        manage_cooldown(user_id=user_id)

        result = ConceptLinks.get_by_id(concept_link_id=concept_link_id)
        for field, value in result.items():
            if isinstance(value, str):
                result[field] = html_tags_unconverter(value)
            elif isinstance(value, ObjectId):
                result[field] = str(value)
            elif isinstance(value, list):
                result[field] = [
                    html_tags_unconverter(v) for v in value
                ]
        return jsonify({
            'concept': result
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
    
'''
GET /api/concepts
- Retrieves a list of concepts with pagination.
- Supports 'limit' and 'skip' query parameters for pagination.
- Returns a list of concept objects with their IDs and details.
- If no concepts are found, returns an empty list and count as 0.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
- If the user does not have access to the concepts, returns an error message.
'''
@concept_bp.route('', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/concepts/get_concepts.yaml')
def get_concepts():
    try:
        user_id = get_jwt_identity()

        if not user_id:
            return jsonify({"error": "Invalid or missing user ID"})
        
        manage_cooldown(user_id=user_id)

        limit = int(request.args.get('limit', 10))
        skip = int(request.args.get('skip', 0))
        results_obj = ConceptLinks.get_concepts(skip=skip, limit=limit)
        results = []
        for result in results_obj:
            for field, value in result.items():
                if isinstance(value, str):
                    result[field] = html_tags_unconverter(value)
                elif isinstance(value, ObjectId):
                    result[field] = str(value)
                elif isinstance(value, list):
                    result[field] = [
                        html_tags_unconverter(v) for v in value
                    ]
            results.append(result)

        return jsonify({
            'concepts': results,
            'count': ConceptLinks.get_document_count()
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
PUT /api/concepts/<concept_link_id>
- Updates a concept by its ID.
- Expects a JSON payload with 'concepts', 'links', and 'description'.
- Returns the updated concept or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires admin privileges.
- If the user is not authenticated, returns an error message.
- If the user does not have admin privileges, returns an error message.
'''
@concept_bp.route('/<concept_link_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('concepts', 'links', 'description')
@yaml_from_file('docs/swagger/concepts/update_concept.yaml')
def update_concept(concept_link_id):
    try:
        data = sanitize_input(request.get_json())

        result = ConceptLinks.update(
            concept_link_id=concept_link_id,
            updated_data={
                'concepts': data.get('concepts'),
                'links': data.get('links'),
                'description': data.get('description')
            }
        )

        if result:
            result = ConceptLinks.get_by_id(
                concept_link_id=concept_link_id
            )
            for field, value in result.items():
                if isinstance(value, str):
                    result[field] = html_tags_unconverter(value)
                elif isinstance(value, ObjectId):
                    result[field] = str(value)
                elif isinstance(value, list):
                    result[field] = [
                        html_tags_unconverter(v) for v in value
                    ]

            return jsonify({
                'message': 'Concept updated successfully',
                'concept': result
            }), 200
        
        return jsonify({'error': 'Failed to update concept'}), 400
    
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
DELETE /api/concepts/<concept_link_id>
- Deletes a concept by its ID.
- Returns a success message or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires admin privileges.
- If the user is not authenticated, returns an error message.
- If the user does not have admin privileges, returns an error message.
'''
@concept_bp.route('/concept_link_id', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/concepts/delete_concept.yaml')
def delete_concept(concept_link_id):
    try:
        result = ConceptLinks.remove(concept_link_id=concept_link_id)
        
        if result:
            return jsonify({
                'message': 'Concept deleted successfully'
            }), 200
        
        return jsonify({'error': 'Failed to delete concept'})

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({'error': f'Internal server error'}), 500

'''
GET /api/concepts/search
- Searches for concepts based on a query string.
- Supports pagination with 'limit' and 'skip' query parameters.
- Returns a list of concept objects matching the query.
- If no concepts are found, returns an empty list and count as 0.
'''
@concept_bp.route('/search', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/concepts/search_concepts.yaml')
def search_concepts():
    try:
        user_id = get_jwt_identity()

        if not user_id:
            return jsonify({"error": "Invalid or missing user ID"}), 400
        
        manage_cooldown(user_id=user_id)

        query = request.args.get('query', '').strip()
        limit = int(request.args.get('limit', 10))
        skip = int(request.args.get('skip', 0))

        results_obj = ConceptLinks.search(query=query, skip=skip, limit=limit)
        
        if not results_obj:
            return jsonify({
                'concepts': [],
                'count': 0
            }), 200
        
        
        results = []
        for result in results_obj:
            for field, value in result.items():
                if isinstance(value, str):
                    result[field] = html_tags_unconverter(value)
                elif isinstance(value, ObjectId):
                    result[field] = str(value)
                elif isinstance(value, list):
                    result[field] = [
                        html_tags_unconverter(v) for v in value
                    ]
            results.append(result)

        return jsonify({
            'concepts': results,
            'count': ConceptLinks.get_document_count(query=query)
        }), 200
    
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503
    
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
