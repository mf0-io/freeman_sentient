"""Telegram community monitor using the Bot API."""

import logging
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx

from src.community.models import CommunitySnapshot
from src.community.monitors.base import BaseCommunityMonitor

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


class TelegramCommunityMonitor(BaseCommunityMonitor):
    """
    Monitor Telegram communities via the Bot API.

    Requires a bot token with access to the monitored chats.
    Config keys:
        - monitored_chats: list of chat_id strings
    Env vars:
        - TELEGRAM_BOT_TOKEN
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self._base_url = TELEGRAM_API_BASE.format(token=self._token)
        self._monitored_chats: List[str] = config.get("monitored_chats", [])
        self.config["monitored_ids"] = self._monitored_chats

    @property
    def platform_name(self) -> str:
        return "telegram"

    async def _api_call(
        self, method: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make a Telegram Bot API call."""
        url = f"{self._base_url}/{method}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params or {})
                resp.raise_for_status()
                data = resp.json()
                if not data.get("ok"):
                    logger.error(
                        f"Telegram API error on {method}: {data.get('description')}"
                    )
                    return {}
                return data.get("result", {})
        except httpx.HTTPError as e:
            logger.error(f"Telegram API request failed for {method}: {e}")
            return {}

    async def snapshot_community(self, community_id: str) -> CommunitySnapshot:
        """Snapshot a Telegram chat using getChat + getChatMemberCount + getUpdates."""
        chat_info = await self._api_call("getChat", {"chat_id": community_id})
        member_count_result = await self._api_call(
            "getChatMemberCount", {"chat_id": community_id}
        )
        member_count = (
            member_count_result if isinstance(member_count_result, int) else 0
        )

        messages = await self.get_recent_messages(community_id, limit=200)

        now = datetime.now(timezone.utc)
        cutoff_24h = now - timedelta(hours=24)
        recent_messages = [
            m
            for m in messages
            if datetime.fromtimestamp(m.get("timestamp", 0), tz=timezone.utc)
            > cutoff_24h
        ]

        active_authors = set()
        topic_counter: Counter = Counter()
        for msg in recent_messages:
            author = msg.get("author", "")
            if author:
                active_authors.add(author)
            # Simple topic extraction: use first significant word
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
            name=chat_info.get("title", community_id),
            member_count=member_count,
            active_members_24h=active_24h,
            messages_24h=messages_24h,
            sentiment_score=0.0,  # Placeholder; real sentiment from aggregator
            top_topics=top_topics,
            engagement_rate=min(engagement, 1.0),
            growth_rate_weekly=0.0,  # Requires historical data
            timestamp=now,
            is_own=True,
            metadata={
                "chat_type": chat_info.get("type", "unknown"),
                "description": chat_info.get("description", ""),
            },
        )

    async def get_recent_messages(
        self, community_id: str, limit: int = 100
    ) -> List[Dict]:
        """Fetch recent messages via getUpdates filtered by chat_id."""
        updates = await self._api_call(
            "getUpdates", {"limit": limit, "allowed_updates": '["message"]'}
        )
        if not isinstance(updates, list):
            return []

        messages = []
        for update in updates:
            msg = update.get("message", {})
            chat = msg.get("chat", {})
            chat_id = str(chat.get("id", ""))
            if chat_id != str(community_id):
                continue

            sender = msg.get("from", {})
            messages.append(
                {
                    "message_id": msg.get("message_id"),
                    "text": msg.get("text", ""),
                    "author": sender.get("username", sender.get("first_name", "")),
                    "author_id": str(sender.get("id", "")),
                    "timestamp": msg.get("date", 0),
                }
            )

        return messages[:limit]

    async def get_member_stats(self, community_id: str) -> Dict[str, Any]:
        """Get basic member statistics for a Telegram chat."""
        member_count_result = await self._api_call(
            "getChatMemberCount", {"chat_id": community_id}
        )
        member_count = (
            member_count_result if isinstance(member_count_result, int) else 0
        )

        messages = await self.get_recent_messages(community_id, limit=200)
        author_counts: Counter = Counter()
        for msg in messages:
            author = msg.get("author", "unknown")
            author_counts[author] += 1

        return {
            "total_members": member_count,
            "recent_active_authors": len(author_counts),
            "top_authors": dict(author_counts.most_common(20)),
            "messages_sampled": len(messages),
        }
