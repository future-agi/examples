import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import timedelta
import logging
from sqlalchemy import text

# Import models and routes
from src.models.user import db, User
from src.models.notebook import Notebook, Source, Conversation, GeneratedContent, Podcast
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.notebooks import notebooks_bp
from src.routes.chat import chat_bp
from src.routes.content import content_bp
from src.routes.podcasts import podcasts_bp

from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType
from traceai_openai import OpenAIInstrumentor
from opentelemetry import trace
from fi.evals import Evaluator
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import (
    ProjectType
)
from fi.evals import Evaluator
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="notebooklm",
    set_global_tracer_provider=True
)

OpenAIInstrumentor().instrument(tracer_provider=trace_provider)
trace.set_tracer_provider(trace_provider)

tracer = FITracer(trace_provider.get_tracer(__name__))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=30)

# Database configuration
database_path = os.path.join(os.path.dirname(__file__), 'database', 'app.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{database_path}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app, origins="*")  # Allow all origins for development

# Create upload directory
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# JWT error handlers
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'error': {
            'code': 'TOKEN_EXPIRED',
            'message': 'Token has expired'
        }
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'INVALID_TOKEN',
            'message': 'Invalid token'
        }
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'TOKEN_REQUIRED',
            'message': 'Authorization token is required'
        }
    }), 401

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(notebooks_bp, url_prefix='/api/notebooks')
app.register_blueprint(chat_bp, url_prefix='/api/chat')
app.register_blueprint(content_bp, url_prefix='/api/content')
app.register_blueprint(podcasts_bp, url_prefix='/api/podcasts')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'database': db_status,
            'version': '1.0.0',
            'timestamp': '2025-07-16T10:30:00Z'
        }
    })

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'BAD_REQUEST',
            'message': 'Bad request'
        }
    }), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_FOUND',
            'message': 'Resource not found'
        }
    }), 404

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'error': {
            'code': 'FILE_TOO_LARGE',
            'message': 'File size exceeds maximum allowed limit'
        }
    }), 413

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({
        'success': False,
        'error': {
            'code': 'INTERNAL_ERROR',
            'message': 'Internal server error'
        }
    }), 500

# Initialize database
with app.app_context():
    try:
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(database_path), exist_ok=True)
        
        # Create all tables
        db.create_all()
        logger.info("Database initialized successfully")
        
        # Create a test user if none exists (for development)
        if not User.query.first():
            from werkzeug.security import generate_password_hash
            
            test_user = User(
                email='test@example.com',
                name='Test User',
                password_hash=generate_password_hash('password123')
            )
            db.session.add(test_user)
            db.session.commit()
            logger.info("Test user created: test@example.com / password123")
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

# Frontend serving routes
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve frontend files"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return jsonify({
            'success': False,
            'error': {
                'code': 'STATIC_FOLDER_NOT_CONFIGURED',
                'message': 'Static folder not configured'
            }
        }), 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            # Return API info if no frontend is available
            return jsonify({
                'name': 'NotebookLM Open Source API',
                'version': '1.0.0',
                'description': 'Open source implementation of NotebookLM with document processing, AI chat, and podcast generation',
                'endpoints': {
                    'health': '/api/health',
                    'auth': '/api/auth/*',
                    'notebooks': '/api/notebooks/*',
                    'users': '/api/users/*'
                },
                'documentation': 'See API specifications for detailed endpoint documentation'
            })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)

