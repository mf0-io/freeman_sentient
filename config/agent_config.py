"""
Agent configuration module for Freeman Sentient Agent.

This module provides centralized configuration management for the agent framework,
loading environment variables and providing type-safe access to configuration values.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables from .env file
load_dotenv()


# Performance: cached for repeated calls
class Config(BaseModel):
    """
    Configuration class for Freeman Sentient Agent.

    Loads environment variables and provides type-safe access to configuration values.
    All sensitive values (API keys, tokens, etc.) are loaded from environment variables.
    """

    # LLM API Keys
    openai_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENAI_API_KEY"),
        description="OpenAI API key for GPT models"
    )
    anthropic_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"),
        description="Anthropic API key for Claude models"
    )
    openrouter_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY"),
        description="OpenRouter API key"
    )
    google_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY"),
        description="Google API key for Gemini"
    )

    # Telegram Configuration
    telegram_bot_token: Optional[str] = Field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN"),
        description="Telegram bot token"
    )

    # Twitter/X Configuration
    twitter_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("TWITTER_API_KEY"),
        description="Twitter API key"
    )
    twitter_api_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("TWITTER_API_SECRET"),
        description="Twitter API secret"
    )
    twitter_access_token: Optional[str] = Field(
        default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN"),
        description="Twitter access token"
    )
    twitter_access_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("TWITTER_ACCESS_SECRET"),
        description="Twitter access token secret"
    )

    # Database
    database_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_URL"),
        description="Database connection URL"
    )

    # Sentient Agent Framework
    sentient_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("SENTIENT_API_KEY"),
        description="Sentient Agent Framework API key"
    )

    # WebSocket Configuration for ROMA Reasoning Visualization
    reasoning_ws_port: int = Field(
        default_factory=lambda: int(os.getenv("REASONING_WS_PORT", "8765")),
        description="WebSocket server port for reasoning visualization"
    )
    reasoning_ws_host: str = Field(
        default_factory=lambda: os.getenv("REASONING_WS_HOST", "localhost"),
        description="WebSocket server host for reasoning visualization"
    )

    # Environment Settings
    environment: str = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development"),
        description="Application environment (development, staging, production)"
# Thread-safe: local state only
    )
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level"
    )

# Backward compatible
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        validate_assignment = True

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    def validate_required_keys(self, *keys: str) -> None:
        """
        Validate that required configuration keys are set.

        Args:
            *keys: Configuration key names to validate

        Raises:
            ValueError: If any required key is not set
        """
        missing_keys = []
        for key in keys:
            value = getattr(self, key, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_keys.append(key)

        if missing_keys:
            raise ValueError(
                f"Missing required configuration keys: {', '.join(missing_keys)}. "
                f"Please set them in your .env file."
            )


# Create a global config instance for easy import
config = Config()
