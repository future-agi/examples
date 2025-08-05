"""
Banking AI Agent - Main Application
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from getpass import getpass

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Import core components
from core.agent import BankingAIAgent

# Load environment variables
load_dotenv()

if not os.getenv("FI_API_KEY"):
    os.environ["FI_API_KEY"] = getpass("Enter your FI_API_KEY: ")

if not os.getenv("FI_SECRET_KEY"):
    os.environ["FI_SECRET_KEY"] = getpass("Enter your FI_SECRET_KEY: ")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('BankingAIAgent')

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global agent instance
banking_agent = None

def create_agent_config() -> Dict[str, Any]:
    """Create configuration for the banking AI agent"""
    return {
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'model_name': os.getenv('MODEL_NAME', 'gpt-4o'),
        'temperature': float(os.getenv('TEMPERATURE', '0.1')),
        'max_tokens': int(os.getenv('MAX_TOKENS', '2000')),
        'chroma_persist_directory': os.getenv('CHROMA_PERSIST_DIRECTORY', './data/chroma_db'),
        'database_path': os.getenv('DATABASE_PATH', './data/memory.db'),
        'max_context_length': int(os.getenv('MAX_CONTEXT_LENGTH', '10')),
        'context_window_hours': int(os.getenv('CONTEXT_WINDOW_HOURS', '24')),
        'chunk_size': int(os.getenv('CHUNK_SIZE', '1000')),
        'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', '200')),
        'max_retrieval_docs': int(os.getenv('MAX_RETRIEVAL_DOCS', '10')),
        'embedding_model': os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
    }

def initialize_agent():
    """Initialize the banking AI agent"""
    global banking_agent
    
    try:
        config = create_agent_config()
        
        # Validate required configuration
        if not config['openai_api_key']:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Create agent instance
        banking_agent = BankingAIAgent(config)
        
        # Initialize async components in a new event loop
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(banking_agent.initialize_async_components())
        loop.close()
        
        logger.info("Banking AI Agent initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Banking AI Agent: {str(e)}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if banking_agent is None:
            return jsonify({
                'status': 'error',
                'message': 'Agent not initialized'
            }), 500
        
        # Get status from all components
        status = banking_agent.get_health_status()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'agent_status': status
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint for customer interactions"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided'
            }), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        customer_id = data.get('customer_id')
        session_id = data.get('session_id')
        context = data.get('context', {})
        
        logger.info(f"Processing chat request: {query[:100]}...")
        
        # Process query with banking agent (sync version)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(banking_agent.process_query(
            query=query,
            customer_id=customer_id,
            session_id=session_id,
            context=context
        ))
        loop.close()
        
        return jsonify({
            'success': True,
            'response': result.content,
            'plan_id': result.execution_plan.get('plan_id') if result.execution_plan else None,
            'confidence_score': result.confidence,
            'compliance_status': result.compliance_status,
            'execution_time': result.execution_plan.get('total_estimated_duration') if result.execution_plan else None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500

@app.route('/account/balance', methods=['POST'])
def get_account_balance():
    """Get account balance for a customer"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        data = request.get_json()
        customer_id = data.get('customer_id')
        account_id = data.get('account_id')
        
        if not customer_id or not account_id:
            return jsonify({
                'success': False,
                'error': 'customer_id and account_id are required'
            }), 400
        
        # Use banking tools to get balance (sync version)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(banking_agent.tools_manager.get_account_balance(customer_id, account_id))
        loop.close()
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting account balance: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/account/transactions', methods=['POST'])
async def get_transaction_history():
    """Get transaction history for an account"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        data = request.get_json()
        customer_id = data.get('customer_id')
        account_id = data.get('account_id')
        limit = data.get('limit', 10)
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not customer_id or not account_id:
            return jsonify({
                'success': False,
                'error': 'customer_id and account_id are required'
            }), 400
        
        # Use banking tools to get transactions
        result = await banking_agent.tools_manager.get_transaction_history(
            customer_id, account_id, limit, start_date, end_date
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting transaction history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/transfer', methods=['POST'])
async def transfer_funds():
    """Transfer funds between accounts"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        data = request.get_json()
        customer_id = data.get('customer_id')
        from_account = data.get('from_account')
        to_account = data.get('to_account')
        amount = data.get('amount')
        description = data.get('description', '')
        
        if not all([customer_id, from_account, to_account, amount]):
            return jsonify({
                'success': False,
                'error': 'customer_id, from_account, to_account, and amount are required'
            }), 400
        
        try:
            amount = float(amount)
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Amount must be a valid number'
            }), 400
        
        # Check fraud risk first
        fraud_check = await banking_agent.tools_manager.check_fraud_risk(
            customer_id, 'transfer', amount, from_account
        )
        
        if fraud_check['success'] and fraud_check['recommendation'] == 'block':
            return jsonify({
                'success': False,
                'error': 'Transaction blocked due to fraud risk',
                'fraud_risk': fraud_check
            }), 403
        
        # Process transfer
        result = await banking_agent.tools_manager.transfer_funds(
            customer_id, from_account, to_account, amount, description
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error processing transfer: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/products/<product_type>', methods=['GET'])
async def get_product_info(product_type):
    """Get information about banking products"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        # Use banking tools to get product information
        result = await banking_agent.tools_manager.get_product_information(product_type)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting product information: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/compliance/check', methods=['POST'])
async def check_compliance():
    """Check compliance for a query or operation"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        data = request.get_json()
        query = data.get('query', '')
        customer_id = data.get('customer_id')
        context = data.get('context', {})
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Perform compliance check
        result = await banking_agent.compliance_checker.check_query(
            query, customer_id, context
        )
        
        return jsonify({
            'success': True,
            'compliance_result': {
                'status': result.status,
                'confidence': result.confidence,
                'violations': result.violations,
                'warnings': result.warnings,
                'guidance': result.guidance,
                'required_actions': result.required_actions,
                'escalation_required': result.escalation_required
            }
        })
        
    except Exception as e:
        logger.error(f"Error checking compliance: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/memory/context', methods=['POST'])
async def get_memory_context():
    """Get conversation context from memory"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        data = request.get_json()
        customer_id = data.get('customer_id')
        session_id = data.get('session_id')
        query = data.get('query')
        
        # Get context from memory system
        context = await banking_agent.memory_system.get_context(
            customer_id, session_id, query
        )
        
        return jsonify({
            'success': True,
            'context': context
        })
        
    except Exception as e:
        logger.error(f"Error getting memory context: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/analytics/quality', methods=['GET'])
def get_quality_metrics():
    """Get quality metrics from self-reflection module"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        # Get quality metrics
        metrics = banking_agent.reflection_module.get_quality_metrics()
        
        return jsonify({
            'success': True,
            'quality_metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting quality metrics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/knowledge/search', methods=['POST'])
async def search_knowledge():
    """Search the banking knowledge base"""
    try:
        if banking_agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 500
        
        data = request.get_json()
        query = data.get('query', '')
        category = data.get('category')
        limit = data.get('limit', 5)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Query is required'
            }), 400
        
        # Search knowledge base
        results = await banking_agent.rag_system.search_similar(query, category, limit)
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'category': category
        })
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    try:
        # Initialize the banking agent
        initialize_agent()
        
        # Start the Flask application
        port = int(os.getenv('PORT', 5000))
        debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"Starting Banking AI Agent on port {port}")
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        exit(1)