"""PersonaMemory wrapper for namespaced memory operations

Provides memory isolation between different personas by namespacing all memory
operations with the persona_id. Each persona gets completely isolated memory stores.
"""

from typing import Any, Dict, Optional


class MemoryStore:
    """Base class for a namespaced memory store

    Each memory type (user, relationship, action, emotional, conversation)
    gets its own isolated store per persona.
    """

    def __init__(self, persona_id: str, memory_type: str):
        """Initialize a memory store for a specific persona and type

        Args:
            persona_id: Unique identifier for the persona
            memory_type: Type of memory (user, relationship, action, etc.)
        """
        self.persona_id = persona_id
        self.memory_type = memory_type
        self._namespace = f"{persona_id}:{memory_type}"
        # In-memory storage (will be replaced with proper backend later)
        self._store: Dict[str, Any] = {}

    def _get_key(self, key: str) -> str:
        """Generate a namespaced key for storage

        Args:
            key: Original key

        Returns:
            Namespaced key with persona_id prefix
        """
        return f"{self._namespace}:{key}"

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from memory

        Args:
            key: Memory key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        namespaced_key = self._get_key(key)
        return self._store.get(namespaced_key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in memory

        Args:
            key: Memory key
            value: Value to store
        """
        namespaced_key = self._get_key(key)
        self._store[namespaced_key] = value

    def delete(self, key: str) -> bool:
        """Delete a value from memory

        Args:
            key: Memory key

        Returns:
            True if deleted, False if not found
        """
        namespaced_key = self._get_key(key)
        if namespaced_key in self._store:
            del self._store[namespaced_key]
            return True
        return False

    def exists(self, key: str) -> bool:
        """Check if a key exists in memory

        Args:
            key: Memory key

        Returns:
            True if key exists, False otherwise
        """
        namespaced_key = self._get_key(key)
        return namespaced_key in self._store

    def clear(self) -> None:
        """Clear all memory for this store (persona + type specific)"""
        # Only clear keys for this specific namespace
        keys_to_delete = [
            k for k in self._store.keys()
            if k.startswith(f"{self._namespace}:")
        ]
        for key in keys_to_delete:
            del self._store[key]

    def keys(self) -> list[str]:
        """Get all keys for this memory store

        Returns:
            List of keys (without namespace prefix)
        """
        prefix = f"{self._namespace}:"
        prefix_len = len(prefix)
        return [
            k[prefix_len:] for k in self._store.keys()
            if k.startswith(prefix)
        ]


class PersonaMemory:
    """Wrapper that namespaces all memory operations for a specific persona

    PersonaMemory ensures complete memory isolation between personas by:
    - Prefixing all memory keys with the persona_id
    - Providing separate stores for different memory types
    - Preventing cross-persona memory access

    Usage:
        memory = PersonaMemory(persona_id="freeman")
        memory.user_memory.set("user123", {"name": "John", "interactions": 5})
        user_data = memory.user_memory.get("user123")
    """

    def __init__(self, persona_id: str):
        """Initialize PersonaMemory for a specific persona

        Args:
            persona_id: Unique identifier for the persona

        Raises:
            ValueError: If persona_id is empty or invalid
        """
        if not persona_id or not isinstance(persona_id, str):
            raise ValueError("persona_id must be a non-empty string")

        self.persona_id = persona_id

        # Initialize separate memory stores for different memory types
        self._user_memory = MemoryStore(persona_id, "user")
        self._relationship_memory = MemoryStore(persona_id, "relationship")
        self._action_memory = MemoryStore(persona_id, "action")
        self._emotional_memory = MemoryStore(persona_id, "emotional")
        self._conversation_memory = MemoryStore(persona_id, "conversation")

    @property
    def user_memory(self) -> MemoryStore:
        """Access to user memory store

        Stores information about individual users including:
        - User profiles
        - Interaction counts
        - Sentiment tracking

        Returns:
            MemoryStore for user memory
        """
        return self._user_memory

    @property
    def relationship_memory(self) -> MemoryStore:
        """Access to relationship memory store

        Stores relationship data including:
        - Relationship levels (stranger, acquaintance, friend, ally)
        - Trust scores
        - Interaction history

        Returns:
            MemoryStore for relationship memory
        """
        return self._relationship_memory

    @property
    def action_memory(self) -> MemoryStore:
        """Access to action memory store

        Stores user actions including:
        - Likes, comments, reposts
        - Token purchases
        - Other interactions

        Returns:
            MemoryStore for action memory
        """
        return self._action_memory

    @property
    def emotional_memory(self) -> MemoryStore:
        """Access to emotional memory store

        Stores emotional context including:
        - Emotional triggers
        - Resonant topics
        - Emotional responses

        Returns:
            MemoryStore for emotional memory
        """
        return self._emotional_memory

    @property
    def conversation_memory(self) -> MemoryStore:
        """Access to conversation memory store

        Stores conversation history including:
        - Important topics
        - Key positions
        - Conversation chunks with importance scores

        Returns:
            MemoryStore for conversation memory
        """
        return self._conversation_memory

    def clear_all(self) -> None:
        """Clear all memory stores for this persona

        Warning: This will delete all memory data for this persona!
        """
        self._user_memory.clear()
        self._relationship_memory.clear()
        self._action_memory.clear()
        self._emotional_memory.clear()
        self._conversation_memory.clear()

    def get_namespace(self) -> str:
        """Get the namespace prefix for this persona

        Returns:
            Namespace string used to prefix all keys
        """
        return self.persona_id

    def __repr__(self) -> str:
        """Developer-friendly representation"""
        return f"PersonaMemory(persona_id='{self.persona_id}')"

    def __str__(self) -> str:
        """String representation"""
        return f"PersonaMemory for '{self.persona_id}'"
