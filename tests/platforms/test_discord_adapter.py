"""
Unit tests for DiscordAdapter

Tests the DiscordAdapter implementation including:
- Configuration validation
- Bot lifecycle management (start/stop)
- Message sending (text, embeds, files)
- Message receiving and handling
- Error handling
- Discord-specific features
"""

import pytest
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime

from src.platforms.adapters.discord import DiscordAdapter, DISCORD_AVAILABLE
from src.platforms.models import MessageType

try:
    from discord.errors import DiscordException
except ImportError:
    DiscordException = Exception

pytestmark = pytest.mark.skipif(
    not DISCORD_AVAILABLE, reason="discord.py not installed"
)

if DISCORD_AVAILABLE:
    import discord
else:
    discord = None


class TestDiscordAdapter:
    """Test suite for DiscordAdapter"""

    @pytest.fixture
    def valid_config(self):
        """Fixture providing valid Discord configuration"""
        return {
            'bot_token': 'MTIzNDU2Nzg5MDEyMzQ1Njc4.G1a2b3.c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0',
            'command_prefix': '!',
            'intents': {
                'message_content': True,
                'messages': True,
                'guilds': True
            }
        }

    @pytest.fixture
    def adapter(self, valid_config):
        """Fixture providing a DiscordAdapter instance"""
        return DiscordAdapter(valid_config)

    def test_initialization_with_valid_config(self, valid_config):
        """Test adapter initializes properly with valid config"""
        adapter = DiscordAdapter(valid_config)

        assert adapter is not None
        assert adapter.config == valid_config
        assert adapter.platform_name == "discord"
        assert adapter.is_running is False
        assert adapter.bot is None
        assert adapter.message_handler_callback is None
        assert hasattr(adapter, 'logger')

    def test_initialization_with_invalid_config_missing_token(self):
        """Test adapter initialization fails without bot_token"""
        invalid_config = {'command_prefix': '!'}

        with pytest.raises(ValueError) as exc_info:
            DiscordAdapter(invalid_config)

        assert "bot_token" in str(exc_info.value)

    def test_initialization_with_empty_token(self):
        """Test adapter initialization fails with empty bot_token"""
        invalid_config = {'bot_token': ''}

        with pytest.raises(ValueError) as exc_info:
            DiscordAdapter(invalid_config)

        assert "bot_token" in str(exc_info.value)
        assert "empty" in str(exc_info.value).lower()

    def test_initialization_with_whitespace_token(self):
        """Test adapter initialization fails with whitespace-only token"""
        invalid_config = {'bot_token': '   '}

        with pytest.raises(ValueError) as exc_info:
            DiscordAdapter(invalid_config)

        assert "bot_token" in str(exc_info.value)

    def test_get_platform_name(self, adapter):
        """Test get_platform_name returns 'discord'"""
        assert adapter.get_platform_name() == "discord"

    def test_validate_config_success(self, valid_config):
        """Test validate_config passes with valid configuration"""
        adapter = DiscordAdapter(valid_config)
        # If we reach here without exception, validation passed
        assert adapter.config == valid_config

    def test_get_status_before_start(self, adapter):
        """Test get_status returns correct status before starting"""
        status = adapter.get_status()

        assert isinstance(status, dict)
        assert status['platform'] == 'discord'
        assert status['is_running'] is False
        assert status['config_valid'] is True

    @pytest.mark.asyncio
    @patch('src.platforms.adapters.discord.commands.Bot')
    @patch('asyncio.create_task')
    @patch('asyncio.sleep', new_callable=AsyncMock)
    async def test_start_success(self, mock_sleep, mock_create_task, mock_bot_class, adapter):
        """Test successful start of Discord adapter"""
        mock_bot_instance = MagicMock()
        mock_bot_instance.user = MagicMock(name="TestBot")
        mock_bot_instance.start = AsyncMock()
        mock_bot_class.return_value = mock_bot_instance

        mock_task = MagicMock()
        mock_create_task.return_value = mock_task

        await adapter.start()

        assert adapter.is_running is True
        assert adapter.bot is not None
        mock_bot_class.assert_called_once()
        mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_when_already_running(self, adapter):
        """Test start when adapter is already running"""
        adapter.is_running = True

        await adapter.start()

        # Should return early without error
        assert adapter.is_running is True

    @pytest.mark.asyncio
    @patch('src.platforms.adapters.discord.commands.Bot')
    async def test_start_with_discord_error(self, mock_bot_class, adapter):
        """Test start fails gracefully with DiscordException"""
        mock_bot_class.side_effect = DiscordException("Connection failed")

        with pytest.raises(DiscordException):
            await adapter.start()

        assert adapter.is_running is False

    @pytest.mark.asyncio
    async def test_stop_success(self, adapter):
        """Test successful stop of Discord adapter"""
        # Setup adapter as if it's running
        mock_bot = AsyncMock()
        mock_bot.close = AsyncMock()

        mock_task = MagicMock()
        mock_task.cancel = MagicMock()

        adapter.bot = mock_bot
        adapter._bot_task = mock_task
        adapter.is_running = True

        await adapter.stop()

        assert adapter.is_running is False
        assert adapter.bot is None
        mock_bot.close.assert_called_once()
        mock_task.cancel.assert_called_once()

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
            await adapter.send_message("123456789", "Hello")

        assert "not started" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_send_text_message_success(self, adapter):
        """Test successful text message sending"""
        # Setup mock bot and channel
        mock_message = MagicMock()
        mock_message.id = 987654321
        mock_message.channel_id = 123456789

        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(return_value=mock_message)

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("123456789", "Hello Discord")

        assert result["success"] is True
        assert result["message_id"] == "987654321"
        assert result["platform"] == "discord"
        mock_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_to_user_dm(self, adapter):
        """Test sending DM to a user"""
        mock_message = MagicMock()
        mock_message.id = 987654321

        mock_dm_channel = AsyncMock()
        mock_dm_channel.send = AsyncMock(return_value=mock_message)

        mock_user = AsyncMock()
        mock_user.create_dm = AsyncMock(return_value=mock_dm_channel)

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=None)
        mock_bot.fetch_channel = AsyncMock(side_effect=Exception("Not a channel"))
        mock_bot.fetch_user = AsyncMock(return_value=mock_user)

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("123456789", "Hello in DM")

        assert result["success"] is True
        mock_user.create_dm.assert_called_once()
        mock_dm_channel.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_with_embed(self, adapter):
        """Test sending message with embed"""
        mock_message = MagicMock()
        mock_message.id = 987654321

        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(return_value=mock_message)

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        adapter.bot = mock_bot
        adapter.is_running = True

        metadata = {
            "embed": {
                "title": "Test Embed",
                "description": "This is a test",
                "color": 0x00ff00
            }
        }

        result = await adapter.send_message("123456789", "Check this embed", metadata)

        assert result["success"] is True
        mock_channel.send.assert_called_once()
        call_kwargs = mock_channel.send.call_args[1]
        assert "embed" in call_kwargs

    @pytest.mark.asyncio
    async def test_send_message_with_reply(self, adapter):
        """Test sending message as reply"""
        mock_reply_message = MagicMock()
        mock_reply_message.id = 111111111

        mock_sent_message = MagicMock()
        mock_sent_message.id = 987654321

        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(return_value=mock_sent_message)
        mock_channel.fetch_message = AsyncMock(return_value=mock_reply_message)

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        adapter.bot = mock_bot
        adapter.is_running = True

        metadata = {
            "reply_to_message_id": "111111111"
        }

        result = await adapter.send_message("123456789", "This is a reply", metadata)

        assert result["success"] is True
        mock_channel.fetch_message.assert_called_once_with(111111111)
        call_kwargs = mock_channel.send.call_args[1]
        assert "reference" in call_kwargs

    @pytest.mark.asyncio
    async def test_send_message_reply_not_found(self, adapter):
        """Test sending message when reply-to message not found"""
        mock_sent_message = MagicMock()
        mock_sent_message.id = 987654321

        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(return_value=mock_sent_message)
        mock_channel.fetch_message = AsyncMock(side_effect=Exception("Message not found"))

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        adapter.bot = mock_bot
        adapter.is_running = True

        metadata = {
            "reply_to_message_id": "999999999"
        }

        result = await adapter.send_message("123456789", "Message", metadata)

        # Should succeed even if reply-to fails
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_message_channel_not_found(self, adapter):
        """Test send_message when channel/user not found"""
        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=None)
        mock_bot.fetch_channel = AsyncMock(side_effect=Exception("Not found"))
        mock_bot.fetch_user = AsyncMock(side_effect=Exception("User not found"))

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("999999999", "Hello")

        assert result["success"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_send_message_discord_error(self, adapter):
        """Test send_message handles DiscordException gracefully"""
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(
            side_effect=DiscordException("Forbidden")
        )

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("123456789", "Hello")

        assert result["success"] is False
        assert "error" in result
        assert "Forbidden" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_unexpected_error(self, adapter):
        """Test send_message handles unexpected errors"""
        mock_channel = AsyncMock()
        mock_channel.send = AsyncMock(
            side_effect=Exception("Unexpected error")
        )

        mock_bot = MagicMock()
        mock_bot.get_channel = MagicMock(return_value=mock_channel)

        adapter.bot = mock_bot
        adapter.is_running = True

        result = await adapter.send_message("123456789", "Hello")

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
    async def test_handle_discord_message_text(self, adapter):
        """Test handling incoming text message"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        # Create mock Discord message
        mock_author = MagicMock()
        mock_author.id = 123456789
        mock_author.name = "testuser"
        mock_author.discriminator = "1234"
        mock_author.bot = False

        mock_channel = MagicMock()
        mock_channel.id = 987654321

        mock_guild = MagicMock()
        mock_guild.id = 111222333

        mock_message = MagicMock()
        mock_message.id = 555666777
        mock_message.author = mock_author
        mock_message.channel = mock_channel
        mock_message.guild = mock_guild
        mock_message.content = "Hello Discord!"
        mock_message.created_at = datetime.utcnow()
        mock_message.attachments = []
        mock_message.embeds = []
        mock_message.reference = None

        mock_bot_user = MagicMock()
        mock_bot_user.id = 999999999

        adapter.bot = MagicMock()
        adapter.bot.user = mock_bot_user

        await adapter._handle_discord_message(mock_message)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["message_id"] == "555666777"
        assert msg["user_id"] == "123456789"
        assert msg["content"] == "Hello Discord!"
        assert msg["platform"] == "discord"
        assert msg["message_type"] == MessageType.TEXT.value
        assert msg["metadata"]["author_name"] == "testuser"
        assert msg["metadata"]["channel_id"] == "987654321"

    @pytest.mark.asyncio
    async def test_handle_discord_message_with_image_attachment(self, adapter):
        """Test handling message with image attachment"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        # Create mock attachment
        mock_attachment = MagicMock()
        mock_attachment.id = 444333222
        mock_attachment.filename = "image.jpg"
        mock_attachment.url = "https://cdn.discord.com/attachments/123/456/image.jpg"
        mock_attachment.content_type = "image/jpeg"
        mock_attachment.size = 1024000

        mock_author = MagicMock()
        mock_author.id = 123456789
        mock_author.name = "testuser"
        mock_author.discriminator = "1234"
        mock_author.bot = False

        mock_channel = MagicMock()
        mock_channel.id = 987654321

        mock_message = MagicMock()
        mock_message.id = 555666777
        mock_message.author = mock_author
        mock_message.channel = mock_channel
        mock_message.guild = None
        mock_message.content = "Check this out"
        mock_message.created_at = datetime.utcnow()
        mock_message.attachments = [mock_attachment]
        mock_message.embeds = []
        mock_message.reference = None

        mock_bot_user = MagicMock()
        mock_bot_user.id = 999999999

        adapter.bot = MagicMock()
        adapter.bot.user = mock_bot_user

        await adapter._handle_discord_message(mock_message)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["message_type"] == MessageType.IMAGE.value
        assert "attachments" in msg["metadata"]
        assert len(msg["metadata"]["attachments"]) == 1
        assert msg["metadata"]["attachments"][0]["filename"] == "image.jpg"

    @pytest.mark.asyncio
    async def test_handle_discord_message_with_video_attachment(self, adapter):
        """Test handling message with video attachment"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        mock_attachment = MagicMock()
        mock_attachment.id = 444333222
        mock_attachment.filename = "video.mp4"
        mock_attachment.url = "https://cdn.discord.com/video.mp4"
        mock_attachment.content_type = "video/mp4"
        mock_attachment.size = 5000000

        mock_author = MagicMock()
        mock_author.id = 123456789
        mock_author.name = "testuser"
        mock_author.discriminator = "1234"
        mock_author.bot = False

        mock_channel = MagicMock()
        mock_channel.id = 987654321

        mock_message = MagicMock()
        mock_message.id = 555666777
        mock_message.author = mock_author
        mock_message.channel = mock_channel
        mock_message.guild = None
        mock_message.content = "Watch this"
        mock_message.created_at = datetime.utcnow()
        mock_message.attachments = [mock_attachment]
        mock_message.embeds = []
        mock_message.reference = None

        mock_bot_user = MagicMock()
        mock_bot_user.id = 999999999

        adapter.bot = MagicMock()
        adapter.bot.user = mock_bot_user

        await adapter._handle_discord_message(mock_message)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["message_type"] == MessageType.VIDEO.value

    @pytest.mark.asyncio
    async def test_handle_discord_message_with_embeds(self, adapter):
        """Test handling message with embeds"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        mock_embed = MagicMock()
        mock_embed.to_dict = MagicMock(return_value={
            "title": "Test Embed",
            "description": "Test description"
        })

        mock_author = MagicMock()
        mock_author.id = 123456789
        mock_author.name = "testuser"
        mock_author.discriminator = "1234"
        mock_author.bot = False

        mock_channel = MagicMock()
        mock_channel.id = 987654321

        mock_message = MagicMock()
        mock_message.id = 555666777
        mock_message.author = mock_author
        mock_message.channel = mock_channel
        mock_message.guild = None
        mock_message.content = "Embedded content"
        mock_message.created_at = datetime.utcnow()
        mock_message.attachments = []
        mock_message.embeds = [mock_embed]
        mock_message.reference = None

        mock_bot_user = MagicMock()
        mock_bot_user.id = 999999999

        adapter.bot = MagicMock()
        adapter.bot.user = mock_bot_user

        await adapter._handle_discord_message(mock_message)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert "embeds" in msg["metadata"]
        assert len(msg["metadata"]["embeds"]) == 1

    @pytest.mark.asyncio
    async def test_handle_discord_message_ignore_self(self, adapter):
        """Test that messages from bot itself are ignored"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        mock_bot_user = MagicMock()
        mock_bot_user.id = 999999999

        mock_message = MagicMock()
        mock_message.author = mock_bot_user
        mock_message.content = "Self message"

        adapter.bot = MagicMock()
        adapter.bot.user = mock_bot_user

        await adapter._handle_discord_message(mock_message)

        # Should not process own messages
        assert len(received_messages) == 0

    @pytest.mark.asyncio
    async def test_handle_discord_message_no_handler(self, adapter):
        """Test handling message when no handler is registered"""
        mock_author = MagicMock()
        mock_author.id = 123456789

        mock_bot_user = MagicMock()
        mock_bot_user.id = 999999999

        mock_message = MagicMock()
        mock_message.author = mock_author
        mock_message.content = "Hello"

        adapter.bot = MagicMock()
        adapter.bot.user = mock_bot_user

        # Should not raise error
        await adapter._handle_discord_message(mock_message)

    @pytest.mark.asyncio
    async def test_handle_discord_message_with_reply(self, adapter):
        """Test handling message that is a reply"""
        received_messages = []

        async def mock_handler(message: Dict[str, Any]):
            received_messages.append(message)

        adapter.message_handler_callback = mock_handler

        mock_reference = MagicMock()
        mock_reference.message_id = 111111111

        mock_author = MagicMock()
        mock_author.id = 123456789
        mock_author.name = "testuser"
        mock_author.discriminator = "1234"
        mock_author.bot = False

        mock_channel = MagicMock()
        mock_channel.id = 987654321

        mock_message = MagicMock()
        mock_message.id = 555666777
        mock_message.author = mock_author
        mock_message.channel = mock_channel
        mock_message.guild = None
        mock_message.content = "Reply message"
        mock_message.created_at = datetime.utcnow()
        mock_message.attachments = []
        mock_message.embeds = []
        mock_message.reference = mock_reference

        mock_bot_user = MagicMock()
        mock_bot_user.id = 999999999

        adapter.bot = MagicMock()
        adapter.bot.user = mock_bot_user

        await adapter._handle_discord_message(mock_message)

        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg["reply_to_id"] == "111111111"

    def test_logger_is_configured(self, adapter):
        """Test that logger is properly configured"""
        assert hasattr(adapter, 'logger')
        assert 'discord' in adapter.logger.name.lower()

    def test_log_methods(self, adapter):
        """Test logging helper methods"""
        # Should not raise errors
        adapter.log_info("Info message")
        adapter.log_debug("Debug message")
        adapter.log_warning("Warning message")
        adapter.log_error("Error message")
        adapter.log_error("Error with exception", Exception("test"))
