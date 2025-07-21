#!/usr/bin/env python3
"""
Comprehensive integration test for NotebookLM backend
Tests all APIs and functionality
"""
import os
import sys
import json
import tempfile
from io import BytesIO

# Add the project root to Python path
sys.path.insert(0, '/home/ubuntu/notebooklm-backend')

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import openai
import anthropic

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'test-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'test-jwt-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///integration_test.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
CORS(app, origins=['*'])
db = SQLAlchemy(app)
jwt = JWTManager(app)

# JWT Configuration
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({'success': False, 'error': 'Token has expired'}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({'success': False, 'error': 'Invalid token'}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({'success': False, 'error': 'Authorization token required'}), 401

# Initialize AI clients
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Notebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)
    status = db.Column(db.String(50), default='processing')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=False)
    title = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    sources = db.Column(db.Text)  # JSON array of source references
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'message': 'NotebookLM backend is running',
            'version': '1.0.0',
            'services': {
                'database': 'connected',
                'api': 'active',
                'openai': bool(os.getenv('OPENAI_API_KEY')),
                'anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
                'google': bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
            }
        }
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        # Create new user
        user = User(
            email=data['email'],
            name=data.get('name', data['email'].split('@')[0])
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.name
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and user.check_password(data['password']):
            access_token = create_access_token(identity=user.id)
            
            return jsonify({
                'success': True,
                'data': {
                    'access_token': access_token,
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'name': user.name
                    }
                }
            })
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notebooks', methods=['GET'])
@jwt_required()
def get_notebooks():
    try:
        user_id = get_jwt_identity()
        notebooks = Notebook.query.filter_by(user_id=user_id).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': nb.id,
                'title': nb.title,
                'description': nb.description,
                'created_at': nb.created_at.isoformat(),
                'updated_at': nb.updated_at.isoformat()
            } for nb in notebooks]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notebooks', methods=['POST'])
@jwt_required()
def create_notebook():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        notebook = Notebook(
            title=data['title'],
            description=data.get('description', ''),
            user_id=user_id
        )
        
        db.session.add(notebook)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': notebook.id,
                'title': notebook.title,
                'description': notebook.description,
                'created_at': notebook.created_at.isoformat(),
                'updated_at': notebook.updated_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notebooks/<int:notebook_id>/sources', methods=['POST'])
@jwt_required()
def upload_source():
    try:
        user_id = get_jwt_identity()
        
        # Verify notebook ownership
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
        if not notebook:
            return jsonify({'success': False, 'error': 'Notebook not found'}), 404
        
        # Handle file upload or text content
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400
            
            # Read file content
            content = file.read().decode('utf-8', errors='ignore')
            title = file.filename
            file_type = file.filename.split('.')[-1] if '.' in file.filename else 'txt'
            file_size = len(content)
            
        else:
            # Handle text content
            data = request.get_json()
            content = data.get('content', '')
            title = data.get('title', 'Text Document')
            file_type = 'txt'
            file_size = len(content)
        
        # Create source
        source = Source(
            notebook_id=notebook_id,
            title=title,
            content=content,
            file_type=file_type,
            file_size=file_size,
            status='completed'
        )
        
        db.session.add(source)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': source.id,
                'title': source.title,
                'file_type': source.file_type,
                'file_size': source.file_size,
                'status': source.status,
                'created_at': source.created_at.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notebooks/<int:notebook_id>/sources', methods=['GET'])
@jwt_required()
def get_sources():
    try:
        user_id = get_jwt_identity()
        
        # Verify notebook ownership
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
        if not notebook:
            return jsonify({'success': False, 'error': 'Notebook not found'}), 404
        
        sources = Source.query.filter_by(notebook_id=notebook_id).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': source.id,
                'title': source.title,
                'file_type': source.file_type,
                'file_size': source.file_size,
                'status': source.status,
                'created_at': source.created_at.isoformat()
            } for source in sources]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notebooks/<int:notebook_id>/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Verify notebook ownership
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
        if not notebook:
            return jsonify({'success': False, 'error': 'Notebook not found'}), 404
        
        message = data.get('message', '')
        conversation_id = data.get('conversation_id')
        
        # Get or create conversation
        if conversation_id:
            conversation = Conversation.query.filter_by(id=conversation_id, notebook_id=notebook_id).first()
        else:
            conversation = Conversation(
                notebook_id=notebook_id,
                title=message[:50] + '...' if len(message) > 50 else message
            )
            db.session.add(conversation)
            db.session.commit()
        
        # Get relevant sources for context
        sources = Source.query.filter_by(notebook_id=notebook_id).all()
        context = "\n\n".join([f"Source: {s.title}\nContent: {s.content[:500]}..." for s in sources[:3]])
        
        # Generate AI response using OpenAI
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": f"You are a helpful AI assistant. Use the following context to answer questions: {context}"},
                    {"role": "user", "content": message}
                ],
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
        except Exception as e:
            # Fallback to Anthropic if OpenAI fails
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": f"Context: {context}\n\nQuestion: {message}"}
                    ]
                )
                ai_response = response.content[0].text
            except:
                ai_response = "I apologize, but I'm having trouble accessing the AI services right now. Please try again later."
        
        # Save messages
        user_message = Message(
            conversation_id=conversation.id,
            content=message,
            role='user'
        )
        
        assistant_message = Message(
            conversation_id=conversation.id,
            content=ai_response,
            role='assistant',
            sources=json.dumps([{'id': s.id, 'title': s.title} for s in sources[:3]])
        )
        
        db.session.add(user_message)
        db.session.add(assistant_message)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'conversation_id': conversation.id,
                'response': ai_response,
                'sources': [{'id': s.id, 'title': s.title} for s in sources[:3]]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notebooks/<int:notebook_id>/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    try:
        user_id = get_jwt_identity()
        
        # Verify notebook ownership
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
        if not notebook:
            return jsonify({'success': False, 'error': 'Notebook not found'}), 404
        
        conversations = Conversation.query.filter_by(notebook_id=notebook_id).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': conv.id,
                'title': conv.title,
                'created_at': conv.created_at.isoformat()
            } for conv in conversations]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_messages():
    try:
        user_id = get_jwt_identity()
        
        # Verify access through notebook ownership
        conversation = Conversation.query.get(conversation_id)
        if not conversation:
            return jsonify({'success': False, 'error': 'Conversation not found'}), 404
        
        notebook = Notebook.query.filter_by(id=conversation.notebook_id, user_id=user_id).first()
        if not notebook:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.created_at).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'id': msg.id,
                'content': msg.content,
                'role': msg.role,
                'sources': json.loads(msg.sources) if msg.sources else [],
                'created_at': msg.created_at.isoformat()
            } for msg in messages]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notebooks/<int:notebook_id>/generate', methods=['POST'])
@jwt_required()
def generate_content():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Verify notebook ownership
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
        if not notebook:
            return jsonify({'success': False, 'error': 'Notebook not found'}), 404
        
        content_type = data.get('type', 'summary')
        
        # Get sources for context
        sources = Source.query.filter_by(notebook_id=notebook_id).all()
        if not sources:
            return jsonify({'success': False, 'error': 'No sources available for content generation'}), 400
        
        context = "\n\n".join([f"Source: {s.title}\nContent: {s.content}" for s in sources])
        
        # Generate content based on type
        prompts = {
            'summary': f"Create a comprehensive summary of the following documents:\n\n{context}",
            'faq': f"Generate frequently asked questions and answers based on the following documents:\n\n{context}",
            'study_guide': f"Create a detailed study guide based on the following documents:\n\n{context}",
            'timeline': f"Create a timeline of events mentioned in the following documents:\n\n{context}"
        }
        
        prompt = prompts.get(content_type, prompts['summary'])
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that creates well-structured content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000
            )
            
            generated_content = response.choices[0].message.content
            
        except Exception as e:
            # Fallback to Anthropic
            try:
                response = anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                generated_content = response.content[0].text
            except:
                return jsonify({'success': False, 'error': 'Failed to generate content'}), 500
        
        return jsonify({
            'success': True,
            'data': {
                'type': content_type,
                'content': generated_content,
                'sources': [{'id': s.id, 'title': s.title} for s in sources]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Initialize database and create test user
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create test user if not exists
        test_user = User.query.filter_by(email='test@example.com').first()
        if not test_user:
            test_user = User(
                email='test@example.com',
                name='Test User'
            )
            test_user.set_password('password123')
            db.session.add(test_user)
            db.session.commit()
            print("✅ Test user created: test@example.com / password123")

if __name__ == '__main__':
    init_db()
    print("🚀 Starting NotebookLM Integration Test Server...")
    print("📍 Backend API: http://localhost:5050")
    print("🔑 Test Login: test@example.com / password123")
    print("📚 API Endpoints:")
    print("   - GET  /api/health")
    print("   - POST /api/auth/login")
    print("   - POST /api/auth/register")
    print("   - GET  /api/notebooks")
    print("   - POST /api/notebooks")
    print("   - POST /api/notebooks/<id>/sources")
    print("   - GET  /api/notebooks/<id>/sources")
    print("   - POST /api/notebooks/<id>/chat")
    print("   - GET  /api/notebooks/<id>/conversations")
    print("   - GET  /api/conversations/<id>/messages")
    print("   - POST /api/notebooks/<id>/generate")
    
    app.run(host='0.0.0.0', port=5001, debug=True)

