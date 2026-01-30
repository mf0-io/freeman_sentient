"""
Metrics Tracker

Tracks and manages engagement metrics collection for the analytics system.
Stores metric entries and provides methods for recording and retrieving metrics.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from .models import MetricEntry
from config.analytics_config import MetricType


class MetricsTracker:
    """
    Tracks and manages engagement metrics.

    Responsible for recording metric entries, storing them in memory,
    and providing retrieval methods for analysis.

    Attributes:
        metrics: Dictionary storing metric entries organized by type
    """

    def __init__(self):
        """Initialize the MetricsTracker with empty metric storage"""
        self.metrics: Dict[MetricType, List[MetricEntry]] = defaultdict(list)
        # Track messages for response rate calculation
        self._messages_sent: List[Dict[str, Any]] = []
        self._messages_responded: List[Dict[str, Any]] = []
        # Track conversations for length and duration metrics
        self._conversations: Dict[str, Dict[str, Any]] = {}

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
        entry = MetricEntry(
            metric_type=metric_type,
            value=value,
            user_id=user_id,
            metadata=metadata or {},
            timestamp=timestamp or datetime.now(),
        )
        self.metrics[metric_type].append(entry)
        return entry

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
        # Determine which metric types to search
        if metric_type is not None:
            metric_types_to_search = [metric_type]
        else:
            metric_types_to_search = list(self.metrics.keys())

        results = []
        for mtype in metric_types_to_search:
            for entry in self.metrics[mtype]:
                # Apply filters
                if user_id is not None and entry.user_id != user_id:
                    continue
                if start_time is not None and entry.timestamp < start_time:
                    continue
                if end_time is not None and entry.timestamp > end_time:
                    continue

                results.append(entry)

        # Sort by timestamp (oldest first)
        results.sort(key=lambda e: e.timestamp)
        return results

    def get_latest_metric(
        self,
        metric_type: MetricType,
        user_id: Optional[str] = None,
    ) -> Optional[MetricEntry]:
        """
        Get the most recent metric entry of a specific type.

        Args:
            metric_type: Type of metric to retrieve
            user_id: Optional user ID filter

        Returns:
            The most recent MetricEntry or None if no metrics exist
        """
        metrics = self.get_metrics(metric_type=metric_type, user_id=user_id)
        return metrics[-1] if metrics else None

    def get_average_value(
        self,
        metric_type: MetricType,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate the average value for a metric type.

        Args:
            metric_type: Type of metric to average
            user_id: Optional user ID filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Average value or 0.0 if no metrics exist
        """
        metrics = self.get_metrics(
            metric_type=metric_type,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )
        if not metrics:
            return 0.0

        total = sum(entry.value for entry in metrics)
        return total / len(metrics)

    def get_metric_count(
        self,
        metric_type: Optional[MetricType] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """
        Count the number of metrics matching the filters.

        Args:
            metric_type: Optional metric type filter
            user_id: Optional user ID filter
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Number of matching metrics
        """
        metrics = self.get_metrics(
            metric_type=metric_type,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )
        return len(metrics)

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
        count = 0

        if metric_type is not None:
            # Clear specific metric type
            metric_types_to_clear = [metric_type]
        else:
            # Clear all metric types
            metric_types_to_clear = list(self.metrics.keys())

        for mtype in metric_types_to_clear:
            if before_time is None:
                # Clear all metrics of this type
                count += len(self.metrics[mtype])
                self.metrics[mtype] = []
            else:
                # Clear only metrics before the specified time
                original_count = len(self.metrics[mtype])
                self.metrics[mtype] = [
                    entry for entry in self.metrics[mtype]
                    if entry.timestamp >= before_time
                ]
                count += original_count - len(self.metrics[mtype])

        return count

    def track_message_sent(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Track a message that was sent.

        Used for calculating response rates. Records when a message is sent
        to or from a user.

        Args:
            user_id: Optional user ID associated with the message
            metadata: Additional context about the message
            timestamp: Optional timestamp (defaults to now)
        """
        message_data = {
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": timestamp or datetime.now(),
        }
        self._messages_sent.append(message_data)

    def track_message_responded(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Track a message that received a response.

        Used for calculating response rates. Records when a message receives
        a response.

        Args:
            user_id: Optional user ID associated with the message
            metadata: Additional context about the response
            timestamp: Optional timestamp (defaults to now)
        """
        message_data = {
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": timestamp or datetime.now(),
        }
        self._messages_responded.append(message_data)

    def calculate_response_rate(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate the response rate as a percentage.

        Response rate = (messages responded / messages sent) * 100

        Args:
            user_id: Optional filter by specific user ID (None for all users)
            start_time: Optional filter messages after this time
            end_time: Optional filter messages before this time

        Returns:
            Response rate as a percentage (0.0 to 100.0)
        """
        # Filter messages sent
        sent_count = 0
        for msg in self._messages_sent:
            # Apply filters
            if user_id is not None and msg["user_id"] != user_id:
                continue
            if start_time is not None and msg["timestamp"] < start_time:
                continue
            if end_time is not None and msg["timestamp"] > end_time:
                continue
            sent_count += 1

        # If no messages sent, return 0%
        if sent_count == 0:
            return 0.0

        # Filter messages responded
        responded_count = 0
        for msg in self._messages_responded:
            # Apply filters
            if user_id is not None and msg["user_id"] != user_id:
                continue
            if start_time is not None and msg["timestamp"] < start_time:
                continue
            if end_time is not None and msg["timestamp"] > end_time:
                continue
            responded_count += 1

        # Calculate percentage
        response_rate = (responded_count / sent_count) * 100
        return response_rate

    def start_conversation(
        self,
        conversation_id: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Start tracking a new conversation.

        Records the start of a conversation with initial metadata.
        The first message is counted automatically at conversation start.

        Args:
            conversation_id: Unique identifier for the conversation
            user_id: Optional user ID associated with the conversation
            metadata: Additional context about the conversation
            timestamp: Optional timestamp (defaults to now)
        """
        start_time = timestamp or datetime.now()
        self._conversations[conversation_id] = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "start_time": start_time,
            "end_time": None,
            "message_count": 1,  # Start counts as first message
            "metadata": metadata or {},
            "is_active": True,
        }

    def add_conversation_message(
        self,
        conversation_id: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add a message to an existing conversation.

        Increments the message count for the conversation.

        Args:
            conversation_id: The conversation to add a message to
            timestamp: Optional timestamp of the message (defaults to now)
        """
        if conversation_id not in self._conversations:
            raise ValueError(f"Conversation {conversation_id} not found. Call start_conversation first.")

        self._conversations[conversation_id]["message_count"] += 1

    def end_conversation(
        self,
        conversation_id: str,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Mark a conversation as ended.

        Records the end time and marks the conversation as inactive.

        Args:
            conversation_id: The conversation to end
            timestamp: Optional timestamp (defaults to now)
        """
        if conversation_id not in self._conversations:
            raise ValueError(f"Conversation {conversation_id} not found.")

        end_time = timestamp or datetime.now()
        self._conversations[conversation_id]["end_time"] = end_time
        self._conversations[conversation_id]["is_active"] = False

    def get_conversation_stats(
        self,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a specific conversation.

        Returns message count, duration, and activity status.
        For active conversations, duration is calculated from start to now.

        Args:
            conversation_id: The conversation to get stats for

        Returns:
            Dictionary with conversation statistics or None if not found
        """
        if conversation_id not in self._conversations:
            return None

        conv = self._conversations[conversation_id]
        start_time = conv["start_time"]
        end_time = conv["end_time"]
        is_active = conv["is_active"]

        # Calculate duration
        if end_time is not None:
            duration = (end_time - start_time).total_seconds()
        else:
            # Active conversation: calculate duration from start to now
            duration = (datetime.now() - start_time).total_seconds()

        return {
            "conversation_id": conversation_id,
            "user_id": conv["user_id"],
            "message_count": conv["message_count"],
            "duration_seconds": duration,
            "start_time": start_time,
            "end_time": end_time,
            "is_active": is_active,
            "metadata": conv["metadata"],
        }

    def calculate_average_conversation_length(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate the average conversation length in messages.

        Only includes ended conversations in the calculation.

        Args:
            user_id: Optional filter by specific user ID
            start_time: Optional filter conversations after this time
            end_time: Optional filter conversations before this time

        Returns:
            Average number of messages per conversation or 0.0 if no conversations
        """
        total_messages = 0
        count = 0

        for conv_id, conv in self._conversations.items():
            # Only include ended conversations
            if conv["is_active"]:
                continue

            # Apply filters
            if user_id is not None and conv["user_id"] != user_id:
                continue
            if start_time is not None and conv["start_time"] < start_time:
                continue
            if end_time is not None and conv["start_time"] > end_time:
                continue

            total_messages += conv["message_count"]
            count += 1

        if count == 0:
            return 0.0

        return total_messages / count

    def calculate_average_conversation_duration(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> float:
        """
        Calculate the average conversation duration in seconds.

        Only includes ended conversations in the calculation.

        Args:
            user_id: Optional filter by specific user ID
            start_time: Optional filter conversations after this time
            end_time: Optional filter conversations before this time

        Returns:
            Average duration in seconds or 0.0 if no conversations
        """
        total_duration = 0.0
        count = 0

        for conv_id, conv in self._conversations.items():
            # Only include ended conversations
            if conv["is_active"] or conv["end_time"] is None:
                continue

            # Apply filters
            if user_id is not None and conv["user_id"] != user_id:
                continue
            if start_time is not None and conv["start_time"] < start_time:
                continue
            if end_time is not None and conv["start_time"] > end_time:
                continue

            duration = (conv["end_time"] - conv["start_time"]).total_seconds()
            total_duration += duration
            count += 1

        if count == 0:
            return 0.0

        return total_duration / count

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the entire tracker state to dictionary.

        Returns:
            Dictionary representation of all metrics and tracking data
        """
        return {
            "metrics": {
                metric_type.value: [entry.to_dict() for entry in entries]
                for metric_type, entries in self.metrics.items()
            },
            "messages_sent": [
                {
                    "user_id": msg["user_id"],
                    "metadata": msg["metadata"],
                    "timestamp": msg["timestamp"].isoformat(),
                }
                for msg in self._messages_sent
            ],
            "messages_responded": [
                {
                    "user_id": msg["user_id"],
                    "metadata": msg["metadata"],
                    "timestamp": msg["timestamp"].isoformat(),
                }
                for msg in self._messages_responded
            ],
            "conversations": {
                conv_id: {
                    "conversation_id": conv["conversation_id"],
                    "user_id": conv["user_id"],
                    "start_time": conv["start_time"].isoformat(),
                    "end_time": conv["end_time"].isoformat() if conv["end_time"] else None,
                    "message_count": conv["message_count"],
                    "metadata": conv["metadata"],
                    "is_active": conv["is_active"],
                }
                for conv_id, conv in self._conversations.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricsTracker":
        """
        Create a MetricsTracker from dictionary representation.

        Args:
            data: Dictionary containing metrics data and message tracking

        Returns:
            New MetricsTracker instance with loaded data
        """
        tracker = cls()
        metrics_data = data.get("metrics", {})

        for metric_type_str, entries_data in metrics_data.items():
            metric_type = MetricType(metric_type_str)
            for entry_data in entries_data:
                entry = MetricEntry.from_dict(entry_data)
                tracker.metrics[metric_type].append(entry)

        # Restore message tracking data
        messages_sent_data = data.get("messages_sent", [])
        for msg_data in messages_sent_data:
            tracker._messages_sent.append({
                "user_id": msg_data["user_id"],
                "metadata": msg_data.get("metadata", {}),
                "timestamp": datetime.fromisoformat(msg_data["timestamp"]),
            })

        messages_responded_data = data.get("messages_responded", [])
        for msg_data in messages_responded_data:
            tracker._messages_responded.append({
                "user_id": msg_data["user_id"],
                "metadata": msg_data.get("metadata", {}),
                "timestamp": datetime.fromisoformat(msg_data["timestamp"]),
            })

        # Restore conversation data
        conversations_data = data.get("conversations", {})
        for conv_id, conv_data in conversations_data.items():
            tracker._conversations[conv_id] = {
                "conversation_id": conv_data["conversation_id"],
                "user_id": conv_data["user_id"],
                "start_time": datetime.fromisoformat(conv_data["start_time"]),
                "end_time": datetime.fromisoformat(conv_data["end_time"]) if conv_data["end_time"] else None,
                "message_count": conv_data["message_count"],
                "metadata": conv_data.get("metadata", {}),
                "is_active": conv_data["is_active"],
            }

        return tracker


__all__ = ["MetricsTracker"]
