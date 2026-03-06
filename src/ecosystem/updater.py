"""Dynamic ecosystem graph updater from analytics and community data."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from src.ecosystem.graph import EcosystemGraph
from src.ecosystem.models import ProductMetrics

logger = logging.getLogger(__name__)


class EcosystemUpdater:
    """
    Updates the ecosystem graph with live data from analytics
    and community intelligence systems.

    Called periodically to keep product metrics current.
    """

    def __init__(self, graph: EcosystemGraph):
        self.graph = graph

    async def update_from_analytics(
        self,
        product_id: str,
        analytics_data: Dict[str, Any],
    ) -> None:
        """Update product metrics from analytics manager data."""
        try:
            metrics = ProductMetrics(
                users=analytics_data.get("unique_users"),
                engagement_rate=analytics_data.get("engagement_rate"),
                growth_rate_weekly=analytics_data.get("growth_rate"),
                custom=analytics_data.get("custom_metrics", {}),
                measured_at=datetime.utcnow(),
            )
            await self.graph.update_metrics(product_id, metrics)
            logger.info(f"Updated metrics for {product_id}")
        except Exception as e:
            logger.error(f"Failed to update {product_id} from analytics: {e}")

    async def update_from_community(
        self,
        product_id: str,
        community_data: Dict[str, Any],
    ) -> None:
        """Update product metrics from community snapshot data."""
        try:
            product = await self.graph.get_product(product_id)
            if not product:
                return

            updates = {}
            if "member_count" in community_data:
                product.metrics.users = community_data["member_count"]
            if "engagement_rate" in community_data:
                product.metrics.engagement_rate = community_data["engagement_rate"]
            if "growth_rate_weekly" in community_data:
                product.metrics.growth_rate_weekly = community_data["growth_rate_weekly"]

            product.metrics.measured_at = datetime.utcnow()
            logger.info(f"Updated {product_id} from community data")
        except Exception as e:
            logger.error(f"Failed to update {product_id} from community: {e}")

    async def stage_transition(
        self,
        product_id: str,
        new_stage: str,
        reason: str = "",
    ) -> Optional[Dict[str, Any]]:
        """Record a product stage transition."""
        product = await self.graph.get_product(product_id)
        if not product:
            return None

        old_stage = product.stage.value
        await self.graph.update_product(product_id, {"stage": new_stage})

        transition = {
            "product_id": product_id,
            "old_stage": old_stage,
            "new_stage": new_stage,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.info(
            f"Product {product_id}: {old_stage} -> {new_stage}"
            f"{' (' + reason + ')' if reason else ''}"
        )
        return transition
