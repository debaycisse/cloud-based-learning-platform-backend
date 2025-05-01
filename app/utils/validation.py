import re
from flask import request, jsonify
from functools import wraps

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
    bool: True if valid, False otherwise'''
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
        # Remove HTML tags
        data = re.sub(r'<[^>]*>', '', data)
        # Escape special characters
        data = data.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        data = data.replace('"', '&quot;').replace("'", '&#39;')
    elif isinstance(data, dict):
        return {k: sanitize_input(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_input(item) for item in data]
    return data


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
    if not isinstance(content, dict) or 'sections' not in content:
        return False
    
    if not isinstance(content['sections'], list):
        return False
    
    for section in content['sections']:
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
