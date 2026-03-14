"""Data models for product hypothesis testing."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class HypothesisStatus(str, Enum):
    ACTIVE = "active"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    INCONCLUSIVE = "inconclusive"
    PAUSED = "paused"


@dataclass
class Evidence:
    """A piece of evidence supporting or contradicting a hypothesis."""
    evidence_id: str
    hypothesis_id: str
    direction: str  # supports, contradicts, neutral
    source: str  # community:tg_main, analytics:engagement, intelligence:briefing
    description: str
    data_point: Any = None
    confidence: float = 0.5  # 0.0-1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class Hypothesis:
    """A testable product hypothesis."""
    hypothesis_id: str
    product_id: str  # references EcosystemGraph
    statement: str
    success_criteria: str
    metric_name: Optional[str] = None
    metric_target: Optional[float] = None
    status: HypothesisStatus = HypothesisStatus.ACTIVE
    evidence: List[Evidence] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def support_score(self) -> float:
        """Weighted ratio of supporting vs contradicting evidence."""
        if not self.evidence:
            return 0.5

        support = sum(
            e.confidence for e in self.evidence if e.direction == "supports"
        )
        contradict = sum(
            e.confidence for e in self.evidence if e.direction == "contradicts"
        )
        total = support + contradict
        if total == 0:
            return 0.5
        return round(support / total, 3)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        d["deadline"] = self.deadline.isoformat() if self.deadline else None
        d["support_score"] = self.support_score()
        d["evidence"] = [e.to_dict() for e in self.evidence]
        return d


@dataclass
class HypothesisReport:
    """Generated report on a hypothesis's status."""
    report_id: str
    hypothesis: Hypothesis
    evidence_summary: Dict[str, int]  # {supports: N, contradicts: M, neutral: K}
    recommendation: str
    next_steps: List[str]
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "hypothesis_id": self.hypothesis.hypothesis_id,
            "statement": self.hypothesis.statement,
            "status": self.hypothesis.status.value,
            "support_score": self.hypothesis.support_score(),
            "evidence_summary": self.evidence_summary,
            "recommendation": self.recommendation,
            "next_steps": self.next_steps,
            "generated_at": self.generated_at.isoformat(),
        }
