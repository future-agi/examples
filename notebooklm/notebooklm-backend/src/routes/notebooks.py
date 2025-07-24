from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime

from src.models.user import db, User
from src.models.notebook import Notebook, Source
from src.services.document_processor import DocumentProcessor
from src.services.vector_store import VectorStore

from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType
from traceai_openai import OpenAIInstrumentor
from opentelemetry import trace
from fi.evals import Evaluator
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import (
    ProjectType, FiSpanKindValues, SpanAttributes
)
from opentelemetry import trace

tracer = FITracer(trace.get_tracer(__name__))

notebooks_bp = Blueprint('notebooks', __name__)

# Initialize services
document_processor = DocumentProcessor()
vector_store = VectorStore()

def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

def allowed_file(filename):
    """Check if file type is allowed"""
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'md', 'mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac', 'mp4'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@notebooks_bp.route('', methods=['GET'])
@jwt_required()
def list_notebooks():
    """List all notebooks for the authenticated user"""
    with tracer.start_as_current_span("list_notebooks") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", "List Notebooks")
        
        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"
                            }
                    })
                )
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            limit = min(request.args.get('limit', 20, type=int), 100)
            search = request.args.get('search', '').strip()
            sort = request.args.get('sort', 'updated_at')
            order = request.args.get('order', 'desc')
            
            # Build query
            query = Notebook.query.filter_by(user_id=user.id)
            
            # Apply search filter
            if search:
                query = query.filter(Notebook.title.contains(search))
            
            # Apply sorting
            if hasattr(Notebook, sort):
                sort_column = getattr(Notebook, sort)
                if order.lower() == 'desc':
                    query = query.order_by(sort_column.desc())
                else:
                    query = query.order_by(sort_column.asc())
            
            # Paginate
            offset = (page - 1) * limit
            notebooks = query.offset(offset).limit(limit).all()
            total_count = query.count()
            
            # Format response
            notebooks_data = []
            for notebook in notebooks:
                notebook.update_statistics()
                notebooks_data.append(notebook.to_dict())
            
            span.set_attribute("output.value", json.dumps({
                "notebooks": notebooks_data
            }))
            
            return jsonify({
                'success': True,
                'data': {
                    'notebooks': notebooks_data,
                    'pagination': {
                        'current_page': page,
                        'total_pages': (total_count + limit - 1) // limit,
                        'total_items': total_count,
                        'items_per_page': limit
                    }
                }
            })
            
        except Exception as e:
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to list notebooks",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to list notebooks',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('', methods=['POST'])
@jwt_required()
def create_notebook():
    """Create a new notebook"""
    with tracer.start_as_current_span("create_notebook") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", "Create Notebook")
        
        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            # Check usage limits
            can_create, message = user.check_usage_limits('create_notebook')
            if not can_create:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "LIMIT_EXCEEDED", "message": message}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'LIMIT_EXCEEDED', 'message': message}
                }), 403
            
            data = request.get_json()
            
            # Validate required fields
            if not data.get('title'):
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "VALIDATION_ERROR", "message": "Title is required"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'VALIDATION_ERROR', 'message': 'Title is required'}
                }), 400
            
            # Create notebook
            notebook = Notebook(
                user_id=user.id,
                title=data['title'].strip(),
                description=data.get('description', '').strip(),
            )
            
            # Set tags if provided
            if data.get('tags'):
                notebook.set_tags(data['tags'])
            
            db.session.add(notebook)
            db.session.commit()
            
            # Update user usage stats
            user.update_usage_stats()
            db.session.commit()
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "data": notebook.to_dict(),
                "message": "Notebook created successfully"
            }))
            return jsonify({
                'success': True,
                'data': notebook.to_dict(),
                'message': 'Notebook created successfully'
            }), 201
            
        except Exception as e:
            db.session.rollback()
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to create notebook",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to create notebook',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('/<notebook_id>', methods=['GET'])
@jwt_required()
def get_notebook(notebook_id):
    """Get detailed information about a specific notebook"""
    with tracer.start_as_current_span("get_notebook") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
        
        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
            if not notebook:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NOTEBOOK_NOT_FOUND", "message": "Notebook not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
                }), 404
            
            # Update statistics
            notebook.update_statistics()
            db.session.commit()
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "data": notebook.to_dict(include_sources=True, include_content=True)
            }))
            return jsonify({
                'success': True,
                'data': notebook.to_dict(include_sources=True, include_content=True)
            })
            
        except Exception as e:
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to get notebook",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get notebook',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('/<notebook_id>', methods=['PUT'])
@jwt_required()
def update_notebook(notebook_id):
    """Update notebook information"""
    with tracer.start_as_current_span("update_notebook") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
        
        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
            if not notebook:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NOTEBOOK_NOT_FOUND", "message": "Notebook not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
                }), 404
            
            data = request.get_json()
            
            # Update allowed fields
            if 'title' in data:
                notebook.title = data['title'].strip()
            if 'description' in data:
                notebook.description = data['description'].strip()
            if 'tags' in data:
                notebook.set_tags(data['tags'])
            
            notebook.updated_at = datetime.utcnow()
            db.session.commit()
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "data": notebook.to_dict(),
                "message": "Notebook updated successfully"
            }))
            return jsonify({
                'success': True,
                'data': notebook.to_dict(),
                'message': 'Notebook updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to update notebook",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to update notebook',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('/<notebook_id>', methods=['DELETE'])
@jwt_required()
def delete_notebook(notebook_id):
    """Delete a notebook and all associated content"""
    with tracer.start_as_current_span("delete_notebook") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
        
        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
            if not notebook:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NOTEBOOK_NOT_FOUND", "message": "Notebook not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
                }), 404
            
            # Delete vector store collection
            vector_store.delete_notebook_collection(notebook_id)
            
            # Delete notebook (cascade will handle related records)
            db.session.delete(notebook)
            db.session.commit()
            
            # Update user usage stats
            user.update_usage_stats()
            db.session.commit()
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "message": "Notebook deleted successfully"
            }))
            return jsonify({
                'success': True,
                'message': 'Notebook deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to delete notebook",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete notebook',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('/<notebook_id>/sources', methods=['GET'])
@jwt_required()
def get_sources(notebook_id):
    """Get all sources for a notebook"""
    with tracer.start_as_current_span("get_sources") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
        
        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            # Check if notebook exists and belongs to user
            notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
            if not notebook:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NOTEBOOK_NOT_FOUND", "message": "Notebook not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
                }), 404
            
            # Get all sources for this notebook
            sources = Source.query.filter_by(notebook_id=notebook_id).all()
            sources_data = [source.to_dict() for source in sources]
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "data": {
                    "sources": sources_data,
                    "total_count": len(sources_data)
                }
            }))
            return jsonify({
                'success': True,
                'data': {
                    'sources': sources_data,
                    'total_count': len(sources_data)
                }
            })
            
        except Exception as e:
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to get sources",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to get sources',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('/<notebook_id>/sources', methods=['POST'])
@jwt_required()
def upload_source(notebook_id):
    """Upload a new document source to a notebook"""
    with tracer.start_as_current_span("upload_source") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))
        
        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
            if not notebook:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NOTEBOOK_NOT_FOUND", "message": "Notebook not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
                }), 404
            
            # Check usage limits
            can_add, message = user.check_usage_limits('add_source', notebook=notebook)
            if not can_add:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "LIMIT_EXCEEDED", "message": message}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'LIMIT_EXCEEDED', 'message': message}
                }), 403
            
            # Handle file upload
            if 'file' not in request.files:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NO_FILE", "message": "No file provided"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NO_FILE', 'message': 'No file provided'}
                }), 400
            
            file = request.files['file']
            if file.filename == '':
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NO_FILE", "message": "No file provided"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NO_FILE', 'message': 'No file selected'}
                }), 400
            
            if not allowed_file(file.filename):
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "INVALID_FILE_TYPE", "message": "File type not supported"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'INVALID_FILE_TYPE', 'message': 'File type not supported'}
                }), 400
            
            # Get additional form data
            title = request.form.get('title', file.filename)
            description = request.form.get('description', '')
            
            # Save file
            filename = secure_filename(file.filename)
            file_id = str(uuid.uuid4())
            file_extension = filename.rsplit('.', 1)[1].lower()
            saved_filename = f"{file_id}.{file_extension}"
            
            upload_dir = os.path.join(current_app.root_path, 'uploads', notebook_id)
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, saved_filename)
            
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            # Check storage limits
            can_store, message = user.check_usage_limits('storage', file_size=file_size)
            if not can_store:
                os.remove(file_path)  # Clean up
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "STORAGE_LIMIT_EXCEEDED", "message": message}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'STORAGE_LIMIT_EXCEEDED', 'message': message}
                }), 403
            
            # Create source record
            source = Source(
                notebook_id=notebook_id,
                title=title,
                description=description,
                type=document_processor.detect_document_type(file_path),
                original_filename=filename,
                file_path=file_path,
                size=file_size,
                status='processing'
            )
            
            db.session.add(source)
            db.session.commit()
            
            # Process document asynchronously (simplified for demo)
            try:
                # Process document
                result = document_processor.process_document(file_path=file_path)
                
                if result.get('text'):
                    # Update source with processing results
                    source.set_metadata(result.get('metadata', {}))
                    source.set_processing_stats(result.get('processing_stats', {}))
                    source.status = 'processed'
                    source.processed_at = datetime.utcnow()
                    
                    # Add to vector store
                    if result.get('chunks'):
                        vector_store.add_document_chunks(notebook_id, source.id, result['chunks'])
                    
                    db.session.commit()
                else:
                    source.status = 'error'
                    source.error_message = 'Failed to extract text from document'
                    db.session.commit()
                    
            except Exception as e:
                source.status = 'error'
                source.error_message = str(e)
                db.session.commit()
            
            # Update notebook and user statistics
            notebook.update_statistics()
            user.update_usage_stats()
            db.session.commit()
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "data": source.to_dict(),
                "message": "Source uploaded and processed successfully"
            }))
            return jsonify({
                'success': True,
                'data': source.to_dict(),
                'message': 'Source uploaded and processed successfully'
            }), 201
            
        except Exception as e:
            db.session.rollback()
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to upload source",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to upload source',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('/<notebook_id>/sources/url', methods=['POST'])
@jwt_required()
def add_url_source(notebook_id):
    """Add a document source from URL"""
    with tracer.start_as_current_span("add_url_source") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id}))

        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
            if not notebook:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NOTEBOOK_NOT_FOUND", "message": "Notebook not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
                }), 404
            
            data = request.get_json()
            url = data.get('url', '').strip()
            
            if not url:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "VALIDATION_ERROR", "message": "URL is required"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'VALIDATION_ERROR', 'message': 'URL is required'}
                }), 400
            
            # Check usage limits
            can_add, message = user.check_usage_limits('add_source', notebook=notebook)
            if not can_add:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "LIMIT_EXCEEDED", "message": message}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'LIMIT_EXCEEDED', 'message': message}
                }), 403
            
            # Create source record
            source = Source(
                notebook_id=notebook_id,
                title=data.get('title', url),
                description=data.get('description', ''),
                type=document_processor.detect_document_type(url=url),
                url=url,
                status='processing'
            )
            
            db.session.add(source)
            db.session.commit()
            
            # Process URL content
            try:
                result = document_processor.process_document(url=url)
                
                if result.get('text'):
                    # Update source with processing results
                    source.set_metadata(result.get('metadata', {}))
                    source.set_processing_stats(result.get('processing_stats', {}))
                    source.status = 'processed'
                    source.processed_at = datetime.utcnow()
                    source.size = len(result['text'].encode('utf-8'))
                    
                    # Add to vector store
                    if result.get('chunks'):
                        vector_store.add_document_chunks(notebook_id, source.id, result['chunks'])
                    
                    db.session.commit()
                else:
                    source.status = 'error'
                    source.error_message = 'Failed to extract content from URL'
                    db.session.commit()
                    
            except Exception as e:
                source.status = 'error'
                source.error_message = str(e)
                db.session.commit()
            
            # Update statistics
            notebook.update_statistics()
            user.update_usage_stats()
            db.session.commit()
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "data": source.to_dict(),
                "message": "URL source added and processed successfully"
            }))
            return jsonify({
                'success': True,
                'data': source.to_dict(),
                'message': 'URL source added and processed successfully'
            }), 201
            
        except Exception as e:
            db.session.rollback()
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to add URL source",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to add URL source',
                    'details': str(e)
                }
            }), 500

@notebooks_bp.route('/<notebook_id>/sources/<source_id>', methods=['DELETE'])
@jwt_required()
def delete_source(notebook_id, source_id):
    """Delete a source from a notebook"""
    with tracer.start_as_current_span("delete_source") as span:
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
        span.set_attribute("input.value", json.dumps({"notebook_id": notebook_id, "source_id": source_id}))

        try:
            user = get_current_user()
            if not user:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "USER_NOT_FOUND", "message": "User not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
                }), 404
            
            notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
            if not notebook:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "NOTEBOOK_NOT_FOUND", "message": "Notebook not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
                }), 404
            
            source = Source.query.filter_by(id=source_id, notebook_id=notebook_id).first()
            if not source:
                span.set_attribute("output.value", json.dumps({
                    "success": False, 
                    "error": {"code": "SOURCE_NOT_FOUND", "message": "Source not found"}
                }))
                return jsonify({
                    'success': False,
                    'error': {'code': 'SOURCE_NOT_FOUND', 'message': 'Source not found'}
                }), 404
            
            # Delete from vector store
            vector_store.delete_source_chunks(notebook_id, source_id)
            
            # Delete file if it exists
            if source.file_path and os.path.exists(source.file_path):
                os.remove(source.file_path)
            
            # Delete source record
            db.session.delete(source)
            db.session.commit()
            
            # Update statistics
            notebook.update_statistics()
            user.update_usage_stats()
            db.session.commit()
            
            span.set_attribute("output.value", json.dumps({
                "success": True,
                "message": "Source deleted successfully"
            }))
            return jsonify({
                'success': True,
                'message': 'Source deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            span.set_attribute("output.value", json.dumps({
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to delete source",
                    "details": str(e)
                }
            }))
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to delete source',
                    'details': str(e)
                }
            }), 500

