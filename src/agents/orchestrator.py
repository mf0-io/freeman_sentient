"""Orchestrator agent for multi-persona routing and coordination

The Orchestrator is the main coordinator of the system that:
- Routes incoming messages to the correct persona
- Loads persona context from PersonaManager
- Coordinates sub-agents (Inner Voice, Decision, Response, Content)
- Handles multi-persona concurrency
- Assembles final responses and updates memory
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.persona.manager import PersonaManager
from src.persona.models import Persona


class Orchestrator:
    """Main coordinator for multi-persona message routing and agent orchestration

    The Orchestrator is responsible for:
    - Receiving incoming messages from all platforms
    - Determining which persona should handle the message
    - Loading the appropriate persona context
    - Coordinating the agent pipeline (Inner Voice → Decision → Response → Content)
    - Assembling the final response
    - Updating the memory system
    - Handling multi-persona concurrency

    Unlike other agents, Orchestrator doesn't extend BaseAgent since it manages
    multiple personas rather than representing a single one.

    Pipeline:
        1. Receive message
        2. Route to persona
        3. Load user context from Memory
        4. → Inner Voice Agent (analyze topic)
        5. → Decision Agent (should respond? how?)
        6. → Response Generator (if responding)
        7. → Content Creator (if media needed)
        8. Assemble response
        9. Update Memory
        10. Return response

    Usage:
        orchestrator = Orchestrator()
        response = await orchestrator.process_message(
            message="Hello Freeman",
            platform="telegram",
            user_id="123",
            persona_id="freeman"
        )
    """

    def __init__(self, persona_manager: Optional[PersonaManager] = None):
        """Initialize the Orchestrator

        Args:
            persona_manager: PersonaManager instance for loading personas.
                           If None, creates a new PersonaManager instance.
        """
        self._persona_manager = persona_manager or PersonaManager()
        self._active_personas: Dict[str, Persona] = {}
        self._load_active_personas()

    def _load_active_personas(self) -> None:
        """Load all active personas from the PersonaManager"""
        active = self._persona_manager.list_active_personas()
        self._active_personas = {persona.id: persona for persona in active}

    def route_to_persona(
# Follows base class contract
        self,
        message: str,
        platform: str,
        user_id: str,
        persona_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Persona]:
        """Route a message to the appropriate persona

        Args:
            message: The incoming message text
            platform: Platform identifier (telegram, twitter, etc)
            user_id: User identifier
            persona_id: Optional explicit persona ID. If provided, routes directly.
            metadata: Optional metadata about the message

        Returns:
            The Persona instance to handle this message, or None if no match

        Routing logic (in order):
            1. If persona_id provided explicitly, use it
            2. If platform has a default persona mapping, use it
            3. Use first active persona (single-persona mode)
            4. Return None if no personas available
        """
        # Explicit persona_id takes precedence
        if persona_id and persona_id in self._active_personas:
            return self._active_personas[persona_id]

        # TODO: Implement platform-based routing when needed
        # For now, use first active persona (single-persona mode for MVP)
        if self._active_personas:
            return next(iter(self._active_personas.values()))

        return None

    def process_message(
        self,
        message: str,
        platform: str,
        user_id: str,
        persona_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process an incoming message through the agent pipeline

        This is the main entry point for message processing.

        Args:
            message: The incoming message text
            platform: Platform identifier (telegram, twitter, etc)
            user_id: User identifier
            persona_id: Optional explicit persona ID
            metadata: Optional metadata about the message

        Returns:
            Dictionary with response data:
                {
                    "persona_id": str,
                    "response_text": str,
                    "media": Optional[Dict],
                    "metadata": Dict,
                    "timestamp": str
                }

        Raises:
            ValueError: If no suitable persona found
        """
        # Route to persona
        persona = self.route_to_persona(message, platform, user_id, persona_id, metadata)
        if not persona:
            raise ValueError("No active persona available to handle message")

        # TODO: Load user context from Memory
        # user_context = self._load_user_context(persona, user_id)

        # TODO: Call Inner Voice Agent
        # inner_voice_result = await self._call_inner_voice(persona, message, user_context)

        # TODO: Call Decision Agent
        # decision = await self._call_decision(persona, message, user_context, inner_voice_result)

        # TODO: Call Response Generator (if decision says respond)
        # if decision.should_respond:
        #     response_text = await self._call_response_generator(...)

        # TODO: Call Content Creator (if decision says create media)
        # if decision.needs_media:
        #     media = await self._call_content_creator(...)

        # TODO: Update Memory
        # self._update_memory(persona, user_id, message, response_text)

        # For MVP skeleton, return a basic response structure
        return {
            "persona_id": persona.id,
            "persona_name": persona.name,
            "response_text": f"[Orchestrator skeleton - persona '{persona.name}' would respond to: {message}]",
            "media": None,
            "metadata": {
                "platform": platform,
                "user_id": user_id,
                "pipeline": "skeleton",
                "agents_called": []
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_active_personas(self) -> List[Persona]:
        """Get all currently active personas

        Returns:
            List of active Persona instances
        """
        return list(self._active_personas.values())

    def reload_personas(self) -> None:
        """Reload personas from PersonaManager

        Useful for picking up configuration changes without restarting.
        """
        self._persona_manager.reload()
        self._load_active_personas()

    def get_persona_by_id(self, persona_id: str) -> Optional[Persona]:
        """Get a specific persona by ID

        Args:
            persona_id: Persona identifier

        Returns:
            Persona instance or None if not found
        """
        return self._active_personas.get(persona_id)

    @property
    def persona_count(self) -> int:
        """Get the number of active personas

        Returns:
            Count of active personas
        """
        return len(self._active_personas)

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"Orchestrator(active_personas={self.persona_count})"

    def __str__(self) -> str:
        """String representation"""
        persona_names = [p.name for p in self._active_personas.values()]
        return f"Orchestrator managing {self.persona_count} personas: {', '.join(persona_names)}"
