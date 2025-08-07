"""RelationshipMemory for tracking relationship levels and progression.

This module manages user relationships with Freeman, tracking relationship points,
levels (stranger -> acquaintance -> friend -> ally), and interaction history.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.memory_config import config
from src.memory.graphiti_adapter import GraphitiAdapter

logger = logging.getLogger(__name__)


class Relationship:
    """Relationship data structure.

    Attributes:
        user_id: Unique user identifier
        relationship_points: Total points accumulated through interactions
        relationship_level: Current level (stranger, acquaintance, friend, ally)
        first_interaction: Timestamp of first interaction
        last_interaction: Timestamp of last interaction
        interaction_count: Total number of interactions
        metadata: Additional relationship metadata
    """

    def __init__(
        self,
        user_id: str,
        relationship_points: int = 0,
        relationship_level: Optional[str] = None,
        first_interaction: Optional[datetime] = None,
        last_interaction: Optional[datetime] = None,
        interaction_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a relationship.

        Args:
            user_id: Unique user identifier
            relationship_points: Total accumulated points (defaults to 0)
            relationship_level: Current level (auto-calculated if not provided)
            first_interaction: When relationship started (defaults to now)
            last_interaction: When last interaction occurred (defaults to now)
            interaction_count: Total number of interactions
            metadata: Additional relationship metadata
        """
        self.user_id = user_id
        self.relationship_points = relationship_points
        self.first_interaction = first_interaction or datetime.now()
        self.last_interaction = last_interaction or datetime.now()
        self.interaction_count = interaction_count
        self.metadata = metadata or {}

        # Auto-calculate relationship level if not provided
        if relationship_level is None:
            self.relationship_level = config.get_relationship_level(relationship_points)
        else:
            self.relationship_level = relationship_level

    def add_points(self, points: int) -> str:
        """Add points to the relationship and recalculate level.

        Args:
            points: Points to add (can be negative for point deductions)

        Returns:
            New relationship level after adding points
        """
        old_level = self.relationship_level
        self.relationship_points += points
        self.relationship_level = config.get_relationship_level(self.relationship_points)

        # Update interaction tracking
        self.last_interaction = datetime.now()
        self.interaction_count += 1

        if old_level != self.relationship_level:
            logger.info(
                f"Relationship with {self.user_id} leveled up: "
                f"{old_level} -> {self.relationship_level} "
                f"(points: {self.relationship_points})"
            )

        return self.relationship_level

    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary format.

        Returns:
            Dictionary representation of the relationship
        """
        return {
            "user_id": self.user_id,
            "relationship_points": self.relationship_points,
            "relationship_level": self.relationship_level,
            "first_interaction": self.first_interaction.isoformat(),
            "last_interaction": self.last_interaction.isoformat(),
            "interaction_count": self.interaction_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Relationship":
        """Create a relationship from dictionary data.

        Args:
            data: Dictionary containing relationship data

        Returns:
            Relationship instance
        """
        return cls(
            user_id=data["user_id"],
            relationship_points=data.get("relationship_points", 0),
            relationship_level=data.get("relationship_level"),
            first_interaction=datetime.fromisoformat(data["first_interaction"]) if "first_interaction" in data else None,
            last_interaction=datetime.fromisoformat(data["last_interaction"]) if "last_interaction" in data else None,
            interaction_count=data.get("interaction_count", 0),
            metadata=data.get("metadata", {}),
        )


class RelationshipMemory:
    """Memory management for user relationships.

    Provides high-level interface for tracking and managing relationships
    with users. Handles relationship progression through point accumulation
    and level transitions (stranger -> acquaintance -> friend -> ally).

    Attributes:
        adapter: GraphitiAdapter instance for memory operations
        config: Memory system configuration
    """

    def __init__(self, adapter: Optional[GraphitiAdapter] = None):
        """Initialize the RelationshipMemory.

        Args:
            adapter: Optional pre-configured GraphitiAdapter.
                    If None, creates a new adapter instance.
        """
        self.config = config
        self.adapter = adapter or GraphitiAdapter()
        logger.info("RelationshipMemory initialized")

    async def add_relationship(
        self,
        user_id: str,
        initial_points: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Relationship:
        """Add or update a relationship in memory.

        If the relationship already exists, returns the existing relationship
        without modification. Use update_relationship() or add_points() to modify.

        Args:
            user_id: Unique user identifier
            initial_points: Starting relationship points (defaults to 0)
            metadata: Additional relationship metadata

        Returns:
            Relationship instance with the stored relationship data

        Example:
            >>> memory = RelationshipMemory()
            >>> rel = await memory.add_relationship(
            ...     user_id="alice",
            ...     initial_points=0,
            ...     metadata={"source": "telegram"}
            ... )
        """
        logger.debug(f"Adding relationship for user: {user_id}")

        try:
            # Check if relationship already exists
            existing = await self.get_relationship(user_id)

            if existing:
                logger.debug(f"Relationship already exists for user: {user_id}")
                return existing

            # Create new relationship
            logger.debug(f"Creating new relationship for user: {user_id}")
            relationship = Relationship(
                user_id=user_id,
                relationship_points=initial_points,
                first_interaction=datetime.now(),
                last_interaction=datetime.now(),
                interaction_count=0,
                metadata=metadata or {},
            )

            # Store in Graphiti as an entity
            await self.adapter.add_entity(
                name=f"relationship_{user_id}",
                entity_type="relationship",
                attributes=relationship.to_dict(),
            )

            logger.info(f"Relationship created for {user_id}: {relationship.relationship_level}")
            return relationship

        except Exception as e:
            logger.error(f"Failed to add relationship for {user_id}: {e}")
            raise

    async def get_relationship(self, user_id: str) -> Optional[Relationship]:
        """Retrieve a relationship from memory.

        Args:
            user_id: Unique user identifier

        Returns:
            Relationship if found, None otherwise

        Example:
            >>> memory = RelationshipMemory()
            >>> rel = await memory.get_relationship("alice")
            >>> if rel:
            ...     print(f"Level: {rel.relationship_level}, Points: {rel.relationship_points}")
        """
        logger.debug(f"Retrieving relationship for user: {user_id}")

        try:
            # Search for relationship entity
            results = await self.adapter.search_memory(
                query=f"relationship {user_id}",
                limit=1,
                entity_filter=["relationship"],
            )

            if not results:
                logger.debug(f"Relationship not found for user: {user_id}")
                return None

            # Extract relationship data from first result
            relationship_data = results[0]

            # Parse relationship from attributes
            if "attributes" in relationship_data:
                relationship = Relationship.from_dict(relationship_data["attributes"])
                logger.debug(f"Relationship found for {user_id}: {relationship.relationship_level}")
                return relationship

            logger.debug(f"Relationship found but no attributes for user: {user_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve relationship for {user_id}: {e}")
            raise

    async def add_points(
        self,
        user_id: str,
        points: int,
        reason: Optional[str] = None,
    ) -> Relationship:
        """Add points to a user's relationship and update the level.

        If the relationship doesn't exist, creates it first.
        Points can be negative to represent relationship degradation.

        Args:
            user_id: Unique user identifier
            points: Points to add (positive or negative)
            reason: Optional reason for the point change

        Returns:
            Updated Relationship instance

        Example:
            >>> memory = RelationshipMemory()
            >>> # User liked a post (+1 point)
            >>> rel = await memory.add_points("alice", 1, reason="liked_post")
            >>> # User purchased a token (+50 points)
            >>> rel = await memory.add_points("alice", 50, reason="purchase_token")
        """
        logger.debug(f"Adding {points} points to relationship with {user_id}")

        try:
            # Get or create relationship
            relationship = await self.get_relationship(user_id)

            if not relationship:
                logger.debug(f"Creating new relationship for {user_id}")
                relationship = Relationship(user_id=user_id)

            # Add points and update
            old_points = relationship.relationship_points
            old_level = relationship.relationship_level
            new_level = relationship.add_points(points)

            # Add reason to metadata if provided
            if reason:
                if "point_history" not in relationship.metadata:
                    relationship.metadata["point_history"] = []
                relationship.metadata["point_history"].append({
                    "points": points,
                    "reason": reason,
                    "timestamp": datetime.now().isoformat(),
                })

            # Store updated relationship
            await self.adapter.add_entity(
                name=f"relationship_{user_id}",
                entity_type="relationship",
                attributes=relationship.to_dict(),
            )

            logger.info(
                f"Relationship updated for {user_id}: "
                f"{old_points} -> {relationship.relationship_points} points, "
                f"level: {old_level} -> {new_level}"
            )
            return relationship

        except Exception as e:
            logger.error(f"Failed to add points for {user_id}: {e}")
            raise

    async def update_relationship(
        self,
        user_id: str,
        points: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Relationship]:
        """Update an existing relationship's metadata.

        Use add_points() for point modifications. This method is for
        updating metadata without changing points.

        Args:
            user_id: Unique user identifier
            points: New total points (if provided, replaces current points)
            metadata: Metadata to add/update (if provided)

        Returns:
            Updated Relationship if relationship exists, None otherwise

        Example:
            >>> memory = RelationshipMemory()
            >>> rel = await memory.update_relationship(
            ...     user_id="alice",
            ...     metadata={"last_topic": "AI ethics", "engagement": "high"}
            ... )
        """
        logger.debug(f"Updating relationship for user: {user_id}")

        try:
            # Get existing relationship
            existing = await self.get_relationship(user_id)

            if not existing:
                logger.warning(f"Cannot update non-existent relationship for user: {user_id}")
                return None

            # Update fields
            if points is not None:
                existing.relationship_points = points
                existing.relationship_level = config.get_relationship_level(points)

            if metadata:
                existing.metadata.update(metadata)

            # Update last_interaction
            existing.last_interaction = datetime.now()

            # Store updated relationship
            await self.adapter.add_entity(
                name=f"relationship_{user_id}",
                entity_type="relationship",
                attributes=existing.to_dict(),
            )

            logger.info(f"Relationship updated for {user_id}")
            return existing

        except Exception as e:
            logger.error(f"Failed to update relationship for {user_id}: {e}")
            raise

    async def list_relationships(
        self,
        level_filter: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Relationship]:
        """List all relationships in memory.

        Args:
            level_filter: Optional filter by relationship level
                         (stranger, acquaintance, friend, ally)
            limit: Maximum number of relationships to return (defaults to config limit)

        Returns:
            List of Relationship instances

        Example:
            >>> memory = RelationshipMemory()
            >>> # Get all friends
            >>> friends = await memory.list_relationships(level_filter="friend")
            >>> # Get top 10 relationships
            >>> top_rels = await memory.list_relationships(limit=10)
        """
        logger.debug(f"Listing relationships (filter: {level_filter})")

        try:
            # Search for all relationship entities
            query = "relationship"
            if level_filter:
                query = f"relationship {level_filter}"

            results = await self.adapter.search_memory(
                query=query,
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["relationship"],
            )

            relationships = []
            for result in results:
                if "attributes" in result:
                    try:
                        relationship = Relationship.from_dict(result["attributes"])

                        # Apply level filter if specified
                        if level_filter and relationship.relationship_level != level_filter:
                            continue

                        relationships.append(relationship)
                    except Exception as e:
                        logger.warning(f"Failed to parse relationship: {e}")
                        continue

            logger.info(f"Found {len(relationships)} relationships")
            return relationships

        except Exception as e:
            logger.error(f"Failed to list relationships: {e}")
            raise

    async def get_relationship_stats(self) -> Dict[str, Any]:
        """Get statistics about all relationships.

        Returns:
            Dictionary containing relationship statistics:
            - total_relationships: Total number of relationships
            - by_level: Count of relationships at each level
            - average_points: Average relationship points
            - total_interactions: Total interaction count across all relationships

        Example:
            >>> memory = RelationshipMemory()
            >>> stats = await memory.get_relationship_stats()
            >>> print(f"Total relationships: {stats['total_relationships']}")
            >>> print(f"Friends: {stats['by_level']['friend']}")
        """
        logger.debug("Computing relationship statistics")

        try:
            # Get all relationships
            relationships = await self.list_relationships()

            if not relationships:
                return {
                    "total_relationships": 0,
                    "by_level": {"stranger": 0, "acquaintance": 0, "friend": 0, "ally": 0},
                    "average_points": 0,
                    "total_interactions": 0,
                }

            # Compute statistics
            by_level = {"stranger": 0, "acquaintance": 0, "friend": 0, "ally": 0}
            total_points = 0
            total_interactions = 0

            for rel in relationships:
                by_level[rel.relationship_level] += 1
                total_points += rel.relationship_points
                total_interactions += rel.interaction_count

            stats = {
                "total_relationships": len(relationships),
                "by_level": by_level,
                "average_points": total_points / len(relationships),
                "total_interactions": total_interactions,
            }

            logger.info(f"Relationship stats: {stats['total_relationships']} total, {by_level}")
            return stats

        except Exception as e:
            logger.error(f"Failed to compute relationship stats: {e}")
            raise
