"""
Main Text-to-SQL Agent for Revionics

This module orchestrates all components to provide a complete text-to-SQL solution
including question processing, SQL generation, query execution, and response generation.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import time
from datetime import datetime

from .query_processor import QuestionProcessor, ProcessedQuestion
from .sql_generator import SQLGenerator, QueryContext, GeneratedSQL
from .vector_store import VectorStore, ContextRetriever, SchemaLoader
from .bigquery_client import BigQueryClient, QueryResult
from .response_generator import ResponseGenerator, ResponseContext, GeneratedResponse


@dataclass
class AgentConfig:
    """Configuration for the Text-to-SQL agent"""
    openai_api_key: Optional[str] = None
    bigquery_project_id: Optional[str] = None
    bigquery_dataset_id: Optional[str] = None
    bigquery_credentials_path: Optional[str] = None
    vector_store_path: str = "./chroma_db"
    enable_cache: bool = True
    max_results: int = 1000
    enable_visualization: bool = True
    log_level: str = "INFO"


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


class Text2SQLAgent:
    """Main Text-to-SQL Agent class"""
    
    def __init__(self, config: AgentConfig):
        """
        Initialize the Text-to-SQL Agent
        
        Args:
            config: Agent configuration
        """
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize components
        self.question_processor = QuestionProcessor()
        self.sql_generator = SQLGenerator(api_key=config.openai_api_key)
        self.vector_store = VectorStore(persist_directory=config.vector_store_path)
        self.context_retriever = ContextRetriever(self.vector_store)
        self.bigquery_client = BigQueryClient(
            project_id=config.bigquery_project_id,
            credentials_path=config.bigquery_credentials_path,
            dataset_id=config.bigquery_dataset_id,
            enable_cache=config.enable_cache,
            max_results=config.max_results
        )
        self.response_generator = ResponseGenerator(api_key=config.openai_api_key)
        
        # Initialize schemas and examples
        self._initialize_knowledge_base()
        
        # Track agent metrics
        self.query_count = 0
        self.successful_queries = 0
        self.total_execution_time = 0.0
        
        self.logger.info("Text-to-SQL Agent initialized successfully")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with schemas and examples"""
        try:
            # Check if knowledge base is already populated
            stats = self.vector_store.get_collection_stats()
            
            if stats['schemas'] == 0:
                self.logger.info("Initializing knowledge base...")
                schema_loader = SchemaLoader(self.vector_store)
                schema_loader.load_retail_schemas()
                schema_loader.load_sample_examples()
                schema_loader.load_business_rules()
                self.logger.info("Knowledge base initialized")
            else:
                self.logger.info(f"Knowledge base already populated: {stats}")
                
        except Exception as e:
            self.logger.error(f"Error initializing knowledge base: {str(e)}")
    
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
            query_context = QueryContext(
                table_schemas={schema.table_name: asdict(schema) for schema in context.schemas},
                sample_data={},  # Could be populated with actual sample data
                business_rules=[rule.description for rule in context.rules],
                similar_queries=[{"question": ex.question, "sql": ex.sql_query} for ex in context.examples],
                metadata=context.metadata
            )
            
            generated_sql = self.sql_generator.generate_sql(question, query_context)
            self.logger.debug(f"SQL generated - Confidence: {generated_sql.confidence_score}")
            
            if not generated_sql.sql_query or generated_sql.validation_errors:
                return self._create_error_response(
                    question, 
                    "Failed to generate valid SQL query",
                    generated_sql.validation_errors,
                    start_time
                )
            
            # Step 4: Execute SQL query
            query_result = self.bigquery_client.execute_query(generated_sql.sql_query)
            self.logger.debug(f"Query executed - Success: {query_result.success}, Rows: {query_result.row_count}")
            
            # Step 5: Generate natural language response
            response_context = ResponseContext(
                original_question=question,
                sql_query=generated_sql.sql_query,
                query_result=query_result,
                intent=processed_question.intent,
                entities=[e.value for e in processed_question.entities],
                user_preferences=user_context or {}
            )
            
            generated_response = self.response_generator.generate_response(response_context)
            self.logger.debug("Natural language response generated")
            
            # Calculate execution time
            execution_time = time.time() - start_time
            self.total_execution_time += execution_time
            
            if query_result.success:
                self.successful_queries += 1
            
            # Create final response
            agent_response = AgentResponse(
                success=query_result.success,
                natural_language_response=generated_response.text_response,
                sql_query=generated_sql.sql_query,
                data_table=generated_response.data_table,
                visualization=generated_response.visualization,
                key_insights=generated_response.key_insights,
                execution_time=execution_time,
                row_count=query_result.row_count,
                confidence_score=min(generated_sql.confidence_score, generated_response.confidence_score),
                error_message=query_result.error_message,
                metadata={
                    'processed_question': asdict(processed_question),
                    'generated_sql': asdict(generated_sql),
                    'query_result_metadata': query_result.metadata,
                    'response_metadata': generated_response.metadata,
                    'agent_stats': self.get_stats()
                }
            )
            
            self.logger.info(f"Question processed successfully in {execution_time:.2f}s")
            return agent_response
            
        except Exception as e:
            self.logger.error(f"Error processing question: {str(e)}")
            return self._create_error_response(question, str(e), [], start_time)
    
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
            metadata={'error': True, 'original_question': question}
        )
    
    def refine_query(self, original_question: str, feedback: str) -> AgentResponse:
        """
        Refine a query based on user feedback
        
        Args:
            original_question: Original question
            feedback: User feedback or correction
            
        Returns:
            AgentResponse with refined results
        """
        refined_question = f"{original_question} (Feedback: {feedback})"
        return self.process_question(refined_question)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent performance statistics"""
        success_rate = self.successful_queries / self.query_count if self.query_count > 0 else 0
        avg_execution_time = self.total_execution_time / self.query_count if self.query_count > 0 else 0
        
        return {
            'total_queries': self.query_count,
            'successful_queries': self.successful_queries,
            'success_rate': success_rate,
            'average_execution_time': avg_execution_time,
            'bigquery_stats': self.bigquery_client.get_metrics_summary(),
            'vector_store_stats': self.vector_store.get_collection_stats()
        }
    
    def get_schema_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get schema information for available tables
        
        Args:
            table_name: Specific table name (optional)
            
        Returns:
            Schema information
        """
        if table_name:
            return self.bigquery_client.get_table_schema(table_name)
        else:
            tables = self.bigquery_client.list_tables()
            return {'available_tables': tables}
    
    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query without executing it
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.bigquery_client.validate_query(sql_query)
    
    def clear_cache(self):
        """Clear all caches"""
        self.bigquery_client.clear_cache()
        self.logger.info("Caches cleared")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            'overall_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # Check BigQuery connection
            tables = self.bigquery_client.list_tables()
            health_status['components']['bigquery'] = {
                'status': 'healthy',
                'available_tables': len(tables)
            }
        except Exception as e:
            health_status['components']['bigquery'] = {
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
        
        # Check OpenAI API (simple test)
        try:
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
            health_status['overall_status'] = 'degraded'
        
        return health_status


# Factory function for easy agent creation
def create_agent(
    openai_api_key: Optional[str] = None,
    bigquery_project_id: Optional[str] = None,
    bigquery_dataset_id: Optional[str] = None,
    bigquery_credentials_path: Optional[str] = None,
    **kwargs
) -> Text2SQLAgent:
    """
    Factory function to create a Text-to-SQL agent with default configuration
    
    Args:
        openai_api_key: OpenAI API key
        bigquery_project_id: BigQuery project ID
        bigquery_dataset_id: BigQuery dataset ID
        bigquery_credentials_path: Path to BigQuery credentials
        **kwargs: Additional configuration options
        
    Returns:
        Configured Text2SQLAgent instance
    """
    config = AgentConfig(
        openai_api_key=openai_api_key or os.getenv('OPENAI_API_KEY'),
        bigquery_project_id=bigquery_project_id or os.getenv('GOOGLE_CLOUD_PROJECT'),
        bigquery_dataset_id=bigquery_dataset_id or os.getenv('BIGQUERY_DATASET'),
        bigquery_credentials_path=bigquery_credentials_path,
        **kwargs
    )
    
    return Text2SQLAgent(config)


# Example usage and testing
if __name__ == "__main__":
    # Create agent with default configuration
    agent = create_agent()
    
    # Test questions
    test_questions = [
        "What is the current price for UPC code '0020282000000'?",
        "Show me the top 10 items by elasticity in the frozen food category",
        "What are the pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'?",
        "How many price increases were there in April 2025?"
    ]
    
    print("Testing Text-to-SQL Agent:")
    print("=" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\nTest {i}: {question}")
        print("-" * 30)
        
        response = agent.process_question(question)
        
        print(f"Success: {response.success}")
        print(f"SQL Query: {response.sql_query}")
        print(f"Response: {response.natural_language_response[:200]}...")
        print(f"Execution Time: {response.execution_time:.2f}s")
        print(f"Confidence: {response.confidence_score:.2f}")
        
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

