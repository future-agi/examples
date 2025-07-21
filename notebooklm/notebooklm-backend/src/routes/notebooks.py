from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

from src.models.user import db, User
from src.models.notebook import Notebook, Source
from src.services.document_processor import DocumentProcessor
from src.services.vector_store import VectorStore

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
    try:
        user = get_current_user()
        if not user:
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        # Check usage limits
        can_create, message = user.check_usage_limits('create_notebook')
        if not can_create:
            return jsonify({
                'success': False,
                'error': {'code': 'LIMIT_EXCEEDED', 'message': message}
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title'):
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
        
        return jsonify({
            'success': True,
            'data': notebook.to_dict(),
            'message': 'Notebook created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
        if not notebook:
            return jsonify({
                'success': False,
                'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
            }), 404
        
        # Update statistics
        notebook.update_statistics()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': notebook.to_dict(include_sources=True, include_content=True)
        })
        
    except Exception as e:
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
        if not notebook:
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
        
        return jsonify({
            'success': True,
            'data': notebook.to_dict(),
            'message': 'Notebook updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
        if not notebook:
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
        
        return jsonify({
            'success': True,
            'message': 'Notebook deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        # Check if notebook exists and belongs to user
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
        if not notebook:
            return jsonify({
                'success': False,
                'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
            }), 404
        
        # Get all sources for this notebook
        sources = Source.query.filter_by(notebook_id=notebook_id).all()
        sources_data = [source.to_dict() for source in sources]
        
        return jsonify({
            'success': True,
            'data': {
                'sources': sources_data,
                'total_count': len(sources_data)
            }
        })
        
    except Exception as e:
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
        if not notebook:
            return jsonify({
                'success': False,
                'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
            }), 404
        
        # Check usage limits
        can_add, message = user.check_usage_limits('add_source', notebook=notebook)
        if not can_add:
            return jsonify({
                'success': False,
                'error': {'code': 'LIMIT_EXCEEDED', 'message': message}
            }), 403
        
        # Handle file upload
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': {'code': 'NO_FILE', 'message': 'No file provided'}
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': {'code': 'NO_FILE', 'message': 'No file selected'}
            }), 400
        
        if not allowed_file(file.filename):
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
        
        return jsonify({
            'success': True,
            'data': source.to_dict(),
            'message': 'Source uploaded and processed successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
        if not notebook:
            return jsonify({
                'success': False,
                'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
            }), 404
        
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'URL is required'}
            }), 400
        
        # Check usage limits
        can_add, message = user.check_usage_limits('add_source', notebook=notebook)
        if not can_add:
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
        
        return jsonify({
            'success': True,
            'data': source.to_dict(),
            'message': 'URL source added and processed successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
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
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'success': False,
                'error': {'code': 'USER_NOT_FOUND', 'message': 'User not found'}
            }), 404
        
        notebook = Notebook.query.filter_by(id=notebook_id, user_id=user.id).first()
        if not notebook:
            return jsonify({
                'success': False,
                'error': {'code': 'NOTEBOOK_NOT_FOUND', 'message': 'Notebook not found'}
            }), 404
        
        source = Source.query.filter_by(id=source_id, notebook_id=notebook_id).first()
        if not source:
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
        
        return jsonify({
            'success': True,
            'message': 'Source deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to delete source',
                'details': str(e)
            }
        }), 500

