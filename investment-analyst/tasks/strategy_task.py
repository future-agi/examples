from crewai import Task
from agents.strategy_recommender import strategy_recommender

task_strategy = Task(
    description=(
        "Combine all provided reports for NVIDIA to give a Buy/Sell/Hold recommendation with reasons. "
        "Evaluate it based on the combined findings."
    ),
    expected_output=(
        "A final recommendation (Buy/Sell/Hold) for NVIDIA, a summary of the key reasons, "
        "and two important disclaimers for the investment."
    ),
    agent=strategy_recommender
)