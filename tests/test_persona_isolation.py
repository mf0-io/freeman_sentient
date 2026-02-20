"""Tests for persona memory isolation

Verifies that:
- Personas have completely separate memory spaces
- Operations on one persona don't affect others
- Memory keys are properly namespaced
- All memory types are isolated
"""

import pytest
from src.memory.persona_memory import PersonaMemory, MemoryStore
from src.memory.isolation import (
    MemoryIsolationValidator,
    IsolationViolation,
    validate_persona_isolation
)


class TestMemoryStoreIsolation:
    """Test basic MemoryStore isolation"""

    def test_different_personas_different_stores(self):
        """Test that different personas get different memory stores"""
        store_a = MemoryStore("persona_a", "user")
        store_b = MemoryStore("persona_b", "user")

        store_a.set("key1", "value_a")
        store_b.set("key1", "value_b")

        assert store_a.get("key1") == "value_a"
        assert store_b.get("key1") == "value_b"

    def test_namespace_isolation(self):
        """Test that namespaces prevent cross-contamination"""
        store_a = MemoryStore("persona_a", "user")
        store_b = MemoryStore("persona_b", "user")

        store_a.set("shared_key", "value_from_a")

        # Persona B should not see persona A's data
        assert store_b.get("shared_key") is None

    def test_clear_only_affects_own_namespace(self):
        """Test that clearing one store doesn't affect another"""
        store_a = MemoryStore("persona_a", "user")
        store_b = MemoryStore("persona_b", "user")

        store_a.set("key1", "value_a")
        store_b.set("key1", "value_b")

        # Clear persona A's memory
        store_a.clear()

        # Persona A should be empty
        assert store_a.get("key1") is None

# Backward compatible
        # Persona B should still have its data
        assert store_b.get("key1") == "value_b"

    def test_keys_only_returns_own_keys(self):
        """Test that keys() only returns keys for the specific persona"""
        store_a = MemoryStore("persona_a", "user")
        store_b = MemoryStore("persona_b", "user")

        store_a.set("key1", "value_a")
        store_a.set("key2", "value_a2")
        store_b.set("key1", "value_b")
        store_b.set("key3", "value_b3")

        keys_a = set(store_a.keys())
        keys_b = set(store_b.keys())

        assert keys_a == {"key1", "key2"}
        assert keys_b == {"key1", "key3"}


class TestPersonaMemoryIsolation:
    """Test PersonaMemory isolation"""

    def test_separate_persona_memories(self):
        """Test that separate PersonaMemory instances are isolated"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Store data in both
        memory_a.user_memory.set("user123", {"name": "Alice"})
        memory_b.user_memory.set("user123", {"name": "Bob"})

        # Each should have their own data
        assert memory_a.user_memory.get("user123") == {"name": "Alice"}
        assert memory_b.user_memory.get("user123") == {"name": "Bob"}

    def test_all_memory_types_isolated(self):
        """Test that all memory types are isolated between personas"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Test each memory type
        memory_types = [
            ("user_memory", "user1", {"data": "a"}),
            ("relationship_memory", "rel1", {"level": "friend"}),
            ("action_memory", "action1", {"type": "like"}),
            ("emotional_memory", "emotion1", {"trigger": "betrayal"}),
            ("conversation_memory", "conv1", {"topic": "philosophy"})
        ]

        for memory_type, key, value_a in memory_types:
            value_b = {**value_a, "data": "b"}

            # Set in both personas
            getattr(memory_a, memory_type).set(key, value_a)
            getattr(memory_b, memory_type).set(key, value_b)

            # Verify isolation
            assert getattr(memory_a, memory_type).get(key) == value_a
            assert getattr(memory_b, memory_type).get(key) == value_b

    def test_clear_all_only_affects_own_memory(self):
        """Test that clear_all only clears the specific persona's memory"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Populate both personas
        memory_a.user_memory.set("user1", {"name": "Alice"})
        memory_a.relationship_memory.set("rel1", {"level": "friend"})

        memory_b.user_memory.set("user1", {"name": "Bob"})
        memory_b.relationship_memory.set("rel1", {"level": "ally"})

        # Clear persona A
        memory_a.clear_all()

        # Verify persona A is cleared
        assert memory_a.user_memory.get("user1") is None
        assert memory_a.relationship_memory.get("rel1") is None

        # Verify persona B is intact
        assert memory_b.user_memory.get("user1") == {"name": "Bob"}
        assert memory_b.relationship_memory.get("rel1") == {"level": "ally"}

    def test_invalid_persona_id_raises_error(self):
        """Test that invalid persona_id raises ValueError"""
        with pytest.raises(ValueError, match="persona_id must be a non-empty string"):
            PersonaMemory("")

        with pytest.raises(ValueError, match="persona_id must be a non-empty string"):
            PersonaMemory(None)

    def test_namespace_matches_persona_id(self):
        """Test that namespace correctly matches persona_id"""
        memory = PersonaMemory("freeman")
        assert memory.get_namespace() == "freeman"


class TestMemoryIsolationValidator:
    """Test MemoryIsolationValidator"""

    def test_register_persona(self):
        """Test registering personas for validation"""
        validator = MemoryIsolationValidator()
        memory = PersonaMemory("freeman")

        validator.register_persona("freeman", memory)

        assert "freeman" in validator.personas
        assert validator.personas["freeman"] == memory

    def test_duplicate_registration_raises_error(self):
        """Test that duplicate registration raises ValueError"""
        validator = MemoryIsolationValidator()
        memory = PersonaMemory("freeman")

        validator.register_persona("freeman", memory)

        with pytest.raises(ValueError, match="already registered"):
            validator.register_persona("freeman", memory)

    def test_validate_namespace_uniqueness_success(self):
        """Test namespace uniqueness validation succeeds with unique namespaces"""
        validator = MemoryIsolationValidator()

        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        validator.register_persona("freeman", memory_a)
        validator.register_persona("sidekick", memory_b)

        # Should pass without raising exception
        assert validator.validate_namespace_uniqueness() is True

    def test_validate_namespace_uniqueness_failure(self):
        """Test namespace uniqueness validation fails with duplicate namespaces"""
        validator = MemoryIsolationValidator()

        # Create two memories with same persona_id (same namespace)
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("freeman")

        validator.register_persona("freeman_1", memory_a)
        validator.register_persona("freeman_2", memory_b)

        with pytest.raises(IsolationViolation, match="Duplicate namespaces"):
            validator.validate_namespace_uniqueness()

    def test_validate_memory_isolation_success(self):
        """Test memory isolation validation succeeds with isolated memories"""
        validator = MemoryIsolationValidator()

        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        validator.register_persona("freeman", memory_a)
        validator.register_persona("sidekick", memory_b)

        # Should pass without raising exception
        assert validator.validate_memory_isolation("freeman", "sidekick", "user") is True

    def test_validate_memory_isolation_all_types(self):
        """Test isolation validation across all memory types"""
        validator = MemoryIsolationValidator()

        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        validator.register_persona("freeman", memory_a)
        validator.register_persona("sidekick", memory_b)

        # Should pass for all memory types
        assert validator.validate_all_memory_types_isolated("freeman", "sidekick") is True

    def test_validate_bidirectional_isolation(self):
        """Test bidirectional isolation validation"""
        validator = MemoryIsolationValidator()

        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        validator.register_persona("freeman", memory_a)
        validator.register_persona("sidekick", memory_b)

        # Should pass bidirectional validation
        assert validator.validate_bidirectional_isolation("freeman", "sidekick") is True

    def test_validate_key_namespacing(self):
        """Test that keys are properly namespaced"""
        validator = MemoryIsolationValidator()

        memory = PersonaMemory("freeman")
        validator.register_persona("freeman", memory)

        # Should pass namespacing validation
        assert validator.validate_key_namespacing("freeman", "user") is True

    def test_validate_clear_isolation(self):
        """Test that clearing one persona doesn't affect another"""
        validator = MemoryIsolationValidator()

        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        validator.register_persona("freeman", memory_a)
        validator.register_persona("sidekick", memory_b)

        # Should pass clear isolation validation
        assert validator.validate_clear_isolation("freeman", "sidekick") is True

    def test_validate_unregistered_persona_raises_error(self):
        """Test that validating unregistered persona raises ValueError"""
        validator = MemoryIsolationValidator()

        memory = PersonaMemory("freeman")
        validator.register_persona("freeman", memory)

        with pytest.raises(ValueError, match="not registered"):
            validator.validate_memory_isolation("freeman", "nonexistent")

    def test_run_full_validation(self):
        """Test complete validation suite"""
        validator = MemoryIsolationValidator()

        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")
        memory_c = PersonaMemory("villain")

        validator.register_persona("freeman", memory_a)
        validator.register_persona("sidekick", memory_b)
        validator.register_persona("villain", memory_c)

        results = validator.run_full_validation()

        assert results["status"] == "passed"
        assert results["total_personas"] == 3
        assert results["persona_pairs_tested"] == 3  # 3 personas = 3 pairs
        assert results["validations_run"] > 0
        assert results["validations_passed"] == results["validations_run"]

    def test_unregister_persona(self):
        """Test unregistering a persona"""
        validator = MemoryIsolationValidator()

        memory = PersonaMemory("freeman")
        validator.register_persona("freeman", memory)

        assert "freeman" in validator.personas

        validator.unregister_persona("freeman")

        assert "freeman" not in validator.personas


class TestQuickValidationFunction:
    """Test the quick validation helper function"""

    def test_validate_persona_isolation_success(self):
        """Test quick validation function with isolated personas"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Should pass without raising exception
        assert validate_persona_isolation(memory_a, memory_b) is True

    def test_validate_persona_isolation_with_data(self):
        """Test validation with actual data in memories"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Populate with data
        memory_a.user_memory.set("user1", {"name": "Alice"})
        memory_a.relationship_memory.set("rel1", {"level": "friend"})

        memory_b.user_memory.set("user1", {"name": "Bob"})
        memory_b.relationship_memory.set("rel1", {"level": "ally"})

        # Should still pass validation
        assert validate_persona_isolation(memory_a, memory_b) is True

        # Verify data is still intact and separate
        assert memory_a.user_memory.get("user1") == {"name": "Alice"}
        assert memory_b.user_memory.get("user1") == {"name": "Bob"}


class TestConcurrentPersonaOperations:
    """Test isolation with concurrent-like operations"""

    def test_multiple_personas_same_keys(self):
        """Test multiple personas using the same keys without interference"""
        personas = [
            PersonaMemory(f"persona_{i}")
            for i in range(5)
        ]

        # All personas set the same key
        for i, memory in enumerate(personas):
            memory.user_memory.set("shared_key", f"value_{i}")

        # Each persona should have its own value
        for i, memory in enumerate(personas):
            assert memory.user_memory.get("shared_key") == f"value_{i}"

    def test_interleaved_operations(self):
        """Test interleaved operations across personas"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Interleaved operations
        memory_a.user_memory.set("key1", "value_a1")
        memory_b.user_memory.set("key1", "value_b1")
        memory_a.user_memory.set("key2", "value_a2")
        memory_b.user_memory.set("key2", "value_b2")

        # Verify each persona has correct data
        assert memory_a.user_memory.get("key1") == "value_a1"
        assert memory_a.user_memory.get("key2") == "value_a2"
        assert memory_b.user_memory.get("key1") == "value_b1"
        assert memory_b.user_memory.get("key2") == "value_b2"

    def test_mass_operations_isolation(self):
        """Test isolation with many operations"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Perform many operations
        for i in range(100):
            memory_a.user_memory.set(f"key_{i}", f"value_a_{i}")
            memory_b.user_memory.set(f"key_{i}", f"value_b_{i}")

        # Verify all data is isolated
        for i in range(100):
            assert memory_a.user_memory.get(f"key_{i}") == f"value_a_{i}"
            assert memory_b.user_memory.get(f"key_{i}") == f"value_b_{i}"


class TestEdgeCases:
    """Test edge cases and corner scenarios"""

    def test_same_user_different_personas(self):
        """Test that same user ID can exist in different persona memories"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Same user ID, different data
        user_id = "user_12345"

        memory_a.user_memory.set(user_id, {
            "name": "Alice",
            "relationship": "ally",
            "interactions": 50
        })

        memory_b.user_memory.set(user_id, {
            "name": "Alice",  # Same person
            "relationship": "stranger",  # Different relationship with sidekick
            "interactions": 2
        })

        # Each persona should maintain separate relationship with the same user
        assert memory_a.user_memory.get(user_id)["relationship"] == "ally"
        assert memory_b.user_memory.get(user_id)["relationship"] == "stranger"

    def test_special_characters_in_keys(self):
        """Test isolation with special characters in keys"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        special_keys = [
            "key:with:colons",
            "key_with_underscores",
            "key-with-dashes",
            "key.with.dots",
            "key@with@at"
        ]

        for key in special_keys:
            memory_a.user_memory.set(key, "value_a")
            memory_b.user_memory.set(key, "value_b")

        for key in special_keys:
            assert memory_a.user_memory.get(key) == "value_a"
            assert memory_b.user_memory.get(key) == "value_b"

    def test_empty_memory_operations(self):
        """Test operations on empty memories"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Operations on empty memories should not interfere
        assert memory_a.user_memory.get("nonexistent") is None
        assert memory_b.user_memory.get("nonexistent") is None

        assert not memory_a.user_memory.exists("nonexistent")
        assert not memory_b.user_memory.exists("nonexistent")

    def test_delete_operations_isolated(self):
        """Test that delete operations are isolated"""
        memory_a = PersonaMemory("freeman")
        memory_b = PersonaMemory("sidekick")

        # Set same key in both
        memory_a.user_memory.set("key", "value_a")
        memory_b.user_memory.set("key", "value_b")

        # Delete from persona A
        assert memory_a.user_memory.delete("key") is True

        # Persona A should not have it
        assert memory_a.user_memory.get("key") is None

        # Persona B should still have it
        assert memory_b.user_memory.get("key") == "value_b"
