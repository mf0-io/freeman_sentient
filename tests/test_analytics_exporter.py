"""
Tests for AnalyticsExporter

Tests data export functionality in JSON and CSV formats for metrics,
sentiment results, and trend data.
"""

import pytest
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

from src.analytics.analytics_exporter import AnalyticsExporter
from src.analytics.models import MetricEntry, SentimentResult, TrendData
from config.analytics_config import (
    MetricType,
    SentimentCategory,
    TrendDirection,
    AggregationPeriod,
)


class TestJSONExport:
    """Tests for JSON export functionality"""

    def test_json_export(self):
        """Test JSON export with full analytics data"""
        exporter = AnalyticsExporter(
            include_metadata=True,
            timestamp_format="iso8601",
        )

        now = datetime.now()
        past = now - timedelta(hours=1)

        # Create sample metrics
        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=85.5,
                timestamp=now,
                user_id="user1",
                metadata={"platform": "telegram"},
            ),
            MetricEntry(
                metric_type=MetricType.CONVERSATION_LENGTH,
                value=12.3,
                timestamp=past,
                user_id="user2",
                metadata={"channel": "general"},
            ),
        ]

        # Create sample sentiment results
        sentiment_results = [
            SentimentResult(
                score=0.8,
                category=SentimentCategory.VERY_POSITIVE,
                text="This is absolutely amazing!",
                timestamp=now,
                confidence=0.95,
                user_id="user1",
                metadata={"conversation_id": "conv1"},
            ),
            SentimentResult(
                score=-0.3,
                category=SentimentCategory.NEGATIVE,
                text="Not very good.",
                timestamp=past,
                confidence=0.85,
                user_id="user2",
                metadata={"conversation_id": "conv2"},
            ),
        ]

        # Create sample trend data
        trend_data = [
            TrendData(
                metric_type=MetricType.RESPONSE_RATE,
                direction=TrendDirection.IMPROVING,
                period=AggregationPeriod.DAILY,
                start_time=past,
                end_time=now,
                data_points=metrics[:1],
                average_value=85.5,
                change_percentage=15.2,
                metadata={"trend_strength": "strong"},
            ),
        ]

        # Test individual exports
        metrics_json = exporter.export_metrics_to_json(metrics)
        sentiment_json = exporter.export_sentiment_to_json(sentiment_results)
        trends_json = exporter.export_trends_to_json(trend_data)

        # Verify metrics JSON
        metrics_data = json.loads(metrics_json)
        assert len(metrics_data) == 2, "Expected 2 metrics in export"
        assert metrics_data[0]["metric_type"] == "response_rate"
        assert metrics_data[0]["value"] == 85.5
        assert metrics_data[0]["user_id"] == "user1"
        assert "platform" in metrics_data[0]["metadata"]
        assert "timestamp" in metrics_data[0]

        # Verify sentiment JSON
        sentiment_data = json.loads(sentiment_json)
        assert len(sentiment_data) == 2, "Expected 2 sentiment results in export"
        assert sentiment_data[0]["score"] == 0.8
        assert sentiment_data[0]["category"] == "very_positive"
        assert sentiment_data[0]["text"] == "This is absolutely amazing!"
        assert sentiment_data[0]["confidence"] == 0.95
        assert sentiment_data[0]["user_id"] == "user1"
        assert "conversation_id" in sentiment_data[0]["metadata"]

        # Verify trends JSON
        trends_data = json.loads(trends_json)
        assert len(trends_data) == 1, "Expected 1 trend in export"
        assert trends_data[0]["metric_type"] == "response_rate"
        assert trends_data[0]["direction"] == "improving"
        assert trends_data[0]["period"] == "daily"
        assert trends_data[0]["average_value"] == 85.5
        assert trends_data[0]["change_percentage"] == 15.2
        assert trends_data[0]["num_data_points"] == 1
        assert "trend_strength" in trends_data[0]["metadata"]

    def test_json_export_without_metadata(self):
        """Test JSON export with metadata excluded"""
        exporter = AnalyticsExporter(
            include_metadata=False,
            timestamp_format="iso8601",
        )

        now = datetime.now()
        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=75.0,
                timestamp=now,
                user_id="user1",
                metadata={"key": "value"},
            ),
        ]

        metrics_json = exporter.export_metrics_to_json(metrics)
        metrics_data = json.loads(metrics_json)

        assert len(metrics_data) == 1
        assert "user_id" not in metrics_data[0]
        assert "metadata" not in metrics_data[0]
        assert "metric_type" in metrics_data[0]
        assert "value" in metrics_data[0]
        assert "timestamp" in metrics_data[0]

    def test_json_export_unix_timestamp(self):
        """Test JSON export with Unix timestamp format"""
        exporter = AnalyticsExporter(
            include_metadata=True,
            timestamp_format="unix",
        )

        now = datetime.now()
        metrics = [
            MetricEntry(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                value=92.0,
                timestamp=now,
            ),
        ]

        metrics_json = exporter.export_metrics_to_json(metrics)
        metrics_data = json.loads(metrics_json)

        assert len(metrics_data) == 1
        assert isinstance(metrics_data[0]["timestamp"], int), "Expected Unix timestamp to be integer"
        assert metrics_data[0]["timestamp"] == int(now.timestamp())

    def test_json_export_empty_data(self):
        """Test JSON export with empty data lists"""
        exporter = AnalyticsExporter()

        # Test empty metrics
        metrics_json = exporter.export_metrics_to_json([])
        metrics_data = json.loads(metrics_json)
        assert metrics_data == [], "Expected empty array for empty metrics"

        # Test empty sentiment results
        sentiment_json = exporter.export_sentiment_to_json([])
        sentiment_data = json.loads(sentiment_json)
        assert sentiment_data == [], "Expected empty array for empty sentiment"

        # Test empty trends
        trends_json = exporter.export_trends_to_json([])
        trends_data = json.loads(trends_json)
        assert trends_data == [], "Expected empty array for empty trends"

    def test_json_export_to_file(self, tmp_path):
        """Test JSON export writing to file"""
        exporter = AnalyticsExporter()

        now = datetime.now()
        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=80.0,
                timestamp=now,
            ),
        ]

        # Export to file
        output_file = tmp_path / "metrics.json"
        metrics_json = exporter.export_metrics_to_json(metrics, output_file)

        # Verify file was created
        assert output_file.exists(), "Expected output file to exist"

        # Verify file contents
        with open(output_file, 'r') as f:
            file_data = json.load(f)

        assert len(file_data) == 1
        assert file_data[0]["metric_type"] == "response_rate"
        assert file_data[0]["value"] == 80.0

        # Verify returned string matches file contents
        returned_data = json.loads(metrics_json)
        assert returned_data == file_data

    def test_full_analytics_json_export(self):
        """Test exporting full analytics data in JSON format"""
        exporter = AnalyticsExporter()

        now = datetime.now()
        past = now - timedelta(hours=1)

        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=85.0,
                timestamp=now,
            ),
        ]

        sentiment_results = [
            SentimentResult(
                score=0.7,
                category=SentimentCategory.POSITIVE,
                text="Great work!",
                timestamp=now,
            ),
        ]

        trend_data = [
            TrendData(
                metric_type=MetricType.RESPONSE_RATE,
                direction=TrendDirection.IMPROVING,
                period=AggregationPeriod.DAILY,
                start_time=past,
                end_time=now,
                average_value=85.0,
                change_percentage=10.0,
            ),
        ]

        # Export full analytics
        results = exporter.export_full_analytics(
            metrics=metrics,
            sentiment_results=sentiment_results,
            trend_data=trend_data,
            output_format="json",
        )

        # Verify all three exports are present
        assert "metrics" in results
        assert "sentiment" in results
        assert "trends" in results

        # Verify metrics export
        metrics_data = json.loads(results["metrics"])
        assert len(metrics_data) == 1
        assert metrics_data[0]["metric_type"] == "response_rate"

        # Verify sentiment export
        sentiment_data = json.loads(results["sentiment"])
        assert len(sentiment_data) == 1
        assert sentiment_data[0]["score"] == 0.7

        # Verify trends export
        trends_data = json.loads(results["trends"])
        assert len(trends_data) == 1
        assert trends_data[0]["direction"] == "improving"

    def test_full_analytics_json_export_to_directory(self, tmp_path):
        """Test exporting full analytics to directory"""
        exporter = AnalyticsExporter()

        now = datetime.now()
        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=90.0,
                timestamp=now,
            ),
        ]

        sentiment_results = [
            SentimentResult(
                score=0.5,
                category=SentimentCategory.POSITIVE,
                text="Good!",
                timestamp=now,
            ),
        ]

        trend_data = [
            TrendData(
                metric_type=MetricType.RESPONSE_RATE,
                direction=TrendDirection.STABLE,
                period=AggregationPeriod.WEEKLY,
                start_time=now,
                end_time=now,
                average_value=90.0,
                change_percentage=0.5,
            ),
        ]

        # Export to directory
        output_dir = tmp_path / "analytics_export"
        output_dir.mkdir()

        results = exporter.export_full_analytics(
            metrics=metrics,
            sentiment_results=sentiment_results,
            trend_data=trend_data,
            output_format="json",
            output_dir=output_dir,
        )

        # Verify files were created
        assert (output_dir / "metrics.json").exists()
        assert (output_dir / "sentiment.json").exists()
        assert (output_dir / "trends.json").exists()

        # Verify file contents
        with open(output_dir / "metrics.json", 'r') as f:
            metrics_data = json.load(f)
        assert len(metrics_data) == 1
        assert metrics_data[0]["value"] == 90.0

        with open(output_dir / "sentiment.json", 'r') as f:
            sentiment_data = json.load(f)
        assert len(sentiment_data) == 1
        assert sentiment_data[0]["score"] == 0.5

        with open(output_dir / "trends.json", 'r') as f:
            trends_data = json.load(f)
        assert len(trends_data) == 1
        assert trends_data[0]["direction"] == "stable"


class TestCSVExport:
    """Tests for CSV export functionality"""

    def test_csv_export(self):
        """Test CSV export with full analytics data"""
        exporter = AnalyticsExporter(
            include_metadata=True,
            timestamp_format="iso8601",
        )

        now = datetime.now()
        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=85.5,
                timestamp=now,
                user_id="user1",
                metadata={"platform": "telegram"},
            ),
        ]

        # Export to CSV
        csv_str = exporter.export_metrics_to_csv(metrics)

        # Parse CSV
        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["metric_type"] == "response_rate"
        assert float(rows[0]["value"]) == 85.5
        assert rows[0]["user_id"] == "user1"
        assert "timestamp" in rows[0]

    def test_csv_export_empty_data(self):
        """Test CSV export with empty data"""
        exporter = AnalyticsExporter()

        csv_str = exporter.export_metrics_to_csv([])
        assert csv_str == "", "Expected empty string for empty data"

    def test_csv_export_to_file(self, tmp_path):
        """Test CSV export writing to file"""
        exporter = AnalyticsExporter()

        now = datetime.now()
        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=75.0,
                timestamp=now,
            ),
        ]

        output_file = tmp_path / "metrics.csv"
        csv_str = exporter.export_metrics_to_csv(metrics, output_file)

        assert output_file.exists()

        # Verify file contents
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["metric_type"] == "response_rate"

    def test_full_analytics_csv_export(self):
        """Test exporting full analytics in CSV format"""
        exporter = AnalyticsExporter()

        now = datetime.now()
        past = now - timedelta(hours=1)

        metrics = [
            MetricEntry(
                metric_type=MetricType.RESPONSE_RATE,
                value=85.0,
                timestamp=now,
            ),
        ]

        sentiment_results = [
            SentimentResult(
                score=0.7,
                category=SentimentCategory.POSITIVE,
                text="Great!",
                timestamp=now,
            ),
        ]

        trend_data = [
            TrendData(
                metric_type=MetricType.RESPONSE_RATE,
                direction=TrendDirection.IMPROVING,
                period=AggregationPeriod.DAILY,
                start_time=past,
                end_time=now,
                average_value=85.0,
                change_percentage=10.0,
            ),
        ]

        results = exporter.export_full_analytics(
            metrics=metrics,
            sentiment_results=sentiment_results,
            trend_data=trend_data,
            output_format="csv",
        )

        assert "metrics" in results
        assert "sentiment" in results
        assert "trends" in results

        # Verify metrics CSV
        reader = csv.DictReader(StringIO(results["metrics"]))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["metric_type"] == "response_rate"


class TestExportConfiguration:
    """Tests for export configuration options"""

    def test_metadata_inclusion_toggle(self):
        """Test toggling metadata inclusion"""
        now = datetime.now()
        metric = MetricEntry(
            metric_type=MetricType.RESPONSE_RATE,
            value=80.0,
            timestamp=now,
            user_id="user1",
            metadata={"key": "value"},
        )

        # With metadata
        exporter_with = AnalyticsExporter(include_metadata=True)
        json_with = exporter_with.export_metrics_to_json([metric])
        data_with = json.loads(json_with)
        assert "user_id" in data_with[0]
        assert "metadata" in data_with[0]

        # Without metadata
        exporter_without = AnalyticsExporter(include_metadata=False)
        json_without = exporter_without.export_metrics_to_json([metric])
        data_without = json.loads(json_without)
        assert "user_id" not in data_without[0]
        assert "metadata" not in data_without[0]

    def test_timestamp_format_options(self):
        """Test different timestamp format options"""
        now = datetime.now()
        metric = MetricEntry(
            metric_type=MetricType.RESPONSE_RATE,
            value=80.0,
            timestamp=now,
        )

        # ISO8601 format
        exporter_iso = AnalyticsExporter(timestamp_format="iso8601")
        json_iso = exporter_iso.export_metrics_to_json([metric])
        data_iso = json.loads(json_iso)
        assert isinstance(data_iso[0]["timestamp"], str)
        assert "T" in data_iso[0]["timestamp"]  # ISO format includes 'T'

        # Unix timestamp format
        exporter_unix = AnalyticsExporter(timestamp_format="unix")
        json_unix = exporter_unix.export_metrics_to_json([metric])
        data_unix = json.loads(json_unix)
        assert isinstance(data_unix[0]["timestamp"], int)

    def test_unsupported_format_error(self):
        """Test error handling for unsupported export format"""
        exporter = AnalyticsExporter()

        with pytest.raises(ValueError) as excinfo:
            exporter.export_full_analytics(
                metrics=[],
                sentiment_results=[],
                trend_data=[],
                output_format="xml",  # Unsupported format
            )

        assert "Unsupported format" in str(excinfo.value)
        assert "xml" in str(excinfo.value)
