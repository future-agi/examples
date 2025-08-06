from crewai import Task
from agents.market_analyst import market_analyst

task_market = Task(
    description=(
        "Analyze the latest market trends, competitive landscape, and economic "
        "indicators relevant to NVIDIA. Focus on the most recent quarter."
    ),
    expected_output=(
        "A concise report on market conditions, competitor performance (like AMD and Intel), "
        "and overall industry sentiment for the semiconductor and AI sectors."
    ),
    agent=market_analyst,
    context=[]
)