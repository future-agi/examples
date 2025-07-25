import os
from dotenv import load_dotenv
load_dotenv()   

import logging
from typing import Dict, List, Optional, Generator, Any
import json
from datetime import datetime
import asyncio
# AI/LLM imports
try:
    import openai
    from openai import OpenAI
except ImportError as e:
    logging.warning(f"OpenAI library not available: {e}")
from opentelemetry import trace
from fi_instrumentation import register, FITracer
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

tracer = FITracer(trace.get_tracer(__name__))

class AIService:
    """
    Service for AI/LLM integration supporting multiple providers
    """
    
    def __init__(self):
        self.providers = {}
        self.default_provider = 'openai'
        
        # Initialize available providers
        self._initialize_providers()
        
        # Test connection at startup
        self._test_connections()
        
        # Default model configurations
        self.model_configs = {
            'openai': {
                'chat': 'gpt-4-turbo',
                'chat_advanced': 'gpt-4-turbo',
                'embedding': 'text-embedding-ada-002',
                'max_tokens': 4000,
                'context_window': 128000,
                'temperature': 0.7
            },
            'anthropic': {
                'chat': 'claude-3-sonnet-20240229',
                'chat_advanced': 'claude-3-opus-20240229',
                'max_tokens': 4000,
                'temperature': 0.7
            }
        }
    
    def _initialize_providers(self):
        """Initialize available AI providers"""
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                self.providers['openai'] = OpenAI(
                    api_key=os.getenv('OPENAI_API_KEY'),
                    base_url=os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'),
                    timeout=30.0,  # Set timeout to prevent hanging
                    max_retries=3   # Enable retries
                )
                logging.info("OpenAI provider initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize OpenAI provider: {e}")
        
        # Add other providers here (Anthropic, etc.)
        # For now, focusing on OpenAI as it's most commonly available
        
        if not self.providers:
            logging.warning("No AI providers available. Please configure API keys.")
    
    def _test_connections(self):
        """Test connections to AI providers at startup"""
        for provider_name, client in self.providers.items():
            try:
                logging.info(f"Testing {provider_name} connection...")
                if provider_name == 'openai':
                    response = client.chat.completions.create(
                        model='gpt-3.5-turbo',
                        messages=[{"role": "user", "content": "test"}],
                        max_tokens=5
                    )
                    logging.info(f"✅ {provider_name} connection successful")
                else:
                    logging.info(f"⏭️  Skipping {provider_name} connection test")
            except Exception as e:
                logging.error(f"❌ {provider_name} connection failed: {str(e)}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available AI providers"""
        return list(self.providers.keys())
    
    def get_provider_models(self, provider: str = None) -> Dict:
        with tracer.start_as_current_span("get_provider_models") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"provider": provider}))
        """Get available models for a provider"""
        if not provider:
            provider = self.default_provider
        
        span.set_attribute("output.value", json.dumps(self.model_configs.get(provider, {})))
        return self.model_configs.get(provider, {})
    
    def chat_completion(self, messages: List[Dict], provider: str = None, 
                       model: str = None, stream: bool = False, 
                       context_sources: List[Dict] = None, **kwargs) -> Dict:
        with tracer.start_as_current_span("chat_completion") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.LLM.value)
            span.set_attribute("input.value", json.dumps({"messages": messages, "provider": provider, "model": model, "stream": stream, "context_sources": context_sources, "kwargs": kwargs}))
            """
            Generate chat completion with context from sources
            
            Args:
                messages: List of message objects with role and content
                provider: AI provider to use
                model: Specific model to use
                stream: Whether to stream the response
                context_sources: List of relevant source chunks for context
                **kwargs: Additional parameters for the model
            
            Returns:
                Dict with response content and metadata
            """
            try:
                if not provider:
                    provider = self.default_provider
                
                if provider not in self.providers:
                    raise ValueError(f"Provider '{provider}' not available")
                
                client = self.providers[provider]
                config = self.model_configs.get(provider, {})
                
                if not model:
                    model = config.get('chat', 'gpt-3.5-turbo')
                
                # Prepare system message with context
                system_message = self._build_system_message(context_sources)
                
                # Prepare messages
                formatted_messages = [{"role": "system", "content": system_message}]
                formatted_messages.extend(messages)
                
                # Set parameters
                params = {
                    'model': model,
                    'messages': formatted_messages,
                    'max_tokens': kwargs.get('max_tokens', config.get('max_tokens', 4000)),
                    'temperature': kwargs.get('temperature', config.get('temperature', 0.7)),
                    'stream': stream
                }
                
                # Get AI response directly
                if stream:
                    return self._handle_streaming_response(client, params)
                else:
                    response = client.chat.completions.create(**params)
                span.set_attribute("output.value", json.dumps({
                    'content': response.choices[0].message.content,
                    'model': response.model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    },
                    'provider': provider,
                    'timestamp': datetime.now().isoformat(),
                    'sources_used': len(context_sources) if context_sources else 0
                }))
                return {
                    'content': response.choices[0].message.content,
                    'model': response.model,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    },
                    'provider': provider,
                    'timestamp': datetime.now().isoformat(),
                    'sources_used': len(context_sources) if context_sources else 0
                }
                    
            except Exception as e:
                logging.error(f"Chat completion error: {e}")
                # More descriptive error message
                error_msg = str(e)
                if "Connection error" in error_msg:
                    error_msg = "Connection error - please check network connectivity and API key"
                elif "context_length_exceeded" in error_msg:
                    error_msg = "Context length exceeded - too much text for model to process"
                elif "rate_limit" in error_msg.lower():
                    error_msg = "Rate limit exceeded - please try again in a moment"
                elif "authentication" in error_msg.lower():
                    error_msg = "Authentication error - please check API key"
                

                return {
                    'content': f"I apologize, but I encountered an error: {error_msg}",
                    'error': str(e),
                    'provider': provider,
                    'timestamp': datetime.now().isoformat()
                }
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of tokens (1 token ≈ 4 characters)"""
        return len(text) // 4
    
    def _build_system_message(self, context_sources: List[Dict] = None) -> str:
        """Build system message with context from sources"""
        
        base_prompt = """You are NotebookLM, an AI research assistant that helps users understand and analyze their documents. You have access to the user's uploaded documents and can provide insights, summaries, and answer questions based on their content.

Key capabilities:
- Answer questions based on the provided document context
- Generate summaries and insights from the documents
- Create study guides, FAQs, and briefing documents
- Provide citations and references to specific sources
- Maintain accuracy and cite sources when making claims

Guidelines:
- Always base your responses on the provided context when possible
- If information isn't available in the context, clearly state this
- Provide specific citations when referencing information
- Be helpful, accurate, and concise
- If asked to generate content, use the document context as the foundation"""

        if context_sources and len(context_sources) > 0:
            context_text = "\\n\\nRelevant context from your documents:\\n"
            total_tokens = self._estimate_tokens(base_prompt)
            max_context_tokens = 100000  # Use most of GPT-4 Turbo's 128k context, leave room for response
            
            for i, source in enumerate(context_sources):
                if i >= 20:  # Limit to 20 sources for GPT-4 Turbo
                    break
                    
                source_info = source.get('metadata', {})
                source_id = source_info.get('source_id', 'unknown')
                text = source.get('text', '')
                
                # Dynamically adjust text length based on remaining token budget
                remaining_tokens = max_context_tokens - total_tokens
                if remaining_tokens <= 0:
                    break
                    
                max_text_length = min(3000, remaining_tokens * 4)  # Standard max text per source
                text = text[:max_text_length]
                
                source_context = f"\\n[Source {i+1} - ID: {source_id}]\\n{text}\\n"
                source_tokens = self._estimate_tokens(source_context)
                
                if total_tokens + source_tokens > max_context_tokens:
                    break
                    
                context_text += source_context
                total_tokens += source_tokens
            
            base_prompt += context_text
        
        return base_prompt
    
    def _handle_streaming_response(self, client, params) -> Generator[Dict, None, None]:
        """Handle streaming response from AI provider"""
        try:
            stream = client.chat.completions.create(**params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield {
                        'content': chunk.choices[0].delta.content,
                        'type': 'content',
                        'timestamp': datetime.now().isoformat()
                    }
            
            yield {
                'type': 'done',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            yield {
                'type': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_content(self, content_type: str, sources: List[Dict], 
                        title: str = None, custom_prompt: str = None,
                        provider: str = None, model: str = None) -> Dict:
        with tracer.start_as_current_span("generate_content") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.LLM.value)
            span.set_attribute("input.value", json.dumps({"content_type": content_type, "sources": sources, "title": title, "custom_prompt": custom_prompt, "provider": provider, "model": model}))
            """
            Generate specific types of content from sources
            
            Args:
                content_type: Type of content (summary, faq, timeline, study_guide, briefing, ai_summary, executive_summary, predictive_actions)
                sources: List of source chunks to use
                title: Optional title for the content
                custom_prompt: Custom prompt for generation
                provider: AI provider to use
                model: Specific model to use
            
            Returns:
                Dict with generated content and metadata
            """
            try:
                # Content type specific prompts
                prompts = {
                    'summary': "Create a comprehensive summary of the provided documents. Include key points, main themes, and important details. Structure it with clear headings and bullet points.",
                    
                    'faq': "Generate a comprehensive FAQ based on the provided documents. Create questions that users might ask about the content and provide detailed answers. Format as Q&A pairs.",
                    
                    'timeline': "Create a chronological timeline of events, developments, or processes mentioned in the documents. Include dates, key milestones, and brief descriptions.",
                    
                    'study_guide': "Create a detailed study guide based on the provided documents. Include key concepts, definitions, important facts, and potential study questions. Organize by topics.",
                    
                    'briefing': "Create a concise briefing document that summarizes the most important information from the provided documents. Focus on key insights, decisions, and actionable items.",
                    
                    'ai_summary': """Create a comprehensive AI Summary of the provided documents. Focus on:
    - Key objectives and purposes of the document
    - Main regulations, requirements, or guidelines mentioned
    - Entities and stakeholders affected
    - Compliance requirements and timelines
    - Potential impacts and consequences of non-compliance
    - Strategic opportunities that may arise
    - Important dates, deadlines, or effective periods

    Structure the summary as flowing paragraphs that capture the essence and implications of the document content.""",
                    
                    'executive_summary': """Create a structured Executive Summary of the provided documents. Format with clear sections:
    - Primary objective and purpose of the document
    - Key amendments, requirements, or changes introduced
    - Specific entities, organizations, or stakeholders affected
    - Scope and applicability of the content
    - Important regulatory changes or new obligations
    - Compliance requirements and disclosure obligations
    - Timeline information and deadlines
    - Any exclusions or special considerations mentioned

    Present information in a clear, factual manner suitable for executive-level review.""",
                    
                    'predictive_actions': """Generate comprehensive Predictive Actions based on the provided documents, organized in three priority levels:

    **CRITICAL ACTIONS** (Must be completed immediately):
    - Essential compliance requirements with immediate deadlines
    - Actions required to avoid penalties or legal issues
    - Critical process changes needed for regulatory compliance

    **WARNING ACTIONS** (Should be completed soon):
    - Important process improvements and risk mitigation steps
    - Recommended compliance measures with moderate urgency
    - Actions to enhance transparency and operational efficiency

    **GOOD TO HAVE ACTIONS** (Can be scheduled for future):
    - Strategic opportunities for competitive advantage
    - Process optimizations and best practice implementations
    - Long-term planning and preparatory measures

    For each action, provide:
    - Clear, actionable description
    - Brief rationale based on the document content
    - Suggested timeline or urgency level

    Format each action as a distinct item with clear descriptions."""
                }
                
                if content_type not in prompts:
                    raise ValueError(f"Unsupported content type: {content_type}")
                
                # Use custom prompt if provided
                prompt = custom_prompt or prompts[content_type]
                
                # Add title context if provided
                if title:
                    prompt = f"Title: {title}\\n\\n{prompt}"
                
                # Prepare context from sources
                context_text = "\\n\\nSource Documents:\\n"
                for i, source in enumerate(sources):
                    source_info = source.get('metadata', {})
                    source_id = source_info.get('source_id', f'source_{i+1}')
                    text = source.get('text', '')
                    
                    context_text += f"\\n[Document {i+1} - ID: {source_id}]\\n{text}\\n"
                
                full_prompt = prompt + context_text
                
                # Generate content
                messages = [{"role": "user", "content": full_prompt}]
                
                response = self.chat_completion(
                    messages=messages,
                    provider=provider,
                    model=model,
                    context_sources=[]  # Context already included in prompt
                )
                span.set_attribute("output.value", json.dumps(response))
                return {
                    'content': response.get('content', ''),
                    'type': content_type,
                    'title': title or f"Generated {content_type.title()}",
                    'sources_count': len(sources),
                    'generation_metadata': {
                        'provider': response.get('provider'),
                        'model': response.get('model'),
                        'usage': response.get('usage'),
                        'timestamp': response.get('timestamp')
                    },
                    'citations': self._extract_citations(sources)
                }
                
            except Exception as e:
                logging.error(f"Content generation error: {e}")
                return {
                    'content': f"Error generating {content_type}: {str(e)}",
                    'type': content_type,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def _extract_citations(self, sources: List[Dict]) -> List[Dict]:
        with tracer.start_as_current_span("extract_citations") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"sources": sources}))
            """Extract citation information from sources"""
            citations = []
            
            for i, source in enumerate(sources):
                metadata = source.get('metadata', {})
                
                citation = {
                    'id': metadata.get('source_id', f'source_{i+1}'),
                    'title': metadata.get('title', 'Unknown Document'),
                    'type': metadata.get('type', 'document'),
                    'url': metadata.get('url'),
                    'page': metadata.get('page'),
                    'timestamp': metadata.get('timestamp')
                }
                
                citations.append(citation)
            span.set_attribute("output.value", json.dumps(citations))
            return citations
    
    def analyze_query_intent(self, query: str) -> Dict:
        print(f"Analyzing query intent: {query}")
        with tracer.start_as_current_span("analyze_query_intent") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"query": query}))
            """
            Analyze user query to determine intent and required context
            
            Args:
                query: User's query text
                
            Returns:
                Dict with intent analysis and context requirements
            """
            try:
                # Simple intent classification (can be enhanced with ML models)
                query_lower = query.lower()
                
                # Define intent patterns
                intent_patterns = {
                    'question': ['what', 'how', 'why', 'when', 'where', 'who', '?'],
                    'summary': ['summarize', 'summary', 'overview', 'brief'],
                    'analysis': ['analyze', 'analysis', 'compare', 'contrast', 'evaluate'],
                    'generation': ['create', 'generate', 'write', 'make', 'produce'],
                    'search': ['find', 'search', 'look for', 'locate'],
                    'explanation': ['explain', 'clarify', 'elaborate', 'detail']
                }
                
                # Determine primary intent
                intent_scores = {}
                for intent, patterns in intent_patterns.items():
                    score = sum(1 for pattern in patterns if pattern in query_lower)
                    if score > 0:
                        intent_scores[intent] = score
                
                primary_intent = max(intent_scores, key=intent_scores.get) if intent_scores else 'question'
                
                # Determine context requirements
                context_requirements = {
                    'needs_sources': True,  # Most queries need document context
                    'max_sources': 20,  # Standard context for GPT-4 Turbo
                    'prefer_recent': 'recent' in query_lower or 'latest' in query_lower,
                    'specific_source': self._extract_source_references(query)
                }
                
                span.set_attribute("output.value", json.dumps(context_requirements))
                return {
                    'primary_intent': primary_intent,
                    'confidence': intent_scores.get(primary_intent, 0) / len(query.split()),
                    'context_requirements': context_requirements,
                    'query_complexity': len(query.split()),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logging.error(f"Query intent analysis error: {e}")
                return {
                    'primary_intent': 'question',
                    'confidence': 0.5,
                    'context_requirements': {'needs_sources': True, 'max_sources': 10},
                    'error': str(e)
                }
    
    def _extract_source_references(self, query: str) -> List[str]:
        with tracer.start_as_current_span("extract_source_references") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"query": query}))
            """Extract specific source references from query"""
            # Simple pattern matching for source references
            # Can be enhanced with more sophisticated NLP
            import re
            
            patterns = [
                r'in document (\w+)',
                r'from source (\w+)',
                r'according to (\w+)',
                r'in the (\w+) document'
            ]
            
            references = []
            for pattern in patterns:
                matches = re.findall(pattern, query.lower())
                references.extend(matches)
            span.set_attribute("output.value", json.dumps(references))
            return references
    
    def get_health_status(self) -> Dict:
        with tracer.start_as_current_span("get_health_status") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({}))
            """Get health status of AI service"""
            try:
                status = {
                    'providers_available': len(self.providers),
                    'providers': list(self.providers.keys()),
                    'default_provider': self.default_provider,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Test each provider
                for provider_name, client in self.providers.items():
                    try:
                        # Simple test call
                        test_response = client.chat.completions.create(
                            model=self.model_configs[provider_name]['chat'],
                            messages=[{"role": "user", "content": "Hello"}],
                            max_tokens=10
                        )
                        status[f'{provider_name}_status'] = 'healthy'
                    except Exception as e:
                        status[f'{provider_name}_status'] = f'error: {str(e)}'
                
                span.set_attribute("output.value", json.dumps(status))
                return status
                
            except Exception as e:
                return {
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }

