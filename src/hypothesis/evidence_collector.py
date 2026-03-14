"""Automatic evidence collection from community and analytics data."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.hypothesis.models import Evidence, Hypothesis

logger = logging.getLogger(__name__)


class EvidenceCollector:
    """
    Automatically collects evidence for hypotheses from
    community snapshots, analytics metrics, and intelligence briefings.
    """

    def __init__(
        self,
        analytics_manager=None,
        ecosystem_graph=None,
    ):
        self.analytics = analytics_manager
        self.ecosystem = ecosystem_graph

    async def collect_for_hypothesis(
        self,
        hypothesis: Hypothesis,
        community_data: Optional[Dict[str, Any]] = None,
        analytics_data: Optional[Dict[str, Any]] = None,
        briefing_data: Optional[Dict[str, Any]] = None,
    ) -> List[Evidence]:
        """Collect evidence from all available data sources."""
        evidence_list = []

        if analytics_data and hypothesis.metric_name:
            ev = await self._from_analytics(hypothesis, analytics_data)
            if ev:
                evidence_list.append(ev)

        if community_data:
            evs = await self._from_community(hypothesis, community_data)
            evidence_list.extend(evs)

        if briefing_data:
            ev = await self._from_briefing(hypothesis, briefing_data)
            if ev:
                evidence_list.append(ev)

        return evidence_list

    async def collect_all(
        self,
        hypotheses: List[Hypothesis],
        community_data: Optional[Dict[str, Any]] = None,
        analytics_data: Optional[Dict[str, Any]] = None,
        briefing_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, List[Evidence]]:
        """Collect evidence for all active hypotheses."""
        results = {}
        for h in hypotheses:
            evs = await self.collect_for_hypothesis(
                h, community_data, analytics_data, briefing_data
            )
            if evs:
                results[h.hypothesis_id] = evs
        return results

    async def _from_analytics(
        self,
        hypothesis: Hypothesis,
        data: Dict[str, Any],
    ) -> Optional[Evidence]:
        """Extract evidence from analytics metrics."""
        metric_value = data.get(hypothesis.metric_name)
        if metric_value is None:
            return None

        if hypothesis.metric_target is not None:
            progress = metric_value / hypothesis.metric_target
            if progress >= 1.0:
                direction = "supports"
                confidence = min(1.0, progress * 0.8)
            elif progress >= 0.5:
                direction = "neutral"
                confidence = 0.4
            else:
                direction = "contradicts"
                confidence = min(1.0, (1 - progress) * 0.6)
        else:
            direction = "neutral"
            confidence = 0.3

        return Evidence(
            evidence_id=f"ev_{uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            direction=direction,
            source=f"analytics:{hypothesis.metric_name}",
            description=(
                f"Metric '{hypothesis.metric_name}' = {metric_value}"
                f" (target: {hypothesis.metric_target})"
            ),
            data_point=metric_value,
            confidence=confidence,
        )

    async def _from_community(
        self,
        hypothesis: Hypothesis,
        data: Dict[str, Any],
    ) -> List[Evidence]:
        """Extract evidence from community snapshot data."""
        evidence_list = []

        sentiment = data.get("sentiment_score")
        if sentiment is not None:
            direction = (
                "supports" if sentiment > 0.2
                else "contradicts" if sentiment < -0.2
                else "neutral"
            )
            evidence_list.append(Evidence(
                evidence_id=f"ev_{uuid4().hex[:8]}",
                hypothesis_id=hypothesis.hypothesis_id,
                direction=direction,
                source="community:sentiment",
                description=f"Community sentiment: {sentiment:.2f}",
                data_point=sentiment,
                confidence=abs(sentiment) * 0.7,
            ))

        engagement = data.get("engagement_rate")
        if engagement is not None:
            direction = (
                "supports" if engagement > 0.1
                else "contradicts" if engagement < 0.02
                else "neutral"
            )
            evidence_list.append(Evidence(
                evidence_id=f"ev_{uuid4().hex[:8]}",
                hypothesis_id=hypothesis.hypothesis_id,
                direction=direction,
                source="community:engagement",
                description=f"Engagement rate: {engagement:.2%}",
                data_point=engagement,
                confidence=0.5,
            ))

        return evidence_list

    async def _from_briefing(
        self,
        hypothesis: Hypothesis,
        data: Dict[str, Any],
    ) -> Optional[Evidence]:
        """Extract evidence from daily intelligence briefing."""
        market_signals = data.get("market_signals", [])
        relevant = [
            s for s in market_signals
            if hypothesis.product_id.lower() in str(s).lower()
            or any(
                kw in str(s).lower()
                for kw in hypothesis.statement.lower().split()[:3]
            )
        ]

        if not relevant:
            return None

        return Evidence(
            evidence_id=f"ev_{uuid4().hex[:8]}",
            hypothesis_id=hypothesis.hypothesis_id,
            direction="neutral",
            source="intelligence:briefing",
            description=f"Related market signals: {len(relevant)} found",
            data_point=relevant[:3],
            confidence=0.4,
        )
