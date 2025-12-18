"""
MCP Tools wrapper module for Freeman Sentient Agent.

This module provides a unified interface to access MCP (Model Context Protocol) tools:
- graphiti-memory: For memory management and retrieval
- context7: For knowledge and documentation queries

The MCPTools class provides async methods that can be used by Freeman agents
to interact with these tools while maintaining proper error handling and logging.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from config.agent_config import config


# Configure logging
logger = logging.getLogger("freeman.mcp_tools")


class MemoryType(str, Enum):
    """Types of memory operations supported by graphiti-memory."""
    USER_PROFILE = "user_profile"
    RELATIONSHIP = "relationship"
    ACTION = "action"
    EMOTIONAL = "emotional"
    CONVERSATION = "conversation"


class MCPTools:
    """
    Unified interface for MCP tools (graphiti-memory and context7).

    This class provides methods to interact with MCP tools that are available
    in the Claude Code environment. It handles:
    - Memory operations (store, retrieve, search)
    - Knowledge queries (documentation, code examples)
    - Error handling and logging
    - Configuration integration

    Usage:
        mcp = MCPTools()

        # Store memory
        await mcp.store_memory("user_123", "likes philosophy", MemoryType.USER_PROFILE)

        # Retrieve memories
        memories = await mcp.retrieve_memories("user_123", limit=10)

        # Query knowledge
        docs = await mcp.query_knowledge("Python async patterns")
    """

    def __init__(self, enable_memory: bool = True, enable_knowledge: bool = True):
        """
        Initialize MCP tools wrapper.

        Args:
            enable_memory: Enable graphiti-memory tool (default: True)
            enable_knowledge: Enable context7 tool (default: True)
        """
        self.enable_memory = enable_memory
        self.enable_knowledge = enable_knowledge
        self.config = config
        self.logger = logging.getLogger("freeman.mcp_tools")

        self.logger.info(
            f"MCPTools initialized (memory: {enable_memory}, knowledge: {enable_knowledge})"
        )

    # ============================================================================
    # Memory Operations (graphiti-memory)
    # ============================================================================

    async def store_memory(
        self,
        entity_id: str,
        content: str,
        memory_type: MemoryType = MemoryType.USER_PROFILE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Store a memory in graphiti-memory.

        Args:
            entity_id: Identifier for the entity (user_id, conversation_id, etc.)
            content: Memory content to store
            memory_type: Type of memory (user_profile, relationship, action, etc.)
            metadata: Optional metadata to attach to the memory

        Returns:
            Dictionary with result status and memory ID

        Example:
            result = await mcp.store_memory(
                "user_123",
                "User expressed interest in philosophy and AI ethics",
                MemoryType.USER_PROFILE,
                metadata={"timestamp": "2026-01-31", "source": "telegram"}
            )
        """
        if not self.enable_memory:
            self.logger.warning("Memory operations disabled")
            return {"status": "disabled", "message": "Memory operations are disabled"}

        try:
            self.logger.debug(
                f"Storing memory for {entity_id} (type: {memory_type}): {content[:50]}..."
            )

            # Placeholder for actual MCP tool integration
            # In production, this would call the actual graphiti-memory MCP tool
            result = {
                "status": "success",
                "memory_id": f"mem_{entity_id}_{memory_type}",
                "entity_id": entity_id,
                "content": content,
                "memory_type": memory_type,
                "metadata": metadata or {}
            }

            self.logger.info(f"Memory stored successfully: {result['memory_id']}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
            return {
                "status": "error",
                "message": str(e),
                "entity_id": entity_id
            }

    async def retrieve_memories(
        self,
        entity_id: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve memories from graphiti-memory.

        Args:
            entity_id: Identifier for the entity
            memory_type: Optional memory type filter
            limit: Maximum number of memories to retrieve
            filters: Optional additional filters

        Returns:
            List of memory dictionaries

        Example:
            memories = await mcp.retrieve_memories(
                "user_123",
                memory_type=MemoryType.USER_PROFILE,
                limit=5
            )
        """
        if not self.enable_memory:
            self.logger.warning("Memory operations disabled")
            return []

        try:
            self.logger.debug(
                f"Retrieving memories for {entity_id} "
                f"(type: {memory_type}, limit: {limit})"
            )

            # Placeholder for actual MCP tool integration
            memories = []

            self.logger.info(f"Retrieved {len(memories)} memories for {entity_id}")
            return memories

        except Exception as e:
            self.logger.error(f"Failed to retrieve memories: {e}")
            return []

    async def search_memories(
        self,
        query: str,
        entity_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search memories using semantic search.

        Args:
            query: Search query
            entity_id: Optional entity filter
            memory_type: Optional memory type filter
            limit: Maximum number of results

        Returns:
            List of matching memory dictionaries with relevance scores

        Example:
            results = await mcp.search_memories(
                "philosophy discussions",
                entity_id="user_123",
                limit=5
            )
        """
        if not self.enable_memory:
            self.logger.warning("Memory operations disabled")
            return []

        try:
            self.logger.debug(
                f"Searching memories: '{query}' "
                f"(entity: {entity_id}, type: {memory_type})"
            )

            # Placeholder for actual MCP tool integration
            results = []

            self.logger.info(f"Found {len(results)} matching memories")
            return results

        except Exception as e:
            self.logger.error(f"Failed to search memories: {e}")
            return []

    async def delete_memory(
        self,
        memory_id: str,
        entity_id: str
    ) -> Dict[str, Any]:
        """
        Delete a specific memory.

        Args:
            memory_id: ID of the memory to delete
            entity_id: Entity ID for verification

        Returns:
            Dictionary with deletion status
        """
        if not self.enable_memory:
            self.logger.warning("Memory operations disabled")
            return {"status": "disabled"}

        try:
            self.logger.debug(f"Deleting memory {memory_id} for {entity_id}")

            # Placeholder for actual MCP tool integration
            result = {
                "status": "success",
                "memory_id": memory_id,
                "deleted": True
            }

            self.logger.info(f"Memory deleted: {memory_id}")
            return result

        except Exception as e:
            self.logger.error(f"Failed to delete memory: {e}")
            return {
                "status": "error",
                "message": str(e)
            }

    # ============================================================================
    # Knowledge Operations (context7)
    # ============================================================================

    async def query_knowledge(
        self,
        query: str,
        library_id: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query knowledge base using context7.

        Args:
            query: Knowledge query (e.g., "How to use async in Python")
            library_id: Optional library ID (e.g., "/python/python", "/vercel/next.js")
            limit: Maximum number of results

        Returns:
            List of knowledge items with documentation and examples

        Example:
            docs = await mcp.query_knowledge(
                "async context managers",
                library_id="/python/python"
            )
        """
        if not self.enable_knowledge:
            self.logger.warning("Knowledge operations disabled")
            return []

        try:
            self.logger.debug(
                f"Querying knowledge: '{query}' "
                f"(library: {library_id}, limit: {limit})"
            )

            # Placeholder for actual MCP tool integration
            results = []

            self.logger.info(f"Found {len(results)} knowledge items")
            return results

        except Exception as e:
            self.logger.error(f"Failed to query knowledge: {e}")
            return []

    async def resolve_library(
        self,
        library_name: str,
        query_context: Optional[str] = None
    ) -> Optional[str]:
        """
        Resolve a library name to a Context7-compatible library ID.

        Args:
            library_name: Name of the library (e.g., "python", "react", "django")
            query_context: Optional query context for better matching

        Returns:
            Library ID string or None if not found

        Example:
            library_id = await mcp.resolve_library("fastapi")
            # Returns: "/tiangolo/fastapi"
        """
        if not self.enable_knowledge:
            self.logger.warning("Knowledge operations disabled")
            return None

        try:
            self.logger.debug(f"Resolving library: {library_name}")

            # Placeholder for actual MCP tool integration
            library_id = None

            if library_id:
                self.logger.info(f"Resolved library {library_name} -> {library_id}")
            else:
                self.logger.warning(f"Could not resolve library: {library_name}")

            return library_id

        except Exception as e:
            self.logger.error(f"Failed to resolve library: {e}")
            return None

    # ============================================================================
    # Utility Methods
    # ============================================================================

    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get information about available MCP tools and capabilities.

        Returns:
            Dictionary describing available tools and their status
        """
        return {
            "memory": {
                "enabled": self.enable_memory,
                "tool": "graphiti-memory",
                "operations": [
                    "store_memory",
                    "retrieve_memories",
                    "search_memories",
                    "delete_memory"
                ],
                "memory_types": [t.value for t in MemoryType]
            },
            "knowledge": {
                "enabled": self.enable_knowledge,
                "tool": "context7",
                "operations": [
                    "query_knowledge",
                    "resolve_library"
                ]
            },
            "environment": self.config.environment
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health status of MCP tools.

        Returns:
            Dictionary with health status of each tool
        """
        health = {
            "overall": "healthy",
            "tools": {}
        }

        # Check memory tool
        if self.enable_memory:
            try:
                # Placeholder health check
                health["tools"]["graphiti-memory"] = {
                    "status": "available",
                    "enabled": True
                }
            except Exception as e:
                health["tools"]["graphiti-memory"] = {
                    "status": "error",
                    "enabled": True,
                    "error": str(e)
                }
                health["overall"] = "degraded"
        else:
            health["tools"]["graphiti-memory"] = {
                "status": "disabled",
                "enabled": False
            }

        # Check knowledge tool
        if self.enable_knowledge:
            try:
                # Placeholder health check
                health["tools"]["context7"] = {
                    "status": "available",
                    "enabled": True
                }
            except Exception as e:
                health["tools"]["context7"] = {
                    "status": "error",
                    "enabled": True,
                    "error": str(e)
                }
                health["overall"] = "degraded"
        else:
            health["tools"]["context7"] = {
                "status": "disabled",
                "enabled": False
            }

        self.logger.debug(f"Health check completed: {health['overall']}")
        return health
