"""
Flask API Routes for Text-to-SQL Agent

This module provides REST API endpoints for the text-to-SQL functionality.
"""

import os
import json
import logging
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from typing import Dict, Any, Optional
import traceback

from src.models.text2sql_agent import create_agent, AgentConfig, Text2SQLAgent

# Create blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Global agent instance
_agent: Optional[Text2SQLAgent] = None


def get_agent() -> Text2SQLAgent:
    """Get or create the global agent instance"""
    global _agent
    
    if _agent is None:
        # Create agent with configuration from environment or defaults
        config = AgentConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            bigquery_project_id=os.getenv('GOOGLE_CLOUD_PROJECT', 'revionics-demo'),
            bigquery_dataset_id=os.getenv('BIGQUERY_DATASET', 'retail_analytics'),
            bigquery_credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            vector_store_path=os.getenv('VECTOR_STORE_PATH', './chroma_db'),
            enable_cache=os.getenv('ENABLE_CACHE', 'true').lower() == 'true',
            max_results=int(os.getenv('MAX_RESULTS', '1000')),
            enable_visualization=os.getenv('ENABLE_VISUALIZATION', 'true').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
        
        _agent = Text2SQLAgent(config)
        current_app.logger.info("Text-to-SQL Agent initialized")
    
    return _agent


@api_bp.route('/query', methods=['POST'])
@cross_origin()
def process_query():
    """
    Process a natural language query
    
    Request body:
    {
        "question": "What is the current price for UPC code '123456'?",
        "user_context": {
            "user_id": "user123",
            "preferences": {}
        }
    }
    
    Response:
    {
        "success": true,
        "response": "The current price for UPC code '123456' is $12.99.",
        "sql_query": "SELECT current_price FROM pricing WHERE upc_code = '123456'",
        "data_table": "<table>...</table>",
        "visualization": "base64_encoded_image",
        "key_insights": ["Price is within normal range"],
        "execution_time": 2.5,
        "row_count": 1,
        "confidence_score": 0.95,
        "metadata": {}
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON',
                'error_code': 'INVALID_REQUEST'
            }), 400
        
        data = request.get_json()
        question = data.get('question')
        
        if not question or not isinstance(question, str):
            return jsonify({
                'success': False,
                'error': 'Question is required and must be a string',
                'error_code': 'MISSING_QUESTION'
            }), 400
        
        if len(question.strip()) == 0:
            return jsonify({
                'success': False,
                'error': 'Question cannot be empty',
                'error_code': 'EMPTY_QUESTION'
            }), 400
        
        # Get user context
        user_context = data.get('user_context', {})
        
        # Process the question
        agent = get_agent()
        response = agent.process_question(question, user_context)
        
        # Format response
        api_response = {
            'success': response.success,
            'response': response.natural_language_response,
            'sql_query': response.sql_query,
            'data_table': response.data_table,
            'visualization': response.visualization,
            'key_insights': response.key_insights,
            'execution_time': response.execution_time,
            'row_count': response.row_count,
            'confidence_score': response.confidence_score,
            'metadata': response.metadata
        }
        
        if not response.success:
            api_response['error'] = response.error_message
            api_response['error_code'] = 'QUERY_EXECUTION_FAILED'
        
        status_code = 200 if response.success else 500
        return jsonify(api_response), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error processing query: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@api_bp.route('/refine', methods=['POST'])
@cross_origin()
def refine_query():
    """
    Refine a query based on user feedback
    
    Request body:
    {
        "original_question": "Show me sales data",
        "feedback": "I want data for last month only"
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON',
                'error_code': 'INVALID_REQUEST'
            }), 400
        
        data = request.get_json()
        original_question = data.get('original_question')
        feedback = data.get('feedback')
        
        if not original_question or not feedback:
            return jsonify({
                'success': False,
                'error': 'Both original_question and feedback are required',
                'error_code': 'MISSING_PARAMETERS'
            }), 400
        
        # Refine the query
        agent = get_agent()
        response = agent.refine_query(original_question, feedback)
        
        # Format response (same as process_query)
        api_response = {
            'success': response.success,
            'response': response.natural_language_response,
            'sql_query': response.sql_query,
            'data_table': response.data_table,
            'visualization': response.visualization,
            'key_insights': response.key_insights,
            'execution_time': response.execution_time,
            'row_count': response.row_count,
            'confidence_score': response.confidence_score,
            'metadata': response.metadata
        }
        
        if not response.success:
            api_response['error'] = response.error_message
            api_response['error_code'] = 'QUERY_REFINEMENT_FAILED'
        
        status_code = 200 if response.success else 500
        return jsonify(api_response), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error refining query: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}',
            'error_code': 'INTERNAL_ERROR'
        }), 500


@api_bp.route('/validate-sql', methods=['POST'])
@cross_origin()
def validate_sql():
    """
    Validate SQL query without executing it
    
    Request body:
    {
        "sql_query": "SELECT * FROM products WHERE upc_code = '123456'"
    }
    
    Response:
    {
        "valid": true,
        "error_message": null
    }
    """
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
        
        data = request.get_json()
        sql_query = data.get('sql_query')
        
        if not sql_query:
            return jsonify({
                'success': False,
                'error': 'sql_query is required'
            }), 400
        
        # Validate SQL
        agent = get_agent()
        is_valid, error_message = agent.validate_sql(sql_query)
        
        return jsonify({
            'valid': is_valid,
            'error_message': error_message
        })
        
    except Exception as e:
        current_app.logger.error(f"Error validating SQL: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@api_bp.route('/schema', methods=['GET'])
@cross_origin()
def get_schema():
    """
    Get database schema information
    
    Query parameters:
    - table_name (optional): Specific table name
    
    Response:
    {
        "available_tables": ["products", "pricing", "elasticity"],
        "table_schemas": {...}
    }
    """
    try:
        table_name = request.args.get('table_name')
        
        agent = get_agent()
        schema_info = agent.get_schema_info(table_name)
        
        return jsonify(schema_info)
        
    except Exception as e:
        current_app.logger.error(f"Error getting schema: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@api_bp.route('/stats', methods=['GET'])
@cross_origin()
def get_stats():
    """
    Get agent performance statistics
    
    Response:
    {
        "total_queries": 150,
        "successful_queries": 142,
        "success_rate": 0.947,
        "average_execution_time": 2.3,
        "bigquery_stats": {...},
        "vector_store_stats": {...}
    }
    """
    try:
        agent = get_agent()
        stats = agent.get_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.error(f"Error getting stats: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@api_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Perform health check on all components
    
    Response:
    {
        "overall_status": "healthy",
        "components": {
            "bigquery": {"status": "healthy", "available_tables": 5},
            "vector_store": {"status": "healthy", "collections": {...}},
            "openai": {"status": "healthy", "model": "gpt-4o"}
        },
        "timestamp": "2025-01-15T10:30:00Z"
    }
    """
    try:
        agent = get_agent()
        health_status = agent.health_check()
        
        # Set HTTP status based on overall health
        if health_status['overall_status'] == 'healthy':
            status_code = 200
        elif health_status['overall_status'] == 'degraded':
            status_code = 200  # Still operational but with issues
        else:
            status_code = 503  # Service unavailable
        
        return jsonify(health_status), status_code
        
    except Exception as e:
        current_app.logger.error(f"Error in health check: {str(e)}")
        
        return jsonify({
            'overall_status': 'unhealthy',
            'error': str(e),
            'timestamp': None
        }), 503


@api_bp.route('/clear-cache', methods=['POST'])
@cross_origin()
def clear_cache():
    """
    Clear all caches
    
    Response:
    {
        "success": true,
        "message": "Caches cleared successfully"
    }
    """
    try:
        agent = get_agent()
        agent.clear_cache()
        
        return jsonify({
            'success': True,
            'message': 'Caches cleared successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


@api_bp.route('/examples', methods=['GET'])
@cross_origin()
def get_examples():
    """
    Get example questions for the interface
    
    Response:
    {
        "examples": [
            {
                "category": "Pricing Analysis",
                "questions": [
                    "What is the current price for UPC code '0020282000000'?",
                    "Show me pricing strategies for BREAD & WRAPS in Banner 2"
                ]
            }
        ]
    }
    """
    try:
        examples = {
            "examples": [
                {
                    "category": "Pricing Analysis",
                    "questions": [
                        "What is the current price for UPC code '0020282000000'?",
                        "Show me pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'",
                        "What are the factors driving the suggested price for items in price family '7286'?",
                        "List items with the highest units impact from suggested prices for the week ending '2025-04-15'"
                    ]
                },
                {
                    "category": "Elasticity Analysis",
                    "questions": [
                        "Show me the top 10 items by elasticity in the frozen food category",
                        "Which products are candidates for price reductions due to high elasticity?",
                        "What items should I decrease the price on to drive units in zone 'Orange'?",
                        "Which items have changed elasticity the most in the last 12 weeks?"
                    ]
                },
                {
                    "category": "Competitive Analysis",
                    "questions": [
                        "Which items have a CPI value higher than 1.05?",
                        "List articles where Walmart prices are higher than No Frills Ontario prices",
                        "What is the competitive price index for each subcategory under grocery?",
                        "Which competitor had the highest number of price increases in April 2025?"
                    ]
                },
                {
                    "category": "Sales & Performance",
                    "questions": [
                        "Show me the top 10 selling items within frozen food",
                        "What are the top 10 items by forecast sales within the bakery category?",
                        "Show me revenue by level 2 for the last 6 months in the POKE category",
                        "Which products have the highest selling units within frozen food?"
                    ]
                },
                {
                    "category": "Margin Analysis",
                    "questions": [
                        "Show me the bottom 10 lowest margin items in April",
                        "Show me all items with negative margin in the last 7 days",
                        "What is the impact on margin if I create a minimum price gap of 1% on 'C' products?",
                        "Show me items with the lowest margin percentage"
                    ]
                }
            ]
        }
        
        return jsonify(examples)
        
    except Exception as e:
        current_app.logger.error(f"Error getting examples: {str(e)}")
        
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500


# Error handlers
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found',
        'error_code': 'NOT_FOUND'
    }), 404


@api_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'error_code': 'METHOD_NOT_ALLOWED'
    }), 405


@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'error_code': 'INTERNAL_ERROR'
    }), 500

