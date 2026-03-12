"""Engagement pattern detection and anomaly analysis."""

import logging
import math
import uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.community.models import CommunitySnapshot, EngagementPattern

logger = logging.getLogger(__name__)

VALID_PATTERN_TYPES = (
    "peak_hours",
    "topic_resonance",
    "growth_trigger",
    "decline_trigger",
)


class EngagementPatternAnalyzer:
    """Detects engagement patterns and anomalies in community data."""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._anomaly_threshold_std = self.config.get("anomaly_threshold_std", 2.0)

    async def analyze_patterns(
        self, snapshots: List[CommunitySnapshot]
    ) -> List[EngagementPattern]:
        """
        Detect engagement patterns across community snapshots.

        Looks for: peak hours, topic resonance, growth triggers, decline triggers.

        Args:
            snapshots: List of community snapshots (ideally time-series).

        Returns:
            List of detected EngagementPattern objects.
        """
        if not snapshots:
            return []

        patterns: List[EngagementPattern] = []

        patterns.extend(self._detect_peak_hours(snapshots))
        patterns.extend(self._detect_topic_resonance(snapshots))
        patterns.extend(self._detect_growth_triggers(snapshots))
        patterns.extend(self._detect_decline_triggers(snapshots))

        return patterns

    def _detect_peak_hours(
        self, snapshots: List[CommunitySnapshot]
    ) -> List[EngagementPattern]:
        """Detect hours with highest engagement."""
        patterns = []
        # Group by community
        by_community: Dict[str, List[CommunitySnapshot]] = defaultdict(list)
        for s in snapshots:
            by_community[s.community_id].append(s)

        for community_id, community_snaps in by_community.items():
            hour_engagement: Dict[int, List[float]] = defaultdict(list)
            for s in community_snaps:
                hour = s.timestamp.hour
                hour_engagement[hour].append(s.engagement_rate)

            if not hour_engagement:
                continue

            hour_averages = {
                h: sum(vals) / len(vals) for h, vals in hour_engagement.items()
            }
            if not hour_averages:
                continue

            overall_avg = sum(hour_averages.values()) / len(hour_averages)
            peak_hours = [
                h for h, avg in hour_averages.items() if avg > overall_avg * 1.3
            ]

            if peak_hours:
                patterns.append(
                    EngagementPattern(
                        pattern_id=str(uuid.uuid4()),
                        community_id=community_id,
                        pattern_type="peak_hours",
                        description=(
                            f"Peak engagement hours detected: "
                            f"{sorted(peak_hours)} (>30% above average)"
                        ),
                        confidence=min(
                            len(community_snaps) / 50, 1.0
                        ),  # More data = higher confidence
                        data_points=[
                            {"hour": h, "avg_engagement": hour_averages[h]}
                            for h in sorted(peak_hours)
                        ],
                        detected_at=datetime.now(timezone.utc),
                    )
                )

        return patterns

    def _detect_topic_resonance(
        self, snapshots: List[CommunitySnapshot]
    ) -> List[EngagementPattern]:
        """Detect topics correlated with higher engagement."""
        patterns = []
        by_community: Dict[str, List[CommunitySnapshot]] = defaultdict(list)
        for s in snapshots:
            by_community[s.community_id].append(s)

        for community_id, community_snaps in by_community.items():
            topic_engagements: Dict[str, List[float]] = defaultdict(list)
            for s in community_snaps:
                for topic in s.top_topics:
                    topic_engagements[topic].append(s.engagement_rate)

            if not community_snaps:
                continue

            overall_avg = sum(s.engagement_rate for s in community_snaps) / len(
                community_snaps
            )

            resonant_topics = []
            for topic, engagements in topic_engagements.items():
                if len(engagements) < 2:
                    continue
                avg_eng = sum(engagements) / len(engagements)
                if avg_eng > overall_avg * 1.2:
                    resonant_topics.append(
                        {"topic": topic, "avg_engagement": avg_eng, "occurrences": len(engagements)}
                    )

            if resonant_topics:
                resonant_topics.sort(
                    key=lambda t: t["avg_engagement"], reverse=True
                )
                patterns.append(
                    EngagementPattern(
                        pattern_id=str(uuid.uuid4()),
                        community_id=community_id,
                        pattern_type="topic_resonance",
                        description=(
                            f"Topics with above-average engagement: "
                            f"{[t['topic'] for t in resonant_topics[:5]]}"
                        ),
                        confidence=min(
                            len(community_snaps) / 30, 1.0
                        ),
                        data_points=resonant_topics[:10],
                        detected_at=datetime.now(timezone.utc),
                    )
                )

        return patterns

    def _detect_growth_triggers(
        self, snapshots: List[CommunitySnapshot]
    ) -> List[EngagementPattern]:
        """Detect periods of above-average growth."""
        patterns = []
        by_community: Dict[str, List[CommunitySnapshot]] = defaultdict(list)
        for s in snapshots:
            by_community[s.community_id].append(s)

        for community_id, community_snaps in by_community.items():
            sorted_snaps = sorted(community_snaps, key=lambda s: s.timestamp)
            if len(sorted_snaps) < 3:
                continue

            growth_rates = [s.growth_rate_weekly for s in sorted_snaps]
            avg_growth = sum(growth_rates) / len(growth_rates)
            if avg_growth == 0:
                continue

            growth_spikes = []
            for i, s in enumerate(sorted_snaps):
                if s.growth_rate_weekly > avg_growth * 1.5:
                    growth_spikes.append(
                        {
                            "timestamp": s.timestamp.isoformat(),
                            "growth_rate": s.growth_rate_weekly,
                            "member_count": s.member_count,
                            "top_topics": s.top_topics[:3],
                        }
                    )

            if growth_spikes:
                patterns.append(
                    EngagementPattern(
                        pattern_id=str(uuid.uuid4()),
                        community_id=community_id,
                        pattern_type="growth_trigger",
                        description=(
                            f"Growth spikes detected: {len(growth_spikes)} periods "
                            f"with >50% above average growth rate"
                        ),
                        confidence=min(len(sorted_snaps) / 20, 1.0),
                        data_points=growth_spikes,
                        detected_at=datetime.now(timezone.utc),
                    )
                )

        return patterns

    def _detect_decline_triggers(
        self, snapshots: List[CommunitySnapshot]
    ) -> List[EngagementPattern]:
        """Detect periods of declining engagement or membership."""
        patterns = []
        by_community: Dict[str, List[CommunitySnapshot]] = defaultdict(list)
        for s in snapshots:
            by_community[s.community_id].append(s)

        for community_id, community_snaps in by_community.items():
            sorted_snaps = sorted(community_snaps, key=lambda s: s.timestamp)
            if len(sorted_snaps) < 3:
                continue

            decline_points = []
            for i in range(1, len(sorted_snaps)):
                prev = sorted_snaps[i - 1]
                curr = sorted_snaps[i]

                engagement_drop = (
                    (prev.engagement_rate - curr.engagement_rate)
                    / prev.engagement_rate
                    if prev.engagement_rate > 0
                    else 0
                )
                member_drop = (
                    (prev.member_count - curr.member_count) / prev.member_count
                    if prev.member_count > 0
                    else 0
                )

                if engagement_drop > 0.2 or member_drop > 0.05:
                    decline_points.append(
                        {
                            "timestamp": curr.timestamp.isoformat(),
                            "engagement_drop_pct": round(engagement_drop * 100, 1),
                            "member_drop_pct": round(member_drop * 100, 1),
                            "top_topics": curr.top_topics[:3],
                        }
                    )

            if decline_points:
                patterns.append(
                    EngagementPattern(
                        pattern_id=str(uuid.uuid4()),
                        community_id=community_id,
                        pattern_type="decline_trigger",
                        description=(
                            f"Decline detected: {len(decline_points)} periods with "
                            f"significant engagement or member drops"
                        ),
                        confidence=min(len(sorted_snaps) / 20, 1.0),
                        data_points=decline_points,
                        detected_at=datetime.now(timezone.utc),
                    )
                )

        return patterns

    async def detect_anomalies(
        self,
        snapshots: List[CommunitySnapshot],
        history: Optional[List[CommunitySnapshot]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect unusual spikes or drops using standard deviation threshold.

        Args:
            snapshots: Current snapshots to evaluate.
            history: Historical snapshots for baseline. If None, uses snapshots themselves.

        Returns:
            List of anomaly dicts with metric name, value, baseline, deviation.
        """
        baseline_data = history if history else snapshots
        if not baseline_data or not snapshots:
            return []

        baseline = self._calculate_baseline(baseline_data)
        anomalies = []

        for snapshot in snapshots:
            for metric_name, (mean, std) in baseline.items():
                if std == 0:
                    continue

                value = getattr(snapshot, metric_name, None)
                if value is None:
                    continue

                deviation = abs(value - mean) / std
                if deviation > self._anomaly_threshold_std:
                    direction = "spike" if value > mean else "drop"
                    anomalies.append(
                        {
                            "community_id": snapshot.community_id,
                            "platform": snapshot.platform,
                            "metric": metric_name,
                            "value": value,
                            "baseline_mean": round(mean, 4),
                            "baseline_std": round(std, 4),
                            "deviation_std": round(deviation, 2),
                            "direction": direction,
                            "timestamp": snapshot.timestamp.isoformat(),
                        }
                    )

        anomalies.sort(key=lambda a: a["deviation_std"], reverse=True)
        return anomalies

    def _calculate_baseline(
        self, history: List[CommunitySnapshot]
    ) -> Dict[str, tuple]:
        """
        Calculate mean and standard deviation for key metrics.

        Args:
            history: Historical snapshots to compute baseline from.

        Returns:
            Dict mapping metric name to (mean, std) tuple.
        """
        metrics = [
            "sentiment_score",
            "engagement_rate",
            "messages_24h",
            "active_members_24h",
            "member_count",
            "growth_rate_weekly",
        ]

        baseline: Dict[str, tuple] = {}

        for metric in metrics:
            values = []
            for s in history:
                v = getattr(s, metric, None)
                if v is not None:
                    values.append(float(v))

            if not values:
                baseline[metric] = (0.0, 0.0)
                continue

            mean = sum(values) / len(values)
            variance = sum((v - mean) ** 2 for v in values) / len(values)
            std = math.sqrt(variance)
            baseline[metric] = (mean, std)

        return baseline
