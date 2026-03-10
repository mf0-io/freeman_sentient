"""Tracks quality scores over time and detects trends."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.audit.models import QualityScore

logger = logging.getLogger(__name__)


class QualityTracker:
    """Tracks quality scores over time and detects trends."""

    def __init__(self) -> None:
        self._scores: List[QualityScore] = []
        self._by_dimension: Dict[str, List[QualityScore]] = defaultdict(list)

    def record_scores(self, scores: List[QualityScore]) -> None:
        """Store scores in internal time-series.

        Args:
            scores: List of QualityScore objects to record.
        """
        for score in scores:
            self._scores.append(score)
            self._by_dimension[score.dimension].append(score)
        logger.info("Recorded %d quality scores", len(scores))

    def get_trend(
        self, dimension: str, period_days: int = 7
    ) -> Dict[str, Any]:
        """Return trend data for a dimension.

        Args:
            dimension: The quality dimension to analyze.
            period_days: Number of days to look back.

        Returns:
            Dict with keys: direction, avg_score, change_pct, data_points.
        """
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        recent = [
            s for s in self._by_dimension.get(dimension, [])
            if s.timestamp >= cutoff
        ]

        if len(recent) < 2:
            avg = recent[0].score if recent else 0.0
            return {
                "direction": "stable",
                "avg_score": avg,
                "change_pct": 0.0,
                "data_points": len(recent),
            }

        recent_sorted = sorted(recent, key=lambda s: s.timestamp)
        scores = [s.score for s in recent_sorted]
        avg_score = sum(scores) / len(scores)

        # Compare first half vs second half to determine trend
        midpoint = len(scores) // 2
        first_half_avg = sum(scores[:midpoint]) / max(midpoint, 1)
        second_half_avg = sum(scores[midpoint:]) / max(len(scores) - midpoint, 1)

        if first_half_avg > 0:
            change_pct = (second_half_avg - first_half_avg) / first_half_avg
        else:
            change_pct = 0.0

        if change_pct > 0.05:
            direction = "improving"
        elif change_pct < -0.1:
            direction = "declining"
        else:
            direction = "stable"

        return {
            "direction": direction,
            "avg_score": round(avg_score, 4),
            "change_pct": round(change_pct, 4),
            "data_points": len(recent),
        }

    def get_overall_health(self) -> Dict[str, Any]:
        """Dashboard summary of all dimensions.

        Returns:
            Dict with keys:
              - dimensions: {dim: {current, trend, avg}}
              - overall: float (average of latest scores across dimensions)
        """
        dimensions_summary: Dict[str, Any] = {}
        latest_scores: List[float] = []

        for dimension in [
            "voice_consistency",
            "content_depth",
            "engagement_quality",
            "factual_accuracy",
            "mission_alignment",
        ]:
            dim_scores = self._by_dimension.get(dimension, [])
            trend = self.get_trend(dimension)

            if dim_scores:
                current = sorted(dim_scores, key=lambda s: s.timestamp)[-1].score
            else:
                current = 0.0

            latest_scores.append(current)
            dimensions_summary[dimension] = {
                "current": round(current, 4),
                "trend": trend["direction"],
                "avg": trend["avg_score"],
            }

        overall = sum(latest_scores) / max(len(latest_scores), 1)

        return {
            "dimensions": dimensions_summary,
            "overall": round(overall, 4),
        }

    def get_history(
        self,
        dimension: Optional[str] = None,
        limit: int = 100,
    ) -> List[QualityScore]:
        """Get recent scores, optionally filtered by dimension.

        Args:
            dimension: If provided, only return scores for this dimension.
            limit: Maximum number of scores to return.

        Returns:
            List of QualityScore objects, most recent first.
        """
        if dimension:
            source = self._by_dimension.get(dimension, [])
        else:
            source = self._scores

        sorted_scores = sorted(source, key=lambda s: s.timestamp, reverse=True)
        return sorted_scores[:limit]
