"""
Test script for the LlamaIndex-based search demo.
This script tests the functionality of the search demo across both database and Google Drive sources.
"""

import os
import sys
from dotenv import load_dotenv
from database_connector import DatabaseConnector
from google_drive_connector import GoogleDriveConnector
from app import SearchDemo

# Load environment variables
load_dotenv()

def test_database_connector():
    """Test the database connector functionality."""
    print("\n=== Testing Database Connector ===")
    
    # Get connection string from environment or use a test one
    connection_string = os.getenv("TEST_DB_CONNECTION_STRING")
    
    if not connection_string:
        print("No test database connection string found in environment.")
        print("Skipping database connector test.")
        return False
    
    try:
        # Initialize connector
        print("Initializing database connector...")
        db_connector = DatabaseConnector(connection_string)
        
        # List tables
        print("Listing tables...")
        tables = db_connector.list_tables()
        print(f"Found {len(tables)} tables: {tables}")
        
        # Get documents from a table if available
        if tables:
            print(f"Getting documents from table '{tables[0]}'...")
            docs = db_connector.get_documents_from_table(tables[0], [tables[0]])
            print(f"Retrieved {len(docs)} documents from table '{tables[0]}'")
        
        print("Database connector test completed successfully.")
        return True
    except Exception as e:
        print(f"Error testing database connector: {e}")
        return False

def test_google_drive_connector():
    """Test the Google Drive connector functionality."""
    print("\n=== Testing Google Drive Connector ===")
    
    # Get credentials path from environment or use default
    credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    
    if not os.path.exists(credentials_path):
        print(f"Google Drive credentials file not found at {credentials_path}")
        print("Skipping Google Drive connector test.")
        return False
    
    try:
        # Initialize connector
        print("Initializing Google Drive connector...")
        drive_connector = GoogleDriveConnector(credentials_path)
        
        # List files
        print("Listing files...")
        files = drive_connector.list_files()
        print(f"Found {len(files)} files")
        
        # Get documents if files are available
        if files:
            print("Getting documents from files...")
            docs = drive_connector.get_documents()
            print(f"Retrieved {len(docs)} documents from Google Drive")
        
        print("Google Drive connector test completed successfully.")
        return True
    except Exception as e:
        print(f"Error testing Google Drive connector: {e}")
        return False

def test_search_demo():
    """Test the search demo functionality."""
    print("\n=== Testing Search Demo ===")
    
    try:
        # Initialize demo
        print("Initializing search demo...")
        demo = SearchDemo()
        
        # Test database connection if available
        connection_string = os.getenv("TEST_DB_CONNECTION_STRING")
        if connection_string:
            print("Testing database connection...")
            result = demo.connect_database(connection_string)
            print(f"Database connection result: {result}")
        
        # Test Google Drive connection if available
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if os.path.exists(credentials_path):
            print("Testing Google Drive connection...")
            result = demo.connect_google_drive(credentials_path)
            print(f"Google Drive connection result: {result}")
        
        # Build index if at least one source is connected
        if demo.sources["database"] or demo.sources["google_drive"]:
            print("Building index...")
            result = demo.build_index()
            print(f"Index building result: {result}")
            
            # Test search if index was built
            if demo.query_engine:
                print("Testing search...")
                test_queries = [
                    "What are the latest project updates?",
                    "Who is responsible for the marketing campaign?",
                    "What is the status of the budget?"
                ]
                
                for query in test_queries:
                    print(f"\nQuery: {query}")
                    answer, sources = demo.search(query)
                    print(f"Answer: {answer}")
                    print(f"Sources: {sources}")
        
        print("Search demo test completed.")
        return True
    except Exception as e:
        print(f"Error testing search demo: {e}")
        return False

def main():
    """Main test function."""
    print("=== LlamaIndex Search Demo Test ===")
    
    # Create a .env file with test credentials if it doesn't exist
    if not os.path.exists(".env"):
        print("Creating sample .env file...")
        with open(".env", "w") as f:
            f.write("# OpenAI API Key\n")
            f.write("OPENAI_API_KEY=your-openai-api-key\n\n")
            f.write("# Database Connection\n")
            f.write("DB_TYPE=postgresql\n")
            f.write("DB_USER=postgres\n")
            f.write("DB_PASSWORD=password\n")
            f.write("DB_HOST=localhost\n")
            f.write("DB_PORT=5432\n")
            f.write("DB_NAME=knowledge_db\n\n")
            f.write("# Test Database Connection String\n")
            f.write("TEST_DB_CONNECTION_STRING=sqlite:///test_database.db\n\n")
            f.write("# Google Drive\n")
            f.write("GOOGLE_CREDENTIALS_PATH=credentials.json\n")
            f.write("GOOGLE_TOKEN_PATH=token.pickle\n")
    
    # Run tests
    db_result = test_database_connector()
    drive_result = test_google_drive_connector()
    demo_result = test_search_demo()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Database Connector: {'PASS' if db_result else 'FAIL/SKIP'}")
    print(f"Google Drive Connector: {'PASS' if drive_result else 'FAIL/SKIP'}")
    print(f"Search Demo: {'PASS' if demo_result else 'FAIL'}")
    
    if not (db_result or drive_result):
        print("\nWARNING: Neither database nor Google Drive tests were successful.")
        print("Please check your credentials and try again.")
    
    print("\nTest completed.")

if __name__ == "__main__":
    main()
