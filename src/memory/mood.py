"""
Mood state management for Digital Freeman
Tracks emotional dimensions that influence response generation
"""

from typing import Dict, Any
from ..core.base_memory import BaseTimedMemoryComponent, MemoryValidationError


class MoodState(BaseTimedMemoryComponent):
    """
    Represents Freeman's current mood state across multiple emotional dimensions.

    Mood dimensions:
    - energy_level (0.0-1.0): Affects verbosity and engagement level
    - emotional_valence (-1.0 to 1.0): Negative to positive emotional tone
    - irritability (0.0-1.0): Affects patience and tolerance
    - enthusiasm (0.0-1.0): Affects excitement and detail in responses

    The mood state evolves based on:
    1. Events (interactions, user actions)
    2. Time-based decay toward baseline
    3. Smooth transitions to avoid sudden mood swings
    """

    # Default baseline mood (neutral, moderate energy)
    DEFAULT_ENERGY = 0.6
    DEFAULT_VALENCE = 0.0
    DEFAULT_IRRITABILITY = 0.2
    DEFAULT_ENTHUSIASM = 0.5

    # Transition constraints
    MAX_CHANGE_PER_EVENT = 0.15  # Maximum mood change from single event
    DECAY_RATE = 0.05  # Rate of return to baseline per hour

    def __init__(
        self,
        energy_level: float = None,
        emotional_valence: float = None,
        irritability: float = None,
        enthusiasm: float = None
    ):
        """
        Initialize mood state with specified or default values.

        Args:
            energy_level: Energy level (0.0-1.0), defaults to baseline
            emotional_valence: Emotional tone (-1.0 to 1.0), defaults to baseline
            irritability: Irritability level (0.0-1.0), defaults to baseline
            enthusiasm: Enthusiasm level (0.0-1.0), defaults to baseline
        """
        super().__init__()

        self._energy_level = energy_level if energy_level is not None else self.DEFAULT_ENERGY
        self._emotional_valence = emotional_valence if emotional_valence is not None else self.DEFAULT_VALENCE
        self._irritability = irritability if irritability is not None else self.DEFAULT_IRRITABILITY
        self._enthusiasm = enthusiasm if enthusiasm is not None else self.DEFAULT_ENTHUSIASM

        self._validate_state()

    def _validate_state(self) -> None:
        """Validate that all mood dimensions are within valid ranges"""
        if not (0.0 <= self._energy_level <= 1.0):
            raise MemoryValidationError(f"energy_level must be 0.0-1.0, got {self._energy_level}")

        if not (-1.0 <= self._emotional_valence <= 1.0):
            raise MemoryValidationError(f"emotional_valence must be -1.0 to 1.0, got {self._emotional_valence}")

        if not (0.0 <= self._irritability <= 1.0):
            raise MemoryValidationError(f"irritability must be 0.0-1.0, got {self._irritability}")

        if not (0.0 <= self._enthusiasm <= 1.0):
            raise MemoryValidationError(f"enthusiasm must be 0.0-1.0, got {self._enthusiasm}")

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        """Clamp a value to the specified range"""
        return max(min_val, min(max_val, value))

    def _smooth_transition(self, current: float, target: float, max_change: float) -> float:
        """
        Apply smooth transition with maximum change constraint.

        Args:
            current: Current value
            target: Target value
            max_change: Maximum allowed change

        Returns:
            New value after smooth transition
        """
        delta = target - current

        # Limit the change magnitude
        if abs(delta) > max_change:
            delta = max_change if delta > 0 else -max_change

        return current + delta

    def update(self, event: Dict[str, Any]) -> None:
        """
        Update mood state based on an event.

        Expected event structure:
        {
            "type": "interaction" | "topic_engagement" | "user_action",
            "energy_delta": float,      # Optional: -0.15 to 0.15
            "valence_delta": float,     # Optional: -0.15 to 0.15
            "irritability_delta": float, # Optional: -0.15 to 0.15
            "enthusiasm_delta": float   # Optional: -0.15 to 0.15
        }

        Args:
            event: Dictionary containing mood change deltas
        """
        # Apply changes with smooth transitions and constraints
        if "energy_delta" in event:
            delta = self._clamp(event["energy_delta"], -self.MAX_CHANGE_PER_EVENT, self.MAX_CHANGE_PER_EVENT)
            self._energy_level = self._clamp(self._energy_level + delta, 0.0, 1.0)

        if "valence_delta" in event:
            delta = self._clamp(event["valence_delta"], -self.MAX_CHANGE_PER_EVENT, self.MAX_CHANGE_PER_EVENT)
            self._emotional_valence = self._clamp(self._emotional_valence + delta, -1.0, 1.0)

        if "irritability_delta" in event:
            delta = self._clamp(event["irritability_delta"], -self.MAX_CHANGE_PER_EVENT, self.MAX_CHANGE_PER_EVENT)
            self._irritability = self._clamp(self._irritability + delta, 0.0, 1.0)

        if "enthusiasm_delta" in event:
            delta = self._clamp(event["enthusiasm_delta"], -self.MAX_CHANGE_PER_EVENT, self.MAX_CHANGE_PER_EVENT)
            self._enthusiasm = self._clamp(self._enthusiasm + delta, 0.0, 1.0)

        self._touch()
        self._validate_state()

    def tick(self, time_delta: float) -> None:
        """
        Apply time-based mood decay toward baseline.

        Mood naturally returns to baseline over time if no events occur.
        Decay rate is exponential to create smooth, natural transitions.

        Args:
            time_delta: Time elapsed in seconds since last tick
        """
        # Convert time_delta to hours for decay calculation
        hours = time_delta / 3600.0
        decay_factor = self.DECAY_RATE * hours

        # Apply decay toward baseline for each dimension
        self._energy_level += (self.DEFAULT_ENERGY - self._energy_level) * decay_factor
        self._emotional_valence += (self.DEFAULT_VALENCE - self._emotional_valence) * decay_factor
        self._irritability += (self.DEFAULT_IRRITABILITY - self._irritability) * decay_factor
        self._enthusiasm += (self.DEFAULT_ENTHUSIASM - self._enthusiasm) * decay_factor

        # Ensure values stay within valid ranges (should be guaranteed by decay logic, but safety check)
        self._energy_level = self._clamp(self._energy_level, 0.0, 1.0)
        self._emotional_valence = self._clamp(self._emotional_valence, -1.0, 1.0)
        self._irritability = self._clamp(self._irritability, 0.0, 1.0)
        self._enthusiasm = self._clamp(self._enthusiasm, 0.0, 1.0)

        self._touch()

    def reset(self) -> None:
        """Reset mood state to baseline (default) values"""
        self._energy_level = self.DEFAULT_ENERGY
        self._emotional_valence = self.DEFAULT_VALENCE
        self._irritability = self.DEFAULT_IRRITABILITY
        self._enthusiasm = self.DEFAULT_ENTHUSIASM
        self._touch()

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize mood state to dictionary.

        Returns:
            Dictionary representation of mood state
        """
        return {
            "energy_level": self._energy_level,
            "emotional_valence": self._emotional_valence,
            "irritability": self._irritability,
            "enthusiasm": self._enthusiasm,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load mood state from dictionary.

        Args:
            data: Dictionary containing serialized mood state
        """
        self._energy_level = data.get("energy_level", self.DEFAULT_ENERGY)
        self._emotional_valence = data.get("emotional_valence", self.DEFAULT_VALENCE)
        self._irritability = data.get("irritability", self.DEFAULT_IRRITABILITY)
        self._enthusiasm = data.get("enthusiasm", self.DEFAULT_ENTHUSIASM)

        if "created_at" in data:
            self._created_at = data["created_at"]
        if "updated_at" in data:
            self._updated_at = data["updated_at"]

        self._validate_state()

    # Properties for read access to mood dimensions

    @property
    def energy_level(self) -> float:
        """Current energy level (0.0-1.0)"""
        return self._energy_level

    @property
    def emotional_valence(self) -> float:
        """Current emotional valence (-1.0 to 1.0)"""
        return self._emotional_valence

    @property
    def irritability(self) -> float:
        """Current irritability level (0.0-1.0)"""
        return self._irritability

    @property
    def enthusiasm(self) -> float:
        """Current enthusiasm level (0.0-1.0)"""
        return self._enthusiasm

    def __repr__(self) -> str:
        """String representation of mood state"""
        return (
            f"MoodState(energy={self._energy_level:.2f}, "
            f"valence={self._emotional_valence:.2f}, "
            f"irritability={self._irritability:.2f}, "
            f"enthusiasm={self._enthusiasm:.2f})"
        )
