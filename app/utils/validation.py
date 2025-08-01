import re
import html
from flask import request, jsonify, current_app
from functools import wraps
from os import path
from werkzeug.utils import secure_filename
import magic
import os
from config import Config

'''
Validation utilities for Flask application.
These utilities include input validation for email, password,
username, and JSON request data.
'''

'''
Validates full name format
- 3-50 characters
- Alphabets and spaces only
Args:
    name (str): The full name to validate
Returns:
    bool: True if valid, False otherwise
'''
def validate_full_name(name):
    """
    Validate full name
    - 3-50 characters
    - Alphabets and spaces only
    """
    # Check length
    if len(name) < 3 or len(name) > 50:
        return False
    
    # Check for alphabets and spaces only
    pattern = r'^[a-zA-Z\s]{3,50}$'
    return re.match(pattern, name) is not None

'''
Validates email format
- Uses regex to check if the email is valid
Args:
    email (str): The email address to validate
Returns:
    bool: True if valid, False otherwise
'''
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

'''
Validates password strength
- At least 8 characters
- Contains at least one digit
- Contains at least one uppercase letter
Args:
    password (str): The password to validate
Returns:
    bool: True if valid, False otherwise
'''
def validate_password(password):
    if len(password) < 8:
        return False
    if not any(char.isdigit() for char in password):
        return False
    if not any(char.isupper() for char in password):
        return False
    return True

'''
Validates username format
- 3-20 characters
- Alphanumeric and underscores only
Args:
    username (str): The username to validate
Returns:
    bool: True if valid, False otherwise
'''
def validate_username(username):
    """
    Validate username
    - 3-20 characters
    - Alphanumeric and underscores only
    """
    pattern = r'^[a-zA-Z0-9_]{3,20}$'
    return re.match(pattern, username) is not None

'''
Validates JSON request data
- Checks if the request is JSON
- Checks if required fields are present
Args:
    required_fields (list): List of required fields
Returns:
    decorator: The decorated function
Usage:
    @app.route('/api/some_endpoint', methods=['POST'])
    @validate_json('field1', 'field2')
    def some_endpoint():
        # Your endpoint logic here
        pass
'''
def validate_json(*required_fields):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Request must be JSON"}), 400
            
            data = request.get_json()
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                return jsonify({
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }), 400
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

'''
Validates that a valid email is given
Args:
    email - the email to be validated
Returns:
    True if it is a vliad email, false otherwise.
'''
def validate_website_link(link):
    pattern = r'^(https?:\/\/)?(www\.)?([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(/[\w\-._~:/?#\[\]@!$&\'()*+,;=]*)?$'
    return re.match(pattern, link) is not None

'''
Sanitizes input data to prevent injection attacks
- Removes HTML tags
- Escapes special characters
Args:
    data (str or dict): The input data to sanitize
Returns:
    str or dict: The sanitized data
'''
def sanitize_input(data):
    if isinstance(data, str):
        return html.escape(html.unescape(data))  # converts < to &lt;, > to &gt;, etc.
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data

'''
Converts HTML-escaped text (like &lt;h1&gt;) into actual HTML tags as a string.

Parameters:
    text (str): Escaped HTML string.

Returns:
    str: Unescaped HTML as a plain string.
'''
def html_tags_converter(text: str) -> str:
    if isinstance(text, str):
        return html.escape(text)
    
    raise TypeError("html_tags_converter expects a string input")

'''
Unonverts HTML-escaped text (like &lt;h1&gt;) into actual HTML tags as a string.

Parameters:
    text (str): Escaped HTML string.

Returns:
    str: Unescaped HTML as a plain string.
'''
def html_tags_unconverter(text: str) -> str:
    if isinstance(text, str):
        return html.unescape(text)
    
    raise TypeError("html_tags_unconverter expects a string input")

'''
Validates the course content structure
- Must have a "sections" array
- Each section must have a title
- Each subsection must have a title
- Each data object must have a type and content
Args:
    content (dict): The course content structure
Returns:
    bool: True if valid, False otherwise
'''
def validate_content_structure(content):
    if not isinstance(content, list):
        return False
    
    #if not isinstance(content['sections'], list):
    #    return False
    
    for section in content:
        if not isinstance(section, dict) or 'title' not in section:
            return False
        
        if 'sub_sections' in section:
            if not isinstance(section['sub_sections'], list):
                return False
            
            for subsection in section['sub_sections']:
                if not isinstance(subsection, dict) or 'title' not in subsection:
                    return False
                
                if 'data' in subsection:
                    if not isinstance(subsection['data'], list):
                        return False
                    
                    for data_obj in subsection['data']:
                        if not isinstance(data_obj, dict) or 'type' not in data_obj or 'content' not in data_obj:
                            return False
                        
                        # Validate specific data types
                        if data_obj['type'] == 'image' and ('url' not in data_obj):
                            return False
    
    return True

'''
Validates if the uploaded file is a valid image of an allowed type.
- Saves the file temporarily and checks its MIME type.
- Ensures the file is an image and matches allowed extensions.
Args:
    file_stream: The uploaded file stream (e.g., from Flask's request.files).
Returns:
    bool: True if the file is a valid image of an allowed type, False otherwise.
'''
def is_valid_image(file_stream):
    # Save file temporarily
    temp_path = path.join('/tmp', secure_filename('temp_file'))
    file_stream.save(temp_path)
    file_stream.seek(0)  # Reset file pointer to beginning for later use
    
    try:
        # Check MIME type
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(temp_path)
        
        if not file_type.startswith('image/'):
            return False
        # Check for allowed extensions based on MIME type
        extension_map = {
            'image/jpeg': ['.jpg', '.jpeg'],
            'image/png': ['.png'],
            'image/gif': ['.gif'],
            'image/webp': ['.webp']
        }
        for mime_type, extensions in extension_map.items():
            if file_type == mime_type and any(ext in Config.ALLOWED_EXTENSIONS for ext in extensions):
                return True
        return False
        
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)

'''
Transforms the sanitized course's data to their original form
-Args:
    course_object - the course object whose data is to be transformed
-Returns:
    the transformed course or none if empty course object is passed
'''
def transform_sanitized_course(course_object):
    if course_object and isinstance(course_object, dict):
        for key, value in course_object.items():
                if key == 'title' or key == 'description':
                    course_object[key] = html_tags_unconverter(value)
                elif key == 'content' and isinstance(value, dict):
                    for section in value.get('sections', []):
                        section['title'] = html_tags_unconverter(section.get('title', ''))
                        for subsection in section.get('sub_sections', []):
                            subsection['title'] = html_tags_unconverter(subsection.get('title', ''))
                            for content_data in subsection.get('data', []):
                                if isinstance(content_data, dict):
                                    if content_data.get('type') == 'text':
                                        content_data['content'] = html_tags_unconverter(content_data.get('content', ''))
                                    elif content_data.get('type') == 'image':
                                        content_data['caption'] = html_tags_unconverter(content_data.get('caption', ''))
                                        content_data['alt_text'] = html_tags_unconverter(content_data.get('alt_text', ''))
                                    elif content_data.get('type') == 'video':
                                        content_data['description'] = html_tags_unconverter(content_data.get('description', ''))
                                    elif content_data.get('type') == 'code':
                                        content_data['code'] = html_tags_unconverter(content_data.get('code', ''))
        return course_object
    return None

'''
Transforms the sanitized list of courses' data to their original form
- Args:
    course_list - the list that contains multiple course objects whose data are to be transformed
- Returns:
    the transformed list or none if no (empty) list of course is passed
'''
def transform_sanitized_course_list(course_list):
    if isinstance(course_list, list) and len(course_list) > 0:
        for course_object in course_list:
            for key, value in course_object.items():
                    if key == 'title' or key == 'description':
                        course_object[key] = html_tags_unconverter(value)
                    elif key == 'content' and isinstance(value, dict):
                        for section in value.get('sections', []):
                            section['title'] = html_tags_unconverter(section.get('title', ''))
                            for subsection in section.get('sub_sections', []):
                                subsection['title'] = html_tags_unconverter(subsection.get('title', ''))
                                for content_data in subsection.get('data', []):
                                    if isinstance(content_data, dict):
                                        if content_data.get('type') == 'text':
                                            content_data['content'] = html_tags_unconverter(content_data.get('content', ''))
                                        elif content_data.get('type') == 'image':
                                            content_data['caption'] = html_tags_unconverter(content_data.get('caption', ''))
                                            content_data['alt_text'] = html_tags_unconverter(content_data.get('alt_text', ''))
                                        elif content_data.get('type') == 'video':
                                            content_data['description'] = html_tags_unconverter(content_data.get('description', ''))
                                        elif content_data.get('type') == 'code':
                                            content_data['code'] = html_tags_unconverter(content_data.get('code', ''))
        return course_list
    return None

