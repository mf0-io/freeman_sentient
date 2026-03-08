"""
Telegram Platform Adapter for Freeman.

This module provides the Telegram implementation of BasePlatformAdapter,
enabling Freeman to interact with users via Telegram. It uses the
python-telegram-bot library for async Telegram Bot API integration.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Awaitable

from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from telegram.error import TelegramError

from ..base import BasePlatformAdapter
from ..models import PlatformMessage, MessageType, MessageResponse


class TelegramAdapter(BasePlatformAdapter):
    """
    Telegram platform adapter implementation.

    This adapter handles all Telegram-specific communication, including:
    - Bot initialization and lifecycle management
    - Sending messages (text, images, etc.)
    - Receiving and processing incoming messages
    - Converting between Telegram message format and Freeman's standardized format

    Configuration Requirements:
        - bot_token: Telegram Bot API token (required)
        - allowed_updates: List of update types to receive (optional)

    Attributes:
        bot: Telegram Bot instance
        application: Telegram Application instance for handling updates
        message_handler_callback: User-provided callback for incoming messages
    """

    def __init__(self, config: Dict[str, Any], platform_name: Optional[str] = None):
        """
        Initialize the Telegram adapter.

        Args:
            config: Configuration dictionary containing:
                - bot_token: Telegram Bot API token (required)
                - allowed_updates: List of update types (optional)
            platform_name: Optional override for platform name
        """
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        self.message_handler_callback: Optional[Callable[[Dict[str, Any]], Awaitable[None]]] = None

        # Initialize base class (will call validate_config)
        super().__init__(config, platform_name)

    def get_platform_name(self) -> str:
        """
        Return the unique identifier for Telegram platform.

        Returns:
            "telegram"
        """
        return "telegram"

    def validate_config(self) -> None:
        """
        Validate Telegram-specific configuration.

        Ensures that the required bot_token is present in the configuration.

        Raises:
            ValueError: If bot_token is missing or empty
        """
        if "bot_token" not in self.config:
            raise ValueError("Telegram configuration requires 'bot_token'")

        bot_token = self.config.get("bot_token", "").strip()
        if not bot_token:
            raise ValueError("Telegram 'bot_token' cannot be empty")

        self.log_debug("Telegram configuration validated successfully")

    async def start(self) -> None:
        """
        Start the Telegram bot and begin listening for messages.

        This method:
        - Creates the Telegram Application instance
        - Registers message handlers
        - Starts polling for updates
        - Sets is_running flag to True

        Raises:
            TelegramError: If bot initialization or startup fails
        """
        if self.is_running:
            self.log_info("Telegram adapter is already running")
            return

        try:
            self.log_info("Starting Telegram adapter...")

            # Create application
            self.application = Application.builder().token(
                self.config["bot_token"]
            ).build()

            self.bot = self.application.bot

            # Register handlers for all message types
            self.application.add_handler(
                MessageHandler(filters.ALL, self._handle_telegram_update)
            )

            # Start polling
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling(
                allowed_updates=self.config.get("allowed_updates", None)
            )

            self.is_running = True
            self.log_info("Telegram adapter started successfully")

        except TelegramError as e:
            self.log_error("Failed to start Telegram adapter", e)
            raise
        except Exception as e:
            self.log_error("Unexpected error starting Telegram adapter", e)
            raise

    async def stop(self) -> None:
        """
        Stop the Telegram bot and clean up resources.

        This method:
        - Stops polling for updates
        - Shuts down the application
        - Cleans up resources
        - Sets is_running flag to False
        """
        if not self.is_running:
            self.log_info("Telegram adapter is not running")
            return

        try:
            self.log_info("Stopping Telegram adapter...")

            if self.application:
                # Stop polling
                await self.application.updater.stop()
                # Stop application
                await self.application.stop()
                # Shutdown
                await self.application.shutdown()

            self.is_running = False
            self.bot = None
            self.application = None

            self.log_info("Telegram adapter stopped successfully")

        except Exception as e:
            self.log_error("Error stopping Telegram adapter", e)
            raise

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a user on Telegram.

        Args:
            recipient_id: Telegram chat ID (can be user ID or group ID)
            content: Message text content
            metadata: Optional metadata including:
                - image_url: URL of image to send
                - video_url: URL of video to send
                - reply_to_message_id: Message ID to reply to
                - parse_mode: Telegram parse mode (Markdown, HTML, etc.)

        Returns:
            Dictionary containing:
                - success: Boolean indicating success/failure
                - message_id: Telegram message ID (if successful)
                - timestamp: When the message was sent
                - platform: "telegram"
                - error: Error message (if failed)

        Raises:
            RuntimeError: If bot is not started
            TelegramError: If message sending fails
        """
        if not self.is_running or not self.bot:
            raise RuntimeError("Telegram adapter is not started. Call start() first.")

        metadata = metadata or {}
        timestamp = datetime.utcnow()

        try:
            self.log_debug(f"Sending message to {recipient_id}: {content[:50]}...")

            # Extract optional parameters
            reply_to = metadata.get("reply_to_message_id")
            parse_mode = metadata.get("parse_mode", None)
            image_url = metadata.get("image_url")
            video_url = metadata.get("video_url")

            # Send message based on type
            sent_message = None

            if image_url:
                # Send photo with caption
                sent_message = await self.bot.send_photo(
                    chat_id=recipient_id,
                    photo=image_url,
                    caption=content if content else None,
                    reply_to_message_id=reply_to,
                    parse_mode=parse_mode
                )
            elif video_url:
                # Send video with caption
                sent_message = await self.bot.send_video(
                    chat_id=recipient_id,
                    video=video_url,
                    caption=content if content else None,
                    reply_to_message_id=reply_to,
                    parse_mode=parse_mode
                )
            else:
                # Send text message
                sent_message = await self.bot.send_message(
                    chat_id=recipient_id,
                    text=content,
                    reply_to_message_id=reply_to,
                    parse_mode=parse_mode
                )

            self.log_info(f"Message sent successfully to {recipient_id}")

            return {
                "success": True,
                "message_id": str(sent_message.message_id),
                "timestamp": timestamp.isoformat(),
                "platform": self.platform_name,
                "metadata": {
                    "chat_id": sent_message.chat_id,
                    "date": sent_message.date.isoformat() if sent_message.date else None
                }
            }

        except TelegramError as e:
            self.log_error(f"Telegram error sending message to {recipient_id}", e)
            return {
                "success": False,
                "message_id": None,
                "timestamp": timestamp.isoformat(),
                "platform": self.platform_name,
                "error": str(e)
            }
        except Exception as e:
            self.log_error(f"Unexpected error sending message to {recipient_id}", e)
            return {
                "success": False,
                "message_id": None,
                "timestamp": timestamp.isoformat(),
                "platform": self.platform_name,
                "error": str(e)
            }

    async def receive_message(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        Set up message reception with a callback handler.

        This method registers a callback function that will be called
        for each incoming message. The callback receives a standardized
        message dictionary.

        Args:
            message_handler: Async callback function that receives:
                {
                    "message_id": str,
                    "user_id": str,
                    "content": str,
                    "timestamp": datetime,
                    "platform": "telegram",
                    "metadata": Dict[str, Any]
                }

        Note:
            This method only registers the callback. Messages will only
            be processed after start() is called.
        """
        self.log_info("Registering message handler callback")
        self.message_handler_callback = message_handler

    async def _handle_telegram_update(self, update: Update, context) -> None:
        """
        Internal handler for Telegram updates.

        Converts Telegram Update objects to standardized message format
        and calls the registered message handler callback.

        Args:
            update: Telegram Update object
            context: Telegram context object
        """
        if not update.message:
            # Skip non-message updates (edits, callbacks, etc.)
            return

        message = update.message

        # Skip messages from bots (unless configured otherwise)
        if message.from_user.is_bot and not self.config.get("allow_bot_messages", False):
            return

        try:
            # Convert Telegram message to standardized format
            standardized_message = self._convert_telegram_message(message)

            # Call the registered handler if available
            if self.message_handler_callback:
                await self.message_handler_callback(standardized_message)
            else:
                self.log_debug("No message handler registered, skipping message")

        except Exception as e:
            self.log_error(f"Error handling Telegram update", e)

    def _convert_telegram_message(self, telegram_message) -> Dict[str, Any]:
        """
        Convert Telegram message to standardized message format.

        Args:
            telegram_message: Telegram Message object

        Returns:
            Standardized message dictionary
        """
        # Determine message type
        message_type = MessageType.TEXT
        content = telegram_message.text or ""
        metadata = {}

        if telegram_message.photo:
            message_type = MessageType.IMAGE
            # Get the largest photo
            photo = telegram_message.photo[-1]
            metadata["photo_file_id"] = photo.file_id
            metadata["photo_size"] = {"width": photo.width, "height": photo.height}
            content = telegram_message.caption or ""

        elif telegram_message.video:
            message_type = MessageType.VIDEO
            metadata["video_file_id"] = telegram_message.video.file_id
            metadata["video_duration"] = telegram_message.video.duration
            content = telegram_message.caption or ""

        elif telegram_message.voice:
            message_type = MessageType.AUDIO
            metadata["voice_file_id"] = telegram_message.voice.file_id
            metadata["voice_duration"] = telegram_message.voice.duration

        elif telegram_message.document:
            message_type = MessageType.FILE
            metadata["document_file_id"] = telegram_message.document.file_id
            metadata["document_name"] = telegram_message.document.file_name
            content = telegram_message.caption or ""

        elif telegram_message.sticker:
            message_type = MessageType.STICKER
            metadata["sticker_file_id"] = telegram_message.sticker.file_id
            metadata["sticker_emoji"] = telegram_message.sticker.emoji

        elif telegram_message.location:
            message_type = MessageType.LOCATION
            metadata["latitude"] = telegram_message.location.latitude
            metadata["longitude"] = telegram_message.location.longitude

        # Check if it's a command
        if content.startswith('/'):
            message_type = MessageType.COMMAND

        # Build standardized message
        return {
            "message_id": str(telegram_message.message_id),
            "user_id": str(telegram_message.from_user.id),
            "content": content,
            "timestamp": telegram_message.date.isoformat() if telegram_message.date else datetime.utcnow().isoformat(),
            "platform": self.platform_name,
            "message_type": message_type.value,
            "metadata": {
                **metadata,
                "chat_id": str(telegram_message.chat_id),
                "chat_type": telegram_message.chat.type,
                "username": telegram_message.from_user.username,
                "first_name": telegram_message.from_user.first_name,
                "last_name": telegram_message.from_user.last_name,
                "language_code": telegram_message.from_user.language_code,
                "is_bot": telegram_message.from_user.is_bot,
                "reply_to_message_id": str(telegram_message.reply_to_message.message_id) if telegram_message.reply_to_message else None
            }
        }
