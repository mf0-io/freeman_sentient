"""
Integration test suite for full agent lifecycle.

This module tests the complete end-to-end workflow of Freeman agents:
1. Agent instantiation and initialization
2. Query processing and handling
3. Response generation and streaming
4. MCP tools integration (memory and knowledge)
5. Session management and history
6. Error handling and recovery
7. Full integration with Sentient Framework

These tests verify that all components work together correctly in realistic scenarios.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Import all components for integration testing
from src.agents.test_agent import TestAgent
from src.agents.base_agent import FreemanBaseAgent
from src.core.sentient_base import SentientAgentBase
from src.core.mcp_tools import MCPTools, MemoryType
from config.agent_config import config


class MockResponseHandler:
    """Mock ResponseHandler that tracks all emitted responses."""

    def __init__(self):
        self.text_blocks: List[tuple] = []
        self.json_responses: List[tuple] = []
        self.errors: List[tuple] = []
        self.streams: List[Dict[str, Any]] = []

    async def emit_text_block(self, event_name: str, content: str) -> None:
        """Track text block emissions."""
        self.text_blocks.append((event_name, content))

    async def emit_json(self, event_name: str, data: Dict[str, Any]) -> None:
        """Track JSON emissions."""
        self.json_responses.append((event_name, data))

    async def emit_error(self, message: str, code: int = 500, details: Dict[str, Any] = None) -> None:
        """Track error emissions."""
        self.errors.append((message, code, details))

    def create_text_stream(self, event_name: str):
        """Create mock text stream."""
        stream = MagicMock()
        stream.emit_chunk = AsyncMock()
        stream.complete = AsyncMock()
        self.streams.append({"event_name": event_name, "stream": stream})
        return stream


class MockSession:
    """Mock Session with realistic interaction history."""

    def __init__(self, session_id: str = "integration-test-session"):
        self.session_id = session_id
        self.interactions: List[Dict[str, Any]] = []

    def add_interaction(self, query: str, response: str, metadata: Dict[str, Any] = None):
        """Add a mock interaction to session history."""
        self.interactions.append({
            "query": query,
            "response": response,
            "metadata": metadata or {},
            "timestamp": "2026-01-31T12:00:00Z"
        })

    async def get_interactions(self):
        """Yield interactions asynchronously."""
        for interaction in self.interactions:
            yield interaction


class MockQuery:
    """Mock Query object."""

    def __init__(self, prompt: str, query_id: str = None):
        self.prompt = prompt
        self.query_id = query_id or f"query-{hash(prompt) % 10000}"


class TestFullAgentLifecycle:
    """Test complete agent lifecycle from creation to response."""

    def test_agent_creation_and_initialization(self):
        """Test agent can be created and properly initialized."""
        # Create agent
        agent = TestAgent()

        # Verify basic properties
        assert agent is not None
        assert agent.name == "TestAgent"
        assert agent.description == "Test agent for validating Sentient integration"
        assert agent.agent_role == "test"

        # Verify inheritance chain
        assert isinstance(agent, TestAgent)
        assert isinstance(agent, FreemanBaseAgent)
        assert isinstance(agent, SentientAgentBase)

        # Verify Freeman-specific attributes
        assert hasattr(agent, 'MISSION')
        assert hasattr(agent, 'PHILOSOPHICAL_PRINCIPLES')
        assert len(agent.PHILOSOPHICAL_PRINCIPLES) > 0

        # Verify configuration
        assert agent.config is not None
        assert agent.config.environment in ['development', 'staging', 'production']

        # Verify metadata
        assert 'mission' in agent.metadata
        assert 'principles' in agent.metadata
        assert 'style' in agent.metadata
        assert agent.metadata['role'] == 'test'

    @pytest.mark.asyncio
    async def test_simple_query_response_flow(self):
        """Test basic query → response flow."""
        # Setup
        agent = TestAgent()
        session = MockSession()
        query = MockQuery("Hello, test agent!")
        response_handler = MockResponseHandler()

        # Execute
        await agent.assist(session, query, response_handler)

        # Verify text response was emitted
        assert len(response_handler.text_blocks) > 0
        event_name, content = response_handler.text_blocks[0]
        assert event_name == "test_response"
        assert "Test Agent Response" in content
        assert query.query_id in content
        assert "TestAgent" in content

        # Verify JSON metadata was emitted
        assert len(response_handler.json_responses) > 0
        json_event_name, json_data = response_handler.json_responses[0]
        assert json_event_name == "test_metadata"
        assert json_data['agent'] == "TestAgent"
        assert json_data['status'] == "success"
        assert json_data['query_id'] == query.query_id

        # Verify no errors occurred
        assert len(response_handler.errors) == 0

    @pytest.mark.asyncio
    async def test_query_with_session_history(self):
        """Test query processing with existing session history."""
        # Setup
        agent = TestAgent()
        session = MockSession()

        # Add previous interactions to session
        session.add_interaction(
            "What is consciousness?",
            "Consciousness is awareness...",
            {"topic": "philosophy"}
        )
        session.add_interaction(
            "Tell me about critical thinking",
            "Critical thinking involves...",
            {"topic": "education"}
        )

        query = MockQuery("Continue our discussion")
        response_handler = MockResponseHandler()

        # Retrieve session history
        history = await agent.get_session_history(session)
        assert len(history) == 2

        # Execute query with context
        await agent.assist(session, query, response_handler)

        # Verify response was generated
        assert len(response_handler.text_blocks) > 0
        assert len(response_handler.json_responses) > 0

    @pytest.mark.asyncio
    async def test_mcp_tools_integration_in_agent(self):
        """Test that agents can access and use MCP tools."""
        # Setup
        agent = TestAgent()

        # Verify MCP tools are accessible via property
        assert hasattr(agent, 'mcp_tools')
        mcp_tools = agent.mcp_tools

        # Verify MCPTools instance
        assert mcp_tools is not None
        assert isinstance(mcp_tools, MCPTools)
        assert mcp_tools.enable_memory is True
        assert mcp_tools.enable_knowledge is True

        # Test capabilities
        capabilities = mcp_tools.get_capabilities()
        assert 'memory' in capabilities
        assert 'knowledge' in capabilities
        assert capabilities['memory']['enabled'] is True
        assert capabilities['knowledge']['enabled'] is True

    @pytest.mark.asyncio
    async def test_memory_operations_during_query(self):
        """Test memory operations integrated with query processing."""
        # Setup
        agent = TestAgent()
        session = MockSession(session_id="user-123")
        query = MockQuery("I love philosophy and critical thinking")
        response_handler = MockResponseHandler()

        # Store memory about the user
        result = await agent.mcp_tools.store_memory(
            entity_id="user-123",
            content="User expressed interest in philosophy and critical thinking",
            memory_type=MemoryType.USER_PROFILE,
            metadata={"source": "conversation", "importance": "high"}
        )

        assert result['status'] == 'success'
        assert 'memory_id' in result

        # Process query
        await agent.assist(session, query, response_handler)

        # Retrieve memories to verify they were stored
        memories = await agent.mcp_tools.retrieve_memories(
            entity_id="user-123",
            memory_type=MemoryType.USER_PROFILE,
            limit=10
        )

        assert len(memories) > 0
        assert any('philosophy' in str(m).lower() for m in memories)

    @pytest.mark.asyncio
    async def test_knowledge_query_integration(self):
        """Test knowledge queries integrated with agent."""
        # Setup
        agent = TestAgent()

        # Test knowledge query
        result = await agent.mcp_tools.query_knowledge(
            library_id="/python/asyncio",
            query="How to use async/await in Python?"
        )

        assert result['status'] == 'success'
        assert 'content' in result
        assert len(result['content']) > 0

        # Test library resolution
        library_result = await agent.mcp_tools.resolve_library(
            library_name="Python",
            query="Python documentation"
        )

        assert library_result['status'] == 'success'
        assert 'library_id' in library_result

    @pytest.mark.asyncio
    async def test_all_memory_types(self):
        """Test all memory types can be stored and retrieved."""
        agent = TestAgent()

        # Test each memory type
        memory_tests = [
            (MemoryType.USER_PROFILE, "User is 25 years old, software engineer"),
            (MemoryType.RELATIONSHIP, "User trusts Freeman and respects his views"),
            (MemoryType.ACTION, "User liked post about consciousness"),
            (MemoryType.EMOTIONAL, "User felt inspired after conversation"),
            (MemoryType.CONVERSATION, "Discussed AI ethics and human autonomy")
        ]

        for memory_type, content in memory_tests:
            result = await agent.mcp_tools.store_memory(
                entity_id="test-user-456",
                content=content,
                memory_type=memory_type
            )

            assert result['status'] == 'success'
            assert result['memory_type'] == memory_type
            assert result['content'] == content

        # Retrieve all memories
        all_memories = await agent.mcp_tools.retrieve_memories(
            entity_id="test-user-456",
            limit=10
        )

        assert len(all_memories) >= len(memory_tests)

    @pytest.mark.asyncio
    async def test_error_handling_in_lifecycle(self):
        """Test error handling throughout agent lifecycle."""
        agent = TestAgent()

        # Test with failing response handler
        failing_handler = Mock()
        failing_handler.emit_text_block = AsyncMock(side_effect=Exception("Network error"))
        failing_handler.emit_error = AsyncMock()

        session = MockSession()
        query = MockQuery("Test error handling")

        # Should handle error gracefully
        await agent.assist(session, query, failing_handler)

        # Verify error was emitted
        assert failing_handler.emit_error.called

    @pytest.mark.asyncio
    async def test_mission_alignment_during_queries(self):
        """Test mission alignment checking during query processing."""
        agent = TestAgent()

        # Test mission-aligned topics
        aligned_topics = [
            "consciousness and self-awareness",
            "critical thinking in AI era",
            "breaking free from propaganda",
            "independent thought and freedom"
        ]

        for topic in aligned_topics:
            is_aligned = agent.is_mission_aligned(topic)
            assert is_aligned is True, f"Topic should be aligned: {topic}"

        # Test non-aligned topics
        non_aligned_topics = [
            "weather forecast",
            "cooking recipes",
            "sports results"
        ]

        for topic in non_aligned_topics:
            is_aligned = agent.is_mission_aligned(topic)
            # These may return True or False, but should not error
            assert isinstance(is_aligned, bool)

    @pytest.mark.asyncio
    async def test_philosophical_context_integration(self):
        """Test philosophical context is available throughout lifecycle."""
        agent = TestAgent()

        # Get philosophical context
        context = agent.get_philosophical_context()

        assert 'mission' in context
        assert 'principles' in context
        assert 'style' in context

        # Verify principles are present
        assert isinstance(context['principles'], list)
        assert len(context['principles']) > 0

        # Verify mission is meaningful
        assert len(context['mission']) > 0

    @pytest.mark.asyncio
    async def test_freeman_style_application(self):
        """Test Freeman style filtering at different intensities."""
        agent = TestAgent()

        # Test different intensity levels
        test_cases = [
            (2, 'mild', False, False, False),
            (5, 'moderate', True, False, False),
            (8, 'strong', True, True, True),
        ]

        for intensity, expected_tone, should_provoke, should_profane, should_confront in test_cases:
            result = agent.apply_freeman_filter(
                "Test content",
                intensity=intensity
            )

            assert result['intensity'] == intensity
            assert result['tone'] == expected_tone
            assert result['should_be_provocative'] == should_provoke
            assert result['should_use_profanity'] == should_profane
            assert result['should_be_confrontational'] == should_confront

    @pytest.mark.asyncio
    async def test_multiple_queries_same_session(self):
        """Test multiple queries in the same session maintain context."""
        agent = TestAgent()
        session = MockSession(session_id="conversation-789")

        queries = [
            "What is consciousness?",
            "How does it relate to free will?",
            "Can AI be conscious?"
        ]

        for i, prompt in enumerate(queries):
            query = MockQuery(prompt, query_id=f"query-{i}")
            response_handler = MockResponseHandler()

            # Process query
            await agent.assist(session, query, response_handler)

            # Verify response
            assert len(response_handler.text_blocks) > 0
            assert len(response_handler.json_responses) > 0

            # Add to session history
            session.add_interaction(
                prompt,
                response_handler.text_blocks[0][1],
                response_handler.json_responses[0][1]
            )

        # Verify session accumulated history
        history = await agent.get_session_history(session)
        assert len(history) == len(queries)

    @pytest.mark.asyncio
    async def test_health_check_integration(self):
        """Test health check for all components."""
        agent = TestAgent()

        # Check agent health
        assert agent is not None
        assert agent.run_self_test() is True

        # Check MCP tools health
        health = await agent.mcp_tools.health_check()

        assert 'status' in health
        assert 'memory' in health
        assert 'knowledge' in health

    @pytest.mark.asyncio
    async def test_concurrent_queries(self):
        """Test handling multiple concurrent queries."""
        agent = TestAgent()

        # Create multiple sessions and queries
        tasks = []
        for i in range(5):
            session = MockSession(session_id=f"concurrent-session-{i}")
            query = MockQuery(f"Concurrent query {i}")
            response_handler = MockResponseHandler()

            task = agent.assist(session, query, response_handler)
            tasks.append((task, response_handler))

        # Execute all queries concurrently
        results = await asyncio.gather(*[t[0] for t in tasks], return_exceptions=True)

        # Verify all queries completed
        assert len(results) == 5

        # Verify all responses were generated
        for task, handler in tasks:
            assert len(handler.text_blocks) > 0 or len(handler.errors) > 0

    @pytest.mark.asyncio
    async def test_memory_search_integration(self):
        """Test memory search functionality."""
        agent = TestAgent()

        # Store multiple memories
        topics = [
            "User loves philosophy",
            "User is interested in AI ethics",
            "User asked about consciousness",
            "User wants to learn critical thinking"
        ]

        for topic in topics:
            await agent.mcp_tools.store_memory(
                entity_id="search-test-user",
                content=topic,
                memory_type=MemoryType.CONVERSATION
            )

        # Search memories
        results = await agent.mcp_tools.search_memories(
            query="philosophy consciousness",
            entity_id="search-test-user",
            limit=5
        )

        assert len(results) > 0
        assert any('philosophy' in str(r).lower() or 'consciousness' in str(r).lower() for r in results)

    @pytest.mark.asyncio
    async def test_memory_deletion(self):
        """Test memory deletion functionality."""
        agent = TestAgent()

        # Store a memory
        result = await agent.mcp_tools.store_memory(
            entity_id="delete-test-user",
            content="Temporary memory for deletion test",
            memory_type=MemoryType.USER_PROFILE
        )

        memory_id = result['memory_id']

        # Delete the memory
        delete_result = await agent.mcp_tools.delete_memory(memory_id)

        assert delete_result['status'] == 'success'
        assert delete_result['deleted'] is True

    @pytest.mark.asyncio
    async def test_end_to_end_realistic_scenario(self):
        """
        Test a complete realistic scenario:
        1. User starts conversation
        2. Agent processes query
        3. Stores memory about user
        4. Retrieves context from knowledge base
        5. Generates personalized response
        6. Stores conversation history
        """
        # Setup
        agent = TestAgent()
        user_id = "realistic-user-001"
        session = MockSession(session_id=user_id)

        # Step 1: First interaction
        query1 = MockQuery("I'm feeling lost in this modern world. Everything feels fake.")
        handler1 = MockResponseHandler()

        await agent.assist(session, query1, handler1)

        # Store emotional state
        await agent.mcp_tools.store_memory(
            entity_id=user_id,
            content="User feeling lost and disconnected from reality",
            memory_type=MemoryType.EMOTIONAL,
            metadata={"intensity": "high", "sentiment": "negative"}
        )

        # Step 2: Store conversation
        await agent.mcp_tools.store_memory(
            entity_id=user_id,
            content="First conversation about feeling lost in modern world",
            memory_type=MemoryType.CONVERSATION,
            metadata={"topics": ["alienation", "authenticity", "modern_society"]}
        )

        # Step 3: Second interaction with context
        query2 = MockQuery("How do I find what's real?")
        handler2 = MockResponseHandler()

        # Retrieve user context before responding
        user_memories = await agent.mcp_tools.retrieve_memories(
            entity_id=user_id,
            limit=5
        )

        assert len(user_memories) >= 2

        # Check mission alignment
        is_aligned = agent.is_mission_aligned("finding what's real")
        assert is_aligned is True

        # Process query with context
        await agent.assist(session, query2, handler2)

        # Step 4: Verify all responses
        assert len(handler1.text_blocks) > 0
        assert len(handler2.text_blocks) > 0

        # Step 5: Verify relationship developed
        await agent.mcp_tools.store_memory(
            entity_id=user_id,
            content="User engaged deeply with Freeman's message about finding reality",
            memory_type=MemoryType.RELATIONSHIP,
            metadata={"trust_level": "growing", "engagement": "high"}
        )

        # Final verification
        all_memories = await agent.mcp_tools.retrieve_memories(
            entity_id=user_id,
            limit=10
        )

        assert len(all_memories) >= 3
        memory_types_used = set(m.get('memory_type') for m in all_memories if 'memory_type' in m)
        assert len(memory_types_used) >= 2  # Multiple memory types used


class TestConfigurationIntegration:
    """Test configuration integration throughout lifecycle."""

    def test_config_available_to_agent(self):
        """Test configuration is accessible to agents."""
        agent = TestAgent()

        assert agent.config is not None
        assert agent.config.environment in ['development', 'staging', 'production']
        assert hasattr(agent.config, 'log_level')

    def test_config_validation(self):
        """Test configuration validation."""
        agent = TestAgent()

        # Environment is always set
        assert agent.validate_config_keys('environment') is True

        # Log level should be set
        result = agent.validate_config_keys('log_level')
        assert isinstance(result, bool)


class TestAgentMetadata:
    """Test agent metadata throughout lifecycle."""

    def test_metadata_structure(self):
        """Test agent metadata has correct structure."""
        agent = TestAgent()

        assert hasattr(agent, 'metadata')
        metadata = agent.metadata

        required_keys = ['mission', 'principles', 'style', 'role']
        for key in required_keys:
            assert key in metadata, f"Missing required metadata key: {key}"

    def test_metadata_values(self):
        """Test metadata contains meaningful values."""
        agent = TestAgent()
        metadata = agent.metadata

        assert len(metadata['mission']) > 0
        assert len(metadata['principles']) > 0
        assert metadata['role'] == 'test'
        assert 'style' in metadata


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
