import os
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType, EvalSpanKind, EvalName, EvalTag, EvalTagType, ModelChoices
from traceai_langchain import LangChainInstrumentor
from langchain.schema import HumanMessage
from langchain.schema import HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
class ResearchRequest(BaseModel):
    prompt: str

# Load environment variables from .env file
load_dotenv()
api_key=os.getenv("OPENAI_API_KEY")

model = ChatOpenAI(model="gpt-4o",api_key=api_key, temperature=0.0)
eval_tags=[
        
        EvalTag(
            type=EvalTagType.OBSERVATION_SPAN,
            value=EvalSpanKind.TOOL,
            eval_name=EvalName.EVALUATE_LLM_FUNCTION_CALLING,
            mapping={
                "input":"tool.name",
                "output":"raw.output",
            },
            custom_eval_name="Tool_Function_Calling",
            model=ModelChoices.TURING_LARGE
        ),
       
        EvalTag(
            type=EvalTagType.OBSERVATION_SPAN,
            value=EvalSpanKind.LLM,
            mapping={
                'output' : "raw.output"
            },
            eval_name=EvalName.SUMMARY_QUALITY,
            custom_eval_name="SUMMARY_QUALITY",
            model=ModelChoices.TURING_LARGE,  # Use ModelChoices for model selection
        ),
       EvalTag(
            type=EvalTagType.OBSERVATION_SPAN,
            value=EvalSpanKind.LLM,
            mapping={
                "input": "raw.input",
                'output' : "raw.output"
            },
            eval_name=EvalName.DETECT_HALLUCINATION,
            custom_eval_name="Hallucination",
            model=ModelChoices.TURING_LARGE,  # Use ModelChoices for model selection
        ),
       EvalTag(
            type=EvalTagType.OBSERVATION_SPAN,
            value=EvalSpanKind.LLM,
            eval_name=EvalName.COMPLETENESS,
            config={},
            mapping={
                "input": "raw.input",
                "output": "raw.output"
            },
            custom_eval_name="Completeness",
            model=ModelChoices.TURING_LARGE
        ),
        
         EvalTag(
            type=EvalTagType.OBSERVATION_SPAN,
            value=EvalSpanKind.TOOL,
            eval_name="paper_relevance",
            config={},
            mapping={
                "query": "raw.input",
                "papers": "raw.output"
            },
            custom_eval_name="check_paper_relevance",
        ),
    ]

app = FastAPI(title="Research Assistant API")
trace_provider = register(
    project_type=ProjectType.EXPERIMENT,
    project_name="research_assistant_mcp",
    eval_tags=eval_tags
)

LangChainInstrumentor().instrument(tracer_provider=trace_provider)
async def process_prompt(prompt: str) -> Dict[str, Any]:
    mcp_client = MultiServerMCPClient({
        "arxiv": {
            "url": "http://arxiv-server:8000/sse",  # Use Docker service name
            "transport": "sse",
        },
        "docling": {
            "url": "http://docling-server:8001/sse",  # Use Docker service name
            "transport": "sse",
        }
    })
    async with mcp_client as client:
        agent = create_react_agent(model, client.get_tools())
        def flatten(state):
            # state["messages"] is the running chat history
            user_text = next(m.content for m in state["messages"] if m.type == "human")
            ai_text   = next(m.content for m in reversed(state["messages"]) if m.type == "ai")
            return {"input": user_text, "output": ai_text}

        graph = agent | RunnableLambda(flatten)
        # response = await agent.ainvoke({"messages": prompt}, debug=False)
        state = {"messages": [HumanMessage(content=prompt)]}
        print(f"State before invoking agent: {state}")
        agent = graph.with_config({"run_name": "ResearchAgent"})
        response = await agent.ainvoke(state,debug=False)
        # messages = [{i.type: i.content} for i in response['messages'] if i.content!='']
        # ai_msg = next(m for m in reversed(response["messages"]) if m.type == "ai")
        # return {"answer": ai_msg.content}
        # return {"messages": messages}
        return response

@app.post("/research")
async def research(request: ResearchRequest):
    """Process a research query using arxiv and document analysis tools"""
    answer = await process_prompt(request.prompt)
    return {
        "messages": [{"human":answer["input"]},{"ai": answer["output"]}],
    }

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8080)