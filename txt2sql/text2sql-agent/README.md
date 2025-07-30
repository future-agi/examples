# 🏪 Text-to-SQL Agent

A comprehensive AI-powered system that converts natural language questions into SQL queries, executes them against BigQuery, and presents results in natural language format with visualizations.

## 🎯 Overview

The Text-to-SQL Agent is designed specifically for retail analytics, enabling business users to query their data using natural language instead of writing complex SQL queries. The system leverages GPT-4o for intelligent query generation and provides an intuitive chat interface for seamless interaction.

### Key Features

- **🤖 Natural Language Processing**: Convert business questions into optimized SQL queries
- **📊 Intelligent Visualizations**: Automatic chart generation based on query results
- **💬 Chat Interface**: User-friendly Gradio-powered conversational interface
- **🔌 REST API**: Programmatic access for integration with existing systems
- **⚡ High Performance**: Caching and optimization for fast query execution
- **🎯 Retail-Focused**: Pre-trained on retail and pricing analytics use cases
- **📈 Business Insights**: Automated key insights extraction from query results

## 🏗️ Architecture

The system follows the architecture diagram provided, implementing a complete text-to-SQL pipeline:

```
User Question → Question Processing → Context Retrieval → SQL Generation → 
Query Execution → Response Generation → Natural Language Response
```

### Core Components

1. **Question Processor**: Analyzes user intent and extracts entities
2. **Vector Store**: ChromaDB-based knowledge base with schemas and examples
3. **SQL Generator**: GPT-4o powered SQL query generation
4. **BigQuery Client**: Secure query execution with caching
5. **Response Generator**: Natural language response with visualizations
6. **Gradio Interface**: Interactive chat interface
7. **Flask API**: RESTful endpoints for programmatic access

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- OpenAI API key
- Google Cloud BigQuery access (optional for demo)

### Installation

1. **Clone and Setup**
   ```bash
   cd revionics-text2sql-agent
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   export BIGQUERY_DATASET="your-dataset-id"
   ```

3. **Start the Application**
   ```bash
   python src/main.py
   ```

### Access Points

- **Gradio Chat Interface**: http://localhost:7860
- **Flask API**: http://localhost:6001
- **API Health Check**: http://localhost:6001/api/health

## 💻 Usage Examples

### Chat Interface

Ask questions in natural language:

- "What is the current price for UPC code '0020282000000'?"
- "Show me the top 10 items by elasticity in the frozen food category"
- "Which items have a CPI value higher than 1.05?"
- "What are the pricing strategies for BREAD & WRAPS in Banner 2?"

### API Usage

```python
import requests

# Query the API
response = requests.post('http://localhost:6001/api/query', json={
    'question': 'What is the current price for UPC code "123456"?',
    'user_context': {'user_id': 'analyst1'}
})

result = response.json()
print(result['response'])  # Natural language answer
print(result['sql_query'])  # Generated SQL
```

## 📊 Sample Questions by Category

### Pricing Analysis
- "What is the current price for UPC code '0020282000000'?"
- "Show me pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'"
- "What are the factors driving the suggested price for items in price family '7286'?"

### Elasticity Analysis
- "Show me the top 10 items by elasticity in the frozen food category"
- "Which products are candidates for price reductions due to high elasticity?"
- "What items should I decrease the price on to drive units in zone 'Orange'?"

### Competitive Analysis
- "Which items have a CPI value higher than 1.05?"
- "List articles where Walmart prices are higher than No Frills Ontario prices"
- "What is the competitive price index for each subcategory under grocery?"

### Sales & Performance
- "Show me the top 10 selling items within frozen food"
- "What are the top 10 items by forecast sales within the bakery category?"
- "Show me revenue by level 2 for the last 6 months in the POKE category"

### Margin Analysis
- "Show me the bottom 10 lowest margin items in April"
- "Show me all items with negative margin in the last 7 days"
- "What is the impact on margin if I create a minimum price gap of 1% on 'C' products?"

## 🔧 Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# BigQuery Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
BIGQUERY_DATASET=your-dataset-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json

# Optional
VECTOR_STORE_PATH=./chroma_db
ENABLE_CACHE=true
MAX_RESULTS=1000
LOG_LEVEL=INFO
```

### BigQuery Setup

1. Create a Google Cloud project
2. Enable BigQuery API
3. Create a service account with BigQuery permissions
4. Download credentials JSON file
5. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## 📚 API Documentation

### Endpoints

#### POST /api/query
Process a natural language query

**Request:**
```json
{
    "question": "What is the current price for UPC code '123456'?",
    "user_context": {
        "user_id": "analyst1",
        "preferences": {}
    }
}
```

**Response:**
```json
{
    "success": true,
    "response": "The current price for UPC code '123456' is $12.99.",
    "sql_query": "SELECT current_price FROM pricing WHERE upc_code = '123456'",
    "data_table": "<table>...</table>",
    "visualization": "base64_encoded_image",
    "key_insights": ["Price is within normal range"],
    "execution_time": 2.5,
    "row_count": 1,
    "confidence_score": 0.95
}
```

#### GET /api/health
System health check

#### GET /api/stats
Performance statistics

#### GET /api/examples
Example questions by category

#### POST /api/validate-sql
Validate SQL query without execution

## 🎨 User Interface

### Gradio Chat Interface

The Gradio interface provides:

- **Conversational Chat**: Natural language interaction
- **Example Questions**: Pre-built queries by category
- **Multiple Output Formats**: 
  - Generated SQL queries
  - Data tables with formatting
  - Key insights extraction
  - Automatic visualizations
- **System Monitoring**: Health status and performance metrics
- **Cache Management**: Clear cache functionality

### Interface Features

- **Responsive Design**: Works on desktop and mobile
- **Real-time Processing**: Live query execution
- **Error Handling**: User-friendly error messages
- **Export Options**: Download results and visualizations
- **Query History**: Track previous questions and responses

## 🔍 System Monitoring

### Health Checks

Monitor system components:
- OpenAI API connectivity
- BigQuery connection status
- Vector store availability
- Overall system health

### Performance Metrics

Track key performance indicators:
- Query success rate
- Average execution time
- Cache hit rate
- Total queries processed

### Logging

Comprehensive logging for:
- Query processing steps
- Error tracking
- Performance monitoring
- User interactions

## 🛠️ Development

### Project Structure

```
revionics-text2sql-agent/
├── src/
│   ├── models/
│   │   ├── text2sql_agent.py      # Main agent orchestrator
│   │   ├── query_processor.py     # Question processing
│   │   ├── sql_generator.py       # SQL generation with GPT-4o
│   │   ├── vector_store.py        # ChromaDB knowledge base
│   │   ├── bigquery_client.py     # BigQuery integration
│   │   └── response_generator.py  # Natural language responses
│   ├── routes/
│   │   └── api.py                 # Flask API endpoints
│   ├── gradio_interface.py        # Gradio chat interface
│   └── main.py                    # Application entry point
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── test_results.md               # Test documentation
```

### Adding New Features

1. **New Question Types**: Add examples to vector store
2. **Custom Visualizations**: Extend `DataVisualizer` class
3. **Additional APIs**: Add endpoints to `api.py`
4. **UI Enhancements**: Modify `gradio_interface.py`

### Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 🚀 Deployment

### Local Development
```bash
python src/main.py
```

### Production Deployment

1. **Docker Deployment**
   ```bash
   docker build -t revionics-text2sql .
   docker run -p 6001:6001 -p 7860:7860 revionics-text2sql
   ```

2. **Cloud Deployment**
   - Deploy to Google Cloud Run
   - Use Kubernetes for scaling
   - Configure load balancing

### Environment Setup

Ensure all environment variables are configured:
- OpenAI API credentials
- BigQuery project settings
- Vector store persistence
- Logging configuration

## 🔒 Security

### API Security
- Input validation and sanitization
- SQL injection prevention
- Rate limiting
- Authentication (when configured)

### Data Privacy
- No sensitive data logging
- Secure credential handling
- Query result caching controls
- User session management

## 📈 Performance Optimization

### Caching Strategy
- Query result caching
- Vector similarity caching
- Schema metadata caching
- Response template caching

### Query Optimization
- SQL query validation
- Execution plan analysis
- Result set limiting
- Parallel processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is proprietary to Revionics. All rights reserved.

## 🆘 Support

For support and questions:
- Check the test results in `test_results.md`
- Review API documentation
- Contact the development team

## 🎉 Acknowledgments

- Built with GPT-4o for intelligent SQL generation
- Powered by Google BigQuery for scalable analytics
- Uses ChromaDB for efficient vector storage
- Gradio for user-friendly interfaces
- Flask for robust API development

---

**Text-to-SQL Agent** - Transforming retail analytics through natural language processing.

