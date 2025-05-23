# Interview Agent Application Requirements

## Core Functionality Requirements

### Audio Upload and Transcription
- Accept audio file uploads in common formats (MP3, WAV, M4A, etc.)
- Transcribe audio to English text using OpenAI's Whisper API
- Display transcription progress and results to the user
- Support for various audio durations (short to long interviews)

### Interview Summarization
- Generate concise summaries of transcribed interviews using OpenAI's GPT models
- Extract key topics, main points, and important quotes
- Provide metadata about the interview (duration, speakers if detected, date)
- Allow customization of summary length/detail level

### Vector Database Storage
- Store transcribed interviews in a local vector database (ChromaDB)
- Index content for semantic search capabilities
- Maintain metadata about each interview (title, date, participants, etc.)
- Support for persistent storage between application sessions

### Question Answering on Single Interviews
- Allow users to ask specific questions about any stored interview
- Retrieve relevant context from the vector database
- Generate accurate, contextual answers using OpenAI's GPT models
- Provide source citations/references to the original transcript

### Multi-Interview Analysis
- Support queries across multiple interviews simultaneously
- Compare and contrast information across different interviews
- Identify patterns, contradictions, or common themes
- Generate comprehensive analysis reports

### User Interface Requirements
- Clean, intuitive Gradio interface
- Separate tabs/sections for different functionalities
- Progress indicators for long-running operations
- Responsive design for various screen sizes

## Technical Requirements

### OpenAI API Integration
- Whisper API for audio transcription
- GPT-4 or equivalent for summarization and question answering
- Efficient token usage to minimize API costs
- Proper error handling for API limitations

### Vector Database
- ChromaDB for local vector storage
- Efficient embedding generation using OpenAI embeddings
- Proper indexing for fast retrieval
- Persistence mechanism for long-term storage

### Python Dependencies
- OpenAI Python library
- ChromaDB for vector storage
- Gradio for user interface
- Additional libraries for audio processing and file handling

### Performance Considerations
- Efficient handling of large audio files
- Optimized vector search for quick responses
- Caching mechanisms where appropriate
- Reasonable response times for user queries
