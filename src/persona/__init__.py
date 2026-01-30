"""Persona management module

Handles multiple persona configurations, personalities, and persona-specific logic.
"""

from src.persona.models import Persona
from src.persona.manager import PersonaManager
from src.persona.config import (
    load_persona_config,
    load_persona_config_with_defaults,
    merge_configs,
    ConfigLoadError,
    ConfigValidationError,
)

__all__ = [
    "Persona",
    "PersonaManager",
    "load_persona_config",
    "load_persona_config_with_defaults",
    "merge_configs",
    "ConfigLoadError",
    "ConfigValidationError",
]
