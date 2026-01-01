"""
Test suite for Sentient Agent Framework integration.

This module tests the core integration of the Sentient Agent Framework
with Freeman's agent system, including agent instantiation, query processing,
response handling, and Freeman-specific functionality.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Import the agents and framework components
from src.agents.test_agent import TestAgent
from src.agents.base_agent import FreemanBaseAgent
from src.core.sentient_base import SentientAgentBase
from config.agent_config import config


class MockResponseHandler:
    """Mock ResponseHandler for testing."""

    def __init__(self):
        self.text_blocks: List[tuple] = []
        self.json_responses: List[tuple] = []
        self.errors: List[tuple] = []
        self.streams: List[Dict[str, Any]] = []

    async def emit_text_block(self, event_name: str, content: str) -> None:
        """Mock emit_text_block method."""
        self.text_blocks.append((event_name, content))

    async def emit_json(self, event_name: str, data: Dict[str, Any]) -> None:
        """Mock emit_json method."""
        self.json_responses.append((event_name, data))

    async def emit_error(self, message: str, code: int = 500, details: Dict[str, Any] = None) -> None:
        """Mock emit_error method."""
        self.errors.append((message, code, details))

    def create_text_stream(self, event_name: str):
        """Mock create_text_stream method."""
        stream = MagicMock()
        stream.emit_chunk = AsyncMock()
        stream.complete = AsyncMock()
        self.streams.append({"event_name": event_name, "stream": stream})
        return stream


class MockSession:
    """Mock Session for testing."""

    def __init__(self, session_id: str = "test-session-123"):
        self.session_id = session_id
        self.interactions: List[Any] = []

    async def get_interactions(self):
        """Mock get_interactions method."""
        for interaction in self.interactions:
            yield interaction


class MockQuery:
    """Mock Query for testing."""

    def __init__(self, prompt: str, query_id: str = "test-query-456"):
        self.prompt = prompt
        self.query_id = query_id


class TestSentientIntegration:
    """Test suite for Sentient Agent Framework integration."""

    def test_test_agent_instantiation(self):
        """Test that TestAgent can be instantiated successfully."""
        agent = TestAgent()

        assert agent is not None
        assert agent.name == "TestAgent"
        assert agent.description == "Test agent for validating Sentient integration"
        assert agent.agent_role == "test"
        assert isinstance(agent, FreemanBaseAgent)
        assert isinstance(agent, SentientAgentBase)

    def test_agent_has_freeman_mission(self):
        """Test that agent has Freeman mission and principles."""
        agent = TestAgent()

        assert hasattr(agent, 'MISSION')
        assert hasattr(agent, 'PHILOSOPHICAL_PRINCIPLES')
        assert len(agent.PHILOSOPHICAL_PRINCIPLES) > 0
        assert "consciousness" in agent.MISSION.lower()

    def test_agent_has_config(self):
        """Test that agent has access to configuration."""
        agent = TestAgent()

        assert hasattr(agent, 'config')
        assert agent.config is not None
        assert agent.config.environment in ['development', 'staging', 'production']

    def test_agent_metadata(self):
        """Test that agent metadata is properly initialized."""
        agent = TestAgent()

        assert hasattr(agent, 'metadata')
        assert 'mission' in agent.metadata
        assert 'principles' in agent.metadata
        assert 'style' in agent.metadata
        assert 'role' in agent.metadata
        assert agent.metadata['role'] == 'test'

    def test_agent_self_test(self):
        """Test the agent's self-test functionality."""
        agent = TestAgent()

        result = agent.run_self_test()

        assert result is True

    @pytest.mark.asyncio
    async def test_assist_method_basic_response(self):
        """Test that assist() method processes queries and generates responses."""
        agent = TestAgent()
        session = MockSession()
        query = MockQuery("Hello, are you working?")
        response_handler = MockResponseHandler()

        await agent.assist(session, query, response_handler)

        # Verify text response was emitted
        assert len(response_handler.text_blocks) > 0
        event_name, content = response_handler.text_blocks[0]
        assert event_name == "test_response"
        assert "Test Agent Response" in content
        assert query.query_id in content
        assert agent.name in content

        # Verify JSON metadata was emitted
        assert len(response_handler.json_responses) > 0
        json_event_name, json_data = response_handler.json_responses[0]
        assert json_event_name == "test_metadata"
        assert json_data['agent'] == "TestAgent"
        assert json_data['status'] == "success"
        assert json_data['query_id'] == query.query_id

    @pytest.mark.asyncio
    async def test_assist_method_with_long_prompt(self):
        """Test assist() handles long prompts correctly."""
        agent = TestAgent()
        session = MockSession()
        long_prompt = "A" * 200  # Create a 200-character prompt
        query = MockQuery(long_prompt)
        response_handler = MockResponseHandler()

        await agent.assist(session, query, response_handler)

        # Verify response was generated
        assert len(response_handler.text_blocks) > 0
        event_name, content = response_handler.text_blocks[0]
        # Long prompts should be truncated in display
        assert "..." in content

    @pytest.mark.asyncio
    async def test_emit_text_helper(self):
        """Test the emit_text helper method."""
        agent = TestAgent()
        response_handler = MockResponseHandler()

        await agent.emit_text(response_handler, "Test message", event_name="custom_event")

        assert len(response_handler.text_blocks) == 1
        event_name, content = response_handler.text_blocks[0]
        assert event_name == "custom_event"
        assert content == "Test message"

    @pytest.mark.asyncio
    async def test_emit_json_helper(self):
        """Test the emit_json helper method."""
        agent = TestAgent()
        response_handler = MockResponseHandler()

        test_data = {"key": "value", "number": 42}
        await agent.emit_json(response_handler, test_data, event_name="json_event")

        assert len(response_handler.json_responses) == 1
        event_name, data = response_handler.json_responses[0]
        assert event_name == "json_event"
        assert data == test_data

    @pytest.mark.asyncio
    async def test_emit_error_helper(self):
        """Test the emit_error helper method."""
        agent = TestAgent()
        response_handler = MockResponseHandler()

        await agent.emit_error(
            response_handler,
            "Test error message",
            code=404,
            details={"info": "test"}
        )

        assert len(response_handler.errors) == 1
        message, code, details = response_handler.errors[0]
        assert message == "Test error message"
        assert code == 404
        assert details == {"info": "test"}

    def test_mission_alignment_check(self):
        """Test the is_mission_aligned method."""
        agent = TestAgent()

        # Topics aligned with Freeman's mission
        aligned_topics = [
            "consciousness and awareness",
            "critical thinking in AI age",
            "propaganda manipulation",
            "freedom of thought",
            "questioning conformity"
        ]

        for topic in aligned_topics:
            assert agent.is_mission_aligned(topic), f"Topic should be aligned: {topic}"

        # Topics not strongly aligned
        non_aligned_topics = [
            "weather forecast",
            "cooking recipes",
            "sports scores"
        ]

        for topic in non_aligned_topics:
            # These may or may not be aligned, but shouldn't error
            result = agent.is_mission_aligned(topic)
            assert isinstance(result, bool)

    def test_get_philosophical_context(self):
        """Test getting philosophical context from agent."""
        agent = TestAgent()

        context = agent.get_philosophical_context()

        assert 'mission' in context
        assert 'principles' in context
        assert 'style' in context
        assert isinstance(context['principles'], list)
        assert len(context['principles']) > 0

    def test_apply_freeman_filter(self):
        """Test Freeman style filter application."""
        agent = TestAgent()

        # Test mild intensity
        result_mild = agent.apply_freeman_filter("content", intensity=2)
        assert result_mild['intensity'] == 2
        assert result_mild['tone'] == 'mild'
        assert result_mild['should_be_provocative'] is False

        # Test moderate intensity
        result_moderate = agent.apply_freeman_filter("content", intensity=6)
        assert result_moderate['intensity'] == 6
        assert result_moderate['tone'] == 'moderate'
        assert result_moderate['should_be_provocative'] is True

        # Test strong intensity
        result_strong = agent.apply_freeman_filter("content", intensity=9)
        assert result_strong['intensity'] == 9
        assert result_strong['tone'] == 'strong'
        assert result_strong['should_be_provocative'] is True
        assert result_strong['should_use_profanity'] is True
        assert result_strong['should_be_confrontational'] is True

    def test_get_agent_info(self):
        """Test getting comprehensive agent information."""
        agent = TestAgent()

        info = agent.get_agent_info()

        assert 'name' in info
        assert 'description' in info
        assert 'environment' in info
        assert 'agent_role' in info
        assert 'mission' in info
        assert 'principles_count' in info

        assert info['name'] == 'TestAgent'
        assert info['agent_role'] == 'test'
        assert info['principles_count'] > 0

    @pytest.mark.asyncio
    async def test_get_session_history(self):
        """Test retrieving session history."""
        agent = TestAgent()
        session = MockSession()

        # Add some mock interactions
        session.interactions = [
            {"query": "test1", "response": "response1"},
            {"query": "test2", "response": "response2"},
            {"query": "test3", "response": "response3"}
        ]

        # Get all interactions
        history = await agent.get_session_history(session)
        assert len(history) == 3

        # Get limited interactions
        history_limited = await agent.get_session_history(session, limit=2)
        assert len(history_limited) == 2

    def test_config_validation(self):
        """Test configuration validation helper."""
        agent = TestAgent()

        # Environment is always set (has default value)
        result = agent.validate_config_keys('environment')
        assert result is True

        # Test with a key that might not be set
        # This shouldn't crash even if key is missing
        result = agent.validate_config_keys('log_level')
        assert isinstance(result, bool)

    def test_log_agent_action(self):
        """Test structured logging method."""
        agent = TestAgent()

        # These should not raise exceptions
        agent.log_agent_action("test_action", level="info")
        agent.log_agent_action("test_action", {"detail": "value"}, level="debug")
        agent.log_agent_action("test_action", {"detail": "value"}, level="warning")

    @pytest.mark.asyncio
    async def test_error_handling_in_assist(self):
        """Test that errors in assist() are handled gracefully."""
        agent = TestAgent()

        # Create a response handler that will fail
        failing_handler = Mock()
        failing_handler.emit_text_block = AsyncMock(side_effect=Exception("Test error"))
        failing_handler.emit_error = AsyncMock()

        session = MockSession()
        query = MockQuery("Test query")

        # This should not raise an exception, but handle it internally
        await agent.assist(session, query, failing_handler)

        # Verify error was emitted
        assert failing_handler.emit_error.called

    def test_agent_inheritance_chain(self):
        """Test that the agent inheritance chain is correct."""
        agent = TestAgent()

        # Verify inheritance
        assert isinstance(agent, TestAgent)
        assert isinstance(agent, FreemanBaseAgent)
        assert isinstance(agent, SentientAgentBase)

        # Verify methods are available from all parent classes
        assert hasattr(agent, 'assist')  # From AbstractAgent
        assert hasattr(agent, 'emit_text')  # From SentientAgentBase
        assert hasattr(agent, 'is_mission_aligned')  # From FreemanBaseAgent
        assert hasattr(agent, 'run_self_test')  # From TestAgent


class TestConfigIntegration:
    """Test configuration integration with agents."""

    def test_config_import(self):
        """Test that config can be imported and used."""
        assert config is not None
        assert hasattr(config, 'environment')
        assert hasattr(config, 'log_level')

    def test_config_environment_helpers(self):
        """Test environment helper properties."""
        assert hasattr(config, 'is_development')
        assert hasattr(config, 'is_production')
        assert isinstance(config.is_development, bool)
        assert isinstance(config.is_production, bool)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
