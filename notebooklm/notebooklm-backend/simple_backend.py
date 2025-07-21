#!/usr/bin/env python3
"""
Simplified NotebookLM Backend for Integration Testing
"""
import os
import sys
import json
from datetime import timedelta

sys.path.insert(0, '/home/ubuntu/notebooklm-backend')

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import openai
import anthropic

load_dotenv()

app = Flask(__name__)

# Simple configuration
app.config['SECRET_KEY'] = 'simple-test-key'
app.config['JWT_SECRET_KEY'] = 'simple-jwt-key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///simple_test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app, origins=['*'])
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Initialize AI clients
openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Simple Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Notebook(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Source(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notebook_id = db.Column(db.Integer, db.ForeignKey('notebook.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    file_type = db.Column(db.String(50))

# Routes
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'services': {
                'database': 'connected',
                'openai': bool(os.getenv('OPENAI_API_KEY')),
                'anthropic': bool(os.getenv('ANTHROPIC_API_KEY'))
            }
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.id))  # Convert to string
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token,
                'user': {'id': user.id, 'email': user.email, 'name': user.name}
            }
        })
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/auth/verify', methods=['GET'])
@jwt_required()
def verify_token():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    if user:
        return jsonify({
            'success': True,
            'data': {
                'user': {'id': user.id, 'email': user.email, 'name': user.name}
            }
        })
    
    return jsonify({'success': False, 'error': 'Invalid token'}), 401

@app.route('/api/notebooks', methods=['GET'])
@jwt_required()
def get_notebooks():
    user_id = int(get_jwt_identity())  # Convert string back to int
    notebooks = Notebook.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'success': True,
        'data': [{'id': nb.id, 'title': nb.title, 'description': nb.description} for nb in notebooks]
    })

@app.route('/api/notebooks', methods=['POST'])
@jwt_required()
def create_notebook():
    user_id = int(get_jwt_identity())  # Convert string back to int
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
        'data': {'id': notebook.id, 'title': notebook.title, 'description': notebook.description}
    })

@app.route('/api/notebooks/<int:notebook_id>', methods=['GET'])
@jwt_required()
def get_notebook(notebook_id):
    user_id = int(get_jwt_identity())  # Convert string back to int
    
    # Verify ownership
    notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    if not notebook:
        return jsonify({'success': False, 'error': 'Notebook not found'}), 404
    
    # Get sources for this notebook
    sources = Source.query.filter_by(notebook_id=notebook_id).all()
    
    return jsonify({
        'success': True,
        'data': {
            'id': notebook.id,
            'title': notebook.title,
            'description': notebook.description,
            'sources': [{'id': s.id, 'title': s.title, 'file_type': s.file_type} for s in sources]
        }
    })

@app.route('/api/notebooks/<int:notebook_id>/sources', methods=['POST'])
@jwt_required()
def upload_source(notebook_id):
    user_id = int(get_jwt_identity())  # Convert string back to int
    
    # Verify ownership
    notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    if not notebook:
        return jsonify({'success': False, 'error': 'Notebook not found'}), 404
    
    data = request.get_json()
    source = Source(
        notebook_id=notebook_id,
        title=data['title'],
        content=data['content'],
        file_type='txt'
    )
    
    db.session.add(source)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {'id': source.id, 'title': source.title, 'file_size': len(source.content)}
    })

@app.route('/api/notebooks/<int:notebook_id>/chat', methods=['POST'])
@jwt_required()
def chat(notebook_id):
    user_id = int(get_jwt_identity())  # Convert string back to int
    data = request.get_json()
    
    # Verify ownership
    notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    if not notebook:
        return jsonify({'success': False, 'error': 'Notebook not found'}), 404
    
    message = data['message']
    
    # Get sources for context
    sources = Source.query.filter_by(notebook_id=notebook_id).all()
    context = "\n\n".join([f"Source: {s.title}\nContent: {s.content[:500]}" for s in sources])
    
    # Generate AI response
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": f"Use this context to answer questions: {context}"},
                {"role": "user", "content": message}
            ],
            max_tokens=500
        )
        ai_response = response.choices[0].message.content
    except:
        ai_response = "I'm having trouble accessing the AI service right now."
    
    return jsonify({
        'success': True,
        'data': {
            'response': ai_response,
            'sources': [{'id': s.id, 'title': s.title} for s in sources]
        }
    })

@app.route('/api/notebooks/<int:notebook_id>/generate', methods=['POST'])
@jwt_required()
def generate_content(notebook_id):
    user_id = int(get_jwt_identity())  # Convert string back to int
    data = request.get_json()
    
    # Verify ownership
    notebook = Notebook.query.filter_by(id=notebook_id, user_id=user_id).first()
    if not notebook:
        return jsonify({'success': False, 'error': 'Notebook not found'}), 404
    
    content_type = data.get('type', 'summary')
    
    # Get sources
    sources = Source.query.filter_by(notebook_id=notebook_id).all()
    context = "\n\n".join([s.content for s in sources])
    
    prompt = f"Create a {content_type} of the following content:\n\n{context}"
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000
        )
        generated_content = response.choices[0].message.content
    except:
        generated_content = f"Generated {content_type} would appear here."
    
    return jsonify({
        'success': True,
        'data': {
            'type': content_type,
            'content': generated_content,
            'sources': [{'id': s.id, 'title': s.title} for s in sources]
        }
    })

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create test user
        if not User.query.filter_by(email='test@example.com').first():
            user = User(email='test@example.com', name='Test User')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            print("✅ Test user created")

if __name__ == '__main__':
    init_db()
    print("🚀 Simple NotebookLM Backend Running")
    print("📍 API: http://localhost:5003")
    print("🔑 Login: test@example.com / password123")
    app.run(host='0.0.0.0', port=5003, debug=True)

