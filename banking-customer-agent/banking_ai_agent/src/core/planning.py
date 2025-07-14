"""
Planning Module - Task Decomposition and Strategy Selection
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

class TaskType(Enum):
    ACCOUNT_INQUIRY = "account_inquiry"
    TRANSACTION = "transaction"
    PRODUCT_INFO = "product_info"
    CUSTOMER_SERVICE = "customer_service"
    COMPLIANCE = "compliance"
    COMPLEX_ANALYSIS = "complex_analysis"
    
    def __str__(self):
        return self.value
    
    def to_dict(self):
        return self.value

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    
    def __str__(self):
        return str(self.value)
    
    def to_dict(self):
        return self.value

@dataclass
class PlanStep:
    """Individual step in execution plan"""
    id: str
    description: str
    task_type: TaskType
    priority: Priority
    dependencies: List[str]
    estimated_duration: int  # in seconds
    required_tools: List[str]
    compliance_requirements: List[str]
    success_criteria: str

@dataclass
class ExecutionPlan:
    """Complete execution plan for a query"""
    query: str
    plan_id: str
    steps: List[PlanStep]
    total_estimated_duration: int
    complexity_score: float
    requires_human_escalation: bool
    compliance_level: str
    created_at: str

class PlanningModule:
    """
    Advanced planning module that analyzes queries and creates detailed execution plans
    """
    
    def __init__(self, llm: ChatOpenAI, config: Dict[str, Any]):
        self.llm = llm
        self.config = config
        self.logger = logging.getLogger('PlanningModule')
        
        # Planning prompts
        self.planning_prompt = self._create_planning_prompt()
        
    def _create_planning_prompt(self) -> str:
        """Create system prompt for planning"""
        return """You are an expert planning module for a banking AI agent. Your role is to analyze customer queries and create detailed execution plans.

ANALYSIS FRAMEWORK:
1. Query Classification: Determine the type of banking request
2. Complexity Assessment: Evaluate the complexity level (1-10)
3. Compliance Requirements: Identify regulatory considerations
4. Resource Requirements: Determine needed tools and data
5. Risk Assessment: Evaluate potential risks and mitigation strategies

TASK TYPES:
- account_inquiry: Balance checks, account status, statements
- transaction: Transfers, payments, deposits, withdrawals
- product_info: Loans, credit cards, investment products
- customer_service: General support, complaints, feedback
- compliance: KYC, AML, fraud detection, regulatory queries
- complex_analysis: Multi-step financial analysis, planning

PLANNING PRINCIPLES:
- Break complex queries into manageable steps
- Prioritize security and compliance
- Minimize customer effort and wait time
- Ensure clear success criteria for each step
- Plan for error handling and escalation

OUTPUT FORMAT:
Return a JSON object with the execution plan including:
- Query analysis and classification
- Step-by-step execution plan
- Resource requirements
- Compliance considerations
- Risk assessment
- Escalation criteria

Be thorough but efficient in your planning."""

    async def create_plan(self, query: str, context: Optional[Dict[str, Any]] = None) -> ExecutionPlan:
        """
        Create a comprehensive execution plan for the given query
        """
        try:
            self.logger.info(f"Creating plan for query: {query[:100]}...")
            
            # Prepare context information
            context_info = ""
            if context:
                context_info = f"Additional context: {json.dumps(context, indent=2)}"
            
            # Create planning messages
            messages = [
                SystemMessage(content=self.planning_prompt),
                HumanMessage(content=f"""
                Analyze this banking query and create a detailed execution plan:
                
                Query: {query}
                {context_info}
                
                Provide a comprehensive plan that includes:
                1. Query classification and complexity assessment
                2. Step-by-step execution plan
                3. Required tools and resources
                4. Compliance requirements
                5. Risk assessment and mitigation
                6. Success criteria and escalation points
                """)
            ]
            
            # Get planning response from LLM
            response = await self.llm.ainvoke(messages)
            plan_data = self._parse_planning_response(response.content)
            
            # Create execution plan
            execution_plan = self._create_execution_plan(query, plan_data)
            
            self.logger.info(f"Created plan with {len(execution_plan.steps)} steps")
            return execution_plan
            
        except Exception as e:
            self.logger.error(f"Error creating plan: {str(e)}")
            # Return fallback plan
            return self._create_fallback_plan(query)
    
    def _parse_planning_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured plan data"""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return self._extract_plan_from_text(response)
                
        except json.JSONDecodeError:
            self.logger.warning("Failed to parse JSON from planning response")
            return self._extract_plan_from_text(response)
    
    def _extract_plan_from_text(self, response: str) -> Dict[str, Any]:
        """Extract plan information from text response"""
        # Basic text parsing fallback
        lines = response.split('\n')
        
        plan_data = {
            "query_type": "general",
            "complexity": 5,
            "steps": [],
            "compliance_requirements": [],
            "estimated_duration": 30
        }
        
        # Simple keyword-based classification
        query_lower = response.lower()
        if any(word in query_lower for word in ['balance', 'account', 'statement']):
            plan_data["query_type"] = "account_inquiry"
        elif any(word in query_lower for word in ['transfer', 'payment', 'send']):
            plan_data["query_type"] = "transaction"
        elif any(word in query_lower for word in ['loan', 'credit', 'mortgage']):
            plan_data["query_type"] = "product_info"
        
        return plan_data
    
    def _create_execution_plan(self, query: str, plan_data: Dict[str, Any]) -> ExecutionPlan:
        """Create structured execution plan from parsed data"""
        import uuid
        from datetime import datetime
        
        plan_id = str(uuid.uuid4())
        
        # Create plan steps
        steps = []
        step_data = plan_data.get('steps', [])
        
        if not step_data:
            # Create default steps based on query type
            steps = self._create_default_steps(plan_data.get('query_type', 'general'))
        else:
            for i, step_info in enumerate(step_data):
                step = PlanStep(
                    id=f"step_{i+1}",
                    description=step_info.get('description', f'Step {i+1}'),
                    task_type=TaskType(step_info.get('task_type', 'customer_service')),
                    priority=Priority(step_info.get('priority', 2)),
                    dependencies=step_info.get('dependencies', []),
                    estimated_duration=step_info.get('estimated_duration', 10),
                    required_tools=step_info.get('required_tools', []),
                    compliance_requirements=step_info.get('compliance_requirements', []),
                    success_criteria=step_info.get('success_criteria', 'Step completed successfully')
                )
                steps.append(step)
        
        # Calculate total duration
        total_duration = sum(step.estimated_duration for step in steps)
        
        # Determine escalation need
        complexity = plan_data.get('complexity', 5)
        requires_escalation = complexity > 7 or any(
            'human' in req.lower() for req in plan_data.get('compliance_requirements', [])
        )
        
        return ExecutionPlan(
            query=query,
            plan_id=plan_id,
            steps=steps,
            total_estimated_duration=total_duration,
            complexity_score=complexity,
            requires_human_escalation=requires_escalation,
            compliance_level=plan_data.get('compliance_level', 'standard'),
            created_at=datetime.now().isoformat()
        )
    
    def _create_default_steps(self, query_type: str) -> List[PlanStep]:
        """Create default steps based on query type"""
        
        if query_type == "account_inquiry":
            return [
                PlanStep(
                    id="step_1",
                    description="Verify customer identity",
                    task_type=TaskType.COMPLIANCE,
                    priority=Priority.CRITICAL,
                    dependencies=[],
                    estimated_duration=5,
                    required_tools=["identity_verification"],
                    compliance_requirements=["KYC"],
                    success_criteria="Customer identity verified"
                ),
                PlanStep(
                    id="step_2",
                    description="Retrieve account information",
                    task_type=TaskType.ACCOUNT_INQUIRY,
                    priority=Priority.HIGH,
                    dependencies=["step_1"],
                    estimated_duration=10,
                    required_tools=["account_service"],
                    compliance_requirements=["data_privacy"],
                    success_criteria="Account information retrieved"
                ),
                PlanStep(
                    id="step_3",
                    description="Format and present response",
                    task_type=TaskType.CUSTOMER_SERVICE,
                    priority=Priority.MEDIUM,
                    dependencies=["step_2"],
                    estimated_duration=5,
                    required_tools=["response_formatter"],
                    compliance_requirements=[],
                    success_criteria="Response formatted and delivered"
                )
            ]
        
        elif query_type == "transaction":
            return [
                PlanStep(
                    id="step_1",
                    description="Verify customer identity and authorization",
                    task_type=TaskType.COMPLIANCE,
                    priority=Priority.CRITICAL,
                    dependencies=[],
                    estimated_duration=10,
                    required_tools=["identity_verification", "authorization_service"],
                    compliance_requirements=["KYC", "AML"],
                    success_criteria="Customer authorized for transaction"
                ),
                PlanStep(
                    id="step_2",
                    description="Validate transaction details",
                    task_type=TaskType.TRANSACTION,
                    priority=Priority.HIGH,
                    dependencies=["step_1"],
                    estimated_duration=15,
                    required_tools=["transaction_validator", "fraud_detection"],
                    compliance_requirements=["AML", "fraud_prevention"],
                    success_criteria="Transaction validated and approved"
                ),
                PlanStep(
                    id="step_3",
                    description="Execute transaction",
                    task_type=TaskType.TRANSACTION,
                    priority=Priority.HIGH,
                    dependencies=["step_2"],
                    estimated_duration=20,
                    required_tools=["transaction_processor"],
                    compliance_requirements=["audit_logging"],
                    success_criteria="Transaction executed successfully"
                ),
                PlanStep(
                    id="step_4",
                    description="Confirm transaction and update records",
                    task_type=TaskType.CUSTOMER_SERVICE,
                    priority=Priority.MEDIUM,
                    dependencies=["step_3"],
                    estimated_duration=5,
                    required_tools=["notification_service"],
                    compliance_requirements=["record_keeping"],
                    success_criteria="Transaction confirmed and recorded"
                )
            ]
        
        else:  # Default general steps
            return [
                PlanStep(
                    id="step_1",
                    description="Analyze customer query",
                    task_type=TaskType.CUSTOMER_SERVICE,
                    priority=Priority.HIGH,
                    dependencies=[],
                    estimated_duration=10,
                    required_tools=["nlp_analyzer"],
                    compliance_requirements=[],
                    success_criteria="Query analyzed and understood"
                ),
                PlanStep(
                    id="step_2",
                    description="Retrieve relevant information",
                    task_type=TaskType.CUSTOMER_SERVICE,
                    priority=Priority.MEDIUM,
                    dependencies=["step_1"],
                    estimated_duration=15,
                    required_tools=["knowledge_base", "rag_system"],
                    compliance_requirements=["data_privacy"],
                    success_criteria="Relevant information retrieved"
                ),
                PlanStep(
                    id="step_3",
                    description="Generate and deliver response",
                    task_type=TaskType.CUSTOMER_SERVICE,
                    priority=Priority.MEDIUM,
                    dependencies=["step_2"],
                    estimated_duration=10,
                    required_tools=["response_generator"],
                    compliance_requirements=[],
                    success_criteria="Response generated and delivered"
                )
            ]
    
    def _create_fallback_plan(self, query: str) -> ExecutionPlan:
        """Create a simple fallback plan when planning fails"""
        import uuid
        from datetime import datetime
        
        fallback_step = PlanStep(
            id="fallback_step",
            description="Process query with basic response",
            task_type=TaskType.CUSTOMER_SERVICE,
            priority=Priority.MEDIUM,
            dependencies=[],
            estimated_duration=20,
            required_tools=["basic_responder"],
            compliance_requirements=["basic_compliance"],
            success_criteria="Basic response provided"
        )
        
        return ExecutionPlan(
            query=query,
            plan_id=str(uuid.uuid4()),
            steps=[fallback_step],
            total_estimated_duration=20,
            complexity_score=3.0,
            requires_human_escalation=False,
            compliance_level="basic",
            created_at=datetime.now().isoformat()
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get planning module status"""
        return {
            "module": "planning",
            "status": "healthy",
            "capabilities": [
                "query_analysis",
                "task_decomposition",
                "resource_planning",
                "compliance_assessment",
                "risk_evaluation"
            ]
        }

