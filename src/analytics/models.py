"""
Analytics Data Models

Data models for storing and managing analytics data including metrics,
sentiment analysis results, and trend data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from config.analytics_config import MetricType, SentimentCategory, TrendDirection, AggregationPeriod


@dataclass
class MetricEntry:
    """
    Represents a single metric measurement.

    Attributes:
        metric_type: Type of metric being recorded
        value: Numeric value of the metric
        timestamp: When the metric was recorded
        user_id: Optional user ID if metric is user-specific
        metadata: Additional context and data
    """
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MetricEntry":
        """Create MetricEntry from dictionary"""
        return cls(
            metric_type=MetricType(data["metric_type"]),
            value=data["value"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SentimentResult:
    """
    Represents the result of sentiment analysis.

    Attributes:
        score: Sentiment score (-1.0 to 1.0)
        category: Classification category
        text: Text that was analyzed
        timestamp: When the analysis was performed
        confidence: Confidence level of the analysis (0.0 to 1.0)
        user_id: Optional user ID for user-specific sentiment
        metadata: Additional analysis details
    """
    score: float
    category: SentimentCategory
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "score": self.score,
            "category": self.category.value,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SentimentResult":
        """Create SentimentResult from dictionary"""
        return cls(
            score=data["score"],
            category=SentimentCategory(data["category"]),
            text=data["text"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            confidence=data.get("confidence", 1.0),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class TrendData:
    """
    Represents trend analysis data over a time period.

    Attributes:
        metric_type: Type of metric being tracked
        direction: Trend direction (improving, stable, declining)
        period: Time period for aggregation
        start_time: Start of the trend period
        end_time: End of the trend period
        data_points: List of MetricEntry objects in the period
        average_value: Average metric value over the period
        change_percentage: Percentage change from start to end
        metadata: Additional trend analysis data
    """
    metric_type: MetricType
    direction: TrendDirection
    period: AggregationPeriod
    start_time: datetime
    end_time: datetime
    data_points: List[MetricEntry] = field(default_factory=list)
    average_value: float = 0.0
    change_percentage: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "metric_type": self.metric_type.value,
            "direction": self.direction.value,
            "period": self.period.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "data_points": [dp.to_dict() for dp in self.data_points],
            "average_value": self.average_value,
            "change_percentage": self.change_percentage,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TrendData":
        """Create TrendData from dictionary"""
        return cls(
            metric_type=MetricType(data["metric_type"]),
            direction=TrendDirection(data["direction"]),
            period=AggregationPeriod(data["period"]),
            start_time=datetime.fromisoformat(data["start_time"]),
            end_time=datetime.fromisoformat(data["end_time"]),
            data_points=[
                MetricEntry.from_dict(dp) for dp in data.get("data_points", [])
            ],
            average_value=data.get("average_value", 0.0),
            change_percentage=data.get("change_percentage", 0.0),
            metadata=data.get("metadata", {}),
        )


__all__ = [
    "MetricEntry",
    "SentimentResult",
    "TrendData",
]
