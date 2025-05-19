"""
Database connector for LlamaIndex to integrate with internal knowledge database.
This module provides functionality to connect to a database and load its content into LlamaIndex.
"""

import os
from typing import List, Optional
from sqlalchemy import create_engine, MetaData, Table, select, text
from llama_index.core import Document
from llama_index.readers.database import DatabaseReader
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnector:
    """Class to connect to and extract data from a database for indexing."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the database connector.
        
        Args:
            connection_string: SQLAlchemy connection string. If None, will try to load from environment.
        """
        if connection_string is None:
            # Try to load from environment variables
            db_type = os.getenv("DB_TYPE", "postgresql")
            db_user = os.getenv("DB_USER", "postgres")
            db_password = os.getenv("DB_PASSWORD", "password")
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME", "knowledge_db")
            
            connection_string = f"{db_type}://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self.connection_string = connection_string
        self.engine = create_engine(connection_string)
        self.metadata = MetaData()
        self.reader = DatabaseReader(self.engine)
    
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        self.metadata.reflect(bind=self.engine)
        return list(self.metadata.tables.keys())
    
    def get_documents_from_table(self, table_name: str, content_columns: List[str], 
                                metadata_columns: Optional[List[str]] = None) -> List[Document]:
        """
        Extract documents from a specific table.
        
        Args:
            table_name: Name of the table to extract data from
            content_columns: Columns to use as document content
            metadata_columns: Columns to include as document metadata
            
        Returns:
            List of Document objects
        """
        query = f"SELECT * FROM {table_name}"
        documents = self.reader.load_data(query=query, content_columns=content_columns, metadata_columns=metadata_columns)
        return documents
    
    def get_documents_from_query(self, query: str, content_columns: List[str],
                               metadata_columns: Optional[List[str]] = None) -> List[Document]:
        """
        Extract documents from a custom SQL query.
        
        Args:
            query: SQL query to execute
            content_columns: Columns to use as document content
            metadata_columns: Columns to include as document metadata
            
        Returns:
            List of Document objects
        """
        documents = self.reader.load_data(query=query, content_columns=content_columns, metadata_columns=metadata_columns)
        return documents
    
    def get_all_documents(self, content_column_map: Optional[dict] = None) -> List[Document]:
        """
        Extract documents from all tables in the database.
        
        Args:
            content_column_map: Dictionary mapping table names to content columns
            
        Returns:
            List of Document objects
        """
        all_documents = []
        tables = self.list_tables()
        
        if content_column_map is None:
            content_column_map = {}
        
        for table_name in tables:
            try:
                # If table is in content_column_map, use those columns, otherwise use all columns
                if table_name in content_column_map:
                    content_cols = content_column_map[table_name]
                else:
                    # Get all column names for this table
                    table = Table(table_name, self.metadata, autoload_with=self.engine)
                    content_cols = [col.name for col in table.columns]
                
                # Get documents from this table
                docs = self.get_documents_from_table(table_name, content_cols)
                all_documents.extend(docs)
            except Exception as e:
                print(f"Error processing table {table_name}: {e}")
        
        return all_documents

# Example usage
if __name__ == "__main__":
    # For testing purposes
    connector = DatabaseConnector()
    tables = connector.list_tables()
    print(f"Available tables: {tables}")
