from crewai import Agent
from crewai_tools import SerperDevTool

# Initialize the search tool
search_tool = SerperDevTool()

strategy_recommender = Agent(
    role="Investment Strategy Recommender",
    goal="Synthesize findings from analysts and recommend a comprehensive investment strategy for NVIDIA.",
    backstory="""You are a strategic thinker with a holistic view of investment opportunities and risks.
    You are skilled at combining insights from different domains to formulate sound investment recommendations.""",
    tools=[search_tool],
    verbose=True,
    allow_delegation=False
)