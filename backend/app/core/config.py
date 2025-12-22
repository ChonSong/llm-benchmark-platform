from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./benchmark.db"
    
    # API Keys for LLM providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    
    # Default model settings
    DEFAULT_TEMPERATURE: float = 0.0
    DEFAULT_MAX_TOKENS: int = 4096
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
