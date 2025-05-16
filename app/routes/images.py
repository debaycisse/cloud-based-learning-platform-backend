from dotenv import load_dotenv
load_dotenv()

import os
import requests
from werkzeug.utils import secure_filename
import magic
from app.utils.validation import is_valid_image
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from app.utils.auth import admin_required
from config import Config


images_bp = Blueprint('images', __name__)

@images_bp.route('/upload', methods=['POST'])
@jwt_required()
@admin_required
def upload_image():
    """
    Endpoint to upload an image to ImgBB
    
    Requires:
    - 'image' file in request
    
    Optional:
    - 'expiry' in seconds (default: none)
    - 'name' custom file name
    
    Returns:
    - JSON with image URL or error details
    """
    # Check if the post request has the file part

    if 'image' not in request.files:
        return jsonify({'error': 'No image file in request'}), 400

    file = request.files['image']
    
    
    # Check if file is empty
    if file.filename == '':
        return jsonify({'error': 'Empty file submitted'}), 400
    
    # Check file size before processing
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > Config.MAX_CONTENT_LENGTH:
        return jsonify({
            'error': f'File too large. Maximum size is {Config.MAX_CONTENT_LENGTH/1024/1024}MB'
        }), 413
    
    # Validate file is actually an image
    if not is_valid_image(file):
        return jsonify({
            'error': 'Invalid file. Only JPEG, PNG, GIF and WEBP images are allowed'
        }), 415
    
    try:
        # Prepare optional parameters
        expiry = request.form.get('expiry', None)
        name = request.form.get('name', None)
        
        # Prepare the payload for ImgBB
        payload = {
            'key': Config.IMGBB_API_KEY
        }
        
        if expiry:
            try:
                payload['expiration'] = int(expiry)
            except ValueError:
                return jsonify({'error': 'Expiry must be an integer (seconds)'}), 400
        
        if name:
            payload['name'] = name
        # Reset file pointer and prepare for upload
        file.seek(0)
        
        # Upload to ImgBB
        files = {'image': (file.filename, file, file.content_type)}
        
        response = requests.post(
            'https://api.imgbb.com/1/upload',
            files=files,
            data=payload
        )
        
        # Handle response
        if response.status_code != 200:
            return jsonify({
                'error': f'ImgBB upload failed with status code: {response.status_code}'
            }), 502
            
        response_data = response.json()
        
        if not response_data.get('success'):
            error_msg = response_data.get('error', {}).get('message', 'Unknown error')
            return jsonify({'error': f'ImgBB upload failed: {error_msg}'}), 502
        
        # Return success with image URLs
        image_data = response_data['data']
        
        return jsonify({
			'url': image_data['url']
        }), 200
        
    except requests.RequestException as e:
        return jsonify({'error': f'Network error: {str(e)}'}), 503

    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500
