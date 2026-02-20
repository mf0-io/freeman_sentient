# Multi-Persona Support Guide

> Complete guide to running multiple AI personas with shared infrastructure

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [Memory Isolation](#memory-isolation)
7. [Agent Integration](#agent-integration)
8. [API Reference](#api-reference)
9. [Examples](#examples)
10. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Multi-Persona Support?

Multi-persona support allows you to run multiple distinct AI personas simultaneously, each with:
- **Unique personality** and behavioral traits
- **Isolated memory** - completely separate data stores
- **Independent configuration** - per-persona LLM settings, platform configs, agent configs
- **Shared infrastructure** - efficient resource usage across all personas

### Use Cases

- **Experimentation**: Test different personality configurations side-by-side
- **Persona-as-a-Service**: Manage multiple client personas from one deployment
- **Character Portfolio**: Run a family of related but distinct AI characters
- **A/B Testing**: Compare different persona approaches with real users

### Key Features

✅ **Complete Memory Isolation** - Personas never share data
✅ **Independent Personalities** - Each persona has unique traits and behavior
✅ **Efficient Resource Sharing** - Common infrastructure for all personas
✅ **Easy Management** - Simple API for adding, removing, and configuring personas
✅ **Concurrent Operations** - Multiple personas can operate simultaneously
✅ **Platform Support** - Each persona can be active on different platforms

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     PersonaManager                          │
│                   (Singleton Instance)                      │
│  • Load personas from YAML                                  │
│  • Manage persona lifecycle                                 │
│  • Route messages to correct persona                        │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Persona: Freeman │     │ Persona: Other  │
│  ┌─────────────┐ │     │  ┌─────────────┐│
│  │ Config      │ │     │  │ Config      ││
│  │ Memory      │ │     │  │ Memory      ││
│  │ Agents      │ │     │  │ Agents      ││
│  └─────────────┘ │     │  └─────────────┘│
└─────────────────┘     └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Isolated Memory │     │ Isolated Memory │
│  • User Memory  │     │  • User Memory  │
│  • Relationships│     │  • Relationships│
│  • Actions      │     │  • Actions      │
│  • Emotions     │     │  • Emotions     │
│  • Conversations│     │  • Conversations│
└─────────────────┘     └─────────────────┘
```

### Core Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **Persona** | Data model representing a single persona | `src/persona/models.py` |
| **PersonaManager** | Singleton managing all personas | `src/persona/manager.py` |
| **PersonaMemory** | Memory isolation wrapper | `src/memory/persona_memory.py` |
| **BaseAgent** | Agent base class with persona context | `src/agents/base.py` |
| **Orchestrator** | Multi-persona message routing | `src/agents/orchestrator.py` |

---

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd freeman_sentient

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### 2. Basic Configuration

Create or edit `config/personas.yaml`:

```yaml
personas:
  - id: my_persona
    name: "My First Persona"
    description: "A friendly AI assistant"
    config_file: "config/my_persona.yaml"
    memory_namespace: "my_persona"
    is_active: true
    platforms:
      - telegram
```

Create `config/my_persona.yaml`:

```yaml
id: my_persona
name: "My First Persona"
version: "1.0.0"

personality:
  tone: friendly
  style: conversational
  voice_characteristics:
    - warm
    - helpful
    - encouraging

memory:
  namespace: my_persona
  retention_days: 90

platforms:
  telegram:
    enabled: true
    bot_token: ${TELEGRAM_BOT_TOKEN}
```

### 3. Load and Use

```python
from src.persona.manager import PersonaManager

# Load all personas (singleton pattern)
manager = PersonaManager()

# Get a specific persona
persona = manager.get_persona("my_persona")
print(f"Loaded: {persona.name}")

# List active personas
active = manager.list_active_personas()
print(f"Active personas: {len(active)}")
```

### 4. Run the Demo

```bash
python examples/multi_persona_demo.py
```

---

## Configuration

### Master Configuration: `personas.yaml`

The master configuration file lists all personas in your system:

```yaml
personas:
  - id: persona_id          # Unique identifier (lowercase, alphanumeric, -, _)
    name: "Display Name"    # Human-readable name
    description: "..."      # Brief description
    config_file: "config/persona_id.yaml"  # Path to detailed config
    memory_namespace: "persona_id"  # Memory isolation namespace
    is_active: true         # Whether persona should respond
    platforms:              # Platforms this persona uses
      - telegram
      - twitter

global:
  memory:
    backend: "vector_db"
    isolation_enabled: true
    cross_persona_lookup: false

  orchestrator:
    timeout_seconds: 30
    retry_attempts: 3
    parallel_agents: true
```

### Persona Configuration File

Each persona has a detailed YAML configuration file:

```yaml
# Basic Information
id: freeman
name: "Mr. Freeman"
version: "1.0.0"
mission: |
  Awaken people to consciousness hygiene in the AI era

# Personality Configuration
personality:
  tone: sarcastic
  style: philosophical
  voice_characteristics:
    - direct
    - provocative
    - insightful
  speaking_style:
    - short_sentences
    - rhetorical_questions
    - metaphors

# Memory Settings
memory:
  namespace: freeman
  retention_days: 365
  priority_contexts:
    - user_actions
    - emotional_responses
    - philosophical_discussions

# Agent Configuration
agents:
  inner_voice:
    enabled: true
    depth: deep_analysis
  decision:
    enabled: true
    threshold: 0.7
  response_generator:
    enabled: true
    max_length: 500
  content_creator:
    enabled: true
    media_types:
      - image
      - text

# LLM Configuration
llm:
  provider: anthropic
  model: claude-3-5-sonnet-20241022
  temperature: 0.8
  max_tokens: 2000
  api_key: ${ANTHROPIC_API_KEY}

# Platform Configuration
platforms:
  telegram:
    enabled: true
    bot_token: ${TELEGRAM_BOT_TOKEN}
    rate_limit: 30
  twitter:
    enabled: true
    api_key: ${TWITTER_API_KEY}
    api_secret: ${TWITTER_API_SECRET}

# Behavioral Rules
behavior:
  engagement:
    response_rate: 0.8
    ignore_keywords:
      - spam
      - scam
  content_creation:
    frequency: daily
    time_of_day: evening
  memory_triggers:
    remember_positive_actions: true
    remember_conflicts: true
```

### Environment Variables

Required environment variables (`.env` file):

```env
# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC...

# Twitter
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...

# Database
DATABASE_URL=postgresql://...
```

---

## Usage Guide

### Loading Personas

```python
from src.persona.manager import PersonaManager

# PersonaManager is a singleton - only one instance exists
manager = PersonaManager()

# Load from default location (config/personas.yaml)
# This happens automatically on first access

# Explicitly reload configuration
manager.reload()

# Get count
print(f"Total personas: {len(manager)}")
```

### Accessing Personas

```python
# Get a specific persona by ID
persona = manager.get_persona("freeman")
if persona:
    print(f"Found: {persona.name}")
else:
    print("Persona not found")

# List all personas
all_personas = manager.list_all_personas()
for p in all_personas:
    print(f"- {p.name} ({'active' if p.is_active else 'inactive'})")

# List only active personas
active = manager.list_active_personas()
print(f"Active: {len(active)}")
```

### Creating Personas Programmatically

```python
from src.persona.models import Persona

# Create a new persona
new_persona = Persona(
    id="my_bot",
    name="My Bot",
    personality_config={
        "tone": "friendly",
        "style": "casual"
    },
    memory_namespace="my_bot",
    is_active=True,
    platform_configs={
        "telegram": {"enabled": True}
    }
)

# Add to manager
manager.add_persona(new_persona)

# Verify it was added
assert manager.get_persona("my_bot") is not None
```

### Modifying Personas

```python
# Get persona
persona = manager.get_persona("freeman")

# Modify properties
persona.is_active = False
persona.personality_config["tone"] = "friendly"

# Changes are immediately reflected in the manager
# (singleton pattern with shared references)
```

### Removing Personas

```python
# Remove a persona
success = manager.remove_persona("my_bot")
if success:
    print("Persona removed")
else:
    print("Persona not found")

# Verify removal
assert manager.get_persona("my_bot") is None
```

### Validating Configuration

```python
# Validate a persona configuration
is_valid = manager.validate_persona(persona)
if is_valid:
    print("Configuration is valid")
else:
    print("Configuration has errors")

# The manager performs validation automatically on:
# - Loading from YAML
# - Adding new personas
# - Modifying personas (with validate_assignment=True)
```

---

## Memory Isolation

### How Memory Isolation Works

Each persona has **completely isolated memory**. No persona can access another persona's data.

```python
from src.memory.persona_memory import PersonaMemory

# Create memory for two different personas
freeman_memory = PersonaMemory(persona_id="freeman")
other_memory = PersonaMemory(persona_id="other")

# Store data in Freeman's memory
freeman_memory.user_memory.set("user123", {
    "name": "Alice",
    "relationship": "ally"
})

# Try to access from other persona - returns None
data = other_memory.user_memory.get("user123")
assert data is None  # Different namespace!

# Only Freeman can access Freeman's data
data = freeman_memory.user_memory.get("user123")
assert data["name"] == "Alice"  # Success!
```

### Memory Types

Each persona has five isolated memory stores:

| Memory Type | Purpose | Example |
|-------------|---------|---------|
| **user_memory** | User profiles and preferences | Names, interests, history |
| **relationship_memory** | Relationship status and history | Friend, ally, neutral, enemy |
| **action_memory** | User actions and interactions | Likes, purchases, shares |
| **emotional_memory** | Emotional responses and tone | Happy, frustrated, curious |
| **conversation_memory** | Important topics and positions | Discussed subjects, stances |

### Memory Namespacing

Keys are automatically namespaced to prevent collisions:

```
Format: {persona_id}:{memory_type}:{key}

Examples:
- freeman:user_memory:user123
- freeman:relationship_memory:user123
- other:user_memory:user123  # Different namespace!
```

### Validation

```python
from src.memory.isolation import (
    validate_memory_isolation,
    validate_memory_isolation_quick
)

# Comprehensive validation (checks all memory types)
is_isolated = validate_memory_isolation(
    persona_id_a="freeman",
    persona_id_b="other"
)
assert is_isolated  # Memory is completely isolated

# Quick validation (spot check)
is_isolated = validate_memory_isolation_quick(
    persona_id_a="freeman",
    persona_id_b="other"
)
```

---

## Agent Integration

### Using BaseAgent

All agents should inherit from `BaseAgent` to get persona context:

```python
from src.agents.base import BaseAgent
from src.persona.models import Persona

class MyAgent(BaseAgent):
    """Custom agent with persona awareness"""

    def process(self, message: str) -> str:
        # Access persona config
        tone = self.personality_config.get("tone", "neutral")

        # Access persona memory
        user_id = "user123"
        user_data = self.user_memory.get(user_id)

        # Use persona-specific settings
        max_length = self.get_config("agents.my_agent.max_length", 500)

        # Generate response...
        return response

# Create agent with persona
persona = manager.get_persona("freeman")
agent = MyAgent(persona=persona)

# Process messages
response = agent.process("Hello!")
```

### Orchestrator

The Orchestrator handles multi-persona message routing:

```python
from src.agents.orchestrator import Orchestrator

# Create orchestrator (loads all personas)
orchestrator = Orchestrator()

# Route message to correct persona
result = orchestrator.route_to_persona(
    message="Hello Freeman!",
    persona_id="freeman"  # Explicit routing
)

# Or let orchestrator determine persona
result = orchestrator.route_to_persona(
    message="Hello!",
    platform="telegram",
    platform_user_id="@freeman_bot"  # Platform-based routing
)

# Process message through full agent pipeline
response = orchestrator.process_message(
    persona_id="freeman",
    message="What do you think about AI?"
)
```

### Agent Properties

BaseAgent provides convenient property accessors:

```python
agent = MyAgent(persona=persona)

# Memory access
agent.user_memory        # PersonaMemory.user_memory
agent.relationship_memory
agent.action_memory
agent.emotional_memory
agent.conversation_memory

# Config access
agent.personality_config  # Personality settings
agent.agent_configs      # Agent configurations
agent.llm_config         # LLM settings
agent.behavior_config    # Behavioral rules
agent.platform_configs   # Platform settings

# Nested config access
agent.get_config("agents.my_agent.max_length", default=500)
agent.get_config("llm.temperature", default=0.7)
```

---

## API Reference

### PersonaManager

**Singleton class for managing all personas**

```python
class PersonaManager:
    """Singleton manager for all personas in the system"""

    def __init__(self, config_path: str = "config/personas.yaml"):
        """Initialize manager and load personas"""

    def get_persona(self, persona_id: str) -> Optional[Persona]:
        """Get persona by ID"""

    def list_active_personas(self) -> List[Persona]:
        """Get all active personas"""

    def list_all_personas(self) -> List[Persona]:
        """Get all personas (active and inactive)"""

    def add_persona(self, persona: Persona) -> None:
        """Add a new persona"""

    def remove_persona(self, persona_id: str) -> bool:
        """Remove a persona by ID"""

    def validate_persona(self, persona: Persona) -> bool:
        """Validate persona configuration"""

    def reload(self) -> None:
        """Reload personas from configuration file"""

    def __len__(self) -> int:
        """Get total persona count"""
```

### Persona

**Data model for a single persona**

```python
class Persona(BaseModel):
    """Represents a single AI persona"""

    id: str                              # Unique identifier
    name: str                            # Display name
    personality_config: Dict[str, Any]   # Personality settings
    memory_namespace: str                # Memory isolation namespace
    platform_configs: Dict[str, Any]     # Platform configurations
    created_at: datetime                 # Creation timestamp
    is_active: bool                      # Active status
    version: Optional[str]               # Version identifier
    mission: Optional[str]               # Core mission/purpose
    agent_configs: Dict[str, Any]        # Agent configurations
    llm_config: Dict[str, Any]           # LLM settings
    behavior_config: Dict[str, Any]      # Behavioral rules
```

### PersonaMemory

**Memory wrapper providing isolation**

```python
class PersonaMemory:
    """Isolated memory for a single persona"""

    def __init__(self, persona_id: str):
        """Initialize isolated memory stores"""

    @property
    def user_memory(self) -> MemoryStore:
        """Access user memory store"""

    @property
    def relationship_memory(self) -> MemoryStore:
        """Access relationship memory store"""

    @property
    def action_memory(self) -> MemoryStore:
        """Access action memory store"""

    @property
    def emotional_memory(self) -> MemoryStore:
        """Access emotional memory store"""

    @property
    def conversation_memory(self) -> MemoryStore:
        """Access conversation memory store"""
```

### MemoryStore

**Namespaced key-value storage**

```python
class MemoryStore:
    """Namespaced storage for a specific memory type"""

    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""

    def set(self, key: str, value: Any) -> None:
        """Set value for key"""

    def delete(self, key: str) -> bool:
        """Delete key"""

    def exists(self, key: str) -> bool:
        """Check if key exists"""

    def keys(self) -> List[str]:
        """Get all keys in this store"""

    def clear(self) -> None:
        """Clear all data in this store"""
```

### BaseAgent

**Base class for all agents**

```python
class BaseAgent:
    """Base agent class with persona context"""

    def __init__(self, persona: Persona):
        """Initialize agent with persona context"""

    @property
    def user_memory(self) -> MemoryStore:
        """Access persona's user memory"""

    @property
    def personality_config(self) -> Dict[str, Any]:
        """Access personality configuration"""

    def get_config(self, path: str, default: Any = None) -> Any:
        """Get nested config value by dot-path"""
```

---

## Examples

### Example 1: Basic Multi-Persona Setup

```python
from src.persona.manager import PersonaManager
from src.persona.models import Persona

# Initialize manager
manager = PersonaManager()

# Create two personas
freeman = Persona(
    id="freeman",
    name="Mr. Freeman",
    personality_config={
        "tone": "sarcastic",
        "style": "philosophical"
    },
    memory_namespace="freeman",
    is_active=True
)

helper = Persona(
    id="helper",
    name="Helpful Assistant",
    personality_config={
        "tone": "friendly",
        "style": "supportive"
    },
    memory_namespace="helper",
    is_active=True
)

# Add to manager
manager.add_persona(freeman)
manager.add_persona(helper)

print(f"Total personas: {len(manager)}")
```

### Example 2: Isolated Memory Operations

```python
from src.memory.persona_memory import PersonaMemory

# Create memory for each persona
freeman_mem = PersonaMemory(persona_id="freeman")
helper_mem = PersonaMemory(persona_id="helper")

# Same user interacts with both personas
user_id = "alice123"

# Freeman's interaction
freeman_mem.user_memory.set(user_id, {
    "name": "Alice",
    "relationship": "skeptic"
})
freeman_mem.relationship_memory.set(user_id, "neutral")

# Helper's interaction (completely separate)
helper_mem.user_memory.set(user_id, {
    "name": "Alice",
    "relationship": "friend"
})
helper_mem.relationship_memory.set(user_id, "positive")

# Verify isolation
freeman_data = freeman_mem.user_memory.get(user_id)
helper_data = helper_mem.user_memory.get(user_id)

print(f"Freeman sees: {freeman_data['relationship']}")  # skeptic
print(f"Helper sees: {helper_data['relationship']}")    # friend
```

### Example 3: Agent with Persona Context

```python
from src.agents.base import BaseAgent

class GreetingAgent(BaseAgent):
    """Agent that greets users based on persona personality"""

    def greet(self, user_id: str) -> str:
        # Get personality tone
        tone = self.personality_config.get("tone", "neutral")

        # Check if we know this user
        user_data = self.user_memory.get(user_id)

        if user_data:
            name = user_data.get("name", "friend")
            if tone == "sarcastic":
                return f"Oh look, it's {name} again."
            elif tone == "friendly":
                return f"Hi {name}! Great to see you!"
        else:
            if tone == "sarcastic":
                return "A new victim... I mean, visitor."
            elif tone == "friendly":
                return "Hello! Nice to meet you!"

        return "Hello."

# Use with different personas
freeman = manager.get_persona("freeman")
helper = manager.get_persona("helper")

freeman_agent = GreetingAgent(persona=freeman)
helper_agent = GreetingAgent(persona=helper)

# Same user, different greetings
print(freeman_agent.greet("alice123"))  # "Oh look, it's Alice again."
print(helper_agent.greet("alice123"))   # "Hi Alice! Great to see you!"
```

### Example 4: Orchestrator Routing

```python
from src.agents.orchestrator import Orchestrator

# Initialize orchestrator
orch = Orchestrator()

# Explicit routing
response = orch.route_to_persona(
    message="What do you think?",
    persona_id="freeman"
)

# Platform-based routing
response = orch.route_to_persona(
    message="Help me please",
    platform="telegram",
    platform_user_id="@helper_bot"
)

# Full message processing
result = orch.process_message(
    persona_id="freeman",
    message="Tell me about consciousness",
    user_id="alice123"
)
```

### Example 5: Run Demo Script

See `examples/multi_persona_demo.py` for a complete working example:

```bash
python examples/multi_persona_demo.py
```

Output includes:
- Loading personas from YAML
- Accessing persona details and configuration
- Creating personas programmatically
- Memory isolation demonstration
- Persona management operations

---

## Troubleshooting

### Problem: Persona Not Loading

**Symptom**: `get_persona()` returns `None`

**Solutions**:
1. Check `config/personas.yaml` has correct persona ID
2. Verify `config_file` path is correct
3. Ensure YAML syntax is valid: `python -c "import yaml; yaml.safe_load(open('config/personas.yaml'))"`
4. Check persona's `is_active` is set to `true`
5. Try reloading: `manager.reload()`

### Problem: Memory Leaking Between Personas

**Symptom**: One persona can see another's data

**Solutions**:
1. Verify each persona has unique `memory_namespace`
2. Check you're using `PersonaMemory`, not direct storage
3. Run isolation validation:
   ```python
   from src.memory.isolation import validate_memory_isolation
   validate_memory_isolation("persona1", "persona2")
   ```
4. Check for global variables or shared state

### Problem: Configuration Not Loading

**Symptom**: `personality_config` is empty or missing keys

**Solutions**:
1. Verify YAML structure in persona config file
2. Check for environment variable substitution: `${VAR_NAME}`
3. Ensure environment variables are set in `.env`
4. Validate config structure:
   ```python
   from src.persona.config import load_persona_config
   config = load_persona_config("config/freeman.yaml")
   ```

### Problem: Agent Can't Access Persona Context

**Symptom**: `AttributeError` when accessing persona properties

**Solutions**:
1. Ensure agent inherits from `BaseAgent`
2. Pass persona to constructor: `agent = MyAgent(persona=persona)`
3. Check persona is not `None`
4. Verify persona has required config keys

### Problem: Concurrent Operations Failing

**Symptom**: Race conditions or data corruption with multiple personas

**Solutions**:
1. Ensure each persona has unique `memory_namespace`
2. Use proper locking for shared resources
3. Test with `tests/integration/test_multi_persona.py`
4. Check for singleton pattern violations

### Problem: Tests Failing

**Symptom**: `pytest` tests fail

**Solutions**:
```bash
# Run specific test file
pytest tests/test_persona_isolation.py -v

# Run with output
pytest tests/ -v -s

# Check imports
python -c "from src.persona.manager import PersonaManager; print('OK')"

# Verify YAML config
python -c "import yaml; yaml.safe_load(open('config/personas.yaml')); print('OK')"
```

### Getting Help

1. **Check Logs**: Look for error messages in console output
2. **Run Tests**: `pytest tests/ -v` to identify broken components
3. **Validate Config**: Use `manager.validate_persona(persona)`
4. **Review Examples**: Check `examples/multi_persona_demo.py`
5. **Check Documentation**: Review relevant sections above

---

## Best Practices

### Configuration

✅ **DO**:
- Use descriptive persona IDs (lowercase, alphanumeric)
- Keep persona configs in separate YAML files
- Use environment variables for sensitive data
- Version your persona configurations
- Document persona missions and personalities

❌ **DON'T**:
- Hard-code API keys in YAML files
- Use spaces or special characters in persona IDs
- Share memory namespaces between personas
- Leave personas without proper validation

### Memory Management

✅ **DO**:
- Always use `PersonaMemory` for data storage
- Use unique memory namespaces per persona
- Validate memory isolation in tests
- Clear memory when removing personas
- Document memory retention policies

❌ **DON'T**:
- Access memory stores directly
- Share memory objects between personas
- Store sensitive data without encryption
- Forget to clean up inactive personas

### Agent Development

✅ **DO**:
- Inherit from `BaseAgent` for persona context
- Use property accessors for memory and config
- Handle missing config keys gracefully
- Log agent decisions and actions
- Test agents with multiple personas

❌ **DON'T**:
- Create agents without persona context
- Hard-code personality traits
- Bypass memory isolation
- Ignore error handling

### Testing

✅ **DO**:
- Test memory isolation thoroughly
- Verify persona independence
- Test concurrent operations
- Mock external dependencies
- Use fixtures for test personas

❌ **DON'T**:
- Skip integration tests
- Test only happy paths
- Share test data between tests
- Ignore edge cases

---

## Related Documentation

- [AGENTS.md](../AGENTS.md) - Agent architecture and design
- [BACKLOG.md](../BACKLOG.md) - Feature backlog and roadmap
- [CLAUDE.md](../CLAUDE.md) - Project overview and setup
- [examples/multi_persona_demo.py](../examples/multi_persona_demo.py) - Working demo

---

## Support

For questions, issues, or contributions:

1. Check this documentation first
2. Review the [CLAUDE.md](../CLAUDE.md) file
3. Run the demo: `python examples/multi_persona_demo.py`
4. Check tests: `pytest tests/ -v`

---

**Last Updated**: 2026-02-02
**Version**: 1.0.0
