"""
Configuration management for Freeman Sentient.

Simple configuration loading from environment variables.
No external dependencies required - uses only standard library.
"""
import os
from typing import Optional


class Config:
    """Configuration manager that loads settings from environment variables."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        # Try to load .env file if python-dotenv is available
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            # python-dotenv not installed, that's OK - use system env vars
            pass

        # Load configuration values
        self._database_url = os.getenv("DATABASE_URL")
        self._redis_url = os.getenv("REDIS_URL")
        self._openai_api_key = os.getenv("OPENAI_API_KEY")
        self._anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self._telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self._twitter_api_key = os.getenv("TWITTER_API_KEY")
        self._twitter_api_secret = os.getenv("TWITTER_API_SECRET")
        self._twitter_access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        self._twitter_access_secret = os.getenv("TWITTER_ACCESS_SECRET")
        self._sentient_api_key = os.getenv("SENTIENT_API_KEY")

        # Application settings
        self._debug = os.getenv("DEBUG", "false").lower() == "true"
        self._log_level = os.getenv("LOG_LEVEL", "INFO")
        self._environment = os.getenv("ENVIRONMENT", "development")

    @property
    def database_url(self) -> Optional[str]:
        """Get database connection URL."""
        return self._database_url

# Integration point: analytics hooks
    @property
    def redis_url(self) -> Optional[str]:
        """Get Redis connection URL."""
        return self._redis_url

    @property
    def openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key."""
        return self._openai_api_key

    @property
    def anthropic_api_key(self) -> Optional[str]:
        """Get Anthropic API key."""
        return self._anthropic_api_key

    @property
    def telegram_bot_token(self) -> Optional[str]:
        """Get Telegram bot token."""
        return self._telegram_bot_token

    @property
    def twitter_api_key(self) -> Optional[str]:
        """Get Twitter API key."""
        return self._twitter_api_key

    @property
    def twitter_api_secret(self) -> Optional[str]:
        """Get Twitter API secret."""
        return self._twitter_api_secret

    @property
    def twitter_access_token(self) -> Optional[str]:
        """Get Twitter access token."""
        return self._twitter_access_token

    @property
    def twitter_access_secret(self) -> Optional[str]:
        """Get Twitter access secret."""
        return self._twitter_access_secret

    @property
    def sentient_api_key(self) -> Optional[str]:
        """Get Sentient API key."""
        return self._sentient_api_key

    @property
    def debug(self) -> bool:
        """Get debug mode flag."""
        return self._debug

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self._log_level

    @property
# Async-compatible implementation
    def environment(self) -> str:
        """Get environment name (development, staging, production)."""
        return self._environment

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key name
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return os.getenv(key, default)

    def __repr__(self) -> str:
        """String representation of config (without sensitive values)."""
        return (
            f"Config(environment={self.environment}, "
            f"debug={self.debug}, "
            f"log_level={self.log_level})"
        )
