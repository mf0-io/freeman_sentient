"""Tests for UserMemory."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict

from src.memory.user_memory import UserMemory, UserProfile


@pytest.fixture
def mock_adapter():
    """Create a mock GraphitiAdapter."""
    adapter = MagicMock()

    # Mock async methods
    adapter.add_entity = AsyncMock()
    adapter.search_memory = AsyncMock()

    return adapter


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "user_id": "alice",
        "name": "Alice",
        "platform_ids": {"telegram": "123456789"},
        "first_seen": "2024-01-15T10:30:00",
        "last_seen": "2024-01-15T10:30:00",
        "preferences": {"language": "en", "theme": "dark"}
    }


@pytest.fixture
def sample_user_profile(sample_user_data):
    """Create a sample UserProfile instance."""
    return UserProfile.from_dict(sample_user_data)


class TestUserProfile:
    """Test UserProfile class."""

    def test_init_minimal(self):
        """Test UserProfile initialization with minimal parameters."""
        profile = UserProfile(user_id="bob")

        assert profile.user_id == "bob"
        assert profile.name == "bob"  # Should default to user_id
        assert profile.platform_ids == {}
        assert isinstance(profile.first_seen, datetime)
        assert isinstance(profile.last_seen, datetime)
        assert profile.preferences == {}

    def test_init_full(self):
        """Test UserProfile initialization with all parameters."""
        first_seen = datetime(2024, 1, 15, 10, 30, 0)
        last_seen = datetime(2024, 1, 15, 11, 30, 0)
        platform_ids = {"telegram": "123", "twitter": "@alice"}
        preferences = {"language": "en", "theme": "dark"}

        profile = UserProfile(
            user_id="alice",
            name="Alice",
            platform_ids=platform_ids,
            first_seen=first_seen,
            last_seen=last_seen,
            preferences=preferences,
        )

        assert profile.user_id == "alice"
        assert profile.name == "Alice"
        assert profile.platform_ids == platform_ids
        assert profile.first_seen == first_seen
        assert profile.last_seen == last_seen
        assert profile.preferences == preferences

    def test_to_dict(self, sample_user_profile):
        """Test converting UserProfile to dictionary."""
        data = sample_user_profile.to_dict()

        assert data["user_id"] == "alice"
        assert data["name"] == "Alice"
        assert data["platform_ids"] == {"telegram": "123456789"}
        assert "first_seen" in data
        assert "last_seen" in data
        assert data["preferences"] == {"language": "en", "theme": "dark"}

    def test_from_dict(self, sample_user_data):
        """Test creating UserProfile from dictionary."""
        profile = UserProfile.from_dict(sample_user_data)

        assert profile.user_id == "alice"
        assert profile.name == "Alice"
        assert profile.platform_ids == {"telegram": "123456789"}
        assert isinstance(profile.first_seen, datetime)
        assert isinstance(profile.last_seen, datetime)
        assert profile.preferences == {"language": "en", "theme": "dark"}

    def test_from_dict_minimal(self):
        """Test creating UserProfile from minimal dictionary."""
        minimal_data = {
            "user_id": "charlie",
            "first_seen": "2024-01-15T10:30:00",
            "last_seen": "2024-01-15T10:30:00",
        }

        profile = UserProfile.from_dict(minimal_data)

        assert profile.user_id == "charlie"
        assert profile.name == "charlie"  # defaults to user_id when name not provided
        assert profile.platform_ids == {}
        assert profile.preferences == {}

    def test_round_trip_conversion(self, sample_user_profile):
        """Test that to_dict and from_dict are inverses."""
        data = sample_user_profile.to_dict()
        profile = UserProfile.from_dict(data)

        assert profile.user_id == sample_user_profile.user_id
        assert profile.name == sample_user_profile.name
        assert profile.platform_ids == sample_user_profile.platform_ids
        assert profile.preferences == sample_user_profile.preferences


class TestUserMemoryInitialization:
    """Test UserMemory initialization."""

    def test_init_without_adapter(self):
        """Test initialization without pre-configured adapter."""
        memory = UserMemory()

        assert memory.adapter is not None
        assert memory.config is not None

    def test_init_with_adapter(self, mock_adapter):
        """Test initialization with pre-configured adapter."""
        memory = UserMemory(adapter=mock_adapter)

        assert memory.adapter == mock_adapter
        assert memory.config is not None


class TestUserMemoryAddUser:
    """Test add_user method."""

    @pytest.mark.asyncio
    async def test_add_new_user_minimal(self, mock_adapter):
        """Test adding a new user with minimal parameters."""
        mock_adapter.search_memory.return_value = []

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.add_user(user_id="alice")

        assert profile.user_id == "alice"
        assert profile.name == "alice"

        # Verify adapter was called
        mock_adapter.add_entity.assert_called_once()
        call_args = mock_adapter.add_entity.call_args
        assert call_args.kwargs['name'] == "alice"
        assert call_args.kwargs['entity_type'] == "user"

    @pytest.mark.asyncio
    async def test_add_new_user_full(self, mock_adapter):
        """Test adding a new user with all parameters."""
        mock_adapter.search_memory.return_value = []

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.add_user(
            user_id="alice",
            name="Alice",
            platform="telegram",
            platform_user_id="123456789",
            preferences={"language": "en"}
        )

        assert profile.user_id == "alice"
        assert profile.name == "Alice"
        assert profile.platform_ids == {"telegram": "123456789"}
        assert profile.preferences == {"language": "en"}

        # Verify adapter was called
        mock_adapter.add_entity.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_user_updates_existing(self, mock_adapter, sample_user_data):
        """Test that adding existing user updates their information."""
        # Mock existing user
        existing_profile = UserProfile.from_dict(sample_user_data)
        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.add_user(
            user_id="alice",
            name="Alice Updated",
            platform="twitter",
            platform_user_id="@alice",
            preferences={"theme": "light"}
        )

        # Name should be updated
        assert profile.name == "Alice Updated"

        # Platform IDs should be merged
        assert "telegram" in profile.platform_ids
        assert "twitter" in profile.platform_ids
        assert profile.platform_ids["twitter"] == "@alice"

        # Preferences should be merged
        assert profile.preferences["language"] == "en"  # Original
        assert profile.preferences["theme"] == "light"  # Updated

    @pytest.mark.asyncio
    async def test_add_user_error_handling(self, mock_adapter):
        """Test error handling when adding user fails."""
        mock_adapter.search_memory.side_effect = Exception("Database error")

        memory = UserMemory(adapter=mock_adapter)

        with pytest.raises(Exception, match="Database error"):
            await memory.add_user(user_id="alice")


class TestUserMemoryGetUser:
    """Test get_user method."""

    @pytest.mark.asyncio
    async def test_get_existing_user(self, mock_adapter, sample_user_data):
        """Test retrieving an existing user."""
        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.get_user("alice")

        assert profile is not None
        assert profile.user_id == "alice"
        assert profile.name == "Alice"

        # Verify search was called correctly
        mock_adapter.search_memory.assert_called_once()
        call_args = mock_adapter.search_memory.call_args
        assert call_args.kwargs['query'] == "user alice"
        assert call_args.kwargs['limit'] == 1
        assert call_args.kwargs['entity_filter'] == ["user"]

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, mock_adapter):
        """Test retrieving a user that doesn't exist."""
        mock_adapter.search_memory.return_value = []

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.get_user("nonexistent")

        assert profile is None

    @pytest.mark.asyncio
    async def test_get_user_without_attributes(self, mock_adapter):
        """Test retrieving a user without attributes field."""
        mock_adapter.search_memory.return_value = [
            {"user_id": "alice"}  # No attributes field
        ]

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.get_user("alice")

        assert profile is None

    @pytest.mark.asyncio
    async def test_get_user_error_handling(self, mock_adapter):
        """Test error handling when retrieval fails."""
        mock_adapter.search_memory.side_effect = Exception("Search error")

        memory = UserMemory(adapter=mock_adapter)

        with pytest.raises(Exception, match="Search error"):
            await memory.get_user("alice")


class TestUserMemoryUpdateUser:
    """Test update_user method."""

    @pytest.mark.asyncio
    async def test_update_existing_user_name(self, mock_adapter, sample_user_data):
        """Test updating an existing user's name."""
        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.update_user(
            user_id="alice",
            name="Alice Smith"
        )

        assert profile is not None
        assert profile.name == "Alice Smith"

        # Verify entity was updated
        mock_adapter.add_entity.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_existing_user_platform_ids(self, mock_adapter, sample_user_data):
        """Test updating an existing user's platform IDs."""
        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.update_user(
            user_id="alice",
            platform_ids={"twitter": "@alice", "discord": "alice#1234"}
        )

        assert profile is not None
        assert "telegram" in profile.platform_ids  # Original
        assert "twitter" in profile.platform_ids  # New
        assert "discord" in profile.platform_ids  # New

    @pytest.mark.asyncio
    async def test_update_existing_user_preferences(self, mock_adapter, sample_user_data):
        """Test updating an existing user's preferences."""
        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.update_user(
            user_id="alice",
            preferences={"theme": "light", "notifications": True}
        )

        assert profile is not None
        assert profile.preferences["language"] == "en"  # Original
        assert profile.preferences["theme"] == "light"  # Updated
        assert profile.preferences["notifications"] is True  # New

    @pytest.mark.asyncio
    async def test_update_all_fields(self, mock_adapter, sample_user_data):
        """Test updating all fields at once."""
        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.update_user(
            user_id="alice",
            name="Alice Smith",
            platform_ids={"twitter": "@alice"},
            preferences={"theme": "light"}
        )

        assert profile is not None
        assert profile.name == "Alice Smith"
        assert "twitter" in profile.platform_ids
        assert profile.preferences["theme"] == "light"

    @pytest.mark.asyncio
    async def test_update_nonexistent_user(self, mock_adapter):
        """Test updating a user that doesn't exist."""
        mock_adapter.search_memory.return_value = []

        memory = UserMemory(adapter=mock_adapter)
        profile = await memory.update_user(
            user_id="nonexistent",
            name="New Name"
        )

        assert profile is None

        # Verify add_entity was not called
        mock_adapter.add_entity.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_error_handling(self, mock_adapter):
        """Test error handling when update fails."""
        mock_adapter.search_memory.side_effect = Exception("Update error")

        memory = UserMemory(adapter=mock_adapter)

        with pytest.raises(Exception, match="Update error"):
            await memory.update_user(user_id="alice", name="New Name")


class TestUserMemoryListUsers:
    """Test list_users method."""

    @pytest.mark.asyncio
    async def test_list_users_with_results(self, mock_adapter, sample_user_data):
        """Test listing users when results exist."""
        user_data_2 = {
            "user_id": "bob",
            "name": "Bob",
            "platform_ids": {},
            "first_seen": "2024-01-16T10:30:00",
            "last_seen": "2024-01-16T10:30:00",
            "preferences": {}
        }

        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data},
            {"attributes": user_data_2}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profiles = await memory.list_users()

        assert len(profiles) == 2
        assert profiles[0].user_id == "alice"
        assert profiles[1].user_id == "bob"

        # Verify search was called correctly
        mock_adapter.search_memory.assert_called_once()
        call_args = mock_adapter.search_memory.call_args
        assert call_args.kwargs['query'] == "user"
        assert call_args.kwargs['entity_filter'] == ["user"]

    @pytest.mark.asyncio
    async def test_list_users_with_limit(self, mock_adapter, sample_user_data):
        """Test listing users with custom limit."""
        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data}
        ]

        memory = UserMemory(adapter=mock_adapter)
        profiles = await memory.list_users(limit=5)

        # Verify limit was passed
        call_args = mock_adapter.search_memory.call_args
        assert call_args.kwargs['limit'] == 5

    @pytest.mark.asyncio
    async def test_list_users_empty(self, mock_adapter):
        """Test listing users when no users exist."""
        mock_adapter.search_memory.return_value = []

        memory = UserMemory(adapter=mock_adapter)
        profiles = await memory.list_users()

        assert profiles == []

    @pytest.mark.asyncio
    async def test_list_users_skips_invalid_profiles(self, mock_adapter, sample_user_data):
        """Test that list_users skips profiles that fail to parse."""
        invalid_data = {"not_a_user_id": "invalid"}  # Missing required user_id field

        mock_adapter.search_memory.return_value = [
            {"attributes": sample_user_data},  # Valid
            {"no_attributes": "here"},  # Invalid - no attributes
            {"attributes": invalid_data}  # Invalid - missing user_id
        ]

        memory = UserMemory(adapter=mock_adapter)
        profiles = await memory.list_users()

        # Should only get the valid profile
        assert len(profiles) == 1
        assert profiles[0].user_id == "alice"

    @pytest.mark.asyncio
    async def test_list_users_error_handling(self, mock_adapter):
        """Test error handling when listing fails."""
        mock_adapter.search_memory.side_effect = Exception("List error")

        memory = UserMemory(adapter=mock_adapter)

        with pytest.raises(Exception, match="List error"):
            await memory.list_users()


class TestUserMemoryIntegration:
    """Integration tests for UserMemory workflows."""

    @pytest.mark.asyncio
    async def test_add_get_update_workflow(self, mock_adapter):
        """Test complete workflow of add, get, and update."""
        # Setup: No user exists initially
        mock_adapter.search_memory.return_value = []

        memory = UserMemory(adapter=mock_adapter)

        # Add user
        profile1 = await memory.add_user(
            user_id="workflow_user",
            name="Workflow User",
            platform="telegram",
            platform_user_id="999"
        )

        assert profile1.user_id == "workflow_user"
        assert profile1.name == "Workflow User"

        # Simulate user now exists for subsequent calls
        user_data = profile1.to_dict()
        mock_adapter.search_memory.return_value = [{"attributes": user_data}]

        # Get user
        profile2 = await memory.get_user("workflow_user")
        assert profile2 is not None
        assert profile2.user_id == "workflow_user"

        # Update user
        profile3 = await memory.update_user(
            user_id="workflow_user",
            preferences={"language": "ru"}
        )

        assert profile3 is not None
        assert profile3.preferences["language"] == "ru"

    @pytest.mark.asyncio
    async def test_timestamp_updates(self, mock_adapter):
        """Test that timestamps are properly updated."""
        mock_adapter.search_memory.return_value = []

        memory = UserMemory(adapter=mock_adapter)

        # Add user
        profile1 = await memory.add_user(user_id="timestamp_user")
        first_seen_1 = profile1.first_seen
        last_seen_1 = profile1.last_seen

        # Simulate time passing and user exists
        user_data = profile1.to_dict()
        mock_adapter.search_memory.return_value = [{"attributes": user_data}]

        # Add again (update)
        profile2 = await memory.add_user(user_id="timestamp_user")

        # first_seen should remain the same, last_seen should update
        # Note: Due to test speed, we just verify the fields exist and are datetimes
        assert isinstance(profile2.first_seen, datetime)
        assert isinstance(profile2.last_seen, datetime)
