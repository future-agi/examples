from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models.user import db, User
from src.models.notebook import Notebook, GeneratedContent, Source
from src.services.ai_service import AIService
from src.services.vector_store import VectorStore

content_bp = Blueprint('content', __name__)

# Initialize services
ai_service = AIService()
vector_store = VectorStore()

def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@content_bp.route('/notebooks/<notebook_id>/content', methods=['GET'])
@jwt_required()
def list_generated_content(notebook_id):
    """List all generated content for a notebook"""
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
        content_type = request.args.get('type')  # Optional filter by type
        
        # Build query
        query = GeneratedContent.query.filter_by(notebook_id=notebook_id)
        
        if content_type:
            query = query.filter_by(type=content_type)
        
        # Paginate
        offset = (page - 1) * limit
        content_items = query.order_by(GeneratedContent.created_at.desc()) \
            .offset(offset).limit(limit).all()
        
        total_count = query.count()
        
        # Format response
        content_data = [item.to_dict() for item in content_items]
        
        return jsonify({
            'success': True,
            'data': {
                'content': content_data,
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
                'message': 'Failed to list generated content',
                'details': str(e)
            }
        }), 500

@content_bp.route('/notebooks/<notebook_id>/content/generate', methods=['POST'])
@jwt_required()
def generate_content(notebook_id):
    """Generate new content from notebook sources"""
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
        
        # Validate required fields
        content_type = data.get('type')
        if not content_type:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'Content type is required'}
            }), 400
        
        # Validate content type
        valid_types = ['summary', 'faq', 'timeline', 'study_guide', 'briefing']
        if content_type not in valid_types:
            return jsonify({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR', 
                    'message': f'Invalid content type. Must be one of: {", ".join(valid_types)}'
                }
            }), 400
        
        # Get generation parameters
        title = data.get('title')
        custom_prompt = data.get('custom_prompt')
        source_ids = data.get('source_ids', [])  # Optional: specific sources to use
        max_sources = min(data.get('max_sources', 20), 50)  # Limit for performance
        
        # Get sources to use for generation
        if source_ids:
            # Use specific sources
            sources_query = Source.query.filter(
                Source.id.in_(source_ids),
                Source.notebook_id == notebook_id,
                Source.status == 'processed'
            )
        else:
            # Use all processed sources in the notebook
            sources_query = Source.query.filter_by(
                notebook_id=notebook_id,
                status='processed'
            )
        
        sources = sources_query.limit(max_sources).all()
        
        if not sources:
            return jsonify({
                'success': False,
                'error': {'code': 'NO_SOURCES', 'message': 'No processed sources available for content generation'}
            }), 400
        
        # Get relevant chunks from vector store
        # For content generation, we want comprehensive coverage, not just query-specific chunks
        all_chunks = []
        for source in sources:
            # Get chunks for each source
            source_chunks = vector_store.search_similar_chunks(
                notebook_id=notebook_id,
                query=f"content from {source.title}",  # Generic query to get source content
                n_results=10,  # Get multiple chunks per source
                source_ids=[source.id]
            )
            all_chunks.extend(source_chunks)
        
        if not all_chunks:
            return jsonify({
                'success': False,
                'error': {'code': 'NO_CONTENT', 'message': 'No content chunks available for generation'}
            }), 400
        
        # Generate content using AI service
        generation_result = ai_service.generate_content(
            content_type=content_type,
            sources=all_chunks,
            title=title,
            custom_prompt=custom_prompt
        )
        
        if generation_result.get('error'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'GENERATION_ERROR',
                    'message': 'Content generation failed',
                    'details': generation_result.get('error')
                }
            }), 500
        
        # Save generated content to database
        generated_content = GeneratedContent(
            notebook_id=notebook_id,
            type=content_type,
            title=generation_result.get('title', f"Generated {content_type.title()}"),
            content=generation_result.get('content', '')
        )
        
        # Set source IDs
        generated_content.set_source_ids([source.id for source in sources])
        
        # Set generation parameters
        generation_params = {
            'content_type': content_type,
            'custom_prompt': custom_prompt,
            'max_sources': max_sources,
            'sources_used': len(sources),
            'chunks_used': len(all_chunks)
        }
        generated_content.set_generation_params(generation_params)
        
        # Set citations
        citations = generation_result.get('citations', [])
        generated_content.set_citations(citations)
        
        # Set statistics
        stats = {
            'word_count': len(generation_result.get('content', '').split()),
            'character_count': len(generation_result.get('content', '')),
            'generation_time': generation_result.get('generation_metadata', {}).get('timestamp'),
            'model_used': generation_result.get('generation_metadata', {}).get('model'),
            'provider_used': generation_result.get('generation_metadata', {}).get('provider')
        }
        generated_content.set_statistics(stats)
        
        db.session.add(generated_content)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': generated_content.to_dict(),
            'message': f'{content_type.title()} generated successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to generate content',
                'details': str(e)
            }
        }), 500

@content_bp.route('/notebooks/<notebook_id>/content/<content_id>', methods=['GET'])
@jwt_required()
def get_generated_content(notebook_id, content_id):
    """Get specific generated content"""
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
        
        content = GeneratedContent.query.filter_by(
            id=content_id,
            notebook_id=notebook_id
        ).first()
        
        if not content:
            return jsonify({
                'success': False,
                'error': {'code': 'CONTENT_NOT_FOUND', 'message': 'Generated content not found'}
            }), 404
        
        return jsonify({
            'success': True,
            'data': content.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get generated content',
                'details': str(e)
            }
        }), 500

@content_bp.route('/notebooks/<notebook_id>/content/<content_id>', methods=['PUT'])
@jwt_required()
def update_generated_content(notebook_id, content_id):
    """Update generated content"""
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
        
        content = GeneratedContent.query.filter_by(
            id=content_id,
            notebook_id=notebook_id
        ).first()
        
        if not content:
            return jsonify({
                'success': False,
                'error': {'code': 'CONTENT_NOT_FOUND', 'message': 'Generated content not found'}
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'title' in data:
            content.title = data['title'].strip()
        if 'content' in data:
            content.content = data['content']
        
        content.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': content.to_dict(),
            'message': 'Content updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to update content',
                'details': str(e)
            }
        }), 500

@content_bp.route('/notebooks/<notebook_id>/content/<content_id>', methods=['DELETE'])
@jwt_required()
def delete_generated_content(notebook_id, content_id):
    """Delete generated content"""
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
        
        content = GeneratedContent.query.filter_by(
            id=content_id,
            notebook_id=notebook_id
        ).first()
        
        if not content:
            return jsonify({
                'success': False,
                'error': {'code': 'CONTENT_NOT_FOUND', 'message': 'Generated content not found'}
            }), 404
        
        db.session.delete(content)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Generated content deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to delete content',
                'details': str(e)
            }
        }), 500

@content_bp.route('/notebooks/<notebook_id>/content/types', methods=['GET'])
@jwt_required()
def get_content_types():
    """Get available content generation types and their descriptions"""
    try:
        content_types = {
            'summary': {
                'name': 'Summary',
                'description': 'Create a comprehensive summary of your documents with key points and main themes',
                'icon': 'document-text',
                'estimated_time': '1-2 minutes'
            },
            'faq': {
                'name': 'FAQ',
                'description': 'Generate frequently asked questions and answers based on your content',
                'icon': 'question-mark-circle',
                'estimated_time': '2-3 minutes'
            },
            'timeline': {
                'name': 'Timeline',
                'description': 'Create a chronological timeline of events and developments',
                'icon': 'clock',
                'estimated_time': '1-2 minutes'
            },
            'study_guide': {
                'name': 'Study Guide',
                'description': 'Generate a comprehensive study guide with key concepts and questions',
                'icon': 'academic-cap',
                'estimated_time': '2-4 minutes'
            },
            'briefing': {
                'name': 'Briefing Document',
                'description': 'Create a concise briefing with key insights and actionable items',
                'icon': 'clipboard-document-list',
                'estimated_time': '1-2 minutes'
            }
        }
        
        return jsonify({
            'success': True,
            'data': {
                'content_types': content_types,
                'total_types': len(content_types)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get content types',
                'details': str(e)
            }
        }), 500

@content_bp.route('/notebooks/<notebook_id>/content/regenerate/<content_id>', methods=['POST'])
@jwt_required()
def regenerate_content(notebook_id, content_id):
    """Regenerate existing content with new parameters"""
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
        
        content = GeneratedContent.query.filter_by(
            id=content_id,
            notebook_id=notebook_id
        ).first()
        
        if not content:
            return jsonify({
                'success': False,
                'error': {'code': 'CONTENT_NOT_FOUND', 'message': 'Generated content not found'}
            }), 404
        
        data = request.get_json()
        
        # Get regeneration parameters
        custom_prompt = data.get('custom_prompt')
        use_different_sources = data.get('use_different_sources', False)
        
        # Get sources (reuse original sources or get new ones)
        if use_different_sources:
            source_ids = data.get('source_ids', [])
            if source_ids:
                sources = Source.query.filter(
                    Source.id.in_(source_ids),
                    Source.notebook_id == notebook_id,
                    Source.status == 'processed'
                ).all()
            else:
                sources = Source.query.filter_by(
                    notebook_id=notebook_id,
                    status='processed'
                ).limit(20).all()
        else:
            # Use original sources
            original_source_ids = content.get_source_ids()
            sources = Source.query.filter(
                Source.id.in_(original_source_ids),
                Source.notebook_id == notebook_id
            ).all()
        
        if not sources:
            return jsonify({
                'success': False,
                'error': {'code': 'NO_SOURCES', 'message': 'No sources available for regeneration'}
            }), 400
        
        # Get content chunks
        all_chunks = []
        for source in sources:
            source_chunks = vector_store.search_similar_chunks(
                notebook_id=notebook_id,
                query=f"content from {source.title}",
                n_results=10,
                source_ids=[source.id]
            )
            all_chunks.extend(source_chunks)
        
        # Regenerate content
        generation_result = ai_service.generate_content(
            content_type=content.type,
            sources=all_chunks,
            title=content.title,
            custom_prompt=custom_prompt
        )
        
        if generation_result.get('error'):
            return jsonify({
                'success': False,
                'error': {
                    'code': 'GENERATION_ERROR',
                    'message': 'Content regeneration failed',
                    'details': generation_result.get('error')
                }
            }), 500
        
        # Update content
        content.content = generation_result.get('content', '')
        content.updated_at = datetime.utcnow()
        
        # Update generation parameters
        generation_params = content.get_generation_params()
        generation_params.update({
            'regenerated': True,
            'regeneration_date': datetime.utcnow().isoformat(),
            'custom_prompt': custom_prompt,
            'sources_used': len(sources),
            'chunks_used': len(all_chunks)
        })
        content.set_generation_params(generation_params)
        
        # Update statistics
        stats = content.get_statistics()
        stats.update({
            'word_count': len(generation_result.get('content', '').split()),
            'character_count': len(generation_result.get('content', '')),
            'last_regeneration': datetime.utcnow().isoformat()
        })
        content.set_statistics(stats)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': content.to_dict(),
            'message': 'Content regenerated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to regenerate content',
                'details': str(e)
            }
        }), 500

