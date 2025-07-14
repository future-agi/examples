"""
OpenAI API client with rate limiting, error handling, and retry logic
"""
import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import openai
from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types import CreateEmbeddingResponse

# Try to import config; fallback to env vars
try:
    from config.settings import config  # type: ignore
except ModuleNotFoundError:
    from dataclasses import dataclass
    import os
    @dataclass
    class _OpenAIConfig:
        api_key: str = os.getenv("OPENAI_API_KEY", "")
        organization: str | None = os.getenv("OPENAI_ORG")
        timeout: int = int(os.getenv("OPENAI_TIMEOUT", "30"))
        temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))

    @dataclass
    class _Config:
        openai: _OpenAIConfig = _OpenAIConfig()

    config = _Config()  # type: ignore

from src.utils.logging import get_component_logger

logger = get_component_logger("openai_client")


class ModelType(Enum):
    """OpenAI model types for different use cases"""
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_TURBO_PREVIEW = "gpt-4-turbo-preview"
    EMBEDDING_LARGE = "text-embedding-3-large"
    EMBEDDING_SMALL = "text-embedding-3-small"


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 100
    tokens_per_minute: int = 10000
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0


class CircuitBreaker:
    """Circuit breaker pattern for API fault tolerance"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e


class TokenBucketRateLimiter:
    """Token bucket rate limiter for API requests"""
    
    def __init__(self, requests_per_minute: int, tokens_per_minute: int):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute
        
        self.request_tokens = requests_per_minute
        self.token_tokens = tokens_per_minute
        
        self.last_request_refill = time.time()
        self.last_token_refill = time.time()
    
    async def acquire_request(self):
        """Acquire a request token"""
        await self._refill_request_tokens()
        
        if self.request_tokens <= 0:
            wait_time = 60.0 / self.requests_per_minute
            await asyncio.sleep(wait_time)
            await self._refill_request_tokens()
        
        self.request_tokens -= 1
    
    async def acquire_tokens(self, token_count: int):
        """Acquire token tokens"""
        await self._refill_token_tokens()
        
        while self.token_tokens < token_count:
            wait_time = 60.0 / self.tokens_per_minute
            await asyncio.sleep(wait_time)
            await self._refill_token_tokens()
        
        self.token_tokens -= token_count
    
    async def _refill_request_tokens(self):
        """Refill request tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_request_refill
        tokens_to_add = int(elapsed * self.requests_per_minute / 60.0)
        
        if tokens_to_add > 0:
            self.request_tokens = min(
                self.requests_per_minute,
                self.request_tokens + tokens_to_add
            )
            self.last_request_refill = now
    
    async def _refill_token_tokens(self):
        """Refill token tokens based on time elapsed"""
        now = time.time()
        elapsed = now - self.last_token_refill
        tokens_to_add = int(elapsed * self.tokens_per_minute / 60.0)
        
        if tokens_to_add > 0:
            self.token_tokens = min(
                self.tokens_per_minute,
                self.token_tokens + tokens_to_add
            )
            self.last_token_refill = now


class OpenAIClient:
    """Enhanced OpenAI client with rate limiting and error handling"""
    
    def __init__(self, rate_limit_config: Optional[RateLimitConfig] = None):
        self.config = rate_limit_config or RateLimitConfig()
        
        # Initialize OpenAI clients
        self.client = OpenAI(
            api_key=config.openai.api_key,
            organization=config.openai.organization,
            timeout=config.openai.timeout
        )
        
        self.async_client = AsyncOpenAI(
            api_key=config.openai.api_key,
            organization=config.openai.organization,
            timeout=config.openai.timeout
        )
        
        # Initialize rate limiter and circuit breaker
        self.rate_limiter = TokenBucketRateLimiter(
            self.config.requests_per_minute,
            self.config.tokens_per_minute
        )
        
        self.circuit_breaker = CircuitBreaker()
        
        logger.info("OpenAI client initialized", extra={
            "requests_per_minute": self.config.requests_per_minute,
            "tokens_per_minute": self.config.tokens_per_minute
        })
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: ModelType = ModelType.GPT_4_TURBO,
        temperature: float = None,
        max_tokens: Optional[int] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[Union[str, Dict[str, str]]] = None,
        **kwargs
    ) -> ChatCompletion:
        """Create a chat completion with rate limiting and error handling"""
        
        # Estimate token count for rate limiting
        estimated_tokens = self._estimate_tokens(messages, max_tokens)
        
        # Acquire rate limit tokens
        await self.rate_limiter.acquire_request()
        await self.rate_limiter.acquire_tokens(estimated_tokens)
        
        # Prepare request parameters
        request_params = {
            "model": model.value,
            "messages": messages,
            "temperature": temperature or config.openai.temperature,
            **kwargs
        }
        
        if max_tokens:
            request_params["max_tokens"] = max_tokens
        
        if functions:
            request_params["functions"] = functions
        
        if function_call:
            request_params["function_call"] = function_call
        
        # Execute with retry logic
        for attempt in range(self.config.max_retries):
            try:
                response = await self.async_client.chat.completions.create(**request_params)
                
                logger.info("Chat completion successful", extra={
                    "model": model.value,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "attempt": attempt + 1
                })
                
                return response
                
            except openai.RateLimitError as e:
                wait_time = self._calculate_backoff_delay(attempt)
                logger.warning(f"Rate limit exceeded, waiting {wait_time}s", extra={
                    "attempt": attempt + 1,
                    "error": str(e)
                })
                await asyncio.sleep(wait_time)
                
            except openai.APIError as e:
                if attempt == self.config.max_retries - 1:
                    logger.error("API error after all retries", extra={
                        "error": str(e),
                        "attempts": self.config.max_retries
                    })
                    raise
                
                wait_time = self._calculate_backoff_delay(attempt)
                logger.warning(f"API error, retrying in {wait_time}s", extra={
                    "attempt": attempt + 1,
                    "error": str(e)
                })
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                logger.error("Unexpected error in chat completion", extra={
                    "error": str(e),
                    "attempt": attempt + 1
                })
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(self._calculate_backoff_delay(attempt))
        
        raise Exception(f"Failed to complete request after {self.config.max_retries} attempts")
    
    async def create_embedding(
        self,
        input_text: Union[str, List[str]],
        model: ModelType = ModelType.EMBEDDING_LARGE
    ) -> CreateEmbeddingResponse:
        """Create embeddings with rate limiting"""
        
        # Estimate token count
        if isinstance(input_text, str):
            estimated_tokens = len(input_text.split()) * 1.3  # Rough estimate
        else:
            estimated_tokens = sum(len(text.split()) * 1.3 for text in input_text)
        
        # Acquire rate limit tokens
        await self.rate_limiter.acquire_request()
        await self.rate_limiter.acquire_tokens(int(estimated_tokens))
        
        # Execute with retry logic
        for attempt in range(self.config.max_retries):
            try:
                response = await self.async_client.embeddings.create(
                    model=model.value,
                    input=input_text
                )
                
                logger.info("Embedding creation successful", extra={
                    "model": model.value,
                    "input_count": len(input_text) if isinstance(input_text, list) else 1,
                    "attempt": attempt + 1
                })
                
                return response
                
            except Exception as e:
                if attempt == self.config.max_retries - 1:
                    logger.error("Embedding creation failed", extra={
                        "error": str(e),
                        "attempts": self.config.max_retries
                    })
                    raise
                
                wait_time = self._calculate_backoff_delay(attempt)
                await asyncio.sleep(wait_time)
        
        raise Exception(f"Failed to create embedding after {self.config.max_retries} attempts")
    
    def _estimate_tokens(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> int:
        """Estimate token count for rate limiting"""
        # Rough estimation: 1 token ≈ 0.75 words
        total_chars = sum(len(msg.get("content", "")) for msg in messages)
        estimated_input_tokens = int(total_chars / 4)  # Rough estimate
        estimated_output_tokens = max_tokens or 1000  # Default estimate
        
        return estimated_input_tokens + estimated_output_tokens
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.config.base_delay * (2 ** attempt)
        return min(delay, self.config.max_delay)
    
    async def function_call_completion(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        model: ModelType = ModelType.GPT_4_TURBO,
        function_call: str = "auto"
    ) -> Dict[str, Any]:
        """Execute function calling with structured response"""
        
        response = await self.chat_completion(
            messages=messages,
            model=model,
            functions=functions,
            function_call=function_call
        )
        
        message = response.choices[0].message
        
        if message.function_call:
            return {
                "type": "function_call",
                "function_name": message.function_call.name,
                "function_arguments": json.loads(message.function_call.arguments),
                "content": message.content
            }
        else:
            return {
                "type": "text_response",
                "content": message.content
            }
    
    async def analyze_with_context(
        self,
        query: str,
        context: List[str],
        system_prompt: str,
        model: ModelType = ModelType.GPT_4_TURBO
    ) -> str:
        """Analyze query with provided context"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{chr(10).join(context)}\n\nQuery: {query}"}
        ]
        
        response = await self.chat_completion(messages=messages, model=model)
        return response.choices[0].message.content
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics"""
        return {
            "request_tokens_available": self.rate_limiter.request_tokens,
            "token_tokens_available": self.rate_limiter.token_tokens,
            "circuit_breaker_state": self.circuit_breaker.state,
            "circuit_breaker_failures": self.circuit_breaker.failure_count
        }


# Global OpenAI client instance
openai_client = OpenAIClient()

