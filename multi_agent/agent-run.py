import getpass
import os
from dotenv import load_dotenv
from typing import Annotated, List, Literal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing_extensions import TypedDict

from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command



# Load environment variables
load_dotenv('/Users/apple/Future AGI/examples/.env')

def _set_if_undefined(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"Please provide your {var}")

_set_if_undefined("OPENAI_API_KEY")
_set_if_undefined("TAVILY_API_KEY")


from eval_tags import list_of_eval_tags
from traceai_langchain import LangChainInstrumentor
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType

trace_provider = register(
    project_type=ProjectType.EXPERIMENT,
    project_name="langchain_project",
    project_version_name="multi-step-agent",
    eval_tags=list_of_eval_tags
)

LangChainInstrumentor().instrument(tracer_provider=trace_provider)


# Create working directory for file operations
_TEMP_DIRECTORY = TemporaryDirectory()
WORKING_DIRECTORY = Path(_TEMP_DIRECTORY.name)

# Initialize tools - just two core tools
tavily_tool = TavilySearchResults(max_results=2)  # Further reduced max results

@tool
def write_document(
    content: Annotated[str, "Text content to be written into the document."],
    file_name: Annotated[str, "File path to save the document."],
) -> str:
    """Create and save a text document."""
    with (WORKING_DIRECTORY / file_name).open("w") as file:
        file.write(content)
    return f"Document saved to {file_name}"

# Define the state class for the graph
class State(MessagesState):
    next: str

# Create supervisor node function - simplified
def make_supervisor_node(llm: BaseChatModel, members: list[str]):
    options = ["FINISH"] + members
    system_prompt = (
        f"You are a supervisor managing workers: {members}. "
        "Given the user request, respond with which worker to use next. "
        "When completed, respond with FINISH. Be efficient and minimize steps."
    )

    class Router(TypedDict):
        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        
        # End quickly if we have a lot of messages
        if len(state["messages"]) > 5:
            return Command(goto=END)
            
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    return supervisor_node

# Initialize a faster LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Create simplified search agent
search_agent = create_react_agent(
    llm, 
    tools=[tavily_tool],
    prompt="You are a search agent. Provide concise information from search results."
)

def search_node(state: State) -> Command[Literal["supervisor"]]:
    result = search_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="search")
            ]
        },
        goto="supervisor",
    )

# Create simplified document agent
document_agent = create_react_agent(
    llm,
    tools=[write_document],
    prompt="You are a document agent. Create documents based on information provided."
)

def document_node(state: State) -> Command[Literal["supervisor"]]:
    result = document_agent.invoke(state)
    return Command(
        update={
            "messages": [
                HumanMessage(content=result["messages"][-1].content, name="document_agent")
            ]
        },
        goto="supervisor",
    )

# Create the main supervisor node - reduced to just two workers
main_supervisor_node = make_supervisor_node(llm, ["search", "document_agent"])

# Build a minimal graph
builder = StateGraph(State)
builder.add_node("supervisor", main_supervisor_node)
builder.add_node("search", search_node)
builder.add_node("document_agent", document_node)
builder.add_edge(START, "supervisor")
builder.add_edge("supervisor", "search")
builder.add_edge("supervisor", "document_agent")

graph = builder.compile()

# Main function to run the agent with custom prompts
def run_agent(prompt):
    """Run the agent with a custom prompt."""
    print(f"Running agent with prompt: '{prompt}'")
    print("Processing...")
    
    try:
        for s in graph.stream(
            {"messages": [("user", prompt)]},
            {"recursion_limit": 8},  # Significantly reduced recursion limit
        ):
            print(s)
            print("---")
    except Exception as e:
        print(f"Error: {e}")
    
    print("Processing complete!")

# Run the agent with a prompt
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        prompt = "What are the benefits of AI? Create a brief document about it."
    
    run_agent(prompt)