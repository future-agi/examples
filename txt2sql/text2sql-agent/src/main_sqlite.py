"""
Main Application for Text-to-SQL Agent (SQLite Version)

This is the main entry point for the Text-to-SQL Agent using SQLite
instead of BigQuery. It provides both Flask API and Gradio interface.
"""

import os
import sys
import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))

from flask import Flask, request, jsonify
from flask_cors import CORS
import gradio as gr

# Import our SQLite-based components
from models.text2sql_agent_sqlite import Text2SQLAgentSQLite, AgentConfig, create_agent_sqlite
from models.sqlite_client import create_sqlite_client


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global agent instance
agent: Optional[Text2SQLAgentSQLite] = None

# Flask app configuration
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
DATABASE_PATH = "retail_analytics.db"
VECTOR_STORE_PATH = "./chroma_db"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def initialize_agent():
    """Initialize the Text-to-SQL agent with SQLite backend"""
    global agent
    
    try:
        logger.info("Initializing Text-to-SQL Agent with SQLite...")
        
        # Create agent configuration
        config = AgentConfig(
            openai_api_key=OPENAI_API_KEY,
            database_path=DATABASE_PATH,
            vector_store_path=VECTOR_STORE_PATH,
            enable_cache=True,
            max_results=1000,
            enable_visualization=True,
            log_level="INFO"
        )
        
        # Create agent
        agent = Text2SQLAgentSQLite(config)
        
        logger.info("Text-to-SQL Agent initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing agent: {str(e)}")
        return False

# Flask API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if agent is None:
            return jsonify({
                'status': 'unhealthy',
                'message': 'Agent not initialized',
                'timestamp': datetime.now().isoformat()
            }), 503
        
        health_status = agent.health_check()
        
        status_code = 200 if health_status['overall_status'] == 'healthy' else 503
        return jsonify(health_status), status_code
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process a natural language query"""
    try:
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent not initialized'
            }), 503
        
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing question in request'
            }), 400
        
        question = data['question']
        user_context = data.get('user_context', {})
        
        logger.info(f"Processing query: {question}")
        
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

@app.route('/api/stats', methods=['GET'])
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

@app.route('/api/schema', methods=['GET'])
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

@app.route('/api/examples', methods=['GET'])
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

@app.route('/', methods=['GET'])
def index():
    """Main page"""
    return """
    <html>
    <head>
        <title>Text-to-SQL Agent</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; }
            .endpoint { background: #e8f4f8; padding: 10px; margin: 10px 0; border-radius: 3px; }
            .status { color: green; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏪 Text-to-SQL Agent (SQLite)</h1>
            <p>AI-powered natural language to SQL conversion for retail analytics</p>
            <p class="status">✅ System Status: Running with SQLite Backend</p>
        </div>
        
        <div class="section">
            <h2>🚀 Access Points</h2>
            <div class="endpoint">
                <strong>Gradio Chat Interface:</strong> 
                <a href="http://localhost:7860" target="_blank">http://localhost:7860</a>
            </div>
            <div class="endpoint">
                <strong>API Health Check:</strong> 
                <a href="/api/health" target="_blank">/api/health</a>
            </div>
            <div class="endpoint">
                <strong>Example Questions:</strong> 
                <a href="/api/examples" target="_blank">/api/examples</a>
            </div>
            <div class="endpoint">
                <strong>Database Schema:</strong> 
                <a href="/api/schema" target="_blank">/api/schema</a>
            </div>
            <div class="endpoint">
                <strong>Performance Stats:</strong> 
                <a href="/api/stats" target="_blank">/api/stats</a>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Features</h2>
            <ul>
                <li>Natural language to SQL conversion using GPT-4o</li>
                <li>SQLite database with 1.6M+ synthetic retail records</li>
                <li>Pricing, elasticity, competitive, and sales analysis</li>
                <li>Interactive Gradio chat interface</li>
                <li>RESTful API for programmatic access</li>
                <li>Real-time query processing and caching</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>🎯 Sample Questions</h2>
            <ul>
                <li>"What is the current price for UPC code '0020282000000'?"</li>
                <li>"Show me the top 10 items by elasticity in the frozen food category"</li>
                <li>"Which items have a CPI value higher than 1.05?"</li>
                <li>"Show me revenue by category for the last 6 months"</li>
            </ul>
        </div>
    </body>
    </html>
    """

# Gradio Interface Functions
def process_gradio_query(question: str, history: list) -> tuple:
    """Process query through Gradio interface"""
    try:
        if agent is None:
            error_msg = "❌ Agent not initialized. Please check the system status."
            return error_msg, history + [[question, error_msg]], "", "", ""
        
        if not question.strip():
            error_msg = "Please enter a question."
            return error_msg, history + [[question, error_msg]], "", "", ""
        
        # Process the question
        response = agent.process_question(question)
        
        # Format the response
        if response.success:
            # Main response
            main_response = f"✅ **Answer:** {response.natural_language_response}"
            
            # SQL Query
            sql_display = f"```sql\n{response.sql_query}\n```"
            
            # Data table (if available)
            data_display = response.data_table if response.data_table else "No data returned."
            
            # Key insights
            insights_display = "\n".join([f"• {insight}" for insight in response.key_insights])
            if not insights_display:
                insights_display = "No specific insights generated."
            
            # Metadata
            metadata_display = f"""
**Execution Time:** {response.execution_time:.2f} seconds
**Rows Returned:** {response.row_count:,}
**Confidence Score:** {response.confidence_score:.2f}
**Database:** SQLite (Local)
            """.strip()
            
        else:
            main_response = f"❌ **Error:** {response.error_message}"
            sql_display = response.sql_query if response.sql_query else "No SQL generated due to error."
            data_display = "No data available due to error."
            insights_display = "No insights available due to error."
            metadata_display = f"**Error occurred after:** {response.execution_time:.2f} seconds"
        
        # Update chat history
        new_history = history + [[question, main_response]]
        
        return main_response, new_history, sql_display, data_display, insights_display
        
    except Exception as e:
        error_msg = f"❌ **System Error:** {str(e)}"
        logger.error(f"Gradio query error: {str(e)}")
        return error_msg, history + [[question, error_msg]], "", "", ""

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

def create_gradio_interface():
    """Create and configure Gradio interface"""
    
    with gr.Blocks(
        title="Text-to-SQL Agent",
        theme=gr.themes.Soft(),
        css="""
        .gradio-container {
            max-width: 1200px !important;
        }
        .chat-message {
            padding: 10px;
            margin: 5px 0;
            border-radius: 5px;
        }
        """
    ) as interface:
        
        # Header
        gr.Markdown("""
        # 🏪 Text-to-SQL Agent
        
        **AI-powered natural language to SQL conversion for retail analytics**
        
        Ask questions about pricing, elasticity, competitive analysis, sales performance, and margin analysis in natural language.
        The system will convert your questions to SQL queries and provide comprehensive answers with visualizations.
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # Chat interface
                chatbot = gr.Chatbot(
                    label="💬 Chat with the Agent",
                    height=400,
                    show_label=True
                )
                
                with gr.Row():
                    question_input = gr.Textbox(
                        label="Ask a question",
                        placeholder="e.g., What is the current price for UPC code '0020282000000'?",
                        lines=2,
                        scale=4
                    )
                    submit_btn = gr.Button("Submit", variant="primary", scale=1)
                
                with gr.Row():
                    clear_btn = gr.Button("Clear Chat", variant="secondary")
                    example_btn = gr.Dropdown(
                        choices=get_example_questions(),
                        label="Example Questions",
                        value=None
                    )
            
            with gr.Column(scale=1):
                # System status
                status_display = gr.Markdown(
                    value=get_system_status(),
                    label="📊 System Status"
                )
                
                refresh_status_btn = gr.Button("Refresh Status", variant="secondary")
        
        # Output sections
        with gr.Row():
            with gr.Column():
                sql_output = gr.Code(
                    label="🔍 Generated SQL Query",
                    language="sql",
                    lines=8
                )
            
            with gr.Column():
                insights_output = gr.Markdown(
                    label="💡 Key Insights",
                    value="Key insights will appear here after processing a query."
                )
        
        # Data table output
        data_output = gr.HTML(
            label="📊 Query Results",
            value="<p>Query results will appear here after processing a question.</p>"
        )
        
        # Event handlers
        def submit_question(question, history):
            return process_gradio_query(question, history)
        
        def use_example(example):
            return example
        
        # Wire up the interface
        submit_btn.click(
            fn=submit_question,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot, sql_output, data_output, insights_output]
        )
        
        question_input.submit(
            fn=submit_question,
            inputs=[question_input, chatbot],
            outputs=[question_input, chatbot, sql_output, data_output, insights_output]
        )
        
        clear_btn.click(
            fn=clear_chat,
            outputs=[chatbot, sql_output, data_output, insights_output, question_input]
        )
        
        example_btn.change(
            fn=use_example,
            inputs=[example_btn],
            outputs=[question_input]
        )
        
        refresh_status_btn.click(
            fn=get_system_status,
            outputs=[status_display]
        )
    
    return interface

def run_gradio_interface():
    """Run Gradio interface in a separate thread"""
    try:
        interface = create_gradio_interface()
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True,
            quiet=False
        )
    except Exception as e:
        logger.error(f"Error running Gradio interface: {str(e)}")

def main():
    """Main application entry point"""
    logger.info("Starting Text-to-SQL Agent (SQLite Version)...")
    
    # Check for OpenAI API key
    if not OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable not set!")
        logger.info("Please set your OpenAI API key:")
        logger.info("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Initialize the agent
    if not initialize_agent():
        logger.error("Failed to initialize agent. Exiting.")
        return
    
    # Start Gradio interface in a separate thread
    gradio_thread = threading.Thread(target=run_gradio_interface, daemon=True)
    gradio_thread.start()
    
    # Start Flask app
    logger.info("Starting Flask API server...")
    logger.info("=" * 50)
    logger.info("🚀 Text-to-SQL Agent is running!")
    logger.info("📊 Flask API: http://localhost:5000")
    logger.info("💬 Gradio Interface: http://localhost:7860")
    logger.info("🔍 Health Check: http://localhost:5000/api/health")
    logger.info("📚 API Examples: http://localhost:5000/api/examples")
    logger.info("=" * 50)
    
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")

if __name__ == "__main__":
    main()

