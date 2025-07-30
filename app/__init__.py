from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_mail import Mail
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from config import Config
from app.swagger import setup_swagger
from flask_cors import CORS

# Initialize extensions
mail = Mail()
jwt = JWTManager()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"],
)
mongo_client = None
db = None

'''
Application factory function for creating and configuring the Flask app.
- Loads configuration from the provided config class.
- Initializes Flask extensions (JWT, Mail, Limiter, CORS).
- Sets up MongoDB connection and JWT token blacklist checking.
- Registers all application blueprints for routing.
- Configures Swagger UI for API documentation.
Args:
    config_class (class, optional): The configuration class to use. Defaults to Config.
Returns:
    Flask: The configured Flask application instance.
'''
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure JWT to exempt OPTIONS requests from authentication
    app.config['JWT_EXEMPT_OPTIONS'] = True
    
    # Initialize CORS with more specific settings
    CORS(app, 
         resources={r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
         }},
         supports_credentials=True)
    
    # Initialize extensions with app
    jwt.init_app(app)
    limiter.init_app(app)
    mail.init_app(app)
    
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
    from app.routes.recommendations import recommendations_bp
    from app.routes.images import images_bp
    from app.routes.contact_support import email_bp
    from app.routes.concept_link import concept_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(courses_bp, url_prefix='/api/courses')
    app.register_blueprint(assessments_bp, url_prefix='/api/assessments')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(learning_paths_bp, url_prefix='/api/learning-paths')
    app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
    app.register_blueprint(images_bp, url_prefix='/api/images')
    app.register_blueprint(email_bp, url_prefix='/api/email')
    app.register_blueprint(concept_bp, url_prefix='/api/concepts')
    

    # Setup Swagger UI
    setup_swagger(app)

    return app
