import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    MONGO_URI = os.environ.get('MONGO_URI')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI')
    ASSESSMENT_PASS_THRESHOLD = 0.5  # 50%
    ASSESSMENT_COOLDOWN_HOURS = 72
    DATABASE_NAME = os.environ.get('DATABASE_NAME')
    FLASK_ENV = os.environ.get('FLASK_ENV')
    ASSESSMENT_PASS_THRESHOLD = float(os.environ.get('ASSESSMENT_PASS_THRESHOLD', 0.5))  # 50%

    # For image uplaod parameters
    IMGBB_API_KEY = os.getenv('IMGBB_API_KEY')
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB max file size
    ALLOWED_EXTENSIONS = ['.jpeg', '.jpg', '.png', '.gif', '.webp']

    FRONTEND_DOMAIN = "http://127.0.0.1:5173"

    # For mail server configuration parameters
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS').lower() in ['true', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL').lower() in ['true', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')  # your email
    MAIL_PASSWORD = os.environ.get('MAIL_APP_PASSWORD')  # app password or email password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)

    # Support email address
    SUPPORT_EMAIL = os.environ.get('SUPPORT_EMAIL')
