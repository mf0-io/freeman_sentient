# Memory System Documentation

Comprehensive guide to the Freeman Relationship Management Memory System.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Data Models](#data-models)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
  - [MemoryManager (Recommended)](#memorymanager-recommended)
  - [User Memory](#user-memory)
  - [Relationship Memory](#relationship-memory)
  - [Action Memory](#action-memory)
  - [Emotional Memory](#emotional-memory)
- [API Reference](#api-reference)
- [Relationship Levels](#relationship-levels)
- [Action Weights](#action-weights)
- [Sentiment Analysis](#sentiment-analysis)
- [Storage Layer](#storage-layer)
- [Testing](#testing)

---

## Overview

The Memory System is a comprehensive relationship management solution for the Freeman AI agent. It tracks individual relationships with users across platforms, maintaining interaction history, preferences, relationship depth, and emotional context to enable personalized and meaningful interactions.

### Key Features

- **Cross-Platform Identity Mapping**: Unify user identities across Telegram, Twitter, and other platforms
- **Relationship Tracking**: Track relationship depth from stranger to ally with weighted scoring
- **Action History**: Record all user interactions with automatic relationship score calculation
- **Emotional Memory**: Capture emotional tone and sentiment patterns over time
- **Unified API**: Single `MemoryManager` facade for all memory operations
- **Async/Await**: Full async support for scalable operations
- **Type Safety**: Pydantic v2 models for validation and serialization

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MemoryManager                           │
│  (Unified facade for agent consumption)                     │
└────────────┬────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬──────────────┬──────────────┐
    │                 │              │              │
┌───▼────┐    ┌──────▼──────┐  ┌───▼─────┐  ┌────▼──────┐
│  User  │    │Relationship │  │ Action  │  │ Emotional │
│ Memory │    │   Memory    │  │ Memory  │  │  Memory   │
└───┬────┘    └──────┬──────┘  └───┬─────┘  └────┬──────┘
    │                │              │              │
    └────────────────┴──────────────┴──────────────┘
                           │
                    ┌──────▼──────┐
                    │   Storage   │
                    │   (Abstract)│
                    └──────┬──────┘
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
    ┌────▼─────┐                      ┌─────▼─────┐
    │ InMemory │                      │ Postgres  │
    │ Storage  │                      │  Storage  │
    └──────────┘                      └───────────┘
```

### Components

| Component | Responsibility |
|-----------|---------------|
| **MemoryManager** | High-level unified API for agents |
| **UserMemory** | User profiles and cross-platform identity |
| **RelationshipMemory** | Relationship scoring and level tracking |
| **ActionMemory** | User action tracking and score aggregation |
| **EmotionalMemory** | Sentiment and emotional context tracking |
| **Storage** | Abstract storage layer for backend flexibility |

---

## Data Models

All models are built with Pydantic v2 for type safety, validation, and serialization.

### UserProfile

Represents a unified user profile across platforms.

```python
from src.memory.models import UserProfile

profile = UserProfile(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    platform_ids={
        "telegram": "123456789",
        "twitter": "@freedom_seeker"
    },
    preferred_name="Alex",
    preferences={
        "topics_of_interest": ["philosophy", "technology"],
        "communication_style": "direct"
    },
    metadata={
        "timezone": "UTC",
        "language": "en"
    }
)
```

**Fields:**
- `user_id` (str): Unified UUID identifier
- `platform_ids` (Dict[str, str]): Platform-specific IDs
- `preferred_name` (Optional[str]): Display name
- `preferences` (Dict[str, Any]): User preferences
- `metadata` (Dict[str, Any]): Additional metadata
- `created_at` (datetime): Creation timestamp
- `updated_at` (datetime): Last update timestamp

### Relationship

Tracks relationship depth and trust between Freeman and a user.

```python
from src.memory.models import Relationship, RelationshipLevel

relationship = Relationship(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    relationship_score=45.0,  # 0-100
    trust_score=0.7,          # 0.0-1.0
    sentiment_trend=SentimentTrend.IMPROVING,
    total_interactions=23,
    notes="Engaged user, shares Freeman's views"
)

# Access computed relationship level
level = relationship.relationship_level  # RelationshipLevel.FRIEND
```

**Fields:**
- `user_id` (str): User identifier
- `relationship_score` (float): 0-100 score
- `trust_score` (float): 0.0-1.0 trust level
- `sentiment_trend` (SentimentTrend): improving/stable/declining
- `first_interaction` (datetime): First contact timestamp
- `last_interaction` (datetime): Most recent contact
- `total_interactions` (int): Number of interactions
- `notes` (Optional[str]): Contextual notes

**Property:**
- `relationship_level` (RelationshipLevel): Computed from score

### Action

Represents a user action with weighted scoring.

```python
from src.memory.models import Action, ActionType

action = Action(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    action_type=ActionType.COMMENT,
    context="Thoughtful response about AI consciousness",
    platform="telegram"
)

# Access computed weight
weight = action.weight  # 2 for COMMENT
```

**Fields:**
- `action_id` (str): Unique UUID identifier
- `user_id` (str): User who performed action
- `action_type` (ActionType): Type of action
- `context` (Optional[str]): Contextual information
- `platform` (Optional[str]): Platform where action occurred
- `timestamp` (datetime): Action timestamp

**Property:**
- `weight` (int): Computed score weight

### EmotionalTrace

Captures emotional tone and sentiment of interactions.

```python
from src.memory.models import EmotionalTrace

trace = EmotionalTrace(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    emotion_tags=["curiosity", "engagement", "intellectual"],
    sentiment=0.8,  # -1.0 to 1.0
    context="Deep philosophical discussion about free will",
    interaction_summary="User challenged Freeman's views"
)
```

**Fields:**
- `trace_id` (str): Unique UUID identifier
- `user_id` (str): User identifier
- `emotion_tags` (List[str]): Emotional descriptors (auto-lowercased)
- `sentiment` (float): -1.0 (negative) to 1.0 (positive)
- `context` (str): Interaction context
- `interaction_summary` (Optional[str]): Brief summary
- `timestamp` (datetime): Trace timestamp

### UserContext

Aggregated context for agent consumption.

```python
from src.memory.models import UserContext

# Typically returned by MemoryManager.get_user_context()
context = {
    "profile": UserProfile(...),
    "relationship": Relationship(...),
    "recent_actions": [Action(...), ...],
    "emotional_state": {
        "summary": "User is engaged and curious",
        "traces": [EmotionalTrace(...), ...],
        "average_sentiment": 0.7,
        "common_emotions": ["curiosity", "intellectual"]
    },
    "exists": True
}
```

---

## Configuration

The memory system uses environment variables for configuration.

```python
from src.core.config import Config

config = Config()

# Access configuration
db_url = config.database_url
redis_url = config.redis_url
anthropic_key = config.anthropic_api_key
```

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Database (PostgreSQL required for production)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/freeman

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# Twitter
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_SECRET=...

# Sentient Framework (optional)
SENTIENT_API_KEY=...

# Application
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=development
```

---

## Quick Start

### Basic Setup

```python
import asyncio
from src.memory.manager import MemoryManager
from src.memory.storage import InMemoryStorage  # or PostgresStorage

async def main():
    # Initialize with storage backend
    storage = InMemoryStorage()  # Use PostgresStorage for production
    memory = MemoryManager(storage)

    # Record an interaction
    result = await memory.record_interaction(
        platform="telegram",
        platform_id="123456",
        action_type=ActionType.COMMENT,
        emotion_tags=["curiosity"],
        sentiment=0.7,
        context="User asked about consciousness"
    )

    # Get user context
    context = await memory.get_user_context(
        platform="telegram",
        platform_id="123456"
    )

    print(f"Relationship: {context['relationship'].relationship_level}")

asyncio.run(main())
```

---

## Usage Examples

### MemoryManager (Recommended)

The `MemoryManager` provides a unified high-level API that combines all memory operations.

#### Get Complete User Context

```python
from src.memory.manager import MemoryManager
from src.memory.storage import InMemoryStorage

memory = MemoryManager(InMemoryStorage())

# Get complete context for agent response generation
context = await memory.get_user_context(
    platform="telegram",
    platform_id="123456",
    include_actions=10,    # Number of recent actions
    include_emotions=5,    # Number of emotional traces
    emotion_days=7        # Only last 7 days of emotions
)

if context["exists"]:
    profile = context["profile"]
    relationship = context["relationship"]
    actions = context["recent_actions"]
    emotions = context["emotional_state"]

    print(f"User: {profile.preferred_name}")
    print(f"Level: {relationship.relationship_level}")
    print(f"Trust: {relationship.trust_score}")
    print(f"Recent interactions: {len(actions)}")
    print(f"Emotional state: {emotions['summary']}")
```

#### Record Complete Interaction

```python
from src.memory.manager import MemoryManager
from src.memory.models import ActionType

memory = MemoryManager(InMemoryStorage())

# Record interaction with automatic relationship update
result = await memory.record_interaction(
    platform="telegram",
    platform_id="123456",
    action_type=ActionType.COMMENT,
    emotion_tags=["curiosity", "engagement"],
    sentiment=0.7,
    context="User asked about free will",
    interaction_summary="Discussed determinism vs free will",
    auto_update_relationship=True  # Default: True
)

print(f"User: {result['user'].preferred_name}")
print(f"Action weight: {result['action'].weight}")
print(f"New score: {result['relationship'].relationship_score}")
```

#### Manual Relationship Update

```python
# Update relationship directly
relationship = await memory.update_relationship(
    user_id="user_123",
    score_delta=5.0,     # Add 5 points to score
    trust_delta=0.1,     # Add 0.1 to trust
    notes="Great philosophical discussion"
)

print(f"New level: {relationship.relationship_level}")
```

#### Find Users by Relationship Level

```python
# Get all friends
friends = await memory.get_users_by_relationship_level(
    level="friend",
    limit=50
)

for item in friends:
    user = item["user"]
    rel = item["relationship"]
    print(f"{user.preferred_name}: {rel.relationship_score}")
```

### User Memory

For direct user profile management.

```python
from src.memory.user_memory import UserMemory
from src.memory.storage import InMemoryStorage

user_memory = UserMemory(InMemoryStorage())

# Create a new user
profile = await user_memory.create_user(
    platform="telegram",
    platform_id="123456789",
    preferred_name="Alex",
    preferences={
        "topics_of_interest": ["philosophy", "AI"],
        "communication_style": "direct"
    }
)

# Get user by platform ID
profile = await user_memory.get_by_platform_id("telegram", "123456789")

# Update user profile
profile = await user_memory.update_user(
    user_id=profile.user_id,
    preferred_name="Alexander",
    metadata={"timezone": "America/New_York"}
)

# Update preferences (merges with existing)
await user_memory.update_preferences(
    user_id=profile.user_id,
    preferences={"language": "en"}  # Merged with existing preferences
)

# Link additional platform
await user_memory.link_platform(
    user_id=profile.user_id,
    platform="twitter",
    platform_id="@freedom_seeker"
)

# Get or create (useful for first contact)
profile = await user_memory.get_or_create_user(
    platform="telegram",
    platform_id="123456789",
    preferred_name="Alex"
)

# Delete user
await user_memory.delete_user(profile.user_id)
```

### Relationship Memory

For relationship tracking and scoring.

```python
from src.memory.relationship_memory import RelationshipMemory
from src.memory.storage import InMemoryStorage

rel_memory = RelationshipMemory(InMemoryStorage())

# Create relationship
relationship = await rel_memory.create_relationship(
    user_id="user_123",
    initial_score=0.0,
    trust_score=0.0,
    notes="First contact"
)

# Get or create (useful for first contact)
relationship = await rel_memory.get_or_create_relationship("user_123")

# Update relationship score
relationship = await rel_memory.update_score(
    user_id="user_123",
    score_delta=5.0,
    notes="Engaged in philosophical discussion"
)

# Update trust score
relationship = await rel_memory.update_trust(
    user_id="user_123",
    trust_delta=0.1
)

# Record interaction (increments counters)
relationship = await rel_memory.record_interaction(
    user_id="user_123"
)

# Get all relationships at a specific level
friends = await rel_memory.get_relationships_by_level(
    level=RelationshipLevel.FRIEND,
    limit=50
)

# Calculate level from score
level = RelationshipMemory.calculate_level(45)  # Returns "friend"
```

### Action Memory

For tracking user actions and scores.

```python
from src.memory.action_memory import ActionMemory
from src.memory.models import ActionType
from src.memory.storage import InMemoryStorage

action_memory = ActionMemory(InMemoryStorage())

# Record an action
action = await action_memory.record_action(
    user_id="user_123",
    action_type=ActionType.COMMENT,
    context="Thoughtful response about AI consciousness",
    platform="telegram"
)
print(f"Action weight: {action.weight}")  # 2

# Get all actions for a user
actions = await action_memory.get_actions(user_id="user_123")

# Get recent actions (last N days)
recent = await action_memory.get_recent_actions(
    user_id="user_123",
    days=7,
    limit=20
)

# Get aggregated score
score = await action_memory.get_action_score(user_id="user_123")
print(f"Total score: {score}")

# Get action breakdown
breakdown = await action_memory.get_action_breakdown(user_id="user_123")
print(f"Likes: {breakdown[ActionType.LIKE]}")
print(f"Comments: {breakdown[ActionType.COMMENT]}")
```

### Emotional Memory

For tracking emotional patterns and sentiment.

```python
from src.memory.emotional_memory import EmotionalMemory
from src.memory.storage import InMemoryStorage

emotional_memory = EmotionalMemory(InMemoryStorage())

# Record emotional trace
trace = await emotional_memory.record_trace(
    user_id="user_123",
    emotion_tags=["curiosity", "engagement", "intellectual"],
    sentiment=0.8,
    context="Deep philosophical discussion about free will",
    interaction_summary="User challenged Freeman's views"
)

# Get all traces for a user
traces = await emotional_memory.get_traces(user_id="user_123")

# Get recent traces (last N days)
recent = await emotional_memory.get_recent_traces(
    user_id="user_123",
    days=7
)

# Get emotional summary
summary = await emotional_memory.get_emotional_summary(user_id="user_123")
print(f"Average sentiment: {summary['average_sentiment']}")
print(f"Common emotions: {summary['common_emotions']}")

# Get sentiment trend
trend = await emotional_memory.get_sentiment_trend(user_id="user_123")
print(f"Trend: {trend}")  # "improving", "stable", or "declining"

# Get emotional context for agent
context = await emotional_memory.get_emotional_context(
    user_id="user_123",
    limit=5,
    days=7
)
print(context["summary"])
print(context["traces"])
print(context["average_sentiment"])
print(context["common_emotions"])
```

---

## API Reference

### MemoryManager

```python
class MemoryManager:
    def __init__(self, storage: Optional[MemoryStorage] = None)

    async def get_user_context(
        self,
        platform: str,
        platform_id: str,
        include_actions: int = 10,
        include_emotions: int = 5,
        emotion_days: int = 7
    ) -> Dict[str, Any]

    async def record_interaction(
        self,
        platform: str,
        platform_id: str,
        action_type: ActionType,
        emotion_tags: List[str],
        sentiment: float,
        context: str,
        interaction_summary: Optional[str] = None,
        auto_update_relationship: bool = True,
        score_delta: Optional[float] = None
    ) -> Dict[str, Any]

    async def update_relationship(
        self,
        user_id: str,
        score_delta: Optional[float] = None,
        trust_delta: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Optional[Relationship]

    async def get_user_by_platform(
        self,
        platform: str,
        platform_id: str
    ) -> Optional[UserProfile]

    async def get_relationship(
        self,
        user_id: str
    ) -> Optional[Relationship]

    async def get_users_by_relationship_level(
        self,
        level: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]

    async def close(self) -> None
    async def health_check(self) -> bool
```

### UserMemory

```python
class UserMemory:
    def __init__(self, storage: Optional[MemoryStorage] = None)

    async def create_user(
        self,
        platform: str,
        platform_id: str,
        preferred_name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserProfile

    async def get_user(
        self,
        user_id: str
    ) -> Optional[UserProfile]

    async def get_by_platform_id(
        self,
        platform: str,
        platform_id: str
    ) -> Optional[UserProfile]

    async def update_user(
        self,
        user_id: str,
        preferred_name: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[UserProfile]

    async def link_platform(
        self,
        user_id: str,
        platform: str,
        platform_id: str
    ) -> Optional[UserProfile]

    async def unlink_platform(
        self,
        user_id: str,
        platform: str
    ) -> Optional[UserProfile]

    async def update_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ) -> Optional[UserProfile]

    async def get_or_create_user(
        self,
        platform: str,
        platform_id: str,
        preferred_name: Optional[str] = None
    ) -> UserProfile

    async def delete_user(
        self,
        user_id: str
    ) -> bool
```

### RelationshipMemory

```python
class RelationshipMemory:
    def __init__(self, storage: Optional[MemoryStorage] = None)

    async def get_relationship(
        self,
        user_id: str
    ) -> Optional[Relationship]

    async def create_relationship(
        self,
        user_id: str,
        initial_score: float = 0.0,
        trust_score: float = 0.0,
        notes: Optional[str] = None
    ) -> Relationship

    async def update_score(
        self,
        user_id: str,
        score_delta: float,
        notes: Optional[str] = None
    ) -> Optional[Relationship]

    async def update_trust(
        self,
        user_id: str,
        trust_delta: float
    ) -> Optional[Relationship]

    async def update_relationship(
        self,
        user_id: str,
        score_delta: Optional[float] = None,
        trust_delta: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Optional[Relationship]

    async def record_interaction(
        self,
        user_id: str
    ) -> Optional[Relationship]

    async def get_relationships_by_level(
        self,
        level: RelationshipLevel,
        limit: int = 100
    ) -> List[Relationship]

    async def get_or_create_relationship(
        self,
        user_id: str
    ) -> Relationship

    @staticmethod
    def calculate_level(score: float) -> RelationshipLevel
```

### ActionMemory

```python
class ActionMemory:
    def __init__(self, storage: Optional[MemoryStorage] = None)

    async def record_action(
        self,
        user_id: str,
        action_type: ActionType,
        context: Optional[str] = None,
        platform: Optional[str] = None
    ) -> Action

    async def get_actions(
        self,
        user_id: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Action]

    async def get_recent_actions(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[Action]

    async def get_action_score(
        self,
        user_id: str,
        since: Optional[datetime] = None
    ) -> float

    async def get_action_breakdown(
        self,
        user_id: str,
        since: Optional[datetime] = None
    ) -> Dict[ActionType, int]
```

### EmotionalMemory

```python
class EmotionalMemory:
    def __init__(self, storage: Optional[MemoryStorage] = None)

    async def record_trace(
        self,
        user_id: str,
        emotion_tags: List[str],
        sentiment: float,
        context: str,
        interaction_summary: Optional[str] = None
    ) -> EmotionalTrace

    async def get_traces(
        self,
        user_id: str,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[EmotionalTrace]

    async def get_recent_traces(
        self,
        user_id: str,
        days: int = 30,
        limit: int = 100
    ) -> List[EmotionalTrace]

    async def get_emotional_summary(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]

    async def get_emotional_context(
        self,
        user_id: str,
        limit: int = 10,
        days: int = 7
    ) -> Dict[str, Any]

    async def calculate_average_sentiment(
        self,
        user_id: str,
        since: Optional[datetime] = None
    ) -> float

    async def get_common_emotions(
        self,
        user_id: str,
        since: Optional[datetime] = None
    ) -> List[Tuple[str, int]]

    async def get_sentiment_trend(
        self,
        user_id: str
    ) -> str
```

---

## Relationship Levels

Relationship levels are automatically calculated from `relationship_score`:

| Level | Score Range | Description |
|-------|-------------|-------------|
| **stranger** | 0 | No prior interaction |
| **acquaintance** | 1-25 | Initial interactions (just met) |
| **friend** | 26-75 | Established relationship |
| **ally** | 76-100 | Deep connection, high trust |

### Example Progression

```python
# New user (stranger)
score = 0  → RelationshipLevel.STRANGER

# First like (acquaintance)
score = 1  → RelationshipLevel.ACQUAINTANCE

# Several positive interactions (friend)
score = 30 → RelationshipLevel.FRIEND

# Long-term engaged user (ally)
score = 80 → RelationshipLevel.ALLY
```

### Score Calculation

When using `record_interaction()` with `auto_update_relationship=True`:

```python
# Formula: action_weight * (1.0 + sentiment * 0.5)

# Positive comment (weight=2, sentiment=0.7)
score_delta = 2 * (1.0 + 0.7 * 0.5) = 2 * 1.35 = 2.7

# Neutral like (weight=1, sentiment=0.0)
score_delta = 1 * (1.0 + 0.0 * 0.5) = 1 * 1.0 = 1.0

# Negative action (weight=-5, sentiment=-0.5)
score_delta = -5 * (1.0 + (-0.5) * 0.5) = -5 * 0.75 = -3.75
```

---

## Action Weights

Different actions have different weights for relationship scoring:

| Action Type | Weight | Description |
|-------------|--------|-------------|
| `LIKE` | 1 | Passive engagement |
| `COMMENT` | 2 | Active engagement |
| `MESSAGE` | 2 | Direct communication |
| `REPOST` | 3 | Content amplification |
| `TOKEN_PURCHASE` | 10 | Financial support |
| `NEGATIVE` | -5 | Unwanted behavior |

### Example Usage

```python
from src.memory.models import ActionType

# Record a like (low impact)
await memory.record_interaction(
    platform="telegram",
    platform_id="123456",
    action_type=ActionType.LIKE,
    emotion_tags=["interest"],
    sentiment=0.3,
    context="User liked a post"
)

# Record a token purchase (high impact)
await memory.record_interaction(
    platform="telegram",
    platform_id="123456",
    action_type=ActionType.TOKEN_PURCHASE,
    emotion_tags=["support", "enthusiasm"],
    sentiment=0.9,
    context="User purchased tokens"
)
```

---

## Sentiment Analysis

Sentiment is tracked on a continuous scale from -1.0 to +1.0:

### Sentiment Scale

| Range | Interpretation | Example Tags |
|-------|----------------|--------------|
| -1.0 to -0.5 | Very Negative | anger, frustration, hostility |
| -0.5 to -0.2 | Negative | disappointment, confusion |
| -0.2 to 0.2 | Neutral | indifference, calm |
| 0.2 to 0.5 | Positive | interest, agreement |
| 0.5 to 1.0 | Very Positive | joy, gratitude, enthusiasm |

### Sentiment Trends

Relationships track sentiment trends over time:

| Trend | Description |
|-------|-------------|
| `IMPROVING` | Score is increasing (positive interactions) |
| `STABLE` | Score is consistent |
| `DECLINING` | Score is decreasing (negative interactions) |

### Common Emotion Tags

Suggested emotion tags for consistency:

**Positive:**
- `joy`, `gratitude`, `enthusiasm`, `excitement`
- `curiosity`, `interest`, `engagement`
- `agreement`, `appreciation`, `trust`

**Negative:**
- `anger`, `frustration`, `hostility`
- `disappointment`, `confusion`, `skepticism`

**Neutral:**
- `curiosity` (can be positive), `calm`, `thoughtful`
- `intellectual`, `philosophical`, `analytical`

---

## Storage Layer

The memory system uses an abstract storage layer for flexibility.

### Implementing a Custom Storage Backend

```python
from src.memory.storage import MemoryStorage
from src.memory.models import UserProfile, Relationship, Action, EmotionalTrace

class CustomStorage(MemoryStorage):
    async def save_user(self, user: UserProfile) -> UserProfile:
        # Implement user storage
        pass

    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        # Implement user retrieval
        pass

    # Implement all other abstract methods...
```

### Available Storage Backends

| Backend | Status | Description |
|---------|--------|-------------|
| `InMemoryStorage` | ✅ Implemented | In-memory storage for testing |
| `PostgresStorage` | 🚧 Planned | PostgreSQL for production |

---

## Testing

### Running Tests

```bash
# Run all memory tests
pytest tests/memory/ -v

# Run specific test file
pytest tests/memory/test_manager.py -v

# Run with coverage
pytest tests/memory/ --cov=src/memory --cov-report=html
```

### Test Coverage

The memory system has comprehensive test coverage:

| Component | Tests | Coverage |
|-----------|-------|----------|
| User Memory | 13 | ✅ Full |
| Relationship Memory | 20 | ✅ Full |
| Action Memory | 15 | ✅ Full |
| Emotional Memory | 11 | ✅ Full |
| Memory Manager | 16 | ✅ Full |
| Integration | 10 | ✅ Full |

**Total: 85 tests**

### Example Test

```python
import pytest
from src.memory.manager import MemoryManager
from src.memory.models import ActionType

@pytest.mark.asyncio
async def test_record_interaction():
    storage = InMemoryStorage()
    memory = MemoryManager(storage)

    result = await memory.record_interaction(
        platform="telegram",
        platform_id="123456",
        action_type=ActionType.COMMENT,
        emotion_tags=["curiosity"],
        sentiment=0.7,
        context="Test interaction"
    )

    assert result["user"] is not None
    assert result["action"].action_type == ActionType.COMMENT
    assert result["relationship"].relationship_score > 0
```

---

## Best Practices

### 1. Always Use MemoryManager

For agent interactions, prefer `MemoryManager` over individual memory classes:

```python
# ✅ Good
context = await memory.get_user_context(platform="telegram", platform_id="123456")

# ❌ Avoid (unless needed)
profile = await user_memory.get_by_platform_id("telegram", "123456")
relationship = await rel_memory.get_relationship(profile.user_id)
```

### 2. Handle New Users Gracefully

```python
context = await memory.get_user_context(platform="telegram", platform_id="123456")

if not context["exists"]:
    # New user - send introduction
    await send_welcome_message(platform_id="123456")
else:
    # Existing user - personalize
    await send_personalized_response(context)
```

### 3. Use Emotion Tags Consistently

```python
# ✅ Good - specific tags
emotion_tags=["curiosity", "intellectual", "engagement"]

# ❌ Avoid - too generic
emotion_tags=["emotion", "feeling"]

# ❌ Avoid - redundant (lowercasing is automatic)
emotion_tags=["Joy", "JOY", "joy"]
```

### 4. Provide Context

Always provide meaningful context for interactions:

```python
# ✅ Good
context="User challenged Freeman's views on free will in a philosophical debate"

# ❌ Avoid
context="User said something"
```

### 5. Calibrate Sentiment

Be thoughtful with sentiment scores:

```python
# ✅ Good - nuanced
sentiment = 0.3  # Mildly positive interest

# ✅ Good - very positive
sentiment = 0.9  # Extremely enthusiastic

# ❌ Avoid - only extremes
sentiment = 1.0  # Should be reserved for exceptional cases
```

---

## Troubleshooting

### Issue: User not found after creation

**Solution:** Always use `get_or_create_user()` for first contact:

```python
profile = await user_memory.get_or_create_user(
    platform="telegram",
    platform_id="123456"
)
```

### Issue: Relationship score not updating

**Solution:** Ensure `auto_update_relationship=True` (default):

```python
await memory.record_interaction(
    platform="telegram",
    platform_id="123456",
    # ... other params ...
    auto_update_relationship=True  # Explicit confirmation
)
```

### Issue: Storage backend not working

**Solution:** Verify storage initialization:

```python
# Check storage health
is_healthy = await memory.health_check()
if not is_healthy:
    raise RuntimeError("Storage backend not accessible")
```

---

## Additional Resources

- [Project README](../README.md)
- [CLAUDE.md](../CLAUDE.md) - Project context
- [BACKLOG.md](../BACKLOG.md) - Feature backlog
- [AGENTS.md](../AGENTS.md) - Agent architecture
