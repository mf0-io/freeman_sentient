# Digital Freeman Memory Systems

> Comprehensive memory architecture for persistent, emotionally-intelligent AI agents

---

## 📚 Table of Contents

1. [Overview](#-overview)
2. [Memory Systems](#-memory-systems)
   - [Persistent Graphiti Memory](#1-persistent-graphiti-memory-system)
   - [Mood & Emotional State System](#2-mood-and-emotional-state-system)
3. [Integration Guide](#-integration-guide)

---

## 🎯 Overview

Digital Freeman implements **two complementary memory systems** that work together to create an AI agent with both long-term memory and emotional authenticity:

| System | Purpose | Technology |
|--------|---------|------------|
| **Persistent Graphiti Memory** | Long-term storage of users, relationships, conversations, actions | Graphiti + Neo4j |
| **Mood & Emotional State** | Dynamic emotional responses that influence behavior | In-memory state machine |

### Why Two Systems?

- **Persistent Memory** ensures Freeman never forgets users, conversations, or relationships across all interactions
- **Mood System** provides emotional authenticity, making responses feel more human and engaging

Together, they solve the two biggest AI problems:
1. **"The AI forgets me"** → Persistent Graphiti Memory
2. **"The AI feels soulless"** → Mood & Emotional State System

---

## 🧠 Memory Systems

---

## 1. Persistent Graphiti Memory System

> Long-term memory using Graphiti knowledge graph and Neo4j database

### Purpose

Solves the #1 pain point across AI assistants: **memory failure**. Users consistently complain about AI forgetting them and losing context.

### Key Features

- **Persistent Memory**: All data survives restarts and persists indefinitely
- **Relationship Tracking**: Build and evolve relationships from stranger to ally
- **Emotional Intelligence**: Remember how interactions made the agent feel
- **Conversation History**: Track topics, positions, and memorable quotes
- **Action Memory**: Remember and score user actions (likes, shares, purchases)
- **Multi-User Support**: Handle concurrent users with data isolation
- **Local Privacy**: All data stored locally with full user control

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MemoryManager                        │
│           (Unified Interface & Orchestration)           │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼──────────────────┐
        │                 │                  │
        ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ UserMemory   │  │Relationship  │  │Conversation  │
│              │  │   Memory     │  │   Memory     │
└──────────────┘  └──────────────┘  └──────────────┘
        │                 │                  │
        └─────────────────┼──────────────────┘
                          │
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ActionMemory  │  │ Emotional    │  │  Graphiti    │
│              │  │   Memory     │  │   Adapter    │
└──────────────┘  └──────────────┘  └──────────────┘
                                            │
                                            ▼
                                    ┌──────────────┐
                                    │   Neo4j      │
                                    │  Database    │
                                    └──────────────┘
```

### Components

1. **GraphitiAdapter**: Low-level integration with Graphiti knowledge graph and Neo4j
2. **UserMemory**: User profiles (names, platform IDs, first/last seen)
3. **RelationshipMemory**: Relationship levels and point tracking
4. **ConversationMemory**: Topics, positions, and memorable quotes
5. **ActionMemory**: User actions with weighted scoring
6. **EmotionalMemory**: Emotional traces from interactions
7. **MemoryManager**: High-level unified interface orchestrating all components

### Quick Start

#### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your Neo4j configuration
```

#### Basic Usage

```python
import asyncio
from src.memory.memory_manager import MemoryManager

async def main():
    # Initialize the memory manager
    async with MemoryManager() as memory:
        # Remember a new user
        await memory.remember_user(
            user_id="alice123",
            name="Alice",
            platform="telegram",
            platform_user_id="@alice"
        )

        # Add a conversation
        await memory.add_conversation(
            user_id="alice123",
            topics=["artificial intelligence", "consciousness"],
            user_positions={"AI consciousness": "believes strong AI is possible"}
        )

        # Get complete user context
        context = await memory.get_user_context("alice123")
        print(f"Relationship: {context['relationship']['level']}")
        print(f"Topics: {[c['topic'] for c in context['recent_conversations']]}")

asyncio.run(main())
```

### Relationship Levels

| Level | Points | Description |
|-------|--------|-------------|
| Stranger | 0-9 | First interactions |
| Acquaintance | 10-49 | Casual conversations |
| Friend | 50-199 | Regular interactions |
| Ally | 200+ | Deep relationship |

### Action Scoring

| Action | Points |
|--------|--------|
| Like | +1 |
| Share | +3 |
| Comment | +5 |
| Purchase Token | +50 |

### API Reference

#### MemoryManager

```python
# User management
await memory.remember_user(user_id, name, platform, platform_user_id)
user_context = await memory.recall_user(user_id)

# Relationship management
await memory.update_relationship(user_id, points_delta, reason)
await memory.update_relationship(user_id, 5, "shared content")

# Conversations
await memory.add_conversation(user_id, topics, user_positions, quotes)
await memory.add_quote_to_conversation(conversation_id, quote)

# Actions
await memory.add_action(user_id, action_type, metadata)

# Emotional memory
await memory.add_emotion(user_id, emotion_type, intensity, context)

# Context retrieval
context = await memory.get_user_context(user_id)
# Returns: {
#   "user": {...},
#   "relationship": {...},
#   "recent_conversations": [...],
#   "recent_actions": [...],
#   "emotional_profile": {...}
# }
```

---

## 2. Mood and Emotional State System

> Dynamic mood states that influence Freeman's responses and behavior

### Purpose

Addresses the "soulless AI" problem by making Freeman feel more alive and emotionally authentic through dynamic mood states.

### Key Features

- **Multi-dimensional mood tracking** - Energy, valence, irritability, and enthusiasm
- **Smooth transitions** - Natural mood changes without sudden swings
- **Time-based decay** - Mood naturally returns to baseline over time
- **Event-driven updates** - User interactions influence mood state
- **Response modifiers** - Mood influences agent behavior and response generation

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERACTION                          │
│         (positive, negative, engaging, boring)               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              EmotionalStateManager                           │
│  ┌───────────────────────────────────────────────┐          │
│  │  • Process interaction events                 │          │
│  │  • Track mood history                         │          │
│  │  • Generate response modifiers                │          │
│  │  • Apply time-based decay                     │          │
│  └───────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### Mood Dimensions

| Dimension | Range | Description |
|-----------|-------|-------------|
| `energy_level` | 0.0 - 1.0 | Affects verbosity and engagement level |
| `emotional_valence` | -1.0 - 1.0 | Negative to positive emotional tone |
| `irritability` | 0.0 - 1.0 | Affects patience and tolerance |
| `enthusiasm` | 0.0 - 1.0 | Affects excitement and detail in responses |

### Interaction Effects

| Type | Energy | Valence | Irritability | Enthusiasm |
|------|--------|---------|--------------|------------|
| `positive_interaction` | - | ↑ +0.10 | ↓ -0.05 | ↑ +0.08 |
| `negative_interaction` | - | ↓ -0.12 | ↑ +0.10 | ↓ -0.05 |
| `engaging_topic` | ↑ +0.12 | ↑ +0.05 | - | ↑ +0.10 |
| `boring_interaction` | ↓ -0.10 | - | ↑ +0.03 | ↓ -0.08 |

### API Reference

```python
from src.memory.emotional_state import EmotionalStateManager

# Initialize manager
manager = EmotionalStateManager()

# Process interactions
manager.process_interaction("positive_interaction")
manager.process_interaction("engaging_topic", sentiment=0.8)

# Get current mood
current_mood = manager.get_current_mood()

# Get response modifiers for agents
modifiers = manager.get_response_modifiers()
# Returns: {
#   "verbosity": 0.0-1.0,
#   "tone": -1.0-1.0,
#   "patience": 0.0-1.0,
#   "engagement": 0.0-1.0,
#   "suggested_style": "philosophical"|"sarcastic"|"supportive"|"confrontational"
# }
```

---

## 🔄 Integration Guide

### Using Both Systems Together

```python
import asyncio
from src.memory.memory_manager import MemoryManager
from src.memory.emotional_state import EmotionalStateManager

async def freeman_response(user_id, user_message):
    # Initialize both systems
    async with MemoryManager() as memory:
        mood_manager = EmotionalStateManager()

        # Get persistent memory context
        context = await memory.get_user_context(user_id)

        # Get current mood modifiers
        mood_modifiers = mood_manager.get_response_modifiers()

        # Process the interaction
        mood_manager.process_interaction("user_message")

        # Combine memory and mood for response
        response = generate_response(
            user_message=user_message,
            user_context=context,
            mood_state=mood_modifiers
        )

        # Store the conversation in persistent memory
        await memory.add_conversation(
            user_id=user_id,
            topics=extract_topics(user_message, response),
            user_positions={},
            quotes=[]
        )

        # Store emotional trace
        await memory.add_emotion(
            user_id=user_id,
            emotion_type="curious",
            intensity=mood_modifiers["engagement"],
            context=f"Discussing: {user_message[:50]}"
        )

        return response
```

### Best Practices

1. **Use Persistent Memory** for:
   - User profiles and preferences
   - Relationship tracking
   - Conversation history
   - Long-term emotional patterns

2. **Use Mood System** for:
   - Real-time response modulation
   - Emotional authenticity
   - Conversation flow
   - Dynamic personality expression

3. **Integration Pattern**:
   - Load persistent context at start of interaction
   - Apply mood modifiers to response generation
   - Store both conversation data and emotional traces
   - Update relationship scores based on interaction sentiment

---

## 📖 Additional Documentation

- **Graphiti Memory Examples**: See `examples/memory_demo.py`
- **Testing**: Run `pytest tests/memory/ -v`
- **Configuration**: See `.env.example` for all environment variables

---

## 🏃‍♂️ Running Tests

```bash
# Unit tests (Graphiti memory)
pytest tests/memory/test_graphiti_adapter.py -v
pytest tests/memory/test_user_memory.py -v
pytest tests/memory/test_memory_manager.py -v

# Integration tests (persistence)
pytest tests/memory/test_persistence.py -v

# All tests
pytest tests/memory/ -v
```

---

## 🔧 Configuration

Key environment variables for memory systems:

```bash
# Graphiti / Neo4j
GRAPHITI_DB_HOST=localhost
GRAPHITI_DB_PORT=7687
GRAPHITI_DB_USER=neo4j
GRAPHITI_DB_PASSWORD=your_neo4j_password

# Memory System Settings
RELATIONSHIP_FRIEND_THRESHOLD=50
ACTION_SHARE_POINTS=3
MEMORY_RETENTION_DAYS=365

# Feature Flags
MEMORY_PERSISTENCE_ENABLED=true
MULTI_PERSONA_ENABLED=true
```

See `.env.example` for complete configuration options.
