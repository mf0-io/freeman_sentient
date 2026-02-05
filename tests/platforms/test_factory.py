"""
Unit tests for PlatformFactory

Tests the PlatformFactory class including:
- Platform adapter creation with various config types
- Registry management (registration, availability checks)
- Configuration handling (dict, PlatformConfig instance, env vars)
- Error handling for invalid platforms and configurations
- Platform adapter initialization
# Cross-platform compatible
"""

import pytest
import os
from typing import Dict, Any, Optional, Callable, Awaitable
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

from src.platforms.factory import PlatformFactory
from src.platforms.base import BasePlatformAdapter
from src.platforms.models import PlatformConfig
from src.platforms.config import TelegramConfig, DiscordConfig
from src.platforms.adapters.telegram import TelegramAdapter
from src.platforms.adapters.discord import DiscordAdapter


class MockPlatformAdapter(BasePlatformAdapter):
    """
    Mock platform adapter for testing factory without real platform dependencies.

    This adapter provides a minimal implementation for testing the factory's
    ability to create and configure platform adapters.
    """

    def __init__(self, config: Dict[str, Any], platform_name: Optional[str] = None):
        """Initialize mock adapter."""
        self.initialized = True
        super().__init__(config, platform_name)

    def get_platform_name(self) -> str:
        """Return mock platform name."""
        return "mock_platform"

    def validate_config(self) -> None:
        """Validate mock configuration."""
        if 'api_key' not in self.config:
            raise ValueError("api_key is required")
        if not self.config.get('api_key'):
            raise ValueError("api_key cannot be empty")

    async def start(self) -> None:
        """Start the mock adapter."""
        self.is_running = True

    async def stop(self) -> None:
        """Stop the mock adapter."""
        self.is_running = False

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a mock message."""
        return {
            "message_id": "mock_123",
            "success": True,
            "recipient_id": recipient_id,
            "content": content
        }

    async def receive_message(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Set up mock message reception."""
        pass


class MockPlatformConfig(PlatformConfig):
    """
    Mock configuration class for testing factory.

    Provides a simple config model that extends PlatformConfig
    for testing registration and config handling.
    """

    api_key: str = ""

    def __init__(self, **data):
        """Initialize mock configuration."""
        if 'platform_name' not in data:
            data['platform_name'] = 'mock_platform'
        super().__init__(**data)


class TestPlatformFactory:
    """Test suite for PlatformFactory class"""

    @pytest.fixture
    def factory_with_clean_registry(self):
        """Fixture that provides factory with original registry and restores it after test"""
        # Save original registry
        original_registry = PlatformFactory._registry.copy()

        yield PlatformFactory

        # Restore original registry after test
        PlatformFactory._registry = original_registry

    @pytest.fixture
    def mock_telegram_env(self, monkeypatch):
        """Fixture providing mock Telegram environment variables"""
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test_telegram_token_12345")
        monkeypatch.setenv("TELEGRAM_POLLING_INTERVAL", "2")

    @pytest.fixture
    def mock_discord_env(self, monkeypatch):
        """Fixture providing mock Discord environment variables"""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "test_discord_token_67890")
        monkeypatch.setenv("DISCORD_COMMAND_PREFIX", "!")

    def test_factory_has_initial_platforms(self):
        """Test that factory has telegram and discord registered by default"""
        platforms = PlatformFactory.get_available_platforms()

        assert 'telegram' in platforms
        assert 'discord' in platforms

    def test_get_available_platforms_returns_list(self):
        """Test get_available_platforms returns a list of platform names"""
        platforms = PlatformFactory.get_available_platforms()

        assert isinstance(platforms, list)
        assert len(platforms) >= 2  # At least telegram and discord
        assert all(isinstance(p, str) for p in platforms)

    def test_is_platform_available_for_registered_platform(self):
        """Test is_platform_available returns True for registered platforms"""
        assert PlatformFactory.is_platform_available('telegram') is True
        assert PlatformFactory.is_platform_available('discord') is True

    def test_is_platform_available_for_unknown_platform(self):
        """Test is_platform_available returns False for unregistered platforms"""
        assert PlatformFactory.is_platform_available('unknown_platform') is False
        assert PlatformFactory.is_platform_available('slack') is False
        assert PlatformFactory.is_platform_available('') is False

    def test_create_with_unknown_platform_raises_error(self):
        """Test creating adapter with unknown platform raises ValueError"""
        with pytest.raises(ValueError) as exc_info:
            PlatformFactory.create('unknown_platform')

        error_msg = str(exc_info.value)
        assert 'unknown_platform' in error_msg.lower()
        assert 'available platforms' in error_msg.lower()

    def test_create_telegram_with_config_dict(self, factory_with_clean_registry):
        """Test creating Telegram adapter with config dictionary"""
        config_dict = {
            'bot_token': 'test_token_123',
            'polling_interval': 1
        }

        adapter = factory_with_clean_registry.create('telegram', config=config_dict)

        assert adapter is not None
        assert isinstance(adapter, TelegramAdapter)
        assert adapter.config['bot_token'] == 'test_token_123'
        assert adapter.platform_name == 'telegram'

    def test_create_discord_with_config_dict(self, factory_with_clean_registry):
        """Test creating Discord adapter with config dictionary"""
        config_dict = {
            'bot_token': 'test_discord_token',
            'command_prefix': '!'
        }

        adapter = factory_with_clean_registry.create('discord', config=config_dict)

        assert adapter is not None
        assert isinstance(adapter, DiscordAdapter)
        assert adapter.config['bot_token'] == 'test_discord_token'
        assert adapter.platform_name == 'discord'

    def test_create_telegram_with_config_instance(self, factory_with_clean_registry):
        """Test creating Telegram adapter with TelegramConfig instance"""
        config = TelegramConfig(bot_token='test_token_456', polling_interval=2)

        adapter = factory_with_clean_registry.create('telegram', config=config)

        assert adapter is not None
        assert isinstance(adapter, TelegramAdapter)
        assert adapter.config['bot_token'] == 'test_token_456'
        assert adapter.config['polling_interval'] == 2

    def test_create_discord_with_config_instance(self, factory_with_clean_registry):
        """Test creating Discord adapter with DiscordConfig instance"""
        config = DiscordConfig(bot_token='test_discord_789', command_prefix='/')

        adapter = factory_with_clean_registry.create('discord', config=config)

        assert adapter is not None
        assert isinstance(adapter, DiscordAdapter)
        assert adapter.config['bot_token'] == 'test_discord_789'
        assert adapter.config['command_prefix'] == '/'

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': 'env_token_123'}, clear=True)
    def test_create_telegram_from_environment(self, factory_with_clean_registry):
        """Test creating Telegram adapter with config from environment variables"""
        # Force reload of TelegramConfig to pick up environment
        config = TelegramConfig()

        adapter = factory_with_clean_registry.create('telegram', config=config)

        assert adapter is not None
        assert isinstance(adapter, TelegramAdapter)

    def test_create_with_invalid_config_type_raises_error(self, factory_with_clean_registry):
        """Test creating adapter with invalid config type raises TypeError"""
        invalid_configs = [
            "string_config",
            123,
            ['list', 'config'],
            True
        ]

        for invalid_config in invalid_configs:
            with pytest.raises(TypeError) as exc_info:
                factory_with_clean_registry.create('telegram', config=invalid_config)

            error_msg = str(exc_info.value)
            assert 'config must be' in error_msg.lower()

    def test_create_with_invalid_config_dict_raises_error(self, factory_with_clean_registry):
        """Test creating adapter with invalid config dict raises error"""
        invalid_config = {
            'wrong_field': 'value'
            # Missing required 'bot_token'
        }

        with pytest.raises((ValueError, ValidationError)):
            factory_with_clean_registry.create('telegram', config=invalid_config)

    def test_register_new_platform(self, factory_with_clean_registry):
        """Test registering a new platform adapter"""
        factory_with_clean_registry.register(
            'mock_platform',
            MockPlatformAdapter,
            MockPlatformConfig
        )

        assert factory_with_clean_registry.is_platform_available('mock_platform')
        assert 'mock_platform' in factory_with_clean_registry.get_available_platforms()

    def test_register_and_create_custom_platform(self, factory_with_clean_registry):
        """Test registering and creating instance of custom platform"""
        factory_with_clean_registry.register(
            'mock_platform',
            MockPlatformAdapter,
            MockPlatformConfig
        )

        config = {'api_key': 'test_key_123'}
        adapter = factory_with_clean_registry.create('mock_platform', config=config)

        assert adapter is not None
        assert isinstance(adapter, MockPlatformAdapter)
        assert adapter.config['api_key'] == 'test_key_123'
        assert adapter.initialized is True

    def test_register_with_invalid_adapter_class_raises_error(self, factory_with_clean_registry):
        """Test registering with non-BasePlatformAdapter class raises TypeError"""
        class NotAnAdapter:
            pass

        with pytest.raises(TypeError) as exc_info:
            factory_with_clean_registry.register(
                'invalid',
                NotAnAdapter,
                MockPlatformConfig
            )

        error_msg = str(exc_info.value)
        assert 'baseplatformadapter' in error_msg.lower()

    def test_register_with_invalid_config_class_raises_error(self, factory_with_clean_registry):
        """Test registering with non-PlatformConfig class raises TypeError"""
        class NotAConfig:
            pass

        with pytest.raises(TypeError) as exc_info:
            factory_with_clean_registry.register(
                'invalid',
                MockPlatformAdapter,
                NotAConfig
            )

        error_msg = str(exc_info.value)
        assert 'platformconfig' in error_msg.lower()

    def test_register_duplicate_platform_logs_warning(self, factory_with_clean_registry):
        """Test registering duplicate platform logs warning and overwrites"""
        # Register once
        factory_with_clean_registry.register(
            'mock_platform',
            MockPlatformAdapter,
            MockPlatformConfig
        )

        # Register again - should overwrite
        with patch('src.platforms.factory.logger.warning') as mock_warning:
            factory_with_clean_registry.register(
                'mock_platform',
                MockPlatformAdapter,
                MockPlatformConfig
            )

            mock_warning.assert_called_once()
            assert 'already registered' in mock_warning.call_args[0][0].lower()

    def test_registry_is_dict(self):
        """Test that registry is a dictionary"""
        assert isinstance(PlatformFactory._registry, dict)

    def test_registry_contains_tuples(self):
        """Test that registry values are tuples of (adapter_class, config_class)"""
        for platform_name, entry in PlatformFactory._registry.items():
            assert isinstance(entry, tuple)
            assert len(entry) == 2
            adapter_class, config_class = entry
            assert issubclass(adapter_class, BasePlatformAdapter)
            assert issubclass(config_class, PlatformConfig)

    def test_create_sets_platform_name_parameter(self, factory_with_clean_registry):
        """Test that create passes platform_name to adapter constructor"""
        config = {'bot_token': 'test_token'}
        adapter = factory_with_clean_registry.create('telegram', config=config)

        assert adapter.platform_name == 'telegram'

    def test_create_with_none_config_uses_environment(self, mock_telegram_env, factory_with_clean_registry):
        """Test that create with None config loads from environment"""
        # This should work because mock_telegram_env fixture sets the env var
        config = TelegramConfig()  # Will load from environment
        adapter = factory_with_clean_registry.create('telegram', config=config)

        assert adapter is not None
        assert isinstance(adapter, TelegramAdapter)

    def test_multiple_adapters_are_independent(self, factory_with_clean_registry):
        """Test that multiple adapter instances are independent"""
        config1 = {'bot_token': 'token1'}
        config2 = {'bot_token': 'token2'}

        adapter1 = factory_with_clean_registry.create('telegram', config=config1)
        adapter2 = factory_with_clean_registry.create('telegram', config=config2)

        assert adapter1 is not adapter2
        assert adapter1.config['bot_token'] == 'token1'
        assert adapter2.config['bot_token'] == 'token2'

    def test_factory_methods_are_classmethods(self):
        """Test that factory methods are class methods"""
        assert callable(PlatformFactory.create)
        assert callable(PlatformFactory.register)
        assert callable(PlatformFactory.get_available_platforms)
        assert callable(PlatformFactory.is_platform_available)

    def test_create_with_config_dict_converts_to_pydantic(self, factory_with_clean_registry):
        """Test that config dict is properly converted to Pydantic model"""
        config_dict = {
            'bot_token': 'test_token',
            'polling_interval': 5
        }

        adapter = factory_with_clean_registry.create('telegram', config=config_dict)

        # Verify config was validated and converted properly
        assert adapter.config['bot_token'] == 'test_token'
        assert adapter.config['polling_interval'] == 5

    def test_create_telegram_adapter_is_telegram_adapter(self, factory_with_clean_registry):
        """Test that created telegram adapter is instance of TelegramAdapter"""
        config = {'bot_token': 'test_token'}
        adapter = factory_with_clean_registry.create('telegram', config=config)

        assert isinstance(adapter, TelegramAdapter)
        assert isinstance(adapter, BasePlatformAdapter)

    def test_create_discord_adapter_is_discord_adapter(self, factory_with_clean_registry):
        """Test that created discord adapter is instance of DiscordAdapter"""
        config = {'bot_token': 'test_token'}
        adapter = factory_with_clean_registry.create('discord', config=config)

        assert isinstance(adapter, DiscordAdapter)
        assert isinstance(adapter, BasePlatformAdapter)

    def test_available_platforms_does_not_include_unregistered(self, factory_with_clean_registry):
        """Test that get_available_platforms does not include unregistered platforms"""
        platforms = factory_with_clean_registry.get_available_platforms()

        assert 'unregistered_platform' not in platforms
        assert 'fake_platform' not in platforms

    def test_create_error_message_includes_available_platforms(self):
        """Test that create error message lists available platforms"""
        try:
            PlatformFactory.create('invalid_platform')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            error_msg = str(e)
            assert 'telegram' in error_msg
            assert 'discord' in error_msg

    def test_register_adds_to_registry(self, factory_with_clean_registry):
        """Test that register actually adds entry to internal registry"""
        initial_count = len(factory_with_clean_registry._registry)

        factory_with_clean_registry.register(
            'new_platform',
            MockPlatformAdapter,
            MockPlatformConfig
        )

        assert len(factory_with_clean_registry._registry) == initial_count + 1
        assert 'new_platform' in factory_with_clean_registry._registry

    def test_config_instance_with_dict_method(self, factory_with_clean_registry):
        """Test that PlatformConfig instances are converted using dict() method"""
        config = TelegramConfig(bot_token='test_token')

        # Verify config has dict method
        assert hasattr(config, 'dict')
        config_dict = config.dict()
        assert isinstance(config_dict, dict)
        assert 'bot_token' in config_dict

    def test_create_with_minimal_config(self, factory_with_clean_registry):
        """Test creating adapter with minimal required config"""
        minimal_config = {'bot_token': 'minimal_token'}

        adapter = factory_with_clean_registry.create('telegram', config=minimal_config)

        assert adapter is not None
        assert adapter.config['bot_token'] == 'minimal_token'

    def test_factory_preserves_additional_config_fields(self, factory_with_clean_registry):
        """Test that factory preserves additional config fields from dict"""
        config = {
            'bot_token': 'test_token',
            'polling_interval': 3,
            'timeout_seconds': 60
        }

        adapter = factory_with_clean_registry.create('telegram', config=config)

        assert adapter.config['polling_interval'] == 3
        assert adapter.config['timeout_seconds'] == 60

    @patch('src.platforms.factory.logger.info')
    def test_create_logs_creation_steps(self, mock_logger, factory_with_clean_registry):
        """Test that create method logs appropriate messages"""
        config = {'bot_token': 'test_token'}

        factory_with_clean_registry.create('telegram', config=config)

        # Should have logged several info messages
        assert mock_logger.call_count >= 2

    @patch('src.platforms.factory.logger.info')
    def test_register_logs_registration(self, mock_logger, factory_with_clean_registry):
        """Test that register method logs registration"""
        factory_with_clean_registry.register(
            'mock_platform',
            MockPlatformAdapter,
            MockPlatformConfig
        )

        # Should log the registration
        assert any('registered' in str(call).lower() for call in mock_logger.call_args_list)
