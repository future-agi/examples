# API Documentation - NotebookLM Open Source

This document provides comprehensive documentation for the NotebookLM REST API, including endpoints, request/response formats, authentication, and usage examples.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL and Headers](#base-url-and-headers)
3. [Error Handling](#error-handling)
4. [Rate Limiting](#rate-limiting)
5. [API Endpoints](#api-endpoints)
6. [WebSocket Events](#websocket-events)
7. [SDK Examples](#sdk-examples)

## Authentication

NotebookLM uses JWT (JSON Web Token) authentication. All protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow

1. **Register** or **Login** to obtain a JWT token
2. **Include token** in subsequent requests
3. **Refresh token** when it expires

### Token Format
```
Authorization: Bearer <jwt_token>
```

### Token Expiration
- **Access Token**: 1 hour (configurable)
- **Refresh Token**: 30 days (configurable)

## Base URL and Headers

### Base URL
```
http://localhost:5050/api  # Development
https://your-domain.com/api  # Production
```

### Required Headers
```http
Content-Type: application/json
Authorization: Bearer <jwt_token>  # For protected endpoints
```

### Optional Headers
```http
X-Request-ID: <unique_request_id>  # For request tracking
User-Agent: NotebookLM-Client/1.0
```

## Error Handling

### Error Response Format
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {
      "field": "Additional error details"
    }
  },
  "request_id": "req_123456789"
}
```

### HTTP Status Codes
- **200**: Success
- **201**: Created
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **429**: Rate Limited
- **500**: Internal Server Error

### Common Error Codes
- `INVALID_TOKEN`: JWT token is invalid or expired
- `MISSING_FIELD`: Required field is missing
- `VALIDATION_ERROR`: Input validation failed
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `PERMISSION_DENIED`: User lacks required permissions
- `RATE_LIMITED`: Too many requests

## Rate Limiting

### Default Limits
- **Authenticated Users**: 1000 requests/hour
- **Anonymous Users**: 100 requests/hour
- **File Uploads**: 10 uploads/hour
- **AI Requests**: 50 requests/hour

### Rate Limit Headers
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "secure_password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "expires_in": 3600
    }
  }
}
```

#### POST /auth/login
Authenticate user and obtain JWT tokens.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "secure_password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    },
    "tokens": {
      "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "expires_in": 3600
    }
  }
}
```

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### GET /auth/verify
Verify JWT token validity.

**Headers:**
```http
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "valid": true,
    "user": {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

### Notebook Management

#### GET /notebooks
List user's notebooks with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20, max: 100)
- `search` (optional): Search query
- `status` (optional): Filter by status (active, archived)

**Response:**
```json
{
  "success": true,
  "data": {
    "notebooks": [
      {
        "id": 1,
        "title": "Research Project",
        "description": "My research notebook",
        "status": "active",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-02T00:00:00Z",
        "source_count": 5,
        "conversation_count": 3
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

#### POST /notebooks
Create a new notebook.

**Request Body:**
```json
{
  "title": "New Research Project",
  "description": "Description of the research project"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "notebook": {
      "id": 2,
      "title": "New Research Project",
      "description": "Description of the research project",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "source_count": 0,
      "conversation_count": 0
    }
  }
}
```

#### GET /notebooks/{notebook_id}
Get detailed information about a specific notebook.

**Response:**
```json
{
  "success": true,
  "data": {
    "notebook": {
      "id": 1,
      "title": "Research Project",
      "description": "My research notebook",
      "status": "active",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-02T00:00:00Z",
      "sources": [
        {
          "id": 1,
          "title": "Document 1.pdf",
          "type": "pdf",
          "status": "processed",
          "uploaded_at": "2024-01-01T00:00:00Z"
        }
      ],
      "conversations": [
        {
          "id": 1,
          "title": "Chat about Document 1",
          "created_at": "2024-01-01T00:00:00Z",
          "message_count": 5
        }
      ]
    }
  }
}
```

#### PUT /notebooks/{notebook_id}
Update notebook information.

**Request Body:**
```json
{
  "title": "Updated Title",
  "description": "Updated description",
  "status": "active"
}
```

#### DELETE /notebooks/{notebook_id}
Delete a notebook and all associated data.

**Response:**
```json
{
  "success": true,
  "message": "Notebook deleted successfully"
}
```

### Document Sources

#### POST /notebooks/{notebook_id}/sources
Upload a document to a notebook.

**Request:**
- **Content-Type**: `multipart/form-data`
- **Body**: Form data with file upload

**Form Fields:**
- `file`: Document file (PDF, DOCX, TXT, etc.)
- `title` (optional): Custom title for the document

**Response:**
```json
{
  "success": true,
  "data": {
    "source": {
      "id": 1,
      "title": "Document.pdf",
      "filename": "document_123.pdf",
      "type": "pdf",
      "size": 1024000,
      "status": "processing",
      "uploaded_at": "2024-01-01T00:00:00Z",
      "processing_progress": 0
    }
  }
}
```

#### GET /notebooks/{notebook_id}/sources
List documents in a notebook.

**Query Parameters:**
- `status` (optional): Filter by processing status
- `type` (optional): Filter by document type

**Response:**
```json
{
  "success": true,
  "data": {
    "sources": [
      {
        "id": 1,
        "title": "Document.pdf",
        "type": "pdf",
        "size": 1024000,
        "status": "processed",
        "uploaded_at": "2024-01-01T00:00:00Z",
        "page_count": 10,
        "word_count": 5000
      }
    ]
  }
}
```

#### GET /notebooks/{notebook_id}/sources/{source_id}
Get detailed information about a specific document.

**Response:**
```json
{
  "success": true,
  "data": {
    "source": {
      "id": 1,
      "title": "Document.pdf",
      "filename": "document_123.pdf",
      "type": "pdf",
      "size": 1024000,
      "status": "processed",
      "uploaded_at": "2024-01-01T00:00:00Z",
      "processed_at": "2024-01-01T00:05:00Z",
      "metadata": {
        "page_count": 10,
        "word_count": 5000,
        "author": "John Doe",
        "created_date": "2024-01-01"
      },
      "processing_stats": {
        "chunks_created": 50,
        "embeddings_generated": 50,
        "processing_time": 30.5
      }
    }
  }
}
```

#### DELETE /notebooks/{notebook_id}/sources/{source_id}
Delete a document from a notebook.

### AI Chat

#### POST /chat/notebooks/{notebook_id}/conversations
Create a new conversation.

**Request Body:**
```json
{
  "title": "Discussion about Document 1"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation": {
      "id": 1,
      "title": "Discussion about Document 1",
      "notebook_id": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "message_count": 0
    }
  }
}
```

#### POST /chat/notebooks/{notebook_id}/conversations/{conversation_id}/messages
Send a message in a conversation.

**Request Body:**
```json
{
  "message": "What are the main findings in the document?",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "message": {
      "id": 1,
      "conversation_id": 1,
      "role": "assistant",
      "content": "Based on the documents in your notebook, the main findings are...",
      "created_at": "2024-01-01T00:00:00Z",
      "citations": [
        {
          "source_id": 1,
          "source_title": "Document.pdf",
          "page_number": 5,
          "text": "Relevant excerpt from the document...",
          "relevance_score": 0.95
        }
      ],
      "metadata": {
        "model": "gpt-4",
        "tokens_used": 150,
        "response_time": 2.3
      }
    }
  }
}
```

#### GET /chat/notebooks/{notebook_id}/conversations/{conversation_id}/messages
Get conversation history.

**Query Parameters:**
- `limit` (optional): Number of messages to return
- `before` (optional): Get messages before this message ID

**Response:**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": 1,
        "role": "user",
        "content": "What are the main findings?",
        "created_at": "2024-01-01T00:00:00Z"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "The main findings are...",
        "created_at": "2024-01-01T00:00:01Z",
        "citations": [...]
      }
    ]
  }
}
```

#### POST /chat/notebooks/{notebook_id}/search
Search documents using semantic search.

**Request Body:**
```json
{
  "query": "machine learning algorithms",
  "limit": 10,
  "similarity_threshold": 0.7,
  "source_ids": [1, 2]  // Optional: search specific documents
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "source_id": 1,
        "source_title": "Document.pdf",
        "chunk_id": "chunk_123",
        "content": "Machine learning algorithms are...",
        "page_number": 5,
        "similarity_score": 0.95,
        "metadata": {
          "section": "Introduction",
          "word_count": 100
        }
      }
    ],
    "query_metadata": {
      "total_results": 25,
      "search_time": 0.15,
      "embedding_model": "all-MiniLM-L6-v2"
    }
  }
}
```

### Content Generation

#### POST /content/notebooks/{notebook_id}/content/generate
Generate content from documents.

**Request Body:**
```json
{
  "type": "summary",  // summary, faq, study_guide, timeline
  "title": "Document Summary",
  "source_ids": [1, 2],  // Optional: specific documents
  "options": {
    "length": "medium",  // short, medium, long
    "style": "academic",  // academic, casual, technical
    "focus_areas": ["methodology", "results"],
    "custom_prompt": "Focus on the statistical analysis methods"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "content": {
      "id": 1,
      "type": "summary",
      "title": "Document Summary",
      "content": "This document presents a comprehensive analysis...",
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "metadata": {
        "word_count": 500,
        "generation_time": 15.2,
        "model_used": "gpt-4",
        "sources_used": [1, 2]
      }
    }
  }
}
```

#### GET /content/notebooks/{notebook_id}/content
List generated content.

**Query Parameters:**
- `type` (optional): Filter by content type
- `status` (optional): Filter by status

**Response:**
```json
{
  "success": true,
  "data": {
    "content": [
      {
        "id": 1,
        "type": "summary",
        "title": "Document Summary",
        "status": "completed",
        "created_at": "2024-01-01T00:00:00Z",
        "word_count": 500
      }
    ]
  }
}
```

### Podcast Generation

#### POST /podcasts/notebooks/{notebook_id}/podcasts
Generate an audio podcast from documents.

**Request Body:**
```json
{
  "title": "Research Discussion",
  "style": "conversational",  // conversational, interview, narrative, educational
  "duration": 15,  // minutes
  "voices": {
    "host": "male_voice",
    "guest": "female_voice"
  },
  "source_ids": [1, 2],
  "options": {
    "include_intro": true,
    "include_outro": true,
    "background_music": false,
    "speaking_rate": 1.0
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "podcast": {
      "id": 1,
      "title": "Research Discussion",
      "status": "processing",
      "created_at": "2024-01-01T00:00:00Z",
      "estimated_duration": 15,
      "progress": 0
    }
  }
}
```

#### GET /podcasts/notebooks/{notebook_id}/podcasts/{podcast_id}
Get podcast details and download URL.

**Response:**
```json
{
  "success": true,
  "data": {
    "podcast": {
      "id": 1,
      "title": "Research Discussion",
      "status": "completed",
      "created_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T00:15:00Z",
      "duration": 14.5,
      "file_size": 14500000,
      "download_url": "/api/podcasts/1/download",
      "transcript": "Host: Welcome to today's discussion...",
      "metadata": {
        "style": "conversational",
        "voices_used": ["male_voice", "female_voice"],
        "generation_time": 300
      }
    }
  }
}
```

#### GET /podcasts/{podcast_id}/download
Download podcast audio file.

**Response:**
- **Content-Type**: `audio/mpeg`
- **Content-Disposition**: `attachment; filename="podcast.mp3"`

### Health and Status

#### GET /health
Check API health status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0",
    "services": {
      "database": "healthy",
      "vector_db": "healthy",
      "redis": "healthy",
      "ai_providers": {
        "openai": "healthy",
        "anthropic": "healthy"
      }
    }
  }
}
```

## WebSocket Events

NotebookLM supports real-time updates via WebSocket connections.

### Connection
```javascript
const ws = new WebSocket('ws://localhost:5050/ws');
ws.send(JSON.stringify({
  type: 'authenticate',
  token: 'your_jwt_token'
}));
```

### Events

#### Document Processing Updates
```json
{
  "type": "source_processing_update",
  "data": {
    "source_id": 1,
    "status": "processing",
    "progress": 75,
    "message": "Generating embeddings..."
  }
}
```

#### Podcast Generation Updates
```json
{
  "type": "podcast_generation_update",
  "data": {
    "podcast_id": 1,
    "status": "generating_audio",
    "progress": 50,
    "estimated_time_remaining": 120
  }
}
```

## SDK Examples

### Python SDK Example
```python
import requests
import json

class NotebookLMClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = requests.Session()
        
    def login(self, email, password):
        response = self.session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        data = response.json()
        self.api_key = data['data']['tokens']['access_token']
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}'
        })
        return data
    
    def create_notebook(self, title, description=""):
        return self.session.post(
            f"{self.base_url}/notebooks",
            json={"title": title, "description": description}
        ).json()
    
    def upload_document(self, notebook_id, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            return self.session.post(
                f"{self.base_url}/notebooks/{notebook_id}/sources",
                files=files
            ).json()
    
    def chat(self, notebook_id, conversation_id, message):
        return self.session.post(
            f"{self.base_url}/chat/notebooks/{notebook_id}/conversations/{conversation_id}/messages",
            json={"message": message}
        ).json()

# Usage
client = NotebookLMClient("http://localhost:5050/api")
client.login("test@example.com", "password123")

notebook = client.create_notebook("My Research")
notebook_id = notebook['data']['notebook']['id']

# Upload document
result = client.upload_document(notebook_id, "research_paper.pdf")

# Create conversation and chat
conv = client.session.post(f"{client.base_url}/chat/notebooks/{notebook_id}/conversations", 
                          json={"title": "Discussion"}).json()
conv_id = conv['data']['conversation']['id']

response = client.chat(notebook_id, conv_id, "What are the main findings?")
print(response['data']['message']['content'])
```

### JavaScript SDK Example
```javascript
class NotebookLMClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.token = null;
    }
    
    async login(email, password) {
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await response.json();
        this.token = data.data.tokens.access_token;
        return data;
    }
    
    async createNotebook(title, description = '') {
        return this.request('POST', '/notebooks', { title, description });
    }
    
    async uploadDocument(notebookId, file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${this.baseUrl}/notebooks/${notebookId}/sources`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${this.token}` },
            body: formData
        });
        return response.json();
    }
    
    async chat(notebookId, conversationId, message) {
        return this.request('POST', 
            `/chat/notebooks/${notebookId}/conversations/${conversationId}/messages`,
            { message }
        );
    }
    
    async request(method, endpoint, data = null) {
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            }
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(`${this.baseUrl}${endpoint}`, options);
        return response.json();
    }
}

// Usage
const client = new NotebookLMClient('http://localhost:5050/api');
await client.login('test@example.com', 'password123');

const notebook = await client.createNotebook('My Research');
const notebookId = notebook.data.notebook.id;

// Upload file
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];
await client.uploadDocument(notebookId, file);
```

This completes the comprehensive API documentation for NotebookLM. For additional examples and advanced usage, please refer to the example applications in the repository.

