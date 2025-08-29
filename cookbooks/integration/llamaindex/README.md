# LlamaIndex Document Chat Assistant

A document chat application that allows users to upload documents and chat with their content using AI. This application uses LlamaIndex for RAG (Retrieval-Augmented Generation) capabilities and provides a simple Gradio interface.

## Features

- Upload multiple document types (PDF, TXT, DOCX, MD)
- Chat with document content using AI
- View sources of information used in responses
- Rebuild index to incorporate new documents
- Instrumented with FutureAGI tracing

## Requirements

- OpenAI API key
- Future AGI API Key and Secret Key (click [here](https://app.futureagi.com/dashboard/keys) to get your FI keys)


## Installation

1. Clone the repository
2. Set up the environment:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:

```
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4o-mini  # Optional, defaults to gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-large  # Optional, defaults to text-embedding-3-large

# FutureAGI keys
FI_API_KEY=your_fi_api_key
FI_SECRET_KEY=your_fi_secret_key
```

## Usage

1. Run the application:

```bash
python app.py
```

2. Open your browser at http://localhost:7860
3. Upload documents using the file uploader
4. Start chatting with your documents

## Directory Structure

- `./documents/`: Place to store uploaded documents
- `./vectorstore/`: Storage for the vector index
- `app.py`: Main application file

## How It Works

1. Documents are uploaded to the `./documents/` directory
2. LlamaIndex creates vector embeddings of the documents
3. The chat engine uses these embeddings to find relevant information
4. Responses include citations to the source documents

## Configuration

You can customize the following settings:
- LLM model: Set `OPENAI_MODEL` in your `.env` file
- Embedding model: Set `OPENAI_EMBED_MODEL` in your `.env` file
