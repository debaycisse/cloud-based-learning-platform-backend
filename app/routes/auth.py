from flask import current_app
import requests
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    decode_token
)
from app.models.user import User
from app.utils.validation import (
    validate_json,
    validate_full_name,
    validate_email,
    validate_password,
    validate_username,
    sanitize_input
)
from app import limiter, db
from app.utils.swagger_utils import yaml_from_file
from app.utils.email import (
    send_reset_email, 
    send_login_email
)
from app.utils.cooldown_manager import manage_cooldown

auth_bp = Blueprint('auth', __name__)

'''
Authentication routes for user registration, login, logout, and profile retrieval.
These routes include input validation, rate limiting, and JWT token generation.
'''

'''
POST /api/auth/register
- Registers a new user.
- Expects a JSON payload with 'name', 'email', 'username', and 'password'.
- Returns a success message or an error message.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Rate limit: 5 requests per minute.
'''
@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json('name', 'email', 'username', 'password')
@yaml_from_file('docs/swagger/auth/register.yaml')
def register():
    try:
        data = sanitize_input(request.get_json())
        name = data.get('name')
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')
        
        # Validate input
        if not validate_full_name(name):
            return jsonify({"error": "Name must contain only letters and spaces"}), 400

        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        if not validate_username(username):
            return jsonify({"error": "Username must be 3-20 characters and contain only letters, numbers, and underscores"}), 400
        
        if not validate_password(password):
            return jsonify({"error": "Password must be at least 8 characters and contain at least one digit and one uppercase letter"}), 400
        
        # Check if user already exists
        if User.find_by_email(email):
            return jsonify({"error": "Email already registered"}), 400
        
        if User.find_by_username(username):
            return jsonify({"error": "Username already taken"}), 400
        
        # Create user
        user = User.create(name, email, username, password)
        
        # Generate access token
        access_token = create_access_token(identity=str(user['_id']))

        # Send login link to the user's email        
        send_login_email(user.get('email'), user.get('name'))

        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "_id": str(user.get('_id', None)),
                "name": user.get('name', None),
                "email": user.get('email', None),
                "username": user.get('username', None),
                "role": user.get('role', None),
                "created_at": user.get('created_at', None),
                "updated_at": user.get('updated_at', None),
                "progress": user.get('progress', {}),
                "preferences": user.get('preferences', {})
            }
        }), 201

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 400

'''
POST /api/auth/login
- Logs in a user.
- Expects a JSON payload with 'email' and 'password'.
- Returns a success message with an access token or an error message.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Rate limit: 5 requests per minute.
'''
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json('email', 'password')
@yaml_from_file('docs/swagger/auth/login.yaml')
def login():
    try:
        data = sanitize_input(request.get_json())
        email = data.get('email', '')
        password = data.get('password', '')

        # Find user by email
        user = User.find_by_email(email)

        manage_cooldown(user_id=user.get('_id', ''))
        
        # Check password
        if not user or not User.check_password(user, password):
            return jsonify({"error": "Invalid email or password"}), 401
        

        # Generate access token
        access_token = create_access_token(identity=str(user['_id']))
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "_id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "username": user['username'],
                "role": user['role'],
                "created_at": user['created_at'],
                "updated_at": user['updated_at'],
                "progress": user['progress'],
                "preferences": user['preferences']
            }
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


'''
POST /api/auth/logout
- Logs out a user by blacklisting the JWT token.
- Returns a success message or an error message.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
'''
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
@yaml_from_file('docs/swagger/auth/logout.yaml')
def logout():
    try:
        # Get the unique identifier (jti) of the token
        jti = get_jwt()['jti']
        # Set expiry time (e.g., 24 hours)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        # Add the token to the blacklist collection in MongoDB
        db.token_blacklist.insert_one({"jti": jti, "expires_at": expires_at})
        # Automatically remove expired tokens
        db.token_blacklist.create_index("expires_at", expireAfterSeconds=0)
        
        return jsonify({"message": "Logout successful"}), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 400


'''
GET /api/auth/user
- Retrieves the authenticated user's profile.
- Returns the user's details or an error message if not found.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Requires user authentication.
- If the user is not authenticated, returns an error message.
- If the user does not have access to the profile, returns an error message.
'''
@auth_bp.route('/user', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/auth/get_user.yaml')
def get_user():
    try:
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        manage_cooldown(user_id=user_id)
        
        return jsonify({
            "user": {
                "_id": str(user['_id']),
                "name": user['name'],
                "email": user['email'],
                "username": user['username'],
                "role": user.get('role', 'user'),
                "created_at": user.get('created_at', None),
                "updated_at": user.get('updated_at', None),
                "progress": user.get('progress'),
                "preferences": user.get('preferences'),
            }
        }), 200
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 400

'''
POST /api/auth/reset_password
- Initiates the password reset process by sending a reset token to the user's email.
- Expects a JSON payload with 'email'.
- Returns a success message or an error message.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Rate limit: 5 requests per minute.
'''
@auth_bp.route('/reset_password', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json('email')
@yaml_from_file('docs/swagger/auth/reset_password.yaml')
def reset_password():
    try:

        data = sanitize_input(request.get_json())
        email = data.get('email')
        
        # Validate email
        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        # Find user by email
        user = User.find_by_email(email)

        if not user:
            return jsonify({"error": "User not found"}), 404
        
        manage_cooldown(user_id=user.get('_id', ''))
        
        # Generate reset token
        reset_token = create_access_token(identity=str(user['_id']), expires_delta=timedelta(hours=1))

        # Send reset token to user's email
        is_sent = send_reset_email(
            to_email=email,
            token=reset_token,
            username=user.get('name'))
        
        if not is_sent:
            return jsonify({
                'error': 'Internal server error'
            }), 500
        
        return jsonify({
            "message": "Reset token is sent to user's email",
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
GET /api/auth/verify_reset_token/<token>
- Verifies the reset token.
- Returns a success message if the token is valid or an error message if invalid.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Rate limit: 5 requests per minute.
'''
@auth_bp.route('/verify_reset_token/<token>', methods=['GET'])
@limiter.limit("5 per minute")
@yaml_from_file('docs/swagger/auth/verify_reset_token.yaml')
def verify_reset_token(token):
    # Verify the token
    try:
        decoded = decode_token(token)
        user = User.find_by_id(decoded['sub'])
        
        if not user:
            return jsonify({"error": "Invalid token"}), 401
        
        return jsonify({
            "message": "Token is valid",
            "is_valid": True
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

'''
PUT /api/auth/update_password/<token>
- Updates the user's password using the reset token.
- Expects a JSON payload with 'new_password'.
- Returns a success message or an error message if the token is invalid or password update fails.
- If the request fails, returns a network error message.
- If an internal server error occurs, returns an error message.
- Rate limit: 5 requests per minute.
'''
@auth_bp.route('/update_password/<token>', methods=['PUT'])
@limiter.limit("5 per minute")
@validate_json('new_password')
@yaml_from_file('docs/swagger/auth/update_password.yaml')
def update_password(token):
    try:
        # Verify the token
        data = sanitize_input(request.get_json())
        new_password = data.get('new_password')
        
        # Validate new password
        if not validate_password(new_password):
            return jsonify({"error": "Password must be at least 8 characters and contain at least one digit and one uppercase letter"}), 400
        
        decoded = decode_token(token)
        identity = decoded['sub']
        user = User.find_by_id(identity)
        
        if not user:
            return jsonify({"error": "Invalid token"}), 401
        
        # Update password
        updated_user = User.update_password(user, new_password)

        if updated_user.get('_id') != user.get('_id'):
            return jsonify({
                'error': 'Password update failure occured'
            }), 400
        
        return jsonify({
            "message": "Password updated successfully"
        }), 200
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
