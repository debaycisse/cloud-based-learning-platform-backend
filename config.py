import os
from datetime import timedelta
from dotenv import load_dotenv

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
