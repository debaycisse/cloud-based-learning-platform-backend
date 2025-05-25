from flask import Blueprint, request, jsonify
import requests
from app.utils.validation import validate_json, validate_email
from app.utils.email import contact_support_email

email_bp = Blueprint('email', __name__)

@email_bp.route('/contact_support', methods=['POST'])
@validate_json('data')
def contact_support():
    """
    Endpoint to handle contact support requests.
    Expects a JSON payload with 'email', 'subject', and 'message'.
    """
    try:
        data = request.json.get('data', {})
        
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')

        if email is None or subject is None or message is None:
            return jsonify({"error": "Email, subject, and message are required"}), 400

        if not validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400

        success = contact_support_email(
            from_email=email,
            subject=f'[CBLP] {subject}',
            message=message
        )
        
        if success:
            return jsonify({"message": "Support request sent successfully"}), 200
        else:
            return jsonify({"error": "Failed to send support request"}), 400
    except requests.RequestException as e:
        return jsonify({"error": f"Network error: {str(e)}"}), 503
    
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
