# Openbook - Open Source AI Research Assistant by Future AGI Inc

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

An open-source implementation of an AI-powered research assistant that transforms documents into actionable insights. Upload documents, chat with AI about their contents, generate summaries and study guides, and create engaging audio podcasts from your research materials.

## 🌟 Features

### 📄 Document Processing
- **Multi-format Support**: Upload PDFs, Word documents, text files, PowerPoint presentations, and more
- **Intelligent Extraction**: Advanced text extraction with OCR support for scanned documents
- **Metadata Preservation**: Maintain document structure, formatting, and source attribution
- **Batch Processing**: Upload multiple documents simultaneously with progress tracking

### 🤖 AI-Powered Chat
- **Contextual Conversations**: Chat with AI about your documents using advanced RAG (Retrieval-Augmented Generation)
- **Source Citations**: Every AI response includes citations to specific document sections
- **Multiple LLM Support**: Compatible with OpenAI GPT, Anthropic Claude, Google Gemini, and more
- **Conversation History**: Persistent chat history with search and organization features

### 📚 Content Generation
- **Smart Summaries**: Generate comprehensive summaries of single documents or entire collections
- **Study Guides**: Create structured study materials with key concepts and questions
- **FAQ Generation**: Automatically generate frequently asked questions and answers
- **Timeline Creation**: Extract and organize chronological information from documents
- **Custom Prompts**: Use custom instructions for specialized content generation

### 🎧 Audio Podcasts
- **Natural Conversations**: Transform documents into engaging audio podcasts with multiple speakers
- **Multiple Styles**: Choose from conversational, interview, narrative, or educational formats
- **Voice Customization**: Select from various AI voices and speaking styles
- **Length Control**: Generate podcasts of different durations (5-30 minutes)
- **High-Quality Audio**: Professional-grade text-to-speech with natural intonation

### 🔍 Semantic Search
- **Vector Search**: Find information using natural language queries, not just keywords
- **Cross-Document Search**: Search across all documents in a notebook simultaneously
- **Relevance Scoring**: Results ranked by semantic similarity and relevance
- **Context Preservation**: Search results include surrounding context for better understanding

### 👥 User Management
- **Secure Authentication**: JWT-based authentication with password hashing
- **Notebook Organization**: Create and manage multiple research notebooks
- **Sharing Capabilities**: Share notebooks and collaborate with team members
- **Usage Tracking**: Monitor API usage and document processing statistics

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- OpenAI API key (optional, for full AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/future-agi-inc/openbook.git
   cd openbook
   ```

2. **Set up environment variables**
   ```bash
   cp openbook-backend/.env.example .env
   # Edit .env file and add your API keys
   ```

3. **Deploy with Docker**
   ```bash
   ./deploy.sh start
   ```

4. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:5050
   - Login with: `test@example.com` / `password123`

### Manual Setup (Development)

If you prefer to run the services individually for development:

#### Backend Setup
```bash
cd openbook-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/database/init_db.py
python src/main.py
```

#### Frontend Setup
```bash
cd openbook-frontend
npm install
npm run dev
```

## 📖 Documentation

### API Documentation

The backend provides a comprehensive REST API with the following endpoints:

#### Authentication
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - User login
- `GET /api/auth/verify` - Verify JWT token

#### Notebooks
- `GET /api/notebooks` - List user's notebooks
- `POST /api/notebooks` - Create new notebook
- `GET /api/notebooks/{id}` - Get notebook details
- `PUT /api/notebooks/{id}` - Update notebook
- `DELETE /api/notebooks/{id}` - Delete notebook

#### Document Sources
- `POST /api/notebooks/{id}/sources` - Upload document
- `GET /api/notebooks/{id}/sources` - List documents
- `DELETE /api/notebooks/{id}/sources/{source_id}` - Delete document

#### AI Chat
- `POST /api/chat/notebooks/{id}/conversations` - Create conversation
- `POST /api/chat/notebooks/{id}/conversations/{conv_id}/messages` - Send message
- `POST /api/chat/notebooks/{id}/search` - Search documents

#### Content Generation
- `POST /api/content/notebooks/{id}/content/generate` - Generate content
- `GET /api/content/notebooks/{id}/content` - List generated content

#### Podcasts
- `POST /api/podcasts/notebooks/{id}/podcasts` - Create podcast
- `GET /api/podcasts/notebooks/{id}/podcasts` - List podcasts

### Configuration

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `SECRET_KEY` | Flask secret key | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///openbook.db` |
| `OPENAI_API_KEY` | OpenAI API key | Optional |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `CHROMA_PERSIST_DIRECTORY` | Vector DB storage path | `./chroma_db` |
| `UPLOAD_FOLDER` | File upload directory | `./uploads` |
| `MAX_CONTENT_LENGTH` | Max file size (bytes) | `16777216` |

#### LLM Provider Configuration

The system supports multiple LLM providers. Configure them in your `.env` file:

```env
# OpenAI (recommended)
OPENAI_API_KEY=your-openai-key
OPENAI_API_BASE=https://api.openai.com/v1

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-key

# Google Gemini
GOOGLE_API_KEY=your-google-key

# Cohere
COHERE_API_KEY=your-cohere-key
```

## 🏗️ Architecture

### System Overview

Openbook follows a modern microservices architecture with clear separation of concerns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   Flask Backend │    │   Vector DB     │
│   (Port 80)     │◄──►│   (Port 5050)   │◄──►│   (ChromaDB)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   PostgreSQL    │
                       │   (Port 5432)   │
                       └─────────────────┘
```

### Technology Stack

#### Backend
- **Framework**: Flask 3.0 with SQLAlchemy ORM
- **Database**: PostgreSQL (production) / SQLite (development)
- **Vector Database**: ChromaDB for semantic search
- **Authentication**: JWT tokens with Flask-JWT-Extended
- **Document Processing**: PyPDF2, python-docx, BeautifulSoup4
- **AI Integration**: OpenAI, Anthropic, Google AI APIs
- **Audio Generation**: OpenAI TTS, ElevenLabs, gTTS
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)

#### Frontend
- **Framework**: React 18 with TypeScript
- **Routing**: React Router DOM
- **UI Components**: shadcn/ui with Tailwind CSS
- **State Management**: React Context API
- **HTTP Client**: Fetch API with custom hooks
- **Icons**: Lucide React
- **Build Tool**: Vite

#### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Web Server**: Nginx (production)
- **Process Manager**: Gunicorn with Gevent workers
- **Caching**: Redis for session storage and caching
- **Monitoring**: Health checks and logging

### Data Flow

1. **Document Upload**: Users upload documents through the React frontend
2. **Processing Pipeline**: Backend extracts text, generates embeddings, stores in vector DB
3. **AI Interaction**: User queries are processed using RAG with vector similarity search
4. **Response Generation**: LLM generates responses with source citations
5. **Content Creation**: AI generates summaries, podcasts, and other content types

## 🔧 Development

### Project Structure

```
openbook/
├── openbook-backend/          # Flask backend application
│   ├── src/
│   │   ├── models/              # Database models
│   │   ├── routes/              # API endpoints
│   │   ├── services/            # Business logic
│   │   └── database/            # Database utilities
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile              # Backend container
├── openbook-frontend/         # React frontend application
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── hooks/              # Custom React hooks
│   │   └── lib/                # Utility functions
│   ├── package.json            # Node.js dependencies
│   └── Dockerfile              # Frontend container
├── docker-compose.yml          # Multi-service orchestration
├── deploy.sh                   # Deployment script
└── README.md                   # This file
```

### Development Workflow

1. **Setup Development Environment**
   ```bash
   # Backend
   cd openbook-backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Frontend
   cd openbook-frontend
   npm install
   ```

2. **Run Services Locally**
   ```bash
   # Terminal 1: Backend
   cd openbook-backend
   python src/main.py
   
   # Terminal 2: Frontend
   cd openbook-frontend
   npm run dev
   ```

3. **Database Management**
   ```bash
   # Initialize database
   python src/database/init_db.py
   
   # Reset database
   python src/database/init_db.py reset
   ```

### Testing

#### Backend Tests
```bash
cd openbook-backend
pytest tests/
```

#### Frontend Tests
```bash
cd openbook-frontend
npm test
```

#### Integration Tests
```bash
# Start all services
./deploy.sh start

# Run integration tests
python tests/integration/test_full_workflow.py
```

## 🚀 Deployment

### Production Deployment

1. **Prepare Environment**
   ```bash
   # Clone repository
   git clone https://github.com/future-agi-inc/openbook.git
   cd openbook
   
   # Configure environment
   cp openbook-backend/.env.example .env
   # Edit .env with production values
   ```

2. **Deploy with Docker**
   ```bash
   ./deploy.sh start
   ```

3. **Verify Deployment**
   ```bash
   ./deploy.sh status
   ```

### Scaling Considerations

For high-traffic deployments, consider:

- **Load Balancing**: Use multiple backend instances behind a load balancer
- **Database Scaling**: Use PostgreSQL with read replicas
- **Caching**: Implement Redis caching for frequently accessed data
- **CDN**: Use a CDN for static assets and file downloads
- **Monitoring**: Implement comprehensive logging and monitoring

### Security Considerations

- **HTTPS**: Always use HTTPS in production
- **API Keys**: Store API keys securely using environment variables
- **Database**: Use strong passwords and restrict database access
- **CORS**: Configure CORS properly for your domain
- **Rate Limiting**: Implement rate limiting for API endpoints

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint and Prettier for JavaScript/TypeScript
- Write comprehensive tests for new features
- Update documentation for API changes
- Use conventional commit messages

### Areas for Contribution

- **New LLM Providers**: Add support for additional AI providers
- **Document Formats**: Extend support for more file types
- **UI/UX Improvements**: Enhance the user interface and experience
- **Performance Optimization**: Improve processing speed and efficiency
- **Internationalization**: Add support for multiple languages
- **Mobile Support**: Improve mobile responsiveness

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- The open-source community for providing excellent libraries and tools
- AI research community for advancing the field of natural language processing
- Contributors who help improve this project

## 📞 Support

- **Documentation**: Check this README and inline code comments
- **Issues**: Report bugs and request features on GitHub Issues
- **Discussions**: Join community discussions on GitHub Discussions
- **Email**: Contact the maintainers at support@futureagi.com

---

**Built with ❤️ by the open-source community**

