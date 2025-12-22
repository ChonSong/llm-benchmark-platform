import time
import httpx
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class LLMResponse:
    content: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    model: str
    cost: float


class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                       temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        pass


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "gpt-4o", cost_input: float = 0.005, cost_output: float = 0.015):
        self.model_id = model_id
        self.cost_input = cost_input
        self.cost_output = cost_output
        self.api_key = settings.OPENAI_API_KEY
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            data = response.json()
        
        latency_ms = (time.time() - start_time) * 1000
        
        input_tokens = data["usage"]["prompt_tokens"]
        output_tokens = data["usage"]["completion_tokens"]
        cost = (input_tokens / 1000 * self.cost_input) + (output_tokens / 1000 * self.cost_output)
        
        return LLMResponse(
            content=data["choices"][0]["message"]["content"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=self.model_id,
            cost=cost
        )


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "claude-sonnet-4-20250514", cost_input: float = 0.003, cost_output: float = 0.015):
        self.model_id = model_id
        self.cost_input = cost_input
        self.cost_output = cost_output
        self.api_key = settings.ANTHROPIC_API_KEY
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")
        
        start_time = time.time()
        
        request_body = {
            "model": self.model_id,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            request_body["system"] = system_prompt
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json=request_body
            )
            response.raise_for_status()
            data = response.json()
        
        latency_ms = (time.time() - start_time) * 1000
        
        input_tokens = data["usage"]["input_tokens"]
        output_tokens = data["usage"]["output_tokens"]
        cost = (input_tokens / 1000 * self.cost_input) + (output_tokens / 1000 * self.cost_output)
        
        content = ""
        for block in data["content"]:
            if block["type"] == "text":
                content += block["text"]
        
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=self.model_id,
            cost=cost
        )


class GoogleProvider(BaseLLMProvider):
    def __init__(self, model_id: str = "gemini-2.0-flash", cost_input: float = 0.00025, cost_output: float = 0.001):
        self.model_id = model_id
        self.cost_input = cost_input
        self.cost_output = cost_output
        self.api_key = settings.GOOGLE_API_KEY
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None,
                       temperature: float = 0.0, max_tokens: int = 4096) -> LLMResponse:
        if not self.api_key:
            raise ValueError("Google API key not configured")
        
        start_time = time.time()
        
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent",
                headers={"Content-Type": "application/json"},
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": full_prompt}]}],
                    "generationConfig": {
                        "temperature": temperature,
                        "maxOutputTokens": max_tokens
                    }
                }
            )
            response.raise_for_status()
            data = response.json()
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Extract token counts from usage metadata
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)
        cost = (input_tokens / 1000 * self.cost_input) + (output_tokens / 1000 * self.cost_output)
        
        content = ""
        if "candidates" in data and len(data["candidates"]) > 0:
            parts = data["candidates"][0].get("content", {}).get("parts", [])
            for part in parts:
                if "text" in part:
                    content += part["text"]
        
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=self.model_id,
            cost=cost
        )


def get_provider(provider_name: str, model_id: str, cost_input: float = 0.0, cost_output: float = 0.0) -> BaseLLMProvider:
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider
    }
    
    if provider_name not in providers:
        raise ValueError(f"Unknown provider: {provider_name}")
    
    return providers[provider_name](model_id=model_id, cost_input=cost_input, cost_output=cost_output)
