"""
Telegram collector — parses group chats and DMs for interaction data.

Extracts: replies, mentions, reactions, forwards, media shares.
Feeds into the Temporal People Graph as interaction edges.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)

FREEMAN_BOT_ID = os.environ.get("TELEGRAM_BOT_USER_ID", "")


class TelegramCollector(BaseCollector):
    """
    Collects interaction data from Telegram groups and DMs.

    Parses message history to extract:
    - Reply chains (A replies to B = directed interaction)
    - @mentions (A mentions B = directed interaction)
    - Reactions (A reacts to B's message)
    - Forwards (A forwards B's message)
    - Group co-presence (A and B active in same group within time window)
    """

    @property
    def platform_name(self) -> str:
        return "telegram"

    def __init__(self, graph, config: Dict[str, Any]):
        super().__init__(graph, config)
        self.bot_token = config.get("telegram_bot_token", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
        self.group_ids = config.get("telegram_group_ids", [])
        self._api_base = f"https://api.telegram.org/bot{self.bot_token}"

    async def validate_credentials(self) -> bool:
        if not self.bot_token:
            return False
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self._api_base}/getMe", timeout=10)
                return resp.status_code == 200 and resp.json().get("ok", False)
        except Exception as e:
            logger.error(f"Telegram credential validation failed: {e}")
            return False

    async def collect(self, since: Optional[datetime] = None) -> int:
        """Collect interactions from Telegram group messages."""
        import httpx

        if not self.group_ids:
            logger.warning("No Telegram group IDs configured")
            return 0

        total = 0
        async with httpx.AsyncClient() as client:
            for group_id in self.group_ids:
                count = await self._collect_group(client, group_id, since)
                total += count

        return total

    async def _collect_group(
        self, client, group_id: str, since: Optional[datetime]
    ) -> int:
        """Parse messages from a single Telegram group."""
        try:
            resp = await client.get(
                f"{self._api_base}/getUpdates",
                params={"limit": 100, "timeout": 0},
                timeout=15,
            )
            if resp.status_code != 200:
                return 0

            data = resp.json()
            if not data.get("ok"):
                return 0

            count = 0
            for update in data.get("result", []):
                message = update.get("message", {})
                chat = message.get("chat", {})

                if str(chat.get("id")) != str(group_id):
                    continue

                ts = datetime.utcfromtimestamp(message.get("date", 0))
                if since and ts < since:
                    continue

                count += await self._process_message(message, ts)

            return count

        except Exception as e:
            logger.error(f"Failed to collect from group {group_id}: {e}")
            return 0

    async def _process_message(self, message: Dict, timestamp: datetime) -> int:
        """Extract interactions from a single message."""
        interactions = 0
        from_user = message.get("from", {})
        if not from_user or from_user.get("is_bot", False):
            return 0

        sender_id = str(from_user.get("id", ""))
        sender_name = (
            f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip()
            or from_user.get("username", sender_id)
        )

        await self._ensure_person(
            name=sender_name,
            platform_user_id=sender_id,
            metadata={"username": from_user.get("username", "")},
        )

        # Reply interaction
        reply_to = message.get("reply_to_message", {})
        if reply_to and reply_to.get("from"):
            target_user = reply_to["from"]
            if not target_user.get("is_bot", False):
                target_id = str(target_user.get("id", ""))
                target_name = (
                    f"{target_user.get('first_name', '')} {target_user.get('last_name', '')}".strip()
                    or target_user.get("username", target_id)
                )
                await self._ensure_person(name=target_name, platform_user_id=target_id)
                await self._record_interaction(
                    source_platform_id=sender_id,
                    target_platform_id=target_id,
                    interaction_type="reply",
                    context=message.get("text", "")[:200],
                    weight=2.0,
                    timestamp=timestamp,
                )
                interactions += 1

        # @mention interactions
        text = message.get("text", "")
        entities = message.get("entities", [])
        for entity in entities:
            if entity.get("type") == "mention":
                offset = entity["offset"]
                length = entity["length"]
                mentioned = text[offset:offset + length].lstrip("@")
                if mentioned:
                    target = await self.graph.find_person_by_platform("telegram", mentioned)
                    if not target:
                        target_node = await self._ensure_person(
                            name=mentioned, platform_user_id=mentioned
                        )
                    await self._record_interaction(
                        source_platform_id=sender_id,
                        target_platform_id=mentioned,
                        interaction_type="mention",
                        context=text[:200],
                        weight=1.5,
                        timestamp=timestamp,
                    )
                    interactions += 1

        # Forward interaction
        forward_from = message.get("forward_from", {})
        if forward_from and not forward_from.get("is_bot"):
            fwd_id = str(forward_from.get("id", ""))
            fwd_name = (
                f"{forward_from.get('first_name', '')} {forward_from.get('last_name', '')}".strip()
            )
            if fwd_id:
                await self._ensure_person(name=fwd_name, platform_user_id=fwd_id)
                await self._record_interaction(
                    source_platform_id=sender_id,
                    target_platform_id=fwd_id,
                    interaction_type="forward",
                    weight=1.0,
                    timestamp=timestamp,
                )
                interactions += 1

        return interactions
