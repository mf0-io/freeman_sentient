"""MemoryManager for orchestrating all memory components with unified interface.

This module provides a high-level unified interface for managing all memory types:
user profiles, relationships, conversations, actions, and emotional traces.
It coordinates between memory components and provides comprehensive context retrieval.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.memory_config import config
from src.memory.action_memory import ActionMemory
from src.memory.conversation_memory import ConversationMemory
from src.memory.emotional_memory import EmotionalMemory
from src.memory.graphiti_adapter import GraphitiAdapter
from src.memory.relationship_memory import RelationshipMemory
from src.memory.temporal_people_graph import TemporalPeopleGraph
from src.memory.user_memory import UserMemory

logger = logging.getLogger(__name__)


class UserContext:
    """Comprehensive user context data structure.

    Aggregates all memory types for a user to provide complete context
    for AI agent interactions.

    Attributes:
        user_id: User identifier
        profile: User profile data (from UserMemory)
        relationship: Relationship data (from RelationshipMemory)
        recent_conversations: Recent conversation entries (from ConversationMemory)
        recent_actions: Recent user actions (from ActionMemory)
        recent_emotions: Recent emotional traces (from EmotionalMemory)
        context_timestamp: When this context was generated
    """

    def __init__(
        self,
        user_id: str,
        profile: Optional[Dict[str, Any]] = None,
        relationship: Optional[Dict[str, Any]] = None,
        recent_conversations: Optional[List[Dict[str, Any]]] = None,
        recent_actions: Optional[List[Dict[str, Any]]] = None,
        recent_emotions: Optional[List[Dict[str, Any]]] = None,
    ):
        """Initialize a user context.

        Args:
            user_id: User identifier
            profile: User profile data
            relationship: Relationship data
            recent_conversations: Recent conversation entries
            recent_actions: Recent user actions
            recent_emotions: Recent emotional traces
        """
        self.user_id = user_id
        self.profile = profile or {}
        self.relationship = relationship or {}
        self.recent_conversations = recent_conversations or []
        self.recent_actions = recent_actions or []
        self.recent_emotions = recent_emotions or []
        self.context_timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary format.

        Returns:
            Dictionary representation of the user context
        """
        return {
            "user_id": self.user_id,
            "profile": self.profile,
            "relationship": self.relationship,
            "recent_conversations": self.recent_conversations,
            "recent_actions": self.recent_actions,
            "recent_emotions": self.recent_emotions,
            "context_timestamp": self.context_timestamp.isoformat(),
        }


class MemoryManager:
    """Unified memory management interface.

    Orchestrates all memory components (User, Relationship, Conversation,
    Action, Emotional) and provides high-level methods for storing and
    retrieving comprehensive user context.

    This is the main entry point for the memory system.

    Attributes:
        adapter: Shared GraphitiAdapter instance for all memory components
        user_memory: UserMemory instance
        relationship_memory: RelationshipMemory instance
        conversation_memory: ConversationMemory instance
        action_memory: ActionMemory instance
        emotional_memory: EmotionalMemory instance
        config: Memory system configuration
    """

    def __init__(self, adapter: Optional[GraphitiAdapter] = None):
        """Initialize the MemoryManager.

        Creates a shared GraphitiAdapter and initializes all memory components.

        Args:
            adapter: Optional pre-configured GraphitiAdapter.
                    If None, creates a new adapter instance shared across all components.
        """
        self.config = config
        self.adapter = adapter or GraphitiAdapter()

        # Initialize all memory components with shared adapter
        self.user_memory = UserMemory(adapter=self.adapter)
        self.relationship_memory = RelationshipMemory(adapter=self.adapter)
        self.conversation_memory = ConversationMemory(adapter=self.adapter)
        self.action_memory = ActionMemory(adapter=self.adapter)
        self.emotional_memory = EmotionalMemory(adapter=self.adapter)

        # Temporal People Graph — cross-platform relationship tracking
        self.people_graph = TemporalPeopleGraph(adapter=self.adapter)

        logger.info("MemoryManager initialized with all memory components + people graph")

    async def remember_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        platform: Optional[str] = None,
        platform_user_id: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Remember a user by storing their profile and initializing relationship.

        This is the primary method for first-time user registration.
        It creates both a user profile and initializes their relationship.

        Args:
            user_id: Unique user identifier
            name: User's display name
            platform: Platform name (e.g., "telegram", "twitter")
            platform_user_id: Platform-specific user ID
            preferences: User preferences and metadata

        Returns:
            Dictionary containing user profile and relationship data

        Example:
            >>> manager = MemoryManager()
            >>> result = await manager.remember_user(
            ...     user_id="alice",
            ...     name="Alice",
            ...     platform="telegram",
            ...     platform_user_id="123456789",
            ...     preferences={"language": "en"}
            ... )
        """
        logger.debug(f"Remembering user: {user_id}")

        try:
            # Add or update user profile
            profile = await self.user_memory.add_user(
                user_id=user_id,
                name=name,
                platform=platform,
                platform_user_id=platform_user_id,
                preferences=preferences,
            )

            # Initialize or get relationship
            relationship = await self.relationship_memory.add_relationship(
                user_id=user_id,
                initial_points=0,
                metadata={"platform": platform} if platform else None,
            )

            logger.info(f"User remembered: {user_id}")

            return {
                "user_id": user_id,
                "profile": profile.to_dict(),
                "relationship": relationship.to_dict(),
            }

        except Exception as e:
            logger.error(f"Failed to remember user {user_id}: {e}")
            raise

    async def recall_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Recall a user's basic information (profile + relationship).

        Retrieves user profile and relationship data without full context.
        For comprehensive context, use get_user_context().

        Args:
            user_id: User identifier to recall

        Returns:
            Dictionary with profile and relationship data, or None if user not found

        Example:
            >>> manager = MemoryManager()
            >>> user_data = await manager.recall_user("alice")
            >>> if user_data:
            ...     print(f"User: {user_data['profile']['name']}")
            ...     print(f"Level: {user_data['relationship']['relationship_level']}")
        """
        logger.debug(f"Recalling user: {user_id}")

        try:
            # Get user profile
            profile = await self.user_memory.get_user(user_id)
            if not profile:
                logger.debug(f"User not found: {user_id}")
                return None

            # Get relationship
            relationship = await self.relationship_memory.get_relationship(user_id)

            return {
                "user_id": user_id,
                "profile": profile.to_dict(),
                "relationship": relationship.to_dict() if relationship else None,
            }

        except Exception as e:
            logger.error(f"Failed to recall user {user_id}: {e}")
            raise

    async def update_relationship(
        self,
        user_id: str,
# Validated input parameters
        points: int,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a user's relationship by adding points.

        Adds points to the relationship (can be positive or negative)
        and returns the updated relationship data including any level changes.

        Args:
            user_id: User identifier
            points: Points to add (positive or negative)
            context: Optional context explaining why points were added

        Returns:
            Dictionary with updated relationship data

        Example:
            >>> manager = MemoryManager()
            >>> result = await manager.update_relationship(
            ...     user_id="alice",
            ...     points=5,
            ...     context="Had meaningful conversation about AI ethics"
            ... )
            >>> print(f"New level: {result['relationship_level']}")
        """
        logger.debug(f"Updating relationship for user: {user_id} (points: {points})")

        try:
            # Ensure relationship exists
            relationship = await self.relationship_memory.get_relationship(user_id)
            if not relationship:
                logger.debug(f"Creating new relationship for user: {user_id}")
                relationship = await self.relationship_memory.add_relationship(
                    user_id=user_id,
                    initial_points=0,
                )

            # Add points
            old_level = relationship.relationship_level
            new_level = await self.relationship_memory.add_points(
                user_id=user_id,
                points=points,
                reason=context,
            )

            # Get updated relationship
            relationship = await self.relationship_memory.get_relationship(user_id)

            result = relationship.to_dict()
            result["level_changed"] = old_level != new_level
            result["old_level"] = old_level

            logger.info(
                f"Relationship updated for {user_id}: "
                f"{old_level} -> {new_level} ({points:+d} points)"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to update relationship for {user_id}: {e}")
            raise

    async def add_conversation(
        self,
        user_id: str,
        topic: str,
        user_position: Optional[str] = None,
        quotes: Optional[List[str]] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a conversation entry to memory.

        Stores a conversation with its topic, user's position, memorable quotes,
        and context for later retrieval.

        Args:
            user_id: User involved in the conversation
            topic: Main topic or subject discussed
            user_position: User's position or opinion on the topic
            quotes: List of memorable quotes from the conversation
            context: Additional context about the conversation
            metadata: Additional metadata

        Returns:
            Dictionary with stored conversation data

        Example:
            >>> manager = MemoryManager()
            >>> conv = await manager.add_conversation(
            ...     user_id="alice",
            ...     topic="AI consciousness",
            ...     user_position="Believes AI can develop consciousness",
            ...     quotes=["Mind is just information processing"],
            ...     context="Deep philosophical discussion"
            ... )
        """
        logger.debug(f"Adding conversation for user {user_id}: {topic}")

        try:
            entry = await self.conversation_memory.add_conversation(
                user_id=user_id,
                topic=topic,
                user_position=user_position,
                quotes=quotes,
                context=context,
                metadata=metadata,
            )

            logger.info(f"Conversation added: {entry.entry_id}")
            return entry.to_dict()

        except Exception as e:
            logger.error(f"Failed to add conversation for {user_id}: {e}")
            raise

    async def add_action(
        self,
        user_id: str,
        action_type: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add a user action and update relationship points automatically.

        Records the action and automatically awards points based on action type
        (configured in MemoryConfig). Also updates the user's relationship.

        Args:
            user_id: User who performed the action
            action_type: Type of action (like, share, comment, purchase_token)
            context: Additional context about the action
            metadata: Additional metadata

        Returns:
            Dictionary with action data and relationship update

        Example:
            >>> manager = MemoryManager()
            >>> result = await manager.add_action(
            ...     user_id="alice",
            ...     action_type="share",
            ...     context="Shared Freeman's post about consciousness"
            ... )
            >>> print(f"Points awarded: {result['points']}")
            >>> print(f"New relationship level: {result['relationship_level']}")
        """
        logger.debug(f"Adding action for user {user_id}: {action_type}")

        try:
            # Add action (points are auto-calculated)
            action = await self.action_memory.add_action(
                user_id=user_id,
                action_type=action_type,
                context=context,
                metadata=metadata,
            )

            # Update relationship with action points
            relationship = await self.update_relationship(
                user_id=user_id,
                points=action.points,
                context=f"Action: {action_type}",
            )

            logger.info(
                f"Action added for {user_id}: {action_type} "
                f"(+{action.points} points, level: {relationship['relationship_level']})"
            )

            return {
                "action": action.to_dict(),
                "relationship_level": relationship["relationship_level"],
                "relationship_points": relationship["relationship_points"],
                "level_changed": relationship["level_changed"],
            }

        except Exception as e:
            logger.error(f"Failed to add action for {user_id}: {e}")
            raise

    async def add_emotion(
        self,
        emotion_type: str,
        intensity: float,
        user_id: Optional[str] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Add an emotional trace to memory.

        Records how Freeman felt during an interaction - curiosity, inspiration,
        annoyance, etc. This helps Freeman maintain emotional continuity.

        Args:
            emotion_type: Type of emotion (curious, inspired, annoyed, etc.)
            intensity: Emotion intensity (0.0-10.0 scale)
            user_id: User who triggered this emotion (if applicable)
            context: What triggered the emotion
            metadata: Additional metadata

        Returns:
            Dictionary with stored emotional trace data

        Example:
            >>> manager = MemoryManager()
            >>> emotion = await manager.add_emotion(
            ...     emotion_type="inspired",
            ...     intensity=8.5,
            ...     user_id="alice",
            ...     context="Alice shared a brilliant insight about AI consciousness"
            ... )
        """
        logger.debug(f"Adding emotion: {emotion_type} (intensity: {intensity})")

        try:
            trace = await self.emotional_memory.add_emotion(
                emotion_type=emotion_type,
                intensity=intensity,
                user_id=user_id,
                context=context,
                metadata=metadata,
            )

            logger.info(
                f"Emotion added: {emotion_type} "
                f"(intensity: {intensity}, user: {user_id or 'general'})"
            )
            return trace.to_dict()

        except Exception as e:
            logger.error(f"Failed to add emotion: {e}")
            raise

    async def get_user_context(
        self,
        user_id: str,
        conversation_limit: int = 10,
        action_limit: int = 20,
        emotion_limit: int = 10,
    ) -> Optional[UserContext]:
        """Get comprehensive user context for AI agent interactions.

        Retrieves all memory types for a user: profile, relationship,
        recent conversations, actions, and emotional traces. This provides
        complete context for generating personalized responses.

        Args:
            user_id: User identifier
            conversation_limit: Number of recent conversations to include
            action_limit: Number of recent actions to include
            emotion_limit: Number of recent emotional traces to include

        Returns:
            UserContext instance with all memory data, or None if user not found

        Example:
            >>> manager = MemoryManager()
            >>> context = await manager.get_user_context("alice")
            >>> if context:
            ...     print(f"User: {context.profile['name']}")
            ...     print(f"Level: {context.relationship['relationship_level']}")
            ...     print(f"Recent conversations: {len(context.recent_conversations)}")
        """
        logger.debug(f"Getting user context for: {user_id}")

        try:
            # Get user profile
            profile = await self.user_memory.get_user(user_id)
            if not profile:
                logger.debug(f"User not found: {user_id}")
                return None

            # Get relationship
            relationship = await self.relationship_memory.get_relationship(user_id)

            # Get recent conversations
            conversations = await self.conversation_memory.get_conversations_by_user(
                user_id=user_id,
                limit=conversation_limit,
            )

            # Get recent actions
            actions = await self.action_memory.get_actions_by_user(
                user_id=user_id,
                limit=action_limit,
            )

            # Get recent emotions about this user
            emotions = await self.emotional_memory.get_emotions_by_user(
                user_id=user_id,
                limit=emotion_limit,
            )

            context = UserContext(
                user_id=user_id,
                profile=profile.to_dict(),
                relationship=relationship.to_dict() if relationship else None,
                recent_conversations=[c.to_dict() for c in conversations],
                recent_actions=[a.to_dict() for a in actions],
                recent_emotions=[e.to_dict() for e in emotions],
            )

            logger.info(
                f"User context retrieved for {user_id}: "
                f"{len(conversations)} conversations, "
                f"{len(actions)} actions, "
                f"{len(emotions)} emotions"
            )

            return context

        except Exception as e:
            logger.error(f"Failed to get user context for {user_id}: {e}")
            raise

    async def initialize(self) -> bool:
        """Initialize the memory manager and verify connection to Graphiti.

        Should be called before using the memory manager to ensure
        all components are properly connected.

        Returns:
            True if initialization successful, False otherwise

        Example:
            >>> manager = MemoryManager()
            >>> if await manager.initialize():
            ...     print("Memory system ready")
        """
        logger.info("Initializing MemoryManager...")

        try:
            # Check Graphiti connection
            health_result = await self.adapter.health_check()
            is_healthy = health_result.get("status") == "healthy" if isinstance(health_result, dict) else bool(health_result)

            if is_healthy:
                logger.info("MemoryManager initialized successfully")
            else:
                logger.warning("MemoryManager initialized but Graphiti connection unhealthy")

            return is_healthy

        except Exception as e:
            logger.error(f"Failed to initialize MemoryManager: {e}")
            return False

    async def close(self) -> None:
        """Close the memory manager and clean up resources.

        Should be called when shutting down to properly close
        database connections and clean up resources.

        Example:
            >>> manager = MemoryManager()
            >>> await manager.initialize()
            >>> # ... use memory manager ...
            >>> await manager.close()
        """
        logger.info("Closing MemoryManager...")

        try:
            await self.adapter.close()
            logger.info("MemoryManager closed successfully")

        except Exception as e:
            logger.error(f"Failed to close MemoryManager: {e}")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
