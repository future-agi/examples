# 🤖 10-Agent Orchestration System with Future AGI Evaluation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd SDK_Testing/multi_agent
pip install -r requirements.txt
```

### 2. Set Up API Keys
Create a `.env` file:
```bash
cp env_template.txt .env
# Edit .env and add your OPENAI_API_KEY and TAVILY_API_KEY
```

**Required Keys:**
- `OPENAI_API_KEY`: Get from https://platform.openai.com/api-keys
- `TAVILY_API_KEY`: Get free tier at https://tavily.com/

**Note:** Future AGI keys are already configured in the code for demo purposes.

### 3. Run the Demo
```bash
python agent_system.py
```

## 🎬 What You'll See

The system demonstrates **10 specialized agents** working together:

1. **Query Planner** - Generates search queries
2. **Researcher** - Performs web searches via Tavily
3. **Data Cleaner** - Consolidates and cleans data
4. **Fact Extractor** - Extracts key facts
5. **Bias Identifier** - Checks for biases
6. **Sentiment Analyzer** - Analyzes sentiment
7. **Fact Checker** - Verifies facts
8. **Argument Generator** - Creates key arguments
9. **Report Writer** - Drafts the report
10. **Proofreader** - Polishes the final output

## 📊 Features

- **Circuit Breaker Pattern**: Prevents cascade failures
- **Future AGI Integration**: Evaluates output quality using `factual_accuracy`
- **Performance Metrics**: Tracks latency and success rates
- **Automatic Fallbacks**: Graceful degradation on failures

## 📝 Sample Output

```
✅ Future AGI monitor enabled with factual_accuracy evaluation.

=== RUNNING SUCCESSFUL WORKFLOW ===
Workflow execution order: ['planner', 'researcher', 'cleaner', ...]

--- Executing Agent: planner ---
Planner: Generating search queries...
--- Finished Agent: planner ---

[... all agents execute ...]

✅✅✅ FINAL SUCCESSFUL WORKFLOW REPORT ✅✅✅
[Complete research report about renewable energy]

Evaluation (writer): score=0.85 reason="Well-structured and comprehensive"
Evaluation (proofreader): score=0.92 reason="Clear and professionally written"

Agent Latencies (seconds):
- planner: count=1 avg=1.23
- researcher: count=1 avg=3.45
...

Agent Success Rates:
- planner: 100% success
- researcher: 100% success
...
```

## ⏱️ Runtime

The demo takes approximately 1-2 minutes to complete, depending on API response times.
