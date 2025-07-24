"""Memory System for Digital Freeman

Manages multiple memory systems:
- Persona/Mood memory: Multi-persona support with mood states and isolation
- Persistent Graphiti memory: User profiles, relationships, conversations, actions, and emotional traces
"""

# ==============================================================================
# Persona & Mood Memory System
# ==============================================================================
from src.memory.persona_memory import PersonaMemory, MemoryStore
from src.memory.isolation import (
    MemoryIsolationValidator,
    IsolationViolation,
    validate_persona_isolation
)
from src.memory.mood import MoodState
from src.memory.emotional_state import EmotionalStateManager

# ==============================================================================
# Persistent Graphiti Memory System
# ==============================================================================
from src.memory.graphiti_adapter import GraphitiAdapter
from src.memory.user_memory import UserMemory
from src.memory.relationship_memory import RelationshipMemory
from src.memory.conversation_memory import ConversationMemory
from src.memory.action_memory import ActionMemory
from src.memory.emotional_memory import EmotionalMemory
from src.memory.memory_manager import MemoryManager

# ==============================================================================
# Temporal People Graph
# ==============================================================================
from src.memory.temporal_people_graph import (
    TemporalPeopleGraph,
    PersonNode,
    InteractionEdge,
    GraphSnapshot,
)

__all__ = [
    # Persona & Mood Memory
    'PersonaMemory',
    'MemoryStore',
    'MemoryIsolationValidator',
    'IsolationViolation',
    'validate_persona_isolation',
    'MoodState',
    'EmotionalStateManager',
    # Persistent Graphiti Memory
    'GraphitiAdapter',
    'UserMemory',
    'RelationshipMemory',
    'ConversationMemory',
    'ActionMemory',
    'EmotionalMemory',
    'MemoryManager',
    # Temporal People Graph
    'TemporalPeopleGraph',
    'PersonNode',
    'InteractionEdge',
    'GraphSnapshot',
]
