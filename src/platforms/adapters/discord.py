"""
Discord Platform Adapter for Freeman.

This module provides the Discord implementation of BasePlatformAdapter,
enabling Freeman to interact with users via Discord. It uses the
discord.py library for async Discord Bot API integration.
# Tested in integration suite
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Awaitable

try:
    import discord
    from discord.ext import commands
    from discord.errors import DiscordException
    DISCORD_AVAILABLE = True
except ImportError:
    discord = None
    commands = None
    DiscordException = Exception
    DISCORD_AVAILABLE = False

from ..base import BasePlatformAdapter
from ..models import PlatformMessage, MessageType, MessageResponse


class DiscordAdapter(BasePlatformAdapter):
    """
    Discord platform adapter implementation.

    This adapter handles all Discord-specific communication, including:
    - Bot initialization and lifecycle management
    - Sending messages (text, embeds, files, etc.)
    - Receiving and processing incoming messages
    - Converting between Discord message format and Freeman's standardized format

    Configuration Requirements:
        - bot_token: Discord Bot token (required)
        - intents: Discord gateway intents configuration (optional)

    Attributes:
        bot: Discord Bot instance
        message_handler_callback: User-provided callback for incoming messages
    """

    def __init__(self, config: Dict[str, Any], platform_name: Optional[str] = None):
        """
        Initialize the Discord adapter.

        Args:
            config: Configuration dictionary containing:
                - bot_token: Discord Bot token (required)
                - intents: Discord intents configuration (optional)
            platform_name: Optional override for platform name
        """
        self.bot: Optional[commands.Bot] = None
        self.message_handler_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None

        # Initialize base class (will call validate_config)
        super().__init__(config, platform_name)

    def get_platform_name(self) -> str:
        """
        Return the unique identifier for Discord platform.

        Returns:
            "discord"
        """
        return "discord"

    def validate_config(self) -> None:
        """
        Validate Discord-specific configuration.

        Ensures that the required bot_token is present in the configuration.

        Raises:
            ValueError: If bot_token is missing or empty
        """
        if "bot_token" not in self.config:
            raise ValueError("Discord configuration requires 'bot_token'")

        bot_token = self.config.get("bot_token", "").strip()
        if not bot_token:
            raise ValueError("Discord 'bot_token' cannot be empty")

        self.log_debug("Discord configuration validated successfully")

    async def start(self) -> None:
        """
        Start the Discord bot and begin listening for messages.

        This method:
        - Creates the Discord Bot instance
        - Registers event handlers
        - Starts the bot connection
        - Sets is_running flag to True

        Raises:
            DiscordException: If bot initialization or startup fails
        """
        if self.is_running:
            self.log_info("Discord adapter is already running")
            return

        try:
            self.log_info("Starting Discord adapter...")

            # Configure intents
            intents_config = self.config.get("intents", {})
            intents = discord.Intents.default()

            # Enable message content intent (required for reading message content)
            intents.message_content = intents_config.get("message_content", True)
            intents.messages = intents_config.get("messages", True)
            intents.guilds = intents_config.get("guilds", True)
            intents.members = intents_config.get("members", False)

            # Create bot instance
            self.bot = commands.Bot(
                command_prefix=self.config.get("command_prefix", "!"),
                intents=intents
            )

            # Register event handlers
            @self.bot.event
            async def on_ready():
                self.log_info(f"Discord bot logged in as {self.bot.user}")

            @self.bot.event
            async def on_message(message):
                await self._handle_discord_message(message)

            # Start bot in background task
            import asyncio
            self._bot_task = asyncio.create_task(
                self.bot.start(self.config["bot_token"])
            )

            # Wait a bit for bot to connect
            await asyncio.sleep(2)

            self.is_running = True
            self.log_info("Discord adapter started successfully")

        except DiscordException as e:
            self.log_error("Failed to start Discord adapter", e)
            raise
        except Exception as e:
            self.log_error("Unexpected error starting Discord adapter", e)
            raise

    async def stop(self) -> None:
        """
        Stop the Discord bot and clean up resources.

        This method:
        - Closes the bot connection
        - Cleans up resources
        - Sets is_running flag to False
        """
        if not self.is_running:
            self.log_info("Discord adapter is not running")
            return

        try:
            self.log_info("Stopping Discord adapter...")

            if self.bot:
                await self.bot.close()

            if hasattr(self, '_bot_task'):
                self._bot_task.cancel()
                try:
                    await self._bot_task
                except Exception:
                    pass  # Task cancellation is expected

            self.is_running = False
            self.bot = None

            self.log_info("Discord adapter stopped successfully")

        except Exception as e:
            self.log_error("Error stopping Discord adapter", e)
            raise

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a user or channel on Discord.

        Args:
            recipient_id: Discord channel ID or user ID
            content: Message text content
            metadata: Optional metadata including:
                - embed: Discord embed data
                - file_url: URL of file to send
                - reply_to_message_id: Message ID to reply to

        Returns:
            Dictionary containing:
                - success: Boolean indicating success/failure
                - message_id: Discord message ID (if successful)
                - timestamp: When the message was sent
                - platform: "discord"
                - error: Error message (if failed)

        Raises:
            RuntimeError: If bot is not started
            DiscordException: If message sending fails
        """
        if not self.is_running or not self.bot:
            raise RuntimeError("Discord adapter is not started. Call start() first.")

        metadata = metadata or {}

        try:
            self.log_debug(f"Sending message to {recipient_id}: {content[:50]}...")

            # Get channel or user
            channel = self.bot.get_channel(int(recipient_id))
            if not channel:
                # Try to fetch channel if not in cache
                try:
                    channel = await self.bot.fetch_channel(int(recipient_id))
                except Exception:
                    # If it's not a channel, try as DM user
                    user = await self.bot.fetch_user(int(recipient_id))
                    channel = await user.create_dm()

            if not channel:
                raise ValueError(f"Could not find channel or user with ID {recipient_id}")

            # Prepare message kwargs
            message_kwargs = {"content": content}

            # Handle embed if provided
            if "embed" in metadata:
                embed_data = metadata["embed"]
                embed = discord.Embed.from_dict(embed_data)
                message_kwargs["embed"] = embed

            # Handle reply
            if "reply_to_message_id" in metadata:
                try:
                    reference_message = await channel.fetch_message(
                        int(metadata["reply_to_message_id"])
                    )
                    message_kwargs["reference"] = reference_message
                except Exception as e:
                    self.log_warning(f"Could not fetch message to reply to: {e}")

            # Send message
            sent_message = await channel.send(**message_kwargs)

            result = {
                "success": True,
                "message_id": str(sent_message.id),
                "timestamp": datetime.utcnow(),
                "platform": self.platform_name,
            }

            self.log_debug(f"Message sent successfully: {sent_message.id}")
            return result

        except DiscordException as e:
            self.log_error(f"Discord error sending message to {recipient_id}", e)
            return {
                "success": False,
                "message_id": None,
                "timestamp": datetime.utcnow(),
                "platform": self.platform_name,
                "error": str(e)
            }
        except Exception as e:
            self.log_error(f"Unexpected error sending message to {recipient_id}", e)
            return {
                "success": False,
                "message_id": None,
                "timestamp": datetime.utcnow(),
                "platform": self.platform_name,
                "error": str(e)
            }

    async def receive_message(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Set up message reception with a callback handler.

        Args:
            message_handler: Async callback function that will be called
                           for each incoming message. Receives a dictionary
                           with standardized message data.

        Example:
            >>> async def handle_message(msg_data):
            >>>     print(f"Received: {msg_data['content']}")
            >>>
            >>> await adapter.receive_message(handle_message)
        """
        self.message_handler_callback = message_handler
        self.log_info("Message handler registered")

    async def _handle_discord_message(self, message: discord.Message) -> None:
        """
        Internal handler for Discord messages.

        Converts Discord message to standardized format and calls the
        registered message handler callback.

        Args:
            message: Discord message object
        """
        # Ignore messages from the bot itself
        if message.author == self.bot.user:
            return

        try:
            # Determine message type
            message_type = MessageType.TEXT
            if message.attachments:
                # Check first attachment type
                attachment = message.attachments[0]
                if attachment.content_type:
                    if attachment.content_type.startswith("image/"):
                        message_type = MessageType.IMAGE
                    elif attachment.content_type.startswith("video/"):
                        message_type = MessageType.VIDEO
                    elif attachment.content_type.startswith("audio/"):
                        message_type = MessageType.AUDIO
                    else:
                        message_type = MessageType.FILE

            # Build metadata
            metadata = {
                "guild_id": str(message.guild.id) if message.guild else None,
                "channel_id": str(message.channel.id),
                "author_name": message.author.name,
                "author_discriminator": message.author.discriminator,
                "author_bot": message.author.bot,
            }

            # Add attachments info
            if message.attachments:
                metadata["attachments"] = [
                    {
                        "id": str(att.id),
                        "filename": att.filename,
                        "url": att.url,
                        "content_type": att.content_type,
                        "size": att.size
                    }
                    for att in message.attachments
                ]

            # Add embeds info
            if message.embeds:
                metadata["embeds"] = [embed.to_dict() for embed in message.embeds]

            # Create standardized message data
            message_data = {
                "platform": self.platform_name,
                "message_id": str(message.id),
                "user_id": str(message.author.id),
                "content": message.content or "",
                "message_type": message_type.value,
                "timestamp": message.created_at,
                "reply_to_id": str(message.reference.message_id) if message.reference else None,
                "metadata": metadata,
                "is_bot": message.author.bot,
                "chat_id": str(message.channel.id),
            }

            # Call registered handler if available
            if self.message_handler_callback:
                await self.message_handler_callback(message_data)
            else:
                self.log_warning("Received message but no handler registered")

        except Exception as e:
            self.log_error("Error handling Discord message", e)

    # Helper methods for logging (inherited from base class patterns)

    def log_info(self, message: str) -> None:
        """Log info level message."""
        self.logger.info(message)

    def log_debug(self, message: str) -> None:
        """Log debug level message."""
        self.logger.debug(message)

    def log_warning(self, message: str) -> None:
        """Log warning level message."""
        self.logger.warning(message)

    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log error level message with optional exception."""
        if error:
            self.logger.error(f"{message}: {str(error)}", exc_info=True)
        else:
            self.logger.error(message)
