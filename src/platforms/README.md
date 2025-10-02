# Platform Extension Framework

This directory contains the platform adapter framework for Freeman, enabling multi-platform support (Telegram, Discord, Twitter, etc.) through a unified interface.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [How to Add a New Platform](#how-to-add-a-new-platform)
- [Interface Requirements](#interface-requirements)
- [Configuration Setup](#configuration-setup)
- [Example Code](#example-code)
- [Testing Your Adapter](#testing-your-adapter)

---

## Overview

The platform framework provides:

- **Unified Interface**: All platforms implement the same `BasePlatformAdapter` interface
- **Standardized Models**: Pydantic models for messages, users, and configurations
- **Factory Pattern**: Easy creation and registration of platform adapters
- **Type Safety**: Full type hints and runtime validation with Pydantic
- **Extensibility**: Add new platforms without modifying core code

---

## Architecture

```
platforms/
├── base.py              # BasePlatformAdapter - abstract base class
├── models.py            # Pydantic models (PlatformMessage, PlatformUser, etc.)
├── config.py            # Platform-specific configuration classes
├── factory.py           # PlatformFactory for creating adapters
├── adapters/            # Platform-specific implementations
│   ├── telegram.py      # TelegramAdapter implementation
│   ├── discord.py       # DiscordAdapter implementation
│   └── __init__.py
└── README.md            # This file
```

### Key Components

1. **BasePlatformAdapter**: Abstract base class defining the platform interface
2. **PlatformMessage**: Standardized message format across all platforms
3. **PlatformConfig**: Base configuration class with common settings
4. **PlatformFactory**: Factory for creating and registering adapters

---

## How to Add a New Platform

Follow these steps to add support for a new platform (e.g., Twitter, WhatsApp):

### Step 1: Create Configuration Class

Create a configuration class in `config.py`:

```python
class TwitterConfig(PlatformConfig):
    """Configuration for Twitter platform adapter."""

    api_key: str = Field(
        default_factory=lambda: os.getenv("TWITTER_API_KEY", ""),
        description="Twitter API key"
    )
    api_secret: str = Field(
        default_factory=lambda: os.getenv("TWITTER_API_SECRET", ""),
        description="Twitter API secret"
    )
    access_token: str = Field(
        default_factory=lambda: os.getenv("TWITTER_ACCESS_TOKEN", ""),
        description="Twitter access token"
    )

    def __init__(self, **data):
        if 'platform_name' not in data:
            data['platform_name'] = 'twitter'
        super().__init__(**data)

    @validator('api_key')
    def validate_api_key(cls, v):
        if not v or not v.strip():
            raise ValueError("api_key is required. Set TWITTER_API_KEY in .env")
        return v.strip()
```

### Step 2: Create Adapter Class

Create a new adapter file in `adapters/your_platform.py`:

```python
from typing import Optional, Dict, Any, Callable, Awaitable
from ..base import BasePlatformAdapter
from ..models import MessageType

class TwitterAdapter(BasePlatformAdapter):
    """Twitter platform adapter implementation."""

    def __init__(self, config: Dict[str, Any], platform_name: Optional[str] = None):
        # Initialize your platform-specific client
        self.client = None
        super().__init__(config, platform_name)

    def get_platform_name(self) -> str:
        """Return platform identifier."""
        return "twitter"

    def validate_config(self) -> None:
        """Validate platform configuration."""
        required_keys = ["api_key", "api_secret", "access_token"]
        for key in required_keys:
            if key not in self.config or not self.config[key]:
                raise ValueError(f"Twitter configuration requires '{key}'")

    async def start(self) -> None:
        """Start the adapter and begin listening."""
        if self.is_running:
            return

        # Initialize your platform client
        self.client = YourPlatformClient(
            api_key=self.config["api_key"],
            api_secret=self.config["api_secret"]
        )

        # Start listening for messages/events
        await self.client.start()

        self.is_running = True
        self.log_info("Twitter adapter started successfully")

    async def stop(self) -> None:
        """Stop the adapter and cleanup."""
        if not self.is_running:
            return

        # Cleanup resources
        if self.client:
            await self.client.stop()
            self.client = None

        self.is_running = False
        self.log_info("Twitter adapter stopped successfully")

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message to a user."""
        if not self.is_running or not self.client:
            raise RuntimeError("Adapter not started. Call start() first.")

        metadata = metadata or {}

        try:
            # Send message using your platform's API
            result = await self.client.send_message(
                to=recipient_id,
                text=content,
                **metadata
            )

            return {
                "success": True,
                "message_id": result.id,
                "timestamp": result.timestamp.isoformat(),
                "platform": self.platform_name,
                "metadata": {"extra": "data"}
            }
        except Exception as e:
            self.log_error(f"Error sending message to {recipient_id}", e)
            return {
                "success": False,
                "message_id": None,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": self.platform_name,
                "error": str(e)
            }

    async def receive_message(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """Register callback for incoming messages."""
        self.message_handler_callback = message_handler

        # Set up your platform's message listener
        # This will call message_handler with standardized message format
```

### Step 3: Register in Factory

Add your adapter to the factory registry in `factory.py`:

```python
from .adapters.twitter import TwitterAdapter
from .config import TwitterConfig

class PlatformFactory:
    _registry: Dict[str, tuple[Type[BasePlatformAdapter], Type[PlatformConfig]]] = {
        'telegram': (TelegramAdapter, TelegramConfig),
        'discord': (DiscordAdapter, DiscordConfig),
        'twitter': (TwitterAdapter, TwitterConfig),  # Add your platform
    }
```

### Step 4: Add Environment Variables

Document the required environment variables in `.env.example`:

```bash
# Twitter Configuration
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
```

### Step 5: Use Your Adapter

```python
from src.platforms.factory import PlatformFactory

# Create adapter (loads config from environment)
adapter = PlatformFactory.create('twitter')

# Or create with explicit config
adapter = PlatformFactory.create('twitter', config={
    'api_key': 'your_key',
    'api_secret': 'your_secret',
    'access_token': 'your_token'
})

# Start the adapter
await adapter.start()

# Send a message
result = await adapter.send_message(
    recipient_id="user_123",
    content="Hello from Freeman!",
    metadata={"image_url": "https://..."}
)

# Stop when done
await adapter.stop()
```

---

## Interface Requirements

All platform adapters **MUST** implement these abstract methods:

### Required Methods

#### 1. `get_platform_name() -> str`

Returns the unique identifier for your platform.

```python
def get_platform_name(self) -> str:
    return "twitter"  # Must be unique across all platforms
```

#### 2. `validate_config() -> None`

Validates platform-specific configuration. Raise `ValueError` if invalid.

```python
def validate_config(self) -> None:
    if "api_key" not in self.config:
        raise ValueError("api_key is required")
    if not self.config["api_key"].strip():
        raise ValueError("api_key cannot be empty")
```

#### 3. `async start() -> None`

Initialize the platform client and start listening for messages.

**Requirements:**
- Initialize platform-specific clients/connections
- Set up message handlers
- Begin polling or webhook listening
- Set `self.is_running = True`

```python
async def start(self) -> None:
    if self.is_running:
        return

    # Your initialization code
    self.client = PlatformClient(self.config["api_key"])
    await self.client.connect()

    self.is_running = True
```

#### 4. `async stop() -> None`

Stop the adapter and clean up resources.

**Requirements:**
- Stop polling/webhook listening
- Close connections
- Clean up resources
- Set `self.is_running = False`

```python
async def stop(self) -> None:
    if not self.is_running:
        return

    if self.client:
        await self.client.disconnect()
        self.client = None

    self.is_running = False
```

#### 5. `async send_message(recipient_id: str, content: str, metadata: Optional[Dict]) -> Dict`

Send a message to a user on the platform.

**Parameters:**
- `recipient_id`: Platform-specific user identifier
- `content`: Message text content
- `metadata`: Optional dict with additional data (images, reply_to, etc.)

**Returns:** Dictionary with:
- `success` (bool): Whether message was sent successfully
- `message_id` (str): Platform-specific message ID (if successful)
- `timestamp` (str): ISO format timestamp
- `platform` (str): Platform name
- `error` (str): Error message if failed
- `metadata` (dict): Additional platform-specific data

```python
async def send_message(
    self,
    recipient_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    try:
        result = await self.client.send(recipient_id, content)
        return {
            "success": True,
            "message_id": result.id,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": self.platform_name,
            "metadata": {}
        }
    except Exception as e:
        return {
            "success": False,
            "message_id": None,
            "timestamp": datetime.utcnow().isoformat(),
            "platform": self.platform_name,
            "error": str(e)
        }
```

#### 6. `async receive_message(message_handler: Callable) -> None`

Register a callback function for incoming messages.

**Parameters:**
- `message_handler`: Async function that receives standardized message dict

**Message Handler Format:**
The callback receives a dictionary with:
- `message_id` (str): Platform message ID
- `user_id` (str): Platform user ID
- `content` (str): Message text
- `timestamp` (str): ISO format timestamp
- `platform` (str): Platform name
- `message_type` (str): One of MessageType enum values
- `metadata` (dict): Platform-specific metadata

```python
async def receive_message(
    self,
    message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
) -> None:
    self.message_handler_callback = message_handler

    # When you receive a platform message, convert and call:
    # await message_handler(standardized_message_dict)
```

### Helper Methods (Inherited from Base)

These are provided by `BasePlatformAdapter` and don't need to be implemented:

- `get_status() -> Dict`: Returns adapter status
- `log_info(message: str)`: Log info-level message
- `log_error(message: str, error: Exception)`: Log error-level message
- `log_debug(message: str)`: Log debug-level message

---

## Configuration Setup

### Base Configuration

All platform configs extend `PlatformConfig` which provides:

```python
class PlatformConfig(BaseModel):
    platform_name: str              # Platform identifier
    enabled: bool = True            # Whether adapter is enabled
    max_retries: int = 3            # Retry attempts for failed operations
    timeout_seconds: int = 30       # API call timeout
    rate_limit_per_minute: int = 30 # Rate limiting (0 = unlimited)
```

### Creating Platform-Specific Config

1. Extend `PlatformConfig`
2. Add platform-specific fields with environment variable defaults
3. Set `platform_name` in `__init__`
4. Add validators for required fields

```python
from pydantic import Field, validator
import os

class MyPlatformConfig(PlatformConfig):
    api_token: str = Field(
        default_factory=lambda: os.getenv("MY_PLATFORM_TOKEN", ""),
        description="API token for MyPlatform"
    )

    webhook_url: Optional[str] = Field(
        default_factory=lambda: os.getenv("MY_PLATFORM_WEBHOOK"),
        description="Webhook URL for receiving updates"
    )

    def __init__(self, **data):
        if 'platform_name' not in data:
            data['platform_name'] = 'myplatform'
        super().__init__(**data)

    @validator('api_token')
    def validate_token(cls, v):
        if not v or not v.strip():
            raise ValueError(
                "api_token is required. "
                "Set MY_PLATFORM_TOKEN in .env file"
            )
        return v.strip()
```

### Environment Variables

Create a `.env` file in project root:

```bash
# MyPlatform Configuration
MY_PLATFORM_TOKEN=your_token_here
MY_PLATFORM_WEBHOOK=https://your-domain.com/webhook

# Optional: Override base config
MY_PLATFORM_MAX_RETRIES=5
MY_PLATFORM_TIMEOUT=60
```

---

## Example Code

### Complete Minimal Adapter

Here's a minimal working example for a hypothetical platform:

```python
# adapters/example.py
from datetime import datetime
from typing import Optional, Dict, Any, Callable, Awaitable
from ..base import BasePlatformAdapter

class ExampleAdapter(BasePlatformAdapter):
    """Example platform adapter - minimal implementation."""

    def __init__(self, config: Dict[str, Any], platform_name: Optional[str] = None):
        self.client = None
        self.callback = None
        super().__init__(config, platform_name)

    def get_platform_name(self) -> str:
        return "example"

    def validate_config(self) -> None:
        if "api_key" not in self.config:
            raise ValueError("api_key is required")

    async def start(self) -> None:
        if self.is_running:
            return

        # Initialize your client
        # self.client = ExampleClient(self.config["api_key"])

        self.is_running = True
        self.log_info("Example adapter started")

    async def stop(self) -> None:
        if not self.is_running:
            return

        # Cleanup
        self.client = None
        self.is_running = False
        self.log_info("Example adapter stopped")

    async def send_message(
        self,
        recipient_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        if not self.is_running:
            raise RuntimeError("Adapter not started")

        try:
            # Send via your platform's API
            # message_id = self.client.send(recipient_id, content)

            return {
                "success": True,
                "message_id": "msg_123",
                "timestamp": datetime.utcnow().isoformat(),
                "platform": self.platform_name,
                "metadata": {}
            }
        except Exception as e:
            return {
                "success": False,
                "message_id": None,
                "timestamp": datetime.utcnow().isoformat(),
                "platform": self.platform_name,
                "error": str(e)
            }

    async def receive_message(
        self,
        message_handler: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        self.callback = message_handler
        # Register with your platform to receive messages
```

### Using the Adapter

```python
import asyncio
from src.platforms.factory import PlatformFactory

async def handle_message(msg: Dict):
    """Callback for incoming messages."""
    print(f"Received from {msg['user_id']}: {msg['content']}")

async def main():
    # Create adapter
    adapter = PlatformFactory.create('telegram')

    # Register message handler
    await adapter.receive_message(handle_message)

    # Start adapter
    await adapter.start()

    # Send a message
    result = await adapter.send_message(
        recipient_id="123456789",
        content="Hello from Freeman!",
        metadata={"parse_mode": "Markdown"}
    )

    if result["success"]:
        print(f"Message sent: {result['message_id']}")
    else:
        print(f"Failed: {result['error']}")

    # Keep running...
    await asyncio.sleep(3600)

    # Cleanup
    await adapter.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### Converting Platform Messages to Standardized Format

When receiving messages from your platform, convert them to the standard format:

```python
def _convert_platform_message(self, platform_msg) -> Dict[str, Any]:
    """Convert platform-specific message to standardized format."""

    # Determine message type
    message_type = "text"  # Default
    if platform_msg.has_image:
        message_type = "image"
    elif platform_msg.has_video:
        message_type = "video"
    elif platform_msg.content.startswith('/'):
        message_type = "command"

    # Build standardized message
    return {
        "message_id": str(platform_msg.id),
        "user_id": str(platform_msg.sender_id),
        "content": platform_msg.text or "",
        "timestamp": platform_msg.created_at.isoformat(),
        "platform": self.platform_name,
        "message_type": message_type,
        "metadata": {
            "chat_id": str(platform_msg.chat_id),
            "username": platform_msg.sender.username,
            "display_name": platform_msg.sender.name,
            # Add any platform-specific fields
            "custom_field": platform_msg.custom_data
        }
    }
```

---

## Testing Your Adapter

### Unit Tests

Create tests in `tests/platforms/test_your_platform.py`:

```python
import pytest
from src.platforms.factory import PlatformFactory
from src.platforms.config import YourPlatformConfig

@pytest.fixture
def config():
    return {
        "api_key": "test_key",
        "api_secret": "test_secret"
    }

@pytest.fixture
def adapter(config):
    return PlatformFactory.create('yourplatform', config=config)

def test_platform_name(adapter):
    assert adapter.get_platform_name() == "yourplatform"

def test_config_validation():
    with pytest.raises(ValueError):
        PlatformFactory.create('yourplatform', config={})

@pytest.mark.asyncio
async def test_start_stop(adapter):
    await adapter.start()
    assert adapter.is_running is True

    await adapter.stop()
    assert adapter.is_running is False

@pytest.mark.asyncio
async def test_send_message(adapter):
    await adapter.start()

    result = await adapter.send_message(
        recipient_id="test_user",
        content="Test message"
    )

    assert result["success"] is True
    assert result["platform"] == "yourplatform"
    assert "message_id" in result

    await adapter.stop()
```

### Manual Testing

1. Create `.env` file with your platform credentials
2. Create a test script:

```python
# test_manual.py
import asyncio
from src.platforms.factory import PlatformFactory

async def test_adapter():
    adapter = PlatformFactory.create('yourplatform')

    async def on_message(msg):
        print(f"Received: {msg}")

    await adapter.receive_message(on_message)
    await adapter.start()

    print("Adapter is running. Send a test message to your platform...")
    await asyncio.sleep(60)

    await adapter.stop()

if __name__ == "__main__":
    asyncio.run(test_adapter())
```

3. Run: `python test_manual.py`

---

## Best Practices

1. **Error Handling**: Always catch platform-specific exceptions and convert to standard format
2. **Logging**: Use `self.log_info()`, `self.log_error()`, `self.log_debug()` for consistent logging
3. **Validation**: Validate all inputs in `validate_config()` before initialization
4. **Cleanup**: Ensure `stop()` properly cleans up all resources
5. **Async/Await**: Use async/await for all I/O operations
6. **Type Hints**: Add type hints to all methods for better IDE support
7. **Documentation**: Document platform-specific behavior and limitations

---

## Common Patterns

### Polling vs Webhooks

```python
class MyAdapter(BasePlatformAdapter):
    async def start(self) -> None:
        if self.config.get("webhook_url"):
            # Webhook mode
            await self._start_webhook()
        else:
            # Polling mode
            await self._start_polling()
```

### Rate Limiting

```python
from asyncio import Semaphore

class MyAdapter(BasePlatformAdapter):
    def __init__(self, config, platform_name=None):
        super().__init__(config, platform_name)
        rate_limit = self.config.get("rate_limit_per_minute", 30)
        self.semaphore = Semaphore(rate_limit)

    async def send_message(self, recipient_id, content, metadata=None):
        async with self.semaphore:
            # Send message with rate limiting
            pass
```

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class MyAdapter(BasePlatformAdapter):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def send_message(self, recipient_id, content, metadata=None):
        # Will retry up to 3 times with exponential backoff
        pass
```

---

## Troubleshooting

### Config Validation Errors

**Problem**: `ValueError: api_key is required`

**Solution**: Ensure environment variable is set in `.env` file or pass config explicitly:

```python
adapter = PlatformFactory.create('platform', config={'api_key': 'your_key'})
```

### Adapter Not Receiving Messages

**Problem**: Messages sent but callback never called

**Solution**:
1. Ensure `receive_message()` is called before `start()`
2. Verify platform-specific message handler is properly registered
3. Check logs for errors in message processing

### RuntimeError on send_message

**Problem**: `RuntimeError: Adapter not started`

**Solution**: Call `await adapter.start()` before sending messages

---

## Additional Resources

- See `adapters/telegram.py` for a complete real-world example
- See `adapters/discord.py` for webhook pattern implementation
- See `models.py` for all available data models
- See `base.py` for complete interface documentation

---

## Questions?

If you encounter issues or need help implementing a new platform adapter, please:

1. Check existing adapters for reference patterns
2. Review the base class documentation in `base.py`
3. Ensure all abstract methods are implemented
4. Test thoroughly before registering in the factory

Happy coding! 🚀
