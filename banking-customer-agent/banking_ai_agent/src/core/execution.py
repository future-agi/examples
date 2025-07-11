"""
Execution Engine - Plan Execution and Tool Orchestration
"""

import json
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from .planning import ExecutionPlan, PlanStep
from .rag import RAGSystem
from .memory import MemorySystem
from .reflection import SelfReflectionModule
from .compliance import ComplianceChecker
from .tools import BankingToolsManager

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

@dataclass
class ExecutionResult:
    """Result of plan execution"""
    success: bool
    response: str
    plan_id: str
    steps_completed: int
    total_steps: int
    execution_time: float
    compliance_status: str
    confidence_score: float
    errors: List[str]
    warnings: List[str]

class ExecutionEngine:
    """
    Advanced execution engine for orchestrating plan execution
    """
    
    def __init__(self, 
                 llm: ChatOpenAI,
                 rag_system: RAGSystem,
                 memory_system: MemorySystem,
                 reflection_module: SelfReflectionModule,
                 compliance_checker: ComplianceChecker,
                 tools_manager: BankingToolsManager,
                 config: Dict[str, Any]):
        
        self.llm = llm
        self.rag_system = rag_system
        self.memory_system = memory_system
        self.reflection_module = reflection_module
        self.compliance_checker = compliance_checker
        self.tools_manager = tools_manager
        self.config = config
        self.logger = logging.getLogger('ExecutionEngine')
        
        # Execution prompts
        self.execution_prompt = self._create_execution_prompt()
        
    def _create_execution_prompt(self) -> str:
        """Create system prompt for execution"""
        return """You are an expert execution engine for a banking AI agent. Your role is to execute plans step by step and generate appropriate responses for customers.

EXECUTION PRINCIPLES:
1. Follow the execution plan precisely
2. Use retrieved context to inform responses
3. Ensure compliance with banking regulations
4. Provide clear, helpful, and accurate information
5. Maintain professional banking communication standards
6. Include appropriate disclaimers and warnings
7. Escalate when necessary for customer safety

RESPONSE GUIDELINES:
- Be professional, clear, and helpful
- Use banking terminology appropriately
- Include relevant disclaimers (FDIC insurance, financial advice, etc.)
- Provide specific information when available
- Suggest next steps or actions for the customer
- Maintain customer confidentiality and privacy

COMPLIANCE REQUIREMENTS:
- Always verify customer identity for account-specific requests
- Include appropriate regulatory disclosures
- Protect sensitive customer information
- Follow KYC, AML, and BSA requirements
- Escalate suspicious activities or complex regulatory scenarios

TOOL USAGE:
- Use banking tools to retrieve real-time information
- Validate all account and transaction data
- Check fraud risk for financial operations
- Provide accurate product information
- Ensure all operations meet security standards

Generate responses that are helpful, compliant, and maintain the highest standards of banking customer service."""

    async def execute_plan(self,
                          plan: ExecutionPlan,
                          customer_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None) -> ExecutionResult:
        """
        Execute a complete plan and generate response
        """
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Executing plan {plan.plan_id} with {len(plan.steps)} steps")
            
            # Initialize execution state
            execution_context = {
                'plan': plan,
                'customer_id': customer_id,
                'session_id': session_id,
                'context': context or {},
                'step_results': [],
                'accumulated_data': {},
                'errors': [],
                'warnings': []
            }
            
            # Execute each step
            for i, step in enumerate(plan.steps):
                self.logger.info(f"Executing step {i+1}/{len(plan.steps)}: {step.description}")
                
                try:
                    step_result = await self._execute_step(step, execution_context)
                    execution_context['step_results'].append(step_result)
                    
                    # Accumulate data from step
                    if step_result.get('data'):
                        execution_context['accumulated_data'].update(step_result['data'])
                    
                    # Check for step errors
                    if not step_result.get('success', True):
                        execution_context['errors'].append(f"Step {i+1} failed: {step_result.get('error', 'Unknown error')}")
                        
                        # Decide whether to continue or abort
                        if step.priority.value >= 3:  # HIGH or CRITICAL priority
                            self.logger.error(f"Critical step failed, aborting execution")
                            break
                    
                    # Check for warnings
                    if step_result.get('warnings'):
                        execution_context['warnings'].extend(step_result['warnings'])
                
                except Exception as e:
                    self.logger.error(f"Error executing step {i+1}: {str(e)}")
                    execution_context['errors'].append(f"Step {i+1} error: {str(e)}")
                    
                    if step.priority.value >= 3:  # HIGH or CRITICAL priority
                        break
            
            # Generate final response
            response = await self._generate_response(execution_context)
            
            # Calculate execution metrics
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            steps_completed = len(execution_context['step_results'])
            
            # Determine overall success
            success = len(execution_context['errors']) == 0 and steps_completed == len(plan.steps)
            
            # Get compliance status
            compliance_status = execution_context.get('compliance_status', 'unknown')
            
            # Estimate confidence score
            confidence_score = self._calculate_confidence_score(execution_context)
            
            return ExecutionResult(
                success=success,
                response=response,
                plan_id=plan.plan_id,
                steps_completed=steps_completed,
                total_steps=len(plan.steps),
                execution_time=execution_time,
                compliance_status=compliance_status,
                confidence_score=confidence_score,
                errors=execution_context['errors'],
                warnings=execution_context['warnings']
            )
            
        except Exception as e:
            self.logger.error(f"Error executing plan: {str(e)}")
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return ExecutionResult(
                success=False,
                response=f"I apologize, but I encountered an error while processing your request. Please try again or contact customer service for assistance.",
                plan_id=plan.plan_id,
                steps_completed=0,
                total_steps=len(plan.steps),
                execution_time=execution_time,
                compliance_status='error',
                confidence_score=0.0,
                errors=[str(e)],
                warnings=[]
            )
    
    async def _execute_step(self, step: PlanStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single plan step"""
        try:
            step_result = {
                'step_id': step.id,
                'success': True,
                'data': {},
                'warnings': [],
                'execution_time': 0
            }
            
            step_start = datetime.now()
            
            # Execute based on step type
            if step.task_type.value == 'compliance':
                result = await self._execute_compliance_step(step, execution_context)
            elif step.task_type.value == 'account_inquiry':
                result = await self._execute_account_inquiry_step(step, execution_context)
            elif step.task_type.value == 'transaction':
                result = await self._execute_transaction_step(step, execution_context)
            elif step.task_type.value == 'product_info':
                result = await self._execute_product_info_step(step, execution_context)
            elif step.task_type.value == 'customer_service':
                result = await self._execute_customer_service_step(step, execution_context)
            else:
                result = await self._execute_general_step(step, execution_context)
            
            # Update step result
            step_result.update(result)
            
            # Calculate execution time
            step_end = datetime.now()
            step_result['execution_time'] = (step_end - step_start).total_seconds()
            
            return step_result
            
        except Exception as e:
            self.logger.error(f"Error executing step {step.id}: {str(e)}")
            return {
                'step_id': step.id,
                'success': False,
                'error': str(e),
                'data': {},
                'warnings': [],
                'execution_time': 0
            }
    
    async def _execute_compliance_step(self, step: PlanStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compliance-related step"""
        query = execution_context['plan'].query
        customer_id = execution_context.get('customer_id')
        
        # Perform compliance check
        compliance_result = await self.compliance_checker.check_query(
            query, customer_id, execution_context.get('context')
        )
        
        # Store compliance status
        execution_context['compliance_status'] = compliance_result.status
        
        return {
            'success': compliance_result.status != 'violation',
            'data': {
                'compliance_result': compliance_result,
                'compliance_status': compliance_result.status,
                'required_actions': compliance_result.required_actions
            },
            'warnings': compliance_result.warnings if compliance_result.warnings else []
        }
    
    async def _execute_account_inquiry_step(self, step: PlanStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute account inquiry step"""
        customer_id = execution_context.get('customer_id')
        
        if not customer_id:
            return {
                'success': False,
                'error': 'Customer authentication required for account inquiry',
                'data': {},
                'warnings': ['Customer identity verification needed']
            }
        
        # Get customer accounts
        accounts_result = await self.tools_manager.get_customer_accounts(customer_id)
        
        if not accounts_result['success']:
            return {
                'success': False,
                'error': accounts_result.get('error', 'Failed to retrieve account information'),
                'data': {},
                'warnings': []
            }
        
        return {
            'success': True,
            'data': {
                'accounts': accounts_result['accounts'],
                'account_count': accounts_result['account_count']
            },
            'warnings': []
        }
    
    async def _execute_transaction_step(self, step: PlanStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transaction-related step"""
        customer_id = execution_context.get('customer_id')
        query = execution_context['plan'].query
        
        if not customer_id:
            return {
                'success': False,
                'error': 'Customer authentication required for transactions',
                'data': {},
                'warnings': ['Customer identity verification needed']
            }
        
        # For now, just get transaction history (actual transaction execution would require more specific parameters)
        # In a real implementation, this would parse the query to determine specific transaction details
        
        # Get customer accounts first
        accounts_result = await self.tools_manager.get_customer_accounts(customer_id)
        
        if not accounts_result['success']:
            return {
                'success': False,
                'error': 'Failed to access customer accounts',
                'data': {},
                'warnings': []
            }
        
        # Get transaction history for primary account
        if accounts_result['accounts']:
            primary_account = accounts_result['accounts'][0]['account_id']
            transactions_result = await self.tools_manager.get_transaction_history(
                customer_id, primary_account, limit=10
            )
            
            return {
                'success': transactions_result['success'],
                'data': {
                    'transactions': transactions_result.get('transactions', []),
                    'account_id': primary_account
                },
                'warnings': []
            }
        
        return {
            'success': False,
            'error': 'No accounts found for customer',
            'data': {},
            'warnings': []
        }
    
    async def _execute_product_info_step(self, step: PlanStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute product information step"""
        query = execution_context['plan'].query.lower()
        
        # Determine product type from query
        product_type = 'checking'  # Default
        if 'savings' in query or 'save' in query:
            product_type = 'savings'
        elif 'credit card' in query or 'credit' in query:
            product_type = 'credit_card'
        elif 'loan' in query:
            product_type = 'personal_loan'
        
        # Get product information
        product_result = await self.tools_manager.get_product_information(product_type)
        
        return {
            'success': product_result['success'],
            'data': {
                'product_info': product_result.get('product_info', {}),
                'product_type': product_type
            },
            'warnings': []
        }
    
    async def _execute_customer_service_step(self, step: PlanStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute customer service step"""
        query = execution_context['plan'].query
        
        # Retrieve relevant context using RAG
        rag_context = await self.rag_system.retrieve_context(query, execution_context['plan'])
        
        return {
            'success': True,
            'data': {
                'rag_context': rag_context,
                'knowledge_documents': rag_context.get('documents', [])
            },
            'warnings': []
        }
    
    async def _execute_general_step(self, step: PlanStep, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute general step"""
        query = execution_context['plan'].query
        
        # Use RAG to get relevant information
        rag_context = await self.rag_system.retrieve_context(query)
        
        return {
            'success': True,
            'data': {
                'rag_context': rag_context
            },
            'warnings': []
        }
    
    async def _generate_response(self, execution_context: Dict[str, Any]) -> str:
        """Generate final response based on execution results"""
        try:
            plan = execution_context['plan']
            query = plan.query
            step_results = execution_context['step_results']
            accumulated_data = execution_context['accumulated_data']
            errors = execution_context['errors']
            warnings = execution_context['warnings']
            
            # Prepare context for response generation
            context_info = ""
            
            # Add compliance information
            if 'compliance_result' in accumulated_data:
                compliance = accumulated_data['compliance_result']
                context_info += f"Compliance Status: {compliance.status}\n"
                if compliance.guidance:
                    context_info += f"Compliance Guidance: {compliance.guidance}\n"
            
            # Add account information
            if 'accounts' in accumulated_data:
                accounts = accumulated_data['accounts']
                context_info += f"Customer has {len(accounts)} account(s)\n"
                for account in accounts:
                    context_info += f"- {account['account_type'].title()} Account {account['account_id']}: ${account['balance']:,.2f}\n"
            
            # Add transaction information
            if 'transactions' in accumulated_data:
                transactions = accumulated_data['transactions']
                context_info += f"Recent transactions ({len(transactions)} shown):\n"
                for txn in transactions[:3]:  # Show top 3
                    context_info += f"- {txn['date']}: {txn['description']} ${txn['amount']:,.2f}\n"
            
            # Add product information
            if 'product_info' in accumulated_data:
                product = accumulated_data['product_info']
                context_info += f"Product Information: {product.get('name', 'Unknown Product')}\n"
                context_info += f"Description: {product.get('description', 'No description available')}\n"
            
            # Add RAG context
            if 'rag_context' in accumulated_data:
                rag_context = accumulated_data['rag_context']
                if rag_context.get('documents'):
                    context_info += f"Knowledge Base: {len(rag_context['documents'])} relevant documents found\n"
            
            # Add knowledge documents
            if 'knowledge_documents' in accumulated_data:
                docs = accumulated_data['knowledge_documents']
                if docs:
                    context_info += "Relevant Banking Information:\n"
                    for doc in docs[:2]:  # Use top 2 documents
                        content = doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content']
                        context_info += f"- {content}\n"
            
            # Handle errors
            if errors:
                context_info += f"Execution Errors: {'; '.join(errors)}\n"
            
            # Handle warnings
            if warnings:
                context_info += f"Warnings: {'; '.join(warnings)}\n"
            
            # Create response generation messages
            messages = [
                SystemMessage(content=self.execution_prompt),
                HumanMessage(content=f"""
                Generate a professional banking response for this customer query:
                
                Customer Query: {query}
                
                Execution Context:
                {context_info}
                
                Requirements:
                - Provide a helpful, accurate, and professional response
                - Include relevant account information if available
                - Add appropriate banking disclaimers
                - Suggest next steps if applicable
                - Maintain customer confidentiality
                - Follow banking communication standards
                
                If there were errors or the request cannot be completed, explain clearly and suggest alternatives.
                """)
            ]
            
            # Generate response
            response = await self.llm.ainvoke(messages)
            return response.content
            
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I'm unable to process your request at this time. Please contact customer service for assistance."
    
    def _calculate_confidence_score(self, execution_context: Dict[str, Any]) -> float:
        """Calculate confidence score for execution"""
        try:
            total_steps = len(execution_context['plan'].steps)
            completed_steps = len(execution_context['step_results'])
            successful_steps = sum(1 for result in execution_context['step_results'] if result.get('success', False))
            
            # Base score from step completion
            completion_score = completed_steps / total_steps if total_steps > 0 else 0
            success_score = successful_steps / completed_steps if completed_steps > 0 else 0
            
            # Adjust for errors and warnings
            error_penalty = len(execution_context['errors']) * 0.1
            warning_penalty = len(execution_context['warnings']) * 0.05
            
            # Adjust for compliance status
            compliance_bonus = 0
            if execution_context.get('compliance_status') == 'compliant':
                compliance_bonus = 0.1
            elif execution_context.get('compliance_status') == 'violation':
                compliance_bonus = -0.3
            
            # Calculate final score
            confidence = (completion_score * 0.4 + success_score * 0.4) + compliance_bonus - error_penalty - warning_penalty
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {str(e)}")
            return 0.5
    
    def get_status(self) -> Dict[str, Any]:
        """Get execution engine status"""
        return {
            "module": "execution",
            "status": "healthy",
            "capabilities": [
                "plan_execution",
                "step_orchestration",
                "tool_integration",
                "response_generation",
                "error_handling"
            ],
            "supported_step_types": [
                "compliance",
                "account_inquiry", 
                "transaction",
                "product_info",
                "customer_service",
                "complex_analysis"
            ]
        }

