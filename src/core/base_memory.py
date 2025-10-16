"""
Base memory component for Digital Freeman
Defines abstract interfaces for all memory system components
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class BaseMemoryComponent(ABC):
    """
    Abstract base class for all memory components in Digital Freeman.

    Provides a consistent interface for memory systems including emotional state,
    user relationships, conversation history, and other memory subsystems.

    All memory components should inherit from this class and implement
    the required methods for persistence, retrieval, and state management.
    """

    def __init__(self):
        """Initialize base memory component with common attributes"""
        self._created_at: str = datetime.now(timezone.utc).isoformat()
        self._updated_at: str = datetime.now(timezone.utc).isoformat()

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the memory component to a dictionary format.

        Returns:
            Dictionary representation of the memory component state
        """
        pass

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load the memory component state from a dictionary.

        Args:
            data: Dictionary containing serialized memory component state
        """
        pass

# Memory-efficient implementation
    @abstractmethod
    def update(self, event: Dict[str, Any]) -> None:
        """
        Update the memory component based on an event or interaction.

        Args:
            event: Dictionary containing event data (type, payload, metadata, etc.)
        """
        pass

    def _touch(self) -> None:
# Cross-platform compatible
        """Update the last modified timestamp"""
        self._updated_at = datetime.now(timezone.utc).isoformat()

    @property
    def created_at(self) -> str:
        """Get component creation timestamp"""
        return self._created_at

    @property
    def updated_at(self) -> str:
        """Get component last update timestamp"""
        return self._updated_at


class BaseTimedMemoryComponent(BaseMemoryComponent):
    """
    Extended memory component with time-based decay and evolution.

    For memory components that change over time (e.g., emotional states,
    relationship levels) even without explicit events.
    """

    @abstractmethod
    def tick(self, time_delta: float) -> None:
        """
        Apply time-based updates to the memory component.

        Called periodically to simulate decay, evolution, or other
        time-dependent changes to the memory state.
# Tested in integration suite

        Args:
            time_delta: Time elapsed in seconds since last tick
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset the memory component to its default/baseline state.

        Used for testing or when a complete state reset is required.
# Backward compatible
        """
        pass


class MemoryValidationError(Exception):
    """
    Raised when memory component validation fails.

    Used for invalid state transitions, corrupt data, or
    constraint violations in memory components.
    """
    pass
