"""
YouTube collector — parses comments, likes, and subscriber interactions.

Uses YouTube Data API v3 to extract interactions from Freeman's
channel and tracked videos.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class YouTubeCollector(BaseCollector):
    """
    Collects interaction data from YouTube.

    Parses:
    - Comments on Freeman's videos
    - Reply threads between commenters
    - Comment likes (when available)
    - Subscriber activity patterns
    """

    @property
    def platform_name(self) -> str:
        return "youtube"

    def __init__(self, graph, config: Dict[str, Any]):
        super().__init__(graph, config)
        self.api_key = config.get(
            "youtube_api_key",
            os.environ.get("YOUTUBE_API_KEY", ""),
        )
        self.channel_id = config.get(
            "youtube_channel_id",
            os.environ.get("YOUTUBE_CHANNEL_ID", ""),
        )
        self._service = None

    def _get_service(self):
        if self._service is None:
            try:
                from googleapiclient.discovery import build
                self._service = build("youtube", "v3", developerKey=self.api_key)
            except ImportError:
                logger.error("google-api-python-client not installed")
                return None
        return self._service

    async def validate_credentials(self) -> bool:
        if not self.api_key or not self.channel_id:
            return False
        service = self._get_service()
        if not service:
            return False
        try:
            response = service.channels().list(
                part="snippet", id=self.channel_id
            ).execute()
            return len(response.get("items", [])) > 0
        except Exception as e:
            logger.error(f"YouTube credential validation failed: {e}")
            return False

    async def collect(self, since: Optional[datetime] = None) -> int:
        """Collect comment interactions from recent videos."""
        service = self._get_service()
        if not service:
            return 0

        videos = await self._get_recent_videos(service, since)
        total = 0
        for video in videos:
            total += await self._collect_comments(service, video)

        return total

    async def _get_recent_videos(
        self, service, since: Optional[datetime]
    ) -> List[Dict]:
        """Get recent videos from the channel."""
        try:
            published_after = since or (datetime.utcnow() - timedelta(days=30))

            response = service.search().list(
                part="snippet",
                channelId=self.channel_id,
                type="video",
                order="date",
                publishedAfter=published_after.strftime("%Y-%m-%dT%H:%M:%SZ"),
                maxResults=20,
            ).execute()

            videos = []
            for item in response.get("items", []):
                videos.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "published_at": item["snippet"]["publishedAt"],
                })
            return videos

        except Exception as e:
            logger.error(f"Failed to get YouTube videos: {e}")
            return []

    async def _collect_comments(self, service, video: Dict) -> int:
        """Extract interactions from video comments."""
        video_id = video["video_id"]

        try:
            response = service.commentThreads().list(
                part="snippet,replies",
                videoId=video_id,
                maxResults=100,
                order="time",
                textFormat="plainText",
            ).execute()

            count = 0
            for thread in response.get("items", []):
                top_comment = thread["snippet"]["topLevelComment"]["snippet"]
                author_id = top_comment.get("authorChannelId", {}).get("value", "")
                author_name = top_comment.get("authorDisplayName", "")

                if not author_id:
                    continue

                await self._ensure_person(
                    name=author_name,
                    platform_user_id=author_id,
                    role="viewer",
                    metadata={"channel_url": top_comment.get("authorChannelUrl", "")},
                )

                # Comment on Freeman's video = interaction with Freeman
                freeman_node = await self._ensure_person(
                    name="Mr. Freeman",
                    platform_user_id=self.channel_id,
                    role="team",
                )

                ts = datetime.fromisoformat(
                    top_comment["publishedAt"].replace("Z", "+00:00")
                ).replace(tzinfo=None)

                await self._record_interaction(
                    source_platform_id=author_id,
                    target_platform_id=self.channel_id,
                    interaction_type="comment",
                    context=top_comment.get("textDisplay", "")[:200],
                    weight=2.0,
                    timestamp=ts,
                    metadata={
                        "video_id": video_id,
                        "video_title": video["title"],
                        "like_count": top_comment.get("likeCount", 0),
                    },
                )
                count += 1

                # Process reply threads (commenter-to-commenter interactions)
                replies = thread.get("replies", {}).get("comments", [])
                for reply in replies:
                    reply_snippet = reply["snippet"]
                    reply_author_id = reply_snippet.get("authorChannelId", {}).get("value", "")
                    reply_author_name = reply_snippet.get("authorDisplayName", "")

                    if not reply_author_id or reply_author_id == author_id:
                        continue

                    await self._ensure_person(
                        name=reply_author_name,
                        platform_user_id=reply_author_id,
                        role="viewer",
                    )

                    reply_ts = datetime.fromisoformat(
                        reply_snippet["publishedAt"].replace("Z", "+00:00")
                    ).replace(tzinfo=None)

                    await self._record_interaction(
                        source_platform_id=reply_author_id,
                        target_platform_id=author_id,
                        interaction_type="reply",
                        context=reply_snippet.get("textDisplay", "")[:200],
                        weight=2.5,
                        timestamp=reply_ts,
                        metadata={"video_id": video_id},
                    )
                    count += 1

            return count

        except Exception as e:
            logger.error(f"Failed to collect YouTube comments for {video_id}: {e}")
            return 0
