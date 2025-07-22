"""
BigQuery Integration and Query Execution System for Text-to-SQL Agent

This module handles all BigQuery operations including connection management,
query execution, result processing, and caching.
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from google.cloud import bigquery
from google.cloud.exceptions import NotFound, BadRequest, Forbidden
from google.oauth2 import service_account
import hashlib
import pickle


@dataclass
class QueryResult:
    """Result of a BigQuery execution"""
    success: bool
    data: Optional[pd.DataFrame]
    row_count: int
    execution_time: float
    query_job_id: str
    error_message: Optional[str]
    bytes_processed: int
    bytes_billed: int
    cache_hit: bool
    metadata: Dict[str, Any]


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    execution_time: float
    bytes_processed: int
    bytes_billed: int
    row_count: int
    cache_hit: bool
    timestamp: datetime
    success: bool
    error_type: Optional[str]


class QueryCache:
    """Caches query results to improve performance"""
    
    def __init__(self, cache_dir: str = "./query_cache", ttl_hours: int = 24):
        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load cache index
        self.cache_index_file = os.path.join(cache_dir, "cache_index.json")
        self.cache_index = self._load_cache_index()
    
    def _load_cache_index(self) -> Dict[str, Dict]:
        """Load cache index from disk"""
        try:
            if os.path.exists(self.cache_index_file):
                with open(self.cache_index_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load cache index: {str(e)}")
        
        return {}
    
    def _save_cache_index(self):
        """Save cache index to disk"""
        try:
            with open(self.cache_index_file, 'w') as f:
                json.dump(self.cache_index, f, default=str)
        except Exception as e:
            self.logger.warning(f"Could not save cache index: {str(e)}")
    
    def _get_query_hash(self, sql_query: str) -> str:
        """Generate hash for SQL query"""
        return hashlib.md5(sql_query.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        try:
            cached_time = datetime.fromisoformat(cache_entry['timestamp'])
            expiry_time = cached_time + timedelta(hours=self.ttl_hours)
            return datetime.now() < expiry_time
        except:
            return False
    
    def get(self, sql_query: str) -> Optional[QueryResult]:
        """Get cached result for query"""
        query_hash = self._get_query_hash(sql_query)
        
        if query_hash not in self.cache_index:
            return None
        
        cache_entry = self.cache_index[query_hash]
        
        if not self._is_cache_valid(cache_entry):
            # Remove expired entry
            self._remove_cache_entry(query_hash)
            return None
        
        try:
            # Load cached result
            cache_file = os.path.join(self.cache_dir, f"{query_hash}.pkl")
            with open(cache_file, 'rb') as f:
                cached_result = pickle.load(f)
            
            # Mark as cache hit
            cached_result.cache_hit = True
            
            self.logger.info(f"Cache hit for query hash: {query_hash}")
            return cached_result
            
        except Exception as e:
            self.logger.warning(f"Could not load cached result: {str(e)}")
            self._remove_cache_entry(query_hash)
            return None
    
    def put(self, sql_query: str, result: QueryResult):
        """Cache query result"""
        query_hash = self._get_query_hash(sql_query)
        
        try:
            # Save result to file
            cache_file = os.path.join(self.cache_dir, f"{query_hash}.pkl")
            with open(cache_file, 'wb') as f:
                pickle.dump(result, f)
            
            # Update cache index
            self.cache_index[query_hash] = {
                'timestamp': datetime.now().isoformat(),
                'row_count': result.row_count,
                'bytes_processed': result.bytes_processed,
                'execution_time': result.execution_time
            }
            
            self._save_cache_index()
            
            self.logger.info(f"Cached result for query hash: {query_hash}")
            
        except Exception as e:
            self.logger.warning(f"Could not cache result: {str(e)}")
    
    def _remove_cache_entry(self, query_hash: str):
        """Remove cache entry"""
        try:
            # Remove from index
            if query_hash in self.cache_index:
                del self.cache_index[query_hash]
                self._save_cache_index()
            
            # Remove cache file
            cache_file = os.path.join(self.cache_dir, f"{query_hash}.pkl")
            if os.path.exists(cache_file):
                os.remove(cache_file)
                
        except Exception as e:
            self.logger.warning(f"Could not remove cache entry: {str(e)}")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        expired_hashes = []
        
        for query_hash, cache_entry in self.cache_index.items():
            if not self._is_cache_valid(cache_entry):
                expired_hashes.append(query_hash)
        
        for query_hash in expired_hashes:
            self._remove_cache_entry(query_hash)
        
        self.logger.info(f"Cleared {len(expired_hashes)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache_index)
        total_size = 0
        
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.pkl'):
                    filepath = os.path.join(self.cache_dir, filename)
                    total_size += os.path.getsize(filepath)
        except:
            pass
        
        return {
            'total_entries': total_entries,
            'total_size_mb': total_size / (1024 * 1024),
            'ttl_hours': self.ttl_hours
        }


class BigQueryClient:
    """BigQuery client with advanced features"""
    
    def __init__(self, 
                 project_id: Optional[str] = None,
                 credentials_path: Optional[str] = None,
                 dataset_id: Optional[str] = None,
                 enable_cache: bool = True,
                 max_results: int = 10000):
        """
        Initialize BigQuery client
        
        Args:
            project_id: GCP project ID
            credentials_path: Path to service account JSON file
            dataset_id: Default dataset ID
            enable_cache: Whether to enable query caching
            max_results: Maximum number of results to return
        """
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.dataset_id = dataset_id or os.getenv('BIGQUERY_DATASET')
        self.max_results = max_results
        self.logger = logging.getLogger(__name__)
        
        # Initialize BigQuery client
        self.client = self._initialize_client(credentials_path)
        
        # Initialize cache
        self.cache = QueryCache() if enable_cache else None
        
        # Query metrics tracking
        self.metrics: List[QueryMetrics] = []
        
        self.logger.info(f"BigQuery client initialized for project: {self.project_id}")
    
    def _initialize_client(self, credentials_path: Optional[str]) -> bigquery.Client:
        """Initialize BigQuery client with credentials"""
        try:
            if credentials_path and os.path.exists(credentials_path):
                # Use service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path
                )
                return bigquery.Client(
                    project=self.project_id,
                    credentials=credentials
                )
            else:
                # Use default credentials (environment-based)
                return bigquery.Client(project=self.project_id)
                
        except Exception as e:
            self.logger.error(f"Failed to initialize BigQuery client: {str(e)}")
            # Return a mock client for development/testing
            return self._create_mock_client()
    
    def _create_mock_client(self):
        """Create a mock client for development/testing"""
        class MockClient:
            def query(self, sql, **kwargs):
                # Return mock job for testing
                class MockJob:
                    def __init__(self):
                        self.job_id = "mock_job_123"
                        self.total_bytes_processed = 1024
                        self.total_bytes_billed = 1024
                        self.cache_hit = False
                    
                    def result(self):
                        # Return mock results
                        return []
                    
                    def to_dataframe(self):
                        return pd.DataFrame({
                            'mock_column': ['mock_value_1', 'mock_value_2'],
                            'mock_number': [1, 2]
                        })
                
                return MockJob()
        
        self.logger.warning("Using mock BigQuery client for development")
        return MockClient()
    
    def execute_query(self, sql_query: str, use_cache: bool = True) -> QueryResult:
        """
        Execute SQL query against BigQuery
        
        Args:
            sql_query: SQL query to execute
            use_cache: Whether to use cached results
            
        Returns:
            QueryResult object with execution details
        """
        start_time = time.time()
        query_hash = hashlib.md5(sql_query.encode()).hexdigest()
        
        # Check cache first
        if use_cache and self.cache:
            cached_result = self.cache.get(sql_query)
            if cached_result:
                return cached_result
        
        try:
            # Configure query job
            job_config = bigquery.QueryJobConfig(
                maximum_bytes_billed=100 * 1024 * 1024,  # 100MB limit
                use_query_cache=True,
                dry_run=False
            )
            
            # Execute query
            query_job = self.client.query(sql_query, job_config=job_config)
            
            # Wait for completion with timeout
            query_job.result(timeout=300)  # 5 minute timeout
            
            # Get results as DataFrame
            df = query_job.to_dataframe()
            
            # Limit results if necessary
            if len(df) > self.max_results:
                df = df.head(self.max_results)
                self.logger.warning(f"Results limited to {self.max_results} rows")
            
            execution_time = time.time() - start_time
            
            # Create result object
            result = QueryResult(
                success=True,
                data=df,
                row_count=len(df),
                execution_time=execution_time,
                query_job_id=query_job.job_id,
                error_message=None,
                bytes_processed=query_job.total_bytes_processed or 0,
                bytes_billed=query_job.total_bytes_billed or 0,
                cache_hit=query_job.cache_hit or False,
                metadata={
                    'query_hash': query_hash,
                    'timestamp': datetime.now().isoformat(),
                    'project_id': self.project_id,
                    'dataset_id': self.dataset_id
                }
            )
            
            # Cache successful results
            if use_cache and self.cache and result.success:
                self.cache.put(sql_query, result)
            
            # Track metrics
            self._track_metrics(result, sql_query)
            
            self.logger.info(f"Query executed successfully: {result.row_count} rows, {execution_time:.2f}s")
            return result
            
        except BadRequest as e:
            return self._handle_query_error(e, "Bad Request", sql_query, start_time, query_hash)
        except Forbidden as e:
            return self._handle_query_error(e, "Forbidden", sql_query, start_time, query_hash)
        except Exception as e:
            return self._handle_query_error(e, "Unknown Error", sql_query, start_time, query_hash)
    
    def _handle_query_error(self, error: Exception, error_type: str, 
                          sql_query: str, start_time: float, query_hash: str) -> QueryResult:
        """Handle query execution errors"""
        execution_time = time.time() - start_time
        error_message = str(error)
        
        self.logger.error(f"Query execution failed ({error_type}): {error_message}")
        
        result = QueryResult(
            success=False,
            data=None,
            row_count=0,
            execution_time=execution_time,
            query_job_id="",
            error_message=error_message,
            bytes_processed=0,
            bytes_billed=0,
            cache_hit=False,
            metadata={
                'query_hash': query_hash,
                'timestamp': datetime.now().isoformat(),
                'error_type': error_type
            }
        )
        
        # Track error metrics
        self._track_metrics(result, sql_query, error_type)
        
        return result
    
    def _track_metrics(self, result: QueryResult, sql_query: str, error_type: Optional[str] = None):
        """Track query metrics"""
        try:
            metrics = QueryMetrics(
                query_hash=result.metadata.get('query_hash', ''),
                execution_time=result.execution_time,
                bytes_processed=result.bytes_processed,
                bytes_billed=result.bytes_billed,
                row_count=result.row_count,
                cache_hit=result.cache_hit,
                timestamp=datetime.now(),
                success=result.success,
                error_type=error_type
            )
            
            self.metrics.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics) > 1000:
                self.metrics = self.metrics[-1000:]
                
        except Exception as e:
            self.logger.warning(f"Could not track metrics: {str(e)}")
    
    def validate_query(self, sql_query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate SQL query without executing it
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Use dry run to validate query
            job_config = bigquery.QueryJobConfig(dry_run=True)
            query_job = self.client.query(sql_query, job_config=job_config)
            
            # If we get here, query is valid
            return True, None
            
        except BadRequest as e:
            return False, str(e)
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def get_table_schema(self, table_name: str, dataset_id: Optional[str] = None) -> Optional[Dict]:
        """
        Get schema information for a table
        
        Args:
            table_name: Name of the table
            dataset_id: Dataset ID (uses default if not provided)
            
        Returns:
            Dictionary with schema information
        """
        try:
            dataset_id = dataset_id or self.dataset_id
            table_ref = self.client.dataset(dataset_id).table(table_name)
            table = self.client.get_table(table_ref)
            
            schema_info = {
                'table_name': table_name,
                'dataset_id': dataset_id,
                'num_rows': table.num_rows,
                'num_bytes': table.num_bytes,
                'created': table.created.isoformat() if table.created else None,
                'modified': table.modified.isoformat() if table.modified else None,
                'columns': []
            }
            
            for field in table.schema:
                column_info = {
                    'name': field.name,
                    'type': field.field_type,
                    'mode': field.mode,
                    'description': field.description or ''
                }
                schema_info['columns'].append(column_info)
            
            return schema_info
            
        except NotFound:
            self.logger.warning(f"Table not found: {dataset_id}.{table_name}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting table schema: {str(e)}")
            return None
    
    def list_tables(self, dataset_id: Optional[str] = None) -> List[str]:
        """
        List all tables in a dataset
        
        Args:
            dataset_id: Dataset ID (uses default if not provided)
            
        Returns:
            List of table names
        """
        try:
            dataset_id = dataset_id or self.dataset_id
            dataset_ref = self.client.dataset(dataset_id)
            tables = self.client.list_tables(dataset_ref)
            
            return [table.table_id for table in tables]
            
        except Exception as e:
            self.logger.error(f"Error listing tables: {str(e)}")
            return []
    
    def get_sample_data(self, table_name: str, limit: int = 5, 
                       dataset_id: Optional[str] = None) -> Optional[pd.DataFrame]:
        """
        Get sample data from a table
        
        Args:
            table_name: Name of the table
            limit: Number of sample rows
            dataset_id: Dataset ID (uses default if not provided)
            
        Returns:
            DataFrame with sample data
        """
        try:
            dataset_id = dataset_id or self.dataset_id
            sql_query = f"SELECT * FROM `{self.project_id}.{dataset_id}.{table_name}` LIMIT {limit}"
            
            result = self.execute_query(sql_query, use_cache=False)
            
            if result.success:
                return result.data
            else:
                self.logger.warning(f"Could not get sample data: {result.error_message}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting sample data: {str(e)}")
            return None
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of query metrics"""
        if not self.metrics:
            return {'total_queries': 0}
        
        successful_queries = [m for m in self.metrics if m.success]
        failed_queries = [m for m in self.metrics if not m.success]
        
        return {
            'total_queries': len(self.metrics),
            'successful_queries': len(successful_queries),
            'failed_queries': len(failed_queries),
            'success_rate': len(successful_queries) / len(self.metrics) if self.metrics else 0,
            'avg_execution_time': np.mean([m.execution_time for m in successful_queries]) if successful_queries else 0,
            'total_bytes_processed': sum(m.bytes_processed for m in successful_queries),
            'total_bytes_billed': sum(m.bytes_billed for m in successful_queries),
            'cache_hit_rate': len([m for m in self.metrics if m.cache_hit]) / len(self.metrics) if self.metrics else 0
        }
    
    def clear_cache(self):
        """Clear query cache"""
        if self.cache:
            self.cache.clear_expired()
            self.logger.info("Query cache cleared")


# Example usage and testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize BigQuery client (will use mock client if no credentials)
    bq_client = BigQueryClient(
        project_id="test-project",
        dataset_id="retail_analytics"
    )
    
    # Test query execution
    test_query = """
    SELECT 
        upc_code,
        current_price,
        suggested_price
    FROM pricing 
    WHERE zone = 'Banner 2' 
    AND week_ending = '2025-04-15'
    LIMIT 10
    """
    
    result = bq_client.execute_query(test_query)
    
    print(f"Query success: {result.success}")
    print(f"Row count: {result.row_count}")
    print(f"Execution time: {result.execution_time:.2f}s")
    
    if result.success and result.data is not None:
        print("Sample data:")
        print(result.data.head())
    else:
        print(f"Error: {result.error_message}")
    
    # Print metrics summary
    metrics = bq_client.get_metrics_summary()
    print(f"Metrics: {metrics}")

