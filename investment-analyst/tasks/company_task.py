from crewai import Task
from agents.company_analyst import company_analyst

task_company = Task(
    description=(
        "Conduct a thorough analysis of NVIDIA's financial health. "
        "Look at revenue growth, profit margins, and key performance metrics "
        "from their most recent earnings reports."
    ),
    expected_output=(
        "A detailed report on NVIDIA's financial stability, growth "
        "prospects, and recent developments, including actual figures."
    ),
    agent=company_analyst,
    context=[]
)