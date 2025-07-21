from src.models.user import db
from datetime import datetime
import json
import uuid

class Notebook(db.Model):
    __tablename__ = 'notebooks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    tags = db.Column(db.Text)  # JSON array stored as text
    is_shared = db.Column(db.Boolean, default=False)
    share_settings = db.Column(db.Text)  # JSON object stored as text
    settings = db.Column(db.Text)  # JSON object stored as text
    statistics = db.Column(db.Text)  # JSON object stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sources = db.relationship('Source', backref='notebook', lazy=True, cascade='all, delete-orphan')
    conversations = db.relationship('Conversation', backref='notebook', lazy=True, cascade='all, delete-orphan')
    generated_content = db.relationship('GeneratedContent', backref='notebook', lazy=True, cascade='all, delete-orphan')
    podcasts = db.relationship('Podcast', backref='notebook', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.tags:
            self.tags = json.dumps([])
        if not self.share_settings:
            self.share_settings = json.dumps({
                'is_public': False,
                'share_url': None,
                'allowed_users': [],
                'permissions': 'read'
            })
        if not self.settings:
            self.settings = json.dumps({
                'default_language': 'en',
                'ai_model_preference': 'gpt-3.5-turbo',
                'response_style': 'balanced'
            })
        if not self.statistics:
            self.statistics = json.dumps({
                'sources_count': 0,
                'total_size': 0,
                'queries_count': 0,
                'last_query': None
            })
    
    def get_tags(self):
        return json.loads(self.tags) if self.tags else []
    
    def set_tags(self, tags_list):
        self.tags = json.dumps(tags_list)
    
    def get_share_settings(self):
        return json.loads(self.share_settings) if self.share_settings else {}
    
    def set_share_settings(self, settings_dict):
        self.share_settings = json.dumps(settings_dict)
    
    def get_settings(self):
        return json.loads(self.settings) if self.settings else {}
    
    def set_settings(self, settings_dict):
        self.settings = json.dumps(settings_dict)
    
    def get_statistics(self):
        return json.loads(self.statistics) if self.statistics else {}
    
    def set_statistics(self, stats_dict):
        self.statistics = json.dumps(stats_dict)
    
    def update_statistics(self):
        """Update notebook statistics based on current data"""
        stats = self.get_statistics()
        stats['sources_count'] = len(self.sources)
        stats['total_size'] = sum(source.size or 0 for source in self.sources)
        
        # Count total queries from all conversations
        total_queries = 0
        last_query = None
        for conv in self.conversations:
            messages = conv.get_messages()
            user_messages = [msg for msg in messages if msg.get('type') == 'user']
            total_queries += len(user_messages)
            if user_messages:
                last_msg_time = max(msg.get('timestamp') for msg in user_messages)
                if not last_query or last_msg_time > last_query:
                    last_query = last_msg_time
        
        stats['queries_count'] = total_queries
        stats['last_query'] = last_query
        self.set_statistics(stats)
    
    def to_dict(self, include_sources=False, include_content=False):
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'tags': self.get_tags(),
            'is_shared': self.is_shared,
            'share_settings': self.get_share_settings(),
            'settings': self.get_settings(),
            'statistics': self.get_statistics(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sources:
            result['sources'] = [source.to_dict() for source in self.sources]
        else:
            result['sources_count'] = len(self.sources)
        
        if include_content:
            result['generated_content'] = [content.to_dict() for content in self.generated_content]
            result['podcasts'] = [podcast.to_dict() for podcast in self.podcasts]
        
        return result

class Source(db.Model):
    __tablename__ = 'sources'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = db.Column(db.String(36), db.ForeignKey('notebooks.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False)  # pdf, docx, txt, url, youtube, audio
    original_filename = db.Column(db.String(255))
    file_path = db.Column(db.String(500))
    url = db.Column(db.String(1000))
    size = db.Column(db.Integer)  # Size in bytes
    status = db.Column(db.String(50), default='uploading')  # uploading, processing, processed, error
    processing_progress = db.Column(db.Integer, default=0)  # 0-100
    error_message = db.Column(db.Text)
    doc_metadata = db.Column(db.Text)  # JSON object stored as text
    processing_stats = db.Column(db.Text)  # JSON object stored as text
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.doc_metadata:
            self.doc_metadata = json.dumps({})
        if not self.processing_stats:
            self.processing_stats = json.dumps({})
    
    def get_metadata(self):
        return json.loads(self.doc_metadata) if self.doc_metadata else {}
    
    def set_metadata(self, metadata_dict):
        self.doc_metadata = json.dumps(metadata_dict)
    
    def get_processing_stats(self):
        return json.loads(self.processing_stats) if self.processing_stats else {}
    
    def set_processing_stats(self, stats_dict):
        self.processing_stats = json.dumps(stats_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'type': self.type,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'url': self.url,
            'size': self.size,
            'status': self.status,
            'processing_progress': self.processing_progress,
            'error_message': self.error_message,
            'metadata': self.get_metadata(),
            'processing_stats': self.get_processing_stats(),
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None
        }

class Conversation(db.Model):
    __tablename__ = 'conversations'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = db.Column(db.String(36), db.ForeignKey('notebooks.id'), nullable=False)
    title = db.Column(db.String(255))
    messages = db.Column(db.Text)  # JSON array stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.messages:
            self.messages = json.dumps([])
    
    def get_messages(self):
        return json.loads(self.messages) if self.messages else []
    
    def set_messages(self, messages_list):
        self.messages = json.dumps(messages_list)
    
    def add_message(self, message_dict):
        messages = self.get_messages()
        message_dict['id'] = str(uuid.uuid4())
        message_dict['timestamp'] = datetime.utcnow().isoformat()
        messages.append(message_dict)
        self.set_messages(messages)
        self.updated_at = datetime.utcnow()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'messages': self.get_messages(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GeneratedContent(db.Model):
    __tablename__ = 'generated_content'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = db.Column(db.String(36), db.ForeignKey('notebooks.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # summary, faq, timeline, study_guide, briefing
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)  # Markdown format
    source_ids = db.Column(db.Text)  # JSON array of source IDs
    generation_params = db.Column(db.Text)  # JSON object stored as text
    citations = db.Column(db.Text)  # JSON array stored as text
    statistics = db.Column(db.Text)  # JSON object stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.source_ids:
            self.source_ids = json.dumps([])
        if not self.generation_params:
            self.generation_params = json.dumps({})
        if not self.citations:
            self.citations = json.dumps([])
        if not self.statistics:
            self.statistics = json.dumps({})
    
    def get_source_ids(self):
        return json.loads(self.source_ids) if self.source_ids else []
    
    def set_source_ids(self, ids_list):
        self.source_ids = json.dumps(ids_list)
    
    def get_generation_params(self):
        return json.loads(self.generation_params) if self.generation_params else {}
    
    def set_generation_params(self, params_dict):
        self.generation_params = json.dumps(params_dict)
    
    def get_citations(self):
        return json.loads(self.citations) if self.citations else []
    
    def set_citations(self, citations_list):
        self.citations = json.dumps(citations_list)
    
    def get_statistics(self):
        return json.loads(self.statistics) if self.statistics else {}
    
    def set_statistics(self, stats_dict):
        self.statistics = json.dumps(stats_dict)
    
    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'source_ids': self.get_source_ids(),
            'generation_params': self.get_generation_params(),
            'citations': self.get_citations(),
            'statistics': self.get_statistics(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Podcast(db.Model):
    __tablename__ = 'podcasts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = db.Column(db.String(36), db.ForeignKey('notebooks.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='generating')  # generating, completed, error
    progress = db.Column(db.Integer, default=0)  # 0-100
    source_ids = db.Column(db.Text)  # JSON array of source IDs
    generation_params = db.Column(db.Text)  # JSON object stored as text
    audio_file = db.Column(db.Text)  # JSON object stored as text
    transcript = db.Column(db.Text)
    chapters = db.Column(db.Text)  # JSON array stored as text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.source_ids:
            self.source_ids = json.dumps([])
        if not self.generation_params:
            self.generation_params = json.dumps({})
        if not self.audio_file:
            self.audio_file = json.dumps({})
        if not self.chapters:
            self.chapters = json.dumps([])
    
    def get_source_ids(self):
        return json.loads(self.source_ids) if self.source_ids else []
    
    def set_source_ids(self, ids_list):
        self.source_ids = json.dumps(ids_list)
    
    def get_generation_params(self):
        return json.loads(self.generation_params) if self.generation_params else {}
    
    def set_generation_params(self, params_dict):
        self.generation_params = json.dumps(params_dict)
    
    def get_audio_file(self):
        return json.loads(self.audio_file) if self.audio_file else {}
    
    def set_audio_file(self, file_dict):
        self.audio_file = json.dumps(file_dict)
    
    def get_chapters(self):
        return json.loads(self.chapters) if self.chapters else []
    
    def set_chapters(self, chapters_list):
        self.chapters = json.dumps(chapters_list)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'progress': self.progress,
            'source_ids': self.get_source_ids(),
            'generation_params': self.get_generation_params(),
            'audio_file': self.get_audio_file(),
            'transcript': self.transcript,
            'chapters': self.get_chapters(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }

