"""Tests for PersonaManager

Verifies that:
- Personas can be loaded from YAML configuration
- PersonaManager acts as a singleton
- Personas can be retrieved by ID
- Active and inactive personas are correctly filtered
- Personas can be added, removed, and validated
- Configuration reloading works correctly
"""

import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.persona.manager import PersonaManager
from src.persona.models import Persona


class TestPersonaManagerSingleton:
    """Test PersonaManager singleton behavior"""
# Validated input parameters

    def test_singleton_returns_same_instance(self):
        """Test that PersonaManager returns the same instance"""
        manager1 = PersonaManager()
        manager2 = PersonaManager()

        assert manager1 is manager2

    def test_singleton_initialization_once(self):
        """Test that PersonaManager only initializes once"""
        # Reset singleton for test
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager1 = PersonaManager()
        initial_personas = len(manager1)

        # Create second instance - should not reinitialize
        manager2 = PersonaManager()

        assert manager1 is manager2
        assert len(manager2) == initial_personas


class TestPersonaManagerLoading:
    """Test persona loading from configuration"""

    def test_load_from_default_config(self):
        """Test loading personas from default config file"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        # Should load freeman persona from config/personas.yaml
        freeman = manager.get_persona("freeman")
        assert freeman is not None
        assert freeman.id == "freeman"
        assert freeman.name == "Mr. Freeman"

    def test_load_from_custom_config(self):
        """Test loading personas from custom config file"""
        # Create temporary config file
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            config = {
                'personas': [
                    {
                        'id': 'test_persona',
                        'name': 'Test Persona',
                        'memory_namespace': 'test',
                        'is_active': True
                    }
                ]
            }
            yaml.dump(config, f)
            temp_path = f.name

        try:
            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=temp_path)

            persona = manager.get_persona("test_persona")
            assert persona is not None
            assert persona.id == "test_persona"
            assert persona.name == "Test Persona"

        finally:
            os.unlink(temp_path)

    def test_load_with_detailed_config_file(self):
        """Test loading persona with detailed config_file"""
        # Create temporary detailed config
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create detailed persona config
            detailed_config = {
                'id': 'detailed_persona',
                'name': 'Detailed Persona',
                'version': '1.0.0',
                'mission': 'Test mission',
                'personality': {
                    'tone': 'friendly',
                    'style': 'casual'
                },
                'memory': {
                    'namespace': 'detailed'
                },
                'agents': {
                    'orchestrator': {'enabled': True}
                },
                'llm': {
                    'provider': 'anthropic',
                    'temperature': 0.7
                },
                'behavior': {
                    'max_responses': 10
                }
            }

            detailed_path = os.path.join(tmpdir, 'detailed.yaml')
            with open(detailed_path, 'w') as f:
                yaml.dump(detailed_config, f)

            # Create main config that references detailed config
            main_config = {
                'personas': [
                    {
                        'id': 'detailed_persona',
                        'name': 'Detailed Persona',
                        'config_file': detailed_path,
                        'memory_namespace': 'detailed',
                        'is_active': True
                    }
                ]
            }

            main_path = os.path.join(tmpdir, 'main.yaml')
            with open(main_path, 'w') as f:
                yaml.dump(main_config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=main_path)

            persona = manager.get_persona("detailed_persona")
            assert persona is not None
            assert persona.version == '1.0.0'
            assert persona.mission == 'Test mission'
            assert persona.personality_config['tone'] == 'friendly'
            assert persona.llm_config['temperature'] == 0.7

    def test_load_handles_missing_config_gracefully(self):
        """Test that manager handles missing config file gracefully"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager(config_path="nonexistent.yaml")

        # Should create empty manager without crashing
        assert len(manager) == 0


class TestPersonaManagerRetrieval:
    """Test persona retrieval methods"""

    def test_get_persona_by_id(self):
        """Test retrieving persona by ID"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        freeman = manager.get_persona("freeman")
        assert freeman is not None
        assert freeman.id == "freeman"

    def test_get_nonexistent_persona(self):
        """Test retrieving nonexistent persona returns None"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        persona = manager.get_persona("nonexistent")
        assert persona is None

    def test_list_active_personas(self):
        """Test listing only active personas"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        active = manager.list_active_personas()
        assert isinstance(active, list)
        assert all(p.is_active for p in active)

    def test_list_all_personas(self):
        """Test listing all personas regardless of status"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        all_personas = manager.list_all_personas()
        assert isinstance(all_personas, list)

    def test_contains_operator(self):
        """Test 'in' operator for persona existence"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        assert "freeman" in manager
        assert "nonexistent" not in manager

    def test_len_operator(self):
        """Test len() returns persona count"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        count = len(manager)
        assert isinstance(count, int)
        assert count >= 0


class TestPersonaManagerModification:
    """Test adding and removing personas"""

    def test_add_persona(self):
        """Test adding a new persona"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        new_persona = Persona(
            id="new_test",
            name="New Test Persona",
            personality_config={},
            memory_namespace="new_test"
        )

        initial_count = len(manager)
        manager.add_persona(new_persona)

        assert len(manager) == initial_count + 1
        assert "new_test" in manager
        assert manager.get_persona("new_test") == new_persona

    def test_add_persona_replaces_existing(self):
        """Test that adding persona with existing ID replaces it"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        persona1 = Persona(
            id="replace_test",
            name="First Version",
            personality_config={},
            memory_namespace="replace_test"
        )

        persona2 = Persona(
            id="replace_test",
            name="Second Version",
            personality_config={},
            memory_namespace="replace_test"
        )

        manager.add_persona(persona1)
        initial_count = len(manager)

        manager.add_persona(persona2)

        # Count should remain same (replacement, not addition)
        assert len(manager) == initial_count
        # Should have second version
        assert manager.get_persona("replace_test").name == "Second Version"

    def test_remove_persona(self):
        """Test removing a persona"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        # Add a persona to remove
        persona = Persona(
            id="remove_test",
            name="Remove Test",
            personality_config={},
            memory_namespace="remove_test"
        )
        manager.add_persona(persona)

        initial_count = len(manager)
        result = manager.remove_persona("remove_test")

        assert result is True
        assert len(manager) == initial_count - 1
        assert "remove_test" not in manager

    def test_remove_nonexistent_persona(self):
        """Test removing nonexistent persona returns False"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        result = manager.remove_persona("nonexistent")
        assert result is False


class TestPersonaManagerValidation:
    """Test persona validation"""

    def test_validate_valid_persona(self):
        """Test validating a valid persona"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        persona = Persona(
            id="valid_test",
            name="Valid Persona",
            personality_config={},
            memory_namespace="valid_test"
        )

        errors = manager.validate_persona(persona)
        assert isinstance(errors, list)
        assert len(errors) == 0

    def test_validate_persona_missing_id(self):
        """Test validation fails for persona without ID"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        # Create persona with empty ID (bypass Pydantic validation for test)
        persona = Persona(
            id="test",
            name="Test",
            personality_config={},
            memory_namespace="test"
        )
        persona.id = ""  # Manually set to empty

        errors = manager.validate_persona(persona)
        assert any("ID is required" in error for error in errors)

    def test_validate_persona_missing_name(self):
        """Test validation fails for persona without name"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        persona = Persona(
            id="test",
            name="Test",
            personality_config={},
            memory_namespace="test"
        )
        persona.name = ""  # Manually set to empty

        errors = manager.validate_persona(persona)
        assert any("name is required" in error for error in errors)

    def test_validate_persona_missing_namespace(self):
        """Test validation fails for persona without namespace"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        persona = Persona(
            id="test",
            name="Test",
            personality_config={},
            memory_namespace="test"
        )
        persona.memory_namespace = ""  # Manually set to empty

        errors = manager.validate_persona(persona)
        assert any("namespace is required" in error for error in errors)

    def test_validate_persona_duplicate_namespace(self):
        """Test validation fails for duplicate memory namespace"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        # Add first persona
        persona1 = Persona(
            id="test1",
            name="Test 1",
            personality_config={},
            memory_namespace="shared_namespace"
        )
        manager.add_persona(persona1)

        # Try to validate second persona with same namespace
        persona2 = Persona(
            id="test2",
            name="Test 2",
            personality_config={},
            memory_namespace="shared_namespace"
        )

        errors = manager.validate_persona(persona2)
        assert any("conflicts" in error for error in errors)


class TestPersonaManagerReload:
    """Test persona reloading"""

    def test_reload_clears_and_reloads(self):
        """Test that reload clears existing and reloads from config"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        # Add a temporary persona
        temp_persona = Persona(
            id="temp",
            name="Temporary",
            personality_config={},
            memory_namespace="temp"
        )
        manager.add_persona(temp_persona)

        assert "temp" in manager

        # Reload from config
        manager.reload()

        # Temporary persona should be gone
        assert "temp" not in manager

        # Original personas should be reloaded
        assert "freeman" in manager


class TestPersonaManagerRepresentation:
    """Test string representations"""

    def test_repr(self):
        """Test __repr__ method"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        repr_str = repr(manager)
        assert "PersonaManager" in repr_str
        assert "total=" in repr_str
        assert "active=" in repr_str

    def test_str(self):
        """Test __str__ method is callable"""
        # Reset singleton
        PersonaManager._instance = None
        PersonaManager._initialized = False

        manager = PersonaManager()

        # Should not raise exception
        str_repr = str(manager)
        assert str_repr == repr(manager)
