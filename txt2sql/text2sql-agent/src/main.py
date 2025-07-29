"""
Main Application for Text-to-SQL Agent

This is the main entry point for the Text-to-SQL Agent using SQLite
backend. It provides both Flask API and Gradio interface with comprehensive
error handling and user experience improvements.
"""

import os
import sys
import logging
import threading
import time
import json
from datetime import datetime
import traceback
from typing import Dict, Any, Optional, List, Tuple

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Gradio is temporarily disabled due to queue compatibility issues
# import gradio as gr

# Import our SQLite-based components
try:
    from models.text2sql_agent_sqlite import Text2SQLAgentSQLite, AgentConfig, create_agent_sqlite
    from models.sqlite_client import create_sqlite_client
except ImportError as e:
    logging.error(f"Import error: {e}")
    logging.error("Please ensure all required dependencies are installed")
    sys.exit(1)

from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType
from traceai_openai import OpenAIInstrumentor
from opentelemetry import trace
from fi.evals import Evaluator
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import (
    ProjectType
)
from fi.evals import Evaluator
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="agent_text_to_sql",
    set_global_tracer_provider=True
)

evaluator = Evaluator(fi_api_key=os.getenv("FI_API_KEY"), fi_secret_key=os.getenv("FI_SECRET_KEY"))

OpenAIInstrumentor().instrument(tracer_provider=trace_provider)

trace.set_tracer_provider(trace_provider)
tracer = FITracer(trace_provider.get_tracer(__name__))


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
agent = None

# Flask app configuration
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
APP_CONFIG = {
    'flask_host': '0.0.0.0',
    'flask_port': 6001,
    'gradio_host': '0.0.0.0',
    'gradio_port': 7860,
    'database_path': 'retail_analytics.db',
    'vector_store_path': './chroma_db',
    'enable_debug': False,
    'max_query_length': 1000,
    'rate_limit_per_minute': 60
}

# Rate limiting (simple in-memory implementation)
query_timestamps = []
query_lock = threading.Lock()

def check_rate_limit() -> bool:
    """Simple rate limiting check"""
    with query_lock:
        current_time = time.time()
        # Remove timestamps older than 1 minute
        global query_timestamps
        query_timestamps = [ts for ts in query_timestamps if current_time - ts < 60]
        
        # Check if under limit
        if len(query_timestamps) < APP_CONFIG['rate_limit_per_minute']:
            query_timestamps.append(current_time)
            return True
        return False

def validate_question(question: str) -> Tuple[bool, Optional[str]]:
        with tracer.start_as_current_span("validate_question") as span:
            span.set_attribute("question", question)
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.CHAIN.value)
            span.set_attribute("input.value", json.dumps({"question": question}))
            span.set_attribute("output.value", json.dumps({"valid": True}))
            

        """Validate user question"""
        if not question or not question.strip():
            return False, "Question cannot be empty"
        
        if len(question) > APP_CONFIG['max_query_length']:
            return False, f"Question too long (max {APP_CONFIG['max_query_length']} characters)"
        
        # Basic content filtering
        forbidden_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        question_lower = question.lower()
        for keyword in forbidden_keywords:
            if keyword in question_lower:
                return False, f"Question contains forbidden keyword: {keyword}"
        
        return True, None

def initialize_agent():  
    """Initialize the Text-to-SQL agent with SQLite backend"""
    with tracer.start_as_current_span("initialize_agent") as span:
        span.set_attribute("initialize_agent", "initialize_agent")
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.AGENT.value)
        span.set_attribute("input.value", json.dumps({"initializing agent": True}))
        span.set_attribute("output.value", json.dumps({"success": True}))

        global agent
        
        try:
            logger.info("Initializing Text-to-SQL Agent with SQLite...")
            
            # Get OpenAI API key from environment
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                logger.warning("OPENAI_API_KEY not found in environment.")
                logger.warning("Using fallback mode with limited functionality.")
                # Use a placeholder key for fallback mode
                openai_api_key = "sk-fallback-mode-no-ai-features"
            else:
                logger.info(f"Found OpenAI API key: {openai_api_key[:20]}..." if len(openai_api_key) > 20 else openai_api_key[:10] + "...")
            
            # Create agent configuration
            config = AgentConfig(
                openai_api_key=openai_api_key,
                database_path=APP_CONFIG['database_path'],
                vector_store_path=APP_CONFIG['vector_store_path'],
                enable_cache=True,
                max_results=1000,
                enable_visualization=True,
                log_level="INFO"
            )
            
            # Create agent
            agent = Text2SQLAgentSQLite(config)
            
            if openai_api_key.startswith("sk-fallback"):
                logger.info("Text-to-SQL Agent initialized in FALLBACK MODE (limited functionality)")
                logger.info("To enable full AI features, set OPENAI_API_KEY environment variable")
            else:
                logger.info("Text-to-SQL Agent initialized successfully with full AI features")
            
            return True
            
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error initializing agent: {str(e)}")
            logger.info("Attempting to create basic fallback agent...")
            
            # Try to create a minimal fallback agent
            try:
                from models.sqlite_client import create_sqlite_client
                
                # Create a basic SQLite client for direct queries
                sqlite_client = create_sqlite_client(APP_CONFIG['database_path'])
                
                # Create a minimal agent wrapper
                class FallbackAgent:
                    def __init__(self, sqlite_client):
                        self.sqlite_client = sqlite_client
                        self.fallback_mode = True
                        
                    def health_check(self):
                        return {
                            'overall_status': 'degraded',
                            'message': 'Running in fallback mode - AI features disabled',
                            'components': {
                                'database': 'healthy',
                                'openai': 'unavailable',
                                'vector_store': 'unavailable'
                            },
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    def process_question(self, question, user_context=None):
                        with tracer.start_as_current_span("process_question") as span:
                            span.set_attribute("process_question", "process_question")
                            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.AGENT.value)
                            span.set_attribute("input.value", json.dumps({"question": question}))
                            span.set_attribute("output.value", json.dumps({"success": False}))

                            class BasicResponse:
                                def __init__(self):
                                    self.success = False
                                    self.natural_language_response = "AI features are not available. Please set OPENAI_API_KEY environment variable to enable full functionality."
                                    self.sql_query = None
                                    self.data_table = None
                                    self.visualization = None
                                    self.key_insights = ["AI features disabled - set OPENAI_API_KEY to enable"]
                                    self.execution_time = 0.0
                                    self.row_count = 0
                                    self.confidence_score = 0.0
                                    self.error_message = "OpenAI API key not configured"
                                    self.metadata = {"fallback_mode": True}
                            
                            return BasicResponse()
                        
                    def get_stats(self):
                        return {
                            'total_queries': 0,
                            'success_rate': 0.0,
                            'average_execution_time': 0.0,
                            'sqlite_stats': {
                                'total_queries': 0,
                                'cache_hit_rate': 0.0
                            },
                            'fallback_mode': True
                        }
                    
                    def get_schema_info(self, table_name=None):
                        with tracer.start_as_current_span("get_schema_info") as span:
                            span.set_attribute("get_schema_info", "get_schema_info")
                            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
                            span.set_attribute("input.value", json.dumps({"table_name": table_name}))

                            try:
                                # Get basic schema info from SQLite
                                tables = []
                                cursor = self.sqlite_client.connection.cursor()
                                
                                if table_name:
                                    cursor.execute(f"PRAGMA table_info({table_name})")
                                    columns = cursor.fetchall()
                                    span.set_attribute("output.value", json.dumps({"table": table_name, "columns": [{'name': col[1], 'type': col[2]} for col in columns]}))
                                    return {
                                        'table': table_name,
                                        'columns': [{'name': col[1], 'type': col[2]} for col in columns],
                                        'fallback_mode': True
                                    }
                                else:
                                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                                    tables = [row[0] for row in cursor.fetchall()]
                                    span.set_attribute("output.value", json.dumps({"tables": tables}))
                                    return {
                                        'tables': tables,
                                        'fallback_mode': True,
                                        'message': 'Basic schema info only - AI features disabled'
                                    }
                            except Exception as e:
                                span.set_attribute("output.value", json.dumps({"error": str(e)}))
                                return {
                                    'error': str(e),
                                    'fallback_mode': True
                                }
                        
                    def validate_sql(self, sql_query):
                        with tracer.start_as_current_span("validate_sql") as span:
                            span.set_attribute("validate_sql", "validate_sql")
                            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
                            span.set_attribute("input.value", json.dumps({"sql_query": sql_query}))

                            # Basic SQL validation
                            forbidden_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
                            upper_query = sql_query.upper()
                            
                            for keyword in forbidden_keywords:
                                if keyword in upper_query:
                                    span.set_attribute("output.value", json.dumps({"valid": False, "error": f"Forbidden keyword '{keyword}' detected"}))
                                    return False, f"Forbidden keyword '{keyword}' detected"
                            
                            span.set_attribute("output.value", json.dumps({"valid": True}))
                            return True, None
                        
                    def clear_cache(self):
                        pass  # No cache in fallback mode
                
                agent = FallbackAgent(sqlite_client)
                logger.info("Fallback agent created successfully")
                span.set_attribute("output.value", json.dumps({"success": True}))
                return True
                
            except Exception as fallback_error:
                logger.error(f"Failed to create fallback agent: {str(fallback_error)}")
                span.set_attribute("output.value", json.dumps({"success": False, "error": str(fallback_error)}))
                return False

# Flask API Routes
@app.route('/')
def index():    
    """Main page with improved UI"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text-to-SQL Agent</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 1000px; 
                margin: 0 auto; 
                background: rgba(255, 255, 255, 0.95); 
                padding: 30px; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
            }
            h1 { 
                color: #2c3e50; 
                text-align: center; 
                margin-bottom: 10px;
                font-size: 2.5em;
                font-weight: 700;
            }
            .subtitle {
                text-align: center;
                color: #7f8c8d;
                margin-bottom: 30px;
                font-size: 1.2em;
            }
            .status { 
                padding: 15px; 
                margin: 20px 0; 
                border-radius: 10px; 
                font-weight: 500;
            }
            .status.healthy { 
                background: linear-gradient(135deg, #a8e6cf 0%, #7fcdcd 100%); 
                color: #155724; 
                border: 1px solid #c3e6cb; 
            }
            .status.degraded { 
                background: linear-gradient(135deg, #ffd93d 0%, #ff9800 100%); 
                color: #856404; 
                border: 1px solid #ffeaa7; 
            }
            .status.unhealthy { 
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); 
                color: #721c24; 
                border: 1px solid #f5c6cb; 
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .card {
                background: white;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
                border: 1px solid #e1e8ed;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }
            .card:hover {
                transform: translateY(-5px);
                box-shadow: 0 20px 40px rgba(0,0,0,0.15);
            }
            .card h3 {
                color: #2c3e50;
                margin-top: 0;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .api-link { 
                display: inline-block; 
                margin: 5px; 
                padding: 12px 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                text-decoration: none; 
                border-radius: 25px; 
                font-weight: 500;
                transition: all 0.3s ease;
                border: 2px solid transparent;
            }
            .api-link:hover { 
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
                text-decoration: none;
                color: white;
            }
            .gradio-link { 
                background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
            }
            .gradio-link:hover { 
                box-shadow: 0 10px 20px rgba(17, 153, 142, 0.3);
            }
            .examples {
                background: #f8f9fa;
                padding: 20px;
                border-radius: 15px;
                margin: 20px 0;
            }
            .examples ul {
                list-style: none;
                padding: 0;
            }
            .examples li {
                padding: 10px 0;
                border-bottom: 1px solid #e9ecef;
                font-style: italic;
                color: #495057;
            }
            .examples li:last-child {
                border-bottom: none;
            }
            .features {
                display: flex;
                flex-wrap: wrap;
                gap: 15px;
                margin: 20px 0;
            }
            .feature {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 0.9em;
                font-weight: 500;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏪 Text-to-SQL Agent</h1>
            <p class="subtitle">AI-powered natural language to SQL conversion for retail analytics</p>
            
            <div id="status" class="status">
                <strong>System Status:</strong> <span id="status-text">Checking...</span>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>💬 Interactive Chat Interface</h3>
                    <p>Use the Gradio-powered chat interface to ask questions about your retail data in natural language.</p>
                    <div class="features">
                        <span class="feature">Real-time chat</span>
                        <span class="feature">SQL generation</span>
                        <span class="feature">Data visualization</span>
                        <span class="feature">Insights</span>
                    </div>
                    <a href="http://localhost:7860" class="api-link gradio-link" target="_blank">Open Chat Interface</a>
                </div>
                
                <div class="card">
                    <h3>🔌 REST API</h3>
                    <p>Integrate the text-to-SQL functionality into your applications using our comprehensive REST API.</p>
                    <a href="/api/health" class="api-link">🔍 Health Check</a>
                    <a href="/api/stats" class="api-link">📊 Statistics</a>
                    <a href="/api/examples" class="api-link">📚 Examples</a>
                    <a href="/api/schema" class="api-link">🗄️ Schema</a>
                    <a href="/chat" class="api-link">💬 Simple Chat</a>
                </div>
            </div>
            
            <div class="examples">
                <h3>🎯 Sample Questions</h3>
                <ul>
                    <li>"What is the current price for UPC code '0020282000000'?"</li>
                    <li>"Show me the top 10 items by elasticity in the frozen food category"</li>
                    <li>"Which items have a CPI value higher than 1.05?"</li>
                    <li>"Show me the top 10 selling items within frozen food"</li>
                    <li>"Show me all items with negative margin in the last 7 days"</li>
                    <li>"What are the pricing strategies for BREAD & WRAPS in Banner 2?"</li>
                    <li>"List products where Walmart prices are higher than our prices"</li>
                    <li>"Show me revenue by category for the last 6 months"</li>
                </ul>
            </div>
        </div>
        
        <script>
            // Check system status
            fetch('/api/health')
                .then(response => response.json())
                .then(data => {
                    const statusDiv = document.getElementById('status');
                    const statusText = document.getElementById('status-text');
                    
                    statusDiv.className = 'status ' + data.overall_status;
                    statusText.textContent = data.overall_status.charAt(0).toUpperCase() + data.overall_status.slice(1);
                    
                    if (data.overall_status === 'degraded') {
                        statusText.textContent += ' (Some components unavailable, fallback mode active)';
                    }
                })
                .catch(error => {
                    const statusDiv = document.getElementById('status');
                    const statusText = document.getElementById('status-text');
                    statusDiv.className = 'status unhealthy';
                    statusText.textContent = 'Error checking status';
                });
        </script>
    </body>
    </html>
    """)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        if agent is None:
            return jsonify({
                'overall_status': 'unhealthy',
                'message': 'Agent not initialized',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        health_status = agent.health_check()
        
        status_code = 200 if health_status['overall_status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'overall_status': 'unhealthy',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    with tracer.start_as_current_span("process_query") as span:
        span.set_attribute("process_query", "process_query")
        span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.AGENT.value)
        
        """Process a natural language query"""
        try:
            if agent is None:
                return jsonify({
                    'success': False,
                    'error': 'Agent not initialized'
                }), 503
            
            # Check rate limit
            if not check_rate_limit():
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded. Please wait before making another request.'
                }), 429
            
            data = request.get_json()
            if not data or 'question' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing question in request'
                }), 400
            
            question = data['question']
            user_context = data.get('user_context', {})
            
            # Validate question
            is_valid, validation_error = validate_question(question)
            if not is_valid:
                return jsonify({
                    'success': False,
                    'error': validation_error
                }), 400
            
            logger.info(f"Processing query: {question}")
            span.set_attribute("input.value", question)
            # Process the question
            response = agent.process_question(question, user_context)
            # Convert response to JSON-serializable format
            result = {
                'success': response.success,
                'response': response.natural_language_response,
                'sql_query': response.sql_query,
                'data_table': response.data_table,
                'visualization': response.visualization,
                'key_insights': response.key_insights,
                'execution_time': response.execution_time,
                'row_count': response.row_count,
                'confidence_score': response.confidence_score,
                'error_message': response.error_message,
                'metadata': response.metadata
            }
            
            span.set_attribute("output.value", response.natural_language_response)

            print("#########################")
            print("completeness")
            print(json.dumps(question))
            print(json.dumps(response.natural_language_response))
            print("#########################")
            config_completeness = {
                "eval_templates" : "completeness",
                "inputs" : {
                    "input": json.dumps(question),
                    "output": json.dumps(response.natural_language_response),
                },
                "model_name" : "turing_large"
            }
            eval_result1 = evaluator.evaluate(
                **config_completeness, 
                custom_eval_name="completeness_check", 
                trace_eval=True
            )

            print("#########################")
            print("task_completion")
            print(json.dumps(question))
            print(json.dumps(response.natural_language_response))
            print("#########################")
            config_task_completion = {
                "eval_templates" : "task_completion",
                "inputs" : {
                    "input": json.dumps(question),
                    "output": json.dumps(response.natural_language_response),
                },
                "model_name" : "turing_large"
            }

            eval_result2 = evaluator.evaluate(
                **config_task_completion, 
                custom_eval_name="task_completion_check", 
                trace_eval=True
            )

            print("#########################")
            print("context_relevance")
            print(json.dumps(question))
            print(json.dumps(response.data_table))
            print("#########################")
            config_context_relevance = {
                "eval_templates" : "context_relevance",
                "inputs" : {
                    "input": json.dumps(question),
                    "context": json.dumps(response.data_table),
                },
                "model_name" : "turing_large"
            }   
            eval_result3 = evaluator.evaluate(
                **config_context_relevance, 
                custom_eval_name="context_relevance_check", 
                trace_eval=True
            )  

            print("#########################")
            print("answer_correctness")
            print(json.dumps(question))
            print(json.dumps(response.data_table))
            print(json.dumps(response.natural_language_response))
            print("#########################")
            config_answer_correctness_eval = {
                "eval_templates" : "answer_correctness_eval",
                "inputs" : {
                    "question": json.dumps(question),
                    "sql_result": json.dumps(response.data_table),
                    "answer": json.dumps(response.natural_language_response),
                },
                "model_name" : "turing_large"
            }   
            eval_result4 = evaluator.evaluate(
                **config_answer_correctness_eval, 
                custom_eval_name="answer_correctness_eval", 
                trace_eval=True
            )

            print("#########################")
            print("business_context_integration")
            print(json.dumps(response.natural_language_response))
            print(json.dumps(response.key_insights))
            print("#########################")
            config_business_context_integration = {
                "eval_templates" : "business_context_integration",
                "inputs" : {
                    "response": json.dumps(response.natural_language_response),
                    "pricing_concepts": json.dumps(response.key_insights)
                },
                "model_name" : "turing_large"
            }   
            eval_result5 = evaluator.evaluate(
                **config_business_context_integration, 
                custom_eval_name="business_context_integration", 
                trace_eval=True
            )

            print("#########################")
            print("temporal_logic_handling_eval")
            print(json.dumps(question))
            print(json.dumps(response.sql_query))
            print("#########################")
            config_temporal_logic_handling_eval = {
                "eval_templates" : "temporal_logic_handling_eval",
                "inputs" : {
                    "question": json.dumps(question),
                    "sql_query": json.dumps(response.sql_query),
                },
                "model_name" : "turing_large"
            }
            eval_result6 = evaluator.evaluate(
                **config_temporal_logic_handling_eval, 
                custom_eval_name="temporal_logic_handling_eval", 
                trace_eval=True
            )

            print("#########################")
            print("query_optimization")
            print(json.dumps(response.sql_query))
            print("#########################")
            config_query_optimization = {
                "eval_templates" : "query_optimization_2",
                "inputs" : {
                    "input": json.dumps(response.sql_query),
                },
                "model_name" : "turing_large"
            }
            eval_result7 = evaluator.evaluate(
                **config_query_optimization, 
                custom_eval_name="query_optimization", 
                trace_eval=True
            )

            print("#########################")
            print("multi_step_query_resolution")
            print(json.dumps(response.sql_query))
            print(json.dumps(response.data_table))
            print("#########################")
            config_multi_step_query_resolution = {
                "eval_templates" : "multi_step_query_resolution_3",
                "inputs" : {
                    "sql_query": json.dumps(response.sql_query),
                    "result_data": json.dumps(response.data_table if response.data_table is not None else "[]"),
                },
                "model_name" : "turing_large"
            }
            eval_result8 = evaluator.evaluate(
                **config_multi_step_query_resolution, 
                custom_eval_name="multi_step_query_resolution", 
                trace_eval=True
            )
            


            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Query processing error: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

@app.route('/api/validate-sql', methods=['POST'])
def validate_sql():
    """Validate SQL query without executing it"""
    try:
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 503
        
        data = request.get_json()
        if not data or 'sql_query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing sql_query in request'
            }), 400
        
        sql_query = data['sql_query']
        is_valid, error_message = agent.validate_sql(sql_query)
        
        return jsonify({
            'valid': is_valid,
            'error_message': error_message
        })
        
    except Exception as e:
        logger.error(f"SQL validation error: {str(e)}")
        return jsonify({
            'valid': False,
            'error_message': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get agent performance statistics"""
    try:
        if agent is None:
            return jsonify({
                'error': 'Agent not initialized'
            }), 503
        
        stats = agent.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/schema')
def get_schema():
    """Get database schema information"""
    try:
        if agent is None:
            return jsonify({
                'error': 'Agent not initialized'
            }), 503
        
        table_name = request.args.get('table')
        schema_info = agent.get_schema_info(table_name)
        return jsonify(schema_info)
        
    except Exception as e:
        logger.error(f"Schema error: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    """Clear all caches"""
    try:
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 503
        
        agent.clear_cache()
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully'
        })
        
    except Exception as e:
        logger.error(f"Clear cache error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/examples')
def get_examples():
    """Get example questions by category"""
    examples = {
        'pricing_analysis': [
            "What is the current price for UPC code '0020282000000'?",
            "Show me pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'",
            "What are the factors driving the suggested price for items in price family '7286'?"
        ],
        'elasticity_analysis': [
            "Show me the top 10 items by elasticity in the frozen food category",
            "Which products are candidates for price reductions due to high elasticity?",
            "What items should I decrease the price on to drive units in zone 'Orange'?"
        ],
        'competitive_analysis': [
            "Which items have a CPI value higher than 1.05?",
            "List articles where Walmart prices are higher than No Frills Ontario prices",
            "What is the competitive price index for each subcategory under grocery?"
        ],
        'sales_performance': [
            "Show me the top 10 selling items within frozen food",
            "What are the top 10 items by forecast sales within the bakery category?",
            "Show me revenue by level 2 for the last 6 months in the POKE category"
        ],
        'margin_analysis': [
            "Show me the bottom 10 lowest margin items in April",
            "Show me all items with negative margin in the last 7 days",
            "What is the impact on margin if I create a minimum price gap of 1% on 'C' products?"
        ]
    }
    
    return jsonify(examples)

@app.route('/chat')
def simple_chat():
    """Simple HTML-based chat interface as backup to Gradio"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text-to-SQL Chat</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: rgba(255, 255, 255, 0.95); 
                padding: 30px; 
                border-radius: 20px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                backdrop-filter: blur(10px);
            }
            h1 { color: #2c3e50; text-align: center; margin-bottom: 30px; }
            .chat-container {
                border: 1px solid #ddd;
                border-radius: 10px;
                height: 400px;
                overflow-y: auto;
                padding: 20px;
                background: #f8f9fa;
                margin-bottom: 20px;
            }
            .message {
                margin: 10px 0;
                padding: 10px;
                border-radius: 8px;
            }
            .user-message {
                background: #e3f2fd;
                text-align: right;
            }
            .bot-message {
                background: #f1f8e9;
            }
            .input-container {
                display: flex;
                gap: 10px;
            }
            .question-input {
                flex: 1;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
            }
            .send-button {
                padding: 12px 24px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 500;
            }
            .send-button:hover {
                opacity: 0.8;
            }
            .send-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            .status {
                margin: 10px 0;
                padding: 10px;
                border-radius: 5px;
                text-align: center;
                font-weight: 500;
            }
            .status.loading {
                background: #fff3cd;
                color: #856404;
            }
            .status.error {
                background: #f8d7da;
                color: #721c24;
            }
            .back-link {
                display: inline-block;
                margin-bottom: 20px;
                color: #667eea;
                text-decoration: none;
                font-weight: 500;
            }
            .back-link:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-link">← Back to Main</a>
            <h1>💬 Simple Text-to-SQL Chat</h1>
            
            <div id="status" class="status" style="display: none;"></div>
            
            <div id="chatContainer" class="chat-container">
                <div class="bot-message">
                    <strong>🤖 Assistant:</strong> Hello! I'm your Text-to-SQL assistant. Ask me questions about your retail data.
                    <br><br>
                    <strong>Example questions:</strong>
                    <ul>
                        <li>What is the current price for UPC code '0020282000000'?</li>
                        <li>Show me the top 10 items by elasticity in the frozen food category</li>
                        <li>Which items have a CPI value higher than 1.05?</li>
                    </ul>
                </div>
            </div>
            
            <div class="input-container">
                <input type="text" id="questionInput" class="question-input" 
                    placeholder="Ask a question about your data..." 
                    onkeypress="handleKeyPress(event)">
                <button id="sendButton" class="send-button" onclick="sendQuestion()">Send</button>
            </div>
        </div>

        <script>
            function showStatus(message, type) {
                const status = document.getElementById('status');
                status.textContent = message;
                status.className = 'status ' + type;
                status.style.display = 'block';
                
                if (type !== 'loading') {
                    setTimeout(() => {
                        status.style.display = 'none';
                    }, 3000);
                }
            }
            
            function addMessage(content, isUser) {
                const chatContainer = document.getElementById('chatContainer');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + (isUser ? 'user-message' : 'bot-message');
                
                if (isUser) {
                    messageDiv.innerHTML = '<strong>👤 You:</strong> ' + content;
                } else {
                    messageDiv.innerHTML = '<strong>🤖 Assistant:</strong> ' + content;
                }
                
                chatContainer.appendChild(messageDiv);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            
            async function sendQuestion() {
                const input = document.getElementById('questionInput');
                const button = document.getElementById('sendButton');
                const question = input.value.trim();
                
                if (!question) {
                    showStatus('Please enter a question', 'error');
                    return;
                }
                
                // Add user message
                addMessage(question, true);
                
                // Clear input and disable button
                input.value = '';
                button.disabled = true;
                showStatus('Processing your question...', 'loading');
                
                try {
                    const response = await fetch('/api/query', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            question: question
                        })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        let responseText = data.response;
                        
                        if (data.sql_query) {
                            responseText += '<br><br><strong>SQL Query:</strong><br><code>' + data.sql_query + '</code>';
                        }
                        
                        if (data.key_insights && data.key_insights.length > 0) {
                            responseText += '<br><br><strong>Key Insights:</strong><ul>';
                            data.key_insights.forEach(insight => {
                                responseText += '<li>' + insight + '</li>';
                            });
                            responseText += '</ul>';
                        }
                        
                        addMessage(responseText, false);
                        showStatus('Question processed successfully!', 'success');
                    } else {
                        addMessage('Error: ' + (data.error || data.error_message || 'Unknown error occurred'), false);
                        showStatus('Error processing question', 'error');
                    }
                    
                } catch (error) {
                    addMessage('Error: Failed to send request - ' + error.message, false);
                    showStatus('Connection error', 'error');
                }
                
                // Re-enable button
                button.disabled = false;
                input.focus();
            }
            
            function handleKeyPress(event) {
                if (event.key === 'Enter') {
                    sendQuestion();
                }
            }
            
            // Focus on input when page loads
            document.getElementById('questionInput').focus();
        </script>
    </body>
    </html>
    """)

# Gradio Interface Functions
def process_gradio_query(question: str, history: list) -> tuple:
    """Process query through Gradio interface"""
    try:
        if agent is None:
            error_msg = "❌ Agent not initialized. Please check the system status."
            new_history = history + [[question, error_msg]] if history is not None else [[question, error_msg]]
            return "", new_history, "", "", ""
        
        if not question.strip():
            error_msg = "Please enter a question."
            new_history = history + [[question, error_msg]] if history is not None else [[question, error_msg]]
            return "", new_history, "", "", ""
        
        # Validate question
        is_valid, validation_error = validate_question(question)
        if not is_valid:
            error_msg = f"❌ {validation_error}"
            new_history = history + [[question, error_msg]] if history is not None else [[question, error_msg]]
            return "", new_history, "", "", ""
        
        # Check rate limit
        if not check_rate_limit():
            error_msg = "⏰ Rate limit exceeded. Please wait before asking another question."
            new_history = history + [[question, error_msg]] if history is not None else [[question, error_msg]]
            return "", new_history, "", "", ""
        
        # Process the question
        response = agent.process_question(question)
        
        # Format the response
        if response.success:
            # Main response
            main_response = f"✅ **Answer:** {response.natural_language_response}"
            
            # SQL Query
            sql_display = response.sql_query or "No SQL query generated"
            
            # Data table (if available)
            data_display = response.data_table if response.data_table else "No data returned."
            
            # Key insights
            if response.key_insights:
                insights_display = "\n".join([f"• {insight}" for insight in response.key_insights])
            else:
                insights_display = "No specific insights generated."
            
        else:
            main_response = f"❌ **Error:** {response.error_message}"
            sql_display = response.sql_query if response.sql_query else "No SQL generated due to error."
            data_display = "No data available due to error."
            insights_display = "No insights available due to error."
        
        # Update chat history safely
        if history is None:
            new_history = [[question, main_response]]
        else:
            new_history = history + [[question, main_response]]
        
        return "", new_history, sql_display, data_display, insights_display
        
    except Exception as e:
        error_msg = f"❌ **System Error:** {str(e)}"
        logger.error(f"Gradio query error: {str(e)}")
        new_history = history + [[question, error_msg]] if history is not None else [[question, error_msg]]
        return "", new_history, "", "", ""

def get_example_questions():
    """Get example questions for the interface"""
    return [
        "What is the current price for UPC code '0020282000000'?",
        "Show me the top 10 items by elasticity in the frozen food category",
        "Which items have a CPI value higher than 1.05?",
        "Show me the top 10 selling items within frozen food",
        "Show me all items with negative margin in the last 7 days",
        "What are the pricing strategies for BREAD & WRAPS in Banner 2?",
        "List products where Walmart prices are higher than our prices",
        "Show me revenue by category for the last 6 months"
    ]

def clear_chat():
    """Clear chat history"""
    return [], "", "", "", ""

def get_system_status():
    """Get system status for display"""
    try:
        if agent is None:
            return "❌ Agent not initialized"
        
        health = agent.health_check()
        stats = agent.get_stats()
        
        status_text = f"""
**System Status:** {health['overall_status'].title()}
**Total Queries Processed:** {stats['total_queries']:,}
**Success Rate:** {stats['success_rate']:.1%}
**Average Response Time:** {stats['average_execution_time']:.2f}s
**Database:** SQLite ({stats['sqlite_stats']['total_queries']:,} queries)
**Cache Hit Rate:** {stats['sqlite_stats']['cache_hit_rate']:.1%}
        """.strip()
        
        return status_text
        
    except Exception as e:
        return f"❌ Error getting status: {str(e)}"

# Gradio interface temporarily disabled due to queue compatibility issues
def create_gradio_interface():
    """Create and configure Gradio interface - TEMPORARILY DISABLED"""
    # This function is temporarily disabled to prevent queue errors
    # It will be re-enabled once compatibility issues are resolved
    pass

# def create_gradio_interface():
#     """Create and configure Gradio interface"""
#     
#     with gr.Blocks(
#         title="Text-to-SQL Agent",
#         css="""
#         .gradio-container {
#             max-width: 1200px !important;
#             margin: 0 auto !important;
#         }
#         """
#     ) as interface:
#         
#         # Header
#         gr.Markdown("""
#         # 🏪 Text-to-SQL Agent
#         
#         **AI-powered natural language to SQL conversion for retail analytics**
#         
#         Ask questions about pricing, elasticity, competitive analysis, sales performance, and margin analysis in natural language.
#         The system will convert your questions to SQL queries and provide comprehensive answers with visualizations.
#         """)
#         
#         with gr.Row():
#             with gr.Column(scale=2):
#                 # Chat interface
#                 chatbot = gr.Chatbot(
#                     label="💬 Chat with the Agent",
#                     height=400,
#                     show_label=True,
#                     container=True
#                 )
#                 
#                 with gr.Row():
#                     question_input = gr.Textbox(
#                         label="Ask a question",
#                         placeholder="e.g., What is the current price for UPC code '0020282000000'?",
#                         lines=2,
#                         scale=4,
#                         container=True
#                     )
#                     submit_btn = gr.Button("Submit", variant="primary", scale=1)
#                 
#                 with gr.Row():
#                     clear_btn = gr.Button("Clear Chat", variant="secondary")
#                     example_btn = gr.Dropdown(
#                         choices=get_example_questions(),
#                         label="Example Questions",
#                         value=None,
#                         container=True
#                     )
#             
#             with gr.Column(scale=1):
#                 # System status
#                 status_display = gr.Markdown(
#                     value=get_system_status(),
#                     label="📊 System Status",
#                     container=True
#                 )
#                 
#                 refresh_status_btn = gr.Button("Refresh Status", variant="secondary")
#         
#         # Output sections
#         with gr.Row():
#             with gr.Column():
#                 sql_output = gr.Code(
#                     label="🔍 Generated SQL Query",
#                     language="sql",
#                     lines=8,
#                     container=True
#                 )
#             
#             with gr.Column():
#                 insights_output = gr.Markdown(
#                     label="💡 Key Insights",
#                     value="Key insights will appear here after processing a query.",
#                     container=True
#                 )
#         
#         # Data table output
#         data_output = gr.HTML(
#             label="📊 Query Results",
#             value="<p>Query results will appear here after processing a question.</p>",
#             container=True
#         )
#         
#         # Event handlers
#         def submit_question(question, history):
#             return process_gradio_query(question, history)
#         
#         def use_example(example):
#             return example if example else ""
#         
#         # Wire up the interface
#         submit_btn.click(
#             fn=submit_question,
#             inputs=[question_input, chatbot],
#             outputs=[question_input, chatbot, sql_output, data_output, insights_output]
#         )
#         
#         question_input.submit(
#             fn=submit_question,
#             inputs=[question_input, chatbot],
#             outputs=[question_input, chatbot, sql_output, data_output, insights_output]
#         )
#         
#         clear_btn.click(
#             fn=clear_chat,
#             outputs=[chatbot, sql_output, data_output, insights_output, question_input]
#         )
#         
#         example_btn.change(
#             fn=use_example,
#             inputs=[example_btn],
#             outputs=[question_input]
#         )
#         
#         refresh_status_btn.click(
#             fn=get_system_status,
#             outputs=[status_display]
#         )
#     
#     return interface

def run_gradio_interface():
    """Run Gradio interface in a separate thread - TEMPORARILY DISABLED"""
    logger.info("Gradio interface is temporarily disabled due to queue compatibility issues")
    logger.info("Please use the Simple Chat interface at http://localhost:6001/chat")
    
    # Gradio is temporarily disabled to prevent queue errors
    # This will be re-enabled once the compatibility issues are resolved
    
    # try:
    #     logger.info("Creating Gradio interface...")
    #     interface = create_gradio_interface()
    #     
    #     logger.info("Launching Gradio interface...")
    #     interface.queue(max_size=None)  # Initialize queue properly
    #     interface.launch(
    #         server_name=APP_CONFIG['gradio_host'],
    #         server_port=APP_CONFIG['gradio_port'],
    #         share=False,
    #         show_error=True,
    #         quiet=True,
    #         inbrowser=False,
    #         prevent_thread_lock=True
    #     )
    # except Exception as e:
    #     logger.error(f"Error running Gradio interface: {str(e)}")
    #     logger.error("Gradio interface failed to start. Only Flask API will be available.")
    #     logger.info("You can still access the Flask API at http://localhost:6001")

def main():
    """Main application entry point"""
    logger.info("Starting Text-to-SQL Agent...")
    
    # Check for OpenAI API key
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.warning("=" * 60)
        logger.warning("OPENAI_API_KEY environment variable not set!")
        logger.warning("The system will run in FALLBACK MODE with limited functionality.")
        logger.warning("")
        logger.warning("To enable full AI features, set your OpenAI API key:")
        logger.warning("export OPENAI_API_KEY='your-api-key-here'")
        logger.warning("=" * 60)
    
    # Initialize the agent
    if not initialize_agent():
        logger.error("Failed to initialize agent completely. Exiting.")
        return
    
    # Gradio interface is temporarily disabled
    gradio_enabled = False
    logger.info("Gradio interface is temporarily disabled to prevent queue errors")
    
    # This will be re-enabled once compatibility issues are resolved:
    # try:
    #     gradio_thread = threading.Thread(target=run_gradio_interface, daemon=True)
    #     gradio_thread.start()
    #     time.sleep(3)
    #     logger.info("Gradio interface thread started")
    #     gradio_enabled = True
    # except Exception as e:
    #     logger.error(f"Failed to start Gradio thread: {str(e)}")
    #     gradio_enabled = False
    
    # Start Flask app
    logger.info("Starting Flask API server...")
    logger.info("=" * 50)
    logger.info("🚀 Text-to-SQL Agent is running!")
    logger.info(f"📊 Flask API: http://localhost:{APP_CONFIG['flask_port']}")
    
    logger.info(f"💬 Simple Chat Interface: http://localhost:{APP_CONFIG['flask_port']}/chat")
    if gradio_enabled:
        logger.info(f"💬 Gradio Interface: http://localhost:{APP_CONFIG['gradio_port']} (if started successfully)")
    else:
        logger.warning("💬 Gradio Interface: TEMPORARILY DISABLED (queue compatibility issues)")
    
    logger.info(f"🔍 Health Check: http://localhost:{APP_CONFIG['flask_port']}/api/health")
    logger.info(f"📚 API Examples: http://localhost:{APP_CONFIG['flask_port']}/api/examples")
    logger.info("=" * 50)
    
    if not gradio_enabled:
        logger.info("Note: Use the Simple Chat interface for interactive conversations")
        logger.info("Full API functionality is available through Flask endpoints")
    
    try:
        app.run(
            host=APP_CONFIG['flask_host'],
            port=APP_CONFIG['flask_port'],
            debug=APP_CONFIG['enable_debug'],
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")

if __name__ == "__main__":
    main()

