"""Memory isolation validation utilities

Provides validation functions to ensure complete memory isolation between personas.
These validators help detect any memory leaks or cross-persona contamination.
"""

from typing import List, Set, Dict, Any, Optional
from src.memory.persona_memory import PersonaMemory, MemoryStore


class IsolationViolation(Exception):
    """Exception raised when memory isolation is violated"""
    pass


class MemoryIsolationValidator:
    """Validates memory isolation between personas

    This validator ensures that:
    - Each persona has completely separate memory spaces
    - Operations on one persona's memory do not affect others
    - No cross-contamination of data between personas
    - Memory keys are properly namespaced
    """

    def __init__(self):
        """Initialize the isolation validator"""
        self.personas: Dict[str, PersonaMemory] = {}

    def register_persona(self, persona_id: str, memory: PersonaMemory) -> None:
        """Register a persona memory for validation

        Args:
            persona_id: Unique identifier for the persona
            memory: PersonaMemory instance for this persona

        Raises:
            ValueError: If persona_id is already registered
        """
        if persona_id in self.personas:
            raise ValueError(f"Persona '{persona_id}' already registered")

        self.personas[persona_id] = memory

    def unregister_persona(self, persona_id: str) -> None:
        """Unregister a persona from validation

        Args:
            persona_id: Identifier of persona to unregister
        """
        if persona_id in self.personas:
            del self.personas[persona_id]

    def validate_namespace_uniqueness(self) -> bool:
        """Validate that each persona has a unique namespace

        Returns:
            True if all namespaces are unique

        Raises:
            IsolationViolation: If duplicate namespaces detected
        """
        namespaces = [memory.get_namespace() for memory in self.personas.values()]
        unique_namespaces = set(namespaces)

        if len(namespaces) != len(unique_namespaces):
            duplicates = [ns for ns in namespaces if namespaces.count(ns) > 1]
            raise IsolationViolation(
                f"Duplicate namespaces detected: {set(duplicates)}"
            )

        return True

    def validate_memory_isolation(
        self,
        persona_a: str,
        persona_b: str,
        memory_type: str = "user"
    ) -> bool:
        """Validate that two personas have isolated memory

        Args:
            persona_a: ID of first persona
            persona_b: ID of second persona
            memory_type: Type of memory to check (user, relationship, etc.)

        Returns:
            True if memories are isolated

        Raises:
            IsolationViolation: If memories are not isolated
            ValueError: If persona not registered
        """
        if persona_a not in self.personas:
            raise ValueError(f"Persona '{persona_a}' not registered")
        if persona_b not in self.personas:
            raise ValueError(f"Persona '{persona_b}' not registered")

        memory_a = self.personas[persona_a]
        memory_b = self.personas[persona_b]

        # Get the appropriate memory stores
        store_a = self._get_memory_store(memory_a, memory_type)
        store_b = self._get_memory_store(memory_b, memory_type)

        # Test isolation by setting a value in persona A
        test_key = "__isolation_test__"
        test_value = f"test_value_for_{persona_a}"

        store_a.set(test_key, test_value)

        # Verify persona B cannot see this value
        value_in_b = store_b.get(test_key)

        # Clean up
        store_a.delete(test_key)

        if value_in_b is not None:
            raise IsolationViolation(
                f"Memory leak detected: Persona '{persona_b}' can access "
                f"data from persona '{persona_a}' in {memory_type} memory"
            )

        return True

    def validate_all_memory_types_isolated(
        self,
        persona_a: str,
        persona_b: str
    ) -> bool:
        """Validate isolation across all memory types

        Args:
            persona_a: ID of first persona
            persona_b: ID of second persona

        Returns:
            True if all memory types are isolated

        Raises:
            IsolationViolation: If any memory type is not isolated
        """
        memory_types = ["user", "relationship", "action", "emotional", "conversation"]

        for memory_type in memory_types:
            self.validate_memory_isolation(persona_a, persona_b, memory_type)

        return True

    def validate_bidirectional_isolation(
        self,
        persona_a: str,
        persona_b: str
    ) -> bool:
        """Validate bidirectional memory isolation

        Ensures that:
        - A cannot access B's memory
        - B cannot access A's memory

        Args:
            persona_a: ID of first persona
            persona_b: ID of second persona

        Returns:
            True if bidirectionally isolated

        Raises:
            IsolationViolation: If isolation violated in either direction
        """
        # Test A -> B isolation
        self.validate_all_memory_types_isolated(persona_a, persona_b)

        # Test B -> A isolation
        self.validate_all_memory_types_isolated(persona_b, persona_a)

        return True

    def validate_key_namespacing(
        self,
        persona_id: str,
        memory_type: str = "user"
    ) -> bool:
        """Validate that keys are properly namespaced

        Args:
            persona_id: ID of persona to check
            memory_type: Type of memory to check

        Returns:
            True if keys are properly namespaced

        Raises:
            IsolationViolation: If keys lack proper namespace
        """
        if persona_id not in self.personas:
            raise ValueError(f"Persona '{persona_id}' not registered")

        memory = self.personas[persona_id]
        store = self._get_memory_store(memory, memory_type)

        # Set a test value
        test_key = "test_namespacing"
        test_value = "test"
        store.set(test_key, test_value)

        # Check the internal namespaced key
        expected_namespace = f"{persona_id}:{memory_type}:{test_key}"

        # Access internal store to verify namespacing
        if hasattr(store, '_store'):
            internal_keys = list(store._store.keys())
            namespaced_key_found = any(
                expected_namespace == key for key in internal_keys
            )

            # Clean up
            store.delete(test_key)

            if not namespaced_key_found:
                raise IsolationViolation(
                    f"Key namespacing failed for persona '{persona_id}'. "
                    f"Expected namespace pattern: {expected_namespace}"
                )

        # Clean up if not already done
        store.delete(test_key)

        return True

    def validate_clear_isolation(
        self,
        persona_a: str,
        persona_b: str
    ) -> bool:
        """Validate that clearing one persona's memory doesn't affect another

        Args:
            persona_a: ID of first persona
            persona_b: ID of second persona

        Returns:
            True if clear operations are isolated

        Raises:
            IsolationViolation: If clear affects other persona
        """
        if persona_a not in self.personas:
            raise ValueError(f"Persona '{persona_a}' not registered")
        if persona_b not in self.personas:
            raise ValueError(f"Persona '{persona_b}' not registered")

        memory_a = self.personas[persona_a]
        memory_b = self.personas[persona_b]

        # Set data in both personas
        test_key = "clear_test"
        memory_a.user_memory.set(test_key, "value_a")
        memory_b.user_memory.set(test_key, "value_b")

        # Clear persona A's memory
        memory_a.clear_all()

        # Verify persona A's memory is cleared
        value_a = memory_a.user_memory.get(test_key)
        if value_a is not None:
            raise IsolationViolation(
                f"Clear failed: Persona '{persona_a}' still has data after clear"
            )

        # Verify persona B's memory is intact
        value_b = memory_b.user_memory.get(test_key)
        if value_b != "value_b":
            raise IsolationViolation(
                f"Clear leaked: Persona '{persona_b}' lost data when "
                f"persona '{persona_a}' was cleared"
            )

        # Clean up
        memory_b.user_memory.delete(test_key)

        return True

    def _get_memory_store(self, memory: PersonaMemory, memory_type: str) -> MemoryStore:
        """Get the appropriate memory store from PersonaMemory

        Args:
            memory: PersonaMemory instance
            memory_type: Type of memory store to get

        Returns:
            MemoryStore instance

        Raises:
            ValueError: If memory_type is invalid
        """
        store_map = {
            "user": memory.user_memory,
            "relationship": memory.relationship_memory,
            "action": memory.action_memory,
            "emotional": memory.emotional_memory,
            "conversation": memory.conversation_memory
        }

        if memory_type not in store_map:
            raise ValueError(
                f"Invalid memory_type: {memory_type}. "
                f"Valid types: {list(store_map.keys())}"
            )

        return store_map[memory_type]

    def run_full_validation(self) -> Dict[str, Any]:
        """Run complete validation suite on all registered personas

        Returns:
            Dictionary with validation results

        Raises:
            IsolationViolation: If any validation fails
        """
        results = {
            "total_personas": len(self.personas),
            "validations_run": 0,
            "validations_passed": 0,
            "persona_pairs_tested": 0
        }

        persona_ids = list(self.personas.keys())

        # Validate namespace uniqueness
        self.validate_namespace_uniqueness()
        results["validations_run"] += 1
        results["validations_passed"] += 1

        # Validate key namespacing for each persona
        for persona_id in persona_ids:
            for memory_type in ["user", "relationship", "action", "emotional", "conversation"]:
                self.validate_key_namespacing(persona_id, memory_type)
                results["validations_run"] += 1
                results["validations_passed"] += 1

        # Validate bidirectional isolation for each pair
        for i, persona_a in enumerate(persona_ids):
            for persona_b in persona_ids[i+1:]:
                self.validate_bidirectional_isolation(persona_a, persona_b)
                self.validate_clear_isolation(persona_a, persona_b)
                results["persona_pairs_tested"] += 1
                results["validations_run"] += 2
                results["validations_passed"] += 2

        results["status"] = "passed"
        return results


def validate_persona_isolation(
    persona_a: PersonaMemory,
    persona_b: PersonaMemory
) -> bool:
    """Quick validation function for two persona memories

    Args:
        persona_a: First PersonaMemory instance
        persona_b: Second PersonaMemory instance

    Returns:
        True if memories are isolated

    Raises:
        IsolationViolation: If isolation is violated
    """
    validator = MemoryIsolationValidator()
    validator.register_persona(persona_a.persona_id, persona_a)
    validator.register_persona(persona_b.persona_id, persona_b)

    return validator.validate_bidirectional_isolation(
        persona_a.persona_id,
        persona_b.persona_id
    )
