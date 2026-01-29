"""
Integration Tests for Analytics System

Tests the integration and coordination between all analytics components:
- MetricsTracker, SentimentAnalyzer, AnalyticsManager, and AnalyticsExporter
- End-to-end workflows from data collection to export
- Real-world scenarios spanning multiple components
"""

import pytest
import json
import tempfile
import os
from datetime import datetime, timedelta
from src.analytics.analytics_manager import AnalyticsManager
from src.analytics.analytics_exporter import AnalyticsExporter
from config.analytics_config import (
    MetricType,
    SentimentCategory,
    AggregationPeriod,
    TrendDirection,
)


class TestAnalyticsWorkflowIntegration:
    """Tests for end-to-end analytics workflows"""

    def test_complete_analytics_workflow(self):
        """Test complete workflow: track -> analyze -> aggregate -> export"""
        manager = AnalyticsManager()
        exporter = AnalyticsExporter()
        now = datetime.now()

        # Step 1: Track user interactions over a week
        for day in range(7):
            timestamp = now - timedelta(days=6 - day)
            user_id = f"user{day % 3}"  # 3 different users

            # Track messages
            manager.track_message_sent(user_id=user_id, timestamp=timestamp)
            if day % 2 == 0:  # 50% response rate
                manager.track_message_responded(user_id=user_id, timestamp=timestamp)

            # Track conversation
            conv_id = f"conv_{day}"
            manager.start_conversation(
                conversation_id=conv_id,
                user_id=user_id,
                timestamp=timestamp,
            )
            for i in range(day + 2):  # Increasing conversation length
                manager.add_conversation_message(conv_id, timestamp=timestamp)
            manager.end_conversation(conv_id, timestamp=timestamp + timedelta(minutes=10))

            # Analyze sentiment
            message_texts = [
                "This is amazing!",
                "I love this!",
                "Great work!",
            ]
            sentiment_result = manager.analyze_conversation_sentiment(
                messages=message_texts,
                conversation_id=conv_id,
                user_id=user_id,
                timestamp=timestamp,
            )

            # Record engagement metric
            manager.record_metric(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                value=70.0 + day * 5,
                user_id=user_id,
                timestamp=timestamp,
            )

        # Step 2: Calculate response rates and conversation metrics
        response_rate = manager.calculate_response_rate()
        assert response_rate > 0, "Should have calculated response rate"

        avg_conv_length = manager.calculate_average_conversation_length()
        assert avg_conv_length > 0, "Should have calculated average conversation length"

        # Step 3: Aggregate trends
        daily_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=7),
            end_time=now,
        )
        assert len(daily_trends) > 0, "Should have aggregated daily trends"

        # Step 4: Detect trend patterns
        trend_analysis = manager.detect_trend_pattern(daily_trends)
        assert trend_analysis is not None, "Should have detected trend pattern"
        assert (
            trend_analysis["overall_direction"] == TrendDirection.IMPROVING
        ), "Should detect improving trend"

        # Step 5: Export analytics data
        metrics = manager.get_metrics(metric_type=MetricType.ENGAGEMENT_SCORE)
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "analytics.json")
            exporter.export_metrics_to_json(metrics, output_file=json_path)
            assert os.path.exists(json_path), "Should have created JSON export"

            # Verify exported data is valid JSON
            with open(json_path, "r") as f:
                data = json.load(f)
                assert len(data) > 0, "Should have exported metrics"

    def test_multi_user_analytics_workflow(self):
        """Test analytics workflow with multiple users tracked separately"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Track interactions for 3 different users with different patterns
        users = [
            {"id": "user1", "response_rate": 1.0, "sentiment": "positive"},
            {"id": "user2", "response_rate": 0.5, "sentiment": "neutral"},
            {"id": "user3", "response_rate": 0.0, "sentiment": "negative"},
        ]

        for user in users:
            user_id = user["id"]

            # Track messages with different response rates
            for i in range(10):
                manager.track_message_sent(
                    user_id=user_id, timestamp=now - timedelta(minutes=10 - i)
                )
                if i < int(10 * user["response_rate"]):
                    manager.track_message_responded(
                        user_id=user_id, timestamp=now - timedelta(minutes=10 - i)
                    )

            # Analyze sentiment based on user type
            if user["sentiment"] == "positive":
                texts = ["This is great!", "I love it!", "Amazing work!"]
            elif user["sentiment"] == "neutral":
                texts = ["It's okay.", "Not bad.", "Fine."]
            else:  # negative
                texts = ["This is bad.", "Disappointed.", "Not good."]

            sentiment_result = manager.analyze_conversation_sentiment(
                messages=texts,
                user_id=user_id,
                timestamp=now,
            )

            # Verify sentiment matches expected category
            if user["sentiment"] == "positive":
                assert sentiment_result.score > 0, f"Expected positive sentiment for {user_id}"
            elif user["sentiment"] == "negative":
                assert sentiment_result.score < 0, f"Expected negative sentiment for {user_id}"

        # Verify per-user response rates
        user1_rate = manager.calculate_response_rate(user_id="user1")
        assert user1_rate == 100.0, "User1 should have 100% response rate"

        user2_rate = manager.calculate_response_rate(user_id="user2")
        assert user2_rate == 50.0, "User2 should have 50% response rate"

        user3_rate = manager.calculate_response_rate(user_id="user3")
        assert user3_rate == 0.0, "User3 should have 0% response rate"

        # Verify overall response rate
        overall_rate = manager.calculate_response_rate()
        assert overall_rate == 50.0, "Overall response rate should be 50%"

    def test_trend_detection_and_export_workflow(self):
        """Test workflow: collect metrics -> detect trends -> export trend data"""
        manager = AnalyticsManager()
        exporter = AnalyticsExporter()
        now = datetime.now()

        # Scenario 1: Improving engagement trend
        for day in range(14):
            timestamp = now - timedelta(days=13 - day)
            # Value increases each day
            value = 40.0 + day * 3
            manager.record_metric(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                value=value,
                user_id="user1",
                timestamp=timestamp,
            )

        # Aggregate and detect trend
        daily_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.DAILY,
            user_id="user1",
            start_time=now - timedelta(days=14),
            end_time=now,
        )

        trend_analysis = manager.detect_trend_pattern(daily_trends)
        assert (
            trend_analysis["overall_direction"] == TrendDirection.IMPROVING
        ), "Should detect improving trend"
        assert trend_analysis["confidence"] > 0.8, "Should have high confidence"

        # Export trend data
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = os.path.join(tmpdir, "trends.json")
            exporter.export_trends_to_json(daily_trends, output_file=json_path)
            assert os.path.exists(json_path), "Should have created trend export"

            # Verify exported trend data
            with open(json_path, "r") as f:
                data = json.load(f)
                assert len(data) == 14, "Should have 14 daily trends"
                assert all(
                    "average_value" in trend for trend in data
                ), "Each trend should have average_value"

    def test_conversation_sentiment_correlation_workflow(self):
        """Test workflow correlating conversation metrics with sentiment"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Create 5 conversations with varying sentiment and length
        conversations = [
            {
                "id": "conv1",
                "messages": ["Great!", "Love it!", "Amazing!"],
                "length": 5,
                "user": "user1",
            },
            {
                "id": "conv2",
                "messages": ["Okay.", "It's fine.", "Not bad."],
                "length": 3,
                "user": "user2",
            },
            {
                "id": "conv3",
                "messages": ["Terrible!", "Bad!", "Disappointed!"],
                "length": 2,
                "user": "user3",
            },
            {
                "id": "conv4",
                "messages": ["Excellent!", "Perfect!", "Superb!"],
                "length": 8,
                "user": "user1",
            },
            {
                "id": "conv5",
                "messages": ["Poor.", "Not good.", "Awful."],
                "length": 4,
                "user": "user3",
            },
        ]

        sentiment_by_length = {}

        for conv in conversations:
            conv_id = conv["id"]
            user_id = conv["user"]
            timestamp = now - timedelta(hours=len(conversations) - conversations.index(conv))

            # Track conversation
            manager.start_conversation(
                conversation_id=conv_id,
                user_id=user_id,
                timestamp=timestamp,
            )
            for i in range(conv["length"] - 1):
                manager.add_conversation_message(conv_id, timestamp=timestamp)
            manager.end_conversation(conv_id, timestamp=timestamp + timedelta(minutes=5))

            # Analyze sentiment
            sentiment_result = manager.analyze_conversation_sentiment(
                messages=conv["messages"],
                conversation_id=conv_id,
                user_id=user_id,
                timestamp=timestamp,
            )

            # Track correlation
            sentiment_by_length[conv["length"]] = sentiment_result.score

            # Record as metrics
            manager.record_metric(
                metric_type=MetricType.CONVERSATION_LENGTH,
                value=conv["length"],
                user_id=user_id,
                timestamp=timestamp,
            )
            manager.record_metric(
                metric_type=MetricType.SENTIMENT_SCORE,
                value=sentiment_result.score,
                user_id=user_id,
                timestamp=timestamp,
            )

        # Verify conversation metrics
        avg_length = manager.calculate_average_conversation_length()
        assert avg_length > 0, "Should have average conversation length"

        # Verify metrics were recorded
        length_metrics = manager.get_metrics(metric_type=MetricType.CONVERSATION_LENGTH)
        assert len(length_metrics) == 5, "Should have 5 conversation length metrics"

        sentiment_metrics = manager.get_metrics(metric_type=MetricType.SENTIMENT_SCORE)
        assert len(sentiment_metrics) == 5, "Should have 5 sentiment score metrics"

    def test_full_analytics_export_workflow(self):
        """Test exporting complete analytics including all data types"""
        manager = AnalyticsManager()
        exporter = AnalyticsExporter()
        now = datetime.now()

        # Generate diverse analytics data
        for i in range(10):
            timestamp = now - timedelta(hours=10 - i)

            # Track various metrics
            manager.record_metric(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                value=60.0 + i * 2,
                user_id=f"user{i % 3}",
                timestamp=timestamp,
            )

            manager.record_metric(
                metric_type=MetricType.INTERACTION_FREQUENCY,
                value=5.0 + i,
                user_id=f"user{i % 3}",
                timestamp=timestamp,
            )

            # Analyze sentiment
            manager.analyze_sentiment(
                text="This is a test message.",
                user_id=f"user{i % 3}",
                timestamp=timestamp,
            )

        # Get all data
        engagement_metrics = manager.get_metrics(metric_type=MetricType.ENGAGEMENT_SCORE)
        frequency_metrics = manager.get_metrics(metric_type=MetricType.INTERACTION_FREQUENCY)

        # Aggregate trends
        hourly_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.HOURLY,
            start_time=now - timedelta(hours=11),
            end_time=now,
        )

        # Export everything
        with tempfile.TemporaryDirectory() as tmpdir:
            # Export metrics in JSON
            json_path = os.path.join(tmpdir, "metrics.json")
            exporter.export_metrics_to_json(engagement_metrics, output_file=json_path)
            assert os.path.exists(json_path), "Should have created metrics JSON"

            # Export metrics in CSV
            csv_path = os.path.join(tmpdir, "metrics.csv")
            exporter.export_metrics_to_csv(engagement_metrics, output_file=csv_path)
            assert os.path.exists(csv_path), "Should have created metrics CSV"

            # Export trends
            trends_path = os.path.join(tmpdir, "trends.json")
            exporter.export_trends_to_json(hourly_trends, output_file=trends_path)
            assert os.path.exists(trends_path), "Should have created trends export"

            # Verify all files have content
            assert os.path.getsize(json_path) > 0, "Metrics JSON should not be empty"
            assert os.path.getsize(csv_path) > 0, "Metrics CSV should not be empty"
            assert os.path.getsize(trends_path) > 0, "Trends JSON should not be empty"


class TestAnalyticsComponentIntegration:
    """Tests for integration between specific analytics components"""

    def test_metrics_tracker_sentiment_analyzer_integration(self):
        """Test integration between MetricsTracker and SentimentAnalyzer via AnalyticsManager"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Track conversation with messages
        conv_id = "integration_conv"
        manager.start_conversation(conv_id, user_id="user1", timestamp=now)
        manager.add_conversation_message(conv_id, timestamp=now)
        manager.add_conversation_message(conv_id, timestamp=now)
        manager.end_conversation(conv_id, timestamp=now + timedelta(minutes=5))

        # Get conversation stats
        conv_stats = manager.get_conversation_stats(conv_id)
        assert conv_stats is not None, "Should have conversation stats"
        assert conv_stats["message_count"] == 3, "Should have 3 messages"

        # Analyze sentiment for the conversation
        messages = ["Great conversation!", "I learned a lot.", "Thank you!"]
        sentiment = manager.analyze_conversation_sentiment(
            messages=messages,
            conversation_id=conv_id,
            user_id="user1",
            timestamp=now,
        )

        assert sentiment.score > 0, "Should have positive sentiment"
        assert sentiment.metadata["conversation_id"] == conv_id, "Should include conversation ID"

        # Record both metrics
        manager.record_metric(
            metric_type=MetricType.CONVERSATION_LENGTH,
            value=conv_stats["message_count"],
            user_id="user1",
            timestamp=now,
        )
        manager.record_metric(
            metric_type=MetricType.SENTIMENT_SCORE,
            value=sentiment.score,
            user_id="user1",
            timestamp=now,
        )

        # Verify both metrics exist
        length_metrics = manager.get_metrics(metric_type=MetricType.CONVERSATION_LENGTH)
        sentiment_metrics = manager.get_metrics(metric_type=MetricType.SENTIMENT_SCORE)

        assert len(length_metrics) == 1, "Should have 1 conversation length metric"
        assert len(sentiment_metrics) == 1, "Should have 1 sentiment metric"

    def test_manager_exporter_integration(self):
        """Test integration between AnalyticsManager and AnalyticsExporter"""
        manager = AnalyticsManager()
        exporter = AnalyticsExporter()
        now = datetime.now()

        # Generate analytics data through manager
        for i in range(5):
            manager.record_metric(
                metric_type=MetricType.RESPONSE_RATE,
                value=80.0 + i,
                user_id="user1",
                timestamp=now - timedelta(days=4 - i),
            )

        # Get metrics from manager
        metrics = manager.get_metrics(metric_type=MetricType.RESPONSE_RATE)
        assert len(metrics) == 5, "Should have 5 metrics"

        # Export via exporter
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "response_rate.json")
            exporter.export_metrics_to_json(
                metrics=metrics,
                output_file=output_path,
                include_metadata=True,
            )

            # Verify export
            assert os.path.exists(output_path), "Should have created export file"

            with open(output_path, "r") as f:
                data = json.load(f)
                assert len(data) == 5, "Should have exported 5 metrics"
                assert all(
                    m["metric_type"] == "response_rate" for m in data
                ), "All metrics should be response_rate"

    def test_aggregation_trend_detection_integration(self):
        """Test integration between aggregation and trend detection"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Generate metrics with clear improving trend
        for week in range(4):
            for day in range(7):
                timestamp = now - timedelta(days=(3 - week) * 7 + (6 - day))
                # Value increases each week
                value = 50.0 + week * 10
                manager.record_metric(
                    metric_type=MetricType.ENGAGEMENT_SCORE,
                    value=value,
                    timestamp=timestamp,
                )

        # Aggregate by week
        weekly_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.WEEKLY,
            start_time=now - timedelta(days=28),
            end_time=now,
        )

        # Note: Due to calendar week boundaries, 28 days may span 4-5 weekly buckets
        assert len(weekly_trends) >= 4, "Should have at least 4 weekly trends"

        # Detect trend from aggregated data
        trend_analysis = manager.detect_trend_pattern(weekly_trends)

        assert trend_analysis is not None, "Should detect trend"
        assert (
            trend_analysis["overall_direction"] == TrendDirection.IMPROVING
        ), "Should detect improving trend"
        assert trend_analysis["num_periods"] == len(weekly_trends), f"Should analyze {len(weekly_trends)} periods"

        # Verify trend consistency
        assert (
            trend_analysis["consistency_score"] > 0.8
        ), "Should have high consistency for steady improvement"

    def test_serialization_deserialization_integration(self):
        """Test full serialization and deserialization workflow"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Generate diverse data
        manager.record_metric(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            value=75.0,
            user_id="user1",
            timestamp=now,
        )

        manager.track_message_sent(user_id="user1", timestamp=now)
        manager.track_message_responded(user_id="user1", timestamp=now)

        manager.start_conversation("conv1", user_id="user1", timestamp=now)
        manager.add_conversation_message("conv1", timestamp=now)
        manager.end_conversation("conv1", timestamp=now + timedelta(minutes=5))

        # Serialize to dict
        data = manager.to_dict()

        assert "metrics_tracker" in data, "Should include metrics tracker data"
        assert "sentiment_analyzer" in data, "Should include sentiment analyzer data"

        # Create new manager from serialized data
        restored_manager = AnalyticsManager.from_dict(data)

        # Verify data was restored correctly
        metrics = restored_manager.get_metrics(metric_type=MetricType.ENGAGEMENT_SCORE)
        assert len(metrics) == 1, "Should have restored 1 metric"
        assert metrics[0].value == 75.0, "Should have correct metric value"

        response_rate = restored_manager.calculate_response_rate(user_id="user1")
        assert response_rate == 100.0, "Should have restored response rate tracking"

        conv_stats = restored_manager.get_conversation_stats("conv1")
        assert conv_stats is not None, "Should have restored conversation"
        assert conv_stats["message_count"] == 2, "Should have correct message count"


class TestRealWorldScenarios:
    """Tests simulating real-world analytics scenarios"""

    def test_daily_analytics_report_scenario(self):
        """Test scenario: generating a daily analytics report"""
        manager = AnalyticsManager()
        exporter = AnalyticsExporter()
        now = datetime.now()

        # Simulate a day's worth of interactions
        interactions = [
            {"hour": 9, "messages": 5, "responded": 4, "sentiment": "positive"},
            {"hour": 10, "messages": 8, "responded": 7, "sentiment": "positive"},
            {"hour": 11, "messages": 6, "responded": 5, "sentiment": "neutral"},
            {"hour": 14, "messages": 10, "responded": 9, "sentiment": "positive"},
            {"hour": 15, "messages": 7, "responded": 5, "sentiment": "neutral"},
            {"hour": 16, "messages": 4, "responded": 2, "sentiment": "negative"},
        ]

        for interaction in interactions:
            hour = interaction["hour"]
            timestamp = now.replace(hour=hour, minute=0, second=0, microsecond=0)

            # Track messages
            for i in range(interaction["messages"]):
                manager.track_message_sent(user_id="daily_user", timestamp=timestamp)
                if i < interaction["responded"]:
                    manager.track_message_responded(
                        user_id="daily_user", timestamp=timestamp
                    )

            # Analyze sentiment
            if interaction["sentiment"] == "positive":
                text = "Great interaction!"
            elif interaction["sentiment"] == "neutral":
                text = "Okay interaction."
            else:
                text = "Poor interaction."

            sentiment = manager.analyze_sentiment(
                text=text, user_id="daily_user", timestamp=timestamp
            )

            # Record engagement metric
            engagement = (interaction["responded"] / interaction["messages"]) * 100
            manager.record_metric(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                value=engagement,
                user_id="daily_user",
                timestamp=timestamp,
            )

        # Generate report data
        daily_response_rate = manager.calculate_response_rate(
            user_id="daily_user",
            start_time=now.replace(hour=0, minute=0, second=0, microsecond=0),
            end_time=now.replace(hour=23, minute=59, second=59, microsecond=999999),
        )

        assert 70 <= daily_response_rate <= 85, "Should have good response rate for the day"

        # Export daily report
        metrics = manager.get_metrics(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            user_id="daily_user",
            start_time=now.replace(hour=0, minute=0, second=0, microsecond=0),
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = os.path.join(tmpdir, "daily_report.json")
            exporter.export_metrics_to_json(metrics, output_file=report_path)
            assert os.path.exists(report_path), "Should have created daily report"

    def test_user_engagement_tracking_scenario(self):
        """Test scenario: tracking user engagement over multiple weeks"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Track 3 users over 3 weeks
        users = ["power_user", "regular_user", "occasional_user"]
        weekly_interactions = [21, 7, 2]  # Interactions per week

        for week in range(3):
            for user_idx, user_id in enumerate(users):
                interactions_this_week = weekly_interactions[user_idx]

                for interaction in range(interactions_this_week):
                    timestamp = now - timedelta(
                        weeks=2 - week,
                        days=interaction % 7,
                        hours=interaction % 24,
                    )

                    # Track conversation
                    conv_id = f"{user_id}_w{week}_i{interaction}"
                    manager.start_conversation(
                        conv_id, user_id=user_id, timestamp=timestamp
                    )
                    manager.add_conversation_message(conv_id, timestamp=timestamp)
                    manager.end_conversation(
                        conv_id, timestamp=timestamp + timedelta(minutes=5)
                    )

                    # Record interaction frequency
                    manager.record_metric(
                        metric_type=MetricType.INTERACTION_FREQUENCY,
                        value=1.0,
                        user_id=user_id,
                        timestamp=timestamp,
                    )

        # Analyze engagement patterns
        power_user_metrics = manager.get_metrics(
            metric_type=MetricType.INTERACTION_FREQUENCY,
            user_id="power_user",
        )
        assert (
            len(power_user_metrics) == 63
        ), "Power user should have 63 interactions (21 * 3 weeks)"

        regular_user_metrics = manager.get_metrics(
            metric_type=MetricType.INTERACTION_FREQUENCY,
            user_id="regular_user",
        )
        assert (
            len(regular_user_metrics) == 21
        ), "Regular user should have 21 interactions (7 * 3 weeks)"

        occasional_user_metrics = manager.get_metrics(
            metric_type=MetricType.INTERACTION_FREQUENCY,
            user_id="occasional_user",
        )
        assert (
            len(occasional_user_metrics) == 6
        ), "Occasional user should have 6 interactions (2 * 3 weeks)"

        # Verify conversation tracking
        power_user_conv_avg = manager.calculate_average_conversation_length(
            user_id="power_user"
        )
        assert power_user_conv_avg > 0, "Should have conversation data for power user"


class TestMemorySystemHooks:
    """Tests for memory system integration hooks"""

    def test_memory_hooks(self):
        """Test that AnalyticsManager can be integrated with a memory system via hooks"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Test 1: Register hooks for automatic analytics collection
        events_triggered = []

        def on_message_event(event_type, **kwargs):
            events_triggered.append({"event": event_type, **kwargs})

        # Register hooks
        manager.register_hook("message_sent", on_message_event)
        manager.register_hook("message_responded", on_message_event)

        # Test 2: Trigger hooks from memory system events
        # Simulate memory system calling hooks
        manager.on_message_sent(user_id="user1", timestamp=now)
        manager.on_message_responded(user_id="user1", timestamp=now)

        # Verify hooks were called
        assert len(events_triggered) == 2, "Should have triggered 2 hook events"
        assert events_triggered[0]["event"] == "message_sent", "First event should be message_sent"
        assert events_triggered[1]["event"] == "message_responded", "Second event should be message_responded"

        # Verify analytics were automatically tracked
        response_rate = manager.calculate_response_rate(user_id="user1")
        assert response_rate == 100.0, "Should have tracked message stats via hooks"

        # Test 3: Conversation hooks
        manager.on_conversation_started(
            conversation_id="conv1",
            user_id="user1",
            timestamp=now,
        )
        manager.on_conversation_message_added(conversation_id="conv1", timestamp=now)
        manager.on_conversation_ended(conversation_id="conv1", timestamp=now + timedelta(minutes=5))

        conv_stats = manager.get_conversation_stats("conv1")
        assert conv_stats is not None, "Should have tracked conversation via hooks"
        assert conv_stats["message_count"] == 2, "Should have correct message count"

        # Test 4: Sentiment analysis hooks
        sentiment_result = manager.on_sentiment_analyzed(
            text="This is great!",
            user_id="user1",
            timestamp=now,
        )
        assert sentiment_result is not None, "Should return sentiment result"
        assert sentiment_result.score > 0, "Should have positive sentiment"

        # Test 5: Metric recording hooks
        manager.on_metric_recorded(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            value=85.0,
            user_id="user1",
            timestamp=now,
        )

        metrics = manager.get_metrics(metric_type=MetricType.ENGAGEMENT_SCORE, user_id="user1")
        assert len(metrics) == 1, "Should have recorded metric via hook"
        assert metrics[0].value == 85.0, "Should have correct metric value"

        # Test 6: Verify hooks can be unregistered
        manager.unregister_hook("message_sent", on_message_event)
        events_before = len(events_triggered)
        manager.on_message_sent(user_id="user2", timestamp=now)
        assert len(events_triggered) == events_before, "Hook should not be called after unregister"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
