# Text-to-SQL Complex Query Benchmark

This project evaluates the ability of Large Language Models (LLMs) to generate complex SQL queries from natural language questions, using a realistic e-commerce database schema. It is designed for benchmarking and experimentation with models like OpenAI's GPT-4o and DeepSeek.

## Features

- **Complex E-commerce Schema:** Simulates a real-world database with users, products, categories, orders, reviews, and more.
- **Sample Data:** Populates the database with realistic sample data for meaningful query results.
- **Ground Truth Queries:** Includes challenging natural language questions and their correct SQL equivalents for evaluation.
- **LLM Integration:** Uses LangChain to interface with LLMs for SQL generation.
- **Automated Evaluation:** Runs each question through the model, executes the generated SQL, and records results, errors, and latency.
- **Performance Summary:** Outputs results and summary statistics to CSV and JSON files.

## Requirements

- Python 3.9+
- [LangChain](https://github.com/langchain-ai/langchain)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Ollama](https://ollama.com/) (for DeepSeek, optional)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [Pandas](https://pandas.pydata.org/)
- [fi_instrumentation](https://github.com/future-agi/fi-instrumentation) (for tracing, optional)
- [traceai_langchain](https://github.com/future-agi/traceai-langchain) (for tracing, optional)

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Usage

1. **Configure API Keys:**  
   If using OpenAI models, set your `OPENAI_API_KEY` as an environment variable.

2. **Run the Experiment:**

   ```bash
   python main.py
   ```

   This will:
   - Create an in-memory SQLite database with the complex schema and sample data.
   - Run a set of complex natural language questions through the LLM.
   - Save results to `complex_text2sql_results_gpt4o.csv`.
   - Save a summary to `complex_experiment_summary_gpt4o.json`.

3. **Review Results:**
   - Check the CSV for detailed results, including generated SQL, ground truth, execution success, and latency.
   - Check the JSON for summary statistics.

## Customization

- **Add More Questions:**  
  Edit the `COMPLEX_TEXT2SQL_GROUND_TRUTH` dictionary in `main.py` to add or modify questions and their expected SQL.

- **Switch Models:**  
  Change the model name in the `main()` function or use the `run_complex_text2sql_experiment()` function with a different model (e.g., `"deepseek"`).

- **Schema/Data:**  
  Modify `COMPLEX_DB_SCHEMA` and `COMPLEX_SAMPLE_DATA` in `main.py` to experiment with different database structures or data.

## File Structure

- `main.py` — Main experiment script.
- `complex_text2sql_results_gpt4o.csv` — Results of the latest experiment.
- `complex_experiment_summary_gpt4o.json` — Summary statistics of the latest experiment.
- `requirements.txt` — Python dependencies.

## Example Output
