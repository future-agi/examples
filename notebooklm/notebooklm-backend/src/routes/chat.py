from flask import Blueprint, request, jsonify, Response, stream_template
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
from datetime import datetime

from src.models.user import db, User
from src.models.notebook import Notebook, Conversation
from src.services.ai_service import AIService
from src.services.vector_store import VectorStore

chat_bp = Blueprint('chat', __name__)

# Initialize services
ai_service = AIService()
vector_store = VectorStore()

def get_current_user():
    """Get current authenticated user"""
    user_id = get_jwt_identity()
    return User.query.get(user_id)

@chat_bp.route('/notebooks/<notebook_id>/conversations', methods=['GET'])
@jwt_required()
def list_conversations(notebook_id):
    """List all conversations for a notebook"""
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
        
        # Get conversations
        offset = (page - 1) * limit
        conversations = Conversation.query.filter_by(notebook_id=notebook_id) \
            .order_by(Conversation.updated_at.desc()) \
            .offset(offset).limit(limit).all()
        
        total_count = Conversation.query.filter_by(notebook_id=notebook_id).count()
        
        # Format response
        conversations_data = []
        for conv in conversations:
            conv_data = conv.to_dict()
            # Only include last few messages for list view
            messages = conv_data.get('messages', [])
            conv_data['messages'] = messages[-3:] if len(messages) > 3 else messages
            conv_data['message_count'] = len(messages)
            conversations_data.append(conv_data)
        
        return jsonify({
            'success': True,
            'data': {
                'conversations': conversations_data,
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
                'message': 'Failed to list conversations',
                'details': str(e)
            }
        }), 500

@chat_bp.route('/notebooks/<notebook_id>/conversations', methods=['POST'])
@jwt_required()
def create_conversation(notebook_id):
    """Create a new conversation"""
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
        title = data.get('title', f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # Create conversation
        conversation = Conversation(
            notebook_id=notebook_id,
            title=title
        )
        
        db.session.add(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': conversation.to_dict(),
            'message': 'Conversation created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to create conversation',
                'details': str(e)
            }
        }), 500

@chat_bp.route('/notebooks/<notebook_id>/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(notebook_id, conversation_id):
    """Get detailed conversation with all messages"""
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
        
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            notebook_id=notebook_id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': {'code': 'CONVERSATION_NOT_FOUND', 'message': 'Conversation not found'}
            }), 404
        
        return jsonify({
            'success': True,
            'data': conversation.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get conversation',
                'details': str(e)
            }
        }), 500

@chat_bp.route('/notebooks/<notebook_id>/conversations/<conversation_id>/messages', methods=['POST'])
@jwt_required()
def send_message(notebook_id, conversation_id):
    """Send a message and get AI response"""
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
        
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            notebook_id=notebook_id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': {'code': 'CONVERSATION_NOT_FOUND', 'message': 'Conversation not found'}
            }), 404
        
        data = request.get_json()
        message_content = data.get('message', '').strip()
        
        if not message_content:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'Message content is required'}
            }), 400
        
        # Check if streaming is requested
        stream_response = data.get('stream', False)
        
        # Add user message to conversation
        user_message = {
            'type': 'user',
            'content': message_content,
            'timestamp': datetime.now().isoformat()
        }
        conversation.add_message(user_message)
        
        # Analyze query intent
        intent_analysis = ai_service.analyze_query_intent(message_content)
        
        # Get relevant context from vector store
        context_sources = []
        if intent_analysis.get('context_requirements', {}).get('needs_sources', True):
            max_sources = intent_analysis.get('context_requirements', {}).get('max_sources', 20)  # Standard context
            context_sources = vector_store.hybrid_search(
                notebook_id=notebook_id,
                query=message_content,
                n_results=max_sources
            )
        
        # Prepare conversation history for context
        messages = conversation.get_messages()
        recent_messages = messages[-20:]  # Last 20 messages for standard context
        
        # Format messages for AI
        ai_messages = []
        for msg in recent_messages[:-1]:  # Exclude the current user message
            if msg['type'] in ['user', 'assistant']:
                ai_messages.append({
                    'role': msg['type'] if msg['type'] != 'assistant' else 'assistant',
                    'content': msg['content']
                })
        
        # Add current user message
        ai_messages.append({
            'role': 'user',
            'content': message_content
        })
        
        if stream_response:
            return Response(
                stream_ai_response(conversation, ai_messages, context_sources),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            # Get AI response
            ai_response = ai_service.chat_completion(
                messages=ai_messages,
                context_sources=context_sources
            )
            
            # Add AI response to conversation
            assistant_message = {
                'type': 'assistant',
                'content': ai_response.get('content', 'I apologize, but I encountered an error processing your request.'),
                'metadata': {
                    'model': ai_response.get('model'),
                    'provider': ai_response.get('provider'),
                    'usage': ai_response.get('usage'),
                    'sources_used': len(context_sources),
                    'intent_analysis': intent_analysis
                },
                'timestamp': datetime.now().isoformat()
            }
            conversation.add_message(assistant_message)
            
            # Update conversation title if it's the first exchange
            if len(conversation.get_messages()) == 2:  # User + Assistant message
                conversation.title = message_content[:50] + "..." if len(message_content) > 50 else message_content
            
            db.session.commit()
            
            # Update user usage stats
            user.update_usage_stats()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'data': {
                    'conversation': conversation.to_dict(),
                    'response': assistant_message,
                    'context_sources': len(context_sources),
                    'intent_analysis': intent_analysis
                },
                'message': 'Message sent successfully'
            })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to send message',
                'details': str(e)
            }
        }), 500

def stream_ai_response(conversation, ai_messages, context_sources):
    """Stream AI response for real-time chat"""
    try:
        # Get streaming response from AI service
        response_stream = ai_service.chat_completion(
            messages=ai_messages,
            context_sources=context_sources,
            stream=True
        )
        
        full_response = ""
        
        for chunk in response_stream:
            if chunk.get('type') == 'content':
                content = chunk.get('content', '')
                full_response += content
                
                # Send chunk to client
                yield f"data: {json.dumps({'type': 'content', 'content': content})}\\n\\n"
            
            elif chunk.get('type') == 'error':
                yield f"data: {json.dumps({'type': 'error', 'error': chunk.get('error')})}\\n\\n"
                return
            
            elif chunk.get('type') == 'done':
                # Add complete response to conversation
                assistant_message = {
                    'type': 'assistant',
                    'content': full_response,
                    'metadata': {
                        'sources_used': len(context_sources),
                        'streaming': True
                    },
                    'timestamp': datetime.now().isoformat()
                }
                conversation.add_message(assistant_message)
                db.session.commit()
                
                yield f"data: {json.dumps({'type': 'done', 'message_id': assistant_message.get('id')})}\\n\\n"
                return
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\\n\\n"

@chat_bp.route('/notebooks/<notebook_id>/conversations/<conversation_id>', methods=['DELETE'])
@jwt_required()
def delete_conversation(notebook_id, conversation_id):
    """Delete a conversation"""
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
        
        conversation = Conversation.query.filter_by(
            id=conversation_id, 
            notebook_id=notebook_id
        ).first()
        
        if not conversation:
            return jsonify({
                'success': False,
                'error': {'code': 'CONVERSATION_NOT_FOUND', 'message': 'Conversation not found'}
            }), 404
        
        db.session.delete(conversation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Conversation deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to delete conversation',
                'details': str(e)
            }
        }), 500

@chat_bp.route('/notebooks/<notebook_id>/search', methods=['POST'])
@jwt_required()
def search_notebook(notebook_id):
    """Search within notebook content"""
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
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': {'code': 'VALIDATION_ERROR', 'message': 'Search query is required'}
            }), 400
        
        # Get search parameters
        max_results = min(data.get('max_results', 20), 100)
        source_ids = data.get('source_ids')  # Optional filter by specific sources
        
        # Perform hybrid search
        search_results = vector_store.hybrid_search(
            notebook_id=notebook_id,
            query=query,
            n_results=max_results,
            source_ids=source_ids
        )
        
        # Format results
        formatted_results = []
        for result in search_results:
            metadata = result.get('metadata', {})
            formatted_results.append({
                'text': result.get('text', ''),
                'similarity_score': result.get('similarity_score', 0),
                'hybrid_score': result.get('hybrid_score', 0),
                'source_id': metadata.get('source_id'),
                'chunk_index': metadata.get('chunk_index'),
                'word_count': metadata.get('word_count'),
                'character_count': metadata.get('character_count')
            })
        
        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'results': formatted_results,
                'total_results': len(formatted_results),
                'search_metadata': {
                    'notebook_id': notebook_id,
                    'timestamp': datetime.now().isoformat()
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Search failed',
                'details': str(e)
            }
        }), 500

@chat_bp.route('/ai/health', methods=['GET'])
@jwt_required()
def ai_health():
    """Get AI service health status"""
    try:
        health_status = ai_service.get_health_status()
        vector_health = vector_store.get_health_status()
        
        return jsonify({
            'success': True,
            'data': {
                'ai_service': health_status,
                'vector_store': vector_health,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'Failed to get AI health status',
                'details': str(e)
            }
        }), 500

