"""
Base Platform Adapter for Freeman multi-platform support.

This module provides the abstract base class that all platform adapters
must implement to integrate with the Freeman system. It defines the
standard interface for sending/receiving messages, lifecycle management,
and configuration validation.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable, Awaitable


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class BasePlatformAdapter(ABC):
    """
    Abstract base class for platform adapters.

    All platform-specific adapters (Telegram, Discord, Twitter, etc.) must
    inherit from this class and implement the required abstract methods.

    This provides a unified interface for:
    - Sending messages to the platform
    - Receiving messages from the platform
    - Lifecycle management (start/stop)
    - Platform identification
    - Configuration validation

    Attributes:
        platform_name: Unique identifier for the platform (e.g., "telegram", "discord")
        config: Platform-specific configuration dictionary
        logger: Logger instance for this adapter
        is_running: Flag indicating whether the adapter is currently active
    """

    def __init__(
        self,
        config: Dict[str, Any],
        platform_name: Optional[str] = None
    ):
        """
        Initialize the platform adapter.

        Args:
            config: Platform-specific configuration dictionary
            platform_name: Optional override for platform name.
                          If not provided, uses get_platform_name()
        """
        self.config = config
        self.platform_name = platform_name or self.get_platform_name()
        self.logger = logging.getLogger(f"freeman.platform.{self.platform_name}")
        self.is_running = False

        # Validate configuration on initialization
        self.validate_config()

        self.logger.info(f"Initialized {self.platform_name} platform adapter")

    @abstractmethod
    def get_platform_name(self) -> str:
        """
        Return the unique identifier for this platform.

        Returns:
            String identifier (e.g., "telegram", "discord", "twitter")

        Example:
            >>> return "telegram"
        """
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """
        Validate the platform-specific configuration.

        Should raise ValueError or ConfigurationError if required
        configuration parameters are missing or invalid.

        Raises:
            ValueError: If configuration is invalid
            KeyError: If required configuration keys are missing

        Example:
            >>> if 'bot_token' not in self.config:
            >>>     raise ValueError("bot_token is required")
        """
        pass

    @abstractmethod
    async def start(self) -> None:
        """
        Start the platform adapter and begin listening for messages.

        This method should:
        - Initialize platform-specific clients/connections
        - Set up message handlers
        - Begin polling or webhook listening
        - Set is_running = True

        Example:
            >>> await self.bot.start_polling()
            >>> self.is_running = True
        """
        pass

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the platform adapter and clean up resources.

        This method should:
        - Stop polling/webhook listening
        - Close connections
        - Clean up resources
        - Set is_running = False

        Example:
            >>> await self.bot.stop_polling()
            >>> self.is_running = False
        """
        pass

    @abstractmethod
    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a user on this platform.

        Args:
            recipient_id: Platform-specific user identifier
            content: Message text content
            metadata: Optional additional data (media URLs, reply_to, etc.)

        Returns:
            Dictionary containing:
                - message_id: Platform-specific message identifier
                - timestamp: When the message was sent
                - success: Boolean indicating success/failure
                - Any other platform-specific metadata

        Example:
            >>> result = await adapter.send_message(
            >>>     recipient_id="12345",
            >>>     content="Hello, world!",
            >>>     metadata={"image_url": "https://..."}
            >>> )
            >>> print(result["message_id"])
        """
        pass

    @abstractmethod
    async def receive_message(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Set up message reception with a callback handler.

        Args:
            message_handler: Async callback function that will be called
                           for each incoming message. Receives a dictionary
                           with standardized message data:
                           {
                               "message_id": str,
                               "user_id": str,
                               "content": str,
                               "timestamp": datetime,
                               "platform": str,
                               "metadata": Dict[str, Any]
                           }

        Example:
            >>> async def handle_message(msg_data):
            >>>     print(f"Received: {msg_data['content']}")
            >>>
            >>> await adapter.receive_message(handle_message)
        """
        pass

    # Helper methods (concrete implementations)

    def get_status(self) -> Dict[str, Any]:
        """
        Get current adapter status.

        Returns:
            Dictionary with status information including:
                - platform: Platform name
                - is_running: Whether adapter is active
                - config_valid: Whether configuration is valid
        """
        return {
            "platform": self.platform_name,
            "is_running": self.is_running,
            "config_valid": True  # If we got here, config was validated
        }

    def log_info(self, message: str) -> None:
        """
        Helper method to log info-level messages.

        Args:
            message: Log message
        """
        self.logger.info(message)

    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """
        Helper method to log error-level messages.

        Args:
            message: Error message
            error: Optional exception object
        """
        if error:
            self.logger.error(f"{message}: {error}", exc_info=True)
        else:
            self.logger.error(message)

    def log_debug(self, message: str) -> None:
        """
        Helper method to log debug-level messages.

        Args:
            message: Debug message
        """
        self.logger.debug(message)
