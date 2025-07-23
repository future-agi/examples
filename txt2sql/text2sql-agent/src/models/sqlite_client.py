"""
SQLite Client for Text-to-SQL Agent

This module replaces the BigQuery client with SQLite functionality,
providing local database operations for the text-to-SQL system.
"""

import os
import sqlite3
import logging
import time
import json
import hashlib
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
import pandas as pd
from datetime import datetime, timedelta
import threading
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import ProjectType
from traceai_openai import OpenAIInstrumentor
from opentelemetry import trace
from fi.evals import Evaluator
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import (
    ProjectType, FiSpanKindValues, SpanAttributes
)
from opentelemetry import trace

tracer = FITracer(trace.get_tracer(__name__))

@dataclass
class QueryResult:
    """Result of a SQL query execution"""
    success: bool
    data: Optional[pd.DataFrame]
    row_count: int
    execution_time: float
    error_message: Optional[str]
    cache_hit: bool
    metadata: Dict[str, Any]


@dataclass
class TableSchema:
    """Database table schema information"""
    table_name: str
    columns: List[Dict[str, str]]  # [{"name": "column_name", "type": "TEXT", "description": "..."}]
    description: str
    sample_data: Optional[List[Dict[str, Any]]] = None


class QueryCache:
    """Simple in-memory cache for query results"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache: Dict[str, Tuple[QueryResult, float]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
    
    def _generate_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[QueryResult]:
        """Get cached result if available and not expired"""
        with self.lock:
            key = self._generate_key(query)
            if key in self.cache:
                result, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    # Create a copy with cache_hit = True
                    cached_result = QueryResult(
                        success=result.success,
                        data=result.data.copy() if result.data is not None else None,
                        row_count=result.row_count,
                        execution_time=result.execution_time,
                        error_message=result.error_message,
                        cache_hit=True,
                        metadata=result.metadata.copy()
                    )
                    return cached_result
                else:
                    # Remove expired entry
                    del self.cache[key]
        return None
    
    def set(self, query: str, result: QueryResult):
        """Cache query result"""
        with self.lock:
            key = self._generate_key(query)
            
            # Remove oldest entries if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][1])
                del self.cache[oldest_key]
            
            self.cache[key] = (result, time.time())
    
    def clear(self):
        """Clear all cached results"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'ttl_seconds': self.ttl_seconds
            }


class SQLiteClient:
    """SQLite client for local database operations"""
    
    def __init__(self, 
                 database_path: str = "retail_analytics.db",
                 enable_cache: bool = True,
                 max_results: int = 1000,
                 cache_ttl: int = 3600):
        """
        Initialize SQLite client
        
        Args:
            database_path: Path to SQLite database file
            enable_cache: Whether to enable query result caching
            max_results: Maximum number of rows to return
            cache_ttl: Cache time-to-live in seconds
        """
        self.database_path = database_path
        self.max_results = max_results
        self.logger = logging.getLogger(__name__)
        
        # Initialize cache
        self.cache = QueryCache(ttl_seconds=cache_ttl) if enable_cache else None
        
        # Performance metrics
        self.query_count = 0
        self.total_execution_time = 0.0
        self.cache_hits = 0
        self.error_count = 0
        
        # Initialize database
        self._initialize_database()
        
        self.logger.info(f"SQLite client initialized with database: {database_path}")
    
    def _initialize_database(self):
        """Initialize database and create directory if needed"""
        try:
            # Create directory if it doesn't exist
            db_dir = os.path.dirname(self.database_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # Test connection
            with sqlite3.connect(self.database_path) as conn:
                conn.execute("SELECT 1")
            
            self.logger.info("Database connection established successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> QueryResult:
        with tracer.start_as_current_span("execute_query") as span:
            """
            Execute SQL query and return results
            
            Args:
                query: SQL query string
                params: Optional query parameters
                
            Returns:
                QueryResult with execution details
            """
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", query)
            start_time = time.time()
            self.query_count += 1
            
            try:
                # Check cache first
                if self.cache:
                    cached_result = self.cache.get(query)
                    if cached_result:
                        self.cache_hits += 1
                        self.logger.debug(f"Cache hit for query: {query[:100]}...")
                        span.set_attribute("output.value", cached_result.data.to_json(orient="records") if cached_result.data is not None else "[]")
                        return cached_result
                
                # Validate query
                is_valid, error_msg = self.validate_query(query)
                if not is_valid:
                    return self._create_error_result(f"Invalid query: {error_msg}", start_time)
                
                # Execute query
                with sqlite3.connect(self.database_path) as conn:
                    conn.row_factory = sqlite3.Row  # Enable column access by name
                    
                    # Set timeout and other pragmas
                    conn.execute("PRAGMA busy_timeout = 30000")  # 30 second timeout
                    
                    cursor = conn.execute(query, params or ())
                    
                    # Fetch results
                    if query.strip().upper().startswith(('SELECT', 'WITH')):
                        rows = cursor.fetchall()
                        
                        # Convert to DataFrame
                        if rows:
                            # Get column names
                            columns = [description[0] for description in cursor.description]
                            
                            # Convert rows to list of dicts
                            data = [dict(row) for row in rows]
                            
                            # Limit results
                            if len(data) > self.max_results:
                                data = data[:self.max_results]
                                self.logger.warning(f"Results limited to {self.max_results} rows")
                            
                            df = pd.DataFrame(data)
                            row_count = len(df)
                        else:
                            df = pd.DataFrame()
                            row_count = 0
                    else:
                        # For non-SELECT queries (INSERT, UPDATE, DELETE)
                        row_count = cursor.rowcount
                        df = pd.DataFrame()
                
                execution_time = time.time() - start_time
                self.total_execution_time += execution_time
                
                result = QueryResult(
                    success=True,
                    data=df,
                    row_count=row_count,
                    execution_time=execution_time,
                    error_message=None,
                    cache_hit=False,
                    metadata={
                        'query_type': self._get_query_type(query),
                        'database_path': self.database_path,
                        'limited_results': row_count == self.max_results
                    }
                )
                
                # Cache successful SELECT queries
                if self.cache and query.strip().upper().startswith(('SELECT', 'WITH')):
                    self.cache.set(query, result)
                
                self.logger.debug(f"Query executed successfully in {execution_time:.2f}s, {row_count} rows")
                span.set_attribute("output.value", result.data.to_json(orient="records") if result.data is not None else "[]")
                return result
                
            except sqlite3.Error as e:
                self.error_count += 1
                error_msg = f"SQLite error: {str(e)}"
                self.logger.error(f"Query execution failed: {error_msg}")
                span.set_attribute("output.value", error_msg)
                return self._create_error_result(error_msg, start_time)
            
            except Exception as e:
                self.error_count += 1
                error_msg = f"Unexpected error: {str(e)}"
                self.logger.error(f"Query execution failed: {error_msg}")
                span.set_attribute("output.value", error_msg)
                return self._create_error_result(error_msg, start_time)
    
    def _create_error_result(self, error_message: str, start_time: float) -> QueryResult:
        """Create error result"""
        execution_time = time.time() - start_time
        self.total_execution_time += execution_time
        
        return QueryResult(
            success=False,
            data=None,
            row_count=0,
            execution_time=execution_time,
            error_message=error_message,
            cache_hit=False,
            metadata={'error': True}
        )
    
    def _get_query_type(self, query: str) -> str:
        """Determine query type"""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        elif query_upper.startswith('DROP'):
            return 'DROP'
        elif query_upper.startswith('WITH'):
            return 'CTE'
        else:
            return 'OTHER'
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query without executing it
        
        Args:
            query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        with tracer.start_as_current_span("validate_query") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", query)
            output = {"is_valid": False, "error_message": ""}

            try:
                # Basic validation
                if not query or not query.strip():
                    output["error_message"] = "Empty query"
                    span.set_attribute("output.value", json.dumps(output))
                    return False, "Empty query"
                
                # Check for dangerous operations
                dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
                query_upper = query.upper()
                
                for keyword in dangerous_keywords:
                    if keyword in query_upper:
                        # Allow DELETE with WHERE clause for data management
                        if keyword == 'DELETE' and 'WHERE' in query_upper:
                            continue
                        
                        output["error_message"] = f"Dangerous operation '{keyword}' not allowed"
                        span.set_attribute("output.value", json.dumps(output))
                        return False, output["error_message"]
                
                # Try to parse the query using SQLite's EXPLAIN
                with sqlite3.connect(self.database_path) as conn:
                    try:
                        conn.execute(f"EXPLAIN QUERY PLAN {query}")
                        output["is_valid"] = True
                        span.set_attribute("output.value", json.dumps(output))
                        return True, None
                    except sqlite3.Error as e:
                        output["error_message"] = str(e)
                        span.set_attribute("output.value", json.dumps(output))
                        return False, str(e)
                        
            except Exception as e:
                output["error_message"] = f"Validation error: {str(e)}"
                span.set_attribute("output.value", json.dumps(output))
                return False, output["error_message"]
    
    def get_table_schema(self, table_name: str) -> Optional[TableSchema]:
        with tracer.start_as_current_span("get_table_schema") as span:
            """
            Get schema information for a specific table
            
            Args:
                table_name: Name of the table
                
            Returns:
                TableSchema object or None if table doesn't exist
            """
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", table_name)
            try:
                with sqlite3.connect(self.database_path) as conn:
                    # Get table info
                    cursor = conn.execute(f"PRAGMA table_info({table_name})")
                    columns_info = cursor.fetchall()
                    
                    if not columns_info:
                        span.set_attribute("output.value", "null")
                        return None
                    
                    # Format column information
                    columns = []
                    for col_info in columns_info:
                        columns.append({
                            'name': col_info[1],
                            'type': col_info[2],
                            'nullable': not col_info[3],
                            'default': col_info[4],
                            'primary_key': bool(col_info[5])
                        })
                    
                    # Get sample data
                    sample_query = f"SELECT * FROM {table_name} LIMIT 3"
                    sample_result = self.execute_query(sample_query)
                    sample_data = None
                    if sample_result.success and sample_result.data is not None:
                        sample_data = sample_result.data.to_dict('records')
                    
                    schema = TableSchema(
                        table_name=table_name,
                        columns=columns,
                        description=f"Table: {table_name}",
                        sample_data=sample_data
                    )
                    span.set_attribute("output.value", json.dumps(asdict(schema)))
                    return schema
                    
            except Exception as e:
                self.logger.error(f"Error getting schema for table {table_name}: {str(e)}")
                span.set_attribute("output.value", f"Error getting schema for table {table_name}: {str(e)}")
                return None
    
    def list_tables(self) -> List[str]:
        with tracer.start_as_current_span("list_tables") as span:
            """
            Get list of all tables in the database
            
            Returns:
                List of table names
            """
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", self.database_path)
            tables = []
            try:
                with sqlite3.connect(self.database_path) as conn:
                    cursor = conn.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                        ORDER BY name
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    span.set_attribute("output.value", json.dumps(tables))
                    return tables
                    
            except Exception as e:
                self.logger.error(f"Error listing tables: {str(e)}")
                span.set_attribute("output.value", f"Error listing tables: {str(e)}")
                return []
    
    def get_all_schemas(self) -> Dict[str, TableSchema]:
        with tracer.start_as_current_span("get_all_schemas") as span:
            """
            Get schema information for all tables
            
            Returns:
                Dictionary mapping table names to TableSchema objects
            """
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.AGENT.value)
            span.set_attribute("input.value", self.database_path)
            schemas = {}
            tables = self.list_tables()
            
            for table_name in tables:
                schema = self.get_table_schema(table_name)
                if schema:
                    schemas[table_name] = schema
            
            schemas_dict = {k: asdict(v) for k, v in schemas.items()}
            span.set_attribute("output.value", json.dumps(schemas_dict))
            return schemas
    
    def clear_cache(self):
        """Clear query result cache"""
        if self.cache:
            self.cache.clear()
            self.logger.info("Query cache cleared")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        with tracer.start_as_current_span("get_metrics_summary") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", self.database_path)
            """Get performance metrics summary"""
            cache_hit_rate = self.cache_hits / self.query_count if self.query_count > 0 else 0
            avg_execution_time = self.total_execution_time / self.query_count if self.query_count > 0 else 0
            
            metrics = {
                'total_queries': self.query_count,
                'cache_hits': self.cache_hits,
                'cache_hit_rate': cache_hit_rate,
                'error_count': self.error_count,
                'average_execution_time': avg_execution_time,
                'total_execution_time': self.total_execution_time
            }
            
            if self.cache:
                metrics['cache_stats'] = self.cache.get_stats()
            
            span.set_attribute("output.value", json.dumps(metrics))
            return metrics
        
    def execute_script(self, script: str):
        """
        Execute multiple SQL statements from a script
        
        Args:
            script: SQL script with multiple statements
        """
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.executescript(script)
                conn.commit()
            self.logger.info("SQL script executed successfully")
            
        except Exception as e:
            self.logger.error(f"Error executing script: {str(e)}")
            raise
    
    def backup_database(self, backup_path: str):
        """
        Create a backup of the database
        
        Args:
            backup_path: Path for the backup file
        """
        try:
            with sqlite3.connect(self.database_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            self.logger.info(f"Database backed up to {backup_path}")
            
        except Exception as e:
            self.logger.error(f"Error creating backup: {str(e)}")
            raise


# Factory function for easy client creation
def create_sqlite_client(
    database_path: str = "retail_analytics.db",
    enable_cache: bool = True,
    max_results: int = 1000,
    **kwargs
) -> SQLiteClient:
    """
    Factory function to create SQLite client with default configuration
    
    Args:
        database_path: Path to SQLite database file
        enable_cache: Whether to enable query result caching
        max_results: Maximum number of rows to return
        **kwargs: Additional configuration options
        
    Returns:
        Configured SQLiteClient instance
    """
    return SQLiteClient(
        database_path=database_path,
        enable_cache=enable_cache,
        max_results=max_results,
        **kwargs
    )


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create client
    client = create_sqlite_client("test_retail.db")
    
    # Test basic functionality
    print("Testing SQLite Client:")
    print("=" * 30)
    
    # Create a test table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS test_products (
        id INTEGER PRIMARY KEY,
        upc_code TEXT UNIQUE,
        product_name TEXT,
        current_price REAL,
        category TEXT
    )
    """
    
    result = client.execute_query(create_table_sql)
    print(f"Create table result: {result.success}")
    
    # Insert test data
    insert_sql = """
    INSERT OR REPLACE INTO test_products (upc_code, product_name, current_price, category)
    VALUES ('123456', 'Test Product', 9.99, 'Test Category')
    """
    
    result = client.execute_query(insert_sql)
    print(f"Insert result: {result.success}")
    
    # Query data
    select_sql = "SELECT * FROM test_products WHERE upc_code = '123456'"
    result = client.execute_query(select_sql)
    print(f"Select result: {result.success}, rows: {result.row_count}")
    
    if result.success and result.data is not None:
        print("Data:")
        print(result.data)
    
    # Test schema retrieval
    schema = client.get_table_schema('test_products')
    if schema:
        print(f"Schema for test_products: {len(schema.columns)} columns")
    
    # Get metrics
    metrics = client.get_metrics_summary()
    print(f"Metrics: {metrics}")
    
    print("SQLite client test completed!")

