from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app import limiter
from app.models.user import User

'''
Authentication and authorization utilities for Flask application.
These utilities include JWT verification, role-based access control,
input validation, and rate limiting.
'''
def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.find_by_id(user_id)
        
        if not user or user.get('role') != 'admin':
            return jsonify({"error": "Admin privileges required"}), 403
        
        return fn(*args, **kwargs)
    return wrapper

'''
Ensures all requests are rate-limited to prevent abuse.
This decorator applies a rate limit to the endpoint, allowing
a specified number of requests per minute.
Args:
    limit_string (str): The rate limit string, e.g., "5 per minute".
Returns:
    decorator: The decorated function.
Usage:
    @app.route('/api/some_endpoint', methods=['GET'])
    @rate_limit_by_ip("5 per minute")
    def some_endpoint():
        return jsonify({"message": "Success"})
'''
def rate_limit_by_ip(limit_string):
    def decorator(f):
        # Apply the limiter directly using the imported limiter instance
        rate_limited_function = limiter.limit(limit_string)(f)
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # The limiter.limit decorator will handle the rate limiting logic
            # If the limit is exceeded, it will return a 429 Too Many Requests response
            return rate_limited_function(*args, **kwargs)
        
        return decorated_function
    return decorator


