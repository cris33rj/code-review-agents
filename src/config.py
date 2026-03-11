"""
Configuration settings for Code Review Agents.
Supports both local (Ollama) and remote (Claude, OpenAI) LLM providers.
"""

from enum import Enum
from pydantic_settings import BaseSettings
from pydantic import Field


class LLMProvider(str, Enum):
    OLLAMA = "ollama"
    CLAUDE = "claude"
    OPENAI = "openai"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Settings
    #
    app_name: str = "Code Review Agents"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, alias="DEBUG")
    
    # LLM Provider Configuration
    llm_provider: LLMProvider = Field(default=LLMProvider.OLLAMA, alias="LLM_PROVIDER")
    
    # Ollama Configuration (local)
    ollama_base_url: str = Field(
        default="http://host.docker.internal:11434",
        alias="OLLAMA_BASE_URL"
    )
    ollama_model: str = Field(default="qwen2.5-coder:7b", alias="OLLAMA_MODEL")
    
    # Claude Configuration (remote)
    claude_api_key: str = Field(default="", alias="CLAUDE_API_KEY")
    claude_model: str = Field(default="claude-sonnet-4-20250514", alias="CLAUDE_MODEL")
    
    # OpenAI Configuration (remote)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    
    # Agent Settings
    max_code_length: int = Field(default=10000, alias="MAX_CODE_LENGTH")
    request_timeout: int = Field(default=120, alias="REQUEST_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
