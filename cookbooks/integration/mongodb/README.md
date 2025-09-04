# MongoDB Atlas Vector Search RAG Application

A PDF chat application that allows users to upload PDF documents and ask questions about their content using MongoDB Atlas Vector Search. This application uses LangChain for RAG capabilities and provides a simple Gradio interface.

## Features

- Upload and ingest multiple PDF documents
- Vector search using MongoDB Atlas Vector Search
- Chat with document content using AI
- View sources of information used in responses
- Reset and clear document collection
- Instrumented with FutureAGI tracing

## Requirements

- OpenAI API key
- MongoDB Atlas account with Vector Search enabled
- Future AGI API Key and Secret Key (click [here](https://app.futureagi.com/dashboard/keys) to get your FI keys)

## Installation

1. Clone the repository
2. Set up the environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:

```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small  # Optional, defaults to text-embedding-3-small

# MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB=ragdb  # Optional, defaults to ragdb
MONGODB_COLLECTION=pdf_chunks  # Optional, defaults to pdf_chunks
MONGODB_ATLAS_INDEX=vector_index  # Optional, defaults to vector_index

# FutureAGI keys
FI_API_KEY=your_fi_api_key
FI_SECRET_KEY=your_fi_secret_key

# Optional configurations
CHUNK_SIZE=1000  # Optional, defaults to 1000
CHUNK_OVERLAP=150  # Optional, defaults to 150
TOP_K=6  # Optional, defaults to 6
ALLOW_FALLBACK=false  # Optional, defaults to false
```

## Usage

1. Run the application:

```bash
python app.py
```

2. Open your browser at http://localhost:7860
3. Upload PDF documents in the "Ingest" tab
4. Switch to the "Chat" tab to ask questions about your documents

## Directory Structure

- `./documents/`: Storage for uploaded PDF files
- `app.py`: Main application file

## How It Works

1. PDFs are uploaded and stored in the `./documents/` directory
2. Documents are chunked and embedded using OpenAI's embedding model
3. Embeddings are stored in MongoDB Atlas with vector search capabilities
4. When a question is asked:
   - The query is embedded and used for vector similarity search
   - Relevant document chunks are retrieved from MongoDB Atlas
   - The LLM uses these chunks to generate an accurate response
   - Sources are displayed with page numbers for reference

## Configuration

You can customize the following settings in your `.env` file:

- LLM model: Set `OPENAI_MODEL` (defaults to gpt-4o-mini)
- Embedding model: Set `OPENAI_EMBED_MODEL` (defaults to text-embedding-3-small)
- Chunking parameters: Modify `CHUNK_SIZE` and `CHUNK_OVERLAP`
- Number of retrieved documents: Adjust `TOP_K`
- Response behavior: Set `ALLOW_FALLBACK` to true to allow the AI to use general knowledge when documents don't have the answer
