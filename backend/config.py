"""Configuration management for the chatbot backend."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Server Configuration
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:8080,http://localhost:8081"
    
    # Session Configuration
    session_timeout: int = 3600
    max_file_size_mb: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
