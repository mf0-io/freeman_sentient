"""PersonaManager singleton for loading and managing personas"""

import os
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from src.persona.models import Persona


class PersonaManager:
    """Singleton manager for loading and managing personas

    PersonaManager is responsible for:
    - Loading persona configurations from YAML files
    - Maintaining a registry of all personas
    - Providing access to personas by ID
    - Filtering active personas
    - Validating persona configurations

    Usage:
        manager = PersonaManager()
        persona = manager.get_persona("freeman")
        active = manager.list_active_personas()
    """

    _instance: Optional['PersonaManager'] = None
    _initialized: bool = False

    def __new__(cls) -> 'PersonaManager':
        """Ensure only one instance exists (singleton pattern)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the PersonaManager

        Args:
            config_path: Path to personas.yaml config file.
                        Defaults to config/personas.yaml
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return

        self._personas: Dict[str, Persona] = {}
        self._config_path = config_path or "config/personas.yaml"
        self._personas_dir = Path("config")

        # Load personas if config exists
        if os.path.exists(self._config_path):
            self._load_personas()

        self._initialized = True

    def _load_personas(self) -> None:
        """Load all personas from the configuration file"""
        try:
            with open(self._config_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'personas' not in config:
                return

            for persona_entry in config['personas']:
                try:
                    persona = self._load_persona_from_entry(persona_entry)
                    if persona:
                        self._personas[persona.id] = persona
                except Exception as e:
                    # Log error but continue loading other personas
                    print(f"Warning: Failed to load persona {persona_entry.get('id')}: {e}")
                    continue

        except Exception as e:
            print(f"Warning: Failed to load personas config from {self._config_path}: {e}")

    def _load_persona_from_entry(self, entry: Dict) -> Optional[Persona]:
        """Load a single persona from a config entry

        Args:
            entry: Dictionary with persona metadata from personas.yaml

        Returns:
            Persona instance or None if loading failed
        """
        persona_id = entry.get('id')
        if not persona_id:
            return None

        # Load detailed config if config_file is specified
        detailed_config = {}
        config_file = entry.get('config_file')
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    detailed_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config file {config_file}: {e}")

        # Merge entry and detailed config
        persona_data = {
            'id': persona_id,
            'name': entry.get('name') or detailed_config.get('name', persona_id),
            'memory_namespace': entry.get('memory_namespace') or detailed_config.get('memory', {}).get('namespace', persona_id),
            'is_active': entry.get('is_active', True),
            'version': detailed_config.get('version'),
            'mission': detailed_config.get('mission'),
            'personality_config': detailed_config.get('personality', {}),
            'agent_configs': detailed_config.get('agents', {}),
            'platform_configs': detailed_config.get('platforms', {}),
            'llm_config': detailed_config.get('llm', {}),
            'behavior_config': detailed_config.get('behavior', {}),
        }

        # Validate and create Persona instance
        try:
            return Persona(**persona_data)
        except Exception as e:
            print(f"Warning: Failed to validate persona {persona_id}: {e}")
            return None

    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get a persona by ID

        Args:
            persona_id: Unique identifier for the persona

        Returns:
            Persona instance or None if not found
        """
        return self._personas.get(persona_id)

    def list_active_personas(self) -> List[Persona]:
        """Get all active personas

        Returns:
            List of active Persona instances
        """
        return [
            persona for persona in self._personas.values()
            if persona.is_active
        ]

    def list_all_personas(self) -> List[Persona]:
        """Get all personas (active and inactive)

        Returns:
            List of all Persona instances
        """
        return list(self._personas.values())

    def add_persona(self, persona: Persona) -> None:
        """Add or update a persona in the registry

        Args:
            persona: Persona instance to add/update
        """
        self._personas[persona.id] = persona

    def remove_persona(self, persona_id: str) -> bool:
        """Remove a persona from the registry

        Args:
            persona_id: ID of the persona to remove

        Returns:
            True if removed, False if not found
        """
        if persona_id in self._personas:
            del self._personas[persona_id]
            return True
        return False

    def validate_persona(self, persona: Persona) -> List[str]:
        """Validate a persona configuration

        Args:
            persona: Persona instance to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required fields
        if not persona.id:
            errors.append("Persona ID is required")

        if not persona.name:
            errors.append("Persona name is required")

        if not persona.memory_namespace:
            errors.append("Memory namespace is required")

        # Check namespace uniqueness
        for existing_id, existing_persona in self._personas.items():
            if existing_id != persona.id and existing_persona.memory_namespace == persona.memory_namespace:
                errors.append(f"Memory namespace '{persona.memory_namespace}' conflicts with persona '{existing_id}'")

        return errors

    def reload(self) -> None:
        """Reload all personas from config files"""
        self._personas.clear()
        if os.path.exists(self._config_path):
            self._load_personas()

    def __len__(self) -> int:
        """Return the number of loaded personas"""
        return len(self._personas)

    def __contains__(self, persona_id: str) -> bool:
        """Check if a persona exists"""
        return persona_id in self._personas

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        active_count = len(self.list_active_personas())
        total_count = len(self._personas)
        return f"PersonaManager(total={total_count}, active={active_count})"
