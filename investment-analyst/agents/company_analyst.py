from crewai import Agent
from crewai_tools import SerperDevTool

# Initialize the search tool
search_tool = SerperDevTool()

company_analyst = Agent(
    role="Senior Company Analyst",
    goal="Analyze NVIDIA's financials, structure, and operations.",
    backstory="""You are a skilled company analyst with expertise in dissecting company reports and public filings.
    You are detail-oriented and capable of extracting key information.""",
    tools=[search_tool],
    verbose=True,
    allow_delegation=False
)