# Interview Agent Application Architecture

## System Architecture Overview

```
+---------------------+     +----------------------+     +---------------------+
|                     |     |                      |     |                     |
|  Gradio Web UI      |<--->|  Application Core    |<--->|  OpenAI API         |
|  (User Interface)   |     |  (Backend Logic)     |     |  (AI Services)      |
|                     |     |                      |     |                     |
+---------------------+     +----------------------+     +---------------------+
                                      ^
                                      |
                                      v
                            +----------------------+
                            |                      |
                            |  ChromaDB            |
                            |  (Vector Storage)    |
                            |                      |
                            +----------------------+
```

## Component Descriptions

### 1. Gradio Web UI
- **Purpose**: Provide user interface for all application features
- **Components**:
  - Audio upload interface
  - Transcription display
  - Summary view
  - Question input and answer display
  - Multi-interview analysis interface
  - Interview management dashboard
- **Interactions**:
  - Sends user inputs to Application Core
  - Displays results from Application Core
  - Manages user session state

### 2. Application Core
- **Purpose**: Coordinate all application logic and data flow
- **Components**:
  - Audio processing module
  - Transcription manager
  - Summarization engine
  - Question answering system
  - Multi-interview analyzer
  - Vector database interface
- **Interactions**:
  - Processes audio files for transcription
  - Sends requests to OpenAI API
  - Stores and retrieves data from ChromaDB
  - Formats responses for Gradio UI

### 3. OpenAI API Integration
- **Purpose**: Provide AI capabilities for transcription, summarization, and QA
- **Components**:
  - Whisper API client (transcription)
  - GPT API client (summarization and QA)
  - Embeddings API client (vector encoding)
- **Interactions**:
  - Receives requests from Application Core
  - Returns AI-generated content to Application Core

### 4. ChromaDB Vector Storage
- **Purpose**: Store and retrieve interview transcripts and embeddings
- **Components**:
  - Vector database
  - Embedding index
  - Metadata storage
  - Persistence layer
- **Interactions**:
  - Stores transcript embeddings and metadata
  - Performs semantic searches for relevant content
  - Maintains persistent storage between sessions

## Data Flow

### Audio Upload and Transcription Flow
1. User uploads audio file via Gradio UI
2. Application Core processes and validates audio file
3. Audio sent to OpenAI Whisper API for transcription
4. Transcription result returned to Application Core
5. Transcript displayed to user and prepared for storage

### Summarization Flow
1. User requests summary of transcribed interview
2. Application Core retrieves full transcript
3. Transcript sent to OpenAI GPT API with summarization prompt
4. Summary returned to Application Core
5. Summary displayed to user and stored with transcript metadata

### Vector Storage Flow
1. Application Core processes transcript for storage
2. Transcript chunked into appropriate segments
3. OpenAI Embeddings API generates vector embeddings for each chunk
4. ChromaDB stores chunks, embeddings, and metadata
5. Confirmation of storage returned to user

### Question Answering Flow
1. User submits question about specific interview
2. Application Core formulates query for vector search
3. ChromaDB performs semantic search to find relevant chunks
4. Relevant context retrieved and sent to OpenAI GPT API with user question
5. Answer generated and returned to user with source references

### Multi-Interview Analysis Flow
1. User requests analysis across multiple interviews
2. Application Core identifies relevant interviews
3. Vector searches performed across selected interviews
4. Relevant contexts combined and sent to OpenAI GPT API
5. Comprehensive analysis returned to user

## Data Models

### Interview Document
```python
{
    "id": "unique_interview_id",
    "title": "Interview Title",
    "date_uploaded": "ISO timestamp",
    "audio_metadata": {
        "filename": "original_filename.mp3",
        "duration_seconds": 1234,
        "file_size_bytes": 5678
    },
    "transcript": "Full interview transcript text",
    "summary": "Generated summary of the interview",
    "metadata": {
        "speakers": ["Speaker 1", "Speaker 2"],
        "topics": ["Topic 1", "Topic 2"],
        "custom_fields": {}
    }
}
```

### Vector Chunk
```python
{
    "chunk_id": "unique_chunk_id",
    "interview_id": "parent_interview_id",
    "text": "Chunk of transcript text",
    "embedding": [vector_values],
    "metadata": {
        "position": 42,
        "timestamp": "00:15:30"
    }
}
```

## API Endpoints and Functions

### Core Functions
- `process_audio(file_path)` - Process uploaded audio file
- `transcribe_audio(processed_audio)` - Transcribe audio using Whisper API
- `generate_summary(transcript)` - Generate summary using GPT API
- `store_interview(transcript, metadata)` - Store interview in vector database
- `query_interview(interview_id, question)` - Answer question about specific interview
- `analyze_interviews(interview_ids, query)` - Analyze multiple interviews

### Gradio Interface Functions
- `upload_handler(file)` - Handle audio file uploads
- `transcription_display(transcript)` - Format and display transcription
- `summary_generator(interview_id)` - Generate and display summary
- `qa_interface(interview_id, question)` - Process and display QA results
- `multi_interview_analyzer(interview_ids, query)` - Process and display analysis

## Technology Stack

- **Python 3.9+**: Core programming language
- **OpenAI API**: AI services for transcription, embeddings, and text generation
- **ChromaDB**: Local vector database for semantic storage and retrieval
- **Gradio**: Web interface framework
- **Additional Libraries**:
  - `pydub`: Audio processing
  - `numpy`: Numerical operations
  - `pandas`: Data manipulation
  - `tqdm`: Progress tracking
  - `uuid`: Unique ID generation
  - `datetime`: Timestamp handling
  - `json`: Data serialization
