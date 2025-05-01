from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
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

auth_bp = Blueprint('auth', __name__)

'''
Authentication routes for user registration, login, logout, and profile retrieval.
These routes include input validation, rate limiting, and JWT token generation.
'''

'''
Registers a new user
- POST /api/auth/register
- Request body: JSON with 'email', 'username', and 'password'
- Response: JSON with success message, http status code and JWT access token
- Rate limit: 5 requests per minute
'''
@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json('name', 'email', 'username', 'password')
@yaml_from_file('docs/swagger/auth/register.yaml')
def register():
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
    user = User.create(email, username, password)
    
    # Generate access token
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        "message": "User registered successfully",
        "access_token": access_token,
        "user": {
            "id": str(user['_id']),
            "name": user['name'],
            "email": user['email'],
            "username": user['username']
        }
    }), 201

'''
Logs in a user
- POST /api/auth/login
- Request body: JSON with 'email' and 'password'
- Response: JSON with success message, http status code, JWT access token, and user details
- Rate limit: 5 requests per minute
'''
@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
@validate_json('email', 'password')
@yaml_from_file('docs/swagger/auth/login.yaml')
def login():
    data = sanitize_input(request.get_json())
    email = data.get('email')
    password = data.get('password')
    
    # Find user by email
    user = User.find_by_email(email)
    
    # Check password
    if not user or not User.check_password(user, password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Generate access token
    access_token = create_access_token(identity=str(user['_id']))
    
    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": str(user['_id']),
            "name": user['name'],
            "email": user['email'],
            "username": user['username']
        }
    }), 200


'''
Logs out a user
- POST /api/auth/logout
- Response: JSON with success message, http status code
- Requires Access token
'''
@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
@yaml_from_file('docs/swagger/auth/logout.yaml')
def logout():
    # Get the unique identifier (jti) of the token
    jti = get_jwt()['jti']
    # Set expiry time (e.g., 24 hours)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    # Add the token to the blacklist collection in MongoDB
    db.token_blacklist.insert_one({"jti": jti, "expires_at": expires_at})
    # Automatically remove expired tokens
    db.token_blacklist.create_index("expires_at", expireAfterSeconds=0)
    
    return jsonify({"message": "Logout successful"}), 200


'''
Retrieves the current user's profile
- GET /api/auth/user
- Response: JSON with user details, http status code
- Requires Access token
'''
@auth_bp.route('/user', methods=['GET'])
@jwt_required()
@yaml_from_file('docs/swagger/auth/get_user.yaml')
def get_user():
    user_id = get_jwt_identity()
    user = User.find_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "user": {
            "id": str(user['_id']),
            "name": user['name'],
            "email": user['email'],
            "username": user['username'],
            "role": user.get('role', 'user'),
            "created_at": user.get('created_at').isoformat() if user.get('created_at') else None
        }
    }), 200
