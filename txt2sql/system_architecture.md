# Text-to-SQL Agent System Architecture

## Executive Summary

The Text-to-SQL Agent is a sophisticated natural language processing system designed to democratize access to complex retail analytics data. This system transforms natural language questions about pricing, elasticity, margins, and competitive intelligence into precise SQL queries, executes them against BigQuery data warehouses, and presents results in an intuitive, conversational format.

The architecture follows a multi-stage pipeline approach that ensures accuracy, security, and scalability while maintaining the flexibility to handle diverse retail analytics use cases ranging from simple price lookups to complex competitive analysis and forecasting scenarios.

## System Overview

### Core Architecture Components

The system implements a retrieval-augmented generation (RAG) architecture with the following key components:

**1. Natural Language Processing Layer**
- Question embedding and semantic understanding
- Intent classification and query type detection
- Context extraction and parameter identification

**2. Knowledge Retrieval System**
- Vector store for database schema and metadata
- Contextual information retrieval
- Historical query pattern matching

**3. SQL Generation Engine**
- Large Language Model integration for code generation
- Template-based query construction
- Query validation and optimization

**4. Database Integration Layer**
- BigQuery client and connection management
- Query execution and result processing
- Error handling and retry mechanisms

**5. Response Generation System**
- Natural language result interpretation
- Data visualization and formatting
- Conversational response construction

**6. User Interface Layer**
- Gradio-based web interface
- Chat-like interaction model
- Query history and session management

### Data Flow Architecture

The system follows the architectural pattern shown in the provided diagram:

1. **User Question Input**: Natural language questions are received through the Gradio interface
2. **Question Embedding**: Questions are converted to vector embeddings for semantic search
3. **Context Retrieval**: Relevant database schema, metadata, and examples are retrieved from the vector store
4. **Prompt Construction**: A comprehensive prompt is created combining the question, context, and metadata
5. **SQL Generation**: The LLM generates SQL queries based on the enriched prompt
6. **Query Validation**: Generated queries are validated for syntax and security
7. **Query Execution**: Validated queries are executed against BigQuery
8. **Result Processing**: Query results are processed and formatted
9. **Response Generation**: Natural language responses are generated from the results
10. **User Presentation**: Final responses are presented through the Gradio interface

## Technical Architecture

### Technology Stack

**Backend Framework**: Flask with CORS support for API endpoints
**Web Interface**: Gradio for interactive chat-like experience
**Database**: Google BigQuery for data warehouse operations
**Vector Store**: FAISS or Chroma for embedding storage and retrieval
**LLM Integration**: OpenAI GPT-4 for SQL generation and response formatting
**Embedding Model**: OpenAI text-embedding-ada-002 for semantic search
**Deployment**: Docker containerization with cloud deployment support

### Database Schema Design

Based on the sample questions, the system expects to work with retail analytics tables containing:

**Core Product Tables**:
- Products (UPC codes, descriptions, categories, hierarchies)
- Price families and product groups
- KVI (Key Value Item) classifications

**Pricing Tables**:
- Current retail prices and suggested prices
- Price change history and recommendations
- Competitor pricing data (CP Unit Price)
- Price lock reasons and constraints

**Analytics Tables**:
- Elasticity measurements and confidence scores
- Margin calculations and profit metrics
- Sales forecasts and unit projections
- Revenue and profit impact analyses

**Operational Tables**:
- Zone and banner configurations
- Export logs and approval workflows
- PLG (Price Look-up Group) configurations
- Optimization settings and parameters

### Vector Store Design

The vector store contains embeddings for:

**Schema Information**:
- Table schemas with column descriptions
- Relationship mappings between tables
- Data type specifications and constraints

**Business Context**:
- Domain-specific terminology definitions
- Calculation methodologies for metrics
- Business rule explanations

**Query Examples**:
- Historical successful query patterns
- Question-to-SQL mapping examples
- Common query templates and variations

## Component Specifications

### 1. Question Processing Module

This module handles the initial processing of user questions:

```python
class QuestionProcessor:
    def __init__(self):
        self.embedding_model = OpenAIEmbeddings()
        self.intent_classifier = IntentClassifier()
    
    def process_question(self, question: str) -> ProcessedQuestion:
        # Extract entities, classify intent, generate embeddings
        pass
```

**Responsibilities**:
- Entity extraction (UPC codes, dates, categories, zones)
- Intent classification (pricing query, elasticity analysis, competitive intelligence)
- Question embedding generation for similarity search
- Parameter validation and normalization

### 2. Context Retrieval System

The context retrieval system finds relevant information to enrich SQL generation:

```python
class ContextRetriever:
    def __init__(self, vector_store):
        self.vector_store = vector_store
        self.schema_cache = SchemaCache()
    
    def retrieve_context(self, question_embedding: List[float]) -> Context:
        # Retrieve relevant schema, examples, and metadata
        pass
```

**Responsibilities**:
- Semantic search across schema documentation
- Retrieval of relevant table schemas and relationships
- Historical query pattern matching
- Business context and calculation methodology retrieval

### 3. SQL Generation Engine

The core component that converts natural language to SQL:

```python
class SQLGenerator:
    def __init__(self):
        self.llm_client = OpenAI()
        self.query_validator = QueryValidator()
        self.template_engine = TemplateEngine()
    
    def generate_sql(self, question: str, context: Context) -> GeneratedSQL:
        # Generate SQL using LLM with context
        pass
```

**Responsibilities**:
- Prompt engineering for optimal SQL generation
- Query template selection and customization
- SQL syntax validation and security checking
- Query optimization and performance tuning

### 4. BigQuery Integration

Handles all database operations:

```python
class BigQueryClient:
    def __init__(self, credentials_path: str):
        self.client = bigquery.Client.from_service_account_json(credentials_path)
        self.query_cache = QueryCache()
    
    def execute_query(self, sql: str) -> QueryResult:
        # Execute query with error handling and caching
        pass
```

**Responsibilities**:
- Secure connection management to BigQuery
- Query execution with timeout and retry logic
- Result set processing and formatting
- Query performance monitoring and optimization

### 5. Response Generation System

Converts query results into natural language responses:

```python
class ResponseGenerator:
    def __init__(self):
        self.llm_client = OpenAI()
        self.formatter = ResultFormatter()
    
    def generate_response(self, question: str, results: QueryResult) -> NLResponse:
        # Generate natural language response from results
        pass
```

**Responsibilities**:
- Natural language response generation from structured data
- Data visualization and chart generation when appropriate
- Response formatting for different output types (tables, summaries, insights)
- Error message generation for failed queries

## Security and Compliance

### Data Security Measures

**Query Validation**: All generated SQL queries undergo rigorous validation to prevent SQL injection attacks and unauthorized data access. The system implements a whitelist approach for allowed tables, columns, and operations.

**Access Control**: Integration with existing authentication systems to ensure users can only access data they are authorized to view. Role-based access control (RBAC) restricts query capabilities based on user permissions.

**Data Masking**: Sensitive data elements are automatically masked or redacted in responses based on user access levels and data classification policies.

**Audit Logging**: Comprehensive logging of all queries, results, and user interactions for compliance and security monitoring purposes.

### Privacy Protection

**Data Minimization**: The system only retrieves and processes data necessary to answer specific questions, minimizing exposure of sensitive information.

**Retention Policies**: Query logs and cached results are automatically purged according to configurable retention policies.

**Anonymization**: Personal identifiers in query results are automatically anonymized when not essential for the analysis.

## Performance and Scalability

### Optimization Strategies

**Query Caching**: Frequently executed queries and their results are cached to reduce database load and improve response times. The caching system includes intelligent cache invalidation based on data freshness requirements.

**Connection Pooling**: Database connections are pooled and reused to minimize connection overhead and improve concurrent user support.

**Asynchronous Processing**: Long-running queries are processed asynchronously with progress updates provided to users through the interface.

**Result Pagination**: Large result sets are automatically paginated to prevent memory issues and improve user experience.

### Scalability Architecture

**Horizontal Scaling**: The system is designed to scale horizontally across multiple instances to handle increased user load and query volume.

**Load Balancing**: Request distribution across multiple backend instances ensures optimal resource utilization and fault tolerance.

**Microservices Design**: Core components are designed as loosely coupled microservices that can be scaled independently based on demand patterns.

## Error Handling and Recovery

### Comprehensive Error Management

**SQL Generation Errors**: When the LLM fails to generate valid SQL, the system provides fallback mechanisms including template-based generation and user guidance for query refinement.

**Database Errors**: Connection failures, timeout errors, and query execution errors are handled gracefully with automatic retry mechanisms and user-friendly error messages.

**Data Quality Issues**: The system detects and reports data quality issues such as missing values, inconsistent formats, or unexpected data distributions.

**User Input Validation**: Invalid user inputs are caught early with helpful suggestions for correction and query improvement.

### Recovery Mechanisms

**Automatic Retry**: Transient failures are automatically retried with exponential backoff to handle temporary network or database issues.

**Graceful Degradation**: When advanced features fail, the system falls back to simpler alternatives to maintain basic functionality.

**Circuit Breaker Pattern**: Prevents cascade failures by temporarily disabling failing components while they recover.

## Integration Capabilities

### API Design

The system exposes RESTful APIs for integration with existing systems:

**Query Endpoint**: `/api/v1/query` - Accepts natural language questions and returns structured responses
**Schema Endpoint**: `/api/v1/schema` - Provides database schema information for external integrations
**Health Endpoint**: `/api/v1/health` - System health and status monitoring
**Metrics Endpoint**: `/api/v1/metrics` - Performance and usage metrics for monitoring

### Webhook Support

**Query Completion**: Webhooks notify external systems when long-running queries complete
**Error Notifications**: Critical errors trigger webhook notifications for immediate attention
**Usage Alerts**: Configurable alerts for usage thresholds and performance metrics

## Monitoring and Observability

### Comprehensive Monitoring

**Performance Metrics**: Query execution times, response generation latency, and system resource utilization are continuously monitored.

**Usage Analytics**: User interaction patterns, popular query types, and success rates are tracked for system optimization.

**Error Tracking**: All errors are logged with detailed context for debugging and system improvement.

**Data Quality Monitoring**: Automated checks for data freshness, completeness, and consistency.

### Alerting System

**Performance Alerts**: Notifications when response times exceed acceptable thresholds
**Error Rate Alerts**: Alerts when error rates spike above normal levels
**Capacity Alerts**: Warnings when system resources approach capacity limits
**Data Freshness Alerts**: Notifications when underlying data becomes stale

This comprehensive architecture ensures that the Text-to-SQL Agent provides reliable, secure, and scalable access to complex retail analytics data while maintaining the flexibility to evolve with changing business requirements and technological advances.

