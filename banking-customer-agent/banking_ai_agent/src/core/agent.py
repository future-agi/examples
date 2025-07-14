"""
Banking AI Agent - Core Agent Implementation
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict


from openai import OpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from core.planning import PlanningModule
from core.memory import MemorySystem
from core.reflection import SelfReflectionModule
from core.rag import RAGSystem
from core.tools import BankingToolsManager
from core.compliance import ComplianceChecker



from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues
import logging

tracer = trace.get_tracer(__name__)


@dataclass
class AgentResponse:
    """Structured response from the AI agent"""
    content: str
    confidence: float
    sources: List[str]
    compliance_status: str
    reflection_notes: str
    execution_plan: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None

class BankingAIAgent:
    """
    Main Banking AI Agent with planning, RAG, execution, memory, and self-reflection capabilities
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = self._setup_logging()
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=config.get('openai_api_key'))
        
        # Initialize LangChain ChatOpenAI
        self.llm = ChatOpenAI(
            model=config.get('model_name', 'gpt-4o'),
            temperature=config.get('temperature', 0.1),
            max_tokens=config.get('max_tokens', 4000),
            openai_api_key=config.get('openai_api_key')
        )
        
        # Initialize core components
        self.planning_module = PlanningModule(self.llm, config)
        self.memory_system = MemorySystem(config)
        self.reflection_module = SelfReflectionModule(self.llm, config)
        self.rag_system = RAGSystem(config)
        self.tools_manager = BankingToolsManager(config)
        self.compliance_checker = ComplianceChecker(config)
        
        # System prompt for banking context
        self.system_prompt = self._create_system_prompt()
        
        self.logger.info("Banking AI Agent initialized successfully")
    
    async def initialize_async_components(self):
        """Initialize async components like RAG knowledge loading"""
        try:
            if not self.rag_system.knowledge_loaded:
                await self.rag_system._load_banking_knowledge()
                self.rag_system.knowledge_loaded = True
                self.logger.info("RAG system knowledge loaded successfully")
        except Exception as e:
            self.logger.error(f"Error loading RAG knowledge: {str(e)}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('BankingAIAgent')
        logger.setLevel(getattr(logging, self.config.get('log_level', 'INFO')))
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(self.config.get('log_file', 'logs/banking_agent.log'))
        os.makedirs(log_dir, exist_ok=True)
        
        # File handler
        file_handler = logging.FileHandler(self.config.get('log_file', 'logs/banking_agent.log'))
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _create_system_prompt(self) -> str:
        """Create comprehensive system prompt for banking AI agent"""
        return """You are a sophisticated AI agent for retail banking, designed to assist customers of major banks like JP Morgan, Capital One, and ABSA. You have the following capabilities:

CORE CAPABILITIES:
1. Planning: Break down complex banking queries into manageable steps
2. RAG (Retrieval-Augmented Generation): Access comprehensive banking knowledge
3. Execution: Perform banking operations and integrations
4. Memory: Maintain conversation context and customer history
5. Self-Reflection: Continuously improve responses and learn from interactions
6. Complex Question Answering: Handle sophisticated financial scenarios

BANKING EXPERTISE:
- Account management and transactions
- Loan and credit products
- Investment and wealth management
- Fraud detection and security
- Regulatory compliance (KYC, AML, BSA)
- Customer service and support

COMPLIANCE REQUIREMENTS:
- Always verify customer identity before providing account information
- Follow KYC (Know Your Customer) and AML (Anti-Money Laundering) guidelines
- Ensure all responses comply with banking regulations
- Protect customer privacy and data security
- Provide accurate and up-to-date information

RESPONSE GUIDELINES:
- Be professional, helpful, and empathetic
- Provide clear explanations for complex financial concepts
- Offer step-by-step guidance for banking procedures
- Escalate to human agents when appropriate
- Always prioritize customer security and compliance

Remember: You are representing a trusted financial institution. Maintain the highest standards of accuracy, security, and customer service."""

    async def process_query(self, 
                          query: str, 
                          customer_id: Optional[str] = None,
                          session_id: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        span_input = {
            "query": query,
            "customer_id": customer_id,
            "session_id": session_id,
            "context": context,
        }
        with tracer.start_as_current_span("process_query", 
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.AGENT.value,
                SpanAttributes.INPUT_VALUE: json.dumps(span_input, default=str),
            }) as span:
            """
            Main method to process customer queries with full agent capabilities
            """
            try:
                self.logger.info(f"Processing query: {query[:100]}...")
                
                # Step 1: Planning - Analyze query and create execution plan
                with tracer.start_as_current_span("create_plan", attributes={ SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value, SpanAttributes.INPUT_VALUE: json.dumps({"query": query, "context": context}, default=str)}) as plan_span:
                    plan = await self.planning_module.create_plan(query, context)
                    plan_span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(asdict(plan), default=str))
                self.logger.info(f"Created execution plan with {len(plan.steps)} steps")
                
                # Step 2: Memory - Retrieve relevant conversation history
                with tracer.start_as_current_span("get_memory_context", attributes={ SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.RETRIEVER.value, SpanAttributes.INPUT_VALUE: json.dumps({"customer_id": customer_id, "session_id": session_id, "query": query})}) as mem_span:
                    memory_context = await self.memory_system.get_context(
                        customer_id=customer_id,
                        session_id=session_id,
                        query=query
                    )
                    mem_span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(memory_context, default=str))
                
                # Step 3: RAG - Retrieve relevant banking knowledge
                with tracer.start_as_current_span("retrieve_rag_context", attributes={ SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.RETRIEVER.value, SpanAttributes.INPUT_VALUE: json.dumps({"query": query, "plan": asdict(plan)}, default=str)}) as rag_span:
                    rag_context = await self.rag_system.retrieve_context(query, plan)
                    rag_span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(rag_context, default=str))
                
                # Step 4: Compliance Check - Ensure query compliance
                with tracer.start_as_current_span("check_compliance", attributes={ SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.GUARDRAIL.value, SpanAttributes.INPUT_VALUE: json.dumps({"query": query, "customer_id": customer_id, "context": context}, default=str)}) as compliance_span:
                    compliance_result = await self.compliance_checker.check_query(
                        query, customer_id, context
                    )
                    compliance_span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(asdict(compliance_result), default=str))
                
                # Step 5: Execute plan with all context
                response_content = await self._execute_plan(
                    plan=plan,
                    query=query,
                    memory_context=memory_context,
                    rag_context=rag_context,
                    compliance_result=compliance_result
                )
                
                # Step 6: Self-Reflection - Evaluate response quality
                with tracer.start_as_current_span("reflect_on_response", attributes={ SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.EVALUATOR.value, SpanAttributes.INPUT_VALUE: json.dumps({"query": query, "response": response_content, "plan": asdict(plan), "context": context}, default=str)}) as reflection_span:
                    reflection = await self.reflection_module.reflect_on_response(
                        query=query,
                        response=response_content,
                        plan=plan,
                        context=context
                    )
                    reflection_span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(asdict(reflection), default=str))
                
                # Step 7: Update memory with interaction
                store_interaction_input = {
                    "customer_id": customer_id,
                    "session_id": session_id,
                    "query": query,
                    "response": response_content,
                    "plan": asdict(plan),
                    "reflection": asdict(reflection)
                }
                with tracer.start_as_current_span("store_interaction", attributes={ SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value, SpanAttributes.INPUT_VALUE: json.dumps(store_interaction_input, default=str)}) as store_span:
                    await self.memory_system.store_interaction(
                        customer_id=customer_id,
                        session_id=session_id,
                        query=query,
                        response=response_content,
                        plan=plan,
                        reflection=reflection
                    )
                
                # Create structured response
                agent_response = AgentResponse(
                    content=response_content,
                    confidence=reflection.confidence_score,
                    sources=rag_context.get('sources', []),
                    compliance_status=compliance_result.status,
                    reflection_notes=reflection.notes,
                    execution_plan=asdict(plan),
                    tool_calls=plan.tool_calls if hasattr(plan, 'tool_calls') else None
                )
                
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(agent_response.content))
                self.logger.info("Query processed successfully")
                return agent_response
                
            except Exception as e:
                self.logger.error(f"Error processing query: {str(e)}")
                agent_response = AgentResponse(
                    content="I apologize, but I encountered an error processing your request. Please try again or contact customer support for assistance.",
                    confidence=0.0,
                    sources=[],
                    compliance_status="error",
                    reflection_notes=f"Error occurred: {str(e)}"
                )
                span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(asdict(agent_response), default=str))
                return agent_response
    
    async def _execute_plan(self,
                          plan: Any,
                          query: str,
                          memory_context: Dict[str, Any],
                          rag_context: Dict[str, Any],
                          compliance_result: Any) -> str:
        span_input = {
            "plan": asdict(plan) if hasattr(plan, '__dataclass_fields__') else str(plan),
            "query": query,
            "memory_context": memory_context,
            "rag_context": rag_context,
            "compliance_result": asdict(compliance_result) if hasattr(compliance_result, '__dataclass_fields__') else str(compliance_result),
        }
        with tracer.start_as_current_span("generate_response", 
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.CHAIN.value,
                SpanAttributes.INPUT_VALUE: json.dumps(span_input, default=str),
            }) as span:
            """Execute the planned steps to generate response"""
            
            # Prepare messages for LLM
            messages = [
                SystemMessage(content=self.system_prompt),
            ]
            
            # Add memory context if available
            if memory_context.get('history'):
                for interaction in memory_context['history'][-3:]:  # Last 3 interactions
                    messages.append(HumanMessage(content=interaction['query']))
                    messages.append(AIMessage(content=interaction['response']))
            
            # Add RAG context
            if rag_context.get('documents'):
                context_content = "Relevant banking information:\n"
                for doc in rag_context['documents'][:5]:  # Top 5 relevant documents
                    context_content += f"- {doc['content']}\n"
                messages.append(SystemMessage(content=context_content))
            
            # Add compliance guidance
            if compliance_result.guidance:
                messages.append(SystemMessage(content=f"Compliance guidance: {compliance_result.guidance}"))
            
            # Add current query
            messages.append(HumanMessage(content=query))
            
            # Generate response using LLM
            response = await self.llm.ainvoke(messages)
            
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(response.content))
            return response.content
    
    async def get_account_balance(self, customer_id: str, account_id: str) -> Dict[str, Any]:
        span_input = {"customer_id": customer_id, "account_id": account_id}
        with tracer.start_as_current_span("get_account_balance", 
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(span_input),
            }) as span:

            """Example banking operation - get account balance"""
            # This would integrate with actual banking systems
            result = await self.tools_manager.get_account_balance(customer_id, account_id)
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
            return result
    
    async def transfer_funds(self, 
                           customer_id: str,
                           from_account: str,
                           to_account: str,
                           amount: float,
                           description: str = "") -> Dict[str, Any]:
        span_input = {
            "customer_id": customer_id,
            "from_account": from_account,
            "to_account": to_account,
            "amount": amount,
            "description": description,
        }
        with tracer.start_as_current_span("transfer_funds", 
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(span_input),
            }) as span:
            """Example banking operation - transfer funds"""
            # This would integrate with actual banking systems
            result = await self.tools_manager.transfer_funds(
                customer_id, from_account, to_account, amount, description
            )
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
            return result
    
    async def get_transaction_history(self,
                                    customer_id: str,
                                    account_id: str,
                                    limit: int = 10) -> List[Dict[str, Any]]:
        span_input = {
            "customer_id": customer_id,
            "account_id": account_id,
            "limit": limit,
        }
        with tracer.start_as_current_span("get_transaction_history", 
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.TOOL.value,
                SpanAttributes.INPUT_VALUE: json.dumps(span_input),
            }) as span:
            """Example banking operation - get transaction history"""
            result = await self.tools_manager.get_transaction_history(
                customer_id, account_id, limit
            )
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(result))
            return result
    
    def get_health_status(self) -> Dict[str, Any]:
        with tracer.start_as_current_span("get_health_status", 
            attributes={
                SpanAttributes.FI_SPAN_KIND: FiSpanKindValues.AGENT.value,
                SpanAttributes.INPUT_VALUE: json.dumps({}),
            }) as span:
            """Get health status of all agent components"""
            status = {
                "agent_status": "healthy",
                "planning_module": self.planning_module.get_status(),
                "memory_system": self.memory_system.get_status(),
                "rag_system": self.rag_system.get_status(),
                "tools_manager": self.tools_manager.get_status(),
                "compliance_checker": self.compliance_checker.get_status(),
                "timestamp": datetime.now().isoformat()
            }
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(status))
            return status

