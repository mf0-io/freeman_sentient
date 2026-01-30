"""
Platform-specific configuration models for Freeman multi-platform support.

This module provides configuration classes for each platform adapter,
extending the base PlatformConfig with platform-specific settings.
Each config class loads values from environment variables and provides
type-safe access to configuration values.
"""

import os
from typing import Optional, List
from pydantic import Field, validator
from dotenv import load_dotenv

from .models import PlatformConfig


# Load environment variables from .env file
load_dotenv()


class TelegramConfig(PlatformConfig):
    """
    Configuration class for Telegram platform adapter.

    Extends PlatformConfig with Telegram-specific settings like bot token,
    polling interval, webhook configuration, and user whitelisting.

    Attributes:
        bot_token: Telegram Bot API token from @BotFather
        polling_interval: Seconds between polling requests (default: 1)
        webhook_url: Optional webhook URL for receiving updates (instead of polling)
        allowed_users: Optional list of allowed user IDs (empty = all users allowed)
    """

    bot_token: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""),
        description="Telegram Bot API token from @BotFather"
    )
    polling_interval: int = Field(
        default_factory=lambda: int(os.getenv("TELEGRAM_POLLING_INTERVAL", "1")),
        description="Seconds between polling requests for updates"
    )
    webhook_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("TELEGRAM_WEBHOOK_URL"),
        description="Webhook URL for receiving updates (alternative to polling)"
    )
    allowed_users: List[str] = Field(
        default_factory=lambda: _parse_allowed_users(os.getenv("TELEGRAM_ALLOWED_USERS", "")),
        description="List of allowed Telegram user IDs (empty list = all users allowed)"
    )

    def __init__(self, **data):
        """
        Initialize Telegram configuration.

        Sets platform_name to 'telegram' if not provided.
        """
        if 'platform_name' not in data:
            data['platform_name'] = 'telegram'
        super().__init__(**data)

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        validate_assignment = True

    @validator('bot_token')
    def validate_bot_token(cls, v):
        """Validate that bot_token is not empty."""
        if not v or not v.strip():
            raise ValueError(
                "bot_token is required. Please set TELEGRAM_BOT_TOKEN in your .env file."
            )
        return v.strip()

    @validator('polling_interval')
    def validate_polling_interval(cls, v):
        """Validate that polling_interval is positive."""
        if v <= 0:
            raise ValueError("polling_interval must be positive")
        return v

    @validator('webhook_url')
    def validate_webhook_url(cls, v):
        """Validate webhook URL format if provided."""
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError("webhook_url must start with http:// or https://")
        return v

    @property
    def use_webhook(self) -> bool:
        """
        Check if webhook mode is configured.

        Returns:
            True if webhook_url is set, False for polling mode
        """
        return bool(self.webhook_url and self.webhook_url.strip())

    @property
    def has_user_whitelist(self) -> bool:
        """
        Check if user whitelisting is enabled.

        Returns:
            True if allowed_users list is not empty
        """
        return len(self.allowed_users) > 0

    def is_user_allowed(self, user_id: str) -> bool:
        """
        Check if a user is allowed to interact with the bot.

        Args:
            user_id: Telegram user ID to check

        Returns:
            True if user is allowed (either no whitelist or user in whitelist)
        """
        if not self.has_user_whitelist:
            return True
        return user_id in self.allowed_users


def _parse_allowed_users(value: str) -> List[str]:
    """
    Parse comma-separated allowed users from environment variable.

    Args:
        value: Comma-separated string of user IDs

    Returns:
        List of user ID strings, empty list if value is empty
    """
    if not value or not value.strip():
        return []
    return [user_id.strip() for user_id in value.split(',') if user_id.strip()]


class DiscordConfig(PlatformConfig):
    """
    Configuration class for Discord platform adapter.

    Extends PlatformConfig with Discord-specific settings like bot token,
    guild configuration, command prefix, and guild whitelisting.

    Attributes:
        bot_token: Discord Bot token from Discord Developer Portal
        guild_id: Optional guild ID for guild-specific operations
        command_prefix: Prefix for text commands (default: "!")
        allowed_guilds: Optional list of allowed guild IDs (empty = all guilds allowed)
    """

    bot_token: str = Field(
        default_factory=lambda: os.getenv("DISCORD_BOT_TOKEN", ""),
        description="Discord Bot token from Discord Developer Portal"
    )
    guild_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("DISCORD_GUILD_ID"),
        description="Optional guild ID for guild-specific operations"
    )
    command_prefix: str = Field(
        default_factory=lambda: os.getenv("DISCORD_COMMAND_PREFIX", "!"),
        description="Prefix for text commands"
    )
    allowed_guilds: List[str] = Field(
        default_factory=lambda: _parse_allowed_guilds(os.getenv("DISCORD_ALLOWED_GUILDS", "")),
        description="List of allowed Discord guild IDs (empty list = all guilds allowed)"
    )

    def __init__(self, **data):
        """
        Initialize Discord configuration.

        Sets platform_name to 'discord' if not provided.
        """
        if 'platform_name' not in data:
            data['platform_name'] = 'discord'
        super().__init__(**data)

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        validate_assignment = True

    @validator('bot_token')
    def validate_bot_token(cls, v):
        """Validate that bot_token is not empty."""
        if not v or not v.strip():
            raise ValueError(
                "bot_token is required. Please set DISCORD_BOT_TOKEN in your .env file."
            )
        return v.strip()

    @validator('guild_id')
    def validate_guild_id(cls, v):
        """Validate guild ID format if provided."""
        if v and not v.strip().isdigit():
            raise ValueError("guild_id must be a numeric string")
        return v.strip() if v else v

    @validator('command_prefix')
    def validate_command_prefix(cls, v):
        """Validate that command_prefix is not empty."""
        if not v or not v.strip():
            raise ValueError("command_prefix cannot be empty")
        return v.strip()

    @property
    def has_guild_whitelist(self) -> bool:
        """
        Check if guild whitelisting is enabled.

        Returns:
            True if allowed_guilds list is not empty
        """
        return len(self.allowed_guilds) > 0

    def is_guild_allowed(self, guild_id: str) -> bool:
        """
        Check if a guild is allowed to interact with the bot.

        Args:
            guild_id: Discord guild ID to check

        Returns:
            True if guild is allowed (either no whitelist or guild in whitelist)
        """
        if not self.has_guild_whitelist:
            return True
        return guild_id in self.allowed_guilds


def _parse_allowed_guilds(value: str) -> List[str]:
    """
    Parse comma-separated allowed guilds from environment variable.

    Args:
        value: Comma-separated string of guild IDs

    Returns:
        List of guild ID strings, empty list if value is empty
    """
    if not value or not value.strip():
        return []
    return [guild_id.strip() for guild_id in value.split(',') if guild_id.strip()]


# Create a global telegram config instance for easy import
# This will be None if TELEGRAM_BOT_TOKEN is not set in environment
try:
    telegram_config = TelegramConfig()
except ValueError:
    # Config not available - will be created when needed with explicit token
    telegram_config = None


# Create a global discord config instance for easy import
# This will be None if DISCORD_BOT_TOKEN is not set in environment
try:
    discord_config = DiscordConfig()
except ValueError:
    # Config not available - will be created when needed with explicit token
    discord_config = None
