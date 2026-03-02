"""Base collector interface for platform-specific interaction parsers."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.memory.temporal_people_graph import TemporalPeopleGraph

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """
    Abstract base for platform collectors.

    Each collector connects to a platform API, extracts interactions
    (mentions, replies, comments, subscriptions, etc.), and feeds
    them into the TemporalPeopleGraph.
    """

    def __init__(self, graph: TemporalPeopleGraph, config: Dict[str, Any]):
        self.graph = graph
        self.config = config
        self._last_sync: Optional[datetime] = None

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return platform identifier (telegram, twitter, youtube, kickstarter)."""
        ...

    @abstractmethod
    async def collect(self, since: Optional[datetime] = None) -> int:
        """
        Collect interactions from the platform.

        Args:
            since: Only collect interactions after this timestamp.
                   If None, uses last sync time or collects recent window.

        Returns:
            Number of new interactions collected.
        """
        ...

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Check that API credentials are valid."""
        ...

    async def sync(self) -> Dict[str, Any]:
        """Full sync cycle: validate, collect, compute influence."""
        if not await self.validate_credentials():
            logger.error(f"{self.platform_name}: invalid credentials")
            return {"status": "error", "reason": "invalid_credentials"}

        since = self._last_sync
        count = await self.collect(since=since)
        self._last_sync = datetime.utcnow()

        logger.info(f"{self.platform_name}: collected {count} interactions")
        return {
            "status": "ok",
            "platform": self.platform_name,
            "interactions_collected": count,
            "synced_at": self._last_sync.isoformat(),
        }

    async def _ensure_person(
        self,
        name: str,
        platform_user_id: str,
        role: str = "community",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Helper to add/update a person in the graph."""
        return await self.graph.add_person(
            name=name,
            platform=self.platform_name,
            platform_user_id=platform_user_id,
            role=role,
            tags=tags,
            metadata=metadata,
        )

    async def _record_interaction(
        self,
        source_platform_id: str,
        target_platform_id: str,
        interaction_type: str,
        context: str = "",
        weight: float = 1.0,
        sentiment: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Helper to record an interaction between two platform users."""
        source = await self.graph.find_person_by_platform(
            self.platform_name, source_platform_id
        )
        target = await self.graph.find_person_by_platform(
            self.platform_name, target_platform_id
        )

        if not source or not target:
            return None

        return await self.graph.add_interaction(
            source_id=source.person_id,
            target_id=target.person_id,
            interaction_type=interaction_type,
            platform=self.platform_name,
            context=context,
            weight=weight,
            sentiment=sentiment,
            timestamp=timestamp,
            metadata=metadata,
        )
