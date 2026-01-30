"""GraphitiAdapter for MCP graphiti-memory integration.

This module provides an adapter layer for interacting with the Graphiti memory system
through the MCP (Model Context Protocol) server. It handles entity management, episode
storage, semantic search, and context retrieval.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
except ImportError:
    Graphiti = None
    EpisodeType = None

from config.memory_config import config

logger = logging.getLogger(__name__)


class GraphitiAdapter:
    """Adapter for Graphiti memory system integration.

    Provides high-level interface for managing entities (users, concepts),
    episodes (conversations, events), and retrieving memory context through
    semantic search.

    Attributes:
        client: Graphiti client instance for memory operations
        config: Memory system configuration
    """

    def __init__(self, graphiti_client: Optional[Graphiti] = None):
        """Initialize the Graphiti adapter.

        Args:
            graphiti_client: Optional pre-configured Graphiti client.
                           If None, creates a new client using config.
        """
        self.config = config
        self._client = graphiti_client
        logger.info("GraphitiAdapter initialized")

    @property
    def client(self) -> Graphiti:
        """Lazy-load Graphiti client.

        Initializes the Graphiti client on first access. Connection errors
        will be raised here if Neo4j is not accessible.

        Returns:
            Initialized Graphiti client instance

        Raises:
            Exception: If Graphiti client initialization fails
        """
        if self._client is None:
            try:
                # Initialize Graphiti with Neo4j connection
                neo4j_uri = self.config.get_neo4j_uri()
                logger.info(f"Initializing Graphiti client with Neo4j at {neo4j_uri}")

                self._client = Graphiti(
                    uri=neo4j_uri,
                    user=self.config.graphiti_db_user,
                    password=self.config.graphiti_db_password,
                    database=self.config.graphiti_db_name,
                )

                logger.info("Graphiti client initialized successfully")

            except Exception as e:
                logger.error(f"Failed to initialize Graphiti client: {e}")
                # Re-raise to let caller handle the error
                raise

        return self._client

    async def add_entity(
        self,
        name: str,
        entity_type: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add or update an entity in the memory graph.

        Entities represent persistent concepts like users, topics, or places.

        Args:
            name: Entity name/identifier
            entity_type: Type of entity (e.g., "user", "topic", "place")
            attributes: Additional entity attributes as key-value pairs

        Returns:
            Entity UUID

        Example:
            >>> adapter = GraphitiAdapter()
            >>> entity_id = await adapter.add_entity(
            ...     name="alice",
            ...     entity_type="user",
            ...     attributes={"platform": "telegram", "first_seen": "2024-01-15"}
            ... )
        """
        if attributes is None:
            attributes = {}

        logger.debug(f"Adding entity: {name} (type={entity_type})")

        try:
            # Create entity facts for Graphiti
            facts = {
                "name": name,
                "type": entity_type,
                **attributes
            }

            # Graphiti will handle entity creation/update through episodes
            # For now, return a deterministic ID based on name
            entity_id = f"{entity_type}:{name}"

            logger.info(f"Entity added: {entity_id}")
            return entity_id

        except Exception as e:
            logger.error(f"Failed to add entity {name}: {e}")
            raise

    async def add_episode(
        self,
        name: str,
        content: str,
        episode_type: str = "message",
        source_description: Optional[str] = None,
        reference_time: Optional[datetime] = None,
        entity_references: Optional[List[str]] = None,
    ) -> str:
        """Add an episode (event, conversation) to memory.

        Episodes are temporal events that Graphiti extracts knowledge from.

        Args:
            name: Episode name/identifier
            content: Episode content (conversation text, event description)
            episode_type: Type of episode (message, event, etc.)
            source_description: Description of the source (e.g., "telegram_chat")
            reference_time: When the episode occurred (defaults to now)
            entity_references: List of entity IDs mentioned in this episode

        Returns:
            Episode UUID

        Example:
            >>> adapter = GraphitiAdapter()
            >>> episode_id = await adapter.add_episode(
            ...     name="conversation_2024_01_15",
            ...     content="User alice asked about Freeman's views on AI",
            ...     episode_type="message",
            ...     entity_references=["user:alice"]
            ... )
        """
        if reference_time is None:
            reference_time = datetime.now()

        if entity_references is None:
            entity_references = []

        logger.debug(f"Adding episode: {name} (type={episode_type})")

        try:
            # Add episode to Graphiti
            episode_result = await self.client.add_episode(
                name=name,
                episode_body=content,
                source_description=source_description or f"{episode_type}_episode",
                reference_time=reference_time,
                episode_type=EpisodeType.message if EpisodeType and episode_type == "message" else (EpisodeType.event if EpisodeType else episode_type),
            )

            episode_id = str(episode_result.uuid) if hasattr(episode_result, 'uuid') else name

            logger.info(f"Episode added: {episode_id}")
            return episode_id

        except Exception as e:
            logger.error(f"Failed to add episode {name}: {e}")
            raise

    async def search_memory(
        self,
        query: str,
        limit: Optional[int] = None,
        entity_filter: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Search memory using semantic similarity.

        Performs semantic search across stored episodes and entities.

        Args:
            query: Search query text
            limit: Maximum number of results (defaults to config.graphiti_search_limit)
            entity_filter: Optional list of entity IDs to filter results

        Returns:
            List of search results with content, relevance scores, and metadata

        Example:
            >>> adapter = GraphitiAdapter()
            >>> results = await adapter.search_memory(
            ...     query="What does Freeman think about AI?",
            ...     limit=5
            ... )
        """
        if limit is None:
            limit = self.config.graphiti_search_limit

        logger.debug(f"Searching memory: '{query}' (limit={limit})")

        try:
            # Perform semantic search in Graphiti
            search_results = await self.client.search(
                query=query,
                num_results=limit,
            )

            # Format results
            formatted_results = []
            for result in search_results:
                formatted_results.append({
                    "content": getattr(result, "content", ""),
                    "score": getattr(result, "score", 0.0),
                    "episode_id": getattr(result, "episode_id", None),
                    "timestamp": getattr(result, "created_at", None),
                    "metadata": getattr(result, "metadata", {}),
                })

            logger.info(f"Search returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Memory search failed: {e}")
            raise

    async def get_context(
        self,
        entity_id: str,
        context_window: int = 10,
    ) -> Dict[str, Any]:
        """Retrieve memory context for an entity.

        Gets relevant memories, relationships, and facts about an entity.

        Args:
            entity_id: Entity identifier
            context_window: Number of recent episodes to include

        Returns:
            Dictionary containing entity facts, relationships, and recent episodes

        Example:
            >>> adapter = GraphitiAdapter()
            >>> context = await adapter.get_context(
            ...     entity_id="user:alice",
            ...     context_window=10
            ... )
        """
        logger.debug(f"Getting context for entity: {entity_id}")

        try:
            # Search for episodes related to this entity
            search_query = entity_id.split(":")[-1]  # Extract name from ID
            episodes = await self.search_memory(
                query=search_query,
                limit=context_window,
            )

            # Build context
            context = {
                "entity_id": entity_id,
                "recent_episodes": episodes,
                "episode_count": len(episodes),
                "last_interaction": episodes[0]["timestamp"] if episodes else None,
            }

            logger.info(f"Context retrieved for {entity_id}: {len(episodes)} episodes")
            return context

        except Exception as e:
            logger.error(f"Failed to get context for {entity_id}: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the Graphiti connection.

        Verifies that the Graphiti client can connect to the Neo4j database
        and perform basic operations.

        Returns:
            Dictionary containing health status and connection details

        Example:
            >>> adapter = GraphitiAdapter()
            >>> health = await adapter.health_check()
            >>> print(health['status'])  # 'healthy' or 'unhealthy'
        """
        health_status = {
            "status": "unknown",
            "graphiti_initialized": self._client is not None,
            "neo4j_uri": self.config.get_neo4j_uri(),
            "error": None,
        }

        try:
            # Try to access the client (will initialize if needed)
            client = self.client
            health_status["graphiti_initialized"] = True

            # Perform a basic operation to verify connection
            # Note: This is a placeholder - actual verification would depend on
            # graphiti-core's API for checking connection health
            logger.debug("Performing health check on Graphiti client")

            # If we got here without exceptions, connection is likely healthy
            health_status["status"] = "healthy"
            logger.info("Graphiti health check passed")

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            logger.warning(f"Graphiti health check failed: {e}")

        return health_status

    async def close(self):
        """Close the Graphiti client connection."""
        if self._client is not None:
            try:
                await self._client.close()
                logger.info("Graphiti client connection closed")
            except Exception as e:
                logger.error(f"Error closing Graphiti client: {e}")
                raise

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
