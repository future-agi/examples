# UV Installation Guide for LlamaIndex Demo

This guide provides detailed instructions for installing and using the LlamaIndex demo with the UV package manager.

## What is UV?

UV is a modern Python package installer and resolver, designed to be significantly faster and more reliable than pip. It's written in Rust and provides several advantages:

- Much faster installation speeds
- Improved dependency resolution
- Better caching
- Reliable virtual environment management

## Installation Options

### Option 1: Automated Setup (Recommended)

We've provided a setup script that handles everything for you:

1. Navigate to the project directory:
```bash
cd llamaindex_demo
```

2. Run the setup script:
```bash
./setup.sh
```

This script will:
- Install UV if not already present
- Create a virtual environment
- Install all required dependencies
- Create a template .env file

### Option 2: Manual Setup

If you prefer to install manually:

1. Install UV:
```bash
curl -sSf https://install.ultraviolet.rs | sh
export PATH="$HOME/.cargo/bin:$PATH"
```

2. Create and activate a virtual environment:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install llama-index llama-index-readers-database llama-index-embeddings-openai llama-index-llms-openai gradio python-dotenv sqlalchemy psycopg2-binary pymysql google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Troubleshooting

### Common Issues

1. **UV not found after installation**
   - Make sure to add UV to your PATH: `export PATH="$HOME/.cargo/bin:$PATH"`
   - On Windows, restart your terminal or add the path manually

2. **Permission errors during installation**
   - Try running with sudo: `sudo curl -sSf https://install.ultraviolet.rs | sh`
   - Or use the `--user` flag: `uv pip install --user [packages]`

3. **Dependency conflicts**
   - UV has better resolution than pip, but if conflicts occur, try: `uv pip install --reinstall [problematic-package]`

### Getting Help

- UV Documentation: [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)
- Report issues with this demo on the project's issue tracker

## Additional UV Commands

- Update all packages: `uv pip install --upgrade [packages]`
- List installed packages: `uv pip list`
- Uninstall a package: `uv pip uninstall [package]`
- Create requirements file: `uv pip freeze > requirements.txt`
