"""Integration tests for multi-persona scenarios

Verifies end-to-end functionality:
- Multiple personas can be loaded and run simultaneously
- Personas have completely separate memories
- Agents work correctly with different persona contexts
- Orchestrator routes messages to correct personas
- Concurrent operations maintain isolation
"""

import os
import tempfile

import pytest
import yaml

from src.persona.manager import PersonaManager
from src.persona.models import Persona
from src.memory.persona_memory import PersonaMemory
from src.memory.isolation import validate_persona_isolation
from src.agents.base import BaseAgent
from src.agents.orchestrator import Orchestrator


class TestMultiPersonaLoading:
    """Test loading and managing multiple personas"""

    def test_load_multiple_personas_from_config(self):
        """Test loading multiple personas from YAML config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create config for multiple personas
            config = {
                'personas': [
                    {
                        'id': 'freeman',
                        'name': 'Mr. Freeman',
                        'memory_namespace': 'freeman',
                        'is_active': True
                    },
                    {
                        'id': 'philosopher',
                        'name': 'The Philosopher',
                        'memory_namespace': 'philosopher',
                        'is_active': True
                    },
                    {
                        'id': 'activist',
                        'name': 'The Activist',
                        'memory_namespace': 'activist',
                        'is_active': True
                    }
                ]
            }

            config_path = os.path.join(tmpdir, 'personas.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=config_path)

            # Verify all personas loaded
            assert len(manager) == 3
            assert "freeman" in manager
            assert "philosopher" in manager
            assert "activist" in manager

            # Verify all are active
            active = manager.list_active_personas()
            assert len(active) == 3

    def test_load_personas_with_mixed_active_status(self):
        """Test loading personas with different active statuses"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'personas': [
                    {
                        'id': 'active1',
                        'name': 'Active Persona 1',
                        'memory_namespace': 'active1',
                        'is_active': True
                    },
                    {
                        'id': 'active2',
                        'name': 'Active Persona 2',
                        'memory_namespace': 'active2',
                        'is_active': True
                    },
                    {
                        'id': 'inactive1',
                        'name': 'Inactive Persona',
                        'memory_namespace': 'inactive1',
                        'is_active': False
                    }
                ]
            }

            config_path = os.path.join(tmpdir, 'personas.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=config_path)

            # Verify counts
            assert len(manager) == 3
            assert len(manager.list_active_personas()) == 2
            assert len(manager.list_all_personas()) == 3


class TestMultiPersonaMemoryIsolation:
    """Test complete memory isolation between multiple personas"""

    def test_separate_user_memories(self):
        """Test that user memories are completely separate"""
        memory_freeman = PersonaMemory("freeman")
        memory_philosopher = PersonaMemory("philosopher")
        memory_activist = PersonaMemory("activist")

        # Same user interacts with all three personas
        user_id = "user_12345"

        memory_freeman.user_memory.set(user_id, {
            "name": "Alice",
            "interactions": 50,
            "sentiment": "positive"
        })

        memory_philosopher.user_memory.set(user_id, {
            "name": "Alice",
            "interactions": 10,
            "sentiment": "neutral"
        })

        memory_activist.user_memory.set(user_id, {
            "name": "Alice",
            "interactions": 100,
            "sentiment": "very_positive"
        })

        # Each persona should have independent view of the user
        freeman_data = memory_freeman.user_memory.get(user_id)
        philosopher_data = memory_philosopher.user_memory.get(user_id)
        activist_data = memory_activist.user_memory.get(user_id)

        assert freeman_data["interactions"] == 50
        assert philosopher_data["interactions"] == 10
        assert activist_data["interactions"] == 100

        # Verify isolation
        assert validate_persona_isolation(memory_freeman, memory_philosopher)
        assert validate_persona_isolation(memory_freeman, memory_activist)
        assert validate_persona_isolation(memory_philosopher, memory_activist)

    def test_separate_relationship_memories(self):
        """Test that relationship memories are isolated"""
        memory_a = PersonaMemory("persona_a")
        memory_b = PersonaMemory("persona_b")

        user_id = "user_123"

        # Same user has different relationships with each persona
        memory_a.relationship_memory.set(user_id, {
            "level": "ally",
            "trust_score": 95
        })

        memory_b.relationship_memory.set(user_id, {
            "level": "stranger",
            "trust_score": 10
        })

        # Verify independent relationships
        rel_a = memory_a.relationship_memory.get(user_id)
        rel_b = memory_b.relationship_memory.get(user_id)

        assert rel_a["level"] == "ally"
        assert rel_b["level"] == "stranger"
        assert rel_a["trust_score"] != rel_b["trust_score"]

    def test_separate_action_memories(self):
        """Test that action memories are isolated"""
        memory_a = PersonaMemory("persona_a")
        memory_b = PersonaMemory("persona_b")

        user_id = "user_123"

        # User performs different actions with each persona
        memory_a.action_memory.set(user_id, {
            "likes": 50,
            "comments": 20,
            "reposts": 5
        })

        memory_b.action_memory.set(user_id, {
            "likes": 2,
            "comments": 0,
            "reposts": 0
        })

        actions_a = memory_a.action_memory.get(user_id)
        actions_b = memory_b.action_memory.get(user_id)

        assert actions_a["likes"] == 50
        assert actions_b["likes"] == 2

    def test_all_memory_types_isolated_across_personas(self):
        """Test comprehensive isolation across all memory types"""
        personas = [
            PersonaMemory(f"persona_{i}")
            for i in range(5)
        ]

        # Each persona stores different data in all memory types
        for i, memory in enumerate(personas):
            memory.user_memory.set("user1", {"persona_index": i})
            memory.relationship_memory.set("user1", {"level": f"level_{i}"})
            memory.action_memory.set("action1", {"count": i * 10})
            memory.emotional_memory.set("emotion1", {"intensity": i})
            memory.conversation_memory.set("conv1", {"turn": i})

        # Verify each persona has its own data
        for i, memory in enumerate(personas):
            assert memory.user_memory.get("user1")["persona_index"] == i
            assert memory.relationship_memory.get("user1")["level"] == f"level_{i}"
            assert memory.action_memory.get("action1")["count"] == i * 10
            assert memory.emotional_memory.get("emotion1")["intensity"] == i
            assert memory.conversation_memory.get("conv1")["turn"] == i

        # Verify pairwise isolation
        for i in range(len(personas)):
            for j in range(i + 1, len(personas)):
                assert validate_persona_isolation(personas[i], personas[j])


class TestMultiPersonaAgentIntegration:
    """Test agents working with multiple persona contexts"""

    def test_base_agent_with_different_personas(self):
        """Test BaseAgent works correctly with different personas"""
        freeman = Persona(
            id="freeman",
            name="Mr. Freeman",
            personality_config={"tone": "sarcastic"},
            memory_namespace="freeman"
        )

        philosopher = Persona(
            id="philosopher",
            name="The Philosopher",
            personality_config={"tone": "contemplative"},
            memory_namespace="philosopher"
        )

        agent_freeman = BaseAgent(freeman)
        agent_philosopher = BaseAgent(philosopher)

        # Verify agents have correct persona context
        assert agent_freeman.persona_id == "freeman"
        assert agent_philosopher.persona_id == "philosopher"

        assert agent_freeman.personality_config["tone"] == "sarcastic"
        assert agent_philosopher.personality_config["tone"] == "contemplative"

        # Verify agents have separate memories
        agent_freeman.memory.user_memory.set("user1", {"data": "freeman"})
        agent_philosopher.memory.user_memory.set("user1", {"data": "philosopher"})

        assert agent_freeman.memory.user_memory.get("user1")["data"] == "freeman"
        assert agent_philosopher.memory.user_memory.get("user1")["data"] == "philosopher"

    def test_agents_maintain_separate_state(self):
        """Test that multiple agents maintain separate state"""
        personas = [
            Persona(
                id=f"persona_{i}",
                name=f"Persona {i}",
                personality_config={"index": i},
                memory_namespace=f"persona_{i}"
            )
            for i in range(3)
        ]

        agents = [BaseAgent(persona) for persona in personas]

        # Each agent stores data in memory
        for i, agent in enumerate(agents):
            agent.memory.user_memory.set("test_key", {"agent_index": i})

        # Verify each agent has its own data
        for i, agent in enumerate(agents):
            data = agent.memory.user_memory.get("test_key")
            assert data["agent_index"] == i


class TestOrchestratorMultiPersona:
    """Test Orchestrator with multiple personas"""

    def test_orchestrator_loads_multiple_personas(self):
        """Test Orchestrator loads multiple personas"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'personas': [
                    {
                        'id': 'persona1',
                        'name': 'Persona 1',
                        'memory_namespace': 'persona1',
                        'is_active': True
                    },
                    {
                        'id': 'persona2',
                        'name': 'Persona 2',
                        'memory_namespace': 'persona2',
                        'is_active': True
                    }
                ]
            }

            config_path = os.path.join(tmpdir, 'personas.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=config_path)
            orchestrator = Orchestrator(persona_manager=manager)

            assert orchestrator.persona_count == 2
            active = orchestrator.get_active_personas()
            assert len(active) == 2

    def test_orchestrator_routes_to_explicit_persona(self):
        """Test Orchestrator routes message to explicitly specified persona"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'personas': [
                    {
                        'id': 'freeman',
                        'name': 'Freeman',
                        'memory_namespace': 'freeman',
                        'is_active': True
                    },
                    {
                        'id': 'philosopher',
                        'name': 'Philosopher',
                        'memory_namespace': 'philosopher',
                        'is_active': True
                    }
                ]
            }

            config_path = os.path.join(tmpdir, 'personas.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=config_path)
            orchestrator = Orchestrator(persona_manager=manager)

            # Route to specific persona
            persona = orchestrator.route_to_persona(
                message="Hello",
                platform="telegram",
                user_id="user1",
                persona_id="philosopher"
            )

            assert persona is not None
            assert persona.id == "philosopher"

    def test_orchestrator_process_message_with_different_personas(self):
        """Test processing messages through different personas"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'personas': [
                    {
                        'id': 'persona1',
                        'name': 'Persona 1',
                        'memory_namespace': 'persona1',
                        'is_active': True
                    },
                    {
                        'id': 'persona2',
                        'name': 'Persona 2',
                        'memory_namespace': 'persona2',
                        'is_active': True
                    }
                ]
            }

            config_path = os.path.join(tmpdir, 'personas.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=config_path)
            orchestrator = Orchestrator(persona_manager=manager)

            # Process message through persona1
            response1 = orchestrator.process_message(
                message="Test message",
                platform="telegram",
                user_id="user1",
                persona_id="persona1"
            )

            assert response1["persona_id"] == "persona1"
            assert "response_text" in response1

            # Process message through persona2
            response2 = orchestrator.process_message(
                message="Test message",
                platform="telegram",
                user_id="user1",
                persona_id="persona2"
            )

            assert response2["persona_id"] == "persona2"
            assert response1["persona_id"] != response2["persona_id"]

    def test_orchestrator_handles_no_active_personas(self):
        """Test Orchestrator handles case with no active personas"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'personas': [
                    {
                        'id': 'inactive',
                        'name': 'Inactive',
                        'memory_namespace': 'inactive',
                        'is_active': False
                    }
                ]
            }

            config_path = os.path.join(tmpdir, 'personas.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=config_path)
            orchestrator = Orchestrator(persona_manager=manager)

            # Should raise error when trying to process message
            with pytest.raises(ValueError, match="No active persona"):
                orchestrator.process_message(
                    message="Test",
                    platform="telegram",
                    user_id="user1"
                )

    def test_orchestrator_reload_updates_personas(self):
        """Test Orchestrator can reload personas"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'personas': [
                    {
                        'id': 'persona1',
                        'name': 'Persona 1',
                        'memory_namespace': 'persona1',
                        'is_active': True
                    }
                ]
            }

            config_path = os.path.join(tmpdir, 'personas.yaml')
            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            manager = PersonaManager(config_path=config_path)
            orchestrator = Orchestrator(persona_manager=manager)

            assert orchestrator.persona_count == 1

            # Update config file
            config['personas'].append({
                'id': 'persona2',
                'name': 'Persona 2',
                'memory_namespace': 'persona2',
                'is_active': True
            })

            with open(config_path, 'w') as f:
                yaml.dump(config, f)

            # Reload
            orchestrator.reload_personas()

            assert orchestrator.persona_count == 2


class TestConcurrentMultiPersonaOperations:
    """Test concurrent operations across multiple personas"""

    def test_concurrent_memory_operations(self):
        """Test concurrent memory operations maintain isolation"""
        personas = [PersonaMemory(f"persona_{i}") for i in range(10)]

        # Simulate concurrent operations
        for iteration in range(100):
            for i, memory in enumerate(personas):
                key = f"key_{iteration}"
                value = f"value_{i}_{iteration}"
                memory.user_memory.set(key, value)

        # Verify all data is correctly isolated
        for iteration in range(100):
            for i, memory in enumerate(personas):
                key = f"key_{iteration}"
                expected_value = f"value_{i}_{iteration}"
                actual_value = memory.user_memory.get(key)
                assert actual_value == expected_value

    def test_interleaved_persona_operations(self):
        """Test interleaved operations across personas"""
        memory_a = PersonaMemory("persona_a")
        memory_b = PersonaMemory("persona_b")
        memory_c = PersonaMemory("persona_c")

        # Interleaved operations
        memory_a.user_memory.set("key1", "a1")
        memory_b.user_memory.set("key1", "b1")
        memory_c.user_memory.set("key1", "c1")

        memory_a.relationship_memory.set("rel1", "a_rel")
        memory_b.relationship_memory.set("rel1", "b_rel")

        memory_c.action_memory.set("action1", "c_action")
        memory_a.action_memory.set("action1", "a_action")

        # Verify all operations maintained isolation
        assert memory_a.user_memory.get("key1") == "a1"
        assert memory_b.user_memory.get("key1") == "b1"
        assert memory_c.user_memory.get("key1") == "c1"

        assert memory_a.relationship_memory.get("rel1") == "a_rel"
        assert memory_b.relationship_memory.get("rel1") == "b_rel"
        assert memory_c.relationship_memory.get("rel1") is None

        assert memory_c.action_memory.get("action1") == "c_action"
        assert memory_a.action_memory.get("action1") == "a_action"
        assert memory_b.action_memory.get("action1") is None


class TestEndToEndMultiPersonaScenario:
    """End-to-end test of complete multi-persona system"""

    def test_complete_multi_persona_workflow(self):
        """Test complete workflow with multiple personas"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create detailed configs for multiple personas
            freeman_config = {
                'id': 'freeman',
                'name': 'Mr. Freeman',
                'version': '1.0.0',
                'personality': {'tone': 'sarcastic'},
                'memory': {'namespace': 'freeman'},
                'agents': {'orchestrator': {'enabled': True}}
            }

            philosopher_config = {
                'id': 'philosopher',
                'name': 'The Philosopher',
                'version': '1.0.0',
                'personality': {'tone': 'contemplative'},
                'memory': {'namespace': 'philosopher'},
                'agents': {'orchestrator': {'enabled': True}}
            }

            # Write detailed configs
            freeman_path = os.path.join(tmpdir, 'freeman.yaml')
            with open(freeman_path, 'w') as f:
                yaml.dump(freeman_config, f)

            philosopher_path = os.path.join(tmpdir, 'philosopher.yaml')
            with open(philosopher_path, 'w') as f:
                yaml.dump(philosopher_config, f)

            # Create main config
            main_config = {
                'personas': [
                    {
                        'id': 'freeman',
                        'name': 'Mr. Freeman',
                        'config_file': freeman_path,
                        'memory_namespace': 'freeman',
                        'is_active': True
                    },
                    {
                        'id': 'philosopher',
                        'name': 'The Philosopher',
                        'config_file': philosopher_path,
                        'memory_namespace': 'philosopher',
                        'is_active': True
                    }
                ]
            }

            main_path = os.path.join(tmpdir, 'personas.yaml')
            with open(main_path, 'w') as f:
                yaml.dump(main_config, f)

            # Reset singleton
            PersonaManager._instance = None
            PersonaManager._initialized = False

            # Initialize system
            manager = PersonaManager(config_path=main_path)
            orchestrator = Orchestrator(persona_manager=manager)

            # Verify system initialization
            assert len(manager) == 2
            assert orchestrator.persona_count == 2

            # Get personas
            freeman = manager.get_persona("freeman")
            philosopher = manager.get_persona("philosopher")

            assert freeman is not None
            assert philosopher is not None

            # Create agents
            agent_freeman = BaseAgent(freeman)
            agent_philosopher = BaseAgent(philosopher)

            # Simulate user interactions with both personas
            user_id = "user_12345"

            # User interacts with Freeman
            agent_freeman.memory.user_memory.set(user_id, {
                "name": "Alice",
                "interactions": 50
            })
            agent_freeman.memory.relationship_memory.set(user_id, {
                "level": "ally"
            })

            # Same user interacts with Philosopher (different history)
            agent_philosopher.memory.user_memory.set(user_id, {
                "name": "Alice",
                "interactions": 5
            })
            agent_philosopher.memory.relationship_memory.set(user_id, {
                "level": "stranger"
            })

            # Process messages through orchestrator
            response_freeman = orchestrator.process_message(
                message="What do you think about society?",
                platform="telegram",
                user_id=user_id,
                persona_id="freeman"
            )

            response_philosopher = orchestrator.process_message(
                message="What do you think about society?",
                platform="telegram",
                user_id=user_id,
                persona_id="philosopher"
            )

            # Verify responses are from correct personas
            assert response_freeman["persona_id"] == "freeman"
            assert response_philosopher["persona_id"] == "philosopher"

            # Verify memories remain isolated
            freeman_user = agent_freeman.memory.user_memory.get(user_id)
            philosopher_user = agent_philosopher.memory.user_memory.get(user_id)

            assert freeman_user["interactions"] == 50
            assert philosopher_user["interactions"] == 5

            freeman_rel = agent_freeman.memory.relationship_memory.get(user_id)
            philosopher_rel = agent_philosopher.memory.relationship_memory.get(user_id)

            assert freeman_rel["level"] == "ally"
            assert philosopher_rel["level"] == "stranger"

            # Verify complete isolation
            assert validate_persona_isolation(
                agent_freeman.memory,
                agent_philosopher.memory
            )
