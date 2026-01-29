"""
Tests for MetricsTracker

Tests the metrics tracking functionality including response rate calculation,
conversation metrics, and engagement tracking.
"""

import pytest
from datetime import datetime, timedelta
from src.analytics.metrics_tracker import MetricsTracker
from config.analytics_config import MetricType


class TestResponseRate:
    """Tests for response rate calculation and tracking"""

    def test_response_rate(self):
        """Test response rate calculation with various scenarios"""
        tracker = MetricsTracker()
        now = datetime.now()

        # Scenario 1: Perfect response rate (100%)
        # Record 10 messages, all responded to
        for i in range(10):
            tracker.track_message_sent(
                user_id="user1",
                timestamp=now - timedelta(minutes=10 - i),
            )
            tracker.track_message_responded(
                user_id="user1",
                timestamp=now - timedelta(minutes=10 - i),
            )

        response_rate = tracker.calculate_response_rate(user_id="user1")
        assert response_rate == 100.0, "Expected 100% response rate when all messages are responded to"

        # Scenario 2: 50% response rate
        # Record 10 more messages, only 5 responded to
        for i in range(10):
            tracker.track_message_sent(
                user_id="user2",
                timestamp=now - timedelta(minutes=10 - i),
            )
            if i < 5:
                tracker.track_message_responded(
                    user_id="user2",
                    timestamp=now - timedelta(minutes=10 - i),
                )

        response_rate = tracker.calculate_response_rate(user_id="user2")
        assert response_rate == 50.0, "Expected 50% response rate when half of messages are responded to"

        # Scenario 3: 0% response rate
        # Record 5 messages, none responded to
        for i in range(5):
            tracker.track_message_sent(
                user_id="user3",
                timestamp=now - timedelta(minutes=5 - i),
            )

        response_rate = tracker.calculate_response_rate(user_id="user3")
        assert response_rate == 0.0, "Expected 0% response rate when no messages are responded to"

        # Scenario 4: Overall response rate (all users)
        # Total: user1=10/10, user2=5/10, user3=0/5 = 15/25 = 60%
        overall_rate = tracker.calculate_response_rate()
        assert overall_rate == 60.0, "Expected 60% overall response rate"

        # Scenario 5: Filtered response rate by user (user3 has 0%)
        user3_rate = tracker.calculate_response_rate(user_id="user3")
        assert user3_rate == 0.0, "Expected 0% for user3 (no responses)"

    def test_response_rate_no_messages(self):
        """Test response rate calculation when no messages exist"""
        tracker = MetricsTracker()

        response_rate = tracker.calculate_response_rate()
        assert response_rate == 0.0, "Expected 0% when no messages tracked"

        response_rate = tracker.calculate_response_rate(user_id="nonexistent")
        assert response_rate == 0.0, "Expected 0% for nonexistent user"

    def test_response_rate_metric_recording(self):
        """Test that response rate can be recorded as a metric"""
        tracker = MetricsTracker()
        now = datetime.now()

        # Track some messages
        for i in range(10):
            tracker.track_message_sent(user_id="user1", timestamp=now)
            if i < 7:  # 70% response rate
                tracker.track_message_responded(user_id="user1", timestamp=now)

        # Calculate and record response rate
        response_rate = tracker.calculate_response_rate(user_id="user1")
        tracker.record_metric(
            metric_type=MetricType.RESPONSE_RATE,
            value=response_rate,
            user_id="user1",
            timestamp=now,
        )

        # Verify metric was recorded
        metrics = tracker.get_metrics(
            metric_type=MetricType.RESPONSE_RATE,
            user_id="user1",
        )
        assert len(metrics) == 1, "Expected one response rate metric"
        assert metrics[0].value == 70.0, "Expected 70% response rate metric"

    def test_response_rate_time_filtering(self):
        """Test response rate calculation with time range filters"""
        tracker = MetricsTracker()
        now = datetime.now()

        # Old messages (outside time range)
        for i in range(5):
            tracker.track_message_sent(
                user_id="user1",
                timestamp=now - timedelta(days=10),
            )

        # Recent messages (within time range) - 3/5 responded
        for i in range(5):
            tracker.track_message_sent(
                user_id="user1",
                timestamp=now - timedelta(hours=1),
            )
            if i < 3:
                tracker.track_message_responded(
                    user_id="user1",
                    timestamp=now - timedelta(hours=1),
                )

        # Calculate response rate for last 2 hours only
        recent_rate = tracker.calculate_response_rate(
            user_id="user1",
            start_time=now - timedelta(hours=2),
        )
        assert recent_rate == 60.0, "Expected 60% response rate for recent time range"

        # Calculate response rate for all time
        all_time_rate = tracker.calculate_response_rate(user_id="user1")
        assert all_time_rate == 30.0, "Expected 30% response rate for all time (3/10)"


class TestConversationMetrics:
    """Tests for conversation length and duration tracking"""

    def test_conversation_metrics(self):
        """Test conversation length and duration tracking"""
        tracker = MetricsTracker()
        now = datetime.now()

        # Scenario 1: Single conversation with 5 messages over 10 minutes
        conv_id_1 = "conv1"
        tracker.start_conversation(
            conversation_id=conv_id_1,
            user_id="user1",
            timestamp=now - timedelta(minutes=10),
        )

        # Add 4 more messages (total 5 including start)
        for i in range(4):
            tracker.add_conversation_message(
                conversation_id=conv_id_1,
                timestamp=now - timedelta(minutes=9 - i * 2),
            )

        # End conversation
        tracker.end_conversation(
            conversation_id=conv_id_1,
            timestamp=now,
        )

        # Get conversation stats
        conv_stats = tracker.get_conversation_stats(conversation_id=conv_id_1)
        assert conv_stats is not None, "Expected conversation stats to exist"
        assert conv_stats["message_count"] == 5, "Expected 5 messages in conversation"
        assert conv_stats["duration_seconds"] == 600, "Expected 10 minutes (600 seconds) duration"
        assert conv_stats["user_id"] == "user1", "Expected user_id to be user1"

        # Scenario 2: Multiple conversations for same user
        conv_id_2 = "conv2"
        tracker.start_conversation(
            conversation_id=conv_id_2,
            user_id="user1",
            timestamp=now - timedelta(hours=1),
        )
        tracker.add_conversation_message(conv_id_2)  # Total 2 messages (start + 1 add)
        tracker.end_conversation(
            conversation_id=conv_id_2,
            timestamp=now - timedelta(minutes=55),
        )

        # Calculate average conversation length for user1
        avg_length = tracker.calculate_average_conversation_length(user_id="user1")
        assert avg_length == 3.5, "Expected average of 3.5 messages ((5 + 2) / 2)"

        # Calculate average conversation duration for user1
        avg_duration = tracker.calculate_average_conversation_duration(user_id="user1")
        # conv1: 600 seconds, conv2: 300 seconds, average: 450 seconds
        assert avg_duration == 450.0, "Expected average duration of 450 seconds"

    def test_active_conversation(self):
        """Test tracking of active (not yet ended) conversations"""
        tracker = MetricsTracker()
        now = datetime.now()

        conv_id = "active_conv"
        tracker.start_conversation(
            conversation_id=conv_id,
            user_id="user1",
            timestamp=now - timedelta(minutes=5),
        )
        tracker.add_conversation_message(conv_id)
        tracker.add_conversation_message(conv_id)

        # Get stats for active conversation (not yet ended)
        conv_stats = tracker.get_conversation_stats(conversation_id=conv_id)
        assert conv_stats["message_count"] == 3, "Expected 3 messages"
        assert conv_stats["is_active"] is True, "Expected conversation to be active"
        # Duration should be calculated from start to now
        assert conv_stats["duration_seconds"] >= 300, "Expected at least 5 minutes duration"

        # Now end the conversation
        tracker.end_conversation(conv_id, timestamp=now)
        conv_stats = tracker.get_conversation_stats(conversation_id=conv_id)
        assert conv_stats["is_active"] is False, "Expected conversation to be inactive"

    def test_conversation_length_metric_recording(self):
        """Test that conversation length can be recorded as a metric"""
        tracker = MetricsTracker()
        now = datetime.now()

        # Create a conversation
        conv_id = "conv1"
        tracker.start_conversation(conv_id, user_id="user1", timestamp=now)
        for i in range(9):  # Total 10 messages including start
            tracker.add_conversation_message(conv_id)
        tracker.end_conversation(conv_id)

        # Get conversation stats and record as metric
        stats = tracker.get_conversation_stats(conv_id)
        tracker.record_metric(
            metric_type=MetricType.CONVERSATION_LENGTH,
            value=stats["message_count"],
            user_id="user1",
        )

        # Verify metric was recorded
        metrics = tracker.get_metrics(
            metric_type=MetricType.CONVERSATION_LENGTH,
            user_id="user1",
        )
        assert len(metrics) == 1, "Expected one conversation length metric"
        assert metrics[0].value == 10, "Expected 10 messages"

    def test_multiple_users_conversations(self):
        """Test conversation tracking across multiple users"""
        tracker = MetricsTracker()
        now = datetime.now()

        # User 1: 2 conversations, 5 and 3 messages
        tracker.start_conversation("conv1", user_id="user1")
        for i in range(4):
            tracker.add_conversation_message("conv1")
        tracker.end_conversation("conv1")

        tracker.start_conversation("conv2", user_id="user1")
        for i in range(2):
            tracker.add_conversation_message("conv2")
        tracker.end_conversation("conv2")

        # User 2: 1 conversation, 7 messages
        tracker.start_conversation("conv3", user_id="user2")
        for i in range(6):
            tracker.add_conversation_message("conv3")
        tracker.end_conversation("conv3")

        # Test user-specific averages
        avg_user1 = tracker.calculate_average_conversation_length(user_id="user1")
        assert avg_user1 == 4.0, "Expected average of 4 messages for user1 ((5 + 3) / 2)"

        avg_user2 = tracker.calculate_average_conversation_length(user_id="user2")
        assert avg_user2 == 7.0, "Expected average of 7 messages for user2"

        # Test overall average (all users)
        avg_all = tracker.calculate_average_conversation_length()
        assert avg_all == 5.0, "Expected overall average of 5 messages ((5 + 3 + 7) / 3)"

    def test_conversation_time_filtering(self):
        """Test conversation tracking with time range filters"""
        tracker = MetricsTracker()
        now = datetime.now()

        # Old conversation (outside time range)
        tracker.start_conversation(
            "old_conv",
            user_id="user1",
            timestamp=now - timedelta(days=10),
        )
        tracker.add_conversation_message("old_conv")
        tracker.end_conversation(
            "old_conv",
            timestamp=now - timedelta(days=10, minutes=-5),
        )

        # Recent conversation (within time range)
        tracker.start_conversation(
            "recent_conv",
            user_id="user1",
            timestamp=now - timedelta(hours=1),
        )
        for i in range(4):
            tracker.add_conversation_message("recent_conv")
        tracker.end_conversation("recent_conv")

        # Calculate average for last 2 hours only
        avg_recent = tracker.calculate_average_conversation_length(
            user_id="user1",
            start_time=now - timedelta(hours=2),
        )
        assert avg_recent == 5.0, "Expected only recent conversation (5 messages)"

        # Calculate average for all time
        avg_all = tracker.calculate_average_conversation_length(user_id="user1")
        assert avg_all == 3.5, "Expected average of all conversations ((2 + 5) / 2)"
