from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import requests
from app.models.course import Course
from app.models.user import User
from app.services.recommendation import RecommendationService
from app.services.content_service import ContentService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input, validate_content_structure
from app.utils.swagger_utils import yaml_from_file

courses_bp = Blueprint('courses', __name__)

# GET /api/courses
@courses_bp.route('', methods=['GET'])
@yaml_from_file('docs/swagger/courses/get_courses.yaml')
def get_courses():
    try:
            
        limit = int(request.args.get('limit', 20))
        skip = int(request.args.get('skip', 0))
        category = request.args.get('category', None)

        if category:
            courses = Course.find_by_category(category, limit, skip)
        else:
            courses = Course.find_all(limit, skip)
        return jsonify({
            "courses": courses,
            "count": len(courses),
            "skip": skip,
            "limit": limit
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# GET /api/courses/<course_id>
@courses_bp.route('/<course_id>', methods=['GET'])
@yaml_from_file('docs/swagger/courses/get_course.yaml')
def get_course(course_id):
    try:

        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({"error": "Course not found"}), 404
        course['_id'] = str(course['_id'])
        return jsonify({"course": course}), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# GET /api/courses/recommended
@courses_bp.route('/recommended', methods=['GET'], endpoint='get_recommended_courses')
@jwt_required()
@yaml_from_file('docs/swagger/courses/get_recommended_courses.yaml')
def get_recommended_courses():
    try:
        user_id = get_jwt_identity()
        
        # Get personalized course recommendations
        recommended_courses = RecommendationService.get_course_recommendations(user_id)
        
        return jsonify({
            "recommended_courses": recommended_courses,
            "count": len(recommended_courses)
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# GET /api/courses/popular
@courses_bp.route('/popular', methods=['GET'], endpoint='get_popular_courses')
@yaml_from_file('docs/swagger/courses/get_popular_courses.yaml')
def get_popular_courses():
    try:
            
        # Get query parameters
        limit = int(request.args.get('limit', 20))  # Default limit is 20
        sort = request.args.get('sort', 'popular')  # Default sort is "popular"

        # Fetch popular courses based on the sort value
        courses = Course.find_popular(limit=limit, sort=sort)

        # If no courses are found, return a 404 response
        if not courses:
            return jsonify({"error": "No popular courses found"}), 404

        # Return the list of popular courses
        return jsonify({
            "courses": courses,
            "count": len(courses),
            "limit": limit,
            "sort": sort
        }), 200

    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# POST /api/courses
@courses_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title', 'description', 'category')
@yaml_from_file('docs/swagger/courses/create_course.yaml')
def create_course():
    try:

        data = sanitize_input(request.get_json())
        
        # Extract course data
        title = data.get('title')
        description = data.get('description')
        category = data.get('category')
        prerequisites = data.get('prerequisites', [])
        content_structure = data.get('sections')
        difficulty = data.get('difficulty', 'beginner')
        tags = data.get('tags', [])

        
        # Validate content structure if provided
        if content_structure and not validate_content_structure(content_structure):
            return jsonify({"error": "Invalid content structure"}), 400
        
        # Use ContentService to create the course with proper content structure
        course = ContentService.create_course_with_content(
            title=title,
            description=description,
            category=category,
            prerequisites=prerequisites,
            content_structure=content_structure,
            difficulty=difficulty,
            tags=tags,
        )
        
        return jsonify({
            "message": "Course created successfully",
            "course": course
        }), 201
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# GET /api/courses/<course_id>/sections
@courses_bp.route('/<course_id>/sections', methods=['GET'])
@yaml_from_file('docs/swagger/courses/get_course_sections.yaml')
def get_course_sections(course_id):
    try:

        course = Course.find_by_id(course_id)
        
        if not course:
            return jsonify({"error": "Course not found"}), 404
        
        sections = course.get('content', {}).get('sections', [])
        
        return jsonify({
            "sections": sections,
            "count": len(sections)
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# POST /api/courses/<course_id>/sections
@courses_bp.route('/<course_id>/sections', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title')
@yaml_from_file('docs/swagger/courses/create_course_section_admin_only.yaml')
def add_course_section(course_id):
    try:

        data = sanitize_input(request.get_json())
        
        section_id = Course.add_section(
            course_id=course_id,
            title=data.get('title'),
            order=data.get('order')
        )
        
        if not section_id:
            return jsonify({"error": "Failed to add section"}), 400
        
        return jsonify({
            "message": "Section added successfully",
            "section_id": section_id
        }), 201
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# GET /api/courses/<course_id>/sections/<section_id>
@courses_bp.route('/<course_id>/sections/<section_id>', methods=['GET'])
@yaml_from_file('docs/swagger/courses/get_course_section.yaml')
def get_section(course_id, section_id):
    try:

        section = Course.get_section(course_id, section_id)
        
        if not section:
            return jsonify({"error": "Section not found"}), 404
        
        return jsonify({"section": section}), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# PUT /api/courses/<course_id>/sections/<section_id>
@courses_bp.route('/<course_id>/sections/<section_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('title')
@yaml_from_file('docs/swagger/courses/update_course_section_admin_only.yaml')
def update_section(course_id, section_id):
    try:
            
        data = sanitize_input(request.get_json())
        
        updated_course = Course.update_section(
            course_id=course_id,
            section_id=section_id,
            update_data=data
        )
        
        if not updated_course:
            return jsonify({"error": "Failed to update section"}), 400
        
        return jsonify({
            "message": "Section updated successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# PUT /api/courses/<course_id>
@courses_bp.route('/<course_id>', methods=['PUT'], endpoint='update_course')
@jwt_required()
@admin_required
@validate_json('title', 'description', 'category')
@yaml_from_file('docs/swagger/courses/update_course.yaml')
def update_course(course_id):
    try:
            
        data = sanitize_input(request.get_json())

        # Extract only fields to update
        update_data = {
            'title': data.get('title'),
            'description': data.get('description'),
            'category': data.get('category'),
            'prerequisites': data.get('prerequisites'),
            'difficulty': data.get('difficulty'),
            'tags': data.get('tags', []),
        }

        course = Course.find_by_id(course_id)
        if not course:
            return jsonify({
                "error": "Course not found" 
            }), 404
        # Update the course in the database
        updated_course = Course.update(course_id, update_data)
        updated_course['_id'] = str(updated_course['_id'])
        print(f'Here :: updated_course {updated_course}')

        if not updated_course:
            return jsonify({
                "error": "Failed to update course"
            }), 400
        # Return the updated course object
        return jsonify({
            "message": "Course updated successfully",
            "course": updated_course
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        print(f'\nError Message:: {e}\n')
        return jsonify({'error': 'Internal server error'}), 500

# DELETE /api/courses/<course_id>
@courses_bp.route('/<course_id>', methods=['DELETE'], endpoint='delete_course')
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/courses/delete_course_admin_only.yaml')
def delete_course(course_id):
    try:
        if not Course.find_by_id(course_id):
            return jsonify({
                "error": "Course not found"
            }), 404

        deleted_course = Course.remove_course(course_id)

        if deleted_course.deleted_count == 0:
            return jsonify({
                "error": "Failed to delete course"
            }), 400
        
        return jsonify({
            "message": "Course deleted successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# DELETE /api/courses/<course_id>/sections/<section_id>
@courses_bp.route('/<course_id>/sections/<section_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/courses/delete_course_section_admin_only.yaml')
def delete_section(course_id, section_id):
    try:
        updated_course = Course.delete_section(course_id, section_id)
        
        if not updated_course:
            return jsonify({"error": "Failed to delete section"}), 400
        
        return jsonify({
            "message": "Section deleted successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# GET /api/courses/<course_id>/sections/<section_id>/subsections
@courses_bp.route('/<course_id>/sections/<section_id>/subsections', methods=['GET'])
@yaml_from_file('docs/swagger/courses/get_course_section_subsections.yaml')
def get_subsections(course_id, section_id):
    try:
            
        section = Course.get_section(course_id, section_id)
        
        if not section:
            return jsonify({"error": "Section not found"}), 404
        
        subsections = section.get('sub_sections', [])
        
        return jsonify({
            "subsections": subsections,
            "count": len(subsections)
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# POST /api/courses/<course_id>/sections/<section_id>/subsections
@courses_bp.route('/<course_id>/sections/<section_id>/subsections', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title')
@yaml_from_file('docs/swagger/courses/create_course_section_subsection_admin_only.yaml')
def add_subsection(course_id, section_id):
    try:
            
        data = sanitize_input(request.get_json())
        
        subsection_id = Course.add_subsection(
            course_id=course_id,
            section_id=section_id,
            title=data.get('title'),
            order=data.get('order')
        )
        
        if not subsection_id:
            return jsonify({"error": "Failed to add subsection"}), 400
        
        return jsonify({
            "message": "Subsection added successfully",
            "subsection_id": subsection_id
        }), 201
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# GET /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>', methods=['GET'])
@yaml_from_file('docs/swagger/courses/get_course_section_subsection.yaml')
def get_subsection(course_id, section_id, subsection_id):
    try:
        subsection = Course.get_subsection(course_id, section_id, subsection_id)
        
        if not subsection:
            return jsonify({"error": "Subsection not found"}), 404
        
        return jsonify({"subsection": subsection}), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# PUT /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('title')
@yaml_from_file('docs/swagger/courses/update_course_section_subsection_admin_only.yaml')
def update_subsection(course_id, section_id, subsection_id):
    try:
        data = sanitize_input(request.get_json())
        
        updated_course = Course.update_subsection(
            course_id=course_id,
            section_id=section_id,
            subsection_id=subsection_id,
            update_data=data
        )
        
        if not updated_course:
            return jsonify({"error": "Failed to update subsection"}), 400
        
        return jsonify({
            "message": "Subsection updated successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# DELETE /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/courses/delete_course_section_subsection_admin_only.yaml')
def delete_subsection(course_id, section_id, subsection_id):
    try:
        updated_course = Course.delete_subsection(
            course_id=course_id,
            section_id=section_id,
            subsection_id=subsection_id
        )
        
        if not updated_course:
            return jsonify({"error": "Failed to delete subsection"}), 400
        
        return jsonify({
            "message": "Subsection deleted successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# POST /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>/content
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>/content', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('type', 'content')
@yaml_from_file('docs/swagger/courses/create_course_section_subsection_content_admin_only.yaml')
def add_content_data(course_id, section_id, subsection_id):
    try:
            
        data = sanitize_input(request.get_json())
        
        # Validate content data type
        if data.get('type') not in ['text', 'image', 'video', 'code']:
            return jsonify({"error": "Invalid content type"}), 400
        
        # Create data object
        data_object = {
            'type': data.get('type'),
            'content': data.get('content'),
            'order': data.get('order')
        }
        
        # Add additional fields based on type
        if data.get('type') == 'image':
            data_object['url'] = data.get('url')
            data_object['alt_text'] = data.get('alt_text')
            data_object['caption'] = data.get('caption')
        elif data.get('type') == 'code':
            data_object['language'] = data.get('language')
        
        success = Course.add_content_data(
            course_id=course_id,
            section_id=section_id,
            subsection_id=subsection_id,
            data_object=data_object
        )
        
        if not success:
            return jsonify({"error": "Failed to add content data"}), 400
        
        return jsonify({
            "message": "Content data added successfully"
        }), 201
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# PUT /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>', methods=['PUT'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/courses/update_course_section_subsection_content_admin_only.yaml')
def update_content_data(course_id, section_id, subsection_id, data_id):
    try:
        data = sanitize_input(request.get_json())
        
        success = Course.update_content_data(
            course_id=course_id,
            section_id=section_id,
            subsection_id=subsection_id,
            data_id=data_id,
            update_data=data
        )
        
        if not success:
            return jsonify({"error": "Failed to update content data"}), 400
        
        return jsonify({
            "message": "Content data updated successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# DELETE /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>', methods=['DELETE'])
@jwt_required()
@admin_required
@yaml_from_file('docs/swagger/courses/delete_course_section_subsection_content_admin_only.yaml')
def delete_content_data(course_id, section_id, subsection_id, data_id):
    try:
            
        success = Course.delete_content_data(
            course_id=course_id,
            section_id=section_id,
            subsection_id=subsection_id,
            data_id=data_id
        )
        
        if not success:
            return jsonify({"error": "Failed to delete content data"}), 400
        
        return jsonify({
            "message": "Content data deleted successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# POST /api/courses/enroll
@courses_bp.route('/enroll', methods=['POST'], endpoint='enroll_course')
@jwt_required()
@validate_json('course_id')
@yaml_from_file('docs/swagger/courses/enroll_user_in_a_course.yaml')
def enroll_user_in_course():
    try:
            
        data = sanitize_input(request.get_json())
        
        user_id = get_jwt_identity()
        course_id = data.get('course_id')
        
        # Check if user's in_progress_courses length is 0
        user = User.find_by_id(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if len(user.get('progress', {}).get('in_progress_courses', [])) > 0:
            return jsonify({"error": "Complete your ongoing course firstly"}), 400
        
        # Enroll user in the given course
        success = Course.enroll_user(course_id=course_id, user_id=user_id)

        if not success:
            return jsonify({"error": "Failed to enroll in course"}), 400
        
        return jsonify({
            "message": "User enrolled in course successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

# POST /api/courses/complete
@courses_bp.route('/complete', methods=['POST'], endpoint='complete_course')
@jwt_required()
@validate_json('course_id')
@yaml_from_file('docs/swagger/courses/mark_course_as_completed.yaml')
def mark_course_as_completed():
    try:
            
        data = sanitize_input(request.get_json())
        
        user_id = get_jwt_identity()
        course_id = data.get('course_id')
        
        # Mark the course as completed for the user
        success = Course.mark_course_as_completed(course_id=course_id, user_id=user_id)
        if not success:
            return jsonify({"error": "Failed to mark course as completed"}), 400
        
        return jsonify({
            "message": "Course marked as completed successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
