# RAG Agent Architecture

## Overview
This document outlines the architecture for a Retrieval-Augmented Generation (RAG) agent based on ChatGPT. The system will provide an internal knowledge search database with a ChatGPT-like Gradio UI for asking questions and maintaining chat history.

## System Components

### 1. Knowledge Database
- **Vector Database**: Chroma DB for storing document embeddings
- **Document Processor**: Handles document ingestion, chunking, and preprocessing
- **Embedding Generator**: Creates vector embeddings for documents using sentence-transformers
- **Storage Manager**: Manages persistence and retrieval of vectors and documents

### 2. RAG Pipeline
- **Question Processor**:
  - Question breakdown module to split complex queries into simpler sub-questions
  - Query understanding to identify key entities and intents
- **Retrieval Engine**:
  - Semantic search using vector similarity
  - Metadata filtering capabilities
  - Multi-query retrieval for complex questions
- **Reranker**:
  - Cross-encoder based reranking to improve retrieval precision
  - Contextual relevance scoring
- **Answer Generator**:
  - LLM-based response generation using retrieved contexts
  - Source attribution and confidence scoring
  - Follow-up question handling

### 3. Chat History Manager
- **Session Handler**: Manages user sessions and conversation state
- **Context Window Manager**: Maintains relevant conversation history
- **History Persistence**: Stores chat history for continuity between sessions

### 4. Gradio UI
- **Chat Interface**: ChatGPT-like interface with message history
- **Input Component**: Text input for user questions
- **Output Display**: Formatted responses with source attribution
- **History Display**: Scrollable chat history with user and system messages
- **Styling**: CSS for responsive design and improved user experience

## Data Flow

1. **User Input**: User submits a question through the Gradio UI
2. **Question Processing**:
   - Question is analyzed and broken down if complex
   - Sub-questions are generated if necessary
3. **Context Retrieval**:
   - For each question/sub-question, relevant documents are retrieved from the vector database
   - Initial retrieval based on embedding similarity
4. **Context Reranking**:
   - Retrieved documents are reranked based on relevance to the question
   - Top-k most relevant documents are selected
5. **Answer Generation**:
   - Selected documents and question are passed to the LLM
   - LLM generates a comprehensive answer based on the provided context
6. **Response Display**:
   - Answer is displayed in the UI
   - Chat history is updated
7. **Follow-up Handling**:
   - Previous context and question-answer pairs are maintained in history
   - Follow-up questions are processed with awareness of conversation context

## Technologies

- **Vector Database**: Chroma DB
- **Embeddings**: Sentence-Transformers (e.g., all-MiniLM-L6-v2)
- **Reranking**: Cross-Encoder models
- **LLM Integration**: OpenAI API (ChatGPT)
- **UI Framework**: Gradio
- **Backend**: Python with FastAPI
- **Data Processing**: Langchain for document processing and chunking

## Implementation Considerations

- **Modularity**: Components should be loosely coupled for easy maintenance and extension
- **Scalability**: Design should accommodate growing knowledge base
- **Performance**: Optimize retrieval and reranking for response time
- **User Experience**: Focus on intuitive UI and meaningful responses
- **Error Handling**: Robust error handling for edge cases and unexpected inputs
