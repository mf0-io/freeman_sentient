"""Base community monitor interface for platform-specific community tracking."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.community.models import CommunitySnapshot

logger = logging.getLogger(__name__)


class BaseCommunityMonitor(ABC):
    """
    Abstract base for community monitors.

    Each monitor connects to a platform API, collects community metrics
    (member counts, messages, engagement), and produces CommunitySnapshots.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._last_sync: Optional[datetime] = None

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return platform identifier (telegram, discord, twitter)."""
        ...

    @abstractmethod
    async def snapshot_community(self, community_id: str) -> CommunitySnapshot:
        """
        Take a point-in-time snapshot of a community.

        Args:
            community_id: Platform-specific community identifier.

        Returns:
            CommunitySnapshot with current metrics.
        """
        ...

    @abstractmethod
    async def get_recent_messages(
        self, community_id: str, limit: int = 100
    ) -> List[Dict]:
        """
        Fetch recent messages from the community.

        Args:
            community_id: Platform-specific community identifier.
            limit: Maximum number of messages to return.

        Returns:
            List of message dicts with at least: text, author, timestamp.
        """
        ...

    @abstractmethod
    async def get_member_stats(self, community_id: str) -> Dict[str, Any]:
        """
        Get member statistics for the community.

        Args:
            community_id: Platform-specific community identifier.

        Returns:
            Dict with member counts, activity breakdowns, etc.
        """
        ...

    async def sync(self) -> Dict[str, Any]:
        """Full sync cycle: snapshot all monitored communities."""
        community_ids = self.config.get("monitored_ids", [])
        snapshots = []
        errors = []

        for cid in community_ids:
            try:
                snapshot = await self.snapshot_community(cid)
                snapshots.append(snapshot)
            except Exception as e:
                logger.error(
                    f"{self.platform_name}: failed to snapshot {cid}: {e}"
                )
                errors.append({"community_id": cid, "error": str(e)})

        self._last_sync = datetime.utcnow()

        logger.info(
            f"{self.platform_name}: synced {len(snapshots)} communities, "
            f"{len(errors)} errors"
        )
        return {
            "status": "ok" if not errors else "partial",
            "platform": self.platform_name,
            "snapshots": len(snapshots),
            "errors": errors,
            "synced_at": self._last_sync.isoformat(),
        }
