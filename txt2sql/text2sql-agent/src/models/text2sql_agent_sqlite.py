"""
Main Text-to-SQL Agent for (SQLite Version)

This module orchestrates all components to provide a complete text-to-SQL solution
using SQLite instead of BigQuery for local database operations.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import time
from datetime import datetime
import json

from .query_processor import QuestionProcessor, ProcessedQuestion
from .sql_generator import SQLGenerator, QueryContext, GeneratedSQL
from .vector_store import VectorStore, ContextRetriever, SchemaLoader
from .sqlite_client import SQLiteClient, QueryResult, create_sqlite_client
from .response_generator import ResponseGenerator, ResponseContext, GeneratedResponse

from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType
from traceai_openai import OpenAIInstrumentor
from opentelemetry import trace
from fi.evals import Evaluator
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import (
    ProjectType
)
from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues



evaluator = Evaluator(fi_api_key=os.getenv("FI_API_KEY"), fi_secret_key=os.getenv("FI_SECRET_KEY"))

tracer = FITracer(trace.get_tracer(__name__))

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


class Text2SQLAgentSQLite:
    """Main Text-to-SQL Agent class using SQLite"""
    
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
        
        # Initialize vector store with proper directory creation
        self._ensure_vector_store_directory()
        self.vector_store = VectorStore(persist_directory=config.vector_store_path)
        self.context_retriever = ContextRetriever(self.vector_store)
        
        # Initialize SQLite client
        self.sqlite_client = create_sqlite_client(
            database_path=config.database_path,
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
        
        self.logger.info("Text-to-SQL Agent (SQLite) initialized successfully")
    
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
            # Always try to load actual database schemas first
            self.logger.info("Loading schemas from actual database...")
            self._load_sqlite_schemas_directly()
            
            # Then try to enhance with vector store if available
            if hasattr(self, 'vector_store') and self.vector_store:
                try:
                    stats = self.vector_store.get_collection_stats()
                    
                    if stats.get('schemas', 0) == 0:
                        self.logger.info("Initializing vector store knowledge base...")
                        schema_loader = SchemaLoader(self.vector_store)
                        
                        # Load SQLite-specific retail schemas
                        self._load_sqlite_schemas(schema_loader)
                        schema_loader.load_sample_examples()
                        schema_loader.load_business_rules()
                        
                        self.logger.info("Vector store knowledge base initialized")
                    else:
                        self.logger.info(f"Vector store knowledge base already populated: {stats}")
                except Exception as e:
                    self.logger.warning(f"Vector store knowledge base initialization failed: {str(e)}")
                    self.logger.info("Continuing with direct database schema access")
            else:
                self.logger.info("Vector store not available, using direct database schema access only")
                
        except Exception as e:
            self.logger.error(f"Error initializing knowledge base: {str(e)}")
            # Continue without knowledge base for basic functionality

    def _load_sqlite_schemas_directly(self):
        """Load schemas directly from SQLite database for immediate use"""
        try:
            tables = self.sqlite_client.list_tables()
            self.logger.info(f"Found {len(tables)} tables in database: {tables}")
            
            # Store schemas for direct access
            self.actual_schemas = self.sqlite_client.get_all_schemas()
            self.logger.info(f"Loaded schemas for {len(self.actual_schemas)} tables")
            
            # Log schema details for debugging
            for table_name, schema in self.actual_schemas.items():
                column_names = [col['name'] for col in schema.columns]
                self.logger.debug(f"Table {table_name}: {column_names}")
                
        except Exception as e:
            self.logger.error(f"Error loading SQLite schemas directly: {str(e)}")
            self.actual_schemas = {}
    
    def _load_sqlite_schemas(self, schema_loader: SchemaLoader):
        """Load SQLite-specific retail schemas"""
        try:
            # Get actual table schemas from SQLite database
            tables = self.sqlite_client.list_tables()
            
            if tables:
                # Load schemas from existing tables
                for table_name in tables:
                    schema = self.sqlite_client.get_table_schema(table_name)
                    if schema:
                        schema_loader.add_table_schema(
                            table_name=schema.table_name,
                            columns=schema.columns,
                            description=schema.description,
                            sample_data=schema.sample_data
                        )
            else:
                # Load default retail schemas if no tables exist
                schema_loader.load_retail_schemas()
                
        except Exception as e:
            self.logger.error(f"Error loading SQLite schemas: {str(e)}")
            # Fallback to default schemas
            schema_loader.load_retail_schemas()
    
    def process_question(self, question: str, user_context: Optional[Dict] = None) -> AgentResponse:
        with tracer.start_as_current_span("process_question") as span:
            span.set_attribute("process_question", "process_question")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.AGENT.value)
            span.set_attribute("input.value", json.dumps(question))

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
                
                # Step 3: Generate SQL query with SQLite-specific context
                # If vector store is empty, get schemas directly from database
                if len(context.schemas) == 0:
                    self.logger.info("No schemas in vector store, using direct database schema inspection")
                    all_schemas = self.sqlite_client.get_all_schemas()
                    
                    # Convert SQLite schemas to the format expected by SQL generator
                    table_schemas = {}
                    for table_name, schema in all_schemas.items():
                        table_schemas[table_name] = {
                            'table_name': schema.table_name,
                            'columns': schema.columns,
                            'description': schema.description,
                            'sample_data': schema.sample_data or []
                        }
                else:
                    table_schemas = {schema.table_name: asdict(schema) for schema in context.schemas}

                query_context = QueryContext(
                    table_schemas=table_schemas,
                    sample_data={},  # Could be populated with actual sample data
                    business_rules=[rule.description for rule in context.rules],
                    similar_queries=[{"question": ex.question, "sql": ex.sql_query} for ex in context.examples],
                    metadata={
                        **context.metadata,
                        'database_type': 'sqlite',
                        'available_tables': self.sqlite_client.list_tables(),
                        'actual_schemas_used': len(table_schemas)
                    }
                )
                
                generated_sql = self.sql_generator.generate_sql(question, query_context)
                self.logger.debug(f"SQL generated - Confidence: {generated_sql.confidence_score}")
                
                if not generated_sql.sql_query or generated_sql.validation_errors:

                    #########################################################
                    print("#########################")
                    print("completeness_of_context")
                    print(json.dumps(question))
                    print(json.dumps(table_schemas))
                    print("#########################")
                    config_completeness_of_context = {
                        "eval_templates" : "completeness_of_context",
                        "inputs" : {
                            "question": json.dumps(question),
                            "context": json.dumps(table_schemas),
                        },
                        "model_name" : "turing_large"
                    }

                    eval_result1 = evaluator.evaluate(
                        **config_completeness_of_context, 
                        custom_eval_name="completeness_of_context", 
                        trace_eval=True
                    )

                    print("#########################")
                    print("pricing_logic_correctness")
                    print("None")
                    print("#########################")
                    config_pricing_logic_correctness = {
                        "eval_templates" : "pricing_logic_correctness_2",
                        "inputs" : {
                            "agent_response": json.dumps("None"),
                        },
                        "model_name" : "turing_large"
                    }

                    eval_result2 = evaluator.evaluate(
                        **config_pricing_logic_correctness, 
                        custom_eval_name="pricing_logic_correctness", 
                        trace_eval=True
                    )

                    print("#########################")
                    print("ambiguity_resolution")
                    print(json.dumps(question))
                    print(json.dumps("None"))
                    print("#########################")
                    config_ambiguity_resolution = {
                        "eval_templates" : "ambiguity_resolution_2",
                        "inputs" : {
                            "question": json.dumps(question),
                            "agent_response": json.dumps("None"),
                        },
                        "model_name" : "turing_large"
                    }

                    eval_result3 = evaluator.evaluate(
                        **config_ambiguity_resolution, 
                        custom_eval_name="ambiguity_resolution", 
                        trace_eval=True
                    )
                    return self._create_error_response(
                        question, 
                        "Failed to generate valid SQL query",
                        generated_sql.validation_errors,
                        start_time
                    )
                
                # Step 4: Execute SQL query using SQLite
                query_result = self.sqlite_client.execute_query(generated_sql.sql_query)
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
                        'agent_stats': self.get_stats(),
                        'database_type': 'sqlite'
                    }
                )
                
                self.logger.info(f"Question processed successfully in {execution_time:.2f}s")
                span.set_attribute("output.value", json.dumps(agent_response.natural_language_response))
                
                print("#########################")
                print("completeness_of_context")
                print(json.dumps(question))
                print(json.dumps(table_schemas))
                print("#########################")
                config_completeness_of_context = {
                    "eval_templates" : "completeness_of_context",
                    "inputs" : {
                        "question": json.dumps(question),
                        "context": json.dumps(table_schemas),
                    },
                    "model_name" : "turing_large"
                }

                eval_result4 = evaluator.evaluate(
                    **config_completeness_of_context, 
                    custom_eval_name="completeness_of_context", 
                    trace_eval=True
                )

                print("#########################")
                print("pricing_logic_correctness")
                print(json.dumps(agent_response.natural_language_response if agent_response.natural_language_response is not None else "None"))
                print("#########################")
                config_pricing_logic_correctness = {
                    "eval_templates" : "pricing_logic_correctness_2",
                    "inputs" : {
                        "agent_response": json.dumps(agent_response.natural_language_response if agent_response.natural_language_response is not None else "None"),
                    },
                    "model_name" : "turing_large"
                }

                eval_result5 = evaluator.evaluate(
                    **config_pricing_logic_correctness, 
                    custom_eval_name="pricing_logic_correctness", 
                    trace_eval=True
                )

                print("#########################")
                print("ambiguity_resolution")
                print(json.dumps(question))
                print(json.dumps(agent_response.natural_language_response))
                print("#########################")
                config_ambiguity_resolution = {
                    "eval_templates" : "ambiguity_resolution_2",
                    "inputs" : {
                        "question": json.dumps(question),
                        "agent_response": json.dumps(agent_response.natural_language_response),
                    },
                    "model_name" : "turing_large"
                }

                eval_result6 = evaluator.evaluate(
                    **config_ambiguity_resolution, 
                    custom_eval_name="ambiguity_resolution", 
                    trace_eval=True
                )
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
            metadata={'error': True, 'original_question': question, 'database_type': 'sqlite'}
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
            'sqlite_stats': self.sqlite_client.get_metrics_summary(),
            'vector_store_stats': self.vector_store.get_collection_stats(),
            'database_type': 'sqlite'
        }
    
    def get_schema_info(self, table_name: Optional[str] = None) -> Dict[str, Any]:
        with tracer.start_as_current_span("get_schema_info") as span:
            span.set_attribute("get_schema_info", "get_schema_info")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"table_name": table_name}))

            """
            Get schema information for available tables
            
            Args:
                table_name: Specific table name (optional)
                
            Returns:
                Schema information
            """
            if table_name:
                schema = self.sqlite_client.get_table_schema(table_name)
                span.set_attribute("output.value", json.dumps(asdict(schema) if schema else {}))
                return asdict(schema) if schema else {}
            else:
                tables = self.sqlite_client.list_tables()
                schemas = self.sqlite_client.get_all_schemas()
                span.set_attribute("output.value", json.dumps({"table_schemas": {name: asdict(schema) for name, schema in schemas.items()}}))
                return {
                    'available_tables': tables,
                    'table_schemas': {name: asdict(schema) for name, schema in schemas.items()}
                }
        
    def validate_sql(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        with tracer.start_as_current_span("validate_sql") as span:
            span.set_attribute("validate_sql", "validate_sql")
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"sql_query": sql_query}))
            

            """
            Validate SQL query without executing it
            
            Args:
                sql_query: SQL query to validate
                
            Returns:
                Tuple of (is_valid, error_message)
            """
            span.set_attribute("output.value", json.dumps(self.sqlite_client.validate_query(sql_query)))
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
    
    def backup_database(self, backup_path: str):
        """Create a backup of the SQLite database"""
        try:
            self.sqlite_client.backup_database(backup_path)
            self.logger.info(f"Database backed up to {backup_path}")
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            raise


# Factory function for easy agent creation
def create_agent_sqlite(
    openai_api_key: Optional[str] = None,
    database_path: str = "retail_analytics.db",
    **kwargs
) -> Text2SQLAgentSQLite:
    """
    Factory function to create a Text-to-SQL agent with SQLite backend
    
    Args:
        openai_api_key: OpenAI API key
        database_path: Path to SQLite database file
        **kwargs: Additional configuration options
        
    Returns:
        Configured Text2SQLAgentSQLite instance
    """
    config = AgentConfig(
        openai_api_key=openai_api_key or os.getenv('OPENAI_API_KEY'),
        database_path=database_path,
        **kwargs
    )
    
    return Text2SQLAgentSQLite(config)


# Example usage and testing
if __name__ == "__main__":
    # Create agent with SQLite backend
    agent = create_agent_sqlite(database_path="test_retail.db")
    
    # Test questions
    test_questions = [
        "What is the current price for UPC code '0020282000000'?",
        "Show me the top 10 items by elasticity in the frozen food category",
        "What are the pricing strategies for level 2 'BREAD & WRAPS' in zone 'Banner 2'?",
        "How many price increases were there in April 2025?"
    ]
    
    print("Testing Text-to-SQL Agent (SQLite):")
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

