# RAG Agent Documentation

## Overview

This document provides comprehensive information about the RAG (Retrieval-Augmented Generation) agent that has been developed. The agent features an internal knowledge search database, a sophisticated RAG pipeline, and a ChatGPT-like Gradio UI for asking questions and maintaining chat history.

## Features

- **Internal Knowledge Database**: Vector-based storage using ChromaDB for efficient semantic search
- **RAG Pipeline**: 
  - Question breakdown for complex queries
  - Context retrieval from the knowledge base
  - Context reranking for improved relevance
  - Answer generation using retrieved context
- **Chat History**: Support for follow-up questions and conversation continuity
- **Gradio UI**: ChatGPT-like interface with message history and source attribution

## Project Structure

```
rag_agent/
├── data/
│   ├── chroma_db/       # Vector database storage
│   └── sample_data/     # Sample documents
├── src/
│   ├── knowledge_base.py    # Knowledge database implementation
│   ├── rag_pipeline.py      # RAG pipeline components
│   ├── gradio_ui.py         # Gradio UI implementation
│   ├── sample_data.py       # Sample data generation
│   ├── mock_openai.py       # Mock OpenAI for testing
│   └── main.py              # Main application entry point
├── tests/
│   └── test_rag_agent.py    # Validation tests
└── todo.md                  # Development tasks checklist
```

## Components

### Knowledge Base

The knowledge base uses ChromaDB as a vector database to store document embeddings. It provides:

- Document processing and chunking
- Embedding generation using sentence-transformers
- Efficient vector storage and retrieval
- Metadata filtering capabilities

### RAG Pipeline

The RAG pipeline implements a sophisticated question-answering process:

1. **Question Breakdown**: Complex questions are broken down into simpler sub-questions
2. **Context Retrieval**: Relevant documents are retrieved for each sub-question
3. **Context Reranking**: Retrieved documents are reranked based on relevance
4. **Answer Generation**: A comprehensive answer is generated using the retrieved context

### Chat History Manager

The chat history manager maintains conversation context:

- Session-based history storage
- Support for follow-up questions
- History length management

### Gradio UI

The Gradio UI provides a ChatGPT-like interface:

- Message history display with user and assistant messages
- Input field for user questions
- Source attribution for transparency
- Responsive design with custom styling

## Setup and Installation

### Prerequisites

- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd rag_agent
   ```

2. Install dependencies using uv (fast Python package installer):
   ```
   # Install uv if you don't have it
   curl -sSf https://install.ultraviolet.rs | sh

   # Install dependencies with uv
   uv pip install -r requirements.txt
   ```

   Alternatively, you can use pip:
   ```
   pip install -r requirements.txt
   ```

3. Set up OpenAI API key (for production use):
   ```
   export OPENAI_API_KEY=your_api_key_here
   ```

## Usage

### Running the Application

To start the RAG agent with the Gradio UI:

```
cd rag_agent
python src/main.py
```

Optional command-line arguments:
- `--port`: Specify the port for the Gradio server (default: 7860)
- `--share`: Create a public link for sharing
- `--reset-db`: Reset the knowledge base and reload sample data

### Accessing the UI

Once running, access the UI at:
- Local: http://localhost:7860
- Network: http://your-ip-address:7860

### Using the RAG Agent

1. Enter your question in the input field
2. Click "Send" or press Enter
3. View the response and source attribution
4. Ask follow-up questions as needed
5. Use "Clear Conversation" to start a new session

## Customization

### Adding Custom Data

To add your own documents to the knowledge base:

1. Create a new Python script based on `sample_data.py`
2. Define your documents with title, category, and content
3. Use the `KnowledgeBase` class to add documents:
   ```python
   from knowledge_base import KnowledgeBase
   
   kb = KnowledgeBase()
   kb.add_documents(your_documents, your_metadatas)
   ```

### Modifying the RAG Pipeline

The RAG pipeline can be customized by adjusting parameters in `rag_pipeline.py`:

- Change embedding models
- Adjust reranking parameters
- Modify prompt templates
- Configure context window size

### UI Customization

The Gradio UI can be customized in `gradio_ui.py`:

- Update CSS styling
- Change title and description
- Modify layout and components

## Testing

To run the validation tests:

```
cd rag_agent
python tests/test_rag_agent.py
```

The tests use a mock OpenAI module to validate functionality without requiring an API key.

## Production Deployment

For production deployment:

1. Ensure all dependencies are installed
2. Set the OpenAI API key as an environment variable
3. Configure the server to listen on 0.0.0.0 for network access
4. Consider using a process manager like Supervisor or PM2
5. Set up proper authentication if needed

## Limitations and Future Improvements

- The current implementation uses OpenAI for question breakdown and answer generation
- For a fully self-hosted solution, consider replacing OpenAI with local models
- Performance may vary based on the size of the knowledge base
- Consider implementing caching for frequently asked questions
- Add user authentication for multi-user environments

## Troubleshooting

- If the knowledge base is empty, use the `--reset-db` flag to reload sample data
- For OpenAI API errors, check that your API key is correctly set
- If the UI is not accessible, ensure the server is listening on 0.0.0.0
- For memory issues with large knowledge bases, adjust chunk size and overlap

## License

This project is provided as-is without any warranty. Use at your own risk.
