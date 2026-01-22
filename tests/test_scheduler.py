"""
Unit tests for Content Scheduler Module
Tests ContentScheduler class for optimal scheduling and topic spacing
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

from src.content.scheduler import ContentScheduler, schedule_all, get_schedule_preview
from src.content.storage import ContentQueue, QueuedContent


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'scheduling': {
            'frequency': {
                'min_interval_hours': 4,
                'max_interval_hours': 12,
                'posts_per_day': 3
            },
            'optimal_times': ['08:00', '14:00', '20:00'],
            'time_windows': [
                {'start': '06:00', 'end': '23:00'}
            ],
            'topic_spacing': {
                'enabled': True,
                'min_hours_between_similar': 24
            }
        },
        'content_queue': {
            'storage_path': 'data/test_queue.json',
            'min_queue_size': 5,
            'max_queue_size': 20
        }
    }


@pytest.fixture
def mock_queue():
    """Mock ContentQueue"""
    queue = Mock(spec=ContentQueue)
    return queue


@pytest.fixture
def sample_queued_content():
    """Sample QueuedContent for testing"""
    return QueuedContent(
        id="test-id-1",
        text="Test tweet about AI consciousness",
        topic="AI and consciousness",
        platform="twitter",
        sentiment="philosophical",
        source="philosophical_topics",
        status="queued",
        created_at=datetime.now(),
        scheduled_for=None
    )


@pytest.fixture
def scheduler(mock_config, mock_queue):
    """Create ContentScheduler instance with mocked config and queue"""
    with patch.object(ContentScheduler, '_load_config', return_value=mock_config):
        with patch('src.content.scheduler.ContentQueue', return_value=mock_queue):
            return ContentScheduler()


class TestContentScheduler:
    """Test ContentScheduler class"""

    def test_initialization(self, scheduler, mock_config):
        """Test ContentScheduler initialization"""
        assert scheduler.config == mock_config
        assert scheduler.min_interval_hours == 4
        assert scheduler.max_interval_hours == 12
        assert scheduler.posts_per_day == 3
        assert len(scheduler.optimal_times) == 3
        assert scheduler.topic_spacing_enabled is True
        assert scheduler.min_hours_between_similar == 24

    def test_get_next_optimal_time_morning(self, scheduler):
        """Test getting next optimal time for morning"""
        # Test at 6 AM - should get 8 AM today
        now = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        next_time = scheduler._get_next_optimal_time(now)

        assert next_time.hour == 8
        assert next_time.minute == 0
        assert next_time.date() == now.date()

    def test_get_next_optimal_time_after_last_slot(self, scheduler):
        """Test getting next optimal time after last daily slot"""
        # Test at 11 PM - should get 8 AM tomorrow
        now = datetime.now().replace(hour=23, minute=0, second=0, microsecond=0)
        next_time = scheduler._get_next_optimal_time(now)

        assert next_time.hour == 8
        assert next_time.minute == 0
        assert next_time.date() == (now + timedelta(days=1)).date()

    def test_is_within_time_window_valid(self, scheduler):
        """Test time window check for valid time"""
        valid_time = datetime.now().replace(hour=10, minute=0)
        assert scheduler._is_within_time_window(valid_time) is True

    def test_is_within_time_window_invalid(self, scheduler):
        """Test time window check for invalid time"""
        invalid_time = datetime.now().replace(hour=2, minute=0)
        assert scheduler._is_within_time_window(invalid_time) is False

    def test_is_within_time_window_no_restrictions(self, mock_config):
        """Test time window check when no restrictions"""
        mock_config['scheduling']['time_windows'] = []

        with patch.object(ContentScheduler, '_load_config', return_value=mock_config):
            with patch('src.content.scheduler.ContentQueue'):
                scheduler = ContentScheduler()
                any_time = datetime.now()
                assert scheduler._is_within_time_window(any_time) is True

    def test_respects_min_interval_valid(self, scheduler):
        """Test minimum interval check with valid spacing"""
        candidate = datetime.now()
        scheduled_times = [
            candidate - timedelta(hours=5),  # 5 hours before
            candidate + timedelta(hours=5)   # 5 hours after
        ]

        assert scheduler._respects_min_interval(candidate, scheduled_times) is True

    def test_respects_min_interval_invalid(self, scheduler):
        """Test minimum interval check with too close spacing"""
        candidate = datetime.now()
        scheduled_times = [
            candidate - timedelta(hours=2)  # Only 2 hours before (min is 4)
        ]

        assert scheduler._respects_min_interval(candidate, scheduled_times) is False

    def test_respects_min_interval_empty_schedule(self, scheduler):
        """Test minimum interval check with empty schedule"""
        candidate = datetime.now()
        assert scheduler._respects_min_interval(candidate, []) is True

    def test_topics_are_similar_exact_match(self, scheduler):
        """Test topic similarity for exact matches"""
        assert scheduler._topics_are_similar("AI and consciousness", "AI and consciousness") is True

    def test_topics_are_similar_substring(self, scheduler):
        """Test topic similarity for substring matches"""
        assert scheduler._topics_are_similar("AI consciousness", "AI and consciousness") is True

    def test_topics_are_similar_word_overlap(self, scheduler):
        """Test topic similarity for significant word overlap"""
        assert scheduler._topics_are_similar(
            "Social manipulation and control",
            "Social manipulation techniques"
        ) is True

    def test_topics_are_not_similar(self, scheduler):
        """Test topics that are not similar"""
        assert scheduler._topics_are_similar(
            "AI and consciousness",
            "Education system critique"
        ) is False

    def test_respects_topic_spacing_valid(self, scheduler):
        """Test topic spacing with valid spacing"""
        candidate = datetime.now()
        content = QueuedContent(
            id="test",
            text="Test",
            topic="AI and consciousness",
            platform="twitter",
            sentiment="philosophical",
            source="test",
            status="queued",
            created_at=datetime.now(),
            scheduled_for=None
        )

        # Mock scheduled posts with different topic
        scheduled_post = QueuedContent(
            id="scheduled",
            text="Test",
            topic="Education critique",  # Different topic
            platform="twitter",
            sentiment="philosophical",
            source="test",
            status="scheduled",
            created_at=datetime.now(),
            scheduled_for=candidate - timedelta(hours=12)
        )

        scheduler.queue.get_scheduled = Mock(return_value=[scheduled_post])

        assert scheduler._respects_topic_spacing(candidate, content) is True

    def test_respects_topic_spacing_invalid(self, scheduler):
        """Test topic spacing with similar topic too close"""
        candidate = datetime.now()
        content = QueuedContent(
            id="test",
            text="Test",
            topic="AI and consciousness",
            platform="twitter",
            sentiment="philosophical",
            source="test",
            status="queued",
            created_at=datetime.now(),
            scheduled_for=None
        )

        # Mock scheduled post with same topic within 24h
        scheduled_post = QueuedContent(
            id="scheduled",
            text="Test",
            topic="AI and consciousness",  # Same topic
            platform="twitter",
            sentiment="philosophical",
            source="test",
            status="scheduled",
            created_at=datetime.now(),
            scheduled_for=candidate - timedelta(hours=12)  # Only 12h away (min is 24)
        )

        scheduler.queue.get_scheduled = Mock(return_value=[scheduled_post])

        assert scheduler._respects_topic_spacing(candidate, content) is False

    def test_respects_daily_limit_valid(self, scheduler):
        """Test daily limit check with room for more posts"""
        candidate = datetime.now().replace(hour=10)
        scheduled_times = [
            candidate.replace(hour=8),  # 1 post same day
        ]

        # Should return True because limit is 3
        assert scheduler._respects_daily_limit(candidate, scheduled_times) is True

    def test_respects_daily_limit_at_limit(self, scheduler):
        """Test daily limit check when at limit"""
        candidate = datetime.now().replace(hour=20)
        scheduled_times = [
            candidate.replace(hour=8),   # 1st post
            candidate.replace(hour=14),  # 2nd post
            candidate.replace(hour=18),  # 3rd post (at limit of 3)
        ]

        # Should return False because already at limit
        assert scheduler._respects_daily_limit(candidate, scheduled_times) is False

    def test_respects_daily_limit_different_days(self, scheduler):
        """Test daily limit only counts same day"""
        candidate = datetime.now().replace(hour=10)
        yesterday = candidate - timedelta(days=1)
        scheduled_times = [
            yesterday.replace(hour=8),
            yesterday.replace(hour=14),
            yesterday.replace(hour=20),  # 3 posts yesterday (different day)
        ]

        # Should return True because no posts on candidate day
        assert scheduler._respects_daily_limit(candidate, scheduled_times) is True

    def test_schedule_content_success(self, scheduler, sample_queued_content):
        """Test successful content scheduling"""
        scheduler.queue.get_by_id = Mock(return_value=sample_queued_content)
        scheduler.queue.get_scheduled = Mock(return_value=[])
        scheduler.queue.update_status = Mock()

        schedule_time = scheduler.schedule_content("test-id-1")

        assert schedule_time is not None
        assert isinstance(schedule_time, datetime)
        assert schedule_time > datetime.now()
        scheduler.queue.update_status.assert_called_once()

    def test_schedule_content_not_found(self, scheduler):
        """Test scheduling when content not found"""
        scheduler.queue.get_by_id = Mock(return_value=None)

        schedule_time = scheduler.schedule_content("nonexistent-id")

        assert schedule_time is None

    def test_schedule_all_queued(self, scheduler):
        """Test scheduling all queued content"""
        queued_items = [
            QueuedContent(
                id=f"test-{i}",
                text=f"Test tweet {i}",
                topic=f"Topic {i}",
                platform="twitter",
                sentiment="philosophical",
                source="test",
                status="queued",
                created_at=datetime.now(),
                scheduled_for=None
            )
            for i in range(3)
        ]

        scheduler.queue.get_queued = Mock(return_value=queued_items)
        scheduler.queue.get_by_id = Mock(side_effect=queued_items)
        scheduler.queue.get_scheduled = Mock(return_value=[])
        scheduler.queue.update_status = Mock()

        results = scheduler.schedule_all_queued()

        assert len(results) == 3
        assert all('content_id' in r for r in results)
        assert all('scheduled_for' in r for r in results)
        assert all('topic' in r for r in results)

    def test_get_schedule_preview(self, scheduler):
        """Test getting schedule preview"""
        now = datetime.now()
        scheduled_items = [
            QueuedContent(
                id="test-1",
                text="Tweet about consciousness and awareness of truth in the system",
                topic="AI and consciousness",
                platform="twitter",
                sentiment="philosophical",
                source="test",
                status="scheduled",
                created_at=now,
                scheduled_for=now + timedelta(hours=2)
            ),
            QueuedContent(
                id="test-2",
                text="Short tweet",
                topic="Topic",
                platform="twitter",
                sentiment="sarcastic",
                source="test",
                status="scheduled",
                created_at=now,
                scheduled_for=now + timedelta(days=10)  # Beyond 7 days
            )
        ]

        scheduler.queue.get_scheduled = Mock(return_value=scheduled_items)

        preview = scheduler.get_schedule_preview(days=7)

        # Should only include first item (within 7 days)
        assert len(preview) == 1
        assert preview[0]['id'] == 'test-1'
        assert 'text_preview' in preview[0]
        assert len(preview[0]['text_preview']) <= 83  # 80 + '...'

    def test_reschedule_content(self, scheduler, sample_queued_content):
        """Test rescheduling content"""
        scheduler.queue.get_by_id = Mock(return_value=sample_queued_content)
        scheduler.queue.update_status = Mock()
        scheduler.queue.get_scheduled = Mock(return_value=[])

        new_time = scheduler.reschedule_content("test-id-1")

        assert new_time is not None
        # Should be called twice: once to set to queued, once to schedule
        assert scheduler.queue.update_status.call_count == 2

    def test_get_stats(self, scheduler):
        """Test getting scheduler statistics"""
        now = datetime.now()
        scheduled_items = [
            QueuedContent(
                id="test-1",
                text="Test",
                topic="Topic 1",
                platform="twitter",
                sentiment="philosophical",
                source="test",
                status="scheduled",
                created_at=now,
                scheduled_for=now + timedelta(hours=2)
            ),
            QueuedContent(
                id="test-2",
                text="Test",
                topic="Topic 2",
                platform="twitter",
                sentiment="sarcastic",
                source="test",
                status="scheduled",
                created_at=now,
                scheduled_for=now + timedelta(days=1)
            )
        ]

        queued_items = [
            QueuedContent(
                id="test-3",
                text="Test",
                topic="Topic 3",
                platform="twitter",
                sentiment="philosophical",
                source="test",
                status="queued",
                created_at=now,
                scheduled_for=None
            )
        ]

        scheduler.queue.get_scheduled = Mock(return_value=scheduled_items)
        scheduler.queue.get_queued = Mock(return_value=queued_items)

        stats = scheduler.get_stats()

        assert stats['total_scheduled'] == 2
        assert stats['queued_waiting'] == 1
        assert stats['next_post_time'] is not None
        assert stats['next_post_topic'] == "Topic 1"
        assert stats['posts_next_7_days'] == 2

    def test_is_valid_slot_all_checks(self, scheduler, sample_queued_content):
        """Test slot validation with all checks"""
        candidate = datetime.now().replace(hour=10, minute=0)
        scheduler.queue.get_scheduled = Mock(return_value=[])

        is_valid = scheduler._is_valid_slot(
            candidate,
            sample_queued_content,
            []
        )

        # Should pass all checks with empty schedule
        assert is_valid is True

    def test_calculate_next_slot_finds_valid_slot(self, scheduler, sample_queued_content):
        """Test calculating next slot finds valid time"""
        scheduler.queue.get_scheduled = Mock(return_value=[])

        next_slot = scheduler._calculate_next_slot(sample_queued_content)

        assert next_slot is not None
        assert next_slot > datetime.now()

    def test_calculate_next_slot_fallback(self, scheduler, sample_queued_content):
        """Test fallback when no slot found"""
        # Mock that all slots are invalid
        scheduler._is_valid_slot = Mock(return_value=False)
        scheduler.queue.get_scheduled = Mock(return_value=[])

        next_slot = scheduler._calculate_next_slot(sample_queued_content)

        # Should fallback to 7 days in future
        assert next_slot is not None
        days_diff = (next_slot - datetime.now()).days
        assert days_diff >= 6  # Allow some margin


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_schedule_all_function(self, mock_config):
        """Test schedule_all convenience function"""
        with patch.object(ContentScheduler, '_load_config', return_value=mock_config):
            with patch('src.content.scheduler.ContentQueue') as mock_queue_class:
                mock_queue = Mock()
                mock_queue.get_queued = Mock(return_value=[])
                mock_queue_class.return_value = mock_queue

                results = schedule_all()

                assert isinstance(results, list)

    def test_get_schedule_preview_function(self, mock_config):
        """Test get_schedule_preview convenience function"""
        with patch.object(ContentScheduler, '_load_config', return_value=mock_config):
            with patch('src.content.scheduler.ContentQueue') as mock_queue_class:
                mock_queue = Mock()
                mock_queue.get_scheduled = Mock(return_value=[])
                mock_queue_class.return_value = mock_queue

                preview = get_schedule_preview(days=7)

                assert isinstance(preview, list)
