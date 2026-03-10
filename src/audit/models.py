"""Data models for the audit system."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


QUALITY_DIMENSIONS = [
    "voice_consistency",
    "content_depth",
    "engagement_quality",
    "factual_accuracy",
    "mission_alignment",
]

SUGGESTION_CATEGORIES = ["bad_pattern", "new_rule", "topic_adjustment", "tone_correction"]

SEVERITY_LEVELS = ["low", "medium", "high"]

TARGET_SECTIONS = ["BAD", "Rules", "Topics"]

TREND_DIRECTIONS = ["improving", "stable", "declining"]


@dataclass
class QualityScore:
    """Score for a single quality dimension."""

    dimension: str
    score: float  # 0.0 to 1.0
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.dimension not in QUALITY_DIMENSIONS:
            raise ValueError(
                f"Invalid dimension '{self.dimension}'. Must be one of {QUALITY_DIMENSIONS}"
            )
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be between 0.0 and 1.0, got {self.score}")


@dataclass
class ImprovementSuggestion:
    """A concrete suggestion for improving Freeman's outputs."""

    suggestion_id: str
    category: str  # "bad_pattern", "new_rule", "topic_adjustment", "tone_correction"
    description: str
    severity: str  # "low", "medium", "high"
    auto_applicable: bool
    target_section: str  # "BAD", "Rules", "Topics"
    suggested_text: str
    evidence: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        if self.category not in SUGGESTION_CATEGORIES:
            raise ValueError(
                f"Invalid category '{self.category}'. Must be one of {SUGGESTION_CATEGORIES}"
            )
        if self.severity not in SEVERITY_LEVELS:
            raise ValueError(
                f"Invalid severity '{self.severity}'. Must be one of {SEVERITY_LEVELS}"
            )
        if self.target_section not in TARGET_SECTIONS:
            raise ValueError(
                f"Invalid target_section '{self.target_section}'. Must be one of {TARGET_SECTIONS}"
            )


@dataclass
class AuditReport:
    """Summary report for an audit period."""

    report_id: str
    period_start: datetime
    period_end: datetime
    outputs_reviewed: int
    quality_scores: List[QualityScore]
    overall_score: float
    trend_direction: str  # "improving", "stable", "declining"
    suggestions: List[ImprovementSuggestion] = field(default_factory=list)
    auto_applied: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.trend_direction not in TREND_DIRECTIONS:
            raise ValueError(
                f"Invalid trend_direction '{self.trend_direction}'. "
                f"Must be one of {TREND_DIRECTIONS}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the report to a dictionary."""
        return {
            "report_id": self.report_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "outputs_reviewed": self.outputs_reviewed,
            "quality_scores": [
                {
                    "dimension": qs.dimension,
                    "score": qs.score,
                    "reasoning": qs.reasoning,
                    "timestamp": qs.timestamp.isoformat(),
                    "metadata": qs.metadata,
                }
                for qs in self.quality_scores
            ],
            "overall_score": self.overall_score,
            "trend_direction": self.trend_direction,
            "suggestions": [
                {
                    "suggestion_id": s.suggestion_id,
                    "category": s.category,
                    "description": s.description,
                    "severity": s.severity,
                    "auto_applicable": s.auto_applicable,
                    "target_section": s.target_section,
                    "suggested_text": s.suggested_text,
                    "evidence": s.evidence,
                    "timestamp": s.timestamp.isoformat(),
                }
                for s in self.suggestions
            ],
            "auto_applied": self.auto_applied,
            "metadata": self.metadata,
        }
