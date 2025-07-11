"""
Task Planning and Execution System
Handles complex questions by breaking them down into executable steps
"""

import asyncio
import json
from typing import List, Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TaskType(Enum):
    """Types of tasks the system can execute"""
    STOCK_ANALYSIS = "stock_analysis"
    MARKET_RESEARCH = "market_research"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    COMPARISON = "comparison"
    EDUCATION = "education"
    STRATEGY_PLANNING = "strategy_planning"
    RISK_ASSESSMENT = "risk_assessment"
    DATA_RETRIEVAL = "data_retrieval"

class TaskStatus(Enum):
    """Status of task execution"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TaskStep:
    """Represents a single step in task execution"""
    id: str
    type: TaskType
    description: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['type'] = self.type.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class ExecutionPlan:
    """Complete execution plan for a complex query"""
    id: str
    original_query: str
    steps: List[TaskStep]
    context: Dict[str, Any]
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['steps'] = [step.to_dict() for step in self.steps]
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data

class TaskPlanner:
    """
    Intelligent task planner that breaks down complex queries into executable steps
    """
    
    def __init__(self, openai_client=None):
        """Initialize task planner"""
        self.openai_client = openai_client
        self.execution_plans: Dict[str, ExecutionPlan] = {}
        
        # Register available task executors
        self.task_executors: Dict[TaskType, Callable] = {
            TaskType.STOCK_ANALYSIS: self._execute_stock_analysis,
            TaskType.MARKET_RESEARCH: self._execute_market_research,
            TaskType.PORTFOLIO_ANALYSIS: self._execute_portfolio_analysis,
            TaskType.COMPARISON: self._execute_comparison,
            TaskType.EDUCATION: self._execute_education,
            TaskType.STRATEGY_PLANNING: self._execute_strategy_planning,
            TaskType.RISK_ASSESSMENT: self._execute_risk_assessment,
            TaskType.DATA_RETRIEVAL: self._execute_data_retrieval
        }
    
    async def create_execution_plan(self, query: str, context: Dict[str, Any] = None) -> ExecutionPlan:
        """Create an execution plan for a complex query"""
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Analyze query complexity and determine required steps
        steps = await self._analyze_and_plan(query, context or {})
        
        plan = ExecutionPlan(
            id=plan_id,
            original_query=query,
            steps=steps,
            context=context or {},
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.execution_plans[plan_id] = plan
        logger.info(f"Created execution plan {plan_id} with {len(steps)} steps")
        
        return plan
    
    async def execute_plan(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Execute a complete plan"""
        plan.status = TaskStatus.IN_PROGRESS
        results = {}
        
        try:
            # Execute steps in dependency order
            executed_steps = set()
            
            while len(executed_steps) < len(plan.steps):
                # Find steps ready for execution (dependencies satisfied)
                ready_steps = [
                    step for step in plan.steps
                    if step.status == TaskStatus.PENDING and
                    all(dep in executed_steps for dep in step.dependencies)
                ]
                
                if not ready_steps:
                    # Check for circular dependencies or other issues
                    pending_steps = [s for s in plan.steps if s.status == TaskStatus.PENDING]
                    if pending_steps:
                        logger.error(f"Cannot execute remaining steps: {[s.id for s in pending_steps]}")
                        for step in pending_steps:
                            step.status = TaskStatus.FAILED
                            step.error = "Dependency resolution failed"
                    break
                
                # Execute ready steps (can be done in parallel)
                tasks = []
                for step in ready_steps:
                    task = self._execute_step(step, results)
                    tasks.append(task)
                
                # Wait for all tasks to complete
                step_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(step_results):
                    step = ready_steps[i]
                    if isinstance(result, Exception):
                        step.status = TaskStatus.FAILED
                        step.error = str(result)
                        logger.error(f"Step {step.id} failed: {result}")
                    else:
                        step.status = TaskStatus.COMPLETED
                        step.result = result
                        results[step.id] = result
                        executed_steps.add(step.id)
                        logger.info(f"Step {step.id} completed successfully")
            
            # Combine results
            final_result = await self._combine_results(plan, results)
            
            plan.status = TaskStatus.COMPLETED
            plan.completed_at = datetime.now()
            
            return {
                "plan_id": plan.id,
                "status": "completed",
                "results": final_result,
                "execution_summary": self._get_execution_summary(plan)
            }
            
        except Exception as e:
            plan.status = TaskStatus.FAILED
            logger.error(f"Plan execution failed: {e}")
            
            return {
                "plan_id": plan.id,
                "status": "failed",
                "error": str(e),
                "partial_results": results
            }
    
    async def _analyze_and_plan(self, query: str, context: Dict[str, Any]) -> List[TaskStep]:
        """Analyze query and create execution steps"""
        # Use AI to analyze query if available, otherwise use rule-based approach
        if self.openai_client:
            return await self._ai_analyze_and_plan(query, context)
        else:
            return self._rule_based_plan(query, context)
    
    async def _ai_analyze_and_plan(self, query: str, context: Dict[str, Any]) -> List[TaskStep]:
        """Use AI to analyze query and create execution plan"""
        try:
            from src.integrations.openai.client import ModelType
            
            planning_prompt = f"""
            You are an expert trading assistant task planner. Analyze the following query and break it down into executable steps.
            
            Query: {query}
            Context: {json.dumps(context, indent=2)}
            
            Available task types:
            - stock_analysis: Analyze individual stocks
            - market_research: Research market trends and conditions
            - portfolio_analysis: Analyze portfolio composition and performance
            - comparison: Compare multiple stocks or strategies
            - education: Provide educational content
            - strategy_planning: Develop investment strategies
            - risk_assessment: Assess investment risks
            - data_retrieval: Retrieve specific market data
            
            Create a step-by-step execution plan. For each step, provide:
            1. A unique step ID
            2. Task type from the available types
            3. Clear description of what the step does
            4. Parameters needed for execution
            5. Dependencies on other steps (use step IDs)
            
            Return your response as a JSON array of steps with this structure:
            [
                {{
                    "id": "step_1",
                    "type": "stock_analysis",
                    "description": "Analyze Apple stock fundamentals",
                    "parameters": {{"symbol": "AAPL", "analysis_type": "fundamental"}},
                    "dependencies": []
                }}
            ]
            
            Make sure the plan is logical, efficient, and addresses the user's query completely.
            """
            
            messages = [
                {"role": "system", "content": "You are an expert task planner for trading and investment analysis. Provide clear, executable plans in JSON format."},
                {"role": "user", "content": planning_prompt}
            ]
            
            response = await self.openai_client.chat_completion(messages, ModelType.GPT_4O)
            
            # Parse AI response
            try:
                steps_data = json.loads(response.choices[0].message.content)
                steps = []
                
                for step_data in steps_data:
                    step = TaskStep(
                        id=step_data["id"],
                        type=TaskType(step_data["type"]),
                        description=step_data["description"],
                        parameters=step_data["parameters"],
                        dependencies=step_data.get("dependencies", []),
                        status=TaskStatus.PENDING
                    )
                    steps.append(step)
                
                return steps
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Error parsing AI planning response: {e}")
                return self._rule_based_plan(query, context)
                
        except Exception as e:
            logger.error(f"AI planning failed: {e}")
            return self._rule_based_plan(query, context)
    
    def _rule_based_plan(self, query: str, context: Dict[str, Any]) -> List[TaskStep]:
        """Create execution plan using rule-based approach"""
        steps = []
        query_lower = query.lower()
        
        # Extract mentioned stocks
        import re
        stock_symbols = re.findall(r'\b([A-Z]{2,5})\b', query.upper())
        
        # Determine query type and create appropriate steps
        if "compare" in query_lower and len(stock_symbols) >= 2:
            # Comparison query
            for i, symbol in enumerate(stock_symbols[:3]):  # Limit to 3 stocks
                steps.append(TaskStep(
                    id=f"analyze_{symbol.lower()}",
                    type=TaskType.STOCK_ANALYSIS,
                    description=f"Analyze {symbol} stock",
                    parameters={"symbol": symbol, "analysis_type": "comprehensive"},
                    dependencies=[],
                    status=TaskStatus.PENDING
                ))
            
            # Add comparison step
            steps.append(TaskStep(
                id="compare_stocks",
                type=TaskType.COMPARISON,
                description=f"Compare {', '.join(stock_symbols[:3])}",
                parameters={"symbols": stock_symbols[:3], "comparison_type": "comprehensive"},
                dependencies=[f"analyze_{symbol.lower()}" for symbol in stock_symbols[:3]],
                status=TaskStatus.PENDING
            ))
        
        elif any(word in query_lower for word in ["portfolio", "diversification", "allocation"]):
            # Portfolio analysis
            steps.append(TaskStep(
                id="portfolio_analysis",
                type=TaskType.PORTFOLIO_ANALYSIS,
                description="Analyze portfolio composition and performance",
                parameters={"stocks": stock_symbols, "analysis_type": "comprehensive"},
                dependencies=[],
                status=TaskStatus.PENDING
            ))
            
            steps.append(TaskStep(
                id="risk_assessment",
                type=TaskType.RISK_ASSESSMENT,
                description="Assess portfolio risk",
                parameters={"portfolio_data": "from_portfolio_analysis"},
                dependencies=["portfolio_analysis"],
                status=TaskStatus.PENDING
            ))
        
        elif any(word in query_lower for word in ["strategy", "plan", "approach"]):
            # Strategy planning
            steps.append(TaskStep(
                id="market_research",
                type=TaskType.MARKET_RESEARCH,
                description="Research current market conditions",
                parameters={"scope": "general", "timeframe": "current"},
                dependencies=[],
                status=TaskStatus.PENDING
            ))
            
            steps.append(TaskStep(
                id="strategy_planning",
                type=TaskType.STRATEGY_PLANNING,
                description="Develop investment strategy",
                parameters={"market_data": "from_market_research", "user_profile": context.get("user_preferences", {})},
                dependencies=["market_research"],
                status=TaskStatus.PENDING
            ))
        
        elif any(word in query_lower for word in ["what is", "explain", "how does", "learn"]):
            # Educational query
            steps.append(TaskStep(
                id="education",
                type=TaskType.EDUCATION,
                description="Provide educational content",
                parameters={"topic": query, "level": context.get("user_preferences", {}).get("experience_level", "intermediate")},
                dependencies=[],
                status=TaskStatus.PENDING
            ))
        
        elif stock_symbols:
            # Single or multiple stock analysis
            for symbol in stock_symbols[:3]:  # Limit to 3 stocks
                steps.append(TaskStep(
                    id=f"analyze_{symbol.lower()}",
                    type=TaskType.STOCK_ANALYSIS,
                    description=f"Analyze {symbol} stock",
                    parameters={"symbol": symbol, "analysis_type": "comprehensive"},
                    dependencies=[],
                    status=TaskStatus.PENDING
                ))
        
        else:
            # General query - try to provide helpful response
            steps.append(TaskStep(
                id="general_response",
                type=TaskType.EDUCATION,
                description="Provide general trading assistance",
                parameters={"query": query, "context": context},
                dependencies=[],
                status=TaskStatus.PENDING
            ))
        
        return steps
    
    async def _execute_step(self, step: TaskStep, previous_results: Dict[str, Any]) -> Any:
        """Execute a single step"""
        step.status = TaskStatus.IN_PROGRESS
        start_time = datetime.now()
        
        try:
            # Get executor for this task type
            executor = self.task_executors.get(step.type)
            if not executor:
                raise ValueError(f"No executor found for task type: {step.type}")
            
            # Resolve parameter dependencies
            resolved_params = self._resolve_parameters(step.parameters, previous_results)
            
            # Execute the step
            result = await executor(step, resolved_params, previous_results)
            
            step.execution_time = (datetime.now() - start_time).total_seconds()
            return result
            
        except Exception as e:
            step.execution_time = (datetime.now() - start_time).total_seconds()
            raise e
    
    def _resolve_parameters(self, parameters: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter dependencies from previous step results"""
        resolved = {}
        
        for key, value in parameters.items():
            if isinstance(value, str) and value.startswith("from_"):
                # This is a dependency reference
                dependency_step = value.replace("from_", "")
                if dependency_step in previous_results:
                    resolved[key] = previous_results[dependency_step]
                else:
                    logger.warning(f"Could not resolve dependency: {value}")
                    resolved[key] = None
            else:
                resolved[key] = value
        
        return resolved
    
    async def _execute_stock_analysis(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute stock analysis step"""
        symbol = parameters.get("symbol")
        analysis_type = parameters.get("analysis_type", "comprehensive")
        
        if not symbol:
            raise ValueError("Stock symbol is required for stock analysis")
        
        # This would integrate with the existing stock analysis system
        # For now, return a placeholder result
        return {
            "symbol": symbol,
            "analysis_type": analysis_type,
            "recommendation": "HOLD",
            "confidence": 75,
            "key_metrics": {
                "price": 150.00,
                "pe_ratio": 25.5,
                "rsi": 55.2
            },
            "analysis": f"Comprehensive analysis of {symbol} completed"
        }
    
    async def _execute_market_research(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market research step"""
        scope = parameters.get("scope", "general")
        timeframe = parameters.get("timeframe", "current")
        
        return {
            "scope": scope,
            "timeframe": timeframe,
            "market_sentiment": "neutral",
            "key_trends": ["AI adoption", "Interest rate concerns", "Inflation moderation"],
            "sector_performance": {
                "technology": "outperforming",
                "healthcare": "stable",
                "energy": "underperforming"
            }
        }
    
    async def _execute_portfolio_analysis(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio analysis step"""
        stocks = parameters.get("stocks", [])
        
        return {
            "portfolio_size": len(stocks),
            "diversification_score": 7.5,
            "risk_level": "moderate",
            "expected_return": 8.5,
            "recommendations": ["Consider adding international exposure", "Rebalance quarterly"]
        }
    
    async def _execute_comparison(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comparison step"""
        symbols = parameters.get("symbols", [])
        comparison_type = parameters.get("comparison_type", "basic")
        
        return {
            "symbols": symbols,
            "comparison_type": comparison_type,
            "winner": symbols[0] if symbols else None,
            "comparison_matrix": {
                "valuation": {symbol: "fair" for symbol in symbols},
                "growth": {symbol: "moderate" for symbol in symbols},
                "risk": {symbol: "medium" for symbol in symbols}
            }
        }
    
    async def _execute_education(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute education step"""
        topic = parameters.get("topic", "")
        level = parameters.get("level", "intermediate")
        
        return {
            "topic": topic,
            "level": level,
            "content": f"Educational content about {topic} at {level} level",
            "key_points": ["Point 1", "Point 2", "Point 3"],
            "next_steps": ["Practice with examples", "Read additional resources"]
        }
    
    async def _execute_strategy_planning(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute strategy planning step"""
        market_data = parameters.get("market_data", {})
        user_profile = parameters.get("user_profile", {})
        
        return {
            "strategy_type": "balanced growth",
            "asset_allocation": {
                "stocks": 70,
                "bonds": 20,
                "cash": 10
            },
            "timeline": "5-10 years",
            "key_actions": ["Dollar-cost averaging", "Quarterly rebalancing", "Tax-loss harvesting"]
        }
    
    async def _execute_risk_assessment(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk assessment step"""
        portfolio_data = parameters.get("portfolio_data", {})
        
        return {
            "overall_risk": "moderate",
            "risk_score": 6.5,
            "risk_factors": ["Market volatility", "Concentration risk", "Interest rate risk"],
            "mitigation_strategies": ["Diversification", "Stop-loss orders", "Regular rebalancing"]
        }
    
    async def _execute_data_retrieval(self, step: TaskStep, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data retrieval step"""
        data_type = parameters.get("data_type", "market")
        symbols = parameters.get("symbols", [])
        
        return {
            "data_type": data_type,
            "symbols": symbols,
            "timestamp": datetime.now().isoformat(),
            "data": {"placeholder": "market data would be here"}
        }
    
    async def _combine_results(self, plan: ExecutionPlan, results: Dict[str, Any]) -> Dict[str, Any]:
        """Combine results from all steps into final response"""
        completed_steps = [step for step in plan.steps if step.status == TaskStatus.COMPLETED]
        failed_steps = [step for step in plan.steps if step.status == TaskStatus.FAILED]
        
        combined_result = {
            "original_query": plan.original_query,
            "execution_summary": {
                "total_steps": len(plan.steps),
                "completed_steps": len(completed_steps),
                "failed_steps": len(failed_steps),
                "success_rate": len(completed_steps) / len(plan.steps) if plan.steps else 0
            },
            "results": results,
            "final_answer": await self._generate_final_answer(plan, results)
        }
        
        return combined_result
    
    async def _generate_final_answer(self, plan: ExecutionPlan, results: Dict[str, Any]) -> str:
        """Generate final comprehensive answer from all results"""
        if self.openai_client:
            return await self._ai_generate_final_answer(plan, results)
        else:
            return self._rule_based_final_answer(plan, results)
    
    async def _ai_generate_final_answer(self, plan: ExecutionPlan, results: Dict[str, Any]) -> str:
        """Use AI to generate comprehensive final answer"""
        try:
            from src.integrations.openai.client import ModelType
            
            synthesis_prompt = f"""
            You are an expert trading assistant. Synthesize the following execution results into a comprehensive, actionable answer.
            
            Original Query: {plan.original_query}
            
            Execution Results:
            {json.dumps(results, indent=2, default=str)}
            
            Instructions:
            1. Provide a clear, comprehensive answer to the original query
            2. Integrate insights from all completed steps
            3. Highlight key findings and recommendations
            4. Structure the response with clear headings
            5. Include actionable next steps
            6. Acknowledge any limitations or failed steps
            
            Format your response as a professional analysis report.
            """
            
            messages = [
                {"role": "system", "content": "You are an expert trading and investment advisor. Provide comprehensive, actionable insights based on analysis results."},
                {"role": "user", "content": synthesis_prompt}
            ]
            
            response = await self.openai_client.chat_completion(messages, ModelType.GPT_4O)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"AI synthesis failed: {e}")
            return self._rule_based_final_answer(plan, results)
    
    def _rule_based_final_answer(self, plan: ExecutionPlan, results: Dict[str, Any]) -> str:
        """Generate final answer using rule-based approach"""
        answer_parts = [f"## Analysis Results for: {plan.original_query}\n"]
        
        completed_steps = [step for step in plan.steps if step.status == TaskStatus.COMPLETED]
        
        if not completed_steps:
            return "I apologize, but I was unable to complete the analysis due to technical issues. Please try again or rephrase your question."
        
        # Summarize results by step type
        for step in completed_steps:
            result = results.get(step.id, {})
            answer_parts.append(f"### {step.description}")
            
            if step.type == TaskType.STOCK_ANALYSIS:
                symbol = result.get("symbol", "Unknown")
                recommendation = result.get("recommendation", "N/A")
                confidence = result.get("confidence", 0)
                answer_parts.append(f"**{symbol} Analysis:** {recommendation} (Confidence: {confidence}%)")
            
            elif step.type == TaskType.COMPARISON:
                symbols = result.get("symbols", [])
                winner = result.get("winner", "N/A")
                answer_parts.append(f"**Comparison of {', '.join(symbols)}:** Top pick is {winner}")
            
            elif step.type == TaskType.PORTFOLIO_ANALYSIS:
                risk_level = result.get("risk_level", "Unknown")
                expected_return = result.get("expected_return", "N/A")
                answer_parts.append(f"**Portfolio Risk:** {risk_level}, **Expected Return:** {expected_return}%")
            
            else:
                answer_parts.append(f"**Result:** {str(result)[:200]}...")
            
            answer_parts.append("")
        
        # Add summary
        answer_parts.append("### Summary")
        answer_parts.append(f"Completed {len(completed_steps)} out of {len(plan.steps)} analysis steps.")
        answer_parts.append("For more detailed analysis, please ask specific follow-up questions.")
        
        return "\n".join(answer_parts)
    
    def _get_execution_summary(self, plan: ExecutionPlan) -> Dict[str, Any]:
        """Get execution summary for a plan"""
        completed = len([s for s in plan.steps if s.status == TaskStatus.COMPLETED])
        failed = len([s for s in plan.steps if s.status == TaskStatus.FAILED])
        total_time = sum(s.execution_time or 0 for s in plan.steps)
        
        return {
            "total_steps": len(plan.steps),
            "completed": completed,
            "failed": failed,
            "success_rate": completed / len(plan.steps) if plan.steps else 0,
            "total_execution_time": total_time,
            "average_step_time": total_time / len(plan.steps) if plan.steps else 0
        }
    
    def get_plan(self, plan_id: str) -> Optional[ExecutionPlan]:
        """Get execution plan by ID"""
        return self.execution_plans.get(plan_id)
    
    def list_plans(self) -> List[Dict[str, Any]]:
        """List all execution plans"""
        return [
            {
                "id": plan.id,
                "query": plan.original_query,
                "status": plan.status.value,
                "steps": len(plan.steps),
                "created_at": plan.created_at.isoformat()
            }
            for plan in self.execution_plans.values()
        ]

