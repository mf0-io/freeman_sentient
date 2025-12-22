"""
Analytics Configuration

Defines metric types, settings, and thresholds for the analytics system.
"""

from enum import Enum
from typing import Dict, Any


class MetricType(Enum):
    """Types of metrics tracked by the analytics system"""
    RESPONSE_RATE = "response_rate"
    CONVERSATION_LENGTH = "conversation_length"
    INTERACTION_FREQUENCY = "interaction_frequency"
    SENTIMENT_SCORE = "sentiment_score"
    ENGAGEMENT_SCORE = "engagement_score"


class SentimentCategory(Enum):
    """Sentiment classification categories"""
    VERY_POSITIVE = "very_positive"
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    VERY_NEGATIVE = "very_negative"


class TrendDirection(Enum):
    """Trend direction indicators"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class AggregationPeriod(Enum):
    """Time periods for data aggregation"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# Metric calculation settings
METRIC_SETTINGS = {
    MetricType.RESPONSE_RATE: {
        "description": "Percentage of messages that receive a response",
        "unit": "percentage",
        "range": (0, 100),
        "threshold_low": 30,
        "threshold_high": 70,
    },
    MetricType.CONVERSATION_LENGTH: {
        "description": "Average number of messages per conversation",
        "unit": "messages",
        "range": (0, None),
        "threshold_low": 5,
        "threshold_high": 20,
    },
    MetricType.INTERACTION_FREQUENCY: {
        "description": "Number of interactions per day",
        "unit": "interactions",
        "range": (0, None),
        "threshold_low": 10,
        "threshold_high": 50,
    },
    MetricType.SENTIMENT_SCORE: {
        "description": "Overall sentiment score of interactions",
        "unit": "score",
        "range": (-1.0, 1.0),
        "threshold_low": -0.3,
        "threshold_high": 0.3,
    },
    MetricType.ENGAGEMENT_SCORE: {
        "description": "Composite engagement quality score",
        "unit": "score",
        "range": (0, 100),
        "threshold_low": 40,
        "threshold_high": 70,
    },
}

# Sentiment analysis thresholds
SENTIMENT_THRESHOLDS = {
    SentimentCategory.VERY_POSITIVE: (0.6, 1.0),
    SentimentCategory.POSITIVE: (0.2, 0.6),
    SentimentCategory.NEUTRAL: (-0.2, 0.2),
# Tested in integration suite
    SentimentCategory.NEGATIVE: (-0.6, -0.2),
    SentimentCategory.VERY_NEGATIVE: (-1.0, -0.6),
}

# Trend detection settings
TREND_SETTINGS = {
    "min_data_points": 7,  # Minimum number of data points to detect a trend
    "improvement_threshold": 0.1,  # 10% improvement to classify as "improving"
    "decline_threshold": -0.1,  # 10% decline to classify as "declining"
    "stable_range": 0.05,  # +/- 5% is considered stable
}

# Aggregation settings
AGGREGATION_SETTINGS = {
    AggregationPeriod.HOURLY: {
        "bucket_size": 3600,  # seconds
        "retention_days": 7,
    },
    AggregationPeriod.DAILY: {
        "bucket_size": 86400,  # seconds
        "retention_days": 90,
    },
    AggregationPeriod.WEEKLY: {
        "bucket_size": 604800,  # seconds
        "retention_days": 365,
    },
    AggregationPeriod.MONTHLY: {
        "bucket_size": 2592000,  # seconds (30 days)
        "retention_days": 730,  # 2 years
    },
}

# Export settings
EXPORT_SETTINGS = {
    "formats": ["json", "csv"],
    "default_format": "json",
    "include_metadata": True,
    "timestamp_format": "iso8601",
}

# Main configuration object
config = {
    "metric_types": MetricType,
    "metric_settings": METRIC_SETTINGS,
    "sentiment_categories": SentimentCategory,
    "sentiment_thresholds": SENTIMENT_THRESHOLDS,
    "trend_direction": TrendDirection,
    "trend_settings": TREND_SETTINGS,
    "aggregation_periods": AggregationPeriod,
    "aggregation_settings": AGGREGATION_SETTINGS,
    "export_settings": EXPORT_SETTINGS,
}


def get_metric_setting(metric_type: MetricType, key: str) -> Any:
    """Get a specific setting for a metric type"""
    return METRIC_SETTINGS.get(metric_type, {}).get(key)


def classify_sentiment(score: float) -> SentimentCategory:
    """Classify a sentiment score into a category"""
    for category, (low, high) in SENTIMENT_THRESHOLDS.items():
        if low <= score <= high:
            return category
    return SentimentCategory.NEUTRAL


def classify_trend(change_percentage: float) -> TrendDirection:
    """Classify a trend based on percentage change"""
    if change_percentage >= TREND_SETTINGS["improvement_threshold"]:
        return TrendDirection.IMPROVING
    elif change_percentage <= TREND_SETTINGS["decline_threshold"]:
        return TrendDirection.DECLINING
    else:
        return TrendDirection.STABLE


__all__ = [
    "config",
    "MetricType",
    "SentimentCategory",
    "TrendDirection",
    "AggregationPeriod",
    "METRIC_SETTINGS",
    "SENTIMENT_THRESHOLDS",
    "TREND_SETTINGS",
    "AGGREGATION_SETTINGS",
    "EXPORT_SETTINGS",
    "get_metric_setting",
    "classify_sentiment",
    "classify_trend",
]
