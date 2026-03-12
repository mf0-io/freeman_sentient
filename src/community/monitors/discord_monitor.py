"""Discord community monitor using the REST API."""

import logging
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx

from src.community.models import CommunitySnapshot
from src.community.monitors.base import BaseCommunityMonitor

logger = logging.getLogger(__name__)

DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordCommunityMonitor(BaseCommunityMonitor):
    """
    Monitor Discord guilds via the REST API.

    Requires a bot token with guild member and message read permissions.
    Config keys:
        - monitored_guilds: list of guild_id strings
    Env vars:
        - DISCORD_BOT_TOKEN
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._token = os.environ.get("DISCORD_BOT_TOKEN", "")
        self._monitored_guilds: List[str] = config.get("monitored_guilds", [])
        self.config["monitored_ids"] = self._monitored_guilds

    @property
    def platform_name(self) -> str:
        return "discord"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bot {self._token}",
            "Content-Type": "application/json",
        }

    async def _api_get(
        self, path: str, params: Dict[str, Any] = None
    ) -> Any:
        """Make a Discord REST API GET request."""
        url = f"{DISCORD_API_BASE}{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    url, headers=self._headers(), params=params or {}
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Discord API request failed for {path}: {e}")
            return {}

    async def _get_guild_channels(self, guild_id: str) -> List[Dict]:
        """Get text channels for a guild."""
        channels = await self._api_get(f"/guilds/{guild_id}/channels")
        if not isinstance(channels, list):
            return []
        # Filter to text channels (type 0)
        return [c for c in channels if c.get("type") == 0]

    async def _get_channel_messages(
        self, channel_id: str, limit: int = 100
    ) -> List[Dict]:
        """Get recent messages from a channel."""
        messages = await self._api_get(
            f"/channels/{channel_id}/messages", {"limit": min(limit, 100)}
        )
        if not isinstance(messages, list):
            return []
        return messages

    async def snapshot_community(self, community_id: str) -> CommunitySnapshot:
        """Snapshot a Discord guild: info + member count + recent messages."""
        guild = await self._api_get(f"/guilds/{community_id}?with_counts=true")
        if not guild:
            logger.warning(f"Could not fetch guild {community_id}")
            return CommunitySnapshot(
                community_id=community_id,
                platform=self.platform_name,
                name=community_id,
                member_count=0,
                active_members_24h=0,
                messages_24h=0,
                sentiment_score=0.0,
                top_topics=[],
                engagement_rate=0.0,
                growth_rate_weekly=0.0,
                timestamp=datetime.now(timezone.utc),
                is_own=True,
            )

        member_count = guild.get("approximate_member_count", 0)
        online_count = guild.get("approximate_presence_count", 0)

        messages = await self.get_recent_messages(community_id, limit=200)

        now = datetime.now(timezone.utc)
        cutoff_24h = now - timedelta(hours=24)
        recent_messages = []
        active_authors = set()
        topic_counter: Counter = Counter()

        for msg in messages:
            ts = msg.get("timestamp")
            if ts and isinstance(ts, datetime) and ts > cutoff_24h:
                recent_messages.append(msg)

            author = msg.get("author", "")
            if author:
                active_authors.add(author)

            text = msg.get("text", "")
            words = [w.lower() for w in text.split() if len(w) > 4]
            topic_counter.update(words)

        top_topics = [word for word, _ in topic_counter.most_common(10)]
        messages_24h = len(recent_messages)
        active_24h = len(active_authors)
        engagement = active_24h / member_count if member_count > 0 else 0.0

        return CommunitySnapshot(
            community_id=community_id,
            platform=self.platform_name,
            name=guild.get("name", community_id),
            member_count=member_count,
            active_members_24h=active_24h,
            messages_24h=messages_24h,
            sentiment_score=0.0,
            top_topics=top_topics,
            engagement_rate=min(engagement, 1.0),
            growth_rate_weekly=0.0,
            timestamp=now,
            is_own=True,
            metadata={
                "online_count": online_count,
                "guild_id": community_id,
                "description": guild.get("description", ""),
            },
        )

    async def get_recent_messages(
        self, community_id: str, limit: int = 100
    ) -> List[Dict]:
        """Fetch recent messages across guild text channels."""
        channels = await self._get_guild_channels(community_id)
        all_messages = []

        per_channel_limit = max(limit // max(len(channels), 1), 10)

        for channel in channels[:10]:  # Cap at 10 channels
            raw_messages = await self._get_channel_messages(
                channel["id"], limit=per_channel_limit
            )
            for msg in raw_messages:
                author = msg.get("author", {})
                ts_str = msg.get("timestamp", "")
                try:
                    ts = datetime.fromisoformat(ts_str.replace("+00:00", "+00:00"))
                except (ValueError, AttributeError):
                    ts = datetime.now(timezone.utc)

                all_messages.append(
                    {
                        "message_id": msg.get("id"),
                        "text": msg.get("content", ""),
                        "author": author.get("username", ""),
                        "author_id": author.get("id", ""),
                        "channel_id": channel["id"],
                        "channel_name": channel.get("name", ""),
                        "timestamp": ts,
                    }
                )

        all_messages.sort(key=lambda m: m.get("timestamp", datetime.min), reverse=True)
        return all_messages[:limit]

    async def get_member_stats(self, community_id: str) -> Dict[str, Any]:
        """Get member statistics for a Discord guild."""
        guild = await self._api_get(f"/guilds/{community_id}?with_counts=true")
        messages = await self.get_recent_messages(community_id, limit=200)

        author_counts: Counter = Counter()
        for msg in messages:
            author = msg.get("author", "unknown")
            author_counts[author] += 1

        return {
            "total_members": guild.get("approximate_member_count", 0),
            "online_members": guild.get("approximate_presence_count", 0),
            "recent_active_authors": len(author_counts),
            "top_authors": dict(author_counts.most_common(20)),
            "messages_sampled": len(messages),
        }
