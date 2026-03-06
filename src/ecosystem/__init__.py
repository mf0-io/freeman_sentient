"""
Product Ecosystem Graph — knowledge graph of Freeman's product portfolio.

Tracks products, their stages, metrics, team assignments, dependencies,
and cross-product synergies. Provides ecosystem-level context for
the daily briefing and hypothesis testing.
"""

from src.ecosystem.models import (
    ProductNode,
    ProductRelationship,
    ProductMetrics,
    ProductStage,
)
from src.ecosystem.graph import EcosystemGraph
from src.ecosystem.updater import EcosystemUpdater

__all__ = [
    "ProductNode",
    "ProductRelationship",
    "ProductMetrics",
    "ProductStage",
    "EcosystemGraph",
    "EcosystemUpdater",
]
