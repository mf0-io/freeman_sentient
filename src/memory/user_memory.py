"""UserMemory for managing user profiles and metadata.

This module provides high-level user profile management, storing user information
in the Graphiti memory graph. It handles user creation, updates, and retrieval.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.memory_config import config
from src.memory.graphiti_adapter import GraphitiAdapter

logger = logging.getLogger(__name__)


class UserProfile:
    """User profile data structure.

    Attributes:
        user_id: Unique user identifier
        name: User's display name
        platform_ids: Dict mapping platform names to platform-specific user IDs
        first_seen: Timestamp of first interaction
        last_seen: Timestamp of last interaction
        preferences: User preferences and metadata
    """

    def __init__(
        self,
        user_id: str,
        name: Optional[str] = None,
        platform_ids: Optional[Dict[str, str]] = None,
        first_seen: Optional[datetime] = None,
        last_seen: Optional[datetime] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a user profile.

        Args:
            user_id: Unique user identifier
            name: User's display name (defaults to user_id if not provided)
            platform_ids: Platform-specific user IDs (e.g., {"telegram": "123", "twitter": "@user"})
            first_seen: When user was first seen (defaults to now)
            last_seen: When user was last seen (defaults to now)
            preferences: User preferences and metadata
        """
        self.user_id = user_id
        self.name = name or user_id
        self.platform_ids = platform_ids or {}
        self.first_seen = first_seen or datetime.now()
        self.last_seen = last_seen or datetime.now()
        self.preferences = preferences or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary format.

        Returns:
            Dictionary representation of the user profile
        """
        return {
            "user_id": self.user_id,
            "name": self.name,
            "platform_ids": self.platform_ids,
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat(),
            "preferences": self.preferences,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        """Create a user profile from dictionary data.

        Args:
            data: Dictionary containing user profile data

        Returns:
            UserProfile instance
        """
        return cls(
            user_id=data["user_id"],
            name=data.get("name"),
            platform_ids=data.get("platform_ids", {}),
            first_seen=datetime.fromisoformat(data["first_seen"]) if "first_seen" in data else None,
            last_seen=datetime.fromisoformat(data["last_seen"]) if "last_seen" in data else None,
            preferences=data.get("preferences", {}),
        )


class UserMemory:
    """Memory management for user profiles.

    Provides high-level interface for storing and retrieving user information
    in the Graphiti memory graph. Handles user creation, updates, and lookups.

    Attributes:
        adapter: GraphitiAdapter instance for memory operations
        config: Memory system configuration
    """

    def __init__(self, adapter: Optional[GraphitiAdapter] = None):
        """Initialize the UserMemory.

        Args:
            adapter: Optional pre-configured GraphitiAdapter.
                    If None, creates a new adapter instance.
        """
        self.config = config
        self.adapter = adapter or GraphitiAdapter()
        logger.info("UserMemory initialized")

    async def add_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        platform: Optional[str] = None,
        platform_user_id: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> UserProfile:
        """Add or update a user in memory.

        If the user already exists, updates their information and last_seen timestamp.

        Args:
            user_id: Unique user identifier
            name: User's display name
            platform: Platform name (e.g., "telegram", "twitter")
            platform_user_id: Platform-specific user ID
            preferences: User preferences and metadata

        Returns:
            UserProfile instance with the stored user data

        Example:
            >>> memory = UserMemory()
            >>> profile = await memory.add_user(
            ...     user_id="alice",
            ...     name="Alice",
            ...     platform="telegram",
            ...     platform_user_id="123456789",
            ...     preferences={"language": "en"}
            ... )
        """
        logger.debug(f"Adding user: {user_id}")

        try:
            # Check if user already exists
            existing = await self.get_user(user_id)

            if existing:
                # Update existing user
                logger.debug(f"Updating existing user: {user_id}")
                profile = existing

                # Update name if provided
                if name:
                    profile.name = name

                # Update platform IDs
                if platform and platform_user_id:
                    profile.platform_ids[platform] = platform_user_id

                # Merge preferences
                if preferences:
                    profile.preferences.update(preferences)

                # Update last_seen
                profile.last_seen = datetime.now()
            else:
                # Create new user
                logger.debug(f"Creating new user: {user_id}")
                platform_ids = {}
                if platform and platform_user_id:
                    platform_ids[platform] = platform_user_id

                profile = UserProfile(
                    user_id=user_id,
                    name=name,
                    platform_ids=platform_ids,
                    first_seen=datetime.now(),
                    last_seen=datetime.now(),
                    preferences=preferences or {},
                )

            # Store in Graphiti as an entity
            await self.adapter.add_entity(
                name=user_id,
                entity_type="user",
                attributes=profile.to_dict(),
            )

            logger.info(f"User stored: {user_id}")
            return profile

        except Exception as e:
            logger.error(f"Failed to add user {user_id}: {e}")
            raise

    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Retrieve a user profile from memory.

        Args:
            user_id: Unique user identifier

        Returns:
            UserProfile if found, None otherwise

        Example:
            >>> memory = UserMemory()
            >>> profile = await memory.get_user("alice")
            >>> if profile:
            ...     print(f"User: {profile.name}, last seen: {profile.last_seen}")
        """
        logger.debug(f"Retrieving user: {user_id}")

        try:
            # Search for user entity
            results = await self.adapter.search_memory(
                query=f"user {user_id}",
                limit=1,
                entity_filter=["user"],
            )

            if not results:
                logger.debug(f"User not found: {user_id}")
                return None

            # Extract user data from first result
            user_data = results[0]

            # Parse user profile from attributes
            if "attributes" in user_data:
                profile = UserProfile.from_dict(user_data["attributes"])
                logger.debug(f"User found: {user_id}")
                return profile

            logger.debug(f"User found but no attributes: {user_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve user {user_id}: {e}")
            raise

    async def update_user(
        self,
        user_id: str,
        name: Optional[str] = None,
        platform_ids: Optional[Dict[str, str]] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> Optional[UserProfile]:
        """Update an existing user's information.

        Args:
            user_id: Unique user identifier
            name: New display name (if provided)
            platform_ids: Platform IDs to add/update (if provided)
            preferences: Preferences to add/update (if provided)

        Returns:
            Updated UserProfile if user exists, None otherwise

        Example:
            >>> memory = UserMemory()
            >>> profile = await memory.update_user(
            ...     user_id="alice",
            ...     preferences={"language": "ru", "theme": "dark"}
            ... )
        """
        logger.debug(f"Updating user: {user_id}")

        try:
            # Get existing user
            existing = await self.get_user(user_id)

            if not existing:
                logger.warning(f"Cannot update non-existent user: {user_id}")
                return None

            # Update fields
            if name:
                existing.name = name

            if platform_ids:
                existing.platform_ids.update(platform_ids)

            if preferences:
                existing.preferences.update(preferences)

            # Update last_seen
            existing.last_seen = datetime.now()

            # Store updated profile
            await self.adapter.add_entity(
                name=user_id,
                entity_type="user",
                attributes=existing.to_dict(),
            )

            logger.info(f"User updated: {user_id}")
            return existing

        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise

    async def list_users(self, limit: Optional[int] = None) -> List[UserProfile]:
        """List all users in memory.

        Args:
            limit: Maximum number of users to return (defaults to config limit)

        Returns:
            List of UserProfile instances

        Example:
            >>> memory = UserMemory()
            >>> users = await memory.list_users(limit=10)
            >>> for user in users:
            ...     print(f"{user.name} - {user.user_id}")
        """
        logger.debug("Listing users")

        try:
            # Search for all user entities
            results = await self.adapter.search_memory(
                query="user",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["user"],
            )

            profiles = []
            for result in results:
                if "attributes" in result:
                    try:
                        profile = UserProfile.from_dict(result["attributes"])
                        profiles.append(profile)
                    except Exception as e:
                        logger.warning(f"Failed to parse user profile: {e}")
                        continue

            logger.info(f"Found {len(profiles)} users")
            return profiles

        except Exception as e:
            logger.error(f"Failed to list users: {e}")
            raise
