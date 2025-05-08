# RAG-Agent

## Introduction

RAG-Agent is a Retrieval-Augmented Generation (RAG) system designed to enhance question-answering capabilities by breaking down complex questions into sub-questions, retrieving relevant documents, and generating comprehensive answers using OpenAI's language models. The project leverages LangChain, OpenTelemetry, and Chroma for document retrieval and semantic chunking.

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key


### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/future-agi/examples.git
   cd rag-agent
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
     ```bash
     export OPENAI_API_KEY=your_openai_api_key_here
     export FI_API_KEY=your_fi_api_key_here
     export FI_SECRET_KEY=your_fi_secret_key_here
     ```

## Usage

1. Prepare your dataset in a CSV file named `Ragdata.csv` with a column `Query_Text` containing the questions.

2. Run the main script:
   ```bash
   python rag_agent.py
   ```

3. The results will be saved in `semantic_rag_evaluation.csv`.

## Features

- **Sub-question Generation**: Breaks down complex questions into manageable sub-questions.
- **Document Retrieval**: Retrieves relevant documents for each sub-question using Chroma.
- **Semantic Chunking**: Processes documents into semantic chunks for better context understanding.
- **Comprehensive Answers**: Generates answers by connecting information across multiple contexts.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the MIT License.

## Contact

For questions or support, please contact [support@futureagi.com].