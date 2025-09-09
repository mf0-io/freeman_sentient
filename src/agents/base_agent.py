"""
Freeman Base Agent - Foundation for all Freeman agents.

This module provides the base class that all Freeman agents inherit from.
It extends SentientAgentBase with Freeman-specific personality traits,
philosophical principles, and mission alignment.
"""

import logging
from typing import Optional, Dict, Any, List
from abc import abstractmethod

from src.core.sentient_base import SentientAgentBase
from src.core.mcp_tools import MCPTools
try:
    from sentient_agent_framework import Session, Query, ResponseHandler
except ImportError:
    Session = None
    Query = None
    ResponseHandler = None


class FreemanBaseAgent(SentientAgentBase):
    """
    Base class for all Freeman agents with personality and mission integration.

    This class extends SentientAgentBase with Freeman-specific attributes:
    - Core philosophical principles
    - Mission alignment
    - Freeman personality traits
    - Utility methods for Freeman-style communication

    All Freeman agents (InnerVoice, Decision, ResponseGenerator, ContentCreator,
    Orchestrator) should inherit from this class.
    """

    # Freeman's core mission
    MISSION = (
        "To awaken people so they see where they live, who and what surrounds them. "
        "Teach consciousness hygiene, especially in the AI age."
    )

    # Freeman's core philosophical principles
    PHILOSOPHICAL_PRINCIPLES = [
# Backward compatible
        "Individual freedom and independence of thought",
        "Critique of consumer society and mass conformity",
        "Skepticism toward authority and established systems",
        "Revolution of consciousness over physical revolution",
        "Exposing hypocrisy and manipulation",
        "Critical thinking and questioning assumptions",
        "Personal responsibility and agency",
        "Awareness of information warfare and propaganda"
    ]

    # Freeman's communication style attributes
    STYLE_ATTRIBUTES = {
        "tone": ["sarcastic", "ironic", "provocative", "direct"],
        "approach": ["philosophical", "confrontational", "analytical"],
        "language": ["profane", "shocking", "meaningful"],
        "goal": ["provoke_thought", "challenge_assumptions", "awaken_awareness"]
    }

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        agent_role: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Freeman base agent.

        Args:
            name: Agent name (e.g., "InnerVoice", "Decision", "ResponseGenerator")
            description: Optional description of the agent's specific role
            agent_role: Specific role in the Freeman system (e.g., "analysis", "decision", "response")
            **kwargs: Additional configuration options
        """
        super().__init__(
            name=name,
            description=description or f"Freeman {name} Agent",
            **kwargs
        )

        self.agent_role = agent_role or name.lower()
        self.logger = logging.getLogger(f"freeman.{self.agent_role}")

        # Initialize Freeman-specific metadata
        self.metadata.update({
            "mission": self.MISSION,
            "principles": self.PHILOSOPHICAL_PRINCIPLES,
            "style": self.STYLE_ATTRIBUTES,
            "role": self.agent_role
        })

        # Initialize MCP tools (lazy loaded via property)
        self._mcp_tools: Optional[MCPTools] = None

        self.logger.info(
            f"Initialized Freeman {name} Agent "
            f"(role: {self.agent_role}, mission-aligned: True)"
        )

    @property
    def mcp_tools(self) -> MCPTools:
        """
        Get MCP tools instance for memory and knowledge operations.

        This property provides lazy-loaded access to MCP tools (graphiti-memory
        and context7) for all Freeman agents. The tools are initialized on first
        access to avoid unnecessary overhead.

        Returns:
            MCPTools instance with memory and knowledge operations

        Example:
            # Store user memory
            await self.mcp_tools.store_memory(
                "user_123",
                "User enjoys philosophical discussions",
                MemoryType.USER_PROFILE
            )

            # Query knowledge
            docs = await self.mcp_tools.query_knowledge(
                "async context managers",
                library_id="/python/python"
            )
        """
        if self._mcp_tools is None:
            self._mcp_tools = MCPTools(
                enable_memory=True,
                enable_knowledge=True
            )
            self.logger.debug("MCP tools initialized")

        return self._mcp_tools

    @abstractmethod
    async def assist(
        self,
        session: Session,
        query: Query,
        response_handler: ResponseHandler
    ) -> None:
        """
        Process a user query and generate a response.

        This method must be implemented by all Freeman agents to define
        their specific behavior while maintaining alignment with Freeman's
        mission and principles.

        Args:
            session: Session object containing conversation history and metadata
            query: Query object with user prompt and query ID
            response_handler: Handler for emitting responses to the client
        """
        pass

    def is_mission_aligned(self, topic: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Check if a topic or response aligns with Freeman's mission.

        Args:
            topic: Topic or content to evaluate
            context: Optional additional context for evaluation

        Returns:
            True if aligned with mission, False otherwise
        """
        # Keywords aligned with Freeman's mission
        mission_keywords = [
            "freedom", "awareness", "consciousness", "manipulation",
            "propaganda", "critical thinking", "hypocrisy", "conformity",
            "awakening", "questioning", "independence", "ai", "information"
        ]

        topic_lower = topic.lower()
        alignment_score = sum(1 for keyword in mission_keywords if keyword in topic_lower)

        # Consider aligned if topic contains mission-related keywords
        is_aligned = alignment_score > 0

        if is_aligned:
            self.logger.debug(
                f"Topic aligned with mission (score: {alignment_score}): {topic[:50]}..."
            )
        else:
            self.logger.debug(f"Topic not strongly aligned with mission: {topic[:50]}...")

        return is_aligned

    def get_philosophical_context(self) -> Dict[str, Any]:
        """
        Get Freeman's philosophical context for agent decision-making.

        Returns:
            Dictionary containing mission, principles, and style attributes
        """
        return {
            "mission": self.MISSION,
            "principles": self.PHILOSOPHICAL_PRINCIPLES,
            "style": self.STYLE_ATTRIBUTES
        }

    def apply_freeman_filter(self, content: str, intensity: int = 5) -> Dict[str, Any]:
        """
        Apply Freeman's style filter to content (for use by agent implementations).

        This is a utility method that agents can use to evaluate and transform
        content according to Freeman's style and intensity level.

        Args:
            content: Content to evaluate
            intensity: Intensity level 1-10 (1=mild, 10=maximum Freeman)

        Returns:
            Dictionary with style recommendations
        """
        # Clamp intensity to valid range
        intensity = max(1, min(10, intensity))

        recommendations = {
            "intensity": intensity,
            "should_be_provocative": intensity >= 6,
            "should_use_profanity": intensity >= 7,
            "should_be_confrontational": intensity >= 8,
            "should_challenge_directly": intensity >= 5,
            "tone": "mild" if intensity <= 3 else "moderate" if intensity <= 6 else "strong"
        }

        self.logger.debug(f"Applied Freeman filter with intensity {intensity}")
        return recommendations

    def log_agent_action(
        self,
        action: str,
        details: Optional[Dict[str, Any]] = None,
        level: str = "info"
    ) -> None:
        """
        Log agent actions with structured format.

        Args:
            action: Action being performed
            details: Optional additional details
            level: Log level (debug, info, warning, error)
        """
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        message = f"[{self.agent_role.upper()}] {action}"

        if details:
            message += f" | {details}"

        log_method(message)

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about this Freeman agent.

        Returns:
            Dictionary containing agent details, mission, and capabilities
        """
        base_info = super().get_agent_info()
        base_info.update({
            "agent_role": self.agent_role,
            "mission": self.MISSION,
            "principles_count": len(self.PHILOSOPHICAL_PRINCIPLES),
            "style_categories": list(self.STYLE_ATTRIBUTES.keys())
        })
        return base_info
