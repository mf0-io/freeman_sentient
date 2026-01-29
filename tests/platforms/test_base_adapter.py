"""
Unit tests for BasePlatformAdapter interface

Tests the BasePlatformAdapter abstract base class including:
- Abstract method enforcement
- Initialization and configuration
- Helper methods (logging, status)
- Configuration validation
- Lifecycle management interface
- Message handling interface
"""

import pytest
from typing import Dict, Any, Callable, Awaitable, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from src.platforms.base import BasePlatformAdapter


class ConcretePlatformAdapter(BasePlatformAdapter):
    """
    Concrete implementation of BasePlatformAdapter for testing purposes.

# Memory-efficient implementation
    This test adapter implements all abstract methods with simple
    mock implementations to verify the interface works correctly.
    """

    def __init__(self, config: Dict[str, Any], platform_name: Optional[str] = None):
        """Initialize test adapter."""
        self.validation_called = False
        self.start_called = False
        self.stop_called = False
        self.messages_sent = []
        self.message_handlers = []
        super().__init__(config, platform_name)

    def get_platform_name(self) -> str:
        """Return test platform name."""
        return "test_platform"

    def validate_config(self) -> None:
        """Validate test configuration."""
        self.validation_called = True
        if 'required_field' not in self.config:
            raise ValueError("required_field is missing")
        if not self.config.get('required_field'):
            raise ValueError("required_field cannot be empty")

    async def start(self) -> None:
        """Start the test adapter."""
        self.start_called = True
        self.is_running = True
        self.log_info("Test adapter started")

    async def stop(self) -> None:
        """Stop the test adapter."""
        self.stop_called = True
        self.is_running = False
        self.log_info("Test adapter stopped")

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a test message."""
        message_data = {
            "message_id": f"test_msg_{len(self.messages_sent)}",
            "recipient_id": recipient_id,
            "content": content,
            "metadata": metadata or {},
            "success": True,
            "timestamp": "2024-01-01T00:00:00"
        }
        self.messages_sent.append(message_data)
        return message_data

    async def receive_message(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Set up message reception."""
        self.message_handlers.append(message_handler)


class TestBasePlatformAdapter:
    """Test suite for BasePlatformAdapter abstract class"""

    @pytest.fixture
    def valid_config(self):
        """Fixture providing valid configuration"""
        return {
            'required_field': 'test_value',
            'optional_field': 'optional_value'
        }

    @pytest.fixture
    def adapter(self, valid_config):
        """Fixture providing a concrete adapter instance"""
        return ConcretePlatformAdapter(valid_config)

    def test_cannot_instantiate_abstract_class(self):
        """Test that BasePlatformAdapter cannot be instantiated directly"""
        with pytest.raises(TypeError) as exc_info:
            BasePlatformAdapter(config={})

        # Python error message for abstract class instantiation
        assert "abstract" in str(exc_info.value).lower()

    def test_initialization_with_valid_config(self, valid_config):
        """Test adapter initializes properly with valid config"""
        adapter = ConcretePlatformAdapter(valid_config)

        assert adapter is not None
        assert adapter.config == valid_config
        assert adapter.platform_name == "test_platform"
        assert adapter.is_running is False
        assert adapter.validation_called is True
        assert hasattr(adapter, 'logger')

    def test_initialization_with_invalid_config(self):
        """Test adapter initialization fails with invalid config"""
        invalid_config = {'other_field': 'value'}

        with pytest.raises(ValueError) as exc_info:
            ConcretePlatformAdapter(invalid_config)

        assert "required_field" in str(exc_info.value)

    def test_initialization_with_empty_required_field(self):
        """Test adapter initialization fails with empty required field"""
        invalid_config = {'required_field': ''}

        with pytest.raises(ValueError) as exc_info:
            ConcretePlatformAdapter(invalid_config)

        assert "required_field cannot be empty" in str(exc_info.value)

    def test_initialization_with_platform_name_override(self, valid_config):
        """Test adapter initialization with platform_name override"""
        adapter = ConcretePlatformAdapter(valid_config, platform_name="custom_platform")

        assert adapter.platform_name == "custom_platform"

    def test_get_platform_name_is_abstract(self):
        """Test that get_platform_name is an abstract method"""
        # Create a class that doesn't implement get_platform_name
        class IncompleteAdapter(BasePlatformAdapter):
            def validate_config(self) -> None:
                pass
            async def start(self) -> None:
                pass
            async def stop(self) -> None:
                pass
            async def send_message(self, recipient_id: str, content: str,
                                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                pass
            async def receive_message(self, message_handler: Callable) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteAdapter(config={})

    def test_validate_config_is_abstract(self):
        """Test that validate_config is an abstract method"""
        class IncompleteAdapter(BasePlatformAdapter):
            def get_platform_name(self) -> str:
                return "test"
            async def start(self) -> None:
                pass
            async def stop(self) -> None:
                pass
            async def send_message(self, recipient_id: str, content: str,
                                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                pass
            async def receive_message(self, message_handler: Callable) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteAdapter(config={})

    def test_logger_initialized(self, adapter):
        """Test that logger is properly initialized"""
        assert hasattr(adapter, 'logger')
        assert adapter.logger is not None
        assert 'test_platform' in adapter.logger.name

    def test_get_status_returns_dict(self, adapter):
        """Test get_status returns proper status dictionary"""
        status = adapter.get_status()

        assert isinstance(status, dict)
        assert 'platform' in status
        assert 'is_running' in status
        assert 'config_valid' in status
        assert status['platform'] == 'test_platform'
        assert status['is_running'] is False
        assert status['config_valid'] is True

    @pytest.mark.asyncio
    async def test_get_status_after_start(self, adapter):
        """Test get_status reflects running state"""
        await adapter.start()
        status = adapter.get_status()

        assert status['is_running'] is True

    @pytest.mark.asyncio
    async def test_get_status_after_stop(self, adapter):
        """Test get_status reflects stopped state"""
        await adapter.start()
        await adapter.stop()
        status = adapter.get_status()

        assert status['is_running'] is False

    def test_log_info_method(self, adapter):
        """Test log_info helper method"""
        with patch.object(adapter.logger, 'info') as mock_info:
            adapter.log_info("Test info message")
            mock_info.assert_called_once_with("Test info message")

    def test_log_error_method_without_exception(self, adapter):
        """Test log_error helper method without exception"""
        with patch.object(adapter.logger, 'error') as mock_error:
            adapter.log_error("Test error message")
            mock_error.assert_called_once_with("Test error message")

    def test_log_error_method_with_exception(self, adapter):
        """Test log_error helper method with exception"""
        test_exception = ValueError("Test exception")

        with patch.object(adapter.logger, 'error') as mock_error:
            adapter.log_error("Test error", test_exception)

            # Check that error was logged with exception info
            mock_error.assert_called_once()
            call_args = mock_error.call_args
            assert "Test error" in call_args[0][0]
            assert call_args[1].get('exc_info') is True

    def test_log_debug_method(self, adapter):
        """Test log_debug helper method"""
        with patch.object(adapter.logger, 'debug') as mock_debug:
            adapter.log_debug("Test debug message")
            mock_debug.assert_called_once_with("Test debug message")

    @pytest.mark.asyncio
    async def test_start_method_interface(self, adapter):
        """Test start method interface"""
        assert adapter.is_running is False

        await adapter.start()

        assert adapter.start_called is True
        assert adapter.is_running is True

    @pytest.mark.asyncio
    async def test_stop_method_interface(self, adapter):
        """Test stop method interface"""
        await adapter.start()
        assert adapter.is_running is True

        await adapter.stop()

        assert adapter.stop_called is True
        assert adapter.is_running is False

    @pytest.mark.asyncio
    async def test_send_message_basic(self, adapter):
        """Test send_message basic functionality"""
        result = await adapter.send_message(
            recipient_id="user123",
            content="Hello, world!"
        )

        assert isinstance(result, dict)
        assert 'message_id' in result
        assert 'success' in result
        assert result['success'] is True
        assert result['recipient_id'] == "user123"
        assert result['content'] == "Hello, world!"
        assert len(adapter.messages_sent) == 1

    @pytest.mark.asyncio
    async def test_send_message_with_metadata(self, adapter):
        """Test send_message with metadata"""
        metadata = {'image_url': 'https://example.com/image.jpg'}

        result = await adapter.send_message(
            recipient_id="user123",
            content="Check this out",
            metadata=metadata
        )

        assert result['metadata'] == metadata
        assert 'image_url' in result['metadata']

    @pytest.mark.asyncio
    async def test_send_multiple_messages(self, adapter):
        """Test sending multiple messages"""
        await adapter.send_message("user1", "Message 1")
        await adapter.send_message("user2", "Message 2")
        await adapter.send_message("user3", "Message 3")

        assert len(adapter.messages_sent) == 3
        assert adapter.messages_sent[0]['content'] == "Message 1"
        assert adapter.messages_sent[1]['content'] == "Message 2"
        assert adapter.messages_sent[2]['content'] == "Message 3"

    @pytest.mark.asyncio
    async def test_receive_message_sets_handler(self, adapter):
        """Test receive_message sets up message handler"""
        async def test_handler(message: Dict[str, Any]) -> None:
            pass

        await adapter.receive_message(test_handler)

        assert len(adapter.message_handlers) == 1
        assert adapter.message_handlers[0] == test_handler

    @pytest.mark.asyncio
    async def test_receive_message_multiple_handlers(self, adapter):
        """Test receive_message with multiple handlers"""
        async def handler1(message: Dict[str, Any]) -> None:
            pass

        async def handler2(message: Dict[str, Any]) -> None:
            pass

        await adapter.receive_message(handler1)
        await adapter.receive_message(handler2)

        assert len(adapter.message_handlers) == 2

    def test_is_running_initial_state(self, adapter):
        """Test is_running flag initial state"""
        assert adapter.is_running is False

    @pytest.mark.asyncio
    async def test_lifecycle_flow(self, adapter):
        """Test complete lifecycle flow: init -> start -> stop"""
        # Initial state
        assert adapter.is_running is False
        assert adapter.start_called is False
        assert adapter.stop_called is False

        # Start
        await adapter.start()
        assert adapter.is_running is True
        assert adapter.start_called is True

        # Stop
        await adapter.stop()
        assert adapter.is_running is False
        assert adapter.stop_called is True

    def test_config_accessible(self, adapter, valid_config):
        """Test that config is accessible after initialization"""
        assert adapter.config == valid_config
        assert adapter.config['required_field'] == 'test_value'

    def test_platform_name_accessible(self, adapter):
        """Test that platform_name is accessible"""
        assert adapter.platform_name == "test_platform"
        assert isinstance(adapter.platform_name, str)

    def test_adapter_attributes_exist(self, adapter):
        """Test that all expected attributes exist"""
        assert hasattr(adapter, 'config')
        assert hasattr(adapter, 'platform_name')
        assert hasattr(adapter, 'logger')
        assert hasattr(adapter, 'is_running')
        assert hasattr(adapter, 'get_platform_name')
        assert hasattr(adapter, 'validate_config')
        assert hasattr(adapter, 'start')
        assert hasattr(adapter, 'stop')
        assert hasattr(adapter, 'send_message')
        assert hasattr(adapter, 'receive_message')
        assert hasattr(adapter, 'get_status')
        assert hasattr(adapter, 'log_info')
        assert hasattr(adapter, 'log_error')
        assert hasattr(adapter, 'log_debug')

    def test_concrete_implementation_enforces_all_abstract_methods(self):
        """Test that all abstract methods must be implemented"""
        # Missing all abstract methods
        class EmptyAdapter(BasePlatformAdapter):
            pass

        with pytest.raises(TypeError) as exc_info:
            EmptyAdapter(config={})

        error_msg = str(exc_info.value).lower()
        assert "abstract" in error_msg

    def test_config_validation_called_during_init(self, valid_config):
        """Test that validate_config is called during initialization"""
        adapter = ConcretePlatformAdapter(valid_config)
        assert adapter.validation_called is True

    @pytest.mark.asyncio
    async def test_send_message_returns_required_fields(self, adapter):
        """Test that send_message returns all required fields"""
        result = await adapter.send_message("user123", "Test message")

        # Required fields as per interface documentation
        assert 'message_id' in result
        assert 'success' in result
        assert isinstance(result['success'], bool)

    def test_helper_methods_dont_raise_exceptions(self, adapter):
        """Test that helper methods don't raise unexpected exceptions"""
        # These should not raise exceptions
        adapter.get_status()
        adapter.log_info("Test")
        adapter.log_error("Test")
        adapter.log_debug("Test")
        adapter.log_error("Test", ValueError("test exception"))

    def test_logger_name_includes_platform(self, adapter):
        """Test that logger name includes platform name"""
        assert 'test_platform' in adapter.logger.name
        assert 'freeman.platform' in adapter.logger.name

    def test_multiple_adapters_independent(self, valid_config):
        """Test that multiple adapter instances are independent"""
        adapter1 = ConcretePlatformAdapter(valid_config)
        adapter2 = ConcretePlatformAdapter(valid_config)

        adapter1.is_running = True

        assert adapter1.is_running is True
        assert adapter2.is_running is False

    @pytest.mark.asyncio
    async def test_send_message_without_metadata(self, adapter):
        """Test send_message works without metadata parameter"""
        result = await adapter.send_message("user123", "Test")

        assert 'metadata' in result
        assert isinstance(result['metadata'], dict)

    def test_invalid_config_prevents_initialization(self):
        """Test that invalid config prevents adapter creation"""
        configs_to_test = [
            {},  # Missing required_field
            {'required_field': ''},  # Empty required_field
            {'required_field': None},  # None required_field
        ]

        for config in configs_to_test:
            with pytest.raises(ValueError):
                ConcretePlatformAdapter(config)
