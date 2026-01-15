"""Tests for MemoryManager."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from src.memory.memory_manager import MemoryManager, UserContext
from src.memory.user_memory import UserProfile
from src.memory.relationship_memory import Relationship
from src.memory.conversation_memory import ConversationEntry
from src.memory.action_memory import UserAction as ActionRecord
from src.memory.emotional_memory import EmotionalTrace


@pytest.fixture
def mock_adapter():
    """Create a mock GraphitiAdapter."""
    adapter = MagicMock()

    # Mock async methods
    adapter.add_entity = AsyncMock()
    adapter.add_edge = AsyncMock()
    adapter.search_memory = AsyncMock()
    adapter.health_check = AsyncMock(return_value=True)
    adapter.close = AsyncMock()

    return adapter


@pytest.fixture
def sample_user_profile():
    """Sample user profile for testing."""
    return UserProfile(
        user_id="alice",
        name="Alice",
        platform_ids={"telegram": "123456789"},
        first_seen=datetime(2024, 1, 15, 10, 30, 0),
        last_seen=datetime(2024, 1, 15, 11, 30, 0),
        preferences={"language": "en"}
    )


@pytest.fixture
def sample_relationship():
    """Sample relationship for testing."""
    return Relationship(
        user_id="alice",
        relationship_points=10,
        relationship_level="acquaintance",
        first_interaction=datetime(2024, 1, 15, 10, 30, 0),
        last_interaction=datetime(2024, 1, 15, 11, 30, 0),
        interaction_count=5
    )


@pytest.fixture
def sample_conversation():
    """Sample conversation entry for testing."""
    return ConversationEntry(
        entry_id="conv-1",
        user_id="alice",
        topic="AI consciousness",
        user_position="Believes AI can develop consciousness",
        quotes=["Mind is just information processing"],
        context="Deep philosophical discussion",
        timestamp=datetime(2024, 1, 15, 11, 0, 0)
    )


@pytest.fixture
def sample_action():
    """Sample action record for testing."""
    return ActionRecord(
        action_id="action-1",
        user_id="alice",
        action_type="share",
        points=3,
        context="Shared Freeman's post",
        timestamp=datetime(2024, 1, 15, 11, 15, 0)
    )


@pytest.fixture
def sample_emotion():
    """Sample emotional trace for testing."""
    return EmotionalTrace(
        trace_id="emotion-1",
        emotion_type="inspired",
        intensity=8.5,
        user_id="alice",
        context="Brilliant insight shared",
        timestamp=datetime(2024, 1, 15, 11, 20, 0)
    )


class TestUserContext:
    """Test UserContext class."""

    def test_init_minimal(self):
        """Test UserContext initialization with minimal parameters."""
        context = UserContext(user_id="alice")

        assert context.user_id == "alice"
        assert context.profile == {}
        assert context.relationship == {}
        assert context.recent_conversations == []
        assert context.recent_actions == []
        assert context.recent_emotions == []
        assert isinstance(context.context_timestamp, datetime)

    def test_init_full(
        self,
        sample_user_profile,
        sample_relationship,
        sample_conversation,
        sample_action,
        sample_emotion,
    ):
        """Test UserContext initialization with all parameters."""
        profile_dict = sample_user_profile.to_dict()
        relationship_dict = sample_relationship.to_dict()
        conversations = [sample_conversation.to_dict()]
        actions = [sample_action.to_dict()]
        emotions = [sample_emotion.to_dict()]

        context = UserContext(
            user_id="alice",
            profile=profile_dict,
            relationship=relationship_dict,
            recent_conversations=conversations,
            recent_actions=actions,
            recent_emotions=emotions,
        )

        assert context.user_id == "alice"
        assert context.profile == profile_dict
        assert context.relationship == relationship_dict
        assert context.recent_conversations == conversations
        assert context.recent_actions == actions
        assert context.recent_emotions == emotions

    def test_to_dict(
        self,
        sample_user_profile,
        sample_relationship,
        sample_conversation,
        sample_action,
        sample_emotion,
    ):
        """Test converting UserContext to dictionary."""
        context = UserContext(
            user_id="alice",
            profile=sample_user_profile.to_dict(),
            relationship=sample_relationship.to_dict(),
            recent_conversations=[sample_conversation.to_dict()],
            recent_actions=[sample_action.to_dict()],
            recent_emotions=[sample_emotion.to_dict()],
        )

        data = context.to_dict()

        assert data["user_id"] == "alice"
        assert "profile" in data
        assert "relationship" in data
        assert "recent_conversations" in data
        assert "recent_actions" in data
        assert "recent_emotions" in data
        assert "context_timestamp" in data
        assert len(data["recent_conversations"]) == 1
        assert len(data["recent_actions"]) == 1
        assert len(data["recent_emotions"]) == 1


class TestMemoryManagerInitialization:
    """Test MemoryManager initialization."""

    def test_init_without_adapter(self):
        """Test initialization without pre-configured adapter."""
        manager = MemoryManager()

        assert manager.adapter is not None
        assert manager.config is not None
        assert manager.user_memory is not None
        assert manager.relationship_memory is not None
        assert manager.conversation_memory is not None
        assert manager.action_memory is not None
        assert manager.emotional_memory is not None

    def test_init_with_adapter(self, mock_adapter):
        """Test initialization with pre-configured adapter."""
        manager = MemoryManager(adapter=mock_adapter)

        assert manager.adapter == mock_adapter
        assert manager.config is not None
        # Verify all memory components share the same adapter
        assert manager.user_memory.adapter == mock_adapter
        assert manager.relationship_memory.adapter == mock_adapter
        assert manager.conversation_memory.adapter == mock_adapter
        assert manager.action_memory.adapter == mock_adapter
        assert manager.emotional_memory.adapter == mock_adapter

    @pytest.mark.asyncio
    async def test_initialize_success(self, mock_adapter):
        """Test successful initialization."""
        mock_adapter.health_check.return_value = True

        manager = MemoryManager(adapter=mock_adapter)
        result = await manager.initialize()

        assert result is True
        mock_adapter.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_unhealthy(self, mock_adapter):
        """Test initialization with unhealthy connection."""
        mock_adapter.health_check.return_value = False

        manager = MemoryManager(adapter=mock_adapter)
        result = await manager.initialize()

        assert result is False
        mock_adapter.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_error(self, mock_adapter):
        """Test initialization with error."""
        mock_adapter.health_check.side_effect = Exception("Connection failed")

        manager = MemoryManager(adapter=mock_adapter)
        result = await manager.initialize()

        assert result is False

    @pytest.mark.asyncio
    async def test_close(self, mock_adapter):
        """Test closing memory manager."""
        manager = MemoryManager(adapter=mock_adapter)
        await manager.close()

        mock_adapter.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_with_error(self, mock_adapter):
        """Test closing with error raises exception."""
        mock_adapter.close.side_effect = Exception("Close failed")

        manager = MemoryManager(adapter=mock_adapter)

        with pytest.raises(Exception, match="Close failed"):
            await manager.close()

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_adapter):
        """Test async context manager."""
        mock_adapter.health_check.return_value = True

        async with MemoryManager(adapter=mock_adapter) as manager:
            assert manager.adapter == mock_adapter

        mock_adapter.health_check.assert_called_once()
        mock_adapter.close.assert_called_once()


class TestMemoryManagerRememberUser:
    """Test remember_user method."""

    @pytest.mark.asyncio
    async def test_remember_new_user_minimal(self, mock_adapter):
        """Test remembering a new user with minimal parameters."""
        # Mock user_memory.add_user
        mock_profile = UserProfile(user_id="alice")
        mock_adapter.search_memory.return_value = []  # User doesn't exist

        # Mock relationship_memory.add_relationship
        mock_relationship = Relationship(user_id="alice", relationship_points=0)

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory, "add_user", new=AsyncMock(return_value=mock_profile)
        ), patch.object(
            manager.relationship_memory,
            "add_relationship",
            new=AsyncMock(return_value=mock_relationship),
        ):
            result = await manager.remember_user(user_id="alice")

            assert result["user_id"] == "alice"
            assert "profile" in result
            assert "relationship" in result
            assert result["profile"]["user_id"] == "alice"
            assert result["relationship"]["user_id"] == "alice"

            manager.user_memory.add_user.assert_called_once_with(
                user_id="alice",
                name=None,
                platform=None,
                platform_user_id=None,
                preferences=None,
            )
            manager.relationship_memory.add_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_remember_new_user_full(self, mock_adapter):
        """Test remembering a new user with all parameters."""
        mock_profile = UserProfile(
            user_id="alice",
            name="Alice",
            platform_ids={"telegram": "123456789"},
            preferences={"language": "en"},
        )
        mock_relationship = Relationship(user_id="alice", relationship_points=0)
        mock_adapter.search_memory.return_value = []

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory, "add_user", new=AsyncMock(return_value=mock_profile)
        ), patch.object(
            manager.relationship_memory,
            "add_relationship",
            new=AsyncMock(return_value=mock_relationship),
        ):
            result = await manager.remember_user(
                user_id="alice",
                name="Alice",
                platform="telegram",
                platform_user_id="123456789",
                preferences={"language": "en"},
            )

            assert result["user_id"] == "alice"
            assert result["profile"]["name"] == "Alice"
            assert result["relationship"]["user_id"] == "alice"

            manager.user_memory.add_user.assert_called_once_with(
                user_id="alice",
                name="Alice",
                platform="telegram",
                platform_user_id="123456789",
                preferences={"language": "en"},
            )

    @pytest.mark.asyncio
    async def test_remember_user_error(self, mock_adapter):
        """Test remember_user with error."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "add_user",
            new=AsyncMock(side_effect=Exception("Database error")),
        ):
            with pytest.raises(Exception, match="Database error"):
                await manager.remember_user(user_id="alice")


class TestMemoryManagerRecallUser:
    """Test recall_user method."""

    @pytest.mark.asyncio
    async def test_recall_existing_user(self, mock_adapter, sample_user_profile):
        """Test recalling an existing user."""
        mock_relationship = Relationship(user_id="alice", relationship_points=10)

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(return_value=sample_user_profile),
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=mock_relationship),
        ):
            result = await manager.recall_user("alice")

            assert result is not None
            assert result["user_id"] == "alice"
            assert result["profile"]["name"] == "Alice"
            assert result["relationship"]["relationship_points"] == 10

    @pytest.mark.asyncio
    async def test_recall_user_without_relationship(
        self, mock_adapter, sample_user_profile
    ):
        """Test recalling user without relationship."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(return_value=sample_user_profile),
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=None),
        ):
            result = await manager.recall_user("alice")

            assert result is not None
            assert result["user_id"] == "alice"
            assert result["relationship"] is None

    @pytest.mark.asyncio
    async def test_recall_nonexistent_user(self, mock_adapter):
        """Test recalling a user that doesn't exist."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory, "get_user", new=AsyncMock(return_value=None)
        ):
            result = await manager.recall_user("nobody")

            assert result is None

    @pytest.mark.asyncio
    async def test_recall_user_error(self, mock_adapter):
        """Test recall_user with error."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(side_effect=Exception("Database error")),
        ):
            with pytest.raises(Exception, match="Database error"):
                await manager.recall_user("alice")


class TestMemoryManagerUpdateRelationship:
    """Test update_relationship method."""

    @pytest.mark.asyncio
    async def test_update_existing_relationship(self, mock_adapter):
        """Test updating an existing relationship."""
        old_relationship = Relationship(
            user_id="alice", relationship_points=10, relationship_level="acquaintance"
        )
        new_relationship = Relationship(
            user_id="alice", relationship_points=15, relationship_level="acquaintance"
        )
# Configuration-driven behavior

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(side_effect=[old_relationship, new_relationship]),
        ), patch.object(
            manager.relationship_memory, "add_points", new=AsyncMock(return_value="acquaintance")
        ):
            result = await manager.update_relationship(
                user_id="alice", points=5, context="Good conversation"
            )

            assert result["user_id"] == "alice"
            assert result["relationship_points"] == 15
            assert result["level_changed"] is False
            assert result["old_level"] == "acquaintance"

    @pytest.mark.asyncio
    async def test_update_relationship_level_change(self, mock_adapter):
        """Test updating relationship with level change."""
        old_relationship = Relationship(
            user_id="alice", relationship_points=10, relationship_level="acquaintance"
        )
        new_relationship = Relationship(
            user_id="alice", relationship_points=60, relationship_level="friend"
        )

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(side_effect=[old_relationship, new_relationship]),
        ), patch.object(
            manager.relationship_memory, "add_points", new=AsyncMock(return_value="friend")
        ):
            result = await manager.update_relationship(user_id="alice", points=50)

            assert result["relationship_level"] == "friend"
            assert result["level_changed"] is True
            assert result["old_level"] == "acquaintance"

    @pytest.mark.asyncio
    async def test_update_nonexistent_relationship(self, mock_adapter):
        """Test updating relationship for user without one (creates new)."""
        new_relationship = Relationship(user_id="alice", relationship_points=5)

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(side_effect=[None, new_relationship, new_relationship]),
        ), patch.object(
            manager.relationship_memory,
            "add_relationship",
            new=AsyncMock(return_value=new_relationship),
        ), patch.object(
            manager.relationship_memory, "add_points", new=AsyncMock(return_value="stranger")
        ):
            result = await manager.update_relationship(user_id="alice", points=5)

            assert result["user_id"] == "alice"
            manager.relationship_memory.add_relationship.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_relationship_error(self, mock_adapter):
        """Test update_relationship with error."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(side_effect=Exception("Database error")),
        ):
            with pytest.raises(Exception, match="Database error"):
                await manager.update_relationship(user_id="alice", points=5)


class TestMemoryManagerAddConversation:
    """Test add_conversation method."""

    @pytest.mark.asyncio
    async def test_add_conversation_minimal(self, mock_adapter):
        """Test adding a conversation with minimal parameters."""
        mock_entry = ConversationEntry(
            entry_id="conv-1", user_id="alice", topic="AI ethics"
        )

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.conversation_memory,
            "add_conversation",
            new=AsyncMock(return_value=mock_entry),
        ):
            result = await manager.add_conversation(
                user_id="alice", topic="AI ethics"
            )

            assert result["entry_id"] == "conv-1"
            assert result["user_id"] == "alice"
            assert result["topic"] == "AI ethics"

            manager.conversation_memory.add_conversation.assert_called_once_with(
                user_id="alice",
                topic="AI ethics",
                user_position=None,
                quotes=None,
                context=None,
                metadata=None,
            )

    @pytest.mark.asyncio
    async def test_add_conversation_full(self, mock_adapter):
        """Test adding a conversation with all parameters."""
        mock_entry = ConversationEntry(
            entry_id="conv-1",
            user_id="alice",
            topic="AI consciousness",
            user_position="Believes AI can develop consciousness",
            quotes=["Mind is just information processing"],
            context="Deep discussion",
        )

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.conversation_memory,
            "add_conversation",
            new=AsyncMock(return_value=mock_entry),
        ):
            result = await manager.add_conversation(
                user_id="alice",
                topic="AI consciousness",
                user_position="Believes AI can develop consciousness",
                quotes=["Mind is just information processing"],
                context="Deep discussion",
                metadata={"platform": "telegram"},
            )

            assert result["topic"] == "AI consciousness"
            assert result["user_position"] == "Believes AI can develop consciousness"

    @pytest.mark.asyncio
    async def test_add_conversation_error(self, mock_adapter):
        """Test add_conversation with error."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.conversation_memory,
            "add_conversation",
            new=AsyncMock(side_effect=Exception("Database error")),
        ):
            with pytest.raises(Exception, match="Database error"):
                await manager.add_conversation(user_id="alice", topic="AI ethics")


class TestMemoryManagerAddAction:
    """Test add_action method."""

    @pytest.mark.asyncio
    async def test_add_action_updates_relationship(self, mock_adapter):
        """Test that adding action updates relationship."""
        mock_action = ActionRecord(
            action_id="action-1",
            user_id="alice",
            action_type="share",
            points=3,
        )
        mock_relationship_result = {
            "user_id": "alice",
            "relationship_points": 13,
            "relationship_level": "acquaintance",
            "level_changed": False,
            "old_level": "acquaintance",
        }

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.action_memory, "add_action", new=AsyncMock(return_value=mock_action)
        ), patch.object(
            manager,
            "update_relationship",
            new=AsyncMock(return_value=mock_relationship_result),
        ):
            result = await manager.add_action(
                user_id="alice", action_type="share", context="Shared post"
            )

            assert "action" in result
            assert result["action"]["action_type"] == "share"
            assert result["action"]["points"] == 3
            assert result["relationship_level"] == "acquaintance"
            assert result["relationship_points"] == 13
            assert result["level_changed"] is False

            # Verify relationship was updated with action points
            manager.update_relationship.assert_called_once_with(
                user_id="alice", points=3, context="Action: share"
            )

    @pytest.mark.asyncio
    async def test_add_action_with_level_change(self, mock_adapter):
        """Test adding action that causes level change."""
        mock_action = ActionRecord(
            action_id="action-1",
            user_id="alice",
            action_type="purchase_token",
            points=10,
        )
        mock_relationship_result = {
            "user_id": "alice",
            "relationship_points": 60,
            "relationship_level": "friend",
            "level_changed": True,
            "old_level": "acquaintance",
        }

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.action_memory, "add_action", new=AsyncMock(return_value=mock_action)
        ), patch.object(
            manager,
            "update_relationship",
            new=AsyncMock(return_value=mock_relationship_result),
        ):
            result = await manager.add_action(
                user_id="alice", action_type="purchase_token"
            )

            assert result["level_changed"] is True
            assert result["relationship_level"] == "friend"

    @pytest.mark.asyncio
    async def test_add_action_error(self, mock_adapter):
        """Test add_action with error."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.action_memory,
            "add_action",
            new=AsyncMock(side_effect=Exception("Database error")),
        ):
            with pytest.raises(Exception, match="Database error"):
                await manager.add_action(user_id="alice", action_type="share")


class TestMemoryManagerAddEmotion:
    """Test add_emotion method."""

    @pytest.mark.asyncio
    async def test_add_emotion_minimal(self, mock_adapter):
        """Test adding emotion with minimal parameters."""
        mock_trace = EmotionalTrace(
            trace_id="emotion-1", emotion_type="curious", intensity=7.0
        )

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.emotional_memory,
            "add_emotion",
            new=AsyncMock(return_value=mock_trace),
        ):
            result = await manager.add_emotion(emotion_type="curious", intensity=7.0)

            assert result["trace_id"] == "emotion-1"
            assert result["emotion_type"] == "curious"
            assert result["intensity"] == 7.0

            manager.emotional_memory.add_emotion.assert_called_once_with(
                emotion_type="curious",
                intensity=7.0,
                user_id=None,
                context=None,
                metadata=None,
            )

    @pytest.mark.asyncio
    async def test_add_emotion_full(self, mock_adapter):
        """Test adding emotion with all parameters."""
        mock_trace = EmotionalTrace(
            trace_id="emotion-1",
            emotion_type="inspired",
            intensity=8.5,
            user_id="alice",
            context="Brilliant insight",
        )

        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.emotional_memory,
            "add_emotion",
            new=AsyncMock(return_value=mock_trace),
        ):
            result = await manager.add_emotion(
                emotion_type="inspired",
                intensity=8.5,
                user_id="alice",
                context="Brilliant insight",
                metadata={"platform": "telegram"},
            )

            assert result["emotion_type"] == "inspired"
            assert result["intensity"] == 8.5
            assert result["user_id"] == "alice"

    @pytest.mark.asyncio
    async def test_add_emotion_error(self, mock_adapter):
        """Test add_emotion with error."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.emotional_memory,
            "add_emotion",
            new=AsyncMock(side_effect=Exception("Database error")),
        ):
            with pytest.raises(Exception, match="Database error"):
                await manager.add_emotion(emotion_type="curious", intensity=7.0)


class TestMemoryManagerGetUserContext:
    """Test get_user_context method."""

    @pytest.mark.asyncio
    async def test_get_user_context_complete(
        self,
        mock_adapter,
        sample_user_profile,
        sample_relationship,
        sample_conversation,
        sample_action,
        sample_emotion,
    ):
        """Test getting complete user context."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(return_value=sample_user_profile),
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=sample_relationship),
        ), patch.object(
            manager.conversation_memory,
            "get_conversations_by_user",
            new=AsyncMock(return_value=[sample_conversation]),
        ), patch.object(
            manager.action_memory,
            "get_actions_by_user",
            new=AsyncMock(return_value=[sample_action]),
        ), patch.object(
            manager.emotional_memory,
            "get_emotions_by_user",
            new=AsyncMock(return_value=[sample_emotion]),
        ):
            context = await manager.get_user_context("alice")

            assert context is not None
            assert isinstance(context, UserContext)
            assert context.user_id == "alice"
            assert context.profile["name"] == "Alice"
            assert context.relationship["relationship_level"] == "acquaintance"
            assert len(context.recent_conversations) == 1
            assert len(context.recent_actions) == 1
            assert len(context.recent_emotions) == 1

    @pytest.mark.asyncio
    async def test_get_user_context_without_relationship(
        self,
        mock_adapter,
        sample_user_profile,
        sample_conversation,
        sample_action,
        sample_emotion,
    ):
        """Test getting user context without relationship."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(return_value=sample_user_profile),
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=None),
        ), patch.object(
            manager.conversation_memory,
            "get_conversations_by_user",
            new=AsyncMock(return_value=[sample_conversation]),
        ), patch.object(
            manager.action_memory,
            "get_actions_by_user",
            new=AsyncMock(return_value=[sample_action]),
        ), patch.object(
            manager.emotional_memory,
            "get_emotions_by_user",
            new=AsyncMock(return_value=[sample_emotion]),
        ):
            context = await manager.get_user_context("alice")

            assert context is not None
            assert context.relationship == {} or context.relationship is None

    @pytest.mark.asyncio
    async def test_get_user_context_empty_history(
        self, mock_adapter, sample_user_profile, sample_relationship
    ):
        """Test getting user context with empty interaction history."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(return_value=sample_user_profile),
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=sample_relationship),
        ), patch.object(
            manager.conversation_memory,
            "get_conversations_by_user",
            new=AsyncMock(return_value=[]),
        ), patch.object(
            manager.action_memory,
            "get_actions_by_user",
            new=AsyncMock(return_value=[]),
        ), patch.object(
            manager.emotional_memory,
            "get_emotions_by_user",
            new=AsyncMock(return_value=[]),
        ):
            context = await manager.get_user_context("alice")

            assert context is not None
            assert len(context.recent_conversations) == 0
            assert len(context.recent_actions) == 0
            assert len(context.recent_emotions) == 0

    @pytest.mark.asyncio
    async def test_get_user_context_custom_limits(
        self,
        mock_adapter,
        sample_user_profile,
        sample_relationship,
    ):
        """Test getting user context with custom limits."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(return_value=sample_user_profile),
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=sample_relationship),
        ), patch.object(
            manager.conversation_memory,
            "get_conversations_by_user",
            new=AsyncMock(return_value=[]),
        ) as mock_conv, patch.object(
            manager.action_memory,
            "get_actions_by_user",
            new=AsyncMock(return_value=[]),
        ) as mock_act, patch.object(
            manager.emotional_memory,
            "get_emotions_by_user",
            new=AsyncMock(return_value=[]),
        ) as mock_emo:
            await manager.get_user_context(
                "alice",
                conversation_limit=5,
                action_limit=15,
                emotion_limit=7,
            )

            mock_conv.assert_called_once_with(user_id="alice", limit=5)
            mock_act.assert_called_once_with(user_id="alice", limit=15)
            mock_emo.assert_called_once_with(user_id="alice", limit=7)

    @pytest.mark.asyncio
    async def test_get_user_context_nonexistent_user(self, mock_adapter):
        """Test getting context for nonexistent user."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory, "get_user", new=AsyncMock(return_value=None)
        ):
            context = await manager.get_user_context("nobody")

            assert context is None

    @pytest.mark.asyncio
    async def test_get_user_context_error(self, mock_adapter):
        """Test get_user_context with error."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(side_effect=Exception("Database error")),
        ):
            with pytest.raises(Exception, match="Database error"):
                await manager.get_user_context("alice")


class TestMemoryManagerIntegration:
    """Test MemoryManager integration scenarios."""

    @pytest.mark.asyncio
    async def test_complete_user_flow(self, mock_adapter):
        """Test complete user interaction flow."""
        # Setup mocks
        mock_profile = UserProfile(user_id="alice", name="Alice")
        mock_relationship = Relationship(user_id="alice", relationship_points=0)
        mock_relationship_updated = Relationship(
            user_id="alice", relationship_points=3
        )
        mock_conversation = ConversationEntry(
            entry_id="conv-1", user_id="alice", topic="AI ethics"
        )
        mock_action = ActionRecord(
            action_id="action-1", user_id="alice", action_type="share", points=3
        )

        manager = MemoryManager(adapter=mock_adapter)

        # 1. Remember user
        with patch.object(
            manager.user_memory, "add_user", new=AsyncMock(return_value=mock_profile)
        ), patch.object(
            manager.relationship_memory,
            "add_relationship",
            new=AsyncMock(return_value=mock_relationship),
        ):
            user_data = await manager.remember_user(user_id="alice", name="Alice")
            assert user_data["user_id"] == "alice"

        # 2. Add conversation
        with patch.object(
            manager.conversation_memory,
            "add_conversation",
            new=AsyncMock(return_value=mock_conversation),
        ):
            conv_data = await manager.add_conversation(
                user_id="alice", topic="AI ethics"
            )
            assert conv_data["topic"] == "AI ethics"

        # 3. Add action (which updates relationship)
        with patch.object(
            manager.action_memory, "add_action", new=AsyncMock(return_value=mock_action)
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(
                side_effect=[mock_relationship, mock_relationship_updated]
            ),
        ), patch.object(
            manager.relationship_memory,
            "add_points",
            new=AsyncMock(return_value="stranger"),
        ):
            action_result = await manager.add_action(
                user_id="alice", action_type="share"
            )
            assert action_result["action"]["points"] == 3

        # 4. Get complete context
        with patch.object(
            manager.user_memory, "get_user", new=AsyncMock(return_value=mock_profile)
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=mock_relationship_updated),
        ), patch.object(
            manager.conversation_memory,
            "get_conversations_by_user",
            new=AsyncMock(return_value=[mock_conversation]),
        ), patch.object(
            manager.action_memory,
            "get_actions_by_user",
            new=AsyncMock(return_value=[mock_action]),
        ), patch.object(
            manager.emotional_memory,
            "get_emotions_by_user",
            new=AsyncMock(return_value=[]),
        ):
            context = await manager.get_user_context("alice")
            assert context.user_id == "alice"
            assert len(context.recent_conversations) == 1
            assert len(context.recent_actions) == 1

    @pytest.mark.asyncio
    async def test_context_to_dict_serialization(
        self,
        mock_adapter,
        sample_user_profile,
        sample_relationship,
        sample_conversation,
        sample_action,
        sample_emotion,
    ):
        """Test that context can be serialized to dict."""
        manager = MemoryManager(adapter=mock_adapter)

        with patch.object(
            manager.user_memory,
            "get_user",
            new=AsyncMock(return_value=sample_user_profile),
        ), patch.object(
            manager.relationship_memory,
            "get_relationship",
            new=AsyncMock(return_value=sample_relationship),
        ), patch.object(
            manager.conversation_memory,
            "get_conversations_by_user",
            new=AsyncMock(return_value=[sample_conversation]),
        ), patch.object(
            manager.action_memory,
            "get_actions_by_user",
            new=AsyncMock(return_value=[sample_action]),
        ), patch.object(
            manager.emotional_memory,
            "get_emotions_by_user",
            new=AsyncMock(return_value=[sample_emotion]),
        ):
            context = await manager.get_user_context("alice")
            context_dict = context.to_dict()

            # Verify all fields are present and serializable
            assert "user_id" in context_dict
            assert "profile" in context_dict
            assert "relationship" in context_dict
            assert "recent_conversations" in context_dict
            assert "recent_actions" in context_dict
            assert "recent_emotions" in context_dict
            assert "context_timestamp" in context_dict

            # Verify timestamp is ISO format string
            assert isinstance(context_dict["context_timestamp"], str)
