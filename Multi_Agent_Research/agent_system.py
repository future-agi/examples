
import asyncio
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# --- LangChain Imports ---
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# Future AGI evals SDK
from fi.evals import Evaluator


# Load API keys from .env file
load_dotenv()


# =========================
# Step 1: Define Agent Roles
# =========================
class AgentRole(Enum):
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CLEANER = "cleaner"
    EXTRACTOR = "extractor"
    ANALYZER = "analyzer"
    IDENTIFIER = "identifier"
    CHECKER = "checker"
    GENERATOR = "generator"
    WRITER = "writer"
    PROOFREADER = "proofreader"


@dataclass
class AgentConfig:
    name: str
    role: AgentRole
    dependencies: List[str]
    timeout: int = 90
    circuit_breaker_threshold: int = 3
    circuit_breaker_timeout: int = 300  # 5 minutes


# ======================================
# Step 2: Circuit Breaker Implementation
# ======================================
class CircuitBreaker:
    def __init__(self, threshold: int, timeout: int):
        self.threshold, self.timeout = threshold, timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "CLOSED"

    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit breaker is OPEN for {func.__self__.config.name}")
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(func.__self__.config.name)
            raise e

    def _on_success(self):
        self.failure_count, self.state = 0, "CLOSED"
    def _on_failure(self, agent_name: str):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        print(f"CircuitBreaker: Failure #{self.failure_count} for {agent_name}.")
        if self.failure_count >= self.threshold:
            self.state = "OPEN"
            print(f"CircuitBreaker: Threshold reached for {agent_name}. State is now OPEN.")

    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        return (datetime.now() - self.last_failure_time).seconds >= self.timeout


# ======================================
# Step 3: Base Agent
# ======================================
class BaseAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config
        self.circuit_breaker = CircuitBreaker(
            config.circuit_breaker_threshold,
            config.circuit_breaker_timeout,
        )

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self.circuit_breaker.call(self._execute_internal, input_data)
        except Exception as e:
            print(f"!! Agent '{self.config.name}' failed: {e}. Using fallback.")
            return self._get_fallback_response(input_data)

    @abstractmethod
    async def _execute_internal(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _get_fallback_response(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


# ======================================
# Step 5: Monitoring and Evaluation (Future AGI)
# ======================================
class AgentMonitor:
    def __init__(
        self,
        future_agi_api_key: str,
        future_agi_secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_eval_templates: Optional[Union[str, List[str]]] = "factual_accuracy",
        default_model_name: Optional[str] = None,
    ):
        self.api_key = future_agi_api_key
        self.secret_key = future_agi_secret_key or os.getenv("FI_SECRET_KEY")
        self.base_url = base_url or os.getenv("FI_BASE_URL")
        self.default_model_name = default_model_name

        self.metrics = {
            "agent_latencies": {},
            "agent_success_rates": {},
            "agent_outputs": {},
        }

        if not self.secret_key:
            raise ValueError("Future AGI secret key is required (pass it or set FI_SECRET_KEY).")

        self.evaluator = Evaluator(
            fi_api_key=self.api_key,
            fi_secret_key=self.secret_key,
            fi_base_url=self.base_url,
        )

        if isinstance(default_eval_templates, str):
            self.default_eval_templates = [default_eval_templates]
        else:
            self.default_eval_templates = default_eval_templates

    async def evaluate_agent_output(
        self,
        agent_name: str,
        output: Dict[str, Any],
        eval_templates: Optional[Union[str, List[str]]] = None,
        model_name: Optional[str] = None,
        extra_inputs: Optional[Dict[str, Any]] = None,
    ):
        templates = eval_templates or self.default_eval_templates
        if isinstance(templates, str):
            templates = [templates]

        if "input" not in output or "output" not in output:
            raise ValueError("`output` must include 'input' and 'output' keys for evaluation.")

        inputs = {"input": output["input"], "output": output["output"]}
        if extra_inputs:
            inputs.update(extra_inputs)

        result = await asyncio.to_thread(
            self.evaluator.evaluate,
            eval_templates=templates,
            inputs=inputs,
            model_name=model_name or self.default_model_name,
        )

        if agent_name not in self.metrics["agent_outputs"]:
            self.metrics["agent_outputs"][agent_name] = []

        summary = None
        try:
            if result and getattr(result, "eval_results", None):
                first = result.eval_results[0]
                summary = {
                    "score": getattr(first, "output", None),
                    "reason": getattr(first, "reason", None),
                }
        except Exception:
            pass

        self.metrics["agent_outputs"][agent_name].append(
            {"inputs": inputs, "evaluation": result, "summary": summary}
        )

        return result

    async def log_agent_performance(self, agent_name: str, latency: float, success: bool):
        if agent_name not in self.metrics["agent_latencies"]:
            self.metrics["agent_latencies"][agent_name] = []
            self.metrics["agent_success_rates"][agent_name] = []

        self.metrics["agent_latencies"][agent_name].append(latency)
        self.metrics["agent_success_rates"][agent_name].append(success)


# ======================================
# Step 4: Agent Orchestrator (with monitoring)
# ======================================
class AgentOrchestrator:
    def __init__(self, monitor: Optional[AgentMonitor] = None, eval_agents: Optional[List[str]] = None):
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_graph: Dict[str, List[str]] = {}
        self.monitor = monitor
        self.eval_agents = eval_agents or ["writer", "proofreader"]

    def register_agent(self, agent: BaseAgent):
        self.agents[agent.config.name] = agent
        self.execution_graph[agent.config.name] = agent.config.dependencies

    async def execute_workflow(self, initial_input: Dict[str, Any]) -> Dict[str, Any]:
        execution_order = self._topological_sort()
        print(f"Workflow execution order: {[a for a in execution_order]}\n")
        results = {"initial": initial_input}

        for agent_name in execution_order:
            agent = self.agents[agent_name]
            agent_input = self._gather_inputs(agent_name, results)
            if not agent.config.dependencies:
                agent_input.update(initial_input)

            print(f"--- Executing Agent: {agent_name} ---")
            start = time.perf_counter()
            success = True
            try:
                result = await asyncio.wait_for(
                    agent.execute(agent_input), timeout=agent.config.timeout
                )
                results[agent_name] = result
            except asyncio.TimeoutError:
                print(f"!! Agent '{agent_name}' timed out. Using fallback.")
                results[agent_name] = agent._get_fallback_response(agent_input)
                success = False
            except Exception as e:
                print(f"!! Agent '{agent_name}' error: {e}. Using fallback.")
                results[agent_name] = agent._get_fallback_response(agent_input)
                success = False
            finally:
                latency = time.perf_counter() - start
                if self.monitor:
                    await self.monitor.log_agent_performance(agent_name, latency, success)

            # Trigger evaluation for selected agents
            if self.monitor and agent_name in self.eval_agents:
                try:
                    if agent_name == "writer" and "draft_report" in results[agent_name]:
                        await self.monitor.evaluate_agent_output(
                            agent_name,
                            {
                                "input": initial_input.get("query", ""),
                                "output": results[agent_name]["draft_report"],
                            },
                        )
                    elif agent_name == "proofreader" and "final_report" in results[agent_name]:
                        await self.monitor.evaluate_agent_output(
                            agent_name,
                            {
                                "input": initial_input.get("query", ""),
                                "output": results[agent_name]["final_report"],
                            },
                        )
                except Exception as eval_err:
                    print(f"Evaluation error for {agent_name}: {eval_err}")

            print(f"--- Finished Agent: {agent_name} ---\n")

        return results

    def _topological_sort(self) -> List[str]:
        visited, stack = set(), []

        def visit(node):
            if node not in visited:
                visited.add(node)
                for dep in self.execution_graph.get(node, []):
                    visit(dep)
                stack.append(node)

        for agent_name in self.agents:
            visit(agent_name)
        return stack

    def _gather_inputs(self, agent_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
        return {dep: results.get(dep) for dep in self.execution_graph.get(agent_name, [])}


# ======================================
# Step 6: Specialized Agents
# ======================================


# AGENT 1: Query Planner
class QueryPlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(AgentConfig(name="planner", role=AgentRole.PLANNER, dependencies=[]))
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        class Queries(BaseModel):
            queries: List[str] = Field(
                description="A list of 3-5 specific, targeted search queries."
            )

        self.parser = JsonOutputParser(pydantic_object=Queries)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                   "You are a research planning expert. Based on the user's query, generate a list of 3-5 specific, diverse search queries to gather comprehensive information. Respond ONLY in the requested JSON format.\n{format_instructions}",
                ),
                ("user", "User Query: {query}"),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())
        self.chain = self.prompt | self.llm | self.parser

    async def _execute_internal(self, data):
        print(f"Planner: Generating search queries for: '{data['query']}'")
        return await self.chain.ainvoke({"query": data["query"]})

    def _get_fallback_response(self, data):
        return {"queries": [data["query"]]}  # Fallback to the original query


# AGENT 2: Researcher
class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(name="researcher", role=AgentRole.RESEARCHER, dependencies=["planner"])
        )
        self.search_tool = TavilySearchResults(max_results=3)

    async def _execute_internal(self, data):
        queries = data["planner"]["queries"]
        print(f"Researcher: Executing queries: {queries}")
        results = await asyncio.gather(
            *[self.search_tool.ainvoke({"query": q}) for q in queries]
        )
        flat_results = [item for sublist in results for item in sublist]
        raw_data = "\n\n".join(
            [f"Source URL: {res['url']}\nContent: {res['content']}" for res in flat_results]
        )
        return {"raw_data": raw_data}

    def _get_fallback_response(self, data):
        return {"raw_data": "Research failed; no data available."}


# AGENT 3: Data Cleaner
class DataCleanerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(name="cleaner", role=AgentRole.CLEANER, dependencies=["researcher"])
        )
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a data cleaning specialist. Your task is to consolidate the provided raw text, remove redundancies, correct formatting, and extract only the most relevant information into a single, clean text block.",
                ),
                ("user", "Raw Data:\n\n{raw_data}"),
            ]
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def _execute_internal(self, data):
        print("Cleaner: Consolidating and cleaning research data...")
        cleaned_data = await self.chain.ainvoke({"raw_data": data["researcher"]["raw_data"]}) 
        return {"cleaned_data": cleaned_data}

    def _get_fallback_response(self, data):
        return {"cleaned_data": data["researcher"]["raw_data"]}  # Pass through raw data


# AGENT 4: Fact Extractor
class FactExtractorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(name="extractor", role=AgentRole.EXTRACTOR, dependencies=["cleaner"])
        )

        class Facts(BaseModel):
            facts: List[str] = Field(
                description="A list of key, verifiable facts extracted from the text."
            )

        self.parser = JsonOutputParser(pydantic_object=Facts)
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a factual analysis expert. Extract a list of key, verifiable facts from the provided text. Focus on specific claims, data points, and statements. Respond ONLY in the requested JSON format.\n{format_instructions}",
                ),
                ("user", "Cleaned Data:\n\n{cleaned_data}"),
            ]
        ).partial(format_instructions=self.parser.get_format_instructions())
        self.chain = self.prompt | self.llm | self.parser

    async def _execute_internal(self, data):
        print("Extractor: Extracting key facts...")
        return await self.chain.ainvoke({"cleaned_data": data["cleaner"]["cleaned_data"]})

    def _get_fallback_response(self, data):
        return {"facts": []}


# AGENT 5: Bias Identifier
class BiasIdentifierAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(name="identifier", role=AgentRole.IDENTIFIER, dependencies=["cleaner"])
        )
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
        self.prompt = ChatPromptTemplate.from_template(
            "Analyze the following text and identify any potential biases (e.g., commercial, political, selection). Summarize your findings in a brief note. If no significant bias is found, state that. Text to analyze: {cleaned_data}"
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def _execute_internal(self, data):
        print("Identifier: Checking for potential biases...")
        bias_note = await self.chain.ainvoke({"cleaned_data": data["cleaner"]["cleaned_data"]})
        return {"bias_note": bias_note}

    def _get_fallback_response(self, data):
        return {"bias_note": "Bias analysis was not available."}


# AGENT 6: Sentiment Analyzer
class SentimentAnalyzerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(name="analyzer", role=AgentRole.ANALYZER, dependencies=["cleaner"])
        )
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.prompt = ChatPromptTemplate.from_template(
            "Analyze the overall sentiment of the following text (e.g., Positive, Negative, Neutral, Mixed) and provide a one-sentence justification. Text: {cleaned_data}"
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def _execute_internal(self, data):
        print("Analyzer: Analyzing overall sentiment...")
        sentiment = await self.chain.ainvoke({"cleaned_data": data["cleaner"]["cleaned_data"]})
        return {"sentiment": sentiment}

    def _get_fallback_response(self, data):
        return {"sentiment": "Sentiment analysis was not available."}


# AGENT 7: Fact Checker (with failure toggle)
class FactCheckerAgent(BaseAgent):
    def __init__(self, should_fail: bool = False):
        super().__init__(
            AgentConfig(name="checker", role=AgentRole.CHECKER, dependencies=["extractor"])
        )
        self.should_fail = should_fail

    async def _execute_internal(self, data):
        if self.should_fail:
            print("Checker: >>> SIMULATING FACT CHECKER API FAILURE <<<")
            raise ConnectionError("External fact-checking service is down.")
        print("Checker: All facts assumed to be verified (in this successful run).")
        return {"verified_facts": data["extractor"]["facts"], "status": "Verified"}

    def _get_fallback_response(self, data):
        return {
            "verified_facts": data["extractor"]["facts"],
            "status": "Verification Failed/Unavailable",
        }


# AGENT 8: Argument Generator
class ArgumentGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(
                name="generator",
                role=AgentRole.GENERATOR,
                dependencies=["checker", "identifier", "analyzer"],
            )
        )
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
        self.prompt = ChatPromptTemplate.from_template(
            """
        You are a master strategist. Synthesize the following information to generate 3-5 key arguments or talking points for a final report.
        
            Verified Facts: {facts}
            Verification Status: {status}
            Bias Note: {bias}
        Overall Sentiment: {sentiment}
        
        Generate the key arguments based on this data.
        """
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def _execute_internal(self, data): 
        print("Generator: Formulating key arguments...")
        args = await self.chain.ainvoke(
            {
                "facts": data["checker"]["verified_facts"],
                "status": data["checker"]["status"],
                "bias": data["identifier"]["bias_note"],
                "sentiment": data["analyzer"]["sentiment"],
            }
        )
        return {"arguments": args}

    def _get_fallback_response(self, data):
        return {"arguments": "Could not generate arguments due to upstream failures."}


# AGENT 9: Report Writer
class ReportWriterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(name="writer", role=AgentRole.WRITER, dependencies=["generator"])
        )
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.prompt = ChatPromptTemplate.from_template(
            "You are a professional report writer. Write a comprehensive, well-structured report based on the following key arguments. The report should be easy to read and informative.\n\nKey Arguments:\n{arguments}"
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def _execute_internal(self, data):
        print("Writer: Drafting the final report...")
        report = await self.chain.ainvoke({"arguments": data["generator"]["arguments"]})
        return {"draft_report": report}

    def _get_fallback_response(self, data):
        return {"draft_report": "Report could not be written."}


# AGENT 10: Proofreader
class ProofreaderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            AgentConfig(
                name="proofreader", role=AgentRole.PROOFREADER, dependencies=["writer"]
            )
        )
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.prompt = ChatPromptTemplate.from_template(
            "You are an expert proofreader. Review the following report for any grammatical errors, spelling mistakes, or awkward phrasing. Make necessary corrections to improve clarity and professionalism. Output only the final, polished version of the report.\n\nDraft Report:\n{draft_report}"
        )
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def _execute_internal(self, data):
        print("Proofreader: Polishing the final report...")
        final_report = await self.chain.ainvoke(
            {"draft_report": data["writer"]["draft_report"]}
        )
        return {"final_report": final_report}

    def _get_fallback_response(self, data):
        return {
            "final_report": data["writer"]["draft_report"]
            + "\n\n--- (Warning: This report was not proofread due to a system error.) ---",
        }


# ======================================
# Step 7: Main Execution Block
# ======================================

async def main():
    if not os.getenv("OPENAI_API_KEY") or not os.getenv("TAVILY_API_KEY"):
        print(
            "FATAL ERROR: API keys not found. Create a .env file with OPENAI_API_KEY and TAVILY_API_KEY."
        )
        return

    # Initialize monitor if FI keys are provided
    monitor: Optional[AgentMonitor] = None
    fi_api_key = os.getenv("FI_API_KEY")
    fi_secret_key = os.getenv("FI_SECRET_KEY")
    fi_base_url = os.getenv("FI_BASE_URL")

    try:
        monitor = AgentMonitor(
            future_agi_api_key=fi_api_key,
            future_agi_secret_key=fi_secret_key,
            base_url=fi_base_url,
            default_eval_templates="factual_accuracy",
            default_model_name="turing_flash",
        )
        print("✅ Future AGI monitor enabled with factual_accuracy evaluation.")
    except Exception as e:
        print(f"⚠️ Failed to initialize Future AGI monitor: {e}")
        monitor = None

    # --- Agents configuration ---
    all_agents_success = [
        QueryPlannerAgent(),
        ResearcherAgent(),
        DataCleanerAgent(),
        FactExtractorAgent(),
        BiasIdentifierAgent(),
        SentimentAnalyzerAgent(),
        FactCheckerAgent(should_fail=False),
        ArgumentGeneratorAgent(),
        ReportWriterAgent(),
        ProofreaderAgent(),
    ]

    initial_query = {
        "query": "The implications of quantum computing advancements on cybersecurity and data privacy."
    }

    # --- Scenario 1: Successful Workflow ---
    print(
        "===================================\n=   RUNNING SUCCESSFUL WORKFLOW   =\n===================================\n"
    )
    orchestrator_success = AgentOrchestrator(monitor=monitor)
    for agent in all_agents_success:
        orchestrator_success.register_agent(agent)
    success_result = await orchestrator_success.execute_workflow(initial_query)
    print("\n FINAL SUCCESSFUL WORKFLOW REPORT ")
    print(success_result.get("proofreader", {}).get("final_report"))
    
    # Print evaluation summaries if available
    if monitor:
        for name in ["writer", "proofreader"]:
            agent_runs = monitor.metrics["agent_outputs"].get(name, [])
            if agent_runs:
                last_summary = agent_runs[-1].get("summary")
                if last_summary:
                    print(
                        f"\nEvaluation ({name}): score={last_summary.get('score')} reason={last_summary.get('reason')}"
                    )


    # Print simple performance metrics
    if monitor:
        print("\nAgent Latencies (seconds):")
        for name, latencies in monitor.metrics["agent_latencies"].items():
            if latencies:
                print(f"- {name}: count={len(latencies)} avg={sum(latencies)/len(latencies):.2f}")
        print("\nAgent Success Rates:")
        for name, outcomes in monitor.metrics["agent_success_rates"].items():
            if outcomes:
                rate = sum(1 for v in outcomes if v) / len(outcomes)
                print(f"- {name}: {rate:.0%} success")


if __name__ == "__main__":
    asyncio.run(main())

