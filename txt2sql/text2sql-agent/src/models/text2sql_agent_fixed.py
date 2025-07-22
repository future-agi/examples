"""
Fixed Text-to-SQL Agent for (SQLite Version)

This module provides a robust text-to-SQL solution with improved error handling,
fallback mechanisms, and better OpenAI API integration.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import time
from datetime import datetime

from .query_processor import QuestionProcessor, ProcessedQuestion
from .sql_generator import SQLGenerator, QueryContext, GeneratedSQL
from .sql_generator_fallback import FallbackSQLGenerator, FallbackQueryContext, create_fallback_sql_generator
from .vector_store_fixed import VectorStoreFixed, ContextRetrieverFixed, SchemaLoaderFixed
from .sqlite_client import SQLiteClient, QueryResult, create_sqlite_client
from .response_generator import ResponseGenerator, ResponseContext, GeneratedResponse


@dataclass
class AgentConfig:
    """Configuration for the Text-to-SQL agent"""
    openai_api_key: Optional[str] = None
    database_path: str = "retail_analytics.db"
    vector_store_path: str = "./chroma_db"
    enable_cache: bool = True
    max_results: int = 1000
    enable_visualization: bool = True
    log_level: str = "INFO"
    fallback_mode: bool = True  # Enable fallback when OpenAI fails


@dataclass
class AgentResponse:
    """Complete response from the Text-to-SQL agent"""
    success: bool
    natural_language_response: str
    sql_query: str
    data_table: Optional[str]
    visualization: Optional[str]
    key_insights: List[str]
    execution_time: float
    row_count: int
    confidence_score: float
    error_message: Optional[str]
    metadata: Dict[str, Any]


class Text2SQLAgentFixed:
    """Fixed Text-to-SQL Agent class with improved error handling"""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Text-to-SQL Agent
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize components with error handling
        self.question_processor = QuestionProcessor()
        
        # Initialize SQL generator with fallback
        try:
            self.sql_generator = SQLGenerator(api_key=config.openai_api_key)
            self.openai_available = True
        except Exception as e:
            self.logger.warning(f"OpenAI initialization failed: {str(e)}")
            self.sql_generator = None
            self.openai_available = False
        
        # Initialize fallback SQL generator
        self.fallback_sql_generator = create_fallback_sql_generator()
        
        # Initialize vector store with proper directory creation
        self._ensure_vector_store_directory()
        self.vector_store = VectorStoreFixed(persist_directory=config.vector_store_path)
        self.context_retriever = ContextRetrieverFixed(self.vector_store)
        
        # Initialize SQLite client
        self.sqlite_client = create_sqlite_client(
            database_path=config.database_path,
            enable_cache=config.enable_cache,
            max_results=config.max_results
        )
        
        # Initialize response generator with fallback
        try:
            self.response_generator = ResponseGenerator(api_key=config.openai_api_key)
        except Exception as e:
            self.logger.warning(f"Response generator initialization failed: {str(e)}")
            self.response_generator = None
        
        # Initialize schemas and examples
        self._initialize_knowledge_base()
        
        # Track agent metrics
        self.query_count = 0
        self.successful_queries = 0
        self.total_execution_time = 0.0
        self.fallback_queries = 0
        
        self.logger.info("Text-to-SQL Agent (Fixed) initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _ensure_vector_store_directory(self):
        """Ensure vector store directory exists"""
        try:
            if not os.path.exists(self.config.vector_store_path):
                os.makedirs(self.config.vector_store_path)
                self.logger.info(f"Created vector store directory: {self.config.vector_store_path}")
        except Exception as e:
            self.logger.error(f"Error creating vector store directory: {str(e)}")
            # Use a fallback directory
            self.config.vector_store_path = "./chroma_db_fallback"
            if not os.path.exists(self.config.vector_store_path):
                os.makedirs(self.config.vector_store_path)
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with schemas and examples"""
        try:
            # Check if knowledge base is already populated
            stats = self.vector_store.get_collection_stats()
            
            if stats.get('schemas', 0) == 0:
                self.logger.info("Initializing knowledge base...")
                schema_loader = SchemaLoaderFixed(self.vector_store)
                
                # Load retail schemas
                schema_loader.load_retail_schemas()
                schema_loader.load_sample_examples()
                schema_loader.load_business_rules()
                
                self.logger.info("Knowledge base initialized")
            else:
                self.logger.info(f"Knowledge base already populated: {stats}")
                
        except Exception as e:
            self.logger.error(f"Error initializing knowledge base: {str(e)}")
            # Continue without knowledge base for basic functionality
    
    def _generate_fallback_sql(self, question: str, context: Any) -> str:
        """Generate fallback SQL when OpenAI is not available"""
        question_lower = question.lower()
        
        # Simple pattern matching for common queries
        if "current price" in question_lower and "upc" in question_lower:
            # Extract UPC code if possible
            import re
            upc_match = re.search(r"['\"]([0-9]+)['\"]", question)
            if upc_match:
                upc_code = upc_match.group(1)
                return f"""
                SELECT p.product_name, pr.current_price, pr.price_date
                FROM products p 
                JOIN pricing pr ON p.upc_code = pr.upc_code 
                WHERE p.upc_code = '{upc_code}' 
                ORDER BY pr.price_date DESC 
                LIMIT 1
                """
        
        elif "top" in question_lower and "elasticity" in question_lower:
            # Extract category if possible
            category_patterns = ["frozen food", "dairy", "bread", "beverages", "snacks"]
            category = None
            for pattern in category_patterns:
                if pattern in question_lower:
                    category = pattern.upper().replace(" ", " ")
                    break
            
            if category:
                return f"""
                SELECT p.product_name, e.elasticity_value, p.category_level_2
                FROM products p 
                JOIN elasticity e ON p.upc_code = e.upc_code 
                WHERE p.category_level_2 LIKE '%{category}%'
                ORDER BY e.elasticity_value DESC 
                LIMIT 10
                """
            else:
                return """
                SELECT p.product_name, e.elasticity_value, p.category_level_2
                FROM products p 
                JOIN elasticity e ON p.upc_code = e.upc_code 
                ORDER BY e.elasticity_value DESC 
                LIMIT 10
                """
        
        elif "cpi" in question_lower and "higher" in question_lower:
            # Extract threshold if possible
            import re
            threshold_match = re.search(r"(\d+\.?\d*)", question)
            threshold = threshold_match.group(1) if threshold_match else "1.05"
            
            return f"""
            SELECT p.product_name, cp.competitor_name, cp.cpi_value, cp.our_price, cp.competitor_price
            FROM products p 
            JOIN competitive_pricing cp ON p.upc_code = cp.upc_code 
            WHERE cp.cpi_value > {threshold}
            ORDER BY cp.cpi_value DESC 
            LIMIT 20
            """
        
        elif "revenue" in question_lower and "category" in question_lower:
            return """
            SELECT p.category_level_2, SUM(s.revenue) as total_revenue, COUNT(*) as product_count
            FROM products p 
            JOIN sales_data s ON p.upc_code = s.upc_code 
            WHERE s.week_ending_date >= date('now', '-6 months')
            GROUP BY p.category_level_2 
            ORDER BY total_revenue DESC
            """
        
        elif "margin" in question_lower and ("negative" in question_lower or "lowest" in question_lower):
            return """
            SELECT p.product_name, m.margin_percent, m.margin_amount, m.selling_price
            FROM products p 
            JOIN margin_analysis m ON p.upc_code = m.upc_code 
            WHERE m.margin_percent < 0 OR m.margin_amount < 0
            ORDER BY m.margin_percent ASC 
            LIMIT 20
            """
        
        # Default fallback - show product information
        return """
        SELECT product_name, brand, category_level_2, base_price 
        FROM products 
        LIMIT 10
        """
    
    def _generate_fallback_response(self, question: str, query_result: QueryResult) -> str:
        """Generate fallback natural language response"""
        if not query_result.success:
            return f"I encountered an error while processing your question: {query_result.error_message}"
        
        if query_result.row_count == 0:
            return "I couldn't find any data matching your query. Please try rephrasing your question or check if the data exists."
        
        # Generate basic response based on query type
        question_lower = question.lower()
        
        if "current price" in question_lower:
            return f"I found pricing information for your query. The results show {query_result.row_count} record(s) with current pricing data."
        
        elif "elasticity" in question_lower:
            return f"I found {query_result.row_count} product(s) with elasticity data. The results are ordered by elasticity value to help you identify products most sensitive to price changes."
        
        elif "cpi" in question_lower:
            return f"I found {query_result.row_count} product(s) with competitive pricing data meeting your criteria. These products have competitive price index values above your specified threshold."
        
        elif "revenue" in question_lower:
            return f"I found revenue data for {query_result.row_count} categories. The results show total revenue by category for the specified time period."
        
        elif "margin" in question_lower:
            return f"I found {query_result.row_count} product(s) with margin data meeting your criteria. These results can help you identify products that may need pricing adjustments."
        
        else:
            return f"I found {query_result.row_count} record(s) matching your query. Please review the data table below for detailed information."
    
    def process_question(self, question: str, user_context: Optional[Dict] = None) -> AgentResponse:
        """
        Process a natural language question and return a complete response
        
        Args:
            question: Natural language question
            user_context: Optional user context (preferences, filters, etc.)
            
        Returns:
            AgentResponse with complete results
        """
        start_time = time.time()
        self.query_count += 1
        
        try:
            self.logger.info(f"Processing question: {question}")
            
            # Step 1: Process the question
            processed_question = self.question_processor.process_question(question)
            self.logger.debug(f"Question processed - Intent: {processed_question.intent}")
            
            # Step 2: Retrieve relevant context
            context = self.context_retriever.retrieve_context(
                question=question,
                intent=processed_question.intent,
                entities=[e.value for e in processed_question.entities]
            )
            self.logger.debug(f"Context retrieved - {len(context.schemas)} schemas, {len(context.examples)} examples")
            
            # Step 3: Generate SQL query
            sql_query = ""
            confidence_score = 0.5
            
            if self.openai_available and self.sql_generator:
                try:
                    # Try OpenAI-powered SQL generation
                    query_context = QueryContext(
                        table_schemas={schema.table_name: asdict(schema) for schema in context.schemas},
                        sample_data={},
                        business_rules=[rule.description for rule in context.rules],
                        similar_queries=[{"question": ex.question, "sql": ex.sql_query} for ex in context.examples],
                        metadata={
                            **context.metadata,
                            'database_type': 'sqlite',
                            'available_tables': self.sqlite_client.list_tables()
                        }
                    )
                    
                    generated_sql = self.sql_generator.generate_sql(question, query_context)
                    sql_query = generated_sql.sql_query
                    confidence_score = generated_sql.confidence_score
                    
                    if generated_sql.validation_errors:
                        self.logger.warning(f"SQL validation errors: {generated_sql.validation_errors}")
                        raise Exception("SQL validation failed")
                    
                except Exception as e:
                    self.logger.warning(f"OpenAI SQL generation failed: {str(e)}")
                    if self.config.fallback_mode:
                        # Use fallback SQL generator
                        fallback_context = FallbackQueryContext(
                            table_schemas={schema.table_name: asdict(schema) for schema in context.schemas},
                            available_tables=self.sqlite_client.list_tables(),
                            question=question,
                            entities=[e.value for e in processed_question.entities],
                            intent=processed_question.intent
                        )
                        
                        fallback_result = self.fallback_sql_generator.generate_sql(question, fallback_context)
                        sql_query = fallback_result.sql_query
                        confidence_score = fallback_result.confidence_score
                        self.fallback_queries += 1
                        self.logger.info(f"Using fallback SQL generator: {fallback_result.explanation}")
                    else:
                        return self._create_error_response(question, str(e), [], start_time)
            else:
                # Use fallback SQL generation
                fallback_context = FallbackQueryContext(
                    table_schemas={schema.table_name: asdict(schema) for schema in context.schemas},
                    available_tables=self.sqlite_client.list_tables(),
                    question=question,
                    entities=[e.value for e in processed_question.entities],
                    intent=processed_question.intent
                )
                
                fallback_result = self.fallback_sql_generator.generate_sql(question, fallback_context)
                sql_query = fallback_result.sql_query
                confidence_score = fallback_result.confidence_score
                self.fallback_queries += 1
                self.logger.info(f"Using fallback SQL generator: {fallback_result.explanation}")
            
            if not sql_query.strip():
                return self._create_error_response(
                    question, 
                    "Failed to generate SQL query",
                    ["No SQL query generated"],
                    start_time
                )
            
            self.logger.debug(f"SQL generated - Confidence: {confidence_score}")
            
            # Step 4: Execute SQL query using SQLite
            query_result = self.sqlite_client.execute_query(sql_query.strip())
            self.logger.debug(f"Query executed - Success: {query_result.success}, Rows: {query_result.row_count}")
            
            # Step 5: Generate natural language response
            natural_language_response = ""
            data_table = ""
            key_insights = []
            
            if self.response_generator and self.openai_available:
                try:
                    response_context = ResponseContext(
                        original_question=question,
                        sql_query=sql_query,
                        query_result=query_result,
                        intent=processed_question.intent,
                        entities=[e.value for e in processed_question.entities],
                        user_preferences=user_context or {}
                    )
                    
                    generated_response = self.response_generator.generate_response(response_context)
                    natural_language_response = generated_response.text_response
                    data_table = generated_response.data_table
                    key_insights = generated_response.key_insights
                    
                except Exception as e:
                    self.logger.warning(f"OpenAI response generation failed: {str(e)}")
                    natural_language_response = self._generate_fallback_response(question, query_result)
                    data_table = self._format_data_table(query_result)
                    key_insights = [f"Query returned {query_result.row_count} records"]
            else:
                # Use fallback response generation
                natural_language_response = self._generate_fallback_response(question, query_result)
                data_table = self._format_data_table(query_result)
                key_insights = [f"Query returned {query_result.row_count} records"]
            
            # Calculate execution time
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            if query_result.success:
                self.successful_queries += 1
            
            # Create final response
            agent_response = AgentResponse(
                success=query_result.success,
                natural_language_response=natural_language_response,
                sql_query=sql_query,
                data_table=data_table,
                visualization=None,  # Could be enhanced with visualization
                key_insights=key_insights,
                execution_time=execution_time,
                row_count=query_result.row_count,
                confidence_score=confidence_score,
                error_message=query_result.error_message,
                metadata={
                    'processed_question': asdict(processed_question),
                    'query_result_metadata': query_result.metadata,
                    'agent_stats': self.get_stats(),
                    'database_type': 'sqlite',
                    'openai_available': self.openai_available,
                    'fallback_used': not self.openai_available or self.fallback_queries > 0
                }
            )
            
            self.logger.info(f"Question processed successfully in {execution_time:.2f}s")
            return agent_response
            
        except Exception as e:
            self.logger.error(f"Error processing question: {str(e)}")
            return self._create_error_response(question, str(e), [], start_time)
    
    def _format_data_table(self, query_result: QueryResult) -> str:
        """Format query result as HTML table"""
        if not query_result.success or query_result.data is None or query_result.data.empty:
            return "<p>No data available.</p>"
        
        try:
            # Convert DataFrame to HTML table
            html_table = query_result.data.to_html(
                classes='table table-striped table-hover',
                table_id='query-results',
                escape=False,
                index=False
            )
            return html_table
        except Exception as e:
            self.logger.error(f"Error formatting data table: {str(e)}")
            return f"<p>Error formatting results: {str(e)}</p>"
    
    def _create_error_response(self, question: str, error_message: str, 
                             validation_errors: List[str], start_time: float) -> AgentResponse:
        """Create error response"""
        execution_time = time.time() - start_time
        
        # Generate helpful error message
        if validation_errors:
            error_details = f"SQL validation failed: {'; '.join(validation_errors)}"
        else:
            error_details = error_message
        
        return AgentResponse(
            success=False,
            natural_language_response=f"I apologize, but I encountered an issue processing your question: {error_details}. Please try rephrasing your question or contact support if the problem persists.",
            sql_query="",
            data_table="<p>No data available due to error.</p>",
            visualization=None,
            key_insights=[f"Error: {error_details}"],
            execution_time=execution_time,
            row_count=0,
            confidence_score=0.0,
            error_message=error_details,
            metadata={
                'error': True, 
                'original_question': question, 
                'database_type': 'sqlite',
                'openai_available': self.openai_available
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        success_rate = self.successful_queries / self.query_count if self.query_count > 0 else 0
        avg_execution_time = self.total_execution_time / self.query_count if self.query_count > 0 else 0
        fallback_rate = self.fallback_queries / self.query_count if self.query_count > 0 else 0
        
        return {
            'total_queries': self.query_count,
            'successful_queries': self.successful_queries,
            'success_rate': success_rate,
            'average_execution_time': avg_execution_time,
            'fallback_queries': self.fallback_queries,
            'fallback_rate': fallback_rate,
            'openai_available': self.openai_available,
            'sqlite_stats': self.sqlite_client.get_metrics_summary(),
            'vector_store_stats': self.vector_store.get_collection_stats(),
            'database_type': 'sqlite'
        }
    
    def get_schema_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get schema information for available tables"""
        if table_name:
            schema = self.sqlite_client.get_table_schema(table_name)
            return asdict(schema) if schema else {}
        else:
            tables = self.sqlite_client.list_tables()
            schemas = self.sqlite_client.get_all_schemas()
            return {
                'available_tables': tables,
                'table_schemas': {name: asdict(schema) for name, schema in schemas.items()}
            }
    
    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """Validate SQL query without executing it"""
        return self.sqlite_client.validate_query(sql_query)
    
    def clear_cache(self):
        """Clear all caches"""
        self.sqlite_client.clear_cache()
        self.logger.info("Caches cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check SQLite connection
            tables = self.sqlite_client.list_tables()
            health_status['components']['sqlite'] = {
                'status': 'healthy',
                'available_tables': len(tables),
                'database_path': self.sqlite_client.database_path
            }
        except Exception as e:
            health_status['components']['sqlite'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'
        
        try:
            # Check vector store
            stats = self.vector_store.get_collection_stats()
            health_status['components']['vector_store'] = {
                'status': 'healthy',
                'collections': stats
            }
        except Exception as e:
            health_status['components']['vector_store'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['overall_status'] = 'degraded'
        
        # Check OpenAI API (if available)
        if self.openai_available and self.sql_generator:
            try:
                # Simple test
                test_response = self.sql_generator.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                health_status['components']['openai'] = {
                    'status': 'healthy',
                    'model': 'gpt-4o'
                }
            except Exception as e:
                health_status['components']['openai'] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                # Don't mark overall as degraded if fallback is enabled
                if not self.config.fallback_mode:
                    health_status['overall_status'] = 'degraded'
        else:
            health_status['components']['openai'] = {
                'status': 'unavailable',
                'fallback_enabled': self.config.fallback_mode
            }
        
        return health_status


# Factory function for easy agent creation
def create_fixed_agent(
    openai_api_key: Optional[str] = None,
    database_path: str = "retail_analytics.db",
    **kwargs
) -> Text2SQLAgentFixed:
    """
    Factory function to create a fixed Text-to-SQL agent
    
    Args:
        openai_api_key: OpenAI API key
        database_path: Path to SQLite database file
        **kwargs: Additional configuration options
        
    Returns:
        Configured Text2SQLAgentFixed instance
    """
    config = AgentConfig(
        openai_api_key=openai_api_key or os.getenv('OPENAI_API_KEY'),
        database_path=database_path,
        fallback_mode=True,  # Enable fallback by default
        **kwargs
    )
    
    return Text2SQLAgentFixed(config)


# Example usage and testing
if __name__ == "__main__":
    # Create fixed agent
    agent = create_fixed_agent(database_path="test_retail.db")
    
    # Test questions
    test_questions = [
        "What is the current price for UPC code '0020282000000'?",
        "Show me the top 10 items by elasticity in the frozen food category",
        "Which items have a CPI value higher than 1.05?",
        "Show me revenue by category for the last 6 months"
    ]
    
    print("Testing Fixed Text-to-SQL Agent:")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nTest {i}: {question}")
        print("-" * 30)
        
        response = agent.process_question(question)
        
        print(f"Success: {response.success}")
        print(f"SQL Query: {response.sql_query[:100]}...")
        print(f"Response: {response.natural_language_response[:200]}...")
        print(f"Execution Time: {response.execution_time:.2f}s")
        print(f"Confidence: {response.confidence_score:.2f}")
        print(f"Fallback Used: {response.metadata.get('fallback_used', False)}")
        
        if not response.success:
            print(f"Error: {response.error_message}")
    
    # Print agent statistics
    print("\nAgent Statistics:")
    print("=" * 30)
    stats = agent.get_stats()
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_value in value.items():
                print(f"  {sub_key}: {sub_value}")
        else:
            print(f"{key}: {value}")
    
    # Health check
    print("\nHealth Check:")
    print("=" * 20)
    health = agent.health_check()
    print(f"Overall Status: {health['overall_status']}")
    for component, status in health['components'].items():
        print(f"{component}: {status['status']}")

