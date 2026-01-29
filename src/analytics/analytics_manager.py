"""
Analytics Manager

Coordinates all analytics components and provides a unified interface for
tracking metrics, analyzing sentiment, and managing analytics data.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from collections import defaultdict

from .metrics_tracker import MetricsTracker
from .sentiment_analyzer import SentimentAnalyzer
from .models import MetricEntry, SentimentResult, TrendData
from config.analytics_config import (
    MetricType,
    SentimentCategory,
    AggregationPeriod,
    TrendDirection,
    classify_trend,
)


class AnalyticsManager:
    """
    Manages and coordinates all analytics components.

    Provides a unified interface for tracking engagement metrics,
    analyzing sentiment, and accessing analytics data. Acts as the
    main entry point for the analytics system.

    Attributes:
        metrics_tracker: Tracks engagement metrics
        sentiment_analyzer: Analyzes sentiment of text and conversations
    """

    def __init__(self):
        """Initialize the AnalyticsManager with all analytics components"""
        self.metrics_tracker = MetricsTracker()
        self.sentiment_analyzer = SentimentAnalyzer()
        self._hooks: Dict[str, List[callable]] = defaultdict(list)

    # Metrics tracking methods
    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> MetricEntry:
        """
        Record a new metric entry.

        Args:
            metric_type: Type of metric being recorded
            value: Numeric value of the metric
            user_id: Optional user ID if metric is user-specific
            metadata: Additional context and data
            timestamp: Optional timestamp (defaults to now)

        Returns:
            The created MetricEntry
        """
        return self.metrics_tracker.record_metric(
            metric_type=metric_type,
            value=value,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )

    def get_metrics(
        self,
        metric_type: Optional[MetricType] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[MetricEntry]:
        """
        Retrieve metrics with optional filtering.

        Args:
            metric_type: Filter by specific metric type (None for all types)
            user_id: Filter by specific user ID (None for all users)
            start_time: Filter metrics after this time (None for no lower bound)
            end_time: Filter metrics before this time (None for no upper bound)

        Returns:
            List of matching MetricEntry objects
        """
        return self.metrics_tracker.get_metrics(
            metric_type=metric_type,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )

    # Response rate tracking
    def track_message_sent(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Track a message that was sent.

        Args:
            user_id: Optional user ID associated with the message
            metadata: Additional context about the message
            timestamp: Optional timestamp (defaults to now)
        """
        self.metrics_tracker.track_message_sent(
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )

    def track_message_responded(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Track a message that received a response.

        Args:
            user_id: Optional user ID associated with the message
            metadata: Additional context about the response
            timestamp: Optional timestamp (defaults to now)
        """
        self.metrics_tracker.track_message_responded(
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )

    def calculate_response_rate(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate the response rate as a percentage.

        Args:
            user_id: Optional filter by specific user ID (None for all users)
            start_time: Optional filter messages after this time
            end_time: Optional filter messages before this time

        Returns:
            Response rate as a percentage (0.0 to 100.0)
        """
        return self.metrics_tracker.calculate_response_rate(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )

    # Conversation tracking
    def start_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Start tracking a new conversation.

        Args:
            conversation_id: Unique identifier for the conversation
            user_id: Optional user ID associated with the conversation
            metadata: Additional context about the conversation
            timestamp: Optional timestamp (defaults to now)
        """
        self.metrics_tracker.start_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )

    def add_conversation_message(
        self,
        conversation_id: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add a message to an existing conversation.

        Args:
            conversation_id: The conversation to add a message to
            timestamp: Optional timestamp of the message (defaults to now)
        """
        self.metrics_tracker.add_conversation_message(
            conversation_id=conversation_id,
            timestamp=timestamp,
        )

    def end_conversation(
        self,
        conversation_id: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Mark a conversation as ended.

        Args:
            conversation_id: The conversation to end
            timestamp: Optional timestamp (defaults to now)
        """
        self.metrics_tracker.end_conversation(
            conversation_id=conversation_id,
            timestamp=timestamp,
        )

    def get_conversation_stats(
        self,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific conversation.

        Args:
            conversation_id: The conversation to get stats for

        Returns:
            Dictionary with conversation statistics or None if not found
        """
        return self.metrics_tracker.get_conversation_stats(conversation_id)

    def calculate_average_conversation_length(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate the average conversation length in messages.

        Args:
            user_id: Optional filter by specific user ID
            start_time: Optional filter conversations after this time
            end_time: Optional filter conversations before this time

        Returns:
            Average number of messages per conversation or 0.0 if no conversations
        """
        return self.metrics_tracker.calculate_average_conversation_length(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )

    def calculate_average_conversation_duration(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate the average conversation duration in seconds.

        Args:
            user_id: Optional filter by specific user ID
            start_time: Optional filter conversations after this time
            end_time: Optional filter conversations before this time

        Returns:
            Average duration in seconds or 0.0 if no conversations
        """
        return self.metrics_tracker.calculate_average_conversation_duration(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )

    # Sentiment analysis methods
    def analyze_sentiment(
        self,
        text: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> SentimentResult:
        """
        Analyze the sentiment of a text.

        Args:
            text: The text to analyze
            user_id: Optional user ID for user-specific sentiment tracking
            metadata: Additional context about the text
            timestamp: Optional timestamp (defaults to now)

        Returns:
            SentimentResult with score, category, and confidence
        """
        return self.sentiment_analyzer.analyze(
            text=text,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )

    def analyze_conversation_sentiment(
        self,
        messages: List[str],
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> SentimentResult:
        """
        Analyze sentiment for an entire conversation.

        Args:
            messages: List of message texts in the conversation
            conversation_id: Optional conversation identifier
            user_id: Optional user ID for the conversation
            metadata: Additional context about the conversation
            timestamp: Optional timestamp (defaults to now)

        Returns:
            SentimentResult with aggregated conversation sentiment
        """
        return self.sentiment_analyzer.analyze_conversation(
            messages=messages,
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )

    # Time-series aggregation methods
    def aggregate_metrics_by_period(
        self,
        metric_type: MetricType,
        period: AggregationPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[str] = None,
    ) -> List[TrendData]:
        """
        Aggregate metrics into time-series buckets for trend analysis.

        Groups metrics by the specified time period (hourly, daily, weekly, monthly)
        and calculates aggregate statistics for each period.

        Args:
            metric_type: Type of metric to aggregate
            period: Time period for aggregation (hourly, daily, weekly, monthly)
            start_time: Optional start time for the aggregation window
            end_time: Optional end time for the aggregation window
            user_id: Optional filter by specific user ID

        Returns:
            List of TrendData objects, one per time bucket, sorted chronologically
        """
        # Get metrics with filtering
        metrics = self.metrics_tracker.get_metrics(
            metric_type=metric_type,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )

        if not metrics:
            return []

        # Group metrics into time buckets
        buckets = self._group_metrics_into_buckets(metrics, period)

        # Create TrendData objects for each bucket
        trend_data_list = []
        sorted_bucket_keys = sorted(buckets.keys())

        for bucket_start in sorted_bucket_keys:
            bucket_metrics = buckets[bucket_start]
            bucket_end = self._get_bucket_end_time(bucket_start, period)

            # Calculate average value for this bucket
            total_value = sum(m.value for m in bucket_metrics)
            average_value = total_value / len(bucket_metrics)

            # Calculate change percentage (comparing to first value in bucket)
            if len(bucket_metrics) > 1:
                first_value = bucket_metrics[0].value
                last_value = bucket_metrics[-1].value
                if first_value != 0:
                    change_percentage = ((last_value - first_value) / first_value) * 100
                else:
                    change_percentage = 0.0
            else:
                change_percentage = 0.0

            # Classify trend direction
            direction = classify_trend(change_percentage / 100)  # Convert to decimal

            # Create TrendData object
            trend_data = TrendData(
                metric_type=metric_type,
                direction=direction,
                period=period,
                start_time=bucket_start,
                end_time=bucket_end,
                data_points=bucket_metrics,
                average_value=average_value,
                change_percentage=change_percentage,
                metadata={
                    "num_data_points": len(bucket_metrics),
                    "min_value": min(m.value for m in bucket_metrics),
                    "max_value": max(m.value for m in bucket_metrics),
                },
            )
            trend_data_list.append(trend_data)

        return trend_data_list

    def _group_metrics_into_buckets(
        self, metrics: List[MetricEntry], period: AggregationPeriod
    ) -> Dict[datetime, List[MetricEntry]]:
        """
        Group metrics into time buckets based on aggregation period.

        Args:
            metrics: List of metrics to group
            period: Aggregation period (hourly, daily, weekly, monthly)

        Returns:
            Dictionary mapping bucket start time to list of metrics in that bucket
        """
        buckets = defaultdict(list)

        for metric in metrics:
            bucket_start = self._get_bucket_start_time(metric.timestamp, period)
            buckets[bucket_start].append(metric)

        return dict(buckets)

    def _get_bucket_start_time(
        self, timestamp: datetime, period: AggregationPeriod
    ) -> datetime:
        """
        Get the start time of the bucket that contains the given timestamp.

        Args:
            timestamp: The timestamp to find the bucket for
            period: Aggregation period

        Returns:
            Start time of the bucket
        """
        if period == AggregationPeriod.HOURLY:
            # Round down to start of hour
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif period == AggregationPeriod.DAILY:
            # Round down to start of day
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == AggregationPeriod.WEEKLY:
            # Round down to start of week (Monday)
            days_since_monday = timestamp.weekday()
            week_start = timestamp - timedelta(days=days_since_monday)
            return week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == AggregationPeriod.MONTHLY:
            # Round down to start of month
            return timestamp.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Unknown aggregation period: {period}")

    def _get_bucket_end_time(
        self, bucket_start: datetime, period: AggregationPeriod
    ) -> datetime:
        """
        Get the end time of a bucket given its start time.

        Args:
            bucket_start: Start time of the bucket
            period: Aggregation period

        Returns:
            End time of the bucket
        """
        if period == AggregationPeriod.HOURLY:
            return bucket_start + timedelta(hours=1)
        elif period == AggregationPeriod.DAILY:
            return bucket_start + timedelta(days=1)
        elif period == AggregationPeriod.WEEKLY:
            return bucket_start + timedelta(weeks=1)
        elif period == AggregationPeriod.MONTHLY:
            # Handle month boundaries properly
            if bucket_start.month == 12:
                return bucket_start.replace(year=bucket_start.year + 1, month=1)
            else:
                return bucket_start.replace(month=bucket_start.month + 1)
        else:
            raise ValueError(f"Unknown aggregation period: {period}")

    # Trend detection methods
    def detect_trend_pattern(
        self, trend_data_list: List[TrendData]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect overall trend patterns across multiple time periods.

        Analyzes a time-series of aggregated trend data to identify overall
        patterns such as improving, declining, or stable trends over time.
        Provides statistical analysis including confidence levels.

        Args:
            trend_data_list: List of TrendData objects sorted chronologically

        Returns:
            Dictionary with trend analysis results:
            - overall_direction: TrendDirection (IMPROVING, DECLINING, STABLE)
            - confidence: float (0.0-1.0) - confidence in the trend detection
            - start_value: float - average value of first period
            - end_value: float - average value of last period
            - total_change: float - absolute change from start to end
            - total_change_percentage: float - percentage change from start to end
            - average_change_per_period: float - average change between periods
            - num_periods: int - number of periods analyzed
            - consistency_score: float - how consistent the trend is (0.0-1.0)

            Returns None if insufficient data for trend detection.
        """
        # Return None if no data
        if not trend_data_list:
            return None

        # Get minimum data points threshold from config
        from config.analytics_config import TREND_SETTINGS

        min_data_points = TREND_SETTINGS.get("min_data_points", 3)

        # Check if we have enough periods for reliable trend detection
        num_periods = len(trend_data_list)

        if num_periods < 2:
            return None

        # Extract average values from each period
        values = [trend.average_value for trend in trend_data_list]

        # Calculate start and end values
        start_value = values[0]
        end_value = values[-1]

        # Calculate total change
        total_change = end_value - start_value

        # Calculate total change percentage
        if start_value != 0:
            total_change_percentage = (total_change / start_value) * 100
        else:
            # Handle zero start value
            total_change_percentage = 0.0 if total_change == 0 else 100.0

        # Calculate average change per period
        if num_periods > 1:
            average_change_per_period = total_change / (num_periods - 1)
        else:
            average_change_per_period = 0.0

        # Classify overall trend direction
        # Convert percentage to decimal for classify_trend (expects -1.0 to 1.0 scale)
        overall_direction = classify_trend(total_change_percentage / 100)

        # Calculate consistency score (how consistently the trend moves in one direction)
        consistency_score = self._calculate_trend_consistency(values)

        # Calculate confidence based on several factors:
        # 1. Number of data points (more = higher confidence)
        # 2. Consistency of trend (more consistent = higher confidence)
        # 3. Magnitude of change (larger changes = higher confidence for non-stable trends)

        # Confidence from data points (penalize small datasets heavily)
        # For 2 data points: very low confidence
        # For min_data_points: moderate confidence
        # For 2x min_data_points: high confidence
        if num_periods <= 2:
            data_point_confidence = 0.2  # Very low confidence for minimal data
        else:
            data_point_confidence = min(1.0, 0.3 + ((num_periods - 2) / (min_data_points * 2)) * 0.7)

        # Confidence from consistency
        consistency_confidence = consistency_score

        # Confidence from magnitude (for non-stable trends, larger changes = more confident)
        if overall_direction == TrendDirection.STABLE:
            magnitude_confidence = 1.0  # Stable trends don't need large changes
        else:
            # Normalize change percentage (consider 20%+ change as high confidence)
            magnitude_confidence = min(1.0, abs(total_change_percentage) / 20.0)

        # Overall confidence is weighted average of factors
        # For small datasets, weight data points more heavily
        if num_periods <= 2:
            confidence = (
                data_point_confidence * 0.7
                + consistency_confidence * 0.2
                + magnitude_confidence * 0.1
            )
        else:
            confidence = (
                data_point_confidence * 0.4
                + consistency_confidence * 0.4
                + magnitude_confidence * 0.2
            )

        return {
            "overall_direction": overall_direction,
            "confidence": confidence,
            "start_value": start_value,
            "end_value": end_value,
            "total_change": total_change,
            "total_change_percentage": total_change_percentage,
            "average_change_per_period": average_change_per_period,
            "num_periods": num_periods,
            "consistency_score": consistency_score,
        }

    def _calculate_trend_consistency(self, values: List[float]) -> float:
        """
        Calculate how consistent a trend is across periods.

        A consistent trend is one where values generally move in the same direction.
        Returns a score from 0.0 (very inconsistent) to 1.0 (perfectly consistent).

        Args:
            values: List of values from consecutive time periods

        Returns:
            Consistency score (0.0 to 1.0)
        """
        if len(values) < 2:
            return 0.0

        # Calculate changes between consecutive periods
        changes = [values[i + 1] - values[i] for i in range(len(values) - 1)]

        if not changes:
            return 0.0

        # Count how many changes are in the dominant direction
        positive_changes = sum(1 for c in changes if c > 0)
        negative_changes = sum(1 for c in changes if c < 0)
        zero_changes = sum(1 for c in changes if c == 0)

        total_changes = len(changes)

        # If all changes are zero, it's consistently stable
        if zero_changes == total_changes:
            return 1.0

        # Find the dominant direction
        dominant_count = max(positive_changes, negative_changes, zero_changes)

        # Consistency score is the proportion of changes in the dominant direction
        consistency_score = dominant_count / total_changes

        return consistency_score

    # Data management methods
    def clear_metrics(
        self,
        metric_type: Optional[MetricType] = None,
        before_time: Optional[datetime] = None,
    ) -> int:
        """
        Clear metrics from storage.

        Args:
            metric_type: Optional specific metric type to clear (None clears all)
            before_time: Optional timestamp to clear metrics before (None clears all)

        Returns:
            Number of metrics cleared
        """
        return self.metrics_tracker.clear_metrics(
            metric_type=metric_type,
            before_time=before_time,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the entire analytics manager state to dictionary.

        Returns:
            Dictionary representation of all analytics data
        """
        return {
            "metrics_tracker": self.metrics_tracker.to_dict(),
            "sentiment_analyzer": {
                "positive_words": list(self.sentiment_analyzer.positive_words),
                "negative_words": list(self.sentiment_analyzer.negative_words),
                "intensifiers": list(self.sentiment_analyzer.intensifiers),
                "negations": list(self.sentiment_analyzer.negations),
            },
            "hooks": {
                "event_names": list(self._hooks.keys()),
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalyticsManager":
        """
        Create an AnalyticsManager from dictionary representation.

        Args:
            data: Dictionary containing analytics data

        Returns:
            New AnalyticsManager instance with loaded data
        """
        manager = cls()

        # Restore metrics tracker
        if "metrics_tracker" in data:
            manager.metrics_tracker = MetricsTracker.from_dict(data["metrics_tracker"])

        # Restore sentiment analyzer configuration (if customized)
        if "sentiment_analyzer" in data:
            sa_data = data["sentiment_analyzer"]
            if "positive_words" in sa_data:
                manager.sentiment_analyzer.positive_words = set(sa_data["positive_words"])
            if "negative_words" in sa_data:
                manager.sentiment_analyzer.negative_words = set(sa_data["negative_words"])
            if "intensifiers" in sa_data:
                manager.sentiment_analyzer.intensifiers = set(sa_data["intensifiers"])
            if "negations" in sa_data:
                manager.sentiment_analyzer.negations = set(sa_data["negations"])

        # Restore hooks structure (callables can't be serialized, but event names can)
        if "hooks" in data and "event_names" in data["hooks"]:
            for event_name in data["hooks"]["event_names"]:
                if event_name not in manager._hooks:
                    manager._hooks[event_name] = []

        return manager

    # Hook system for memory system integration
    def register_hook(self, event_name: str, callback: callable) -> None:
        """
        Register a callback function for a specific event.

        Allows external systems (like memory systems) to register callbacks
        that will be triggered when specific analytics events occur.

        Args:
            event_name: Name of the event (e.g., "message_sent", "conversation_started")
            callback: Callable function to invoke when the event occurs
        """
        self._hooks[event_name].append(callback)

    def unregister_hook(self, event_name: str, callback: callable) -> None:
        """
        Unregister a callback function for a specific event.

        Args:
            event_name: Name of the event
            callback: Callable function to remove from the event
        """
        if event_name in self._hooks:
            try:
                self._hooks[event_name].remove(callback)
            except ValueError:
                pass  # Callback not in list

    def _trigger_hooks(self, event_name: str, **kwargs) -> None:
        """
        Trigger all registered callbacks for an event.

        Args:
            event_name: Name of the event to trigger
            **kwargs: Arguments to pass to the callback functions
        """
        for callback in self._hooks.get(event_name, []):
            try:
                callback(event_name, **kwargs)
            except Exception:
                pass  # Silently handle callback errors to avoid disrupting analytics

    # Event handler methods for memory system integration
    def on_message_sent(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Handle message sent event from memory system.

        Automatically tracks message sent metrics and triggers registered hooks.

        Args:
            user_id: Optional user ID associated with the message
            metadata: Additional context about the message
            timestamp: Optional timestamp (defaults to now)
        """
        self.track_message_sent(user_id=user_id, metadata=metadata, timestamp=timestamp)
        self._trigger_hooks("message_sent", user_id=user_id, metadata=metadata, timestamp=timestamp)

    def on_message_responded(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Handle message responded event from memory system.

        Automatically tracks message response metrics and triggers registered hooks.

        Args:
            user_id: Optional user ID associated with the message
            metadata: Additional context about the response
            timestamp: Optional timestamp (defaults to now)
        """
        self.track_message_responded(user_id=user_id, metadata=metadata, timestamp=timestamp)
        self._trigger_hooks("message_responded", user_id=user_id, metadata=metadata, timestamp=timestamp)

    def on_conversation_started(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Handle conversation started event from memory system.

        Automatically starts conversation tracking and triggers registered hooks.

        Args:
            conversation_id: Unique identifier for the conversation
            user_id: Optional user ID associated with the conversation
            metadata: Additional context about the conversation
            timestamp: Optional timestamp (defaults to now)
        """
        self.start_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )
        self._trigger_hooks(
            "conversation_started",
            conversation_id=conversation_id,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )

    def on_conversation_message_added(
        self,
        conversation_id: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Handle conversation message added event from memory system.

        Automatically adds message to conversation tracking and triggers registered hooks.

        Args:
            conversation_id: The conversation to add a message to
            timestamp: Optional timestamp of the message (defaults to now)
        """
        self.add_conversation_message(conversation_id=conversation_id, timestamp=timestamp)
        self._trigger_hooks(
            "conversation_message_added",
            conversation_id=conversation_id,
            timestamp=timestamp,
        )

    def on_conversation_ended(
        self,
        conversation_id: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Handle conversation ended event from memory system.

        Automatically ends conversation tracking and triggers registered hooks.

        Args:
            conversation_id: The conversation to end
            timestamp: Optional timestamp (defaults to now)
        """
        self.end_conversation(conversation_id=conversation_id, timestamp=timestamp)
        self._trigger_hooks(
            "conversation_ended",
            conversation_id=conversation_id,
            timestamp=timestamp,
        )

    def on_sentiment_analyzed(
        self,
        text: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> SentimentResult:
        """
        Handle sentiment analysis event from memory system.

        Automatically analyzes sentiment and triggers registered hooks.

        Args:
            text: The text to analyze
            user_id: Optional user ID for user-specific sentiment tracking
            metadata: Additional context about the text
            timestamp: Optional timestamp (defaults to now)

        Returns:
            SentimentResult with score, category, and confidence
        """
        sentiment_result = self.analyze_sentiment(
            text=text,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )
        self._trigger_hooks(
            "sentiment_analyzed",
            text=text,
            user_id=user_id,
            sentiment_result=sentiment_result,
            metadata=metadata,
            timestamp=timestamp,
        )
        return sentiment_result

    def on_metric_recorded(
        self,
        metric_type: MetricType,
        value: float,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> MetricEntry:
        """
        Handle metric recorded event from memory system.

        Automatically records metric and triggers registered hooks.

        Args:
            metric_type: Type of metric being recorded
            value: Numeric value of the metric
            user_id: Optional user ID if metric is user-specific
            metadata: Additional context and data
            timestamp: Optional timestamp (defaults to now)

        Returns:
            The created MetricEntry
        """
        metric_entry = self.record_metric(
            metric_type=metric_type,
            value=value,
            user_id=user_id,
            metadata=metadata,
            timestamp=timestamp,
        )
        self._trigger_hooks(
            "metric_recorded",
            metric_type=metric_type,
            value=value,
            user_id=user_id,
            metric_entry=metric_entry,
            metadata=metadata,
            timestamp=timestamp,
        )
        return metric_entry


__all__ = ["AnalyticsManager"]
