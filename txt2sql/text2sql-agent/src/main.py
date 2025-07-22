import os
import sys
import threading
import logging
from flask import Flask, send_from_directory
from flask_cors import CORS

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import db
from src.routes.user import user_bp
from src.routes.api import api_bp
from src.gradio_interface import create_gradio_interface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app, origins="*")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(api_bp)  # Text-to-SQL API routes

# Database configuration (keep existing)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Global variable for Gradio interface
gradio_interface = None

def start_gradio():
    """Start Gradio interface in a separate thread"""
    global gradio_interface
    try:
        logger.info("Starting Gradio interface...")
        gradio_interface = create_gradio_interface()
        
        # Launch Gradio on a different port
        gradio_interface.launch(
            server_name='0.0.0.0',
            server_port=7860,
            share=False,
            debug=False,
            show_error=True,
            prevent_thread_lock=True  # Important for running in thread
        )
        logger.info("Gradio interface started on port 7860")
    except Exception as e:
        logger.error(f"Error starting Gradio interface: {str(e)}")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files and handle SPA routing"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            # Return a simple HTML page with links to the services
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Text-to-SQL Agent</title>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        max-width: 800px; 
                        margin: 50px auto; 
                        padding: 20px;
                        background-color: #f5f5f5;
                    }
                    .container {
                        background: white;
                        padding: 30px;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }
                    h1 { 
                        color: #2c3e50; 
                        text-align: center;
                        margin-bottom: 30px;
                    }
                    .service-card {
                        border: 1px solid #ddd;
                        border-radius: 8px;
                        padding: 20px;
                        margin: 20px 0;
                        background: #f8f9fa;
                    }
                    .service-card h3 {
                        color: #34495e;
                        margin-top: 0;
                    }
                    .btn {
                        display: inline-block;
                        padding: 10px 20px;
                        background: #3498db;
                        color: white;
                        text-decoration: none;
                        border-radius: 5px;
                        margin: 5px;
                    }
                    .btn:hover {
                        background: #2980b9;
                    }
                    .api-btn {
                        background: #27ae60;
                    }
                    .api-btn:hover {
                        background: #229954;
                    }
                    .status {
                        color: #27ae60;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🏪 Text-to-SQL Agent</h1>
                    
                    <div class="service-card">
                        <h3>📊 Interactive Chat Interface</h3>
                        <p>Use the Gradio-powered chat interface to ask questions about your retail data in natural language.</p>
                        <p><strong>Features:</strong> Real-time chat, SQL query generation, data visualization, and insights</p>
                        <a href="http://localhost:7860" target="_blank" class="btn">Open Chat Interface</a>
                    </div>
                    
                    <div class="service-card">
                        <h3>🔌 REST API</h3>
                        <p>Integrate the text-to-SQL functionality into your applications using our REST API.</p>
                        <p><strong>Endpoints:</strong> /api/query, /api/health, /api/stats, /api/schema</p>
                        <a href="/api/health" target="_blank" class="btn api-btn">Health Check</a>
                        <a href="/api/stats" target="_blank" class="btn api-btn">Statistics</a>
                        <a href="/api/examples" target="_blank" class="btn api-btn">Examples</a>
                    </div>
                    
                    <div class="service-card">
                        <h3>📚 Documentation</h3>
                        <p>Learn how to use the system effectively with example questions and API documentation.</p>
                        <ul>
                            <li><strong>Pricing Analysis:</strong> "What is the current price for UPC code '123456'?"</li>
                            <li><strong>Elasticity Analysis:</strong> "Show me the top 10 items by elasticity"</li>
                            <li><strong>Competitive Analysis:</strong> "Which items have a CPI value higher than 1.05?"</li>
                            <li><strong>Sales Performance:</strong> "Show me the top selling items in frozen food"</li>
                        </ul>
                    </div>
                    
                    <div class="service-card">
                        <h3>⚙️ System Status</h3>
                        <p>Both services are running:</p>
                        <ul>
                            <li>Flask API Server: <span class="status">✅ Running on port 5000</span></li>
                            <li>Gradio Interface: <span class="status">✅ Running on port 7860</span></li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """, 200

@app.route('/gradio')
def gradio_redirect():
    """Redirect to Gradio interface"""
    return """
    <script>
        window.location.href = 'http://localhost:7860';
    </script>
    <p>Redirecting to Gradio interface... <a href="http://localhost:7860">Click here if not redirected</a></p>
    """

if __name__ == '__main__':
    # Start Gradio interface in a separate thread
    gradio_thread = threading.Thread(target=start_gradio, daemon=True)
    gradio_thread.start()
    
    logger.info("Starting Flask application...")
    logger.info("Flask API will be available at: http://localhost:5000")
    logger.info("Gradio interface will be available at: http://localhost:7860")
    
    # Start Flask application
    app.run(host='0.0.0.0', port=5000, debug=False)  # Set debug=False to avoid issues with threading

