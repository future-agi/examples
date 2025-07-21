from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
import uuid

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(20), default='free')  # free, pro, enterprise
    status = db.Column(db.String(20), default='active')  # active, suspended, deleted
    preferences = db.Column(db.Text)  # JSON object stored as text
    usage_stats = db.Column(db.Text)  # JSON object stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    notebooks = db.relationship('Notebook', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.preferences:
            self.preferences = json.dumps({
                'default_language': 'en',
                'theme': 'light',
                'notifications_enabled': True,
                'default_response_style': 'balanced'
            })
        if not self.usage_stats:
            self.usage_stats = json.dumps({
                'notebooks_count': 0,
                'queries_this_month': 0,
                'storage_used': 0,
                'last_active': None
            })
    
    def get_preferences(self):
        return json.loads(self.preferences) if self.preferences else {}
    
    def set_preferences(self, prefs_dict):
        self.preferences = json.dumps(prefs_dict)
    
    def get_usage_stats(self):
        return json.loads(self.usage_stats) if self.usage_stats else {}
    
    def set_usage_stats(self, stats_dict):
        self.usage_stats = json.dumps(stats_dict)
    
    def update_usage_stats(self):
        """Update user usage statistics based on current data"""
        stats = self.get_usage_stats()
        stats['notebooks_count'] = len(self.notebooks)
        
        # Calculate total storage used
        total_storage = 0
        total_queries = 0
        for notebook in self.notebooks:
            for source in notebook.sources:
                total_storage += source.size or 0
            for conv in notebook.conversations:
                messages = conv.get_messages()
                total_queries += len([msg for msg in messages if msg.get('type') == 'user'])
        
        stats['storage_used'] = total_storage
        stats['queries_this_month'] = total_queries  # Simplified for now
        stats['last_active'] = datetime.utcnow().isoformat()
        self.set_usage_stats(stats)
    
    def get_plan_limits(self):
        """Get usage limits based on user plan"""
        limits = {
            'free': {
                'notebooks_limit': 100,
                'queries_limit': 1000,
                'storage_limit': 1024 * 1024 * 1024,  # 1GB
                'sources_per_notebook': 50,
                'podcasts_per_notebook': 3
            },
            'pro': {
                'notebooks_limit': 500,
                'queries_limit': 5000,
                'storage_limit': 10 * 1024 * 1024 * 1024,  # 10GB
                'sources_per_notebook': 200,
                'podcasts_per_notebook': 15
            },
            'enterprise': {
                'notebooks_limit': -1,  # Unlimited
                'queries_limit': -1,
                'storage_limit': -1,
                'sources_per_notebook': -1,
                'podcasts_per_notebook': -1
            }
        }
        return limits.get(self.plan, limits['free'])
    
    def check_usage_limits(self, action_type, **kwargs):
        """Check if user can perform an action based on their plan limits"""
        limits = self.get_plan_limits()
        stats = self.get_usage_stats()
        
        if action_type == 'create_notebook':
            if limits['notebooks_limit'] != -1 and stats['notebooks_count'] >= limits['notebooks_limit']:
                return False, f"Notebook limit reached ({limits['notebooks_limit']})"
        
        elif action_type == 'add_source':
            notebook = kwargs.get('notebook')
            if notebook and limits['sources_per_notebook'] != -1:
                if len(notebook.sources) >= limits['sources_per_notebook']:
                    return False, f"Sources per notebook limit reached ({limits['sources_per_notebook']})"
        
        elif action_type == 'create_podcast':
            notebook = kwargs.get('notebook')
            if notebook and limits['podcasts_per_notebook'] != -1:
                if len(notebook.podcasts) >= limits['podcasts_per_notebook']:
                    return False, f"Podcasts per notebook limit reached ({limits['podcasts_per_notebook']})"
        
        elif action_type == 'storage':
            file_size = kwargs.get('file_size', 0)
            if limits['storage_limit'] != -1:
                if stats['storage_used'] + file_size > limits['storage_limit']:
                    return False, f"Storage limit exceeded ({limits['storage_limit']} bytes)"
        
        return True, "OK"
    
    def to_dict(self, include_usage=True):
        result = {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'plan': self.plan,
            'status': self.status,
            'preferences': self.get_preferences(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_usage:
            stats = self.get_usage_stats()
            limits = self.get_plan_limits()
            result['usage'] = {
                'notebooks_count': stats.get('notebooks_count', 0),
                'notebooks_limit': limits['notebooks_limit'],
                'queries_this_month': stats.get('queries_this_month', 0),
                'queries_limit': limits['queries_limit'],
                'storage_used': f"{stats.get('storage_used', 0) / (1024*1024):.1f}MB",
                'storage_limit': f"{limits['storage_limit'] / (1024*1024):.0f}MB" if limits['storage_limit'] != -1 else "Unlimited"
            }
        
        return result
    
    def __repr__(self):
        return f'<User {self.email}>'

