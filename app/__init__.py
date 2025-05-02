from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from config import Config
from app.swagger import setup_swagger

# Initialize extensions
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
)
mongo_client = None
db = None

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    jwt.init_app(app)
    limiter.init_app(app)
    
    # Initialize MongoDB connection
    global mongo_client, db
    mongo_client = MongoClient(app.config['MONGO_URI'])
    db = mongo_client[app.config['DATABASE_NAME']]

    # Blacklist check function
    @jwt.token_in_blocklist_loader
    def check_if_token_in_blacklist(jwt_header, jwt_payload):
        jti = jwt_payload['jti']  # Get the unique identifier of the token
        # Check if the token exists in the blacklist collection
        token = db.token_blacklist.find_one({"jti": jti})
        return token is not None  # Return True if the token is blacklisted
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.courses import courses_bp
    from app.routes.assessments import assessments_bp
    from app.routes.questions import questions_bp
    from app.routes.learning_paths import learning_paths_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(assessments_bp, url_prefix='/api/assessments')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(learning_paths_bp, url_prefix='/api/learning-paths')

    # Setup Swagger UI
    setup_swagger(app)
    
    return app
