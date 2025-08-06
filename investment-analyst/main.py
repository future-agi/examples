import os
from dotenv import load_dotenv
from getpass import getpass
from fi_instrumentation import register
from fi_instrumentation.fi_types import ProjectType
from traceai_crewai import CrewAIInstrumentor
from IPython.display import display, Markdown

# --- API Key Setup for Local System ---
load_dotenv()  # Loads variables from .env file

# Prompt for FI API keys if not set in environment
if not os.getenv('FI_API_KEY'):
    os.environ["FI_API_KEY"] = getpass("Enter your FI API Key: ")
if not os.getenv('FI_SECRET_KEY'):
    os.environ["FI_SECRET_KEY"] = getpass("Enter your FI Secret Key: ")

os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
os.environ["FI_API_KEY"] = os.getenv('FI_API_KEY')
os.environ["FI_SECRET_KEY"] = os.getenv('FI_SECRET_KEY')
os.environ["SERPER_API_KEY"] = os.getenv('SERPER_API_KEY')

# --- FutureAGI Tracing Setup ---
trace_provider = register(
    project_type=ProjectType.OBSERVE,
    project_name="crewai_project"
)
CrewAIInstrumentor().instrument(tracer_provider=trace_provider)

# --- Import Agents & Tasks ---
from agents.market_analyst import market_analyst
from agents.company_analyst import company_analyst
from agents.risk_evaluator import risk_evaluator
from agents.strategy_recommender import strategy_recommender

from tasks.market_task import task_market
from tasks.company_task import task_company
from tasks.risk_task import task_risk
from tasks.strategy_task import task_strategy

# --- Set Task Dependencies ---
task_strategy.context = [task_market, task_company, task_risk]

from crewai import Crew, Process

# --- Assemble the Crew ---
crew = Crew(
    agents=[
        market_analyst,
        company_analyst,
        risk_evaluator,
        strategy_recommender
    ],
    tasks=[
        task_market,
        task_company,
        task_risk,
        task_strategy
    ],
    process=Process.sequential,
    verbose=True
)

# --- Run the Crew ---
print("🚀 Kicking off the crew...")
results = crew.kickoff()

# --- Print the Final Results ---
print("\n\n--- Final Recommendation ---")
print(results)