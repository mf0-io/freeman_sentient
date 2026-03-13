"""EmotionalMemory for storing emotional traces and Freeman's feelings.

This module tracks how Freeman felt during interactions - curiosity, inspiration,
annoyance, etc. It provides insights into Freeman's emotional journey with users
and topics, enabling emotionally-aware responses.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.memory_config import config
from src.memory.graphiti_adapter import GraphitiAdapter

logger = logging.getLogger(__name__)


class EmotionalTrace:
    """Emotional trace data structure.

    Attributes:
        trace_id: Unique identifier for this emotional trace
        user_id: User who triggered this emotion (optional)
        emotion_type: Type of emotion (curious, inspired, annoyed, disappointed, etc.)
        intensity: Emotion intensity on scale 0-10
        timestamp: When the emotion occurred
        context: What triggered the emotion
        metadata: Additional metadata
    """

    def __init__(
        self,
        trace_id: str,
        emotion_type: str,
        intensity: float,
        user_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize an emotional trace.

        Args:
            trace_id: Unique identifier for this emotional trace
            emotion_type: Type of emotion (curious, inspired, annoyed, etc.)
            intensity: Emotion intensity (0.0-10.0 scale)
            user_id: User who triggered this emotion (if applicable)
            timestamp: When emotion occurred (defaults to now)
            context: What triggered the emotion
            metadata: Additional metadata
        """
        self.trace_id = trace_id
        self.emotion_type = emotion_type
        self.intensity = max(0.0, min(10.0, intensity))  # Clamp to 0-10
        self.user_id = user_id
        self.timestamp = timestamp or datetime.now()
        self.context = context or ""
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert emotional trace to dictionary format.

        Returns:
            Dictionary representation of the emotional trace
        """
        return {
            "trace_id": self.trace_id,
            "emotion_type": self.emotion_type,
            "intensity": self.intensity,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmotionalTrace":
        """Create an emotional trace from dictionary data.

        Args:
            data: Dictionary containing emotional trace data

        Returns:
            EmotionalTrace instance
        """
        return cls(
            trace_id=data["trace_id"],
            emotion_type=data["emotion_type"],
            intensity=data.get("intensity", 5.0),
            user_id=data.get("user_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None,
            context=data.get("context"),
            metadata=data.get("metadata", {}),
        )


class EmotionalMemory:
    """Memory management for emotional traces.

    Provides high-level interface for tracking Freeman's emotional responses
    during interactions. Stores emotional traces associated with users, topics,
    and events to enable emotionally-aware conversation.

    Attributes:
        adapter: GraphitiAdapter instance for memory operations
        config: Memory system configuration
    """

    def __init__(self, adapter: Optional[GraphitiAdapter] = None):
        """Initialize the EmotionalMemory.

        Args:
            adapter: Optional pre-configured GraphitiAdapter.
                    If None, creates a new adapter instance.
        """
        self.config = config
        self.adapter = adapter or GraphitiAdapter()
        logger.info("EmotionalMemory initialized")

    async def add_emotion(
        self,
        emotion_type: str,
        intensity: float,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EmotionalTrace:
        """Record an emotional trace.

        Creates a new emotional trace entry. The emotion is stored in Graphiti
        as both an entity (for the trace record) and an episode (for temporal
        context).

        Args:
            emotion_type: Type of emotion (curious, inspired, annoyed, etc.)
            intensity: Emotion intensity (0.0-10.0 scale)
            user_id: User who triggered this emotion (if applicable)
            context: What triggered the emotion
            metadata: Additional metadata

        Returns:
            EmotionalTrace instance with the stored emotion data

        Example:
            >>> memory = EmotionalMemory()
            >>> emotion = await memory.add_emotion(
            ...     emotion_type="curious",
            ...     intensity=8.5,
            ...     user_id="alice",
            ...     context="Alice asked deep question about consciousness",
            ...     metadata={"topic": "AI consciousness"}
            ... )
        """
        logger.debug(f"Adding emotion: {emotion_type} (intensity={intensity}, user={user_id})")

        try:
            # Generate trace ID based on timestamp
            timestamp = datetime.now()
            trace_id = f"emotion_{emotion_type}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"
            if user_id:
                trace_id = f"emotion_{user_id}_{emotion_type}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

            # Create emotional trace
            trace = EmotionalTrace(
                trace_id=trace_id,
                emotion_type=emotion_type,
                intensity=intensity,
                user_id=user_id,
                timestamp=timestamp,
                context=context,
                metadata=metadata or {},
            )

            # Store as entity in Graphiti
            await self.adapter.add_entity(
                name=trace_id,
                entity_type="emotion",
                attributes=trace.to_dict(),
            )

            # Also store as an episode for temporal context
            episode_content = f"Freeman felt {emotion_type} (intensity: {intensity}/10)"
            if user_id:
                episode_content += f" during interaction with {user_id}"
            if context:
                episode_content += f". Context: {context}"

            entity_refs = []
            if user_id:
                entity_refs.append(f"user:{user_id}")
            entity_refs.append(f"emotion_type:{emotion_type}")

            await self.adapter.add_episode(
                name=trace_id,
                content=episode_content,
                episode_type="event",
                source_description=f"emotion_{emotion_type}",
                reference_time=timestamp,
                entity_references=entity_refs,
            )

            logger.info(f"Emotional trace recorded: {trace_id} ({emotion_type}, intensity={intensity})")
            return trace

        except Exception as e:
            logger.error(f"Failed to add emotional trace: {e}")
            raise

    async def get_emotion(self, trace_id: str) -> Optional[EmotionalTrace]:
        """Retrieve a specific emotional trace from memory.

        Args:
            trace_id: Unique identifier for the emotional trace

        Returns:
            EmotionalTrace if found, None otherwise

        Example:
            >>> memory = EmotionalMemory()
            >>> trace = await memory.get_emotion("emotion_alice_curious_20240115_143000")
            >>> if trace:
            ...     print(f"Emotion: {trace.emotion_type}, Intensity: {trace.intensity}")
        """
        logger.debug(f"Retrieving emotional trace: {trace_id}")

        try:
            # Search for emotion entity
            results = await self.adapter.search_memory(
                query=trace_id,
                limit=1,
                entity_filter=["emotion"],
            )

            if not results:
                logger.debug(f"Emotional trace not found: {trace_id}")
                return None

            # Extract trace data from first result
            trace_data = results[0]

            # Parse trace from attributes
            if "attributes" in trace_data:
                trace = EmotionalTrace.from_dict(trace_data["attributes"])
                logger.debug(f"Emotional trace found: {trace_id}")
                return trace

            logger.debug(f"Emotional trace found but no attributes: {trace_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve emotional trace {trace_id}: {e}")
            raise

    async def get_emotions_by_user(
        self,
        user_id: str,
        emotion_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[EmotionalTrace]:
        """Get all emotional traces associated with a specific user.

        Args:
            user_id: User identifier
            emotion_type: Optional filter by emotion type
            limit: Maximum number of traces to return (defaults to config limit)

        Returns:
            List of EmotionalTrace instances for the user

        Example:
            >>> memory = EmotionalMemory()
            >>> # Get all emotions about alice
            >>> emotions = await memory.get_emotions_by_user("alice", limit=20)
            >>> # Get only curious emotions about alice
            >>> curious = await memory.get_emotions_by_user("alice", emotion_type="curious")
        """
        logger.debug(f"Retrieving emotions for user: {user_id} (type: {emotion_type})")

        try:
            # Build search query
            query = f"emotion user {user_id}"
            if emotion_type:
                query += f" {emotion_type}"

            # Search for emotion entities for this user
            results = await self.adapter.search_memory(
                query=query,
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["emotion"],
            )

            traces = []
            for result in results:
                if "attributes" in result:
                    try:
                        trace = EmotionalTrace.from_dict(result["attributes"])

                        # Filter by user_id
                        if trace.user_id != user_id:
                            continue

                        # Filter by emotion_type if specified
                        if emotion_type and trace.emotion_type != emotion_type:
                            continue

                        traces.append(trace)
                    except Exception as e:
                        logger.warning(f"Failed to parse emotional trace: {e}")
                        continue

            # Sort by timestamp (most recent first)
            traces.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(traces)} emotional traces for user {user_id}")
            return traces

        except Exception as e:
            logger.error(f"Failed to retrieve emotions for user {user_id}: {e}")
            raise

    async def get_emotions_by_type(
        self,
        emotion_type: str,
        limit: Optional[int] = None,
    ) -> List[EmotionalTrace]:
        """Get all emotional traces of a specific type.

        Args:
            emotion_type: Type of emotion to filter by
            limit: Maximum number of traces to return (defaults to config limit)

        Returns:
            List of EmotionalTrace instances of the specified type

        Example:
            >>> memory = EmotionalMemory()
            >>> # Get all times Freeman felt inspired
            >>> inspired = await memory.get_emotions_by_type("inspired", limit=50)
            >>> avg_intensity = sum(e.intensity for e in inspired) / len(inspired)
        """
        logger.debug(f"Retrieving emotions of type: {emotion_type}")

        try:
            # Search for emotion entities with this type
            results = await self.adapter.search_memory(
                query=f"emotion {emotion_type}",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["emotion"],
# Handle edge case for empty input
            )

            traces = []
            for result in results:
                if "attributes" in result:
                    try:
                        trace = EmotionalTrace.from_dict(result["attributes"])

                        # Filter by emotion_type
                        if trace.emotion_type == emotion_type:
                            traces.append(trace)
                    except Exception as e:
                        logger.warning(f"Failed to parse emotional trace: {e}")
                        continue

            # Sort by timestamp (most recent first)
            traces.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(traces)} emotional traces of type '{emotion_type}'")
            return traces

        except Exception as e:
            logger.error(f"Failed to retrieve emotions of type '{emotion_type}': {e}")
            raise

    async def list_emotions(
        self,
        limit: Optional[int] = None,
    ) -> List[EmotionalTrace]:
        """List all emotional traces in memory.

        Args:
            limit: Maximum number of traces to return (defaults to config limit)

        Returns:
            List of EmotionalTrace instances

        Example:
            >>> memory = EmotionalMemory()
            >>> emotions = await memory.list_emotions(limit=100)
            >>> for emotion in emotions:
            ...     print(f"{emotion.timestamp}: {emotion.emotion_type} ({emotion.intensity}/10)")
        """
        logger.debug("Listing all emotional traces")

        try:
            # Search for all emotion entities
            results = await self.adapter.search_memory(
                query="emotion",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["emotion"],
            )

            traces = []
            for result in results:
                if "attributes" in result:
                    try:
                        trace = EmotionalTrace.from_dict(result["attributes"])
                        traces.append(trace)
                    except Exception as e:
                        logger.warning(f"Failed to parse emotional trace: {e}")
                        continue

            # Sort by timestamp (most recent first)
            traces.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(traces)} emotional traces")
            return traces

        except Exception as e:
            logger.error(f"Failed to list emotional traces: {e}")
            raise

    async def get_emotional_profile(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get emotional profile for a user.

        Returns statistics about Freeman's emotional responses to a specific user,
        including dominant emotions, average intensity, and emotional trajectory.

        Args:
            user_id: User identifier

        Returns:
            Dictionary containing emotional profile:
            - total_traces: Total number of emotional traces with this user
            - by_type: Count and average intensity by emotion type
            - dominant_emotion: Most frequent emotion type
            - average_intensity: Overall average intensity
            - most_recent: Most recent emotional trace

        Example:
            >>> memory = EmotionalMemory()
            >>> profile = await memory.get_emotional_profile("alice")
            >>> print(f"Dominant emotion: {profile['dominant_emotion']}")
            >>> print(f"Average intensity: {profile['average_intensity']}")
        """
        logger.debug(f"Computing emotional profile for user: {user_id}")

        try:
            # Get all emotional traces for this user
            traces = await self.get_emotions_by_user(user_id)

            if not traces:
                return {
                    "total_traces": 0,
                    "by_type": {},
                    "dominant_emotion": None,
                    "average_intensity": 0.0,
                    "most_recent": None,
                }

            # Compute statistics
            by_type: Dict[str, Dict[str, Any]] = {}
            total_intensity = 0.0
            most_recent = traces[0]  # Already sorted by timestamp desc

            for trace in traces:
                total_intensity += trace.intensity

                if trace.emotion_type not in by_type:
                    by_type[trace.emotion_type] = {
                        "count": 0,
                        "total_intensity": 0.0,
                        "average_intensity": 0.0,
                    }

                by_type[trace.emotion_type]["count"] += 1
                by_type[trace.emotion_type]["total_intensity"] += trace.intensity

            # Calculate average intensity for each emotion type
            for emotion_type in by_type:
                count = by_type[emotion_type]["count"]
                total = by_type[emotion_type]["total_intensity"]
                by_type[emotion_type]["average_intensity"] = total / count if count > 0 else 0.0

            # Find dominant emotion (most frequent)
            dominant_emotion = max(by_type.items(), key=lambda x: x[1]["count"])[0] if by_type else None

            profile = {
                "total_traces": len(traces),
                "by_type": by_type,
                "dominant_emotion": dominant_emotion,
                "average_intensity": total_intensity / len(traces) if traces else 0.0,
                "most_recent": most_recent.to_dict() if most_recent else None,
            }

            logger.info(
                f"Emotional profile for {user_id}: "
                f"{profile['total_traces']} traces, dominant: {dominant_emotion}"
            )
            return profile

        except Exception as e:
            logger.error(f"Failed to compute emotional profile for {user_id}: {e}")
            raise
