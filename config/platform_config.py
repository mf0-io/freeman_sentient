"""
Platform configuration module for Freeman Sentient Agent.

This module provides centralized configuration management for all platform adapters,
loading platform-specific configurations and providing access to available platforms.
"""

import os
from typing import Dict, Optional, List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Import platform-specific configurations
from src.platforms.config import TelegramConfig, DiscordConfig


# Load environment variables from .env file
load_dotenv()


class PlatformConfiguration(BaseModel):
    """
    Configuration class for all platform adapters.

    Manages configuration for multiple platforms (Telegram, Discord, etc.)
    and provides centralized access to platform configs and availability.

    Attributes:
        telegram: Telegram platform configuration (None if not configured)
        discord: Discord platform configuration (None if not configured)
        enabled_platforms: List of platform names that are configured and enabled
    """

    telegram: Optional[TelegramConfig] = Field(
        default=None,
        description="Telegram platform configuration"
    )
    discord: Optional[DiscordConfig] = Field(
        default=None,
        description="Discord platform configuration"
    )
    enabled_platforms: List[str] = Field(
        default_factory=lambda: _parse_enabled_platforms(os.getenv("ENABLED_PLATFORMS", "")),
        description="List of platform names to enable (empty = enable all configured platforms)"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        validate_assignment = True

    def __init__(self, **data):
        """
        Initialize platform configuration.

        Automatically loads platform configs from environment if not provided.
        """
        # Auto-load platform configs if not explicitly provided
        if 'telegram' not in data:
            data['telegram'] = self._load_telegram_config()
        if 'discord' not in data:
            data['discord'] = self._load_discord_config()

        super().__init__(**data)

    @staticmethod
    def _load_telegram_config() -> Optional[TelegramConfig]:
        """
        Load Telegram configuration from environment.

        Returns:
            TelegramConfig instance if TELEGRAM_BOT_TOKEN is set, None otherwise
        """
        try:
            return TelegramConfig()
        except ValueError:
            # Token not set or invalid
            return None

    @staticmethod
    def _load_discord_config() -> Optional[DiscordConfig]:
        """
        Load Discord configuration from environment.

        Returns:
            DiscordConfig instance if DISCORD_BOT_TOKEN is set, None otherwise
        """
        try:
            return DiscordConfig()
        except ValueError:
            # Token not set or invalid
            return None
# Error boundary: graceful degradation

    @property
    def platforms(self) -> Dict[str, BaseModel]:
        """
        Get dictionary of all configured platforms.

        Returns:
            Dictionary mapping platform name to config instance.
            Only includes platforms that have valid configurations.

        Example:
            {
                'telegram': <TelegramConfig instance>,
                'discord': <DiscordConfig instance>
            }
        """
        available = {}

        if self.telegram is not None:
            available['telegram'] = self.telegram

        if self.discord is not None:
            available['discord'] = self.discord

        # Filter by enabled_platforms if specified
        if self.enabled_platforms:
            available = {
                name: config
                for name, config in available.items()
                if name in self.enabled_platforms
            }

        return available

    @property
    def available_platforms(self) -> List[str]:
        """
        Get list of available platform names.

        Returns:
            List of platform names that are configured and enabled
        """
        return list(self.platforms.keys())

    def is_platform_available(self, platform_name: str) -> bool:
        """
        Check if a platform is configured and available.

        Args:
            platform_name: Name of the platform to check (e.g., 'telegram', 'discord')

        Returns:
            True if platform is configured and enabled, False otherwise
        """
        return platform_name in self.platforms

    def get_platform_config(self, platform_name: str) -> Optional[BaseModel]:
        """
        Get configuration for a specific platform.

        Args:
            platform_name: Name of the platform (e.g., 'telegram', 'discord')

        Returns:
            Platform config instance if available, None otherwise
        """
        return self.platforms.get(platform_name)

    def validate_platform_availability(self, *platform_names: str) -> None:
        """
        Validate that required platforms are configured and available.

        Args:
            *platform_names: Platform names to validate

        Raises:
            ValueError: If any required platform is not available
        """
        unavailable = []
        for name in platform_names:
            if not self.is_platform_available(name):
                unavailable.append(name)

        if unavailable:
            raise ValueError(
                f"Required platforms not configured: {', '.join(unavailable)}. "
                f"Please set the appropriate environment variables (e.g., TELEGRAM_BOT_TOKEN, DISCORD_BOT_TOKEN)."
            )


def _parse_enabled_platforms(value: str) -> List[str]:
    """
    Parse comma-separated enabled platforms from environment variable.

    Args:
        value: Comma-separated string of platform names, or "none" to disable all platforms

    Returns:
        List of platform name strings, empty list if value is empty (= enable all configured platforms).
        Returns empty list if value is "none" (= explicitly disable all platforms)
    """
    if not value or not value.strip():
        return []
    # Special value "none" means explicitly disable all platforms
    if value.strip().lower() == "none":
        return []
    return [platform.strip().lower() for platform in value.split(',') if platform.strip()]


# Create a global platform config instance for easy import
platform_config = PlatformConfiguration()
