"""ConversationMemory for tracking important topics, positions, and quotes.

This module manages conversation history, storing topics discussed, user positions
on those topics, memorable quotes, and timestamps for context retrieval.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from config.memory_config import config
from src.memory.graphiti_adapter import GraphitiAdapter

logger = logging.getLogger(__name__)


class ConversationEntry:
    """Conversation entry data structure.

    Attributes:
        entry_id: Unique identifier for this conversation entry
        topic: Main topic or subject of the conversation
        user_id: User involved in this conversation
        user_position: User's stated position or opinion on the topic
        quotes: List of memorable quotes from this conversation
        timestamp: When this conversation occurred
        context: Additional context about the conversation
        metadata: Additional metadata
    """

    def __init__(
        self,
        entry_id: str,
        topic: str,
        user_id: str,
        user_position: Optional[str] = None,
        quotes: Optional[List[str]] = None,
        timestamp: Optional[datetime] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a conversation entry.

        Args:
            entry_id: Unique identifier for this entry
            topic: Main topic or subject discussed
            user_id: User involved in this conversation
            user_position: User's position or opinion on the topic
            quotes: List of memorable quotes
            timestamp: When conversation occurred (defaults to now)
            context: Additional context about the conversation
            metadata: Additional metadata
        """
        self.entry_id = entry_id
        self.topic = topic
        self.user_id = user_id
        self.user_position = user_position or ""
        self.quotes = quotes or []
        self.timestamp = timestamp or datetime.now()
        self.context = context or ""
        self.metadata = metadata or {}

    def add_quote(self, quote: str) -> None:
        """Add a memorable quote to this conversation entry.

        Args:
            quote: Quote text to add
        """
        if quote and quote not in self.quotes:
            self.quotes.append(quote)

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation entry to dictionary format.

        Returns:
            Dictionary representation of the conversation entry
        """
        return {
            "entry_id": self.entry_id,
            "topic": self.topic,
            "user_id": self.user_id,
            "user_position": self.user_position,
            "quotes": self.quotes,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationEntry":
        """Create a conversation entry from dictionary data.

        Args:
            data: Dictionary containing conversation entry data

        Returns:
            ConversationEntry instance
        """
        return cls(
            entry_id=data["entry_id"],
            topic=data["topic"],
            user_id=data["user_id"],
            user_position=data.get("user_position"),
            quotes=data.get("quotes", []),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else None,
            context=data.get("context"),
            metadata=data.get("metadata", {}),
        )


class ConversationMemory:
    """Memory management for conversation history and topics.

    Provides high-level interface for storing and retrieving conversation
    entries, including topics discussed, user positions, and memorable quotes.

    Attributes:
        adapter: GraphitiAdapter instance for memory operations
        config: Memory system configuration
    """

    def __init__(self, adapter: Optional[GraphitiAdapter] = None):
        """Initialize the ConversationMemory.

        Args:
            adapter: Optional pre-configured GraphitiAdapter.
                    If None, creates a new adapter instance.
        """
        self.config = config
        self.adapter = adapter or GraphitiAdapter()
        logger.info("ConversationMemory initialized")

    async def add_conversation(
        self,
        user_id: str,
        topic: str,
        user_position: Optional[str] = None,
        quotes: Optional[List[str]] = None,
        context: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationEntry:
        """Add a conversation entry to memory.

        Creates a new conversation entry with the given topic, user position,
        and optional quotes. The entry is stored in Graphiti as both an entity
        (for the topic) and an episode (for the conversation event).

        Args:
            user_id: User involved in this conversation
            topic: Main topic or subject discussed
            user_position: User's stated position or opinion on the topic
            quotes: List of memorable quotes from the conversation
            context: Additional context about the conversation
            metadata: Additional metadata

        Returns:
            ConversationEntry instance with the stored conversation data

        Example:
            >>> memory = ConversationMemory()
            >>> entry = await memory.add_conversation(
            ...     user_id="alice",
            ...     topic="AI ethics",
            ...     user_position="AI should be transparent and accountable",
            ...     quotes=["We need to ensure AI serves humanity, not the other way around"],
            ...     context="Deep discussion about AI alignment"
            ... )
        """
        logger.debug(f"Adding conversation for user {user_id} on topic: {topic}")

        try:
            # Generate entry ID based on timestamp and user
            timestamp = datetime.now()
            entry_id = f"conv_{user_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}"

            # Create conversation entry
            entry = ConversationEntry(
                entry_id=entry_id,
                topic=topic,
                user_id=user_id,
                user_position=user_position,
                quotes=quotes or [],
                timestamp=timestamp,
                context=context,
                metadata=metadata or {},
            )

            # Store as entity in Graphiti
            await self.adapter.add_entity(
                name=entry_id,
                entity_type="conversation",
                attributes=entry.to_dict(),
            )

            # Also store as an episode for temporal context
            episode_content = f"User {user_id} discussed '{topic}'"
            if user_position:
                episode_content += f". Position: {user_position}"
            if quotes:
                episode_content += f". Quotes: {'; '.join(quotes[:2])}"  # First 2 quotes

            await self.adapter.add_episode(
                name=entry_id,
                content=episode_content,
                episode_type="message",
                source_description=f"conversation_with_{user_id}",
                reference_time=timestamp,
                entity_references=[f"user:{user_id}", f"topic:{topic}"],
            )

            logger.info(f"Conversation entry stored: {entry_id}")
            return entry

        except Exception as e:
            logger.error(f"Failed to add conversation for {user_id}: {e}")
            raise

    async def get_conversation(self, entry_id: str) -> Optional[ConversationEntry]:
        """Retrieve a specific conversation entry from memory.

        Args:
            entry_id: Unique identifier for the conversation entry

        Returns:
            ConversationEntry if found, None otherwise

        Example:
            >>> memory = ConversationMemory()
            >>> entry = await memory.get_conversation("conv_alice_20240115_143000")
            >>> if entry:
            ...     print(f"Topic: {entry.topic}, Position: {entry.user_position}")
        """
        logger.debug(f"Retrieving conversation: {entry_id}")

        try:
            # Search for conversation entity
            results = await self.adapter.search_memory(
                query=entry_id,
                limit=1,
                entity_filter=["conversation"],
            )

            if not results:
                logger.debug(f"Conversation not found: {entry_id}")
                return None

            # Extract conversation data from first result
            conversation_data = results[0]

            # Parse conversation entry from attributes
            if "attributes" in conversation_data:
                entry = ConversationEntry.from_dict(conversation_data["attributes"])
                logger.debug(f"Conversation found: {entry_id}")
                return entry

            logger.debug(f"Conversation found but no attributes: {entry_id}")
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve conversation {entry_id}: {e}")
            raise

    async def get_conversations_by_user(
        self,
        user_id: str,
        limit: Optional[int] = None,
    ) -> List[ConversationEntry]:
        """Get all conversation entries for a specific user.

        Args:
            user_id: User identifier
            limit: Maximum number of entries to return (defaults to config limit)

        Returns:
            List of ConversationEntry instances for the user

        Example:
            >>> memory = ConversationMemory()
            >>> entries = await memory.get_conversations_by_user("alice", limit=10)
            >>> for entry in entries:
            ...     print(f"{entry.timestamp}: {entry.topic}")
        """
        logger.debug(f"Retrieving conversations for user: {user_id}")

        try:
            # Search for conversation entities for this user
            results = await self.adapter.search_memory(
                query=f"conversation user {user_id}",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["conversation"],
            )

            entries = []
            for result in results:
                if "attributes" in result:
                    try:
                        entry = ConversationEntry.from_dict(result["attributes"])

                        # Filter by user_id
                        if entry.user_id == user_id:
                            entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Failed to parse conversation entry: {e}")
                        continue

            # Sort by timestamp (most recent first)
            entries.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(entries)} conversations for user {user_id}")
            return entries

        except Exception as e:
# Backward compatible
            logger.error(f"Failed to retrieve conversations for user {user_id}: {e}")
            raise

    async def get_conversations_by_topic(
        self,
        topic: str,
        limit: Optional[int] = None,
    ) -> List[ConversationEntry]:
        """Get all conversation entries related to a specific topic.

        Args:
            topic: Topic to search for
            limit: Maximum number of entries to return (defaults to config limit)

        Returns:
            List of ConversationEntry instances related to the topic

        Example:
            >>> memory = ConversationMemory()
            >>> entries = await memory.get_conversations_by_topic("AI ethics")
            >>> for entry in entries:
            ...     print(f"{entry.user_id}: {entry.user_position}")
        """
        logger.debug(f"Retrieving conversations for topic: {topic}")

        try:
            # Search for conversation entities with this topic
            results = await self.adapter.search_memory(
                query=f"conversation topic {topic}",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["conversation"],
            )

            entries = []
            for result in results:
                if "attributes" in result:
                    try:
                        entry = ConversationEntry.from_dict(result["attributes"])

                        # Filter by topic (case-insensitive partial match)
                        if topic.lower() in entry.topic.lower():
                            entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Failed to parse conversation entry: {e}")
                        continue

            # Sort by timestamp (most recent first)
            entries.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(entries)} conversations for topic '{topic}'")
            return entries

        except Exception as e:
            logger.error(f"Failed to retrieve conversations for topic '{topic}': {e}")
            raise

    async def search_quotes(
        self,
        query: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Search for memorable quotes across all conversations.

        Args:
            query: Search query for quotes
            limit: Maximum number of results to return (defaults to config limit)

        Returns:
            List of dictionaries containing quote information:
            - quote: The quote text
            - entry_id: Conversation entry ID
            - user_id: User who said the quote
            - topic: Topic of the conversation
            - timestamp: When the quote was said

        Example:
            >>> memory = ConversationMemory()
            >>> quotes = await memory.search_quotes("humanity")
            >>> for q in quotes:
            ...     print(f"{q['user_id']}: {q['quote']} (Topic: {q['topic']})")
        """
        logger.debug(f"Searching quotes with query: {query}")

        try:
            # Search for conversation entities
            results = await self.adapter.search_memory(
                query=f"quote {query}",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["conversation"],
            )

            quotes = []
            for result in results:
                if "attributes" in result:
                    try:
                        entry = ConversationEntry.from_dict(result["attributes"])

                        # Search through quotes
                        for quote in entry.quotes:
                            if query.lower() in quote.lower():
                                quotes.append({
                                    "quote": quote,
                                    "entry_id": entry.entry_id,
                                    "user_id": entry.user_id,
                                    "topic": entry.topic,
                                    "timestamp": entry.timestamp.isoformat(),
                                })
                    except Exception as e:
                        logger.warning(f"Failed to parse conversation entry: {e}")
                        continue

            # Sort by timestamp (most recent first)
            quotes.sort(key=lambda x: x["timestamp"], reverse=True)

            logger.info(f"Found {len(quotes)} matching quotes")
            return quotes

        except Exception as e:
            logger.error(f"Failed to search quotes: {e}")
            raise

    async def add_quote_to_conversation(
        self,
        entry_id: str,
        quote: str,
    ) -> Optional[ConversationEntry]:
        """Add a memorable quote to an existing conversation entry.

        Args:
            entry_id: Unique identifier for the conversation entry
            quote: Quote text to add

        Returns:
            Updated ConversationEntry if entry exists, None otherwise

        Example:
            >>> memory = ConversationMemory()
            >>> entry = await memory.add_quote_to_conversation(
            ...     "conv_alice_20240115_143000",
            ...     "The future is not something we enter. The future is something we create."
            ... )
        """
        logger.debug(f"Adding quote to conversation: {entry_id}")

        try:
            # Get existing conversation
            existing = await self.get_conversation(entry_id)

            if not existing:
                logger.warning(f"Cannot add quote to non-existent conversation: {entry_id}")
                return None

            # Add quote
            existing.add_quote(quote)

            # Store updated conversation
            await self.adapter.add_entity(
                name=entry_id,
                entity_type="conversation",
                attributes=existing.to_dict(),
            )

            logger.info(f"Quote added to conversation: {entry_id}")
            return existing

        except Exception as e:
            logger.error(f"Failed to add quote to conversation {entry_id}: {e}")
            raise

    async def list_conversations(
        self,
        limit: Optional[int] = None,
    ) -> List[ConversationEntry]:
        """List all conversation entries in memory.

        Args:
            limit: Maximum number of entries to return (defaults to config limit)

        Returns:
            List of ConversationEntry instances

        Example:
            >>> memory = ConversationMemory()
            >>> entries = await memory.list_conversations(limit=20)
            >>> for entry in entries:
            ...     print(f"{entry.timestamp}: {entry.user_id} - {entry.topic}")
        """
        logger.debug("Listing conversations")

        try:
            # Search for all conversation entities
            results = await self.adapter.search_memory(
                query="conversation",
                limit=limit or self.config.graphiti_search_limit,
                entity_filter=["conversation"],
            )

            entries = []
            for result in results:
                if "attributes" in result:
                    try:
                        entry = ConversationEntry.from_dict(result["attributes"])
                        entries.append(entry)
                    except Exception as e:
                        logger.warning(f"Failed to parse conversation entry: {e}")
                        continue

            # Sort by timestamp (most recent first)
            entries.sort(key=lambda x: x.timestamp, reverse=True)

            logger.info(f"Found {len(entries)} conversations")
            return entries

        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            raise
