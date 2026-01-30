"""
Platform data models for Freeman multi-platform support.

This module provides Pydantic models for platform messages, users, and
configurations. These models ensure type safety and data validation across
all platform adapters.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator


class MessageType(str, Enum):
    """
    Enumeration of supported message types across platforms.

    Attributes:
        TEXT: Plain text message
        IMAGE: Image message (with optional caption)
        VIDEO: Video message (with optional caption)
        AUDIO: Audio message (voice note or audio file)
        FILE: Generic file attachment
        STICKER: Sticker or emoji reaction
        LOCATION: Location/geolocation data
        CONTACT: Contact card
        POLL: Poll or survey
        COMMAND: Bot command (e.g., /start, /help)
    """
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACT = "contact"
    POLL = "poll"
    COMMAND = "command"


class PlatformMessage(BaseModel):
    """
    Standardized message model for all platforms.

    This model represents a message received from or sent to any platform,
    providing a unified interface for message handling regardless of the
    underlying platform-specific implementation.

    Attributes:
        platform: Platform identifier (e.g., "telegram", "discord")
        message_id: Platform-specific unique message identifier
        user_id: Platform-specific user identifier who sent the message
        content: Message text content
        message_type: Type of message (text, image, etc.)
        timestamp: When the message was created/received
        reply_to_id: Optional ID of message being replied to
        metadata: Additional platform-specific data (media URLs, etc.)
        is_bot: Whether the sender is a bot
        chat_id: Optional chat/channel/group identifier
    """

    platform: str = Field(
        ...,
        description="Platform identifier (e.g., 'telegram', 'discord')"
    )
    message_id: Optional[str] = Field(
        default=None,
        description="Platform-specific unique message identifier"
    )
    user_id: str = Field(
        ...,
        description="Platform-specific user identifier"
    )
    content: str = Field(
        ...,
        description="Message text content"
    )
    message_type: MessageType = Field(
        default=MessageType.TEXT,
        description="Type of message (text, image, video, etc.)"
    )
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.utcnow,
        description="When the message was created/received"
    )
    reply_to_id: Optional[str] = Field(
        default=None,
        description="ID of message being replied to"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional platform-specific data (media URLs, file info, etc.)"
    )
    is_bot: bool = Field(
        default=False,
        description="Whether the sender is a bot"
    )
    chat_id: Optional[str] = Field(
        default=None,
        description="Chat/channel/group identifier where message was sent"
    )

    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('content')
    def content_not_empty(cls, v):
        """Validate that content is not empty for text messages."""
        if v is not None and isinstance(v, str) and not v.strip():
            raise ValueError("Content cannot be empty")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert message to dictionary format.

        Returns:
            Dictionary representation of the message
        """
        return self.dict()

    def is_command(self) -> bool:
        """
        Check if message is a bot command.

        Returns:
            True if message type is COMMAND or content starts with '/'
        """
        return (
            self.message_type == MessageType.COMMAND or
            (self.content and self.content.strip().startswith('/'))
        )


class PlatformUser(BaseModel):
    """
    Standardized user model for all platforms.

    Represents a user across different platforms with normalized fields.
    Platform-specific data should be stored in the metadata field.

    Attributes:
        platform: Platform identifier (e.g., "telegram", "discord")
        user_id: Platform-specific unique user identifier
        username: User's username/handle (if available)
        display_name: User's display name or full name
        is_bot: Whether this user is a bot
        language_code: User's preferred language code (ISO 639-1)
        metadata: Additional platform-specific user data
    """

    platform: str = Field(
        ...,
        description="Platform identifier (e.g., 'telegram', 'discord')"
    )
    user_id: str = Field(
        ...,
        description="Platform-specific unique user identifier"
    )
    username: Optional[str] = Field(
        default=None,
        description="User's username/handle"
    )
    display_name: Optional[str] = Field(
        default=None,
        description="User's display name or full name"
    )
    is_bot: bool = Field(
        default=False,
        description="Whether this user is a bot"
    )
    language_code: Optional[str] = Field(
        default=None,
        description="User's preferred language code (ISO 639-1)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional platform-specific user data"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

    def get_identifier(self) -> str:
        """
        Get the best available identifier for this user.

        Returns:
            Username if available, otherwise display_name, otherwise user_id
        """
        return self.username or self.display_name or self.user_id

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user to dictionary format.

        Returns:
            Dictionary representation of the user
        """
        return self.dict()


class PlatformConfig(BaseModel):
    """
    Base configuration model for platform adapters.

    This is the base class that platform-specific configurations should inherit from.
    Each platform adapter should create its own config model extending this base.

    Attributes:
        platform_name: Unique identifier for the platform
        enabled: Whether this platform adapter is enabled
        max_retries: Maximum number of retry attempts for failed operations
        timeout_seconds: Timeout for platform API calls in seconds
        rate_limit_per_minute: Maximum requests per minute (0 = unlimited)
    """

    platform_name: str = Field(
        ...,
        description="Unique identifier for the platform"
    )
    enabled: bool = Field(
        default=True,
        description="Whether this platform adapter is enabled"
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts for failed operations"
    )
    timeout_seconds: int = Field(
        default=30,
        description="Timeout for platform API calls in seconds"
    )
    rate_limit_per_minute: int = Field(
        default=30,
        description="Maximum requests per minute (0 = unlimited)"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        validate_assignment = True

    def validate_required_fields(self, *fields: str) -> None:
        """
        Validate that required configuration fields are set.

        Args:
            *fields: Field names to validate

        Raises:
            ValueError: If any required field is not set or is empty
        """
        missing_fields = []
        for field in fields:
            value = getattr(self, field, None)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_fields.append(field)

        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields for {self.platform_name}: "
                f"{', '.join(missing_fields)}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert config to dictionary format.

        Returns:
            Dictionary representation of the config
        """
        return self.dict()


class MessageResponse(BaseModel):
    """
    Response model for sent messages.

    Returned by platform adapters when sending messages to indicate
    success/failure and provide metadata about the sent message.

    Attributes:
        success: Whether the message was sent successfully
        message_id: Platform-specific message identifier (if successful)
        timestamp: When the message was sent
        platform: Platform identifier
        error: Error message if sending failed
        metadata: Additional response metadata from the platform
    """

    success: bool = Field(
        ...,
        description="Whether the message was sent successfully"
    )
    message_id: Optional[str] = Field(
        default=None,
        description="Platform-specific message identifier"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the message was sent"
    )
    platform: str = Field(
        ...,
        description="Platform identifier"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if sending failed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional response metadata from the platform"
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert response to dictionary format.

        Returns:
            Dictionary representation of the response
        """
        return self.dict()
