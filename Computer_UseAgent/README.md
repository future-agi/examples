# Computer Use Agent

## Overview

The Computer Use Agent is an AI-powered application that helps monitor and analyze computer usage patterns. It provides insights into application usage, time tracking, and productivity metrics through an intuitive interface. The application uses TraceAI for comprehensive tracing and instrumentation, sending logs to FutureAGI's observability platform for monitoring and analysis.

## Features

- Real-time application usage tracking
- Time spent analysis per application
- Productivity insights and recommendations
- Customizable monitoring settings
- Data visualization and reporting
- Export functionality for usage data
- TraceAI integration for observability
- Automated logging and monitoring

## Requirements

- Python 3.8+
- Required Python packages:
  - psutil
  - pandas
  - matplotlib
  - gradio
  - python-dotenv
  - langgraph-cua
  - traceai-langchain

## Installation

1. Clone or download the repository:

```bash
git clone https://github.com/future-agi/examples.git
cd examples/Computer_UseAgent
```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

3. Set up the environment variables:

```bash
OPENAI_API_KEY=<OpenAI API Key>
FI_API_KEY=<Future AGI API Key>
FI_SECRET_KEY=<Future AGI Secret Key>
SCRAPYBARA_API_KEY= <Scrapybara-Key>
```

4. Run the application:

```bash
python Cua-Observe.py
```

## Usage    
A computer use agent in a virtual environment which follows the user's instructions and performs the task. all the actions are logged and sent to FutureAGI's observability platform for monitoring and evaluation.


