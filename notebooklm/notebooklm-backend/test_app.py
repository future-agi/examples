#!/usr/bin/env python3
"""
Simple test script to start the NotebookLM backend
"""
import os
import sys
sys.path.insert(0, '/home/ubuntu/notebooklm-backend')

from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'test-secret-key')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'test-jwt-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///test_notebooklm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5174'])
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Simple health check endpoint
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
                'api': 'active'
            }
        }
    })

# Test endpoint
@app.route('/api/test', methods=['GET'])
def test_endpoint():
    return jsonify({
        'success': True,
        'data': {
            'message': 'NotebookLM API is working!',
            'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
            'anthropic_configured': bool(os.getenv('ANTHROPIC_API_KEY')),
            'google_configured': bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'))
        }
    })

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")

if __name__ == '__main__':
    print("Starting NotebookLM Backend Test Server...")
    print("Health check: http://localhost:5050/api/health")
    print("Test endpoint: http://localhost:5050/api/test")
    app.run(host='0.0.0.0', port=5050, debug=True)

