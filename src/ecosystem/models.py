"""Data models for the product ecosystem graph."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ProductStage(str, Enum):
    CONCEPT = "concept"
    MVP = "mvp"
    BETA = "beta"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"


@dataclass
class ProductMetrics:
    """Quantitative metrics for a product."""
    users: Optional[int] = None
    revenue: Optional[float] = None
    engagement_rate: Optional[float] = None
    growth_rate_weekly: Optional[float] = None
    retention_rate: Optional[float] = None
    custom: Dict[str, Any] = field(default_factory=dict)
    measured_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["measured_at"] = self.measured_at.isoformat()
        return d


@dataclass
class ProductNode:
    """A product in the ecosystem graph."""
    product_id: str
    name: str
    description: str
    stage: ProductStage
    platforms: List[str] = field(default_factory=list)
    team: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metrics: ProductMetrics = field(default_factory=ProductMetrics)
    tags: List[str] = field(default_factory=list)
    url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["stage"] = self.stage.value
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        d["metrics"] = self.metrics.to_dict()
        return d


@dataclass
class ProductRelationship:
    """A relationship between two products."""
    source_id: str
    target_id: str
    relationship_type: str  # depends_on, synergy, feeds_into, competes_with
    strength: float = 0.5  # 0.0-1.0
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
