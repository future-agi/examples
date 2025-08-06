from crewai import Agent
from crewai_tools import SerperDevTool

# Initialize the search tool
search_tool = SerperDevTool()

market_analyst = Agent(
    role="Senior Market Analyst",
    goal="Analyze the market demand, identify target audience, and gather competitor information for NVIDIA.",
    backstory="""You are a seasoned market analyst with a keen eye for market trends and competitive landscapes.
    You are adept at using search tools to gather information and provide actionable insights.""",
    tools=[search_tool],
    verbose=True,
    allow_delegation=False
)