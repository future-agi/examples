#!/bin/bash

# Setup script for LlamaIndex Demo with uv-based installation

echo "Setting up LlamaIndex Demo environment..."

# Check if uv is installed, if not install it
if ! command -v uv &> /dev/null; then
    echo "Installing uv package manager..."
    curl -sSf https://install.ultraviolet.rs | sh
    
    # Add uv to PATH for this session
    export PATH="$HOME/.cargo/bin:$PATH"
    
    echo "uv installed successfully!"
else
    echo "uv is already installed."
fi

# Create virtual environment using uv
echo "Creating virtual environment..."
uv venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies using uv
echo "Installing dependencies..."
uv pip install llama-index llama-index-readers-database llama-index-embeddings-openai llama-index-llms-openai gradio python-dotenv sqlalchemy psycopg2-binary pymysql google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Create .env file template if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file template..."
    cat > .env << EOL
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
EOL
    echo ".env template created. Please update with your actual credentials."
else
    echo ".env file already exists."
fi

echo "Setup complete! You can now run the application with: python app.py"
