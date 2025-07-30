from crewai import Task
from agents.risk_evaluator import risk_evaluator

task_risk = Task(
    description=(
        "Identify and evaluate the market, operational, legal, and "
        "regulatory risks associated with NVIDIA."
    ),
    expected_output=(
        "A comprehensive summary of potential risks for NVIDIA, including supply chain, "
        "geopolitical (e.g., related to China), and market competition risks."
    ),
    agent=risk_evaluator,
    context=[]
)