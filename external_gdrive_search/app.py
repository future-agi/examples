"""
Main application file for the LlamaIndex-based search demo.
This module implements a Gradio interface for searching across internal database and Google Drive.
"""

import os
import gradio as gr
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.settings import Settings

from database_connector import DatabaseConnector
from google_drive_connector import GoogleDriveConnector

# Load environment variables
load_dotenv()

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "your-api-key-here")


from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType
from traceai_llamaindex import LlamaIndexInstrumentor

trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="llamaindex_project",
)


LlamaIndexInstrumentor().instrument(tracer_provider=trace_provider)

class SearchDemo:
    """Main class for the search demo application."""
    
    def __init__(self):
        """Initialize the search demo application."""
        self.db_connector = None
        self.drive_connector = None
        self.index = None
        self.query_engine = None
        self.sources = {
            "database": False,
            "google_drive": False
        }
        
        # Initialize LLM and embedding model
        self.llm = OpenAI(model="gpt-4o", temperature=0)
        self.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
        
        # Set global settings for LlamaIndex
        Settings.llm = self.llm
        Settings.embed_model = self.embed_model
        Settings.node_parser = SentenceSplitter(chunk_size=1024, chunk_overlap=100)
    
    def connect_database(self, connection_string: str) -> str:
        """
        Connect to the internal database.
        
        Args:
            connection_string: SQLAlchemy connection string
            
        Returns:
            Status message
        """
        try:
            self.db_connector = DatabaseConnector(connection_string)
            tables = self.db_connector.list_tables()
            self.sources["database"] = True
            return f"Successfully connected to database. Found {len(tables)} tables: {', '.join(tables)}"
        except Exception as e:
            return f"Error connecting to database: {str(e)}"
    
    def connect_google_drive(self, credentials_path: str) -> str:
        """
        Connect to Google Drive.
        
        Args:
            credentials_path: Path to the credentials.json file
            
        Returns:
            Status message
        """
        try:
            self.drive_connector = GoogleDriveConnector(credentials_path)
            files = self.drive_connector.list_files()
            self.sources["google_drive"] = True
            return f"Successfully connected to Google Drive. Found {len(files)} files."
        except Exception as e:
            return f"Error connecting to Google Drive: {str(e)}"
    
    def build_index(self) -> str:
        """
        Build the search index from all connected sources.
        
        Returns:
            Status message
        """
        documents = []
        status_messages = []
        
        # Get documents from database if connected
        if self.sources["database"] and self.db_connector:
            try:
                db_docs = self.db_connector.get_all_documents()
                documents.extend(db_docs)
                status_messages.append(f"Added {len(db_docs)} documents from database.")
            except Exception as e:
                status_messages.append(f"Error loading database documents: {str(e)}")
        
        # Get documents from Google Drive if connected
        if self.sources["google_drive"] and self.drive_connector:
            try:
                drive_docs = self.drive_connector.get_documents()
                documents.extend(drive_docs)
                status_messages.append(f"Added {len(drive_docs)} documents from Google Drive.")
            except Exception as e:
                status_messages.append(f"Error loading Google Drive documents: {str(e)}")
        
        # Build the index if we have documents
        if documents:
            try:
                self.index = VectorStoreIndex.from_documents(
                    documents
                )
                
                # Set up retriever with similarity threshold
                retriever = VectorIndexRetriever(
                    index=self.index,
                    similarity_top_k=5
                )
                
                # Set up query engine with similarity filter
                self.query_engine = RetrieverQueryEngine.from_args(
                    retriever=retriever,
                    node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.2)]
                )
                
                status_messages.append(f"Successfully built index with {len(documents)} documents.")
            except Exception as e:
                status_messages.append(f"Error building index: {str(e)}")
        else:
            status_messages.append("No documents found to index.")
        
        return "\n".join(status_messages)
    
    def search(self, query: str) -> Tuple[str, str]:
        """
        Perform a semantic search using RAG.
        
        Args:
            query: Search query
            
        Returns:
            Tuple of (answer, sources)
        """
        if not self.query_engine:
            return "Please build the index first.", "No sources available."
        
        try:
            # Execute the query
            response = self.query_engine.query(query)

            # Handle different response types
            answer = None
            response_val = getattr(response, 'response', None)
            response_txt_val = getattr(response, 'response_txt', None)
            if isinstance(response_val, str):
                answer = response_val
            elif response_txt_val:
                answer = response_txt_val
            elif response_val is not None:
                answer = str(response_val)
            else:
                answer = str(response)

            # Format the sources
            sources_text = "Sources:\n"
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    source_type = node.metadata.get("source", "unknown")
                    if source_type == "google_drive":
                        sources_text += f"- Google Drive: {node.metadata.get('file_name', 'Unknown file')}\n"
                    else:
                        table_name = node.metadata.get("table_name", "Unknown table")
                        sources_text += f"- Database: {table_name}\n"
            return answer, sources_text
        except Exception as e:
            return f"Error performing search: {str(e)}", "No sources available."

# Create the Gradio interface
def create_interface():
    """Create and launch the Gradio interface."""
    demo = SearchDemo()
    
    with gr.Blocks(title="LlamaIndex Search Demo") as interface:
        gr.Markdown("# LlamaIndex Search Demo")
        gr.Markdown("Search across your internal knowledge database and Google Drive files using semantic search with RAG.")
        
        with gr.Tab("Setup"):
            gr.Markdown("## 1. Connect to Data Sources")
            
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Database Connection")
                    db_connection = gr.Textbox(
                        label="Database Connection String",
                        placeholder="postgresql://user:password@localhost:5432/dbname",
                        type="password"
                    )
                    db_connect_btn = gr.Button("Connect to Database")
                    db_status = gr.Textbox(label="Database Status", interactive=False)
                
                with gr.Column():
                    gr.Markdown("### Google Drive Connection")
                    drive_creds = gr.Textbox(
                        label="Path to credentials.json",
                        placeholder="/path/to/credentials.json",
                        value="credentials.json"
                    )
                    drive_connect_btn = gr.Button("Connect to Google Drive")
                    drive_status = gr.Textbox(label="Google Drive Status", interactive=False)
            
            gr.Markdown("## 2. Build Search Index")
            build_index_btn = gr.Button("Build Index")
            index_status = gr.Textbox(label="Index Status", interactive=False)
            
            # Connect event handlers for setup tab
            db_connect_btn.click(demo.connect_database, inputs=[db_connection], outputs=[db_status])
            drive_connect_btn.click(demo.connect_google_drive, inputs=[drive_creds], outputs=[drive_status])
            build_index_btn.click(demo.build_index, inputs=[], outputs=[index_status])
        
        with gr.Tab("Search"):
            gr.Markdown("## Search Your Knowledge Base")
            query_input = gr.Textbox(
                label="Enter your query",
                placeholder="What is the status of project X?",
                lines=2
            )
            search_btn = gr.Button("Search")
            
            with gr.Row():
                with gr.Column():
                    answer_output = gr.Textbox(label="Answer", interactive=False, lines=10)
                with gr.Column():
                    sources_output = gr.Textbox(label="Sources", interactive=False, lines=10)
            
            # Connect event handler for search tab
            search_btn.click(demo.search, inputs=[query_input], outputs=[answer_output, sources_output])
        
        with gr.Tab("Help"):
            gr.Markdown("""
            ## Setup Instructions
            
            ### Database Connection
            1. Enter your database connection string in the format: `dialect://username:password@host:port/database`
            2. Examples:
               - PostgreSQL: `postgresql://user:password@localhost:5432/dbname`
               - MySQL: `mysql+pymysql://user:password@localhost:3306/dbname`
               - SQLite: `sqlite:///path/to/database.db`
            3. Click "Connect to Database"
            
            ### Google Drive Connection
            1. Create a Google Cloud project and enable the Google Drive API
            2. Create OAuth 2.0 credentials and download the credentials.json file
            3. Place the credentials.json file in the application directory
            4. Enter the path to the credentials.json file
            5. Click "Connect to Google Drive"
            6. Follow the authentication flow in your browser
            
            ### Building the Index
            1. After connecting to your data sources, click "Build Index"
            2. This process may take some time depending on the amount of data
            
            ### Searching
            1. Enter your query in the search box
            2. Click "Search"
            3. View the answer and sources
            
            ## Google Drive API Setup Instructions
            
            1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
            2. Create a new project or select an existing one
            3. Enable the Google Drive API:
               - In the sidebar, click on "APIs & Services" > "Library"
               - Search for "Google Drive API" and click on it
               - Click "Enable"
            4. Create credentials:
               - In the sidebar, click on "APIs & Services" > "Credentials"
               - Click "Create Credentials" and select "OAuth client ID"
               - Select "Desktop app" as the application type
               - Enter a name for your OAuth client
               - Click "Create"
            5. Download the credentials:
               - In the OAuth 2.0 Client IDs section, find your newly created client
               - Click the download icon (⬇️) to download the credentials.json file
            6. Place the credentials.json file in the application directory
            """)
    
    return interface

if __name__ == "__main__":
    interface = create_interface()
    interface.launch(share=True)
