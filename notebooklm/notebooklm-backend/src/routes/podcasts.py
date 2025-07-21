from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from datetime import datetime
import threading

from src.models.user import db, User
from src.models.notebook import Notebook, Podcast, Source
from src.services.podcast_service import PodcastService
from src.services.vector_store import VectorStore

podcasts_bp = Blueprint('podcasts', __name__)

# Initialize services
podcast_service = PodcastService()
vector_store = VectorStore()

def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@podcasts_bp.route('/notebooks/<notebook_id>/podcasts', methods=['GET'])
@jwt_required()
def list_podcasts(notebook_id):
    """List all podcasts for a notebook"""
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
        
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        limit = min(request.args.get('limit', 20, type=int), 100)
        status = request.args.get('status')  # Optional filter by status
        
        # Build query
        query = Podcast.query.filter_by(notebook_id=notebook_id)
        
        if status:
            query = query.filter_by(status=status)
        
        # Paginate
        offset = (page - 1) * limit
        podcasts = query.order_by(Podcast.created_at.desc()) \
            .offset(offset).limit(limit).all()
        
        total_count = query.count()
        
        # Format response
        podcasts_data = [podcast.to_dict() for podcast in podcasts]
        
        return jsonify({
            'success': True,
            'data': {
                'podcasts': podcasts_data,
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
                'message': 'Failed to list podcasts',
                'details': str(e)
            }
        }), 500

@podcasts_bp.route('/notebooks/<notebook_id>/podcasts', methods=['POST'])
@jwt_required()
def create_podcast(notebook_id):
    """Create a new podcast from notebook content"""
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
        can_create, message = user.check_usage_limits('create_podcast', notebook=notebook)
        if not can_create:
            return jsonify({
                'success': False,
                'error': {'code': 'LIMIT_EXCEEDED', 'message': message}
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        title = data.get('title')
        if not title:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'Podcast title is required'}
            }), 400
        
        # Get generation parameters
        style = data.get('style', 'conversational')
        duration_target = data.get('duration_target', 'medium')
        source_ids = data.get('source_ids', [])
        custom_instructions = data.get('custom_instructions')
        description = data.get('description', '')
        
        # Validate style
        available_styles = podcast_service.get_available_styles()
        if style not in available_styles:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': f'Invalid style. Available styles: {", ".join(available_styles.keys())}'
                }
            }), 400
        
        # Get sources to use
        if source_ids:
            sources = Source.query.filter(
                Source.id.in_(source_ids),
                Source.notebook_id == notebook_id,
                Source.status == 'processed'
            ).all()
        else:
            # Use all processed sources
            sources = Source.query.filter_by(
                notebook_id=notebook_id,
                status='processed'
            ).limit(20).all()  # Limit for performance
        
        if not sources:
            return jsonify({
                'success': False,
                'error': {'code': 'NO_SOURCES', 'message': 'No processed sources available for podcast generation'}
            }), 400
        
        # Create podcast record
        podcast = Podcast(
            notebook_id=notebook_id,
            title=title,
            description=description,
            status='generating',
            progress=0
        )
        
        # Set source IDs
        podcast.set_source_ids([source.id for source in sources])
        
        # Set generation parameters
        generation_params = {
            'style': style,
            'duration_target': duration_target,
            'custom_instructions': custom_instructions,
            'sources_count': len(sources)
        }
        podcast.set_generation_params(generation_params)
        
        db.session.add(podcast)
        db.session.commit()
        
        # Start podcast generation in background
        thread = threading.Thread(
            target=generate_podcast_async,
            args=(podcast.id, notebook_id, sources, style, duration_target, custom_instructions, title)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'data': podcast.to_dict(),
            'message': 'Podcast generation started'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to create podcast',
                'details': str(e)
            }
        }), 500

def generate_podcast_async(podcast_id: str, notebook_id: str, sources: list, 
                          style: str, duration_target: str, custom_instructions: str, title: str):
    """Generate podcast asynchronously"""
    try:
        # Get podcast record
        podcast = Podcast.query.get(podcast_id)
        if not podcast:
            return
        
        # Update progress
        podcast.progress = 10
        podcast.status = 'generating'
        db.session.commit()
        
        # Get content chunks from vector store
        all_chunks = []
        for source in sources:
            source_chunks = vector_store.search_similar_chunks(
                notebook_id=notebook_id,
                query=f"content from {source.title}",
                n_results=15,  # More chunks for comprehensive podcast
                source_ids=[source.id]
            )
            all_chunks.extend(source_chunks)
        
        if not all_chunks:
            podcast.status = 'error'
            podcast.error_message = 'No content chunks available for podcast generation'
            db.session.commit()
            return
        
        # Update progress
        podcast.progress = 30
        db.session.commit()
        
        # Generate script
        script_result = podcast_service.generate_podcast_script(
            sources=all_chunks,
            style=style,
            title=title,
            duration_target=duration_target,
            custom_instructions=custom_instructions
        )
        
        if script_result.get('error'):
            podcast.status = 'error'
            podcast.error_message = f"Script generation failed: {script_result.get('error')}"
            db.session.commit()
            return
        
        # Update progress and save script
        podcast.progress = 60
        podcast.transcript = script_result.get('script', '')
        
        # Set chapters from segments
        segments = script_result.get('segments', [])
        chapters = []
        current_time = 0
        
        for i, segment in enumerate(segments):
            duration = segment.get('duration_estimate', 0)
            chapters.append({
                'title': f"{segment.get('speaker', 'Speaker').title()} - Part {i+1}",
                'start_time': current_time,
                'duration': duration,
                'speaker': segment.get('speaker', 'unknown')
            })
            current_time += duration
        
        podcast.set_chapters(chapters)
        db.session.commit()
        
        # Generate audio
        audio_result = podcast_service.generate_audio_from_script(script_result)
        
        if audio_result.get('error'):
            podcast.status = 'error'
            podcast.error_message = f"Audio generation failed: {audio_result.get('error')}"
            db.session.commit()
            return
        
        # Update podcast with audio information
        podcast.progress = 100
        podcast.status = 'completed'
        podcast.completed_at = datetime.utcnow()
        podcast.set_audio_file(audio_result.get('audio_file', {}))
        
        db.session.commit()
        
    except Exception as e:
        # Update podcast with error
        try:
            podcast = Podcast.query.get(podcast_id)
            if podcast:
                podcast.status = 'error'
                podcast.error_message = str(e)
                db.session.commit()
        except:
            pass

@podcasts_bp.route('/notebooks/<notebook_id>/podcasts/<podcast_id>', methods=['GET'])
@jwt_required()
def get_podcast(notebook_id, podcast_id):
    """Get detailed information about a specific podcast"""
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
        
        podcast = Podcast.query.filter_by(
            id=podcast_id,
            notebook_id=notebook_id
        ).first()
        
        if not podcast:
            return jsonify({
                'success': False,
                'error': {'code': 'PODCAST_NOT_FOUND', 'message': 'Podcast not found'}
            }), 404
        
        return jsonify({
            'success': True,
            'data': podcast.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get podcast',
                'details': str(e)
            }
        }), 500

@podcasts_bp.route('/notebooks/<notebook_id>/podcasts/<podcast_id>/audio', methods=['GET'])
@jwt_required()
def download_podcast_audio(notebook_id, podcast_id):
    """Download podcast audio file"""
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
        
        podcast = Podcast.query.filter_by(
            id=podcast_id,
            notebook_id=notebook_id
        ).first()
        
        if not podcast:
            return jsonify({
                'success': False,
                'error': {'code': 'PODCAST_NOT_FOUND', 'message': 'Podcast not found'}
            }), 404
        
        if podcast.status != 'completed':
            return jsonify({
                'success': False,
                'error': {'code': 'PODCAST_NOT_READY', 'message': 'Podcast is not ready for download'}
            }), 400
        
        audio_file_info = podcast.get_audio_file()
        audio_path = audio_file_info.get('path')
        
        if not audio_path or not os.path.exists(audio_path):
            return jsonify({
                'success': False,
                'error': {'code': 'AUDIO_FILE_NOT_FOUND', 'message': 'Audio file not found'}
            }), 404
        
        # Generate safe filename
        safe_title = "".join(c for c in podcast.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_title}.wav"
        
        return send_file(
            audio_path,
            as_attachment=True,
            download_name=filename,
            mimetype='audio/wav'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to download podcast audio',
                'details': str(e)
            }
        }), 500

@podcasts_bp.route('/notebooks/<notebook_id>/podcasts/<podcast_id>', methods=['DELETE'])
@jwt_required()
def delete_podcast(notebook_id, podcast_id):
    """Delete a podcast"""
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
        
        podcast = Podcast.query.filter_by(
            id=podcast_id,
            notebook_id=notebook_id
        ).first()
        
        if not podcast:
            return jsonify({
                'success': False,
                'error': {'code': 'PODCAST_NOT_FOUND', 'message': 'Podcast not found'}
            }), 404
        
        # Delete audio file if it exists
        audio_file_info = podcast.get_audio_file()
        audio_path = audio_file_info.get('path')
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except Exception as e:
                logging.warning(f"Failed to delete audio file: {e}")
        
        # Delete podcast record
        db.session.delete(podcast)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Podcast deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to delete podcast',
                'details': str(e)
            }
        }), 500

@podcasts_bp.route('/podcast-styles', methods=['GET'])
@jwt_required()
def get_podcast_styles():
    """Get available podcast styles"""
    try:
        styles = podcast_service.get_available_styles()
        
        return jsonify({
            'success': True,
            'data': {
                'styles': styles,
                'total_styles': len(styles)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get podcast styles',
                'details': str(e)
            }
        }), 500

@podcasts_bp.route('/podcast-service/health', methods=['GET'])
@jwt_required()
def podcast_service_health():
    """Get podcast service health status"""
    try:
        health_status = podcast_service.get_health_status()
        
        return jsonify({
            'success': True,
            'data': health_status
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get podcast service health',
                'details': str(e)
            }
        }), 500

