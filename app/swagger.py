from flasgger import Swagger

def setup_swagger(app):
    """Configure Swagger UI for the application"""
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Learning Platform API",
            "description": "API documentation for the Learning Platform",
            "version": "1.0.0",
            "contact": {
                "email": "debaycisse@gmail.com"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "basePath": "/",
        "schemes": [
            "http",
            "https"
        ],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Authorization: Bearer {token}\""
            }
        },
        "security": [
            {
                "Bearer": []
            }
        ],
        "tags": [
            {
                "name": "Authentication",
                "description": "User authentication operations"
            },
            {
                "name": "Users",
                "description": "User profile and preference operations"
            },
            {
                "name": "Courses",
                "description": "Course management operations"
            },
            {
                "name": "Assessments",
                "description": "Assessment and quiz operations"
            },
            {
                "name": "Learning Paths",
                "description": "Learning path operations"
            },
            {
                "name": "Recommendations",
                "description": "Personalized recommendation operations"
            },
            {
                "name": "Questions",
                "description": "Question management operations"
            },
            {
                "name": "Images",
                "description": "Images upload managements"
            }
        ]
    }
    

    Swagger(app, config=swagger_config, template=swagger_template)