"""
Google Drive connector for LlamaIndex to integrate with Google Drive files.
This module provides functionality to connect to Google Drive and load its content into LlamaIndex.
"""

import os
import io
import pickle
import logging
from typing import List, Optional, Dict, Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload
from llama_index.core import Document
from dotenv import load_dotenv

load_dotenv()

# Define the scopes for Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Set up logging
logging.basicConfig(level=logging.INFO)

class GoogleDriveConnector:
    """Class to connect to and extract data from Google Drive for indexing."""
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize the Google Drive connector.
        
        Args:
            credentials_path: Path to the credentials.json file. If None, will try to load from environment.
            token_path: Path to save/load the token.pickle file. If None, will use default location.
        """
        if credentials_path is None:
            credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        
        if token_path is None:
            token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.pickle")
        
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API."""
        creds = None
        
        # Check if token.pickle exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If credentials don't exist or are invalid, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build the Drive API service
        return build('drive', 'v3', credentials=creds)
    
    def list_files(self, folder_id: Optional[str] = None, file_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List files in Google Drive, optionally filtered by folder and file types.
        
        Args:
            folder_id: ID of the folder to search in. If None, searches in root.
            file_types: List of MIME types to filter by. If None, returns all files.
            
        Returns:
            List of file metadata dictionaries
        """
        logging.info(f"Listing files from Google Drive (folder_id={folder_id}, file_types={file_types})")
        query_parts = []
        
        # Add folder constraint if specified
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        
        # Add file type constraints if specified
        if file_types:
            mime_type_conditions = [f"mimeType='{mime_type}'" for mime_type in file_types]
            query_parts.append(f"({' or '.join(mime_type_conditions)})")
        
        # Exclude folders from results
        query_parts.append("mimeType != 'application/vnd.google-apps.folder'")
        
        # Combine all query parts
        query = " and ".join(query_parts)
        
        # Execute the query
        results = self.service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name, mimeType, createdTime, modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        logging.info(f"Found {len(files)} files from Google Drive.")
        return files
    
    def list_folders(self, parent_folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List folders in Google Drive, optionally within a specific parent folder.
        
        Args:
            parent_folder_id: ID of the parent folder. If None, lists folders in root.
            
        Returns:
            List of folder metadata dictionaries
        """
        query = "mimeType = 'application/vnd.google-apps.folder'"
        
        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"
        
        results = self.service.files().list(
            q=query,
            pageSize=1000,
            fields="nextPageToken, files(id, name)"
        ).execute()
        
        return results.get('files', [])
    
    def download_file(self, file_id: str) -> bytes:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: ID of the file to download
            
        Returns:
            File content as bytes
        """
        request = self.service.files().get_media(fileId=file_id)
        file_content = io.BytesIO()
        downloader = MediaIoBaseDownload(file_content, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        return file_content.getvalue()
    
    def get_document_from_file(self, file_id: str, file_name: str, mime_type: str) -> Document:
        """
        Create a Document object from a Google Drive file.
        
        Args:
            file_id: ID of the file
            file_name: Name of the file
            mime_type: MIME type of the file
            
        Returns:
            Document object
        """
        # Handle Google Docs/Sheets/Slides export
        export_mime_map = {
            'application/vnd.google-apps.document': 'text/plain',
            'application/vnd.google-apps.spreadsheet': 'text/csv',
            'application/vnd.google-apps.presentation': 'text/plain',
        }
        text_content = ""
        if mime_type in export_mime_map:
            export_mime = export_mime_map[mime_type]
            try:
                content = self.service.files().export(fileId=file_id, mimeType=export_mime).execute()
                text_content = content.decode('utf-8', errors='replace') if isinstance(content, bytes) else content
            except Exception as e:
                text_content = f"Error exporting file: {file_name} ({mime_type}): {e}"
        else:
            content = self.download_file(file_id)
            # Convert content to string if it's a text-based file
            if mime_type in [
                'text/plain', 
                'text/csv', 
                'text/html', 
                'application/json',
                'application/xml'
            ]:
                text_content = content.decode('utf-8', errors='replace')
            else:
                # For binary files, just note that it's binary content
                text_content = f"Binary content of file: {file_name} (MIME type: {mime_type})"
        # Create metadata
        metadata = {
            "file_id": file_id,
            "file_name": file_name,
            "mime_type": mime_type,
            "source": "google_drive"
        }
        return Document(text=text_content, metadata=metadata)
    
    def get_documents(self, folder_id: Optional[str] = None, 
                     file_types: Optional[List[str]] = None) -> List[Document]:
        """
        Get documents from Google Drive files.
        
        Args:
            folder_id: ID of the folder to search in. If None, searches in root.
            file_types: List of MIME types to filter by. If None, returns all files.
            
        Returns:
            List of Document objects
        """
        logging.info(f"Indexing documents from Google Drive (folder_id={folder_id}, file_types={file_types})")
        files = self.list_files(folder_id, file_types)
        LIMIT = 10  # or 10
        if len(files) > LIMIT:
            logging.info(f"Limiting indexing to first {LIMIT} files out of {len(files)} available.")
            files = files[:LIMIT]
        documents = []
        failed = 0
        for idx, file in enumerate(files, 1):
            logging.info(f"Processing file {idx}/{len(files)}: {file['name']} (id={file['id']})")
            try:
                doc = self.get_document_from_file(
                    file_id=file['id'],
                    file_name=file['name'],
                    mime_type=file['mimeType']
                )
                documents.append(doc)
            except Exception as e:
                logging.error(f"Error processing file {file['name']}: {e}")
                failed += 1
        logging.info(f"Indexed {len(documents)} documents from Google Drive. Failed to process {failed} files.")
        return documents

# Example usage
if __name__ == "__main__":
    # For testing purposes
    connector = GoogleDriveConnector()
    files = connector.list_files()
    print(f"Available files: {len(files)}")
