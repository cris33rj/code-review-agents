"""
LLM Gateway - Unified interface for multiple LLM providers.
Supports Ollama (local), Claude, and OpenAI.
"""

import httpx
from abc import ABC, abstractmethod
from typing import Optional
import anthropic
import openai

from src.config import settings, LLMProvider


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response from the LLM."""
        pass


class OllamaClient(BaseLLMClient):
    """Client for Ollama (local LLM)."""
    
    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        async with httpx.AsyncClient(timeout=settings.request_timeout) as client:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
            
            if system_prompt:
                payload["system"] = system_prompt
            
            response = await client.post(
                f"{self.base_url}/api/generate",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")


class ClaudeClient(BaseLLMClient):
    """Client for Anthropic Claude API."""
    
    def __init__(self, api_key: str, model: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        message = await self.client.messages.create(**kwargs)
        return message.content[0].text


class OpenAIClient(BaseLLMClient):
    """Client for OpenAI API."""
    
    def __init__(self, api_key: str, model: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096
        )
        return response.choices[0].message.content


class LLMGateway:
    """
    Unified gateway for LLM access.
    Automatically selects the appropriate client based on configuration.
    """
    
    def __init__(self, provider: Optional[LLMProvider] = None):
        self.provider = provider or settings.llm_provider
        self.client = self._create_client()
    
    def _create_client(self) -> BaseLLMClient:
        if self.provider == LLMProvider.OLLAMA:
            return OllamaClient(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model
            )
        elif self.provider == LLMProvider.CLAUDE:
            if not settings.claude_api_key:
                raise ValueError("CLAUDE_API_KEY is required for Claude provider")
            return ClaudeClient(
                api_key=settings.claude_api_key,
                model=settings.claude_model
            )
        elif self.provider == LLMProvider.OPENAI:
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
            return OpenAIClient(
                api_key=settings.openai_api_key,
                model=settings.openai_model
            )
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a response using the configured LLM provider."""
        return await self.client.generate(prompt, system_prompt)
    
    def get_provider_info(self) -> dict:
        """Return information about the current provider."""
        info = {"provider": self.provider.value}
        
        if self.provider == LLMProvider.OLLAMA:
            info["model"] = settings.ollama_model
            info["base_url"] = settings.ollama_base_url
        elif self.provider == LLMProvider.CLAUDE:
            info["model"] = settings.claude_model
        elif self.provider == LLMProvider.OPENAI:
            info["model"] = settings.openai_model
        
        return info


# Convenience function
async def generate_response(prompt: str, system_prompt: Optional[str] = None) -> str:
    """Quick helper to generate a response using default settings."""
    gateway = LLMGateway()
    return await gateway.generate(prompt, system_prompt)
