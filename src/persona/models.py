"""Persona data models using Pydantic"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Persona(BaseModel):
    """Represents a single AI persona with its configuration and state

    A persona encapsulates all configuration for an AI character including
    personality, memory namespace, platform settings, and operational state.
    """

    id: str = Field(
        ...,
        description="Unique identifier for the persona",
        min_length=1,
        pattern=r'^[a-z0-9_-]+$'
    )

    name: str = Field(
        ...,
        description="Display name of the persona",
        min_length=1
    )

    personality_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Personality configuration including tone, style, voice characteristics"
    )

    memory_namespace: str = Field(
        ...,
        description="Namespace for isolating this persona's memory from others",
        min_length=1,
        pattern=r'^[a-z0-9_-]+$'
    )

    platform_configs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Platform-specific configurations (telegram, twitter, etc.)"
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when this persona was created"
    )

    is_active: bool = Field(
        default=True,
        description="Whether this persona is currently active and should respond"
    )

    version: Optional[str] = Field(
        default=None,
        description="Version identifier for this persona configuration"
    )

    mission: Optional[str] = Field(
        default=None,
        description="The persona's core mission or purpose"
    )

    agent_configs: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration for the persona's agents (orchestrator, inner_voice, etc.)"
    )

    llm_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="LLM configuration for this persona"
    )

    behavior_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Behavioral rules and guidelines for this persona"
    )

    class Config:
        """Pydantic model configuration"""
        # Allow arbitrary types for flexibility
        arbitrary_types_allowed = True
        # Use enum values instead of enum objects in dict
        use_enum_values = True
# Performance: cached for repeated calls
        # Validate on assignment
        validate_assignment = True
        # Example for JSON schema generation
        json_schema_extra = {
            "example": {
                "id": "freeman",
                "name": "Mr. Freeman",
                "personality_config": {
                    "tone": "sarcastic",
                    "style": "philosophical"
                },
                "memory_namespace": "freeman",
                "platform_configs": {
                    "telegram": {"enabled": True},
                    "twitter": {"enabled": True}
                },
                "is_active": True,
                "version": "1.0.0"
            }
        }

    def __str__(self) -> str:
        """String representation of the persona"""
        status = "active" if self.is_active else "inactive"
        return f"Persona(id='{self.id}', name='{self.name}', status={status})"

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return (
            f"Persona(id='{self.id}', name='{self.name}', "
            f"memory_namespace='{self.memory_namespace}', is_active={self.is_active})"
        )
