"""
Test suite for MCP (Model Context Protocol) tools integration.

This module tests the integration between Freeman agents and MCP tools:
- graphiti-memory for memory management
- context7 for knowledge queries
- MCPTools wrapper functionality
- Agent access to MCP tools via base agent
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, MagicMock, patch

# Import MCP tools and agents
from src.core.mcp_tools import MCPTools, MemoryType
from src.agents.base_agent import FreemanBaseAgent
from src.agents.test_agent import TestAgent
from config.agent_config import config


class TestMCPToolsBasic:
    """Test basic MCPTools functionality."""

    def test_mcp_tools_instantiation(self):
        """Test that MCPTools can be instantiated."""
        mcp = MCPTools()

        assert mcp is not None
        assert mcp.enable_memory is True
        assert mcp.enable_knowledge is True
        assert mcp.config is not None

    def test_mcp_tools_disabled_memory(self):
        """Test MCPTools with memory disabled."""
        mcp = MCPTools(enable_memory=False, enable_knowledge=True)

        assert mcp.enable_memory is False
        assert mcp.enable_knowledge is True

    def test_mcp_tools_disabled_knowledge(self):
        """Test MCPTools with knowledge disabled."""
        mcp = MCPTools(enable_memory=True, enable_knowledge=False)

        assert mcp.enable_memory is True
        assert mcp.enable_knowledge is False

    def test_memory_type_enum(self):
        """Test MemoryType enum values."""
        assert MemoryType.USER_PROFILE == "user_profile"
        assert MemoryType.RELATIONSHIP == "relationship"
        assert MemoryType.ACTION == "action"
        assert MemoryType.EMOTIONAL == "emotional"
        assert MemoryType.CONVERSATION == "conversation"

        # Verify all types are accessible
        memory_types = list(MemoryType)
        assert len(memory_types) == 5

    def test_get_capabilities(self):
        """Test getting MCP tools capabilities."""
        mcp = MCPTools()

        capabilities = mcp.get_capabilities()

        assert 'memory' in capabilities
        assert 'knowledge' in capabilities
        assert 'environment' in capabilities

        # Check memory capabilities
        assert capabilities['memory']['enabled'] is True
        assert capabilities['memory']['tool'] == "graphiti-memory"
        assert 'store_memory' in capabilities['memory']['operations']
        assert 'retrieve_memories' in capabilities['memory']['operations']
        assert 'search_memories' in capabilities['memory']['operations']
        assert 'delete_memory' in capabilities['memory']['operations']

        # Check knowledge capabilities
        assert capabilities['knowledge']['enabled'] is True
        assert capabilities['knowledge']['tool'] == "context7"
        assert 'query_knowledge' in capabilities['knowledge']['operations']
        assert 'resolve_library' in capabilities['knowledge']['operations']

    def test_capabilities_with_disabled_tools(self):
        """Test capabilities when tools are disabled."""
        mcp = MCPTools(enable_memory=False, enable_knowledge=False)

        capabilities = mcp.get_capabilities()

        assert capabilities['memory']['enabled'] is False
        assert capabilities['knowledge']['enabled'] is False


class TestMCPMemoryOperations:
    """Test MCP memory operations (graphiti-memory)."""

    @pytest.mark.asyncio
    async def test_store_memory_basic(self):
        """Test storing a memory."""
        mcp = MCPTools()

        result = await mcp.store_memory(
            entity_id="user_123",
            content="User enjoys philosophical discussions",
            memory_type=MemoryType.USER_PROFILE
        )

        assert result is not None
        assert result['status'] == 'success'
        assert result['entity_id'] == "user_123"
        assert result['content'] == "User enjoys philosophical discussions"
        assert result['memory_type'] == MemoryType.USER_PROFILE
        assert 'memory_id' in result

    @pytest.mark.asyncio
    async def test_store_memory_with_metadata(self):
        """Test storing a memory with metadata."""
        mcp = MCPTools()

        metadata = {
            "timestamp": "2026-01-31",
            "source": "telegram",
            "confidence": 0.95
        }

        result = await mcp.store_memory(
            entity_id="user_456",
            content="User expressed interest in AI ethics",
            memory_type=MemoryType.CONVERSATION,
            metadata=metadata
        )

        assert result['status'] == 'success'
        assert result['metadata'] == metadata

    @pytest.mark.asyncio
    async def test_store_memory_disabled(self):
        """Test storing memory when memory is disabled."""
        mcp = MCPTools(enable_memory=False)

        result = await mcp.store_memory(
            entity_id="user_789",
            content="Test content",
            memory_type=MemoryType.USER_PROFILE
        )

        assert result['status'] == 'disabled'

    @pytest.mark.asyncio
    async def test_retrieve_memories_basic(self):
        """Test retrieving memories for an entity."""
        mcp = MCPTools()

        memories = await mcp.retrieve_memories(
            entity_id="user_123",
            limit=10
        )

        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_retrieve_memories_with_type_filter(self):
        """Test retrieving memories with type filter."""
        mcp = MCPTools()

        memories = await mcp.retrieve_memories(
            entity_id="user_123",
            memory_type=MemoryType.USER_PROFILE,
            limit=5
        )

        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_retrieve_memories_disabled(self):
        """Test retrieving memories when memory is disabled."""
        mcp = MCPTools(enable_memory=False)

        memories = await mcp.retrieve_memories(
            entity_id="user_123"
        )

        assert memories == []

    @pytest.mark.asyncio
    async def test_search_memories_basic(self):
        """Test searching memories."""
        mcp = MCPTools()

        results = await mcp.search_memories(
            query="philosophy discussions",
            limit=5
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_memories_with_filters(self):
        """Test searching memories with entity and type filters."""
        mcp = MCPTools()

        results = await mcp.search_memories(
            query="AI ethics",
            entity_id="user_123",
            memory_type=MemoryType.CONVERSATION,
            limit=10
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_memories_disabled(self):
        """Test searching memories when memory is disabled."""
        mcp = MCPTools(enable_memory=False)

        results = await mcp.search_memories(
            query="test query"
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_delete_memory_basic(self):
        """Test deleting a memory."""
        mcp = MCPTools()

        result = await mcp.delete_memory(
            memory_id="mem_user_123_user_profile",
            entity_id="user_123"
        )

        assert result['status'] == 'success'
        assert result['deleted'] is True
        assert result['memory_id'] == "mem_user_123_user_profile"

    @pytest.mark.asyncio
    async def test_delete_memory_disabled(self):
        """Test deleting memory when memory is disabled."""
        mcp = MCPTools(enable_memory=False)

        result = await mcp.delete_memory(
            memory_id="test_id",
            entity_id="user_123"
        )

        assert result['status'] == 'disabled'


class TestMCPKnowledgeOperations:
    """Test MCP knowledge operations (context7)."""

    @pytest.mark.asyncio
    async def test_query_knowledge_basic(self):
        """Test querying knowledge base."""
        mcp = MCPTools()

        results = await mcp.query_knowledge(
            query="How to use async in Python",
            limit=5
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_query_knowledge_with_library(self):
        """Test querying knowledge with specific library."""
        mcp = MCPTools()

        results = await mcp.query_knowledge(
            query="async context managers",
            library_id="/python/python",
            limit=3
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_query_knowledge_disabled(self):
        """Test querying knowledge when knowledge is disabled."""
        mcp = MCPTools(enable_knowledge=False)

        results = await mcp.query_knowledge(
            query="test query"
        )

        assert results == []

    @pytest.mark.asyncio
    async def test_resolve_library_basic(self):
        """Test resolving a library name."""
        mcp = MCPTools()

        library_id = await mcp.resolve_library(
            library_name="fastapi"
        )

        # Should return None or a string (placeholder implementation)
        assert library_id is None or isinstance(library_id, str)

    @pytest.mark.asyncio
    async def test_resolve_library_with_context(self):
        """Test resolving library with query context."""
        mcp = MCPTools()

        library_id = await mcp.resolve_library(
            library_name="react",
            query_context="How to use hooks in React"
        )

        assert library_id is None or isinstance(library_id, str)

    @pytest.mark.asyncio
    async def test_resolve_library_disabled(self):
        """Test resolving library when knowledge is disabled."""
        mcp = MCPTools(enable_knowledge=False)

        library_id = await mcp.resolve_library(
            library_name="test"
        )

        assert library_id is None


class TestMCPHealthCheck:
    """Test MCP tools health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_all_enabled(self):
        """Test health check when all tools are enabled."""
        mcp = MCPTools()

        health = await mcp.health_check()

        assert 'overall' in health
        assert 'tools' in health
        assert 'graphiti-memory' in health['tools']
        assert 'context7' in health['tools']

        # Check memory tool health
        memory_health = health['tools']['graphiti-memory']
        assert memory_health['enabled'] is True
        assert memory_health['status'] == 'available'

        # Check knowledge tool health
        knowledge_health = health['tools']['context7']
        assert knowledge_health['enabled'] is True
        assert knowledge_health['status'] == 'available'

    @pytest.mark.asyncio
    async def test_health_check_memory_disabled(self):
        """Test health check when memory is disabled."""
        mcp = MCPTools(enable_memory=False, enable_knowledge=True)

        health = await mcp.health_check()

        memory_health = health['tools']['graphiti-memory']
        assert memory_health['enabled'] is False
        assert memory_health['status'] == 'disabled'

    @pytest.mark.asyncio
    async def test_health_check_knowledge_disabled(self):
        """Test health check when knowledge is disabled."""
        mcp = MCPTools(enable_memory=True, enable_knowledge=False)

        health = await mcp.health_check()

        knowledge_health = health['tools']['context7']
        assert knowledge_health['enabled'] is False
        assert knowledge_health['status'] == 'disabled'


class TestAgentMCPIntegration:
    """Test integration between Freeman agents and MCP tools."""

    def test_agent_has_mcp_tools_property(self):
        """Test that FreemanBaseAgent has mcp_tools property."""
        agent = TestAgent()

        assert hasattr(agent, 'mcp_tools')
        assert hasattr(agent, '_mcp_tools')

    def test_agent_mcp_tools_lazy_loading(self):
        """Test that MCP tools are lazy loaded."""
        agent = TestAgent()

        # Should be None before first access
        assert agent._mcp_tools is None

        # Access the property
        mcp_tools = agent.mcp_tools

        # Should be initialized now
        assert agent._mcp_tools is not None
        assert isinstance(mcp_tools, MCPTools)

    def test_agent_mcp_tools_singleton(self):
        """Test that MCP tools property returns the same instance."""
        agent = TestAgent()

        mcp_tools_1 = agent.mcp_tools
        mcp_tools_2 = agent.mcp_tools

        # Should be the same instance
        assert mcp_tools_1 is mcp_tools_2

    def test_agent_mcp_tools_enabled(self):
        """Test that agent's MCP tools have both memory and knowledge enabled."""
        agent = TestAgent()

        mcp_tools = agent.mcp_tools

        assert mcp_tools.enable_memory is True
        assert mcp_tools.enable_knowledge is True

    @pytest.mark.asyncio
    async def test_agent_can_store_memory(self):
        """Test that agent can use MCP tools to store memory."""
        agent = TestAgent()

        result = await agent.mcp_tools.store_memory(
            entity_id="user_test",
            content="Test memory from agent",
            memory_type=MemoryType.USER_PROFILE
        )

        assert result['status'] == 'success'
        assert result['entity_id'] == "user_test"

    @pytest.mark.asyncio
    async def test_agent_can_query_knowledge(self):
        """Test that agent can use MCP tools to query knowledge."""
        agent = TestAgent()

        results = await agent.mcp_tools.query_knowledge(
            query="Test query from agent"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_agent_can_access_capabilities(self):
        """Test that agent can access MCP capabilities."""
        agent = TestAgent()

        capabilities = agent.mcp_tools.get_capabilities()

        assert capabilities is not None
        assert 'memory' in capabilities
        assert 'knowledge' in capabilities

    @pytest.mark.asyncio
    async def test_agent_can_perform_health_check(self):
        """Test that agent can perform MCP health check."""
        agent = TestAgent()

        health = await agent.mcp_tools.health_check()

        assert health is not None
        assert 'overall' in health
        assert 'tools' in health


class TestMCPAllMemoryTypes:
    """Test all memory types with MCP tools."""

    @pytest.mark.asyncio
    async def test_store_user_profile_memory(self):
        """Test storing USER_PROFILE memory type."""
        mcp = MCPTools()

        result = await mcp.store_memory(
            "user_1", "User profile data", MemoryType.USER_PROFILE
        )

        assert result['status'] == 'success'
        assert result['memory_type'] == MemoryType.USER_PROFILE

    @pytest.mark.asyncio
    async def test_store_relationship_memory(self):
        """Test storing RELATIONSHIP memory type."""
        mcp = MCPTools()

        result = await mcp.store_memory(
            "user_1", "Relationship data", MemoryType.RELATIONSHIP
        )

        assert result['status'] == 'success'
        assert result['memory_type'] == MemoryType.RELATIONSHIP

    @pytest.mark.asyncio
    async def test_store_action_memory(self):
        """Test storing ACTION memory type."""
        mcp = MCPTools()

        result = await mcp.store_memory(
            "user_1", "Action data", MemoryType.ACTION
        )

        assert result['status'] == 'success'
        assert result['memory_type'] == MemoryType.ACTION

    @pytest.mark.asyncio
    async def test_store_emotional_memory(self):
        """Test storing EMOTIONAL memory type."""
        mcp = MCPTools()

        result = await mcp.store_memory(
            "user_1", "Emotional data", MemoryType.EMOTIONAL
        )

        assert result['status'] == 'success'
        assert result['memory_type'] == MemoryType.EMOTIONAL

    @pytest.mark.asyncio
    async def test_store_conversation_memory(self):
        """Test storing CONVERSATION memory type."""
        mcp = MCPTools()

        result = await mcp.store_memory(
            "user_1", "Conversation data", MemoryType.CONVERSATION
        )

        assert result['status'] == 'success'
        assert result['memory_type'] == MemoryType.CONVERSATION


class TestMCPErrorHandling:
    """Test MCP tools error handling."""

    @pytest.mark.asyncio
    async def test_store_memory_handles_errors_gracefully(self):
        """Test that store_memory handles errors gracefully."""
        mcp = MCPTools()

        # Even with unusual inputs, should not crash
        result = await mcp.store_memory(
            entity_id="",
            content="",
            memory_type=MemoryType.USER_PROFILE
        )

        # Should return a result (success or error)
        assert 'status' in result

    @pytest.mark.asyncio
    async def test_retrieve_memories_handles_errors_gracefully(self):
        """Test that retrieve_memories handles errors gracefully."""
        mcp = MCPTools()

        # Even with unusual inputs, should not crash
        memories = await mcp.retrieve_memories(
            entity_id="",
            limit=0
        )

        # Should return a list
        assert isinstance(memories, list)

    @pytest.mark.asyncio
    async def test_search_memories_handles_errors_gracefully(self):
        """Test that search_memories handles errors gracefully."""
        mcp = MCPTools()

        # Even with unusual inputs, should not crash
        results = await mcp.search_memories(
            query="",
            limit=0
        )

        # Should return a list
        assert isinstance(results, list)


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
