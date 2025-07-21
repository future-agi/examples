from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re

from src.models.user import db, User

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Za-z]', password):
        return False, "Password must contain at least one letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': f'Missing required field: {field}'
                    }
                }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        name = data['name'].strip()
        
        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Invalid email format'
                }
            }), 400
        
        # Validate password strength
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': message
                }
            }), 400
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'USER_EXISTS',
                    'message': 'User with this email already exists'
                }
            }), 409
        
        # Create new user
        password_hash = generate_password_hash(password)
        new_user = User(
            email=email,
            name=name,
            password_hash=password_hash
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(
            identity=new_user.id,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=new_user.id,
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 3600,
                'user': new_user.to_dict(include_usage=False)
            },
            'message': 'User registered successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Registration failed',
                'details': str(e)
            }
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Email and password are required'
                }
            }), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Find user
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_CREDENTIALS',
                    'message': 'Invalid email or password'
                }
            }), 401
        
        # Check user status
        if user.status != 'active':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ACCOUNT_SUSPENDED',
                    'message': 'Account is suspended or inactive'
                }
            }), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        user.update_usage_stats()
        db.session.commit()
        
        # Create tokens
        access_token = create_access_token(
            identity=user.id,
            expires_delta=timedelta(hours=1)
        )
        refresh_token = create_refresh_token(
            identity=user.id,
            expires_delta=timedelta(days=30)
        )
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'expires_in': 3600,
                'user': user.to_dict()
            },
            'message': 'Login successful'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Login failed',
                'details': str(e)
            }
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        
        # Verify user still exists and is active
        user = User.query.get(current_user_id)
        if not user or user.status != 'active':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INVALID_USER',
                    'message': 'User not found or inactive'
                }
            }), 401
        
        # Create new access token
        access_token = create_access_token(
            identity=current_user_id,
            expires_delta=timedelta(hours=1)
        )
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token,
                'expires_in': 3600
            },
            'message': 'Token refreshed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Token refresh failed',
                'details': str(e)
            }
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user (invalidate tokens)"""
    try:
        # In a production system, you would add the token to a blacklist
        # For now, we'll just return success
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Logout failed',
                'details': str(e)
            }
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Update usage stats before returning
        user.update_usage_stats()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get profile',
                'details': str(e)
            }
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update user profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'name' in data:
            user.name = data['name'].strip()
        
        if 'preferences' in data:
            current_prefs = user.get_preferences()
            current_prefs.update(data['preferences'])
            user.set_preferences(current_prefs)
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'Profile updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to update profile',
                'details': str(e)
            }
        }), 500

@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Verify JWT token and return user info"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'USER_NOT_FOUND',
                    'message': 'User not found'
                }
            }), 404
        
        # Check user status
        if user.status != 'active':
            return jsonify({
                'success': False,
                'error': {
                    'code': 'ACCOUNT_SUSPENDED',
                    'message': 'Account is suspended or inactive'
                }
            }), 403
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict(include_usage=False)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Token verification failed',
                'details': str(e)
            }
        }), 500

