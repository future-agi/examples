import os
import sys
from datetime import datetime, timezone
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import threading

# Import trading system components
from config.settings import config
from src.models.trading import db
from src.integrations.openai.client import OpenAIClient
from src.integrations.market_data.data_provider import market_data_manager
from src.integrations.news.news_provider import news_data_manager
from src.knowledge.knowledge_base import KnowledgeManager
from src.orchestration.orchestrator import TradingOrchestrator
from src.utils.logging import get_component_logger

logger = get_component_logger("main")

# Initialize Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Configuration from settings
app.config['SECRET_KEY'] = config.flask_secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = config.database.database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes
CORS(app, origins="*")

# Initialize database
db.init_app(app)

# Global components
openai_client = None
knowledge_manager = None
trading_orchestrator = None
event_loop = None
loop_thread = None


def create_event_loop():
    """Create and run event loop in separate thread"""
    global event_loop
    event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(event_loop)
    event_loop.run_forever()


def run_async(coro):
    """Run async function in the event loop"""
    if event_loop is None:
        return None
    
    future = asyncio.run_coroutine_threadsafe(coro, event_loop)
    return future.result(timeout=30)  # 30 second timeout


def initialize_system():
    """Initialize the trading system components"""
    global openai_client, knowledge_manager, trading_orchestrator, loop_thread
    
    try:
        logger.info("Initializing AI Trading System...")
        
        # Create database tables
        with app.app_context():
            db.create_all()
        
        # Start event loop in separate thread
        loop_thread = threading.Thread(target=create_event_loop, daemon=True)
        loop_thread.start()
        
        # Wait for event loop to be ready
        import time
        time.sleep(1)
        
        # Initialize OpenAI client
        openai_client = OpenAIClient()
        
        # Initialize knowledge manager
        knowledge_manager = KnowledgeManager(openai_client)
        
        # Initialize default knowledge
        run_async(knowledge_manager.initialize_default_knowledge())
        
        # Initialize trading orchestrator
        trading_orchestrator = TradingOrchestrator(
            market_data_manager,
            news_data_manager,
            knowledge_manager
        )
        
        # Start orchestrator
        run_async(trading_orchestrator.start())
        
        logger.info("AI Trading System initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {e}")
        # Don't raise to allow Flask to start even if some components fail


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve static files"""
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return jsonify({
            "message": "AI Trading System API",
            "version": "1.0.0",
            "status": "running",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "endpoints": {
                "health": "/health",
                "analyze": "/api/analyze/<symbol>",
                "market_data": "/api/market-data/<symbol>",
                "news": "/api/news/<symbol>",
                "sentiment": "/api/sentiment/<symbol>",
                "knowledge_search": "/api/knowledge/search",
                "knowledge_ask": "/api/knowledge/ask",
                "orchestrator_status": "/api/orchestrator/status"
            }
        })

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return jsonify({
                "message": "AI Trading System API",
                "version": "1.0.0",
                "status": "running",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        status = {
            "status": "healthy",
            "service": "ai-trading-system",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "database": "healthy",
                "openai_client": "healthy" if openai_client else "not_initialized",
                "knowledge_manager": "healthy" if knowledge_manager else "not_initialized",
                "trading_orchestrator": "healthy" if trading_orchestrator else "not_initialized"
            }
        }
        
        # Check orchestrator status
        if trading_orchestrator:
            orchestrator_status = trading_orchestrator.get_status()
            status["components"]["orchestrator_details"] = orchestrator_status
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500


@app.route('/api/analyze/<symbol>')
def analyze_symbol(symbol):
    """Analyze a stock symbol"""
    try:
        if not trading_orchestrator:
            return jsonify({
                "status": "error",
                "error": "Trading orchestrator not initialized"
            }), 500
        
        symbol = symbol.upper()
        
        # Get priority from query params
        priority = request.args.get('priority', 5, type=int)
        sync = request.args.get('sync', 'false').lower() == 'true'
        
        if sync:
            # Synchronous analysis
            result = run_async(trading_orchestrator.analyze_symbol_sync(symbol))
            return jsonify({
                "status": "completed",
                "result": result.to_dict() if result else None
            })
        else:
            # Asynchronous analysis
            task_id = run_async(trading_orchestrator.analyze_symbol(symbol, priority))
            return jsonify({
                "status": "queued",
                "task_id": task_id,
                "symbol": symbol,
                "check_url": f"/api/analysis/{task_id}"
            })
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/analysis/<task_id>')
def get_analysis_result(task_id):
    """Get analysis result by task ID"""
    try:
        if not trading_orchestrator:
            return jsonify({
                "status": "error",
                "error": "Trading orchestrator not initialized"
            }), 500
        
        result = run_async(trading_orchestrator.get_analysis_result(task_id))
        
        if result is None:
            return jsonify({
                "status": "pending",
                "task_id": task_id
            })
        
        return jsonify({
            "status": "completed",
            "result": result.to_dict() if hasattr(result, 'to_dict') else result
        })
        
    except Exception as e:
        logger.error(f"Error getting analysis result {task_id}: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/market-data/<symbol>')
def get_market_data(symbol):
    """Get market data for a symbol"""
    try:
        symbol = symbol.upper()
        
        # Get parameters
        interval = request.args.get('interval', '1d')
        range_period = request.args.get('range', '1mo')
        
        # Get market data
        market_context = run_async(market_data_manager.get_market_context(symbol))
        
        return jsonify({
            "status": "success",
            "symbol": symbol,
            "data": market_context
        })
        
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/news/<symbol>')
def get_news(symbol):
    """Get news for a symbol"""
    try:
        symbol = symbol.upper()
        limit = request.args.get('limit', 10, type=int)
        
        # Get news articles
        articles = run_async(news_data_manager.get_news_for_symbol(symbol, limit))
        
        return jsonify({
            "status": "success",
            "symbol": symbol,
            "articles": [article.to_dict() for article in articles]
        })
        
    except Exception as e:
        logger.error(f"Error getting news for {symbol}: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/sentiment/<symbol>')
def get_sentiment(symbol):
    """Get sentiment analysis for a symbol"""
    try:
        symbol = symbol.upper()
        
        # Get sentiment summary
        sentiment_summary = run_async(news_data_manager.get_sentiment_summary(symbol))
        
        return jsonify({
            "status": "success",
            "symbol": symbol,
            "sentiment": sentiment_summary
        })
        
    except Exception as e:
        logger.error(f"Error getting sentiment for {symbol}: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/knowledge/search')
def search_knowledge():
    """Search the knowledge base"""
    try:
        if not knowledge_manager:
            return jsonify({
                "status": "error",
                "error": "Knowledge manager not initialized"
            }), 500
        
        query = request.args.get('query', '')
        symbols = request.args.getlist('symbols')
        document_types = request.args.getlist('types')
        
        if not query:
            return jsonify({
                "status": "error",
                "error": "Query parameter is required"
            }), 400
        
        # Search knowledge base
        results = run_async(knowledge_manager.search(
            query, 
            symbols=symbols if symbols else None,
            document_types=document_types if document_types else None
        ))
        
        return jsonify({
            "status": "success",
            "query": query,
            "results": [result.to_dict() for result in results]
        })
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/knowledge/ask', methods=['POST'])
def ask_knowledge():
    """Ask a question using RAG system"""
    try:
        if not knowledge_manager:
            return jsonify({
                "status": "error",
                "error": "Knowledge manager not initialized"
            }), 500
        
        data = request.get_json()
        
        if not data or 'question' not in data:
            return jsonify({
                "status": "error",
                "error": "Question is required in request body"
            }), 400
        
        question = data['question']
        symbols = data.get('symbols', [])
        document_types = data.get('document_types', [])
        
        # Generate response with context
        response = run_async(knowledge_manager.generate_with_context(
            question,
            symbols=symbols if symbols else None,
            document_types=document_types if document_types else None
        ))
        
        return jsonify({
            "status": "success",
            "question": question,
            "response": response
        })
        
    except Exception as e:
        logger.error(f"Error asking knowledge base: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/knowledge/documents')
def get_documents():
    """Get all documents in knowledge base"""
    try:
        if not knowledge_manager:
            return jsonify({
                "status": "error",
                "error": "Knowledge manager not initialized"
            }), 500
        
        documents = knowledge_manager.get_all_documents()
        
        return jsonify({
            "status": "success",
            "documents": [doc.to_dict() for doc in documents],
            "count": len(documents)
        })
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/knowledge/stats')
def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        if not knowledge_manager:
            return jsonify({
                "status": "error",
                "error": "Knowledge manager not initialized"
            }), 500
        
        stats = knowledge_manager.get_statistics()
        
        return jsonify({
            "status": "success",
            "statistics": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting knowledge stats: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/orchestrator/status')
def get_orchestrator_status():
    """Get orchestrator status"""
    try:
        if not trading_orchestrator:
            return jsonify({
                "status": "error",
                "error": "Orchestrator not initialized"
            }), 500
        
        status = trading_orchestrator.get_status()
        
        return jsonify({
            "status": "success",
            "orchestrator": status
        })
        
    except Exception as e:
        logger.error(f"Error getting orchestrator status: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/orchestrator/cache')
def get_cached_analyses():
    """Get cached analysis symbols"""
    try:
        if not trading_orchestrator:
            return jsonify({
                "status": "error",
                "error": "Orchestrator not initialized"
            }), 500
        
        cached_symbols = trading_orchestrator.get_cached_symbols()
        
        return jsonify({
            "status": "success",
            "cached_symbols": cached_symbols,
            "count": len(cached_symbols)
        })
        
    except Exception as e:
        logger.error(f"Error getting cached analyses: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/orchestrator/cache', methods=['DELETE'])
def clear_cache():
    """Clear analysis cache"""
    try:
        if not trading_orchestrator:
            return jsonify({
                "status": "error",
                "error": "Orchestrator not initialized"
            }), 500
        
        run_async(trading_orchestrator.clear_cache())
        
        return jsonify({
            "status": "success",
            "message": "Cache cleared"
        })
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.route('/api/supported-symbols')
def get_supported_symbols():
    """Get list of supported symbols"""
    try:
        symbols = market_data_manager.get_supported_symbols()
        
        return jsonify({
            "status": "success",
            "symbols": symbols,
            "count": len(symbols)
        })
        
    except Exception as e:
        logger.error(f"Error getting supported symbols: {e}")
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "error": "Endpoint not found",
        "message": "The requested endpoint does not exist"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "status": "error",
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500


if __name__ == '__main__':
    # Initialize the trading system
    with app.app_context():
        initialize_system()
    
    # Run the Flask app
    app.run(
        host=config.flask_host,
        port=config.flask_port,
        debug=config.debug,
        threaded=True
    )

