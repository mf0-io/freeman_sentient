"""
Data models for the Intelligence System.

Defines the core data structures for research insights and daily briefings
produced by the multi-LLM research pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class SourceInsight:
    """A single research insight from a provider."""

    provider: str
    domain: str
    title: str
    summary: str
    key_findings: List[str]
    confidence: float
    sources: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DailyBriefing:
    """Assembled daily briefing combining insights from all providers."""

    briefing_id: str
    date: datetime
    insights: List[SourceInsight]
    synthesis: str
    key_topics: List[str]
    content_suggestions: List[Dict[str, Any]]
    strategic_recommendations: List[str]
    market_signals: List[Dict[str, Any]] = field(default_factory=list)
    competitor_activity: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the briefing to a dictionary."""
        return {
            "briefing_id": self.briefing_id,
            "date": self.date.isoformat(),
            "insights": [
                {
                    "provider": i.provider,
                    "domain": i.domain,
                    "title": i.title,
                    "summary": i.summary,
                    "key_findings": i.key_findings,
                    "confidence": i.confidence,
                    "sources": i.sources,
                    "timestamp": i.timestamp.isoformat(),
                    "metadata": i.metadata,
                }
                for i in self.insights
            ],
            "synthesis": self.synthesis,
            "key_topics": self.key_topics,
            "content_suggestions": self.content_suggestions,
            "strategic_recommendations": self.strategic_recommendations,
            "market_signals": self.market_signals,
            "competitor_activity": self.competitor_activity,
            "metadata": self.metadata,
        }

    def get_content_seeds(self) -> List[Dict[str, str]]:
        """Extract topics and angles for ContentIdeator.

        Returns a list of dicts with 'topic' and 'angle' keys derived from
        insights, content suggestions, and strategic recommendations.
        """
        seeds: List[Dict[str, str]] = []

        for suggestion in self.content_suggestions:
            topic = suggestion.get("topic", "")
            angle = suggestion.get("angle", suggestion.get("description", ""))
            if topic:
                seeds.append({"topic": topic, "angle": angle})

        for insight in self.insights:
            if insight.key_findings:
                seeds.append({
                    "topic": insight.title,
                    "angle": insight.key_findings[0],
                })

        for rec in self.strategic_recommendations:
            seeds.append({
                "topic": "Strategic Direction",
                "angle": rec,
            })

        return seeds
