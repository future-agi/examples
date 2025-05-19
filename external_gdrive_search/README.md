# LlamaIndex Demo - README

This repository contains a LlamaIndex-based demo application for searching across an internal knowledge database and Google Drive files using semantic search with Retrieval-Augmented Generation (RAG).

## Features

- Connect to internal databases (PostgreSQL, MySQL, SQLite, etc.)
- Connect to Google Drive for document search
- Semantic search using OpenAI embeddings
- RAG-powered responses using OpenAI's LLM
- User-friendly Gradio interface
- Comprehensive documentation and setup instructions

## Installation

1. Clone this repository:
```bash
git clone https://github.com/future-agi/examples.git
cd external_gdrive_search
```

2. Install dependencies using uv:
```bash
# Install uv if you don't have it already
curl -sSf https://install.ultraviolet.rs | sh

# Activate uv
export PATH="$HOME/.cargo/bin:$PATH"

# Install dependencies with uv
uv pip install llama-index llama-index-readers-database llama-index-embeddings-openai llama-index-llms-openai gradio python-dotenv sqlalchemy psycopg2-binary pymysql google-api-python-client google-auth-httplib2 google-auth-oauthlib traceAI-llamaindex futureAGI
```

3. Set up your environment variables by creating a `.env` file:
```
# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key

# Database Connection (Optional)
DB_TYPE=postgresql
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database

# Google Drive (Optional)
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.pickle
```

4. For Google Drive integration, follow the instructions in `google_drive_setup.md` to set up the Google Drive API and obtain credentials.

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and navigate to the URL displayed in the terminal (typically http://127.0.0.1:7860).

3. In the Setup tab:
   - Connect to your database by entering the connection string
   - Connect to Google Drive by providing the path to your credentials.json file
   - Build the search index

4. In the Search tab:
   - Enter your query and click "Search"
   - View the answer and sources

## Testing

To run the tests:
```bash
python test.py
```

This will test the database connector, Google Drive connector, and search functionality.

## Project Structure

- `app.py`: Main application file with Gradio interface
- `database_connector.py`: Connector for internal knowledge database
- `google_drive_connector.py`: Connector for Google Drive
- `test.py`: Test script for validating functionality
- `google_drive_setup.md`: Instructions for setting up Google Drive API
- `.env`: Environment variables (create this file manually)

## Requirements

- Python 3.7+
- OpenAI API key
- Database (optional)
- Google Drive API credentials (optional)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
