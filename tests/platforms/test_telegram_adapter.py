"""
Unit tests for TelegramAdapter

Tests the TelegramAdapter implementation including:
- Configuration validation
- Bot lifecycle management (start/stop)
- Message sending (text, images, videos)
- Message receiving and handling
- Error handling
- Telegram-specific features
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime

from src.platforms.adapters.telegram import TelegramAdapter
from src.platforms.models import MessageType
from telegram.error import TelegramError


class TestTelegramAdapter:
    """Test suite for TelegramAdapter"""

    @pytest.fixture
    def valid_config(self):
        """Fixture providing valid Telegram configuration"""
        return {
            'bot_token': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz',
            'allowed_updates': ['message', 'edited_message']
        }

    @pytest.fixture
    def adapter(self, valid_config):
        """Fixture providing a TelegramAdapter instance"""
        return TelegramAdapter(valid_config)

    def test_initialization_with_valid_config(self, valid_config):
        """Test adapter initializes properly with valid config"""
        adapter = TelegramAdapter(valid_config)

        assert adapter is not None
        assert adapter.config == valid_config
        assert adapter.platform_name == "telegram"
        assert adapter.is_running is False
        assert adapter.bot is None
        assert adapter.application is None
        assert adapter.message_handler_callback is None
        assert hasattr(adapter, 'logger')

    def test_initialization_with_invalid_config_missing_token(self):
        """Test adapter initialization fails without bot_token"""
        invalid_config = {'other_field': 'value'}

        with pytest.raises(ValueError) as exc_info:
            TelegramAdapter(invalid_config)

        assert "bot_token" in str(exc_info.value)

    def test_initialization_with_empty_token(self):
        """Test adapter initialization fails with empty bot_token"""
        invalid_config = {'bot_token': ''}

        with pytest.raises(ValueError) as exc_info:
            TelegramAdapter(invalid_config)

        assert "bot_token" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_initialization_with_whitespace_token(self):
        """Test adapter initialization fails with whitespace-only token"""
        invalid_config = {'bot_token': '   '}

        with pytest.raises(ValueError) as exc_info:
            TelegramAdapter(invalid_config)

        assert "bot_token" in str(exc_info.value)

    def test_get_platform_name(self, adapter):
        """Test get_platform_name returns 'telegram'"""
        assert adapter.get_platform_name() == "telegram"

    def test_validate_config_success(self, valid_config):
        """Test validate_config passes with valid configuration"""
        adapter = TelegramAdapter(valid_config)
        # If we reach here without exception, validation passed
        assert adapter.config == valid_config

    def test_get_status_before_start(self, adapter):
        """Test get_status returns correct status before starting"""
        status = adapter.get_status()

        assert isinstance(status, dict)
        assert status['platform'] == 'telegram'
        assert status['is_running'] is False
        assert status['config_valid'] is True

    @pytest.mark.asyncio
    @patch('src.platforms.adapters.telegram.Application')
    async def test_start_success(self, mock_application_class, adapter):
        """Test successful start of Telegram adapter"""
        # Mock the application builder chain
        mock_app_instance = MagicMock()
        mock_app_instance.bot = MagicMock()
        mock_app_instance.updater = MagicMock()
        mock_app_instance.updater.start_polling = AsyncMock()
        mock_app_instance.initialize = AsyncMock()
        mock_app_instance.start = AsyncMock()
        mock_app_instance.add_handler = MagicMock()

        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.build.return_value = mock_app_instance

        mock_application_class.builder.return_value = mock_builder

        await adapter.start()

        assert adapter.is_running is True
        assert adapter.application is not None
        assert adapter.bot is not None
        mock_app_instance.initialize.assert_called_once()
        mock_app_instance.start.assert_called_once()
        mock_app_instance.updater.start_polling.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_when_already_running(self, adapter):
        """Test start when adapter is already running"""
        adapter.is_running = True

        await adapter.start()

        # Should return early without error
        assert adapter.is_running is True

    @pytest.mark.asyncio
    @patch('src.platforms.adapters.telegram.Application')
    async def test_start_with_telegram_error(self, mock_application_class, adapter):
        """Test start fails gracefully with TelegramError"""
        mock_builder = MagicMock()
        mock_builder.token.return_value = mock_builder
        mock_builder.build.side_effect = TelegramError("API connection failed")
        mock_application_class.builder.return_value = mock_builder

        with pytest.raises(TelegramError):
            await adapter.start()

        assert adapter.is_running is False

    @pytest.mark.asyncio
    @patch('src.platforms.adapters.telegram.Application')
    async def test_stop_success(self, mock_application_class, adapter):
        """Test successful stop of Telegram adapter"""
        # Setup adapter as if it's running
        mock_updater = MagicMock()
        mock_updater.stop = AsyncMock()

        mock_app = MagicMock()
        mock_app.updater = mock_updater
        mock_app.stop = AsyncMock()
        mock_app.shutdown = AsyncMock()

        adapter.application = mock_app
        adapter.bot = MagicMock()
        adapter.is_running = True

        await adapter.stop()

        assert adapter.is_running is False
        assert adapter.bot is None
        assert adapter.application is None
        mock_updater.stop.assert_called_once()
        mock_app.stop.assert_called_once()
        mock_app.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, adapter):
        """Test stop when adapter is not running"""
        adapter.is_running = False

        await adapter.stop()

        # Should return early without error
        assert adapter.is_running is False

    @pytest.mark.asyncio
    async def test_send_message_not_started(self, adapter):
        """Test send_message raises error when not started"""
        with pytest.raises(RuntimeError) as exc_info:
            await adapter.send_message("123456", "Hello")

        assert "not started" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_text_message_success(self, adapter):
        """Test successful text message sending"""
        # Setup mock bot
        mock_bot = AsyncMock()
        mock_message = MagicMock()
        mock_message.message_id = 42
        mock_message.chat_id = 123456
        mock_message.date = datetime.utcnow()
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("123456", "Hello World")

        assert result["success"] is True
        assert result["message_id"] == "42"
        assert result["platform"] == "telegram"
        assert "timestamp" in result
        mock_bot.send_message.assert_called_once_with(
            chat_id="123456",
            text="Hello World",
            reply_to_message_id=None,
            parse_mode=None
        )

    @pytest.mark.asyncio
    async def test_send_message_with_photo(self, adapter):
        """Test sending message with image"""
        mock_bot = AsyncMock()
        mock_message = MagicMock()
        mock_message.message_id = 43
        mock_message.chat_id = 123456
        mock_message.date = datetime.utcnow()
        mock_bot.send_photo = AsyncMock(return_value=mock_message)

        adapter.bot = mock_bot
        adapter.is_running = True

        metadata = {
            "image_url": "https://example.com/image.jpg"
        }

        result = await adapter.send_message("123456", "Check this out", metadata)

        assert result["success"] is True
        assert result["message_id"] == "43"
        mock_bot.send_photo.assert_called_once_with(
            chat_id="123456",
            photo="https://example.com/image.jpg",
            caption="Check this out",
            reply_to_message_id=None,
            parse_mode=None
        )

    @pytest.mark.asyncio
    async def test_send_message_with_video(self, adapter):
        """Test sending message with video"""
        mock_bot = AsyncMock()
        mock_message = MagicMock()
        mock_message.message_id = 44
        mock_message.chat_id = 123456
        mock_message.date = datetime.utcnow()
        mock_bot.send_video = AsyncMock(return_value=mock_message)

        adapter.bot = mock_bot
        adapter.is_running = True

        metadata = {
            "video_url": "https://example.com/video.mp4"
        }

        result = await adapter.send_message("123456", "Check this video", metadata)

        assert result["success"] is True
        mock_bot.send_video.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_reply(self, adapter):
        """Test sending message as reply to another message"""
        mock_bot = AsyncMock()
        mock_message = MagicMock()
        mock_message.message_id = 45
        mock_message.chat_id = 123456
        mock_message.date = datetime.utcnow()
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        adapter.bot = mock_bot
        adapter.is_running = True

        metadata = {
            "reply_to_message_id": 100
        }

        result = await adapter.send_message("123456", "Reply text", metadata)

        assert result["success"] is True
        mock_bot.send_message.assert_called_once()
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["reply_to_message_id"] == 100

    @pytest.mark.asyncio
    async def test_send_message_with_parse_mode(self, adapter):
        """Test sending message with parse_mode"""
        mock_bot = AsyncMock()
        mock_message = MagicMock()
        mock_message.message_id = 46
        mock_message.chat_id = 123456
        mock_message.date = datetime.utcnow()
        mock_bot.send_message = AsyncMock(return_value=mock_message)

        adapter.bot = mock_bot
        adapter.is_running = True

        metadata = {
            "parse_mode": "Markdown"
        }

        result = await adapter.send_message("123456", "*Bold text*", metadata)

        assert result["success"] is True
        call_kwargs = mock_bot.send_message.call_args[1]
        assert call_kwargs["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_send_message_telegram_error(self, adapter):
        """Test send_message handles TelegramError gracefully"""
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock(
            side_effect=TelegramError("Chat not found")
        )

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("123456", "Hello")

        assert result["success"] is False
        assert "error" in result
        assert "Chat not found" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_unexpected_error(self, adapter):
        """Test send_message handles unexpected errors"""
        mock_bot = AsyncMock()
        mock_bot.send_message = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("123456", "Hello")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_receive_message_registers_handler(self, adapter):
        """Test receive_message registers callback handler"""
        async def mock_handler(message: Dict[str, Any]):
            pass

        await adapter.receive_message(mock_handler)

        assert adapter.message_handler_callback == mock_handler

    @pytest.mark.asyncio
    async def test_handle_telegram_update_text_message(self, adapter):
        """Test handling incoming text message"""
        # Setup mock callback
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        # Create mock Telegram message
        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.username = "testuser"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.language_code = "en"
        mock_user.is_bot = False

        mock_chat = MagicMock()
        mock_chat.id = 67890
        mock_chat.type = "private"

        mock_message = MagicMock()
        mock_message.message_id = 100
        mock_message.from_user = mock_user
        mock_message.chat = mock_chat
        mock_message.chat_id = 67890
        mock_message.text = "Hello bot!"
        mock_message.date = datetime.utcnow()
        mock_message.photo = None
        mock_message.video = None
        mock_message.voice = None
        mock_message.document = None
        mock_message.sticker = None
        mock_message.location = None
        mock_message.reply_to_message = None

        mock_update = MagicMock()
        mock_update.message = mock_message

        # Handle the update
        await adapter._handle_telegram_update(mock_update, None)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["message_id"] == "100"
        assert msg["user_id"] == "12345"
        assert msg["content"] == "Hello bot!"
        assert msg["platform"] == "telegram"
        assert msg["message_type"] == MessageType.TEXT.value
        assert msg["metadata"]["username"] == "testuser"
        assert msg["metadata"]["chat_id"] == "67890"

    @pytest.mark.asyncio
    async def test_handle_telegram_update_image_message(self, adapter):
        """Test handling incoming image message"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        # Create mock photo message
        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.is_bot = False
        mock_user.username = "testuser"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.language_code = "en"

        mock_chat = MagicMock()
        mock_chat.id = 67890
        mock_chat.type = "private"

        mock_photo = MagicMock()
        mock_photo.file_id = "PHOTO_FILE_ID_123"
        mock_photo.width = 1920
        mock_photo.height = 1080

        mock_message = MagicMock()
        mock_message.message_id = 101
        mock_message.from_user = mock_user
        mock_message.chat = mock_chat
        mock_message.chat_id = 67890
        mock_message.text = None
        mock_message.caption = "Check this photo"
        mock_message.photo = [mock_photo]
        mock_message.date = datetime.utcnow()
        mock_message.video = None
        mock_message.voice = None
        mock_message.document = None
        mock_message.sticker = None
        mock_message.location = None
        mock_message.reply_to_message = None

        mock_update = MagicMock()
        mock_update.message = mock_message

        await adapter._handle_telegram_update(mock_update, None)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["message_type"] == MessageType.IMAGE.value
        assert msg["content"] == "Check this photo"
        assert msg["metadata"]["photo_file_id"] == "PHOTO_FILE_ID_123"

    @pytest.mark.asyncio
    async def test_handle_telegram_update_command(self, adapter):
        """Test handling incoming command message"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        # Create mock command message
        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.is_bot = False
        mock_user.username = "testuser"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.language_code = "en"

        mock_chat = MagicMock()
        mock_chat.id = 67890
# Updated for latest API
        mock_chat.type = "private"

        mock_message = MagicMock()
        mock_message.message_id = 102
        mock_message.from_user = mock_user
        mock_message.chat = mock_chat
        mock_message.chat_id = 67890
        mock_message.text = "/start"
        mock_message.date = datetime.utcnow()
        mock_message.photo = None
        mock_message.video = None
        mock_message.voice = None
        mock_message.document = None
        mock_message.sticker = None
        mock_message.location = None
        mock_message.reply_to_message = None

        mock_update = MagicMock()
        mock_update.message = mock_message

        await adapter._handle_telegram_update(mock_update, None)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["message_type"] == MessageType.COMMAND.value
        assert msg["content"] == "/start"

    @pytest.mark.asyncio
    async def test_handle_telegram_update_skip_bot_messages(self, adapter):
        """Test that bot messages are skipped by default"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        # Create mock bot message
        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.is_bot = True

        mock_message = MagicMock()
        mock_message.from_user = mock_user
        mock_message.text = "Bot message"

        mock_update = MagicMock()
        mock_update.message = mock_message

        await adapter._handle_telegram_update(mock_update, None)

        # Should not process bot messages
        assert len(received_messages) == 0

    @pytest.mark.asyncio
    async def test_handle_telegram_update_no_handler(self, adapter):
        """Test handling update when no handler is registered"""
        mock_message = MagicMock()
        mock_message.from_user = MagicMock(is_bot=False)
        mock_message.text = "Hello"

        mock_update = MagicMock()
        mock_update.message = mock_message

        # Should not raise error
        await adapter._handle_telegram_update(mock_update, None)

    @pytest.mark.asyncio
    async def test_handle_telegram_update_no_message(self, adapter):
        """Test handling update without message (e.g., callback query)"""
        mock_update = MagicMock()
        mock_update.message = None

        # Should skip silently
        await adapter._handle_telegram_update(mock_update, None)

    def test_convert_telegram_message_with_location(self, adapter):
        """Test converting Telegram location message"""
        mock_user = MagicMock()
        mock_user.id = 12345
        mock_user.username = "testuser"
        mock_user.first_name = "Test"
        mock_user.last_name = "User"
        mock_user.language_code = "en"
        mock_user.is_bot = False

        mock_chat = MagicMock()
        mock_chat.id = 67890
        mock_chat.type = "private"

        mock_location = MagicMock()
        mock_location.latitude = 40.7128
        mock_location.longitude = -74.0060

        mock_message = MagicMock()
        mock_message.message_id = 103
        mock_message.from_user = mock_user
        mock_message.chat = mock_chat
        mock_message.chat_id = 67890
        mock_message.text = None
        mock_message.date = datetime.utcnow()
        mock_message.photo = None
        mock_message.video = None
        mock_message.voice = None
        mock_message.document = None
        mock_message.sticker = None
        mock_message.location = mock_location
        mock_message.reply_to_message = None

        result = adapter._convert_telegram_message(mock_message)

        assert result["message_type"] == MessageType.LOCATION.value
        assert result["metadata"]["latitude"] == 40.7128
        assert result["metadata"]["longitude"] == -74.0060

    def test_logger_is_configured(self, adapter):
        """Test that logger is properly configured"""
        assert hasattr(adapter, 'logger')
        assert 'telegram' in adapter.logger.name.lower()
