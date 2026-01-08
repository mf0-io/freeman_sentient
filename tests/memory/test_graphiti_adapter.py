"""Tests for GraphitiAdapter."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from src.memory.graphiti_adapter import GraphitiAdapter

try:
    from graphiti_core.nodes import EpisodeType
except ImportError:
    from unittest.mock import MagicMock
    EpisodeType = MagicMock()
    EpisodeType.message = "message"
    EpisodeType.event = "event"


@pytest.fixture
def mock_graphiti_client():
    """Create a mock Graphiti client."""
    client = MagicMock()

    # Mock async methods
    client.add_episode = AsyncMock()
    client.search = AsyncMock()
    client.close = AsyncMock()

    return client


@pytest.fixture
def mock_config():
    """Create a mock config."""
    config = MagicMock()
    config.get_neo4j_uri.return_value = "bolt://localhost:7687"
    config.graphiti_db_user = "neo4j"
    config.graphiti_db_password = "password"
    config.graphiti_db_name = "graphiti"
    config.graphiti_search_limit = 10
    return config


class TestGraphitiAdapterInitialization:
    """Test GraphitiAdapter initialization."""

    def test_init_without_client(self):
        """Test initialization without pre-configured client."""
        adapter = GraphitiAdapter()
        assert adapter._client is None
        assert adapter.config is not None

    def test_init_with_client(self, mock_graphiti_client):
        """Test initialization with pre-configured client."""
        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)
        assert adapter._client == mock_graphiti_client
        assert adapter.config is not None

    @patch('src.memory.graphiti_adapter.Graphiti')
    @patch('src.memory.graphiti_adapter.config')
    def test_lazy_client_initialization(self, mock_config_module, mock_graphiti_class):
        """Test lazy initialization of Graphiti client."""
        # Setup mock config
        mock_config_module.get_neo4j_uri.return_value = "bolt://localhost:7687"
        mock_config_module.graphiti_db_user = "neo4j"
        mock_config_module.graphiti_db_password = "password"
        mock_config_module.graphiti_db_name = "graphiti"

        # Create adapter without client
        adapter = GraphitiAdapter()
        assert adapter._client is None

        # Access client property should trigger initialization
        client = adapter.client

        # Verify Graphiti was initialized with correct parameters
        mock_graphiti_class.assert_called_once_with(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="password",
            database="graphiti"
        )
        assert adapter._client is not None

    @patch('src.memory.graphiti_adapter.Graphiti')
    @patch('src.memory.graphiti_adapter.config')
    def test_lazy_client_initialization_error(self, mock_config_module, mock_graphiti_class):
        """Test error handling during client initialization."""
        # Setup mock to raise exception
        mock_graphiti_class.side_effect = Exception("Connection failed")
        mock_config_module.get_neo4j_uri.return_value = "bolt://localhost:7687"

        adapter = GraphitiAdapter()

        # Accessing client should raise the exception
        with pytest.raises(Exception, match="Connection failed"):
            _ = adapter.client


class TestGraphitiAdapterAddEntity:
    """Test add_entity method."""

    @pytest.mark.asyncio
    async def test_add_entity_basic(self, mock_graphiti_client):
        """Test adding a basic entity."""
        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        entity_id = await adapter.add_entity(
            name="alice",
            entity_type="user"
        )

        assert entity_id == "user:alice"

    @pytest.mark.asyncio
    async def test_add_entity_with_attributes(self, mock_graphiti_client):
        """Test adding an entity with attributes."""
        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        attributes = {
            "platform": "telegram",
            "first_seen": "2024-01-15",
            "preferences": {"language": "en"}
        }

        entity_id = await adapter.add_entity(
            name="alice",
            entity_type="user",
            attributes=attributes
        )

        assert entity_id == "user:alice"

    @pytest.mark.asyncio
    async def test_add_entity_different_types(self, mock_graphiti_client):
        """Test adding entities of different types."""
        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        user_id = await adapter.add_entity(name="bob", entity_type="user")
        topic_id = await adapter.add_entity(name="AI ethics", entity_type="topic")
        place_id = await adapter.add_entity(name="digital_realm", entity_type="place")

        assert user_id == "user:bob"
        assert topic_id == "topic:AI ethics"
        assert place_id == "place:digital_realm"


class TestGraphitiAdapterAddEpisode:
    """Test add_episode method."""

    @pytest.mark.asyncio
    async def test_add_episode_basic(self, mock_graphiti_client):
        """Test adding a basic episode."""
        # Mock the return value
        mock_result = MagicMock()
        mock_result.uuid = "episode-123"
        mock_graphiti_client.add_episode.return_value = mock_result

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        episode_id = await adapter.add_episode(
            name="conversation_1",
            content="User alice asked about AI"
        )

        assert episode_id == "episode-123"
        mock_graphiti_client.add_episode.assert_called_once()

        # Verify call arguments
        call_args = mock_graphiti_client.add_episode.call_args
        assert call_args.kwargs['name'] == "conversation_1"
        assert call_args.kwargs['episode_body'] == "User alice asked about AI"
        assert call_args.kwargs['episode_type'] == EpisodeType.message

    @pytest.mark.asyncio
    async def test_add_episode_with_all_parameters(self, mock_graphiti_client):
        """Test adding an episode with all parameters."""
        mock_result = MagicMock()
        mock_result.uuid = "episode-456"
        mock_graphiti_client.add_episode.return_value = mock_result

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        reference_time = datetime(2024, 1, 15, 10, 30, 0)

        episode_id = await adapter.add_episode(
            name="conversation_2",
            content="Deep discussion about consciousness",
            episode_type="message",
            source_description="telegram_chat_123",
            reference_time=reference_time,
            entity_references=["user:alice", "topic:consciousness"]
        )

        assert episode_id == "episode-456"

        # Verify call arguments
        call_args = mock_graphiti_client.add_episode.call_args
        assert call_args.kwargs['name'] == "conversation_2"
        assert call_args.kwargs['episode_body'] == "Deep discussion about consciousness"
        assert call_args.kwargs['source_description'] == "telegram_chat_123"
        assert call_args.kwargs['reference_time'] == reference_time
        assert call_args.kwargs['episode_type'] == EpisodeType.message

    @pytest.mark.asyncio
    async def test_add_episode_event_type(self, mock_graphiti_client):
        """Test adding an episode with event type."""
        mock_result = MagicMock()
        mock_result.uuid = "episode-789"
        mock_graphiti_client.add_episode.return_value = mock_result

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        episode_id = await adapter.add_episode(
            name="token_purchase",
            content="User purchased 100 tokens",
            episode_type="event"
        )

        assert episode_id == "episode-789"

        # Verify episode type is event
        call_args = mock_graphiti_client.add_episode.call_args
        assert call_args.kwargs['episode_type'] == EpisodeType.event

    @pytest.mark.asyncio
    async def test_add_episode_default_timestamp(self, mock_graphiti_client):
        """Test that episode uses current time when not specified."""
        mock_result = MagicMock()
        mock_result.uuid = "episode-999"
        mock_graphiti_client.add_episode.return_value = mock_result

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        before = datetime.now()
        await adapter.add_episode(
            name="test_episode",
            content="Test content"
        )
        after = datetime.now()

        # Verify timestamp is between before and after
        call_args = mock_graphiti_client.add_episode.call_args
        timestamp = call_args.kwargs['reference_time']
        assert before <= timestamp <= after

    @pytest.mark.asyncio
    async def test_add_episode_no_uuid_in_result(self, mock_graphiti_client):
        """Test handling when result doesn't have uuid attribute."""
        mock_result = MagicMock(spec=[])  # No attributes
        mock_graphiti_client.add_episode.return_value = mock_result

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        episode_id = await adapter.add_episode(
            name="test_episode",
            content="Test content"
        )

        # Should fall back to using the name
        assert episode_id == "test_episode"

    @pytest.mark.asyncio
    async def test_add_episode_error_handling(self, mock_graphiti_client):
        """Test error handling in add_episode."""
        mock_graphiti_client.add_episode.side_effect = Exception("Database error")

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        with pytest.raises(Exception, match="Database error"):
            await adapter.add_episode(
                name="test_episode",
                content="Test content"
            )


class TestGraphitiAdapterSearch:
    """Test search_memory method."""

    @pytest.mark.asyncio
    async def test_search_memory_basic(self, mock_graphiti_client):
        """Test basic memory search."""
        # Mock search results
        mock_result1 = MagicMock()
        mock_result1.content = "Freeman discussed AI ethics"
        mock_result1.score = 0.95
        mock_result1.episode_id = "ep-1"
        mock_result1.created_at = datetime(2024, 1, 15)
        mock_result1.metadata = {"user": "alice"}

        mock_result2 = MagicMock()
        mock_result2.content = "Freeman talked about consciousness"
        mock_result2.score = 0.87
        mock_result2.episode_id = "ep-2"
        mock_result2.created_at = datetime(2024, 1, 16)
        mock_result2.metadata = {"user": "bob"}

        mock_graphiti_client.search.return_value = [mock_result1, mock_result2]

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        results = await adapter.search_memory(
            query="What does Freeman think about AI?",
            limit=5
        )

        assert len(results) == 2

        # Verify first result
        assert results[0]["content"] == "Freeman discussed AI ethics"
        assert results[0]["score"] == 0.95
        assert results[0]["episode_id"] == "ep-1"
        assert results[0]["timestamp"] == datetime(2024, 1, 15)
        assert results[0]["metadata"] == {"user": "alice"}

        # Verify second result
        assert results[1]["content"] == "Freeman talked about consciousness"
        assert results[1]["score"] == 0.87

        # Verify client was called correctly
        mock_graphiti_client.search.assert_called_once_with(
            query="What does Freeman think about AI?",
            num_results=5
        )

    @pytest.mark.asyncio
    async def test_search_memory_default_limit(self, mock_graphiti_client, mock_config):
        """Test search with default limit from config."""
        mock_graphiti_client.search.return_value = []

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)
        adapter.config = mock_config

        await adapter.search_memory(query="test query")

        # Should use config's default limit
        mock_graphiti_client.search.assert_called_once_with(
            query="test query",
            num_results=10
        )

    @pytest.mark.asyncio
    async def test_search_memory_empty_results(self, mock_graphiti_client):
        """Test search with no results."""
        mock_graphiti_client.search.return_value = []

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        results = await adapter.search_memory(
            query="nonexistent topic",
            limit=5
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_search_memory_missing_attributes(self, mock_graphiti_client):
        """Test search with results missing some attributes."""
        mock_result = MagicMock(spec=['content'])  # Only has content
        mock_result.content = "Partial result"

        mock_graphiti_client.search.return_value = [mock_result]

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        results = await adapter.search_memory(query="test", limit=5)

        assert len(results) == 1
        assert results[0]["content"] == "Partial result"
        assert results[0]["score"] == 0.0  # Default value
        assert results[0]["episode_id"] is None
        assert results[0]["timestamp"] is None
        assert results[0]["metadata"] == {}

    @pytest.mark.asyncio
    async def test_search_memory_error_handling(self, mock_graphiti_client):
        """Test error handling in search."""
        mock_graphiti_client.search.side_effect = Exception("Search failed")

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        with pytest.raises(Exception, match="Search failed"):
            await adapter.search_memory(query="test", limit=5)


class TestGraphitiAdapterGetContext:
    """Test get_context method."""

    @pytest.mark.asyncio
    async def test_get_context_basic(self, mock_graphiti_client):
        """Test retrieving context for an entity."""
        # Mock search results
        mock_result = MagicMock()
        mock_result.content = "Alice discussed AI with Freeman"
        mock_result.score = 0.95
        mock_result.episode_id = "ep-1"
        mock_result.created_at = datetime(2024, 1, 15)
        mock_result.metadata = {}

        mock_graphiti_client.search.return_value = [mock_result]

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        context = await adapter.get_context(
            entity_id="user:alice",
            context_window=10
        )

        assert context["entity_id"] == "user:alice"
        assert context["episode_count"] == 1
        assert len(context["recent_episodes"]) == 1
        assert context["last_interaction"] == datetime(2024, 1, 15)

    @pytest.mark.asyncio
    async def test_get_context_no_episodes(self, mock_graphiti_client):
        """Test getting context when no episodes exist."""
        mock_graphiti_client.search.return_value = []

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        context = await adapter.get_context(entity_id="user:newuser")

        assert context["entity_id"] == "user:newuser"
        assert context["episode_count"] == 0
        assert context["recent_episodes"] == []
        assert context["last_interaction"] is None

    @pytest.mark.asyncio
    async def test_get_context_entity_name_extraction(self, mock_graphiti_client):
        """Test that entity name is correctly extracted for search."""
        mock_graphiti_client.search.return_value = []

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        await adapter.get_context(entity_id="user:alice")

        # Should extract 'alice' from 'user:alice' for search query
        mock_graphiti_client.search.assert_called_once()
        call_args = mock_graphiti_client.search.call_args
        assert call_args.kwargs['query'] == "alice"

    @pytest.mark.asyncio
    async def test_get_context_error_handling(self, mock_graphiti_client):
        """Test error handling in get_context."""
        mock_graphiti_client.search.side_effect = Exception("Context retrieval failed")

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        with pytest.raises(Exception, match="Context retrieval failed"):
            await adapter.get_context(entity_id="user:alice")


class TestGraphitiAdapterHealthCheck:
    """Test health_check method."""

    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_graphiti_client, mock_config):
        """Test health check with healthy connection."""
        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)
        adapter.config = mock_config

        health = await adapter.health_check()

        assert health["status"] == "healthy"
        assert health["graphiti_initialized"] is True
        assert health["neo4j_uri"] == "bolt://localhost:7687"
        assert health["error"] is None

    @pytest.mark.asyncio
    @patch('src.memory.graphiti_adapter.config')
    async def test_health_check_uninitialized(self, mock_config_module):
        """Test health check before client initialization."""
        mock_config_module.get_neo4j_uri.return_value = "bolt://localhost:7687"

        adapter = GraphitiAdapter()

        # Should still return status
        health = await adapter.health_check()

        # Status depends on whether initialization succeeds
        assert "status" in health
        assert "graphiti_initialized" in health
        assert "neo4j_uri" in health

    @pytest.mark.asyncio
    @patch('src.memory.graphiti_adapter.Graphiti')
    @patch('src.memory.graphiti_adapter.config')
    async def test_health_check_unhealthy(self, mock_config_module, mock_graphiti_class):
        """Test health check with connection failure."""
        mock_graphiti_class.side_effect = Exception("Connection refused")
        mock_config_module.get_neo4j_uri.return_value = "bolt://localhost:7687"

        adapter = GraphitiAdapter()

        health = await adapter.health_check()

        assert health["status"] == "unhealthy"
        assert "Connection refused" in health["error"]


class TestGraphitiAdapterClose:
    """Test close method and context manager."""

    @pytest.mark.asyncio
    async def test_close_with_client(self, mock_graphiti_client):
        """Test closing adapter with initialized client."""
        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        await adapter.close()

        mock_graphiti_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test closing adapter without initialized client."""
        adapter = GraphitiAdapter()

        # Should not raise an error
        await adapter.close()

    @pytest.mark.asyncio
    async def test_close_error_handling(self, mock_graphiti_client):
        """Test error handling during close."""
        mock_graphiti_client.close.side_effect = Exception("Close failed")

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        with pytest.raises(Exception, match="Close failed"):
            await adapter.close()

    @pytest.mark.asyncio
    async def test_context_manager_basic(self, mock_graphiti_client):
        """Test using adapter as async context manager."""
        adapter_instance = None

        async with GraphitiAdapter(graphiti_client=mock_graphiti_client) as adapter:
            adapter_instance = adapter
            assert adapter._client == mock_graphiti_client

        # Verify close was called on exit
        mock_graphiti_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self, mock_graphiti_client):
        """Test context manager cleanup on exception."""
        try:
            async with GraphitiAdapter(graphiti_client=mock_graphiti_client) as adapter:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Close should still be called
        mock_graphiti_client.close.assert_called_once()


class TestGraphitiAdapterEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_multiple_operations_sequence(self, mock_graphiti_client):
        """Test sequence of multiple operations."""
        # Setup mock returns
        mock_episode_result = MagicMock()
        mock_episode_result.uuid = "ep-1"
        mock_graphiti_client.add_episode.return_value = mock_episode_result

        mock_search_result = MagicMock()
        mock_search_result.content = "Test content"
        mock_search_result.score = 0.9
        mock_search_result.episode_id = "ep-1"
        mock_search_result.created_at = datetime.now()
        mock_search_result.metadata = {}
        mock_graphiti_client.search.return_value = [mock_search_result]

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        # Add entity
        entity_id = await adapter.add_entity(name="alice", entity_type="user")
        assert entity_id == "user:alice"

        # Add episode
        episode_id = await adapter.add_episode(
            name="conv_1",
            content="Test conversation"
        )
        assert episode_id == "ep-1"

        # Search
        results = await adapter.search_memory(query="test", limit=5)
        assert len(results) == 1

        # Get context
        context = await adapter.get_context(entity_id="user:alice")
        assert context["entity_id"] == "user:alice"
        assert context["episode_count"] == 1

    @pytest.mark.asyncio
    async def test_entity_with_empty_name(self, mock_graphiti_client):
        """Test handling entity with empty name."""
        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        # Should still work, just creates an odd ID
        entity_id = await adapter.add_entity(name="", entity_type="user")
        assert entity_id == "user:"

    @pytest.mark.asyncio
    async def test_episode_with_empty_content(self, mock_graphiti_client):
        """Test handling episode with empty content."""
        mock_result = MagicMock()
        mock_result.uuid = "ep-empty"
        mock_graphiti_client.add_episode.return_value = mock_result

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        episode_id = await adapter.add_episode(
            name="empty_episode",
            content=""
        )

        assert episode_id == "ep-empty"

        # Verify empty content was passed
        call_args = mock_graphiti_client.add_episode.call_args
        assert call_args.kwargs['episode_body'] == ""

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self, mock_graphiti_client):
        """Test search with empty query string."""
        mock_graphiti_client.search.return_value = []

        adapter = GraphitiAdapter(graphiti_client=mock_graphiti_client)

        results = await adapter.search_memory(query="", limit=5)

        # Should execute search with empty query
        assert results == []
        mock_graphiti_client.search.assert_called_once_with(
            query="",
            num_results=5
        )
