"""
Platform Factory for creating platform adapter instances.

This module provides a factory pattern for creating platform adapters,
managing the registry of available platforms, and handling configuration
initialization. It simplifies adapter creation by providing a single
entry point for instantiating any platform adapter.
"""

import logging
from typing import Dict, Any, Optional, Type

from .base import BasePlatformAdapter
from .config import TelegramConfig, DiscordConfig
from .models import PlatformConfig
from .adapters.telegram import TelegramAdapter
from .adapters.discord import DiscordAdapter


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("freeman.platform.factory")


class PlatformFactory:
    """
    Factory class for creating platform adapter instances.

    This factory provides a centralized way to create platform adapters
    with proper configuration. It maintains a registry of available
    platforms and their corresponding adapter and config classes.

    Usage:
        >>> # Create adapter with default config from environment
        >>> adapter = PlatformFactory.create('telegram')
        >>>
        >>> # Create adapter with custom config
        >>> config = TelegramConfig(bot_token='custom_token')
        >>> adapter = PlatformFactory.create('telegram', config=config)
        >>>
        >>> # Create adapter with config dictionary
        >>> adapter = PlatformFactory.create('telegram', config={'bot_token': 'token'})
    """

    # Registry mapping platform names to (adapter_class, config_class)
    _registry: Dict[str, tuple[Type[BasePlatformAdapter], Type[PlatformConfig]]] = {
        'telegram': (TelegramAdapter, TelegramConfig),
        'discord': (DiscordAdapter, DiscordConfig),
    }

    @classmethod
    def create(
        cls,
        platform_name: str,
        config: Optional[Dict[str, Any] | PlatformConfig] = None
    ) -> BasePlatformAdapter:
        """
        Create a platform adapter instance.

        Args:
            platform_name: Name of the platform (e.g., 'telegram', 'discord')
            config: Optional configuration. Can be:
                   - PlatformConfig instance (TelegramConfig, DiscordConfig, etc.)
                   - Dictionary of configuration values
                   - None (will load from environment variables)

        Returns:
            Initialized platform adapter instance

        Raises:
            ValueError: If platform_name is not registered
            TypeError: If config is of invalid type
            ConfigurationError: If configuration is invalid

        Examples:
            >>> # Using environment variables
            >>> adapter = PlatformFactory.create('telegram')
            >>>
            >>> # Using config instance
            >>> cfg = TelegramConfig(bot_token='my_token')
            >>> adapter = PlatformFactory.create('telegram', config=cfg)
            >>>
            >>> # Using config dictionary
            >>> adapter = PlatformFactory.create('telegram', config={'bot_token': 'my_token'})
        """
        # Validate platform name
        if platform_name not in cls._registry:
            available = ', '.join(cls._registry.keys())
            raise ValueError(
                f"Unknown platform '{platform_name}'. "
                f"Available platforms: {available}"
            )

        adapter_class, config_class = cls._registry[platform_name]

        # Handle configuration
        if config is None:
            # Create config from environment variables
            logger.info(f"Creating {platform_name} adapter with config from environment")
            platform_config = config_class()
        elif isinstance(config, dict):
            # Create config from dictionary
            logger.info(f"Creating {platform_name} adapter with config dictionary")
            platform_config = config_class(**config)
        elif isinstance(config, PlatformConfig):
            # Use provided config instance
            logger.info(f"Creating {platform_name} adapter with provided config instance")
            platform_config = config
        else:
            raise TypeError(
                f"config must be None, dict, or PlatformConfig instance, "
                f"got {type(config).__name__}"
            )

        # Convert config to dictionary for adapter initialization
        # The adapter expects a dict, not a Pydantic model
        config_dict = platform_config.dict() if hasattr(platform_config, 'dict') else vars(platform_config)

        # Create and return adapter instance
        logger.info(f"Instantiating {adapter_class.__name__}")
        adapter = adapter_class(config=config_dict, platform_name=platform_name)

        logger.info(f"Successfully created {platform_name} adapter")
        return adapter

    @classmethod
    def register(
        cls,
        platform_name: str,
        adapter_class: Type[BasePlatformAdapter],
        config_class: Type[PlatformConfig]
    ) -> None:
        """
        Register a new platform adapter.

        This allows extending the factory with custom platform adapters
        without modifying the factory code.

        Args:
            platform_name: Unique identifier for the platform
            adapter_class: Adapter class (must inherit from BasePlatformAdapter)
            config_class: Config class (must inherit from PlatformConfig)

        Raises:
            TypeError: If classes don't inherit from required base classes
            ValueError: If platform_name is already registered

        Example:
            >>> class CustomAdapter(BasePlatformAdapter):
            >>>     # ... implementation ...
            >>>
            >>> class CustomConfig(PlatformConfig):
            >>>     # ... configuration ...
            >>>
            >>> PlatformFactory.register('custom', CustomAdapter, CustomConfig)
            >>> adapter = PlatformFactory.create('custom')
        """
        # Validate adapter class
        if not issubclass(adapter_class, BasePlatformAdapter):
            raise TypeError(
                f"adapter_class must inherit from BasePlatformAdapter, "
                f"got {adapter_class.__name__}"
            )

        # Validate config class
        if not issubclass(config_class, PlatformConfig):
            raise TypeError(
                f"config_class must inherit from PlatformConfig, "
                f"got {config_class.__name__}"
            )

        # Check if already registered
        if platform_name in cls._registry:
            logger.warning(
                f"Platform '{platform_name}' is already registered. "
                f"Overwriting with {adapter_class.__name__}"
            )

        # Register the platform
        cls._registry[platform_name] = (adapter_class, config_class)
        logger.info(f"Registered platform '{platform_name}' with {adapter_class.__name__}")

    @classmethod
    def get_available_platforms(cls) -> list[str]:
        """
        Get list of all registered platform names.

        Returns:
            List of available platform identifiers

        Example:
            >>> platforms = PlatformFactory.get_available_platforms()
            >>> print(platforms)
            ['telegram', 'discord']
        """
        return list(cls._registry.keys())

    @classmethod
    def is_platform_available(cls, platform_name: str) -> bool:
        """
        Check if a platform is registered.

        Args:
            platform_name: Platform identifier to check

        Returns:
            True if platform is registered, False otherwise

        Example:
            >>> if PlatformFactory.is_platform_available('telegram'):
            >>>     adapter = PlatformFactory.create('telegram')
        """
        return platform_name in cls._registry
