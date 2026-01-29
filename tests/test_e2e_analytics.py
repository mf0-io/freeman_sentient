"""
End-to-End Verification Script for Interaction Analytics System

This script provides comprehensive verification of the entire analytics workflow:
1. Simulate user interaction via memory system hooks
2. Verify metrics are tracked automatically
3. Verify sentiment is analyzed
4. Verify trends are calculated
5. Export analytics report and validate format

Run this script to verify the entire analytics system is working correctly.
"""

import sys
import json
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analytics.analytics_manager import AnalyticsManager
from src.analytics.analytics_exporter import AnalyticsExporter
from config.analytics_config import (
    MetricType,
    SentimentCategory,
    AggregationPeriod,
    TrendDirection,
)


class E2EVerifier:
    """End-to-end verification for analytics system"""

    def __init__(self):
        self.manager = AnalyticsManager()
        self.exporter = AnalyticsExporter()
        self.verification_results = []

    def log(self, step: str, status: str, details: str = ""):
        """Log a verification step"""
        result = {
            "step": step,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.verification_results.append(result)
        status_icon = "✓" if status == "PASS" else "✗" if status == "FAIL" else "ℹ"
        print(f"{status_icon} {step}: {status}")
        if details:
            print(f"   {details}")

    def verify_1_simulate_user_interactions(self):
        """
        STEP 1: Simulate user interactions via memory system hooks

        This tests the integration points where a memory system would call
        into the analytics system through the hook system.
        """
        print("\n" + "=" * 60)
        print("STEP 1: Simulating user interactions via memory system")
        print("=" * 60)

        now = datetime.now()

        # Scenario 1: User sends a message
        try:
            self.manager.on_message_sent(
                user_id="user_alex",
                metadata={"platform": "telegram"},
                timestamp=now - timedelta(minutes=30),
            )
            self.log(
                "1.1 - Message sent tracking",
                "PASS",
                "Tracked message sent event via hook",
            )
        except Exception as e:
            self.log("1.1 - Message sent tracking", "FAIL", str(e))
            return False

        # Scenario 2: Freeman responds to the message
        try:
            self.manager.on_message_responded(
                user_id="user_alex",
                metadata={"response_time_ms": 2500},
                timestamp=now - timedelta(minutes=29),
            )
            self.log(
                "1.2 - Message responded tracking",
                "PASS",
                "Tracked message responded event via hook",
            )
        except Exception as e:
            self.log("1.2 - Message responded tracking", "FAIL", str(e))
            return False

        # Scenario 3: Start a conversation
        try:
            self.manager.on_conversation_started(
                conversation_id="conv_001",
                user_id="user_alex",
                metadata={"platform": "telegram"},
                timestamp=now - timedelta(minutes=30),
            )
            self.log(
                "1.3 - Conversation started",
                "PASS",
                "Started tracking conversation via hook",
            )
        except Exception as e:
            self.log("1.3 - Conversation started", "FAIL", str(e))
            return False

        # Scenario 4: Add messages to conversation
        try:
            self.manager.on_conversation_message_added(
                conversation_id="conv_001",
                timestamp=now - timedelta(minutes=29),
            )
            self.manager.on_conversation_message_added(
                conversation_id="conv_001",
                timestamp=now - timedelta(minutes=28),
            )
            self.log(
                "1.4 - Conversation messages added",
                "PASS",
                "Added 2 messages to conversation via hook",
            )
        except Exception as e:
            self.log("1.4 - Conversation messages added", "FAIL", str(e))
            return False

        # Scenario 5: End conversation
        try:
            self.manager.on_conversation_ended(
                conversation_id="conv_001",
                timestamp=now - timedelta(minutes=25),
            )
            self.log(
                "1.5 - Conversation ended",
                "PASS",
                "Ended conversation tracking via hook",
            )
        except Exception as e:
            self.log("1.5 - Conversation ended", "FAIL", str(e))
            return False

        # Scenario 6: Analyze sentiment from user message
        try:
            sentiment = self.manager.on_sentiment_analyzed(
                text="This is amazing! I love how Freeman responds!",
                user_id="user_alex",
                metadata={"conversation_id": "conv_001"},
                timestamp=now - timedelta(minutes=30),
            )
            if sentiment.score > 0:
                self.log(
                    "1.6 - Sentiment analyzed",
                    "PASS",
                    f"Positive sentiment detected (score: {sentiment.score:.2f}, category: {sentiment.category.value})",
                )
            else:
                self.log(
                    "1.6 - Sentiment analyzed",
                    "FAIL",
                    f"Expected positive sentiment, got {sentiment.category.value}",
                )
                return False
        except Exception as e:
            self.log("1.6 - Sentiment analyzed", "FAIL", str(e))
            return False

        # Scenario 7: Record custom metric
        try:
            self.manager.on_metric_recorded(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                value=85.0,
                user_id="user_alex",
                metadata={"platform": "telegram"},
                timestamp=now - timedelta(minutes=30),
            )
            self.log(
                "1.7 - Custom metric recorded",
                "PASS",
                "Recorded engagement score metric via hook",
            )
        except Exception as e:
            self.log("1.7 - Custom metric recorded", "FAIL", str(e))
            return False

        return True

    def verify_2_metrics_tracked_automatically(self):
        """
        STEP 2: Verify metrics are tracked automatically

        After simulating interactions, verify that all metrics were
        automatically captured and stored correctly.
        """
        print("\n" + "=" * 60)
        print("STEP 2: Verifying metrics are tracked automatically")
        print("=" * 60)

        # Check message tracking
        try:
            response_rate = self.manager.calculate_response_rate(user_id="user_alex")
            if response_rate == 100.0:
                self.log(
                    "2.1 - Response rate tracked",
                    "PASS",
                    f"Response rate: {response_rate}%",
                )
            else:
                self.log(
                    "2.1 - Response rate tracked",
                    "FAIL",
                    f"Expected 100% response rate, got {response_rate}%",
                )
                return False
        except Exception as e:
            self.log("2.1 - Response rate tracked", "FAIL", str(e))
            return False

        # Check conversation tracking
        try:
            conv_stats = self.manager.get_conversation_stats("conv_001")
            if conv_stats and conv_stats["message_count"] == 3:
                self.log(
                    "2.2 - Conversation metrics tracked",
                    "PASS",
                    f"Conversation has {conv_stats['message_count']} messages",
                )
            else:
                self.log(
                    "2.2 - Conversation metrics tracked",
                    "FAIL",
                    f"Expected 3 messages, got {conv_stats.get('message_count', 'N/A')}",
                )
                return False
        except Exception as e:
            self.log("2.2 - Conversation metrics tracked", "FAIL", str(e))
            return False

        # Check engagement metric was stored
        try:
            engagement_metrics = self.manager.get_metrics(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                user_id="user_alex",
            )
            if len(engagement_metrics) == 1 and engagement_metrics[0].value == 85.0:
                self.log(
                    "2.3 - Engagement metric stored",
                    "PASS",
                    f"Engagement score: {engagement_metrics[0].value}",
                )
            else:
                self.log(
                    "2.3 - Engagement metric stored",
                    "FAIL",
                    f"Expected 1 metric with value 85.0, got {len(engagement_metrics)} metrics",
                )
                return False
        except Exception as e:
            self.log("2.3 - Engagement metric stored", "FAIL", str(e))
            return False

        # Check average conversation length
        try:
            avg_length = self.manager.calculate_average_conversation_length(
                user_id="user_alex"
            )
            if avg_length == 3.0:
                self.log(
                    "2.4 - Average conversation length",
                    "PASS",
                    f"Average: {avg_length} messages",
                )
            else:
                self.log(
                    "2.4 - Average conversation length",
                    "FAIL",
                    f"Expected 3.0, got {avg_length}",
                )
                return False
        except Exception as e:
            self.log("2.4 - Average conversation length", "FAIL", str(e))
            return False

        return True

    def verify_3_sentiment_analyzed(self):
        """
        STEP 3: Verify sentiment is analyzed

        Verify that sentiment analysis is working correctly for different
        types of messages and conversations.
        """
        print("\n" + "=" * 60)
        print("STEP 3: Verifying sentiment is analyzed")
        print("=" * 60)

        now = datetime.now()

        # Test positive sentiment
        try:
            positive_result = self.manager.analyze_sentiment(
                text="This is absolutely fantastic! Best experience ever!",
                user_id="user_bob",
                timestamp=now,
            )
            if (
                positive_result.score > 0
                and positive_result.category in [SentimentCategory.POSITIVE, SentimentCategory.VERY_POSITIVE]
            ):
                self.log(
                    "3.1 - Positive sentiment detection",
                    "PASS",
                    f"Score: {positive_result.score:.2f}, Category: {positive_result.category.value}",
                )
            else:
                self.log(
                    "3.1 - Positive sentiment detection",
                    "FAIL",
                    f"Expected positive sentiment, got {positive_result.category.value}",
                )
                return False
        except Exception as e:
            self.log("3.1 - Positive sentiment detection", "FAIL", str(e))
            return False

        # Test negative sentiment
        try:
            negative_result = self.manager.analyze_sentiment(
                text="This is terrible! Very disappointed and unhappy.",
                user_id="user_charlie",
                timestamp=now,
            )
            if (
                negative_result.score < 0
                and negative_result.category in [SentimentCategory.NEGATIVE, SentimentCategory.VERY_NEGATIVE]
            ):
                self.log(
                    "3.2 - Negative sentiment detection",
                    "PASS",
                    f"Score: {negative_result.score:.2f}, Category: {negative_result.category.value}",
                )
            else:
                self.log(
                    "3.2 - Negative sentiment detection",
                    "FAIL",
                    f"Expected negative sentiment, got {negative_result.category.value}",
                )
                return False
        except Exception as e:
            self.log("3.2 - Negative sentiment detection", "FAIL", str(e))
            return False

        # Test conversation sentiment analysis
        try:
            conversation_messages = [
                "I really love this!",
                "This is great work.",
                "Amazing job on this feature.",
            ]
            conv_sentiment = self.manager.analyze_conversation_sentiment(
                messages=conversation_messages,
                conversation_id="conv_002",
                user_id="user_bob",
                timestamp=now,
            )
            if conv_sentiment.score > 0:
                self.log(
                    "3.3 - Conversation sentiment analysis",
                    "PASS",
                    f"Aggregated score: {conv_sentiment.score:.2f}, Category: {conv_sentiment.category.value}",
                )
            else:
                self.log(
                    "3.3 - Conversation sentiment analysis",
                    "FAIL",
                    f"Expected positive conversation sentiment, got {conv_sentiment.category.value}",
                )
                return False
        except Exception as e:
            self.log("3.3 - Conversation sentiment analysis", "FAIL", str(e))
            return False

        return True

    def verify_4_trends_calculated(self):
        """
        STEP 4: Verify trends are calculated

        Generate time-series data and verify that trends are properly
        aggregated and detected.
        """
        print("\n" + "=" * 60)
        print("STEP 4: Verifying trends are calculated")
        print("=" * 60)

        now = datetime.now()

        # Generate time-series data with improving trend
        try:
            for day in range(14):
                timestamp = now - timedelta(days=13 - day)
                value = 50.0 + day * 3  # Increasing values
                self.manager.record_metric(
                    metric_type=MetricType.ENGAGEMENT_SCORE,
                    value=value,
                    user_id="user_diana",
                    timestamp=timestamp,
                )
            self.log(
                "4.1 - Time-series data generated",
                "PASS",
                "Created 14 days of engagement data with improving trend",
            )
        except Exception as e:
            self.log("4.1 - Time-series data generated", "FAIL", str(e))
            return False

        # Aggregate daily trends
        try:
            daily_trends = self.manager.aggregate_metrics_by_period(
                metric_type=MetricType.ENGAGEMENT_SCORE,
                period=AggregationPeriod.DAILY,
                user_id="user_diana",
                start_time=now - timedelta(days=14),
                end_time=now,
            )
            if len(daily_trends) > 0:
                self.log(
                    "4.2 - Daily trend aggregation",
                    "PASS",
                    f"Aggregated {len(daily_trends)} daily trends",
                )
            else:
                self.log(
                    "4.2 - Daily trend aggregation",
                    "FAIL",
                    "No trends were aggregated",
                )
                return False
        except Exception as e:
            self.log("4.2 - Daily trend aggregation", "FAIL", str(e))
            return False

        # Detect trend pattern
        try:
            trend_analysis = self.manager.detect_trend_pattern(daily_trends)
            if (
                trend_analysis
                and trend_analysis["overall_direction"] == TrendDirection.IMPROVING
            ):
                self.log(
                    "4.3 - Trend pattern detection",
                    "PASS",
                    f"Detected {trend_analysis['overall_direction'].value} trend with {trend_analysis['confidence']:.2f} confidence",
                )
            else:
                self.log(
                    "4.3 - Trend pattern detection",
                    "FAIL",
                    f"Expected IMPROVING trend, got {trend_analysis.get('overall_direction', 'None') if trend_analysis else 'None'}",
                )
                return False
        except Exception as e:
            self.log("4.3 - Trend pattern detection", "FAIL", str(e))
            return False

        # Verify trend statistics
        try:
            if trend_analysis:
                stats = (
                    f"Start: {trend_analysis['start_value']:.1f}, "
                    f"End: {trend_analysis['end_value']:.1f}, "
                    f"Change: {trend_analysis['total_change']:.1f} "
                    f"({trend_analysis['total_change_percentage']:.1f}%)"
                )
                self.log(
                    "4.4 - Trend statistics",
                    "PASS",
                    stats,
                )
            else:
                self.log("4.4 - Trend statistics", "FAIL", "No trend analysis data")
                return False
        except Exception as e:
            self.log("4.4 - Trend statistics", "FAIL", str(e))
            return False

        return True

    def verify_5_export_and_validate_report(self):
        """
        STEP 5: Export analytics report and validate format

        Export analytics data in both JSON and CSV formats and validate
        that the exported files are correctly formatted.
        """
        print("\n" + "=" * 60)
        print("STEP 5: Exporting analytics report and validating format")
        print("=" * 60)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Export metrics to JSON
            try:
                metrics = self.manager.get_metrics()
                json_path = os.path.join(tmpdir, "analytics_metrics.json")
                self.exporter.export_metrics_to_json(
                    metrics=metrics,
                    output_file=json_path,
                    include_metadata=True,
                    timestamp_format="ISO8601",
                )
                self.log(
                    "5.1 - JSON metrics export",
                    "PASS",
                    f"Exported {len(metrics)} metrics to JSON",
                )
            except Exception as e:
                self.log("5.1 - JSON metrics export", "FAIL", str(e))
                return False

            # Validate JSON format
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        # Check structure
                        required_keys = ["metric_type", "value", "timestamp"]
                        if all(k in data[0] for k in required_keys):
                            self.log(
                                "5.2 - JSON format validation",
                                "PASS",
                                f"JSON is valid with {len(data)} entries",
                            )
                        else:
                            self.log(
                                "5.2 - JSON format validation",
                                "FAIL",
                                f"Missing required keys in JSON structure",
                            )
                            return False
                    else:
                        self.log(
                            "5.2 - JSON format validation",
                            "FAIL",
                            "JSON data is not a list or is empty",
                        )
                        return False
            except Exception as e:
                self.log("5.2 - JSON format validation", "FAIL", str(e))
                return False

            # Export metrics to CSV
            try:
                csv_path = os.path.join(tmpdir, "analytics_metrics.csv")
                self.exporter.export_metrics_to_csv(
                    metrics=metrics,
                    output_file=csv_path,
                    include_metadata=True,
                )
                self.log(
                    "5.3 - CSV metrics export",
                    "PASS",
                    f"Exported metrics to CSV",
                )
            except Exception as e:
                self.log("5.3 - CSV metrics export", "FAIL", str(e))
                return False

            # Validate CSV format
            try:
                with open(csv_path, "r") as f:
                    csv_content = f.read()
                    lines = csv_content.strip().split("\n")
                    if len(lines) > 1:  # Header + at least 1 data row
                        # Check for required columns
                        headers = lines[0].split(",")
                        required_cols = ["metric_type", "value", "timestamp"]
                        if any(col in headers for col in required_cols):
                            self.log(
                                "5.4 - CSV format validation",
                                "PASS",
                                f"CSV has {len(lines) - 1} data rows with headers",
                            )
                        else:
                            self.log(
                                "5.4 - CSV format validation",
                                "FAIL",
                                "CSV missing required columns",
                            )
                            return False
                    else:
                        self.log(
                            "5.4 - CSV format validation",
                            "FAIL",
                            "CSV is empty or missing data",
                        )
                        return False
            except Exception as e:
                self.log("5.4 - CSV format validation", "FAIL", str(e))
                return False

            # Export full analytics report
            try:
                trend_data = self.manager.aggregate_metrics_by_period(
                    metric_type=MetricType.ENGAGEMENT_SCORE,
                    period=AggregationPeriod.DAILY,
                )
                report_result = self.exporter.export_full_analytics(
                    metrics=metrics,
                    sentiment_results=[],
                    trend_data=trend_data,
                    output_format="json",
                    output_dir=tmpdir,
                )
                self.log(
                    "5.5 - Full analytics report export",
                    "PASS",
                    f"Exported complete analytics report with {len(report_result)} sections",
                )
            except Exception as e:
                self.log("5.5 - Full analytics report export", "FAIL", str(e))
                return False

            # Validate individual report files
            try:
                metrics_path = os.path.join(tmpdir, "metrics.json")
                trends_path = os.path.join(tmpdir, "trends.json")
                if os.path.exists(metrics_path) and os.path.exists(trends_path):
                    self.log(
                        "5.6 - Report file validation",
                        "PASS",
                        "All expected report files were created",
                    )
                else:
                    self.log(
                        "5.6 - Report file validation",
                        "FAIL",
                        "Some expected report files are missing",
                    )
                    return False
            except Exception as e:
                self.log("5.6 - Report file validation", "FAIL", str(e))
                return False

        return True

    def verify_6_serialization_deserialization(self):
        """
        BONUS STEP: Verify serialization and deserialization

        Verify that the entire analytics state can be serialized and
        restored without data loss.
        """
        print("\n" + "=" * 60)
        print("BONUS STEP: Verifying serialization/deserialization")
        print("=" * 60)

        # Serialize manager state
        try:
            state_dict = self.manager.to_dict()
            self.log(
                "6.1 - Manager serialization",
                "PASS",
                "Serialized manager state to dictionary",
            )
        except Exception as e:
            self.log("6.1 - Manager serialization", "FAIL", str(e))
            return False

        # Deserialize and verify
        try:
            restored_manager = AnalyticsManager.from_dict(state_dict)
            self.log(
                "6.2 - Manager deserialization",
                "PASS",
                "Restored manager from dictionary",
            )
        except Exception as e:
            self.log("6.2 - Manager deserialization", "FAIL", str(e))
            return False

        # Verify data integrity
        try:
            # Check metrics were restored
            original_metrics = self.manager.get_metrics()
            restored_metrics = restored_manager.get_metrics()
            if len(original_metrics) == len(restored_metrics):
                self.log(
                    "6.3 - Data integrity verification",
                    "PASS",
                    f"All {len(original_metrics)} metrics restored successfully",
                )
            else:
                self.log(
                    "6.3 - Data integrity verification",
                    "FAIL",
                    f"Metric count mismatch: {len(original_metrics)} vs {len(restored_metrics)}",
                )
                return False
        except Exception as e:
            self.log("6.3 - Data integrity verification", "FAIL", str(e))
            return False

        return True

    def run_verification(self):
        """Run all verification steps"""
        print("\n" + "=" * 60)
        print("END-TO-END VERIFICATION FOR INTERACTION ANALYTICS")
        print("=" * 60)
        print(
            f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        all_passed = True

        # Run each verification step
        all_passed &= self.verify_1_simulate_user_interactions()
        all_passed &= self.verify_2_metrics_tracked_automatically()
        all_passed &= self.verify_3_sentiment_analyzed()
        all_passed &= self.verify_4_trends_calculated()
        all_passed &= self.verify_5_export_and_validate_report()
        all_passed &= self.verify_6_serialization_deserialization()

        # Print summary
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)

        total_steps = len(self.verification_results)
        passed_steps = sum(1 for r in self.verification_results if r["status"] == "PASS")
        failed_steps = sum(1 for r in self.verification_results if r["status"] == "FAIL")

        print(f"Total Steps: {total_steps}")
        print(f"Passed: {passed_steps} ✓")
        print(f"Failed: {failed_steps} ✗")
        print(f"Success Rate: {(passed_steps / total_steps * 100):.1f}%")

        if all_passed:
            print("\n✓ ALL VERIFICATIONS PASSED")
            print("The analytics system is working correctly!")
        else:
            print("\n✗ SOME VERIFICATIONS FAILED")
            print("Please review the failed steps above.")

        # Save verification results
        results_path = "e2e_verification_results.json"
        try:
            with open(results_path, "w") as f:
                json.dump(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "total_steps": total_steps,
                        "passed": passed_steps,
                        "failed": failed_steps,
                        "success_rate": passed_steps / total_steps * 100,
                        "all_passed": all_passed,
                        "results": self.verification_results,
                    },
                    f,
                    indent=2,
                )
            print(f"\nVerification results saved to: {results_path}")
        except Exception as e:
            print(f"\nWarning: Could not save verification results: {e}")

        return all_passed


def main():
    """Main entry point for E2E verification"""
    verifier = E2EVerifier()
    success = verifier.run_verification()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
