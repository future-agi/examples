"""
Authentication and Authorization System for the Multi-Agent AI Trading System
"""
import jwt
import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from flask import request, jsonify, current_app
import bcrypt

from config.settings import config
from src.utils.logging import get_component_logger

logger = get_component_logger("auth")


class UserRole:
    """User role constants"""
    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission:
    """Permission constants"""
    READ_MARKET_DATA = "read_market_data"
    READ_ANALYSIS = "read_analysis"
    CREATE_ANALYSIS = "create_analysis"
    MANAGE_KNOWLEDGE = "manage_knowledge"
    MANAGE_USERS = "manage_users"
    SYSTEM_ADMIN = "system_admin"


# Role-based permissions
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_MARKET_DATA,
        Permission.READ_ANALYSIS,
        Permission.CREATE_ANALYSIS,
        Permission.MANAGE_KNOWLEDGE,
        Permission.MANAGE_USERS,
        Permission.SYSTEM_ADMIN
    ],
    UserRole.TRADER: [
        Permission.READ_MARKET_DATA,
        Permission.READ_ANALYSIS,
        Permission.CREATE_ANALYSIS
    ],
    UserRole.ANALYST: [
        Permission.READ_MARKET_DATA,
        Permission.READ_ANALYSIS,
        Permission.CREATE_ANALYSIS,
        Permission.MANAGE_KNOWLEDGE
    ],
    UserRole.VIEWER: [
        Permission.READ_MARKET_DATA,
        Permission.READ_ANALYSIS
    ]
}


class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.secret_key = config.flask_secret_key
        self.token_expiry = 24 * 60 * 60  # 24 hours
        self.refresh_token_expiry = 7 * 24 * 60 * 60  # 7 days
        
        # In-memory user store (in production, use a database)
        self.users = {}
        self.refresh_tokens = {}
        
        # Create default admin user
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default users for the system"""
        try:
            # Default admin user
            admin_password = self._hash_password("admin123")
            self.users["admin"] = {
                "username": "admin",
                "password_hash": admin_password,
                "role": UserRole.ADMIN,
                "email": "admin@trading-system.com",
                "created_at": datetime.now(timezone.utc),
                "is_active": True,
                "api_key": self._generate_api_key()
            }
            
            # Default trader user
            trader_password = self._hash_password("trader123")
            self.users["trader"] = {
                "username": "trader",
                "password_hash": trader_password,
                "role": UserRole.TRADER,
                "email": "trader@trading-system.com",
                "created_at": datetime.now(timezone.utc),
                "is_active": True,
                "api_key": self._generate_api_key()
            }
            
            logger.info("Created default users: admin, trader")
            
        except Exception as e:
            logger.error(f"Error creating default users: {e}")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_api_key(self) -> str:
        """Generate API key"""
        return secrets.token_urlsafe(32)
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with username and password"""
        try:
            user = self.users.get(username)
            
            if not user:
                logger.warning(f"Authentication failed: user {username} not found")
                return None
            
            if not user.get("is_active", False):
                logger.warning(f"Authentication failed: user {username} is inactive")
                return None
            
            if not self._verify_password(password, user["password_hash"]):
                logger.warning(f"Authentication failed: invalid password for {username}")
                return None
            
            logger.info(f"User {username} authenticated successfully")
            return user
            
        except Exception as e:
            logger.error(f"Error authenticating user {username}: {e}")
            return None
    
    def authenticate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with API key"""
        try:
            for user in self.users.values():
                if user.get("api_key") == api_key and user.get("is_active", False):
                    logger.info(f"API key authentication successful for {user['username']}")
                    return user
            
            logger.warning("API key authentication failed: invalid key")
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating API key: {e}")
            return None
    
    def generate_token(self, user: Dict[str, Any]) -> Dict[str, str]:
        """Generate JWT access and refresh tokens"""
        try:
            now = datetime.now(timezone.utc)
            
            # Access token payload
            access_payload = {
                "username": user["username"],
                "role": user["role"],
                "permissions": ROLE_PERMISSIONS.get(user["role"], []),
                "iat": now,
                "exp": now + timedelta(seconds=self.token_expiry),
                "type": "access"
            }
            
            # Refresh token payload
            refresh_payload = {
                "username": user["username"],
                "iat": now,
                "exp": now + timedelta(seconds=self.refresh_token_expiry),
                "type": "refresh"
            }
            
            # Generate tokens
            access_token = jwt.encode(access_payload, self.secret_key, algorithm="HS256")
            refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm="HS256")
            
            # Store refresh token
            self.refresh_tokens[refresh_token] = {
                "username": user["username"],
                "created_at": now
            }
            
            logger.info(f"Generated tokens for user {user['username']}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "expires_in": self.token_expiry
            }
            
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            return {}
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            
            # Check token type
            if payload.get("type") != "access":
                return None
            
            # Check if user still exists and is active
            username = payload.get("username")
            user = self.users.get(username)
            
            if not user or not user.get("is_active", False):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token verification failed: token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Token verification failed: invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=["HS256"])
            
            if payload.get("type") != "refresh":
                return None
            
            # Check if refresh token is stored
            if refresh_token not in self.refresh_tokens:
                return None
            
            username = payload.get("username")
            user = self.users.get(username)
            
            if not user or not user.get("is_active", False):
                return None
            
            # Generate new access token
            return self.generate_token(user)
            
        except jwt.ExpiredSignatureError:
            # Remove expired refresh token
            self.refresh_tokens.pop(refresh_token, None)
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Error refreshing token: {e}")
            return None
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """Revoke refresh token"""
        try:
            if refresh_token in self.refresh_tokens:
                del self.refresh_tokens[refresh_token]
                logger.info("Refresh token revoked")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error revoking refresh token: {e}")
            return False
    
    def has_permission(self, user_role: str, permission: str) -> bool:
        """Check if user role has specific permission"""
        role_permissions = ROLE_PERMISSIONS.get(user_role, [])
        return permission in role_permissions
    
    def create_user(self, username: str, password: str, role: str, email: str) -> bool:
        """Create new user"""
        try:
            if username in self.users:
                logger.warning(f"User creation failed: {username} already exists")
                return False
            
            if role not in ROLE_PERMISSIONS:
                logger.warning(f"User creation failed: invalid role {role}")
                return False
            
            password_hash = self._hash_password(password)
            
            self.users[username] = {
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "email": email,
                "created_at": datetime.now(timezone.utc),
                "is_active": True,
                "api_key": self._generate_api_key()
            }
            
            logger.info(f"Created user: {username} with role {role}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating user {username}: {e}")
            return False
    
    def update_user(self, username: str, **kwargs) -> bool:
        """Update user information"""
        try:
            if username not in self.users:
                return False
            
            user = self.users[username]
            
            # Update allowed fields
            allowed_fields = ["role", "email", "is_active"]
            for field, value in kwargs.items():
                if field in allowed_fields:
                    user[field] = value
            
            # Update password if provided
            if "password" in kwargs:
                user["password_hash"] = self._hash_password(kwargs["password"])
            
            logger.info(f"Updated user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user {username}: {e}")
            return False
    
    def delete_user(self, username: str) -> bool:
        """Delete user"""
        try:
            if username in self.users:
                del self.users[username]
                logger.info(f"Deleted user: {username}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting user {username}: {e}")
            return False
    
    def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information (without sensitive data)"""
        user = self.users.get(username)
        if user:
            return {
                "username": user["username"],
                "role": user["role"],
                "email": user["email"],
                "created_at": user["created_at"].isoformat(),
                "is_active": user["is_active"],
                "permissions": ROLE_PERMISSIONS.get(user["role"], [])
            }
        return None
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (without sensitive data)"""
        return [self.get_user_info(username) for username in self.users.keys()]


# Global auth manager instance
auth_manager = AuthManager()


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key first
        api_key = request.headers.get('X-API-Key')
        if api_key:
            user = auth_manager.authenticate_api_key(api_key)
            if user:
                request.current_user = user
                return f(*args, **kwargs)
        
        # Check for JWT token
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Authentication required"}), 401
        
        token = auth_header.split(' ')[1]
        payload = auth_manager.verify_token(token)
        
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({"error": "Authentication required"}), 401
            
            user_role = request.current_user.get('role')
            if not auth_manager.has_permission(user_role, permission):
                return jsonify({"error": "Insufficient permissions"}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_role(role: str):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({"error": "Authentication required"}), 401
            
            user_role = request.current_user.get('role')
            if user_role != role:
                return jsonify({"error": "Insufficient role"}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

