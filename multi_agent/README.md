# Multi-Agent Orchestration System

A system that orchestrates multiple specialized agents through a supervisor to solve complex tasks using LangGraph and LangChain.

## Introduction

This project demonstrates a multi-agent orchestration system that leverages LangGraph and LangChain to create a network of specialized agents managed by a supervisor. The system can perform tasks like information retrieval and document creation with minimal human intervention.

## Overview

This project implements a multi-agent system with a supervisor that coordinates specialized worker agents:
- **Supervisor Agent**: Manages the workflow and delegates tasks to specialized agents
- **Search Agent**: Retrieves information using the Tavily search API
- **Document Agent**: Creates and saves documents based on provided information

## Features

- Task delegation through a supervisor agent
- Web search capabilities via Tavily API
- Document creation and storage
- Instrumentation for tracking and evaluation

## Requirements

- Python 3.10+
- OpenAI API key
- Tavily API key
- FI API keys

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/future-agi/examples.git
   cd multi_agent
   ```

2. Create and activate a virtual environment with Python 3.12:
   ```bash
   # macOS/Linux
   python3.12 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Create a `.env` file in the project root with:

```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
FI_API_KEY=your_fi_api_key_here
FI_SECRET_KEY=your_fi_secret_key_here
```

## Usage

Run the agent with a custom prompt:

```bash
python agent-run.py "Your custom prompt here"
```

If no prompt is provided, it will run with the default: "What are the benefits of AI? Create a brief document about it."

## How It Works

1. The system initializes a graph with three nodes: supervisor, search, and document agent
2. The supervisor decides which specialized agent to call next based on the task
3. The search agent uses Tavily to find information
4. The document agent creates and saves documents
5. The process continues until the supervisor decides the task is complete or reaches the recursion limit

## Project Structure

- `agent-run.py`: Main script containing the agent implementation
- `.env`: Environment variables (API keys)
- `eval_tags.py`: Tags for evaluation metrics


## Contact

For questions or support, please contact [support@futureagi.com].




