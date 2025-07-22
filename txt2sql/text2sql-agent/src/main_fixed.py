"""
Fixed Main Application for Text-to-SQL Agent

This is the main entry point for the fixed Text-to-SQL Agent with
improved error handling, fallback mechanisms, and better user experience.
"""

import os
import sys
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

# Flask imports
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Gradio imports
import gradio as gr

# Local imports
from models.text2sql_agent_fixed import Text2SQLAgentFixed, AgentConfig, create_fixed_agent


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
agent: Optional[Text2SQLAgentFixed] = None

# Application configuration
APP_CONFIG = {
    'flask_host': '0.0.0.0',
    'flask_port': 5050,
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


def initialize_agent() -> Text2SQLAgentFixed:
    """Initialize the Text-to-SQL agent with configuration"""
    try:
        logger.info("Initializing Text-to-SQL Agent...")
        
        # Get OpenAI API key from environment
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.warning("OPENAI_API_KEY not found in environment. Fallback mode will be used.")
        
        # Create agent configuration
        config = AgentConfig(
            openai_api_key=openai_api_key,
            database_path=APP_CONFIG['database_path'],
            vector_store_path=APP_CONFIG['vector_store_path'],
            enable_cache=True,
            max_results=1000,
            enable_visualization=True,
            log_level="INFO",
            fallback_mode=True  # Always enable fallback
        )
        
        # Create agent
        agent = Text2SQLAgentFixed(config)
        
        logger.info("Text-to-SQL Agent initialized successfully")
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}")
        raise


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


# Flask Application
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def index():
    """Main page"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text-to-SQL Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; text-align: center; }
            .status { padding: 15px; margin: 20px 0; border-radius: 5px; }
            .status.healthy { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .status.degraded { background-color: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .status.unhealthy { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .api-link { display: inline-block; margin: 10px; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px; }
            .api-link:hover { background-color: #0056b3; }
            .gradio-link { background-color: #28a745; }
            .gradio-link:hover { background-color: #1e7e34; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏪 Text-to-SQL Agent</h1>
            <p><strong>AI-powered natural language to SQL conversion for retail analytics</strong></p>
            
            <div id="status" class="status">
                <strong>System Status:</strong> <span id="status-text">Checking...</span>
            </div>
            
            <h3>🚀 Access Points</h3>
            <a href="http://localhost:7860" class="api-link gradio-link" target="_blank">💬 Chat Interface (Gradio)</a>
            <a href="/api/health" class="api-link">🔍 Health Check</a>
            <a href="/api/stats" class="api-link">📊 Statistics</a>
            <a href="/api/examples" class="api-link">📚 Examples</a>
            <a href="/api/schema" class="api-link">🗄️ Database Schema</a>
            
            <h3>📋 Sample Questions</h3>
            <ul>
                <li>What is the current price for UPC code '0020282000000'?</li>
                <li>Show me the top 10 items by elasticity in the frozen food category</li>
                <li>Which items have a CPI value higher than 1.05?</li>
                <li>Show me revenue by category for the last 6 months</li>
                <li>What are the pricing strategies for BREAD & WRAPS in Banner 2?</li>
            </ul>
            
            <h3>🔧 API Endpoints</h3>
            <ul>
                <li><code>POST /api/query</code> - Process natural language questions</li>
                <li><code>GET /api/health</code> - System health check</li>
                <li><code>GET /api/stats</code> - Performance statistics</li>
                <li><code>GET /api/examples</code> - Sample questions and responses</li>
                <li><code>GET /api/schema</code> - Database schema information</li>
                <li><code>POST /api/validate-sql</code> - Validate SQL queries</li>
            </ul>
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
        if agent:
            health_status = agent.health_check()
            return jsonify(health_status)
        else:
            return jsonify({
                'overall_status': 'unhealthy',
                'error': 'Agent not initialized',
                'timestamp': datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'overall_status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get agent statistics"""
    try:
        if agent:
            stats = agent.get_stats()
            return jsonify(stats)
        else:
            return jsonify({'error': 'Agent not initialized'}), 500
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/schema')
def get_schema():
    """Get database schema information"""
    try:
        if agent:
            schema_info = agent.get_schema_info()
            return jsonify(schema_info)
        else:
            return jsonify({'error': 'Agent not initialized'}), 500
    except Exception as e:
        logger.error(f"Schema error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/examples')
def get_examples():
    """Get sample questions and responses"""
    examples = [
        {
            "question": "What is the current price for UPC code '0020282000000'?",
            "description": "Get current pricing for a specific product",
            "category": "pricing",
            "difficulty": "easy"
        },
        {
            "question": "Show me the top 10 items by elasticity in the frozen food category",
            "description": "Find products most sensitive to price changes",
            "category": "elasticity",
            "difficulty": "medium"
        },
        {
            "question": "Which items have a CPI value higher than 1.05?",
            "description": "Identify products where competitors have higher prices",
            "category": "competitive_analysis",
            "difficulty": "medium"
        },
        {
            "question": "Show me revenue by category for the last 6 months",
            "description": "Analyze sales performance by product category",
            "category": "sales_analysis",
            "difficulty": "medium"
        },
        {
            "question": "What are the pricing strategies for BREAD & WRAPS in Banner 2?",
            "description": "Review pricing strategies for specific category and banner",
            "category": "pricing_strategy",
            "difficulty": "hard"
        }
    ]
    
    return jsonify({
        'examples': examples,
        'total_count': len(examples),
        'categories': list(set(ex['category'] for ex in examples))
    })

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process natural language query"""
    try:
        # Check rate limit
        if not check_rate_limit():
            return jsonify({
                'success': False,
                'error_message': 'Rate limit exceeded. Please wait before making another request.',
                'response': 'Too many requests. Please try again later.'
            }), 429
        
        # Get request data
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error_message': 'Missing question in request',
                'response': 'Please provide a question in the request body.'
            }), 400
        
        question = data['question']
        user_context = data.get('context', {})
        
        # Validate question
        is_valid, validation_error = validate_question(question)
        if not is_valid:
            return jsonify({
                'success': False,
                'error_message': validation_error,
                'response': f'Invalid question: {validation_error}'
            }), 400
        
        # Process question
        if agent:
            response = agent.process_question(question, user_context)
            
            # Convert response to JSON-serializable format
            response_dict = {
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
            
            return jsonify(response_dict)
        else:
            return jsonify({
                'success': False,
                'error_message': 'Agent not initialized',
                'response': 'System is not ready. Please try again later.'
            }), 500
            
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error_message': str(e),
            'response': f'An error occurred while processing your question: {str(e)}'
        }), 500

@app.route('/api/validate-sql', methods=['POST'])
def validate_sql():
    """Validate SQL query"""
    try:
        data = request.get_json()
        if not data or 'sql' not in data:
            return jsonify({
                'valid': False,
                'error': 'Missing SQL query in request'
            }), 400
        
        sql_query = data['sql']
        
        if agent:
            is_valid, error_message = agent.validate_sql(sql_query)
            return jsonify({
                'valid': is_valid,
                'error': error_message
            })
        else:
            return jsonify({
                'valid': False,
                'error': 'Agent not initialized'
            }), 500
            
    except Exception as e:
        logger.error(f"SQL validation error: {str(e)}")
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 500


# Gradio Interface
def create_gradio_interface():
    """Create Gradio chat interface"""
    
    def process_question_gradio(question: str, history: List[Tuple[str, str]]) -> Tuple[str, List[Tuple[str, str]]]:
        """Process question through Gradio interface"""
        try:
            if not question.strip():
                return "", history
            
            # Validate question
            is_valid, validation_error = validate_question(question)
            if not is_valid:
                error_response = f"❌ {validation_error}"
                history.append((question, error_response))
                return "", history
            
            # Check rate limit
            if not check_rate_limit():
                error_response = "⏰ Rate limit exceeded. Please wait before asking another question."
                history.append((question, error_response))
                return "", history
            
            if agent:
                # Process the question
                response = agent.process_question(question)
                
                # Format response for Gradio
                if response.success:
                    formatted_response = f"""
**🤖 Answer:** {response.natural_language_response}

**📊 Data Summary:** {response.row_count} records found

**⚡ Query Time:** {response.execution_time:.2f} seconds

**🎯 Confidence:** {response.confidence_score:.1%}

**💡 Key Insights:**
{chr(10).join(f"• {insight}" for insight in response.key_insights)}

**🔍 SQL Query:**
```sql
{response.sql_query}
```

**📋 Data Table:**
{response.data_table if response.data_table else "No data to display"}
"""
                else:
                    formatted_response = f"""
**❌ Error:** {response.error_message}

**🔍 SQL Query:**
```sql
{response.sql_query if response.sql_query else "No query generated"}
```

**💡 Suggestion:** Try rephrasing your question or check if the data exists in our database.
"""
                
                history.append((question, formatted_response))
                return "", history
            else:
                error_response = "❌ System not ready. Please try again later."
                history.append((question, error_response))
                return "", history
                
        except Exception as e:
            logger.error(f"Gradio processing error: {str(e)}")
            error_response = f"❌ An error occurred: {str(e)}"
            history.append((question, error_response))
            return "", history
    
    def get_system_status():
        """Get system status for display"""
        try:
            if agent:
                health = agent.health_check()
                stats = agent.get_stats()
                
                status_text = f"""
**System Status:** {health['overall_status'].title()}
**Total Queries Processed:** {stats['total_queries']}
**Success Rate:** {stats['success_rate']:.1%}
**Average Response Time:** {stats['average_execution_time']:.2f}s
**Database:** SQLite ({stats['sqlite_stats']['total_queries']} queries)
**Cache Hit Rate:** {stats['sqlite_stats']['cache_hit_rate']:.1%}
"""
                return status_text
            else:
                return "**System Status:** Not Ready"
        except Exception as e:
            return f"**System Status:** Error - {str(e)}"
    
    def get_example_questions():
        """Get example questions for dropdown"""
        examples = [
            "What is the current price for UPC code '0020282000000'?",
            "Show me the top 10 items by elasticity in the frozen food category",
            "Which items have a CPI value higher than 1.05?",
            "Show me revenue by category for the last 6 months",
            "What are the pricing strategies for BREAD & WRAPS in Banner 2?",
            "Which products have negative margins?",
            "Show me the most elastic products in the dairy category",
            "What is the average price for products in the BEVERAGES category?",
            "Which stores have the highest revenue in the last month?",
            "Show me competitive pricing for Wonder Bread products"
        ]
        return examples
    
    # Create Gradio interface
    with gr.Blocks(
        title="Text-to-SQL Agent",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .chat-message {
            font-size: 14px !important;
        }
        """
    ) as interface:
        
        gr.Markdown("""
        # 🏪 Text-to-SQL Agent
        
        **AI-powered natural language to SQL conversion for retail analytics**
        
        Ask questions about pricing, elasticity, competitive analysis, sales performance, and margin analysis in natural language. 
        The system will convert your questions to SQL queries and provide comprehensive answers with visualizations.
        """)
        
        with gr.Row():
            with gr.Column(scale=3):
                # Chat interface
                chatbot = gr.Chatbot(
                    label="💬 Chat with the Agent",
                    height=400,
                    type="messages"
                )
                
                with gr.Row():
                    question_input = gr.Textbox(
                        label="Ask a question",
                        placeholder="e.g., What is the current price for UPC code '0020282000000'?",
                        scale=4
                    )
                    submit_btn = gr.Button("Submit", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
                    example_dropdown = gr.Dropdown(
                        label="Example Questions",
                        choices=get_example_questions(),
                        value=None,
                        interactive=True
                    )
            
            with gr.Column(scale=1):
                # System status
                status_display = gr.Markdown(
                    value=get_system_status(),
                    label="📊 System Status"
                )
                
                refresh_btn = gr.Button("🔄 Refresh Status", variant="secondary")
                
                # SQL query display
                sql_display = gr.Code(
                    label="🔍 Generated SQL Query",
                    language="sql",
                    interactive=False
                )
                
                # Key insights
                insights_display = gr.Markdown(
                    label="💡 Key Insights",
                    value="Key insights will appear here after processing a query."
                )
        
        # Event handlers
        def submit_question(question, history):
            response_text, updated_history = process_question_gradio(question, history)
            
            # Extract SQL query and insights from the last response
            if updated_history and len(updated_history) > 0:
                last_response = updated_history[-1][1]
                
                # Extract SQL query
                sql_query = ""
                if "```sql" in last_response:
                    sql_start = last_response.find("```sql") + 6
                    sql_end = last_response.find("```", sql_start)
                    if sql_end > sql_start:
                        sql_query = last_response[sql_start:sql_end].strip()
                
                # Extract insights
                insights = "Key insights will appear here after processing a query."
                if "**💡 Key Insights:**" in last_response:
                    insights_start = last_response.find("**💡 Key Insights:**") + 20
                    insights_end = last_response.find("**🔍 SQL Query:**")
                    if insights_end > insights_start:
                        insights = last_response[insights_start:insights_end].strip()
                
                return "", updated_history, sql_query, insights
            
            return "", updated_history, "", "Key insights will appear here after processing a query."
        
        def clear_chat():
            return [], "", ""
        
        def use_example(example):
            return example
        
        def refresh_status():
            return get_system_status()
        
        # Connect event handlers
        submit_btn.click(
            submit_question,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot, sql_display, insights_display]
        )
        
        question_input.submit(
            submit_question,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot, sql_display, insights_display]
        )
        
        clear_btn.click(
            clear_chat,
            outputs=[chatbot, sql_display, insights_display]
        )
        
        example_dropdown.change(
            use_example,
            inputs=[example_dropdown],
            outputs=[question_input]
        )
        
        refresh_btn.click(
            refresh_status,
            outputs=[status_display]
        )
    
    return interface


def run_flask_app():
    """Run Flask application"""
    logger.info("Starting Flask API server...")
    app.run(
        host=APP_CONFIG['flask_host'],
        port=APP_CONFIG['flask_port'],
        debug=APP_CONFIG['enable_debug'],
        threaded=True
    )


def run_gradio_app():
    """Run Gradio application"""
    logger.info("Starting Gradio interface...")
    interface = create_gradio_interface()
    interface.launch(
        server_name=APP_CONFIG['gradio_host'],
        server_port=APP_CONFIG['gradio_port'],
        share=False,
        show_error=True,
        quiet=False
    )


def main():
    """Main application entry point"""
    try:
        logger.info("=" * 50)
        logger.info("🚀 Starting Text-to-SQL Agent")
        logger.info("=" * 50)
        
        # Initialize global agent
        global agent
        agent = initialize_agent()
        
        logger.info("Text-to-SQL Agent initialized successfully")
        
        # Start Flask API server in a separate thread
        flask_thread = threading.Thread(target=run_flask_app, daemon=True)
        flask_thread.start()
        
        # Give Flask a moment to start
        time.sleep(2)
        
        logger.info("Starting Flask API server...")
        logger.info("=" * 50)
        logger.info("🚀 Text-to-SQL Agent is running!")
        logger.info(f"📊 Flask API: http://localhost:{APP_CONFIG['flask_port']}")
        logger.info(f"💬 Gradio Interface: http://localhost:{APP_CONFIG['gradio_port']}")
        logger.info(f"🔍 Health Check: http://localhost:{APP_CONFIG['flask_port']}/api/health")
        logger.info(f"📚 API Examples: http://localhost:{APP_CONFIG['flask_port']}/api/examples")
        logger.info("=" * 50)
        
        # Start Gradio interface (this will block)
        run_gradio_app()
        
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise


if __name__ == "__main__":
    main()

