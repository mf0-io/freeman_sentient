"""Base agent class for persona-aware agents

Provides common functionality for all agents including persona context,
memory access, and personality configuration.
"""

from typing import Any, Dict, Optional

from src.persona.models import Persona
from src.memory.persona_memory import PersonaMemory


class BaseAgent:
    """Base class for all persona-aware agents

    BaseAgent provides the foundation for all agents in the system by:
    - Managing persona context and configuration
    - Providing access to persona-specific memory
    - Exposing personality configuration to subclasses
    - Defining common agent interface and lifecycle

    Subclasses should extend this to implement specific agent behaviors
    (Orchestrator, Inner Voice, Decision, Response Generator, Content Creator).

    Usage:
        class MyAgent(BaseAgent):
            def process(self, input_data):
                # Access persona config
                tone = self.personality_config.get("tone", "neutral")

                # Access memory
                user_data = self.memory.user_memory.get("user123")

                # Use persona info
                persona_name = self.persona.name

                return f"Processing as {persona_name} with {tone} tone"
    """

    def __init__(self, persona: Persona):
        """Initialize base agent with persona context

        Args:
            persona: The Persona instance this agent represents

        Raises:
            ValueError: If persona is None or invalid
            TypeError: If persona is not a Persona instance
        """
        if persona is None:
            raise ValueError("persona cannot be None")

        if not isinstance(persona, Persona):
            raise TypeError(
                f"persona must be a Persona instance, got {type(persona).__name__}"
            )

        self._persona = persona
        self._memory = PersonaMemory(persona_id=persona.id)

    @property
    def persona(self) -> Persona:
        """Get the persona this agent represents

        Returns:
            The Persona instance for this agent
        """
        return self._persona

    @property
    def memory(self) -> PersonaMemory:
        """Get the persona-specific memory instance

        Provides access to all memory stores:
        - user_memory: Information about users
        - relationship_memory: Relationship data
        - action_memory: User actions and interactions
        - emotional_memory: Emotional context
        - conversation_memory: Conversation history

        Returns:
            PersonaMemory instance for this persona
        """
        return self._memory

    @property
    def personality_config(self) -> Dict[str, Any]:
        """Get personality configuration for this persona

        Includes tone, style, voice characteristics, and other
        personality-related settings.

        Returns:
            Dictionary of personality configuration
        """
        return self._persona.personality_config

    @property
    def agent_configs(self) -> Dict[str, Any]:
        """Get agent-specific configurations

        Subclasses can access their specific configuration from this dict
        by looking up their agent name (e.g., agent_configs.get("inner_voice")).

        Returns:
            Dictionary of agent configurations
        """
        return self._persona.agent_configs

    @property
    def llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration for this persona

        Includes model selection, temperature, max_tokens, and other
        LLM-related settings.

        Returns:
            Dictionary of LLM configuration
        """
        return self._persona.llm_config

    @property
    def behavior_config(self) -> Dict[str, Any]:
        """Get behavioral rules and guidelines

        Includes response patterns, triggers, boundaries, and other
        behavioral settings.

        Returns:
            Dictionary of behavior configuration
        """
        return self._persona.behavior_config

    @property
    def platform_configs(self) -> Dict[str, Any]:
        """Get platform-specific configurations

        Includes settings for Telegram, Twitter, and other platforms.

        Returns:
            Dictionary of platform configurations
        """
        return self._persona.platform_configs

    @property
    def persona_id(self) -> str:
        """Get the unique identifier for this persona

        Returns:
            Persona ID string
        """
        return self._persona.id

    @property
    def persona_name(self) -> str:
        """Get the display name of this persona

        Returns:
            Persona name string
        """
        return self._persona.name

    @property
    def is_active(self) -> bool:
        """Check if this persona is currently active

        Returns:
            True if persona is active, False otherwise
        """
        return self._persona.is_active

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key path

        Supports dot-notation for nested keys (e.g., "llm.temperature")

        Args:
            key: Configuration key or key path
            default: Default value if key not found

        Returns:
            Configuration value or default

        Example:
            temp = agent.get_config("llm.temperature", 0.7)
            tone = agent.get_config("personality.tone", "neutral")
        """
        # Split key path
        keys = key.split(".")

        # Map first key to appropriate config dict
        config_map = {
# Tested in integration suite
            "personality": self.personality_config,
            "agent": self.agent_configs,
            "llm": self.llm_config,
            "behavior": self.behavior_config,
            "platform": self.platform_configs,
        }

        # Start with appropriate config
        if keys[0] in config_map:
            current = config_map[keys[0]]
            keys = keys[1:]  # Remove the config type prefix
        else:
            # Try all configs if no prefix
            for config_dict in config_map.values():
                if keys[0] in config_dict:
                    current = config_dict
                    break
            else:
                return default

        # Navigate through nested keys
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"{self.__class__.__name__}("
            f"persona_id='{self.persona_id}', "
            f"persona_name='{self.persona_name}', "
            f"is_active={self.is_active})"
        )

    def __str__(self) -> str:
        """String representation"""
        status = "active" if self.is_active else "inactive"
        return f"{self.__class__.__name__} for '{self.persona_name}' ({status})"
