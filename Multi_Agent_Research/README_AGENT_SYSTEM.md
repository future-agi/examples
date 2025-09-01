# 🤖 10-Agent Orchestration System with Circuit Breaker Pattern

## 🚀 Quick Start (For Your Video!)

### 1. Install Dependencies
```bash
cd SDK_Testing
pip install -r requirements.txt
```

### 2. Set Up API Keys
Create a `.env` file in SDK_Testing folder:
```env
# Required
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key

# Optional (for Future AGI monitoring)
FI_API_KEY=30144ee1f5eb46f8ace092311e708076
FI_SECRET_KEY=43a27876f61d4c938d8d8915f919c05e
FI_BASE_URL=https://dev.api.futureagi.com
```

**Get your keys:**
- OpenAI: https://platform.openai.com/api-keys
- Tavily (free tier available): https://tavily.com/

### 3. Run the Demo
```bash
python agent_system.py
```

Or use the automated script:
```bash
./run_agent_system.sh
```

## 🎬 What It Does

The system demonstrates:

1. **10 Specialized Agents** working together:
   - Query Planner → Researcher → Data Cleaner → Fact Extractor
   - Bias Identifier, Sentiment Analyzer, Fact Checker
   - Argument Generator → Report Writer → Proofreader

2. **Circuit Breaker Pattern** preventing cascade failures
3. **Future AGI Integration** for output quality evaluation
4. **Automatic Fallback** mechanisms

## 📊 Demo Scenarios

The script runs TWO scenarios automatically:

### ✅ Scenario 1: Successful Workflow
- All agents work correctly
- Produces a polished research report
- Shows evaluation scores (if Future AGI is configured)

### 🛑 Scenario 2: Failure Handling
- Fact Checker agent intentionally fails
- Circuit breaker activates after 3 failures
- System continues with fallback responses
- Demonstrates resilience

## 🎯 Key Features for Your Video

1. **Real-time Progress**: Watch each agent execute in sequence
2. **Performance Metrics**: See latency and success rates
3. **Quality Evaluation**: Future AGI scores for writer/proofreader outputs
4. **Failure Recovery**: Circuit breaker in action

## 📝 Sample Output

```
=== RUNNING SUCCESSFUL WORKFLOW ===
Workflow execution order: ['planner', 'researcher', 'cleaner', ...]

--- Executing Agent: planner ---
Planner: Generating search queries...
--- Finished Agent: planner ---

[... agents execute ...]

✅✅✅ FINAL SUCCESSFUL WORKFLOW REPORT ✅✅✅
[Complete research report about renewable energy]

Evaluation (writer): score=0.85 reason="Comprehensive and well-structured"
Evaluation (proofreader): score=0.92 reason="Excellent clarity and polish"

Agent Latencies (seconds):
- planner: count=1 avg=1.23
- researcher: count=1 avg=3.45
[...]

Agent Success Rates:
- planner: 100% success
- researcher: 100% success
[...]
```

## 🔧 Troubleshooting

If you get import errors:
```bash
pip install langchain langchain-community langchain-openai tavily-python python-dotenv pydantic
```

If Future AGI isn't working, you can run without it - just don't set the FI_* keys in .env

## 💡 Tips for Recording

1. Clear terminal before running for clean output
2. The full run takes ~2-3 minutes
3. Most interesting parts:
   - Agent execution sequence
   - Circuit breaker activation (in failure scenario)
   - Final reports comparison
   - Performance metrics at the end
