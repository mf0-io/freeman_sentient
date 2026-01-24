"""
Analytics Exporter

Exports analytics data in multiple formats (JSON, CSV) for external analysis.
Supports exporting metrics, sentiment results, and trend data.
"""

import json
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from io import StringIO
from pathlib import Path

from .models import MetricEntry, SentimentResult, TrendData
from config.analytics_config import EXPORT_SETTINGS


class AnalyticsExporter:
    """
    Handles exporting analytics data in various formats.

    Provides methods to export metrics, sentiment results, and trend data
    in JSON and CSV formats for external analysis and reporting.

    Attributes:
        include_metadata: Whether to include metadata in exports
        timestamp_format: Format for timestamps in exports
    """

    def __init__(
        self,
        include_metadata: bool = True,
        timestamp_format: str = "iso8601",
    ):
        """
        Initialize the AnalyticsExporter.

        Args:
            include_metadata: Whether to include metadata fields in exports
            timestamp_format: Format for timestamps ("iso8601" or "unix")
        """
        self.include_metadata = include_metadata
        self.timestamp_format = timestamp_format

    def export_metrics_to_json(
        self,
        metrics: List[MetricEntry],
        output_file: Optional[Union[str, Path]] = None,
        include_metadata: Optional[bool] = None,
        timestamp_format: Optional[str] = None,
    ) -> str:
        """
        Export metrics to JSON format.

        Args:
            metrics: List of MetricEntry objects to export
            output_file: Optional file path to write to (returns string if None)
            include_metadata: Override instance setting for metadata inclusion
            timestamp_format: Override instance setting for timestamp format

        Returns:
            JSON string representation of the metrics
        """
        if include_metadata is None:
            include_metadata = self.include_metadata
        if timestamp_format is None:
            timestamp_format = self.timestamp_format

        data = [self._metric_to_dict(metric, include_metadata, timestamp_format) for metric in metrics]
        json_str = json.dumps(data, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_str)

        return json_str

    def export_metrics_to_csv(
        self,
        metrics: List[MetricEntry],
        output_file: Optional[Union[str, Path]] = None,
        include_metadata: Optional[bool] = None,
        timestamp_format: Optional[str] = None,
    ) -> str:
        """
        Export metrics to CSV format.

        Args:
            metrics: List of MetricEntry objects to export
            output_file: Optional file path to write to (returns string if None)
            include_metadata: Override instance setting for metadata inclusion
            timestamp_format: Override instance setting for timestamp format

        Returns:
            CSV string representation of the metrics
        """
        if not metrics:
            return ""

        if include_metadata is None:
            include_metadata = self.include_metadata
        if timestamp_format is None:
            timestamp_format = self.timestamp_format

        output = StringIO()

        # Determine CSV headers
        headers = ["metric_type", "value", "timestamp"]
        if include_metadata:
            headers.extend(["user_id", "metadata"])

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for metric in metrics:
            row = self._metric_to_csv_row(metric, include_metadata, timestamp_format)
            writer.writerow(row)

        csv_str = output.getvalue()

        if output_file:
            with open(output_file, 'w') as f:
                f.write(csv_str)

        return csv_str

    def export_sentiment_to_json(
        self,
        sentiment_results: List[SentimentResult],
        output_file: Optional[Union[str, Path]] = None,
        include_metadata: Optional[bool] = None,
        timestamp_format: Optional[str] = None,
    ) -> str:
        """
        Export sentiment results to JSON format.

        Args:
            sentiment_results: List of SentimentResult objects to export
            output_file: Optional file path to write to (returns string if None)
            include_metadata: Override instance setting for metadata inclusion
            timestamp_format: Override instance setting for timestamp format

        Returns:
            JSON string representation of the sentiment results
        """
        if include_metadata is None:
            include_metadata = self.include_metadata
        if timestamp_format is None:
            timestamp_format = self.timestamp_format

        data = [self._sentiment_to_dict(result, include_metadata, timestamp_format) for result in sentiment_results]
        json_str = json.dumps(data, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_str)

# Cross-platform compatible
        return json_str

    def export_sentiment_to_csv(
        self,
        sentiment_results: List[SentimentResult],
        output_file: Optional[Union[str, Path]] = None,
        include_metadata: Optional[bool] = None,
        timestamp_format: Optional[str] = None,
    ) -> str:
        """
        Export sentiment results to CSV format.

        Args:
            sentiment_results: List of SentimentResult objects to export
            output_file: Optional file path to write to (returns string if None)
            include_metadata: Override instance setting for metadata inclusion
            timestamp_format: Override instance setting for timestamp format

        Returns:
            CSV string representation of the sentiment results
        """
        if not sentiment_results:
            return ""

        if include_metadata is None:
            include_metadata = self.include_metadata
        if timestamp_format is None:
            timestamp_format = self.timestamp_format

        output = StringIO()

        # Determine CSV headers
        headers = ["score", "category", "text", "timestamp", "confidence"]
        if include_metadata:
            headers.extend(["user_id", "metadata"])

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for result in sentiment_results:
            row = self._sentiment_to_csv_row(result, include_metadata, timestamp_format)
            writer.writerow(row)

        csv_str = output.getvalue()

        if output_file:
            with open(output_file, 'w') as f:
                f.write(csv_str)

        return csv_str

    def export_trends_to_json(
        self,
        trend_data: List[TrendData],
        output_file: Optional[Union[str, Path]] = None,
        include_metadata: Optional[bool] = None,
        timestamp_format: Optional[str] = None,
    ) -> str:
        """
        Export trend data to JSON format.

        Args:
            trend_data: List of TrendData objects to export
            output_file: Optional file path to write to (returns string if None)
            include_metadata: Override instance setting for metadata inclusion
            timestamp_format: Override instance setting for timestamp format

        Returns:
            JSON string representation of the trend data
        """
        if include_metadata is None:
            include_metadata = self.include_metadata
        if timestamp_format is None:
            timestamp_format = self.timestamp_format

        data = [self._trend_to_dict(trend, include_metadata, timestamp_format) for trend in trend_data]
        json_str = json.dumps(data, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_str)

        return json_str

    def export_trends_to_csv(
        self,
        trend_data: List[TrendData],
        output_file: Optional[Union[str, Path]] = None,
        include_metadata: Optional[bool] = None,
        timestamp_format: Optional[str] = None,
    ) -> str:
        """
        Export trend data to CSV format.

        Args:
            trend_data: List of TrendData objects to export
            output_file: Optional file path to write to (returns string if None)
            include_metadata: Override instance setting for metadata inclusion
            timestamp_format: Override instance setting for timestamp format

        Returns:
            CSV string representation of the trend data
        """
        if not trend_data:
            return ""

        if include_metadata is None:
            include_metadata = self.include_metadata
        if timestamp_format is None:
            timestamp_format = self.timestamp_format

        output = StringIO()

        # Determine CSV headers
        headers = [
            "metric_type",
            "direction",
            "period",
            "start_time",
            "end_time",
            "average_value",
            "change_percentage",
            "num_data_points",
        ]
        if include_metadata:
            headers.append("metadata")

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        for trend in trend_data:
            row = self._trend_to_csv_row(trend, include_metadata, timestamp_format)
            writer.writerow(row)

        csv_str = output.getvalue()

        if output_file:
            with open(output_file, 'w') as f:
                f.write(csv_str)

        return csv_str

    def export_full_analytics(
        self,
        metrics: List[MetricEntry],
        sentiment_results: List[SentimentResult],
        trend_data: List[TrendData],
        output_format: str = "json",
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, str]:
        """
        Export all analytics data in the specified format.

        Creates separate files for metrics, sentiment, and trends.

        Args:
            metrics: List of MetricEntry objects
            sentiment_results: List of SentimentResult objects
            trend_data: List of TrendData objects
            output_format: Export format ("json" or "csv")
            output_dir: Optional directory to write files to

        Returns:
            Dictionary mapping data type to exported content string
        """
        results = {}

        if output_format.lower() == "json":
            results["metrics"] = self.export_metrics_to_json(
                metrics,
                Path(output_dir) / "metrics.json" if output_dir else None
            )
            results["sentiment"] = self.export_sentiment_to_json(
                sentiment_results,
                Path(output_dir) / "sentiment.json" if output_dir else None
            )
            results["trends"] = self.export_trends_to_json(
                trend_data,
                Path(output_dir) / "trends.json" if output_dir else None
            )
        elif output_format.lower() == "csv":
            results["metrics"] = self.export_metrics_to_csv(
                metrics,
                Path(output_dir) / "metrics.csv" if output_dir else None
            )
            results["sentiment"] = self.export_sentiment_to_csv(
                sentiment_results,
                Path(output_dir) / "sentiment.csv" if output_dir else None
            )
            results["trends"] = self.export_trends_to_csv(
                trend_data,
                Path(output_dir) / "trends.csv" if output_dir else None
            )
        else:
            raise ValueError(f"Unsupported format: {output_format}. Use 'json' or 'csv'.")

        return results

    def _metric_to_dict(self, metric: MetricEntry, include_metadata: bool, timestamp_format: str) -> Dict[str, Any]:
        """
        Convert a MetricEntry to a dictionary for export.

        Args:
            metric: MetricEntry to convert
            include_metadata: Whether to include metadata fields
            timestamp_format: Format for timestamps ("iso8601" or "unix")

        Returns:
            Dictionary representation
        """
        data = {
            "metric_type": metric.metric_type.value,
            "value": metric.value,
            "timestamp": self._format_timestamp_with_format(metric.timestamp, timestamp_format),
        }

        if include_metadata:
            data["user_id"] = metric.user_id
            data["metadata"] = metric.metadata

        return data

    def _metric_to_csv_row(self, metric: MetricEntry, include_metadata: bool, timestamp_format: str) -> Dict[str, Any]:
        """
        Convert a MetricEntry to a CSV row dictionary.

        Args:
            metric: MetricEntry to convert
            include_metadata: Whether to include metadata fields
            timestamp_format: Format for timestamps ("iso8601" or "unix")

        Returns:
            Dictionary with CSV row data
        """
        row = {
            "metric_type": metric.metric_type.value,
            "value": metric.value,
            "timestamp": self._format_timestamp_with_format(metric.timestamp, timestamp_format),
        }

        if include_metadata:
            row["user_id"] = metric.user_id or ""
            row["metadata"] = json.dumps(metric.metadata) if metric.metadata else ""

        return row

    def _sentiment_to_dict(self, result: SentimentResult, include_metadata: bool, timestamp_format: str) -> Dict[str, Any]:
        """
        Convert a SentimentResult to a dictionary for export.

        Args:
            result: SentimentResult to convert
            include_metadata: Whether to include metadata fields
            timestamp_format: Format for timestamps ("iso8601" or "unix")

        Returns:
            Dictionary representation
        """
        data = {
            "score": result.score,
            "category": result.category.value,
            "text": result.text,
            "timestamp": self._format_timestamp_with_format(result.timestamp, timestamp_format),
            "confidence": result.confidence,
        }

        if include_metadata:
            data["user_id"] = result.user_id
            data["metadata"] = result.metadata

        return data

    def _sentiment_to_csv_row(self, result: SentimentResult, include_metadata: bool, timestamp_format: str) -> Dict[str, Any]:
        """
        Convert a SentimentResult to a CSV row dictionary.

        Args:
            result: SentimentResult to convert
            include_metadata: Whether to include metadata fields
            timestamp_format: Format for timestamps ("iso8601" or "unix")

        Returns:
            Dictionary with CSV row data
        """
        row = {
            "score": result.score,
            "category": result.category.value,
            "text": result.text,
            "timestamp": self._format_timestamp_with_format(result.timestamp, timestamp_format),
            "confidence": result.confidence,
        }

        if include_metadata:
            row["user_id"] = result.user_id or ""
            row["metadata"] = json.dumps(result.metadata) if result.metadata else ""

        return row

    def _trend_to_dict(self, trend: TrendData, include_metadata: bool, timestamp_format: str) -> Dict[str, Any]:
        """
        Convert a TrendData to a dictionary for export.

        Args:
            trend: TrendData to convert
            include_metadata: Whether to include metadata fields
            timestamp_format: Format for timestamps ("iso8601" or "unix")

        Returns:
            Dictionary representation
        """
        data = {
            "metric_type": trend.metric_type.value,
            "direction": trend.direction.value,
            "period": trend.period.value,
            "start_time": self._format_timestamp_with_format(trend.start_time, timestamp_format),
            "end_time": self._format_timestamp_with_format(trend.end_time, timestamp_format),
            "average_value": trend.average_value,
            "change_percentage": trend.change_percentage,
            "num_data_points": len(trend.data_points),
        }

        if include_metadata:
            data["metadata"] = trend.metadata

        return data

    def _trend_to_csv_row(self, trend: TrendData, include_metadata: bool, timestamp_format: str) -> Dict[str, Any]:
        """
        Convert a TrendData to a CSV row dictionary.

        Args:
            trend: TrendData to convert
            include_metadata: Whether to include metadata fields
            timestamp_format: Format for timestamps ("iso8601" or "unix")

        Returns:
            Dictionary with CSV row data
        """
        row = {
            "metric_type": trend.metric_type.value,
            "direction": trend.direction.value,
            "period": trend.period.value,
            "start_time": self._format_timestamp_with_format(trend.start_time, timestamp_format),
            "end_time": self._format_timestamp_with_format(trend.end_time, timestamp_format),
            "average_value": trend.average_value,
            "change_percentage": trend.change_percentage,
            "num_data_points": len(trend.data_points),
        }

        if include_metadata:
            row["metadata"] = json.dumps(trend.metadata) if trend.metadata else ""

        return row

    def _format_timestamp(self, timestamp: datetime) -> Union[str, int]:
        """
        Format a timestamp according to the configured format.

        Args:
            timestamp: datetime object to format

        Returns:
            Formatted timestamp (ISO 8601 string or Unix timestamp)
        """
        return self._format_timestamp_with_format(timestamp, self.timestamp_format)

    def _format_timestamp_with_format(self, timestamp: datetime, timestamp_format: str) -> Union[str, int]:
        """
        Format a timestamp with a specific format.

        Args:
            timestamp: datetime object to format
            timestamp_format: Format for timestamps ("iso8601" or "unix")

        Returns:
            Formatted timestamp (ISO 8601 string or Unix timestamp)
        """
        if timestamp_format == "unix":
            return int(timestamp.timestamp())
        else:  # iso8601 or default
            return timestamp.isoformat()


__all__ = ["AnalyticsExporter"]
