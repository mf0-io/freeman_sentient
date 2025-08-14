"""ActionMemory for tracking user actions with point scoring.

This module manages user actions (likes, shares, comments, purchases), tracking
action history, points awarded, and providing action-based analytics.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.memory_config import config
from src.memory.graphiti_adapter import GraphitiAdapter

logger = logging.getLogger(__name__)


class UserAction:
    """User action data structure.

    Attributes:
        action_id: Unique identifier for this action
        user_id: User who performed the action
        action_type: Type of action (like, share, comment, purchase_token)
        points: Points awarded for this action
        timestamp: When the action occurred
        context: Additional context about the action
        metadata: Additional metadata
    """

    def __init__(
        self,
        action_id: str,
        user_id: str,
        action_type: str,
        points: int,
        timestamp: Optional[datetime] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a user action.

        Args:
            action_id: Unique identifier for this action
            user_id: User who performed the action
            action_type: Type of action (like, share, comment, purchase_token)
            points: Points awarded for this action
            timestamp: When action occurred (defaults to now)
            context: Additional context about the action
            metadata: Additional metadata
        """
        self.action_id = action_id
        self.user_id = user_id
        self.action_type = action_type
        self.points = points
        self.timestamp = timestamp or datetime.now()
        self.context = context or ""
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary format.

        Returns:
            Dictionary representation of the user action
        """
        return {
            "action_id": self.action_id,
            "user_id": self.user_id,
            "action_type": self.action_type,
            "points": self.points,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserAction":
        """Create a user action from dictionary data.

        Args:
            data: Dictionary containing user action data

        Returns:
            UserAction instance
        """
        return cls(
            action_id=data["action_id"],
            user_id=data["user_id"],
            action_type=data["action_type"],
            points=data.get("points", 0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None,
            context=data.get("context"),
            metadata=data.get("metadata", {}),
        )


class ActionMemory:
    """Memory management for user actions and scoring.

    Provides high-level interface for tracking user actions (likes, shares,
    comments, purchases), storing action history, and retrieving action-based
    analytics and statistics.

    Attributes:
        adapter: GraphitiAdapter instance for memory operations
        config: Memory system configuration
    """

    def __init__(self, adapter: Optional[GraphitiAdapter] = None):
        """Initialize the ActionMemory.

        Args:
            adapter: Optional pre-configured GraphitiAdapter.
                    If None, creates a new adapter instance.
        """
        self.config = config
        self.adapter = adapter or GraphitiAdapter()
        logger.info("ActionMemory initialized")

    async def add_action(
        self,
        user_id: str,
        action_type: str,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UserAction:
        """Record a user action and award points.

        Creates a new action entry with automatic point scoring based on
        action type. The action is stored in Graphiti as both an entity
        (for the action record) and an episode (for temporal context).

        Args:
            user_id: User who performed the action
            action_type: Type of action (like, share, comment, purchase_token)
            context: Additional context about the action
            metadata: Additional metadata

        Returns:
            UserAction instance with the stored action data

        Raises:
            ValueError: If action_type is not recognized

        Example:
            >>> memory = ActionMemory()
            >>> action = await memory.add_action(
            ...     user_id="alice",
            ...     action_type="like",
            ...     context="Liked post about AI ethics",
            ...     metadata={"post_id": "post_123"}
            ... )
        """
        logger.debug(f"Adding action for user {user_id}: {action_type}")

        try:
            # Get points for this action type
            points = self.config.get_action_points(action_type)

            # Generate action ID based on timestamp and user
            timestamp = datetime.now()
            action_id = f"action_{user_id}_{action_type}_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}"

            # Create action entry
            action = UserAction(
                action_id=action_id,
                user_id=user_id,
                action_type=action_type,
                points=points,
                timestamp=timestamp,
                context=context,
                metadata=metadata or {},
            )

            # Store as entity in Graphiti
            await self.adapter.add_entity(
                name=action_id,
                entity_type="action",
                attributes=action.to_dict(),
            )

            # Also store as an episode for temporal context
            episode_content = f"User {user_id} performed action '{action_type}' (+{points} points)"
            if context:
                episode_content += f". Context: {context}"

            await self.adapter.add_episode(
                name=action_id,
                content=episode_content,
                episode_type="event",
                source_description=f"action_{action_type}",
                reference_time=timestamp,
                entity_references=[f"user:{user_id}", f"action_type:{action_type}"],
            )

            logger.info(f"Action recorded: {action_id} ({action_type}, +{points} points)")
            return action

        except ValueError as e:
            logger.error(f"Invalid action type '{action_type}': {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to add action for {user_id}: {e}")
            raise

    async def get_action(self, action_id: str) -> Optional[UserAction]:
        """Retrieve a specific action from memory.

        Args:
            action_id: Unique identifier for the action

        Returns:
            UserAction if found, None otherwise

        Example:
            >>> memory = ActionMemory()
            >>> action = await memory.get_action("action_alice_like_20240115_143000")
            >>> if action:
            ...     print(f"Action: {action.action_type}, Points: {action.points}")
        """
        logger.debug(f"Retrieving action: {action_id}")

        try:
            # Search for action entity
            results = await self.adapter.search_memory(
                query=action_id,
                limit=1,
                entity_filter=["action"],
            )

            if not results:
                logger.debug(f"Action not found: {action_id}")
                return None

            # Extract action data from first result
            action_data = results[0]

            # Parse action from attributes
            if "attributes" in action_data:
                action = UserAction.from_dict(action_data["attributes"])
                logger.debug(f"Action found: {action_id}")
                return action

            logger.debug(f"Action found but no attributes: {action_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve action {action_id}: {e}")
            raise

    async def get_actions_by_user(
        self,
        user_id: str,
        action_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[UserAction]:
        """Get all actions performed by a specific user.

        Args:
            user_id: User identifier
            action_type: Optional filter by action type
            limit: Maximum number of actions to return (defaults to config limit)

        Returns:
            List of UserAction instances for the user

        Example:
            >>> memory = ActionMemory()
            >>> # Get all actions by alice
            >>> actions = await memory.get_actions_by_user("alice", limit=20)
            >>> # Get only alice's likes
            >>> likes = await memory.get_actions_by_user("alice", action_type="like")
        """
        logger.debug(f"Retrieving actions for user: {user_id} (type: {action_type})")

        try:
            # Build search query
            query = f"action user {user_id}"
            if action_type:
                query += f" {action_type}"

            # Search for action entities for this user
            results = await self.adapter.search_memory(
                query=query,
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["action"],
            )

            actions = []
            for result in results:
                if "attributes" in result:
                    try:
                        action = UserAction.from_dict(result["attributes"])

                        # Filter by user_id
                        if action.user_id != user_id:
                            continue

                        # Filter by action_type if specified
                        if action_type and action.action_type != action_type:
                            continue

                        actions.append(action)
                    except Exception as e:
                        logger.warning(f"Failed to parse action: {e}")
                        continue

            # Sort by timestamp (most recent first)
            actions.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(actions)} actions for user {user_id}")
            return actions

        except Exception as e:
            logger.error(f"Failed to retrieve actions for user {user_id}: {e}")
            raise

    async def get_actions_by_type(
        self,
        action_type: str,
        limit: Optional[int] = None,
    ) -> List[UserAction]:
        """Get all actions of a specific type.

        Args:
            action_type: Type of action to filter by
            limit: Maximum number of actions to return (defaults to config limit)

        Returns:
            List of UserAction instances of the specified type

        Example:
            >>> memory = ActionMemory()
            >>> # Get all purchase actions
            >>> purchases = await memory.get_actions_by_type("purchase_token", limit=50)
            >>> total_revenue = sum(1 for p in purchases)
        """
        logger.debug(f"Retrieving actions of type: {action_type}")

        try:
            # Search for action entities with this type
            results = await self.adapter.search_memory(
                query=f"action {action_type}",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["action"],
            )

            actions = []
            for result in results:
                if "attributes" in result:
                    try:
                        action = UserAction.from_dict(result["attributes"])

                        # Filter by action_type
                        if action.action_type == action_type:
                            actions.append(action)
                    except Exception as e:
                        logger.warning(f"Failed to parse action: {e}")
                        continue

            # Sort by timestamp (most recent first)
            actions.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(actions)} actions of type '{action_type}'")
            return actions

        except Exception as e:
            logger.error(f"Failed to retrieve actions of type '{action_type}': {e}")
            raise

    async def list_actions(
        self,
        limit: Optional[int] = None,
    ) -> List[UserAction]:
        """List all actions in memory.

        Args:
            limit: Maximum number of actions to return (defaults to config limit)

        Returns:
            List of UserAction instances

        Example:
            >>> memory = ActionMemory()
            >>> actions = await memory.list_actions(limit=100)
            >>> for action in actions:
            ...     print(f"{action.timestamp}: {action.user_id} - {action.action_type}")
        """
        logger.debug("Listing all actions")

        try:
            # Search for all action entities
            results = await self.adapter.search_memory(
                query="action",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["action"],
            )

            actions = []
            for result in results:
                if "attributes" in result:
                    try:
                        action = UserAction.from_dict(result["attributes"])
                        actions.append(action)
                    except Exception as e:
                        logger.warning(f"Failed to parse action: {e}")
                        continue

            # Sort by timestamp (most recent first)
            actions.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(actions)} actions")
            return actions

        except Exception as e:
            logger.error(f"Failed to list actions: {e}")
            raise

    async def get_user_action_stats(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """Get statistics about a user's actions.

        Returns:
            Dictionary containing action statistics:
            - total_actions: Total number of actions by the user
            - total_points: Total points earned from all actions
            - by_type: Count and points breakdown by action type
            - most_recent: Most recent action timestamp

        Example:
            >>> memory = ActionMemory()
            >>> stats = await memory.get_user_action_stats("alice")
            >>> print(f"Total points: {stats['total_points']}")
            >>> print(f"Likes: {stats['by_type']['like']['count']}")
        """
        logger.debug(f"Computing action statistics for user: {user_id}")

        try:
            # Get all actions for this user
            actions = await self.get_actions_by_user(user_id)

            if not actions:
                return {
                    "total_actions": 0,
                    "total_points": 0,
                    "by_type": {
                        "like": {"count": 0, "points": 0},
                        "share": {"count": 0, "points": 0},
                        "comment": {"count": 0, "points": 0},
                        "purchase_token": {"count": 0, "points": 0},
                    },
                    "most_recent": None,
                }

            # Compute statistics
            by_type = {
                "like": {"count": 0, "points": 0},
                "share": {"count": 0, "points": 0},
                "comment": {"count": 0, "points": 0},
                "purchase_token": {"count": 0, "points": 0},
            }
            total_points = 0
            most_recent = actions[0].timestamp  # Already sorted by timestamp desc

            for action in actions:
                total_points += action.points
                if action.action_type in by_type:
                    by_type[action.action_type]["count"] += 1
                    by_type[action.action_type]["points"] += action.points

            stats = {
                "total_actions": len(actions),
                "total_points": total_points,
                "by_type": by_type,
                "most_recent": most_recent.isoformat(),
            }

            logger.info(
                f"Action stats for {user_id}: "
                f"{stats['total_actions']} actions, {total_points} points"
            )
            return stats

        except Exception as e:
            logger.error(f"Failed to compute action stats for {user_id}: {e}")
            raise

    async def get_global_action_stats(self) -> Dict[str, Any]:
        """Get global statistics about all actions.

        Returns:
            Dictionary containing global action statistics:
            - total_actions: Total number of all actions
            - total_points: Total points awarded across all actions
            - by_type: Count and points breakdown by action type
            - unique_users: Number of unique users who performed actions

        Example:
            >>> memory = ActionMemory()
            >>> stats = await memory.get_global_action_stats()
            >>> print(f"Total engagement: {stats['total_actions']}")
            >>> print(f"Active users: {stats['unique_users']}")
        """
        logger.debug("Computing global action statistics")

        try:
            # Get all actions
            actions = await self.list_actions(limit=self.config.graphiti_max_episodes)

            if not actions:
                return {
                    "total_actions": 0,
                    "total_points": 0,
                    "by_type": {
                        "like": {"count": 0, "points": 0},
                        "share": {"count": 0, "points": 0},
                        "comment": {"count": 0, "points": 0},
                        "purchase_token": {"count": 0, "points": 0},
                    },
                    "unique_users": 0,
                }

            # Compute statistics
            by_type = {
                "like": {"count": 0, "points": 0},
                "share": {"count": 0, "points": 0},
                "comment": {"count": 0, "points": 0},
                "purchase_token": {"count": 0, "points": 0},
            }
            total_points = 0
            unique_users = set()

            for action in actions:
                total_points += action.points
                unique_users.add(action.user_id)
                if action.action_type in by_type:
                    by_type[action.action_type]["count"] += 1
                    by_type[action.action_type]["points"] += action.points

            stats = {
                "total_actions": len(actions),
                "total_points": total_points,
                "by_type": by_type,
                "unique_users": len(unique_users),
            }

            logger.info(
                f"Global action stats: {stats['total_actions']} actions, "
                f"{stats['unique_users']} users, {total_points} points"
            )
            return stats

        except Exception as e:
            logger.error(f"Failed to compute global action stats: {e}")
            raise
