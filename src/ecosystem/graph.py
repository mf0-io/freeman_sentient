"""Ecosystem Graph — knowledge graph of Freeman's product portfolio."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.ecosystem.models import (
    ProductMetrics,
    ProductNode,
    ProductRelationship,
    ProductStage,
)

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config/ecosystem_config.yaml"


class EcosystemGraph:
    """
    Knowledge graph of Freeman's product ecosystem.

    Loads product definitions from YAML config and provides
    CRUD operations, relationship queries, and ecosystem-level
    summaries for the daily briefing.
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self._products: Dict[str, ProductNode] = {}
        self._relationships: List[ProductRelationship] = []

    async def initialize(self) -> None:
        """Load products and relationships from YAML config."""
        path = Path(self.config_path)
        if not path.exists():
            logger.warning(f"Ecosystem config not found: {self.config_path}")
            return

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            for p in data.get("products", []):
                node = ProductNode(
                    product_id=p["id"],
                    name=p["name"],
                    description=p.get("description", ""),
                    stage=ProductStage(p.get("stage", "concept")),
                    platforms=p.get("platforms", []),
                    team=p.get("team", []),
                    dependencies=p.get("dependencies", []),
                    tags=p.get("tags", []),
                    url=p.get("url"),
                )
                self._products[node.product_id] = node

            for r in data.get("relationships", []):
                rel = ProductRelationship(
                    source_id=r["source"],
                    target_id=r["target"],
                    relationship_type=r.get("type", "synergy"),
                    strength=r.get("strength", 0.5),
                    description=r.get("description", ""),
                )
                self._relationships.append(rel)

            logger.info(
                f"Loaded {len(self._products)} products, "
                f"{len(self._relationships)} relationships"
            )
        except Exception as e:
            logger.error(f"Failed to load ecosystem config: {e}")

    async def get_product(self, product_id: str) -> Optional[ProductNode]:
        return self._products.get(product_id)

    async def list_products(
        self, stage: Optional[ProductStage] = None
    ) -> List[ProductNode]:
        products = list(self._products.values())
        if stage:
            products = [p for p in products if p.stage == stage]
        return products

    async def update_product(
        self, product_id: str, updates: Dict[str, Any]
    ) -> Optional[ProductNode]:
        node = self._products.get(product_id)
        if not node:
            return None

        from datetime import datetime

        for key, value in updates.items():
            if key == "stage":
                node.stage = ProductStage(value)
            elif key == "metrics":
                node.metrics = ProductMetrics(**value)
            elif hasattr(node, key):
                setattr(node, key, value)

        node.updated_at = datetime.utcnow()
        return node

    async def update_metrics(
        self, product_id: str, metrics: ProductMetrics
    ) -> None:
        node = self._products.get(product_id)
        if node:
            node.metrics = metrics
            from datetime import datetime
            node.updated_at = datetime.utcnow()

    async def get_relationships(
        self, product_id: str
    ) -> List[ProductRelationship]:
        return [
            r for r in self._relationships
            if r.source_id == product_id or r.target_id == product_id
        ]

    async def get_synergies(self) -> List[ProductRelationship]:
        return [
            r for r in self._relationships
            if r.relationship_type == "synergy"
        ]

    async def get_dependency_chain(
        self, product_id: str
    ) -> List[str]:
        """Get the full dependency chain for a product."""
        visited = set()
        chain = []

        def _traverse(pid):
            if pid in visited:
                return
            visited.add(pid)
            node = self._products.get(pid)
            if node:
                for dep_id in node.dependencies:
                    _traverse(dep_id)
                chain.append(pid)

        _traverse(product_id)
        return chain

    async def get_ecosystem_summary(self) -> Dict[str, Any]:
        """Full ecosystem state for briefing context."""
        stage_counts = {}
        for p in self._products.values():
            stage = p.stage.value
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        products_summary = []
        for p in self._products.values():
            products_summary.append({
                "id": p.product_id,
                "name": p.name,
                "stage": p.stage.value,
                "platforms": p.platforms,
                "team_size": len(p.team),
                "metrics": p.metrics.to_dict() if p.metrics else {},
            })

        synergies = await self.get_synergies()

        return {
            "total_products": len(self._products),
            "stages": stage_counts,
            "products": products_summary,
            "synergies": [
                {
                    "source": s.source_id,
                    "target": s.target_id,
                    "strength": s.strength,
                    "description": s.description,
                }
                for s in synergies
            ],
            "active_platforms": list(set(
                p for node in self._products.values()
                for p in node.platforms
            )),
        }

    async def get_stats(self) -> Dict[str, Any]:
        return {
            "total_products": len(self._products),
            "total_relationships": len(self._relationships),
            "products_by_stage": {
                stage.value: sum(
                    1 for p in self._products.values()
                    if p.stage == stage
                )
                for stage in ProductStage
            },
        }
