from crewai import Agent
from crewai_tools import SerperDevTool

# Initialize the search tool
search_tool = SerperDevTool()

risk_evaluator = Agent(
    role="Senior Risk Evaluator",
    goal="Identify and evaluate potential risks and challenges for investing in NVIDIA.",
    backstory="""You are a cautious risk evaluator with a deep understanding of market volatility, regulatory changes, and potential pitfalls.
    You are adept at foreseeing potential issues and suggesting mitigation strategies.""",
    tools=[search_tool],
    verbose=True,
    allow_delegation=False
)