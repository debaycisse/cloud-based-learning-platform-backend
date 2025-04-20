from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models.course import Course
from app.services.recommendation import RecommendationService
from app.services.content_service import ContentService
from app.utils.auth import admin_required
from app.utils.validation import validate_json, sanitize_input, validate_content_structure

courses_bp = Blueprint('courses', __name__)

'''
Course Management routes for retrieving, creating, and managing course content.
These routes include JWT authentication, input validation, and data sanitization.
'''

'''
Retrieves a list of courses
- GET /api/courses
- Query parameters: limit, skip, category
- Response: JSON with list of courses, count, skip, and limit
- JWT required
'''
@courses_bp.route('', methods=['GET'])
def get_courses():
    limit = int(request.args.get('limit', 20))
    skip = int(request.args.get('skip', 0))
    category = request.args.get('category')
    
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

'''
Retrieves a specific course by ID
- GET /api/courses/<course_id>
- Response: JSON with course details
'''
@courses_bp.route('/<course_id>', methods=['GET'])
def get_course(course_id):
    course = Course.find_by_id(course_id)
    
    if not course:
        return jsonify({"error": "Course not found"}), 404
    
    return jsonify({"course": course}), 200

'''
Retrieves personalized course recommendations for the logged-in user
- GET /api/courses/recommended
- Response: JSON with list of recommended courses
- JWT required
'''
@courses_bp.route('/recommended', methods=['GET'])
@jwt_required()
def get_recommended_courses():
    user_id = get_jwt_identity()
    
    # Get personalized course recommendations
    recommended_courses = RecommendationService.get_course_recommendations(user_id)
    
    return jsonify({
        "recommended_courses": recommended_courses,
        "count": len(recommended_courses)
    }), 200

'''
Creates a new course
- POST /api/courses
- Request body: JSON with course details
- Response: JSON with success message and course details
- JWT required
- Admin privileges required
'''
@courses_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title', 'description', 'category')
def create_course():
    data = sanitize_input(request.get_json())
    
    # Extract course data
    title = data.get('title')
    description = data.get('description')
    category = data.get('category')
    prerequisites = data.get('prerequisites', [])
    content_structure = data.get('content')
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
        content_structure=content_structure
    )
    
    return jsonify({
        "message": "Course created successfully",
        "course": course
    }), 201

# New routes for managing course content structure

'''
Retrieves sections of a specific course
- GET /api/courses/<course_id>/sections
- Response: JSON with list of sections and count
'''
@courses_bp.route('/<course_id>/sections', methods=['GET'])
def get_course_sections(course_id):
    course = Course.find_by_id(course_id)
    
    if not course:
        return jsonify({"error": "Course not found"}), 404
    
    sections = course.get('content', {}).get('sections', [])
    
    return jsonify({
        "sections": sections,
        "count": len(sections)
    }), 200

'''
Adds a new section to a specific course
- POST /api/courses/<course_id>/sections
- Request body: JSON with section details
- Response: JSON with success message and section ID
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title')
def add_course_section(course_id):
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

'''
Retrieves a specific section of a course
- GET /api/courses/<course_id>/sections/<section_id>
- Response: JSON with section details
'''
@courses_bp.route('/<course_id>/sections/<section_id>', methods=['GET'])
def get_section(course_id, section_id):
    section = Course.get_section(course_id, section_id)
    
    if not section:
        return jsonify({"error": "Section not found"}), 404
    
    return jsonify({"section": section}), 200

'''
Updates a specific section of a course
- PUT /api/courses/<course_id>/sections/<section_id>
- Request body: JSON with section details
- Response: JSON with success message
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('title')
def update_section(course_id, section_id):
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

'''
Deletes a specific section of a course
- DELETE /api/courses/<course_id>/sections/<section_id>
- Response: JSON with success message
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_section(course_id, section_id):
    updated_course = Course.delete_section(course_id, section_id)
    
    if not updated_course:
        return jsonify({"error": "Failed to delete section"}), 400
    
    return jsonify({
        "message": "Section deleted successfully"
    }), 200

'''
Retrieves subsections of a specific section in a course
- GET /api/courses/<course_id>/sections/<section_id>/subsections
- Response: JSON with list of subsections and count
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections', methods=['GET'])
def get_subsections(course_id, section_id):
    section = Course.get_section(course_id, section_id)
    
    if not section:
        return jsonify({"error": "Section not found"}), 404
    
    subsections = section.get('sub_sections', [])
    
    return jsonify({
        "subsections": subsections,
        "count": len(subsections)
    }), 200

'''
Adds a new subsection to a specific section in a course
- POST /api/courses/<course_id>/sections/<section_id>/subsections
- Request body: JSON with subsection details
- Response: JSON with success message and subsection ID
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('title')
def add_subsection(course_id, section_id):
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

'''
Retrieves a specific subsection of a section in a course
- GET /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>
- Request body: JSON with subsection details
- Response: JSON with subsection details
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>', methods=['GET'])
def get_subsection(course_id, section_id, subsection_id):
    subsection = Course.get_subsection(course_id, section_id, subsection_id)
    
    if not subsection:
        return jsonify({"error": "Subsection not found"}), 404
    
    return jsonify({"subsection": subsection}), 200

'''
Updates a specific subsection of a section in a course
- PUT /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>
- Request body: JSON with subsection details
- Response: JSON with success message
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>', methods=['PUT'])
@jwt_required()
@admin_required
@validate_json('title')
def update_subsection(course_id, section_id, subsection_id):
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

'''
Deletes a specific subsection of a section in a course
- DELETE /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>
- Request body: JSON with subsection details
- Response: JSON with success message
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_subsection(course_id, section_id, subsection_id):
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

'''
Adds content data to a specific subsection in a course
- POST /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>/content
- Request body: JSON with content data
- Response: JSON with success message and content data ID
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>/content', methods=['POST'])
@jwt_required()
@admin_required
@validate_json('type', 'content')
def add_content_data(course_id, section_id, subsection_id):
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

'''
Updates a specific content data in a subsection of a course
- PUT /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>
- Request body: JSON with content data
- Response: JSON with success message
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_content_data(course_id, section_id, subsection_id, data_id):
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

'''
Deletes a specific content data in a subsection of a course
- DELETE /api/courses/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>
- Request body: JSON with content data
- Response: JSON with success message
- JWT required
- Admin privileges required
'''
@courses_bp.route('/<course_id>/sections/<section_id>/subsections/<subsection_id>/content/<data_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_content_data(course_id, section_id, subsection_id, data_id):
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
