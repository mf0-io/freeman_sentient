"""
Emotional state management for Digital Freeman
Manages mood state over time and provides response modifiers for agents
"""

from typing import Dict, Any, List, Optional
from collections import deque
from .mood import MoodState
from ..core.base_memory import BaseMemoryComponent


class EmotionalStateManager(BaseMemoryComponent):
    """
    Manages Freeman's emotional state over time across interactions.

    Responsibilities:
    - Maintain current mood state
    - Track mood history for analysis and persistence
    - Process interaction events and update mood accordingly
    - Apply time-based mood decay
    - Provide mood-influenced response parameters for agents

    The manager translates high-level interaction events (user actions, sentiment)
    into specific mood dimension changes that the underlying MoodState handles.
    """

    # Mood history configuration
    MAX_HISTORY_SIZE = 100  # Keep last N mood snapshots

    # Interaction type to mood impact mappings
    INTERACTION_IMPACTS = {
        "positive_interaction": {
            "valence_delta": 0.10,
            "enthusiasm_delta": 0.08,
            "irritability_delta": -0.05,
        },
        "negative_interaction": {
            "valence_delta": -0.12,
            "irritability_delta": 0.10,
            "enthusiasm_delta": -0.05,
        },
        "engaging_topic": {
            "energy_delta": 0.12,
            "enthusiasm_delta": 0.10,
            "valence_delta": 0.05,
        },
        "boring_interaction": {
            "energy_delta": -0.10,
            "enthusiasm_delta": -0.08,
            "irritability_delta": 0.03,
        },
    }

    def __init__(self, initial_mood: Optional[MoodState] = None):
        """
        Initialize emotional state manager.

        Args:
            initial_mood: Optional initial MoodState. If None, uses default baseline mood.
        """
        super().__init__()
        self._current_mood = initial_mood if initial_mood is not None else MoodState()
        self._mood_history: deque = deque(maxlen=self.MAX_HISTORY_SIZE)

        # Store initial mood in history
        self._snapshot_mood()

    def get_current_mood(self) -> MoodState:
        """
        Get the current mood state.

        Returns:
            Current MoodState object
        """
        return self._current_mood

    def process_interaction(
        self,
        interaction_type: str,
        sentiment: Optional[float] = None,
        custom_impact: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Process an interaction event and update mood accordingly.

        Args:
            interaction_type: Type of interaction (positive_interaction, negative_interaction,
                            engaging_topic, boring_interaction)
            sentiment: Optional sentiment score (-1.0 to 1.0) to modulate impact
            custom_impact: Optional custom mood deltas to override default impacts

        The sentiment parameter can be used to fine-tune the mood impact based on
        sentiment analysis of the user's message.
        """
        # Determine mood impact
        if custom_impact is not None:
            impact = custom_impact
        elif interaction_type in self.INTERACTION_IMPACTS:
            impact = self.INTERACTION_IMPACTS[interaction_type].copy()
        else:
            # Unknown interaction type - use neutral impact
            impact = {}

        # Modulate impact by sentiment if provided
        if sentiment is not None and impact:
            # Sentiment range: -1.0 (very negative) to 1.0 (very positive)
            # Scale all deltas by sentiment strength
            sentiment_multiplier = 0.5 + (sentiment * 0.5)  # Maps to 0.0-1.0
            impact = {k: v * sentiment_multiplier for k, v in impact.items()}

        # Create event and update mood
        event = {"type": interaction_type, **impact}
        self._current_mood.update(event)

        # Snapshot mood after significant change
        self._snapshot_mood()

        self._touch()

    def tick(self, time_delta: float) -> None:
        """
        Apply time-based mood decay.

        Delegates to the underlying MoodState's tick method for natural
        decay toward baseline over time.

        Args:
            time_delta: Time elapsed in seconds since last tick
        """
        self._current_mood.tick(time_delta)
        self._touch()

    def get_response_modifiers(self) -> Dict[str, Any]:
        """
        Get mood-based response modifiers for agent decision-making.

        Returns:
            Dictionary containing response parameters influenced by current mood:
            - verbosity: float (0.0-1.0) - Based on energy level
            - tone: float (-1.0 to 1.0) - Based on emotional valence
            - patience: float (0.0-1.0) - Inverse of irritability
            - engagement: float (0.0-1.0) - Based on enthusiasm
            - suggested_style: str - Suggested response style based on mood
        """
        mood = self._current_mood

        # Calculate modifiers from mood dimensions
        verbosity = mood.energy_level  # Low energy = shorter responses
        tone = mood.emotional_valence  # Negative = sarcastic/critical, positive = supportive
        patience = 1.0 - mood.irritability  # High irritability = less patient
        engagement = mood.enthusiasm  # High enthusiasm = more detailed, excited

        # Determine suggested style based on mood combination
        suggested_style = self._determine_style(mood)

        return {
            "verbosity": verbosity,
            "tone": tone,
            "patience": patience,
            "engagement": engagement,
            "suggested_style": suggested_style,
            "raw_mood": {
                "energy_level": mood.energy_level,
                "emotional_valence": mood.emotional_valence,
                "irritability": mood.irritability,
                "enthusiasm": mood.enthusiasm,
            }
        }

    def _determine_style(self, mood: MoodState) -> str:
        """
        Determine suggested response style based on current mood.

        Args:
            mood: Current MoodState

        Returns:
            Suggested style string: philosophical, sarcastic, supportive, or confrontational
        """
        # High energy + high enthusiasm + positive valence = philosophical/engaging
        if mood.energy_level > 0.6 and mood.enthusiasm > 0.6 and mood.emotional_valence > 0.2:
            return "philosophical"

        # Negative valence + high irritability = sarcastic/confrontational
        if mood.emotional_valence < -0.2 and mood.irritability > 0.5:
            return "confrontational"

        # Negative valence but low irritability = sarcastic
        if mood.emotional_valence < -0.1 and mood.irritability < 0.4:
            return "sarcastic"

        # Positive valence + moderate energy = supportive
        if mood.emotional_valence > 0.2 and mood.energy_level > 0.4:
            return "supportive"

        # Default to philosophical (Freeman's core style)
        return "philosophical"

    def _snapshot_mood(self) -> None:
        """Take a snapshot of current mood and add to history"""
        snapshot = self._current_mood.to_dict()
        self._mood_history.append(snapshot)

    def get_mood_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get mood history snapshots.

        Args:
            limit: Optional limit on number of historical snapshots to return

        Returns:
            List of mood state dictionaries, most recent first
        """
        history = list(self._mood_history)
        history.reverse()  # Most recent first

        if limit is not None:
            history = history[:limit]

        return history

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize emotional state manager to dictionary.

        Returns:
            Dictionary representation including current mood and history
        """
        return {
            "current_mood": self._current_mood.to_dict(),
            "mood_history": list(self._mood_history),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """
        Load emotional state manager from dictionary.

        Args:
            data: Dictionary containing serialized state
        """
        # Restore current mood
        if "current_mood" in data:
            self._current_mood = MoodState()
            self._current_mood.from_dict(data["current_mood"])

        # Restore mood history
        if "mood_history" in data:
            self._mood_history = deque(data["mood_history"], maxlen=self.MAX_HISTORY_SIZE)

        # Restore timestamps
        if "created_at" in data:
            self._created_at = data["created_at"]
        if "updated_at" in data:
            self._updated_at = data["updated_at"]

    def update(self, event: Dict[str, Any]) -> None:
        """
        Update emotional state based on a generic event.

        This method provides compatibility with the BaseMemoryComponent interface.
        For most use cases, prefer using process_interaction() which provides
        a higher-level interface.

        Args:
            event: Event dictionary containing:
                - type: Event type (interaction_type)
                - sentiment: Optional sentiment score
                - custom_impact: Optional custom mood deltas
        """
        interaction_type = event.get("type", "unknown")
        sentiment = event.get("sentiment")
        custom_impact = event.get("custom_impact")

        self.process_interaction(interaction_type, sentiment, custom_impact)

    def reset(self) -> None:
        """
        Reset emotional state to baseline.

        Resets current mood to default values and clears history.
        """
        self._current_mood.reset()
        self._mood_history.clear()
        self._snapshot_mood()
        self._touch()

    def __repr__(self) -> str:
        """String representation of emotional state manager"""
        return f"EmotionalStateManager(current_mood={self._current_mood})"
