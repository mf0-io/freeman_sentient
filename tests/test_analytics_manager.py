"""
Tests for AnalyticsManager

Tests the analytics manager coordination of all analytics components including
time-series aggregation and trend detection.
"""

import pytest
from datetime import datetime, timedelta
from src.analytics.analytics_manager import AnalyticsManager
from config.analytics_config import MetricType, AggregationPeriod, TrendDirection


class TestTimeSeriesAggregation:
    """Tests for time-series aggregation functionality"""

    def test_time_series_aggregation(self):
        """Test aggregating metrics into time periods"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Record metrics over 30 days
        for day in range(30):
            timestamp = now - timedelta(days=29 - day)
            # Record 5 metrics per day with varying values
            for i in range(5):
                manager.record_metric(
                    metric_type=MetricType.ENGAGEMENT_SCORE,
                    value=50.0 + day,  # Increasing value over time
                    user_id="user1",
                    timestamp=timestamp + timedelta(hours=i),
                )

        # Test daily aggregation
        daily_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=30),
            end_time=now,
        )

        assert len(daily_trends) > 0, "Should have daily trend data"
        assert all(
            trend.period == AggregationPeriod.DAILY for trend in daily_trends
        ), "All trends should be daily"
        assert all(
            trend.metric_type == MetricType.ENGAGEMENT_SCORE for trend in daily_trends
        ), "All trends should be for engagement score"

        # Verify first day has correct average
        first_day_trend = daily_trends[0]
        assert (
            first_day_trend.average_value == 50.0
        ), "First day should have average of 50.0"
        assert len(first_day_trend.data_points) == 5, "First day should have 5 data points"

        # Test weekly aggregation
        weekly_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.WEEKLY,
            start_time=now - timedelta(days=30),
            end_time=now,
        )

        assert len(weekly_trends) > 0, "Should have weekly trend data"
        assert all(
            trend.period == AggregationPeriod.WEEKLY for trend in weekly_trends
        ), "All trends should be weekly"

        # Weekly trends should aggregate multiple days
        # Find a weekly bucket with substantial data (not a partial week)
        full_week_found = False
        for trend in weekly_trends:
            if len(trend.data_points) >= 5:
                full_week_found = True
                break
        assert full_week_found, "Should have at least one week with multiple days of data"

        # Test monthly aggregation
        monthly_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.MONTHLY,
            start_time=now - timedelta(days=30),
            end_time=now,
        )

        assert len(monthly_trends) > 0, "Should have monthly trend data"
        assert all(
            trend.period == AggregationPeriod.MONTHLY for trend in monthly_trends
        ), "All trends should be monthly"

        # Monthly trend should aggregate a substantial portion of data
        # Note: Due to calendar month boundaries, data may be split across 1-2 months
        total_monthly_data = sum(len(trend.data_points) for trend in monthly_trends)
        assert total_monthly_data >= 140, f"Monthly trends should aggregate most data (got {total_monthly_data})"

    def test_time_series_aggregation_user_filter(self):
        """Test aggregating metrics filtered by user"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Record metrics for multiple users
        for day in range(7):
            timestamp = now - timedelta(days=6 - day)
            for user_num in range(3):
                user_id = f"user{user_num}"
                manager.record_metric(
                    metric_type=MetricType.RESPONSE_RATE,
                    value=50.0 + user_num * 10,  # Different values per user
                    user_id=user_id,
                    timestamp=timestamp,
                )

        # Aggregate for specific user
        user1_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.RESPONSE_RATE,
            period=AggregationPeriod.DAILY,
            user_id="user1",
            start_time=now - timedelta(days=7),
            end_time=now,
        )

        assert len(user1_trends) == 7, "Should have 7 daily trends for user1"
        # Verify all trends are for user1 only (average should be 60.0)
        for trend in user1_trends:
            assert trend.average_value == 60.0, "User1 should have average of 60.0"
            assert len(trend.data_points) == 1, "Each day should have 1 data point for user1"

    def test_time_series_aggregation_empty_periods(self):
        """Test aggregation handles empty periods correctly"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Record metrics only on specific days (with gaps)
        manager.record_metric(
            metric_type=MetricType.CONVERSATION_LENGTH,
            value=10.0,
            timestamp=now - timedelta(days=10),
        )
        manager.record_metric(
            metric_type=MetricType.CONVERSATION_LENGTH,
            value=20.0,
            timestamp=now - timedelta(days=5),
        )
        manager.record_metric(
            metric_type=MetricType.CONVERSATION_LENGTH,
            value=30.0,
            timestamp=now,
        )

        # Aggregate over full period
        trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.CONVERSATION_LENGTH,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=11),
            end_time=now,
        )

        # Should only have trends for days with data
        assert len(trends) == 3, "Should have 3 daily trends (only days with data)"
        assert trends[0].average_value == 10.0, "First trend should be 10.0"
        assert trends[1].average_value == 20.0, "Second trend should be 20.0"
        assert trends[2].average_value == 30.0, "Third trend should be 30.0"

    def test_time_series_aggregation_no_data(self):
        """Test aggregation with no metrics"""
        manager = AnalyticsManager()
        now = datetime.now()

        trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=7),
            end_time=now,
        )

        assert len(trends) == 0, "Should have no trends when no metrics exist"

    def test_hourly_aggregation(self):
        """Test hourly aggregation for recent data"""
        manager = AnalyticsManager()
        # Use a fixed time at noon to avoid hour boundary issues
        now = datetime.now().replace(hour=12, minute=0, second=0, microsecond=0)

        # Record metrics over 24 hours (hourly)
        for hour in range(24):
            timestamp = now - timedelta(hours=23 - hour)
            for i in range(3):  # 3 metrics per hour (spaced 15 min apart to stay within hour)
                manager.record_metric(
                    metric_type=MetricType.INTERACTION_FREQUENCY,
                    value=10.0 + hour,
                    timestamp=timestamp + timedelta(minutes=i * 15),
                )

        # Aggregate by hour
        hourly_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.INTERACTION_FREQUENCY,
            period=AggregationPeriod.HOURLY,
            start_time=now - timedelta(hours=24),
            end_time=now,
        )

        assert len(hourly_trends) == 24, "Should have 24 hourly trends"
        assert all(
            trend.period == AggregationPeriod.HOURLY for trend in hourly_trends
        ), "All trends should be hourly"

        # Verify first hour
        first_hour = hourly_trends[0]
        assert first_hour.average_value == 10.0, "First hour should have average of 10.0"
        assert len(first_hour.data_points) == 3, "Each hour should have 3 data points"


class TestTrendDetection:
    """Tests for trend detection functionality"""

    def test_trend_detection(self):
        """Test detecting trends in time-series data"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Record metrics showing an improving trend
        # Days 0-9: values 50-59 (slowly increasing)
        for day in range(10):
            timestamp = now - timedelta(days=9 - day)
            manager.record_metric(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                value=50.0 + day,
                user_id="user1",
                timestamp=timestamp,
            )

        # Aggregate by daily periods
        daily_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=10),
            end_time=now,
        )

        # Detect overall trend pattern
        trend_analysis = manager.detect_trend_pattern(daily_trends)

        assert trend_analysis is not None, "Should detect a trend pattern"
        assert (
            trend_analysis["overall_direction"] == TrendDirection.IMPROVING
        ), "Should detect improving trend"
        assert (
            trend_analysis["confidence"] > 0.7
        ), "Should have high confidence in trend detection"
        assert (
            "start_value" in trend_analysis
        ), "Should include start value in analysis"
        assert "end_value" in trend_analysis, "Should include end value in analysis"
        assert (
            "total_change" in trend_analysis
        ), "Should include total change in analysis"
        assert (
            "average_change_per_period" in trend_analysis
        ), "Should include average change per period"

    def test_trend_detection_declining(self):
        """Test detecting declining trends"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Record metrics showing a declining trend
        for day in range(10):
            timestamp = now - timedelta(days=9 - day)
            manager.record_metric(
                metric_type=MetricType.RESPONSE_RATE,
                value=90.0 - day * 2,  # Declining from 90 to 72
                timestamp=timestamp,
            )

        daily_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.RESPONSE_RATE,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=10),
            end_time=now,
        )

        trend_analysis = manager.detect_trend_pattern(daily_trends)

        assert (
            trend_analysis["overall_direction"] == TrendDirection.DECLINING
        ), "Should detect declining trend"
        assert trend_analysis["total_change"] < 0, "Total change should be negative"

    def test_trend_detection_stable(self):
        """Test detecting stable trends"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Record metrics showing a stable trend (minimal variation)
        for day in range(10):
            timestamp = now - timedelta(days=9 - day)
            # Value varies slightly around 50 (within stable range)
            value = 50.0 + (day % 3 - 1)  # Values: 49, 50, 51 repeating
            manager.record_metric(
                metric_type=MetricType.SENTIMENT_SCORE,
                value=value,
                timestamp=timestamp,
            )

        daily_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.SENTIMENT_SCORE,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=10),
            end_time=now,
        )

        trend_analysis = manager.detect_trend_pattern(daily_trends)

        assert (
            trend_analysis["overall_direction"] == TrendDirection.STABLE
        ), "Should detect stable trend"
        assert (
            abs(trend_analysis["total_change_percentage"]) < 10
        ), "Total change percentage should be small for stable trend"

    def test_trend_detection_insufficient_data(self):
        """Test trend detection with insufficient data points"""
        manager = AnalyticsManager()
        now = datetime.now()

        # Record only 2 metrics (below minimum threshold)
        manager.record_metric(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            value=50.0,
            timestamp=now - timedelta(days=1),
        )
        manager.record_metric(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            value=55.0,
            timestamp=now,
        )

        daily_trends = manager.aggregate_metrics_by_period(
            metric_type=MetricType.ENGAGEMENT_SCORE,
            period=AggregationPeriod.DAILY,
            start_time=now - timedelta(days=2),
            end_time=now,
        )

        trend_analysis = manager.detect_trend_pattern(daily_trends)

        # Should either return None or indicate low confidence
        if trend_analysis is not None:
            assert (
                trend_analysis["confidence"] < 0.5
            ), "Should have low confidence with insufficient data"
        # Alternatively, it's acceptable to return None for insufficient data

    def test_trend_detection_empty_data(self):
        """Test trend detection with no data"""
        manager = AnalyticsManager()

        trend_analysis = manager.detect_trend_pattern([])

        assert trend_analysis is None, "Should return None for empty data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
