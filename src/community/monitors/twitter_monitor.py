"""Twitter/X community monitor using the v2 API."""

import logging
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx

from src.community.models import CommunitySnapshot, CompetitorProfile
from src.community.monitors.base import BaseCommunityMonitor

logger = logging.getLogger(__name__)

TWITTER_API_BASE = "https://api.twitter.com/2"


class TwitterCommunityMonitor(BaseCommunityMonitor):
    """
    Monitor Twitter/X accounts and community engagement via API v2.

    Tracks own accounts and competitor public metrics.
    Config keys:
        - tracked_accounts: list of username strings
    Env vars:
        - TWITTER_BEARER_TOKEN
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._token = os.environ.get("TWITTER_BEARER_TOKEN", "")
        self._tracked_accounts: List[str] = config.get("tracked_accounts", [])
        self.config["monitored_ids"] = self._tracked_accounts

    @property
    def platform_name(self) -> str:
        return "twitter"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    async def _api_get(
        self, path: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make a Twitter API v2 GET request."""
        url = f"{TWITTER_API_BASE}{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    url, headers=self._headers(), params=params or {}
                )
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Twitter API request failed for {path}: {e}")
            return {}

    async def _get_user_by_username(self, username: str) -> Dict[str, Any]:
        """Look up a user by username, including public metrics."""
        data = await self._api_get(
            f"/users/by/username/{username}",
            {"user.fields": "public_metrics,description,created_at"},
        )
        return data.get("data", {})

    async def _get_user_tweets(
        self, user_id: str, max_results: int = 100
    ) -> List[Dict]:
        """Get recent tweets for a user with engagement metrics."""
        data = await self._api_get(
            f"/users/{user_id}/tweets",
            {
                "max_results": min(max_results, 100),
                "tweet.fields": "public_metrics,created_at,text",
            },
        )
        return data.get("data", [])

    async def _get_user_mentions(
        self, user_id: str, max_results: int = 100
    ) -> List[Dict]:
        """Get recent mentions for a user."""
        data = await self._api_get(
            f"/users/{user_id}/mentions",
            {
                "max_results": min(max_results, 100),
                "tweet.fields": "public_metrics,created_at,text,author_id",
            },
        )
        return data.get("data", [])

    async def snapshot_community(self, community_id: str) -> CommunitySnapshot:
        """
        Snapshot a Twitter account as a community.

        Uses user metrics and recent tweet engagement as proxy for community health.
        community_id is treated as a Twitter username.
        """
        user = await self._get_user_by_username(community_id)
        if not user:
            logger.warning(f"Could not fetch Twitter user: {community_id}")
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

        metrics = user.get("public_metrics", {})
        follower_count = metrics.get("followers_count", 0)
        user_id = user.get("id", "")

        tweets = await self._get_user_tweets(user_id, max_results=50)
        mentions = await self._get_user_mentions(user_id, max_results=50)

        now = datetime.now(timezone.utc)
        cutoff_24h = now - timedelta(hours=24)

        tweets_24h = 0
        total_engagement = 0
        topic_counter: Counter = Counter()

        for tweet in tweets:
            created_str = tweet.get("created_at", "")
            try:
                created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                created = now

            if created > cutoff_24h:
                tweets_24h += 1

            t_metrics = tweet.get("public_metrics", {})
            total_engagement += (
                t_metrics.get("like_count", 0)
                + t_metrics.get("retweet_count", 0)
                + t_metrics.get("reply_count", 0)
                + t_metrics.get("quote_count", 0)
            )

            text = tweet.get("text", "")
            words = [w.lower() for w in text.split() if len(w) > 4 and not w.startswith("http")]
            topic_counter.update(words)

        top_topics = [word for word, _ in topic_counter.most_common(10)]
        engagement_rate = (
            total_engagement / (len(tweets) * follower_count)
            if tweets and follower_count > 0
            else 0.0
        )

        # Count unique authors in mentions as proxy for active community members
        mention_authors = set()
        for m in mentions:
            author_id = m.get("author_id", "")
            if author_id:
                mention_authors.add(author_id)

        return CommunitySnapshot(
            community_id=community_id,
            platform=self.platform_name,
            name=user.get("name", community_id),
            member_count=follower_count,
            active_members_24h=len(mention_authors),
            messages_24h=tweets_24h + len(mentions),
            sentiment_score=0.0,
            top_topics=top_topics,
            engagement_rate=min(engagement_rate, 1.0),
            growth_rate_weekly=0.0,
            timestamp=now,
            is_own=True,
            metadata={
                "user_id": user_id,
                "following_count": metrics.get("following_count", 0),
                "tweet_count": metrics.get("tweet_count", 0),
                "listed_count": metrics.get("listed_count", 0),
                "description": user.get("description", ""),
            },
        )

    async def get_recent_messages(
        self, community_id: str, limit: int = 100
    ) -> List[Dict]:
        """Get recent mentions and replies for a Twitter account."""
        user = await self._get_user_by_username(community_id)
        if not user:
            return []

        user_id = user.get("id", "")
        mentions = await self._get_user_mentions(user_id, max_results=limit)

        messages = []
        for m in mentions:
            created_str = m.get("created_at", "")
            try:
                ts = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                ts = datetime.now(timezone.utc)

            messages.append(
                {
                    "message_id": m.get("id"),
                    "text": m.get("text", ""),
                    "author_id": m.get("author_id", ""),
                    "author": "",  # Would need user lookup for username
                    "timestamp": ts,
                    "metrics": m.get("public_metrics", {}),
                }
            )

        return messages[:limit]

    async def get_member_stats(self, community_id: str) -> Dict[str, Any]:
        """Get follower and engagement stats for a Twitter account."""
        user = await self._get_user_by_username(community_id)
        if not user:
            return {"error": f"User not found: {community_id}"}

        metrics = user.get("public_metrics", {})
        user_id = user.get("id", "")
        tweets = await self._get_user_tweets(user_id, max_results=50)

        total_likes = 0
        total_retweets = 0
        total_replies = 0
        for tweet in tweets:
            t_metrics = tweet.get("public_metrics", {})
            total_likes += t_metrics.get("like_count", 0)
            total_retweets += t_metrics.get("retweet_count", 0)
            total_replies += t_metrics.get("reply_count", 0)

        tweet_count = len(tweets) if tweets else 1

        return {
            "followers": metrics.get("followers_count", 0),
            "following": metrics.get("following_count", 0),
            "total_tweets": metrics.get("tweet_count", 0),
            "avg_likes_per_tweet": total_likes / tweet_count,
            "avg_retweets_per_tweet": total_retweets / tweet_count,
            "avg_replies_per_tweet": total_replies / tweet_count,
            "tweets_sampled": tweet_count,
        }

    async def get_competitor_profile(
        self, username: str, category: str = ""
    ) -> CompetitorProfile:
        """Build a CompetitorProfile from public Twitter metrics."""
        user = await self._get_user_by_username(username)
        if not user:
            return CompetitorProfile(
                competitor_id=username,
                name=username,
                platform=self.platform_name,
                category=category,
                follower_count=0,
                engagement_rate=0.0,
                content_frequency=0.0,
                top_topics=[],
                sentiment_score=0.0,
                last_updated=datetime.now(timezone.utc),
            )

        metrics = user.get("public_metrics", {})
        user_id = user.get("id", "")
        tweets = await self._get_user_tweets(user_id, max_results=100)

        follower_count = metrics.get("followers_count", 0)
        total_engagement = 0
        topic_counter: Counter = Counter()

        # Calculate content frequency from tweet timestamps
        tweet_dates = []
        for tweet in tweets:
            t_metrics = tweet.get("public_metrics", {})
            total_engagement += (
                t_metrics.get("like_count", 0)
                + t_metrics.get("retweet_count", 0)
                + t_metrics.get("reply_count", 0)
            )

            text = tweet.get("text", "")
            words = [w.lower() for w in text.split() if len(w) > 4 and not w.startswith("http")]
            topic_counter.update(words)

            created_str = tweet.get("created_at", "")
            try:
                tweet_dates.append(
                    datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                )
            except (ValueError, AttributeError):
                pass

        content_frequency = 0.0
        if len(tweet_dates) >= 2:
            tweet_dates.sort()
            span_days = (tweet_dates[-1] - tweet_dates[0]).total_seconds() / 86400
            if span_days > 0:
                content_frequency = len(tweet_dates) / span_days

        engagement_rate = (
            total_engagement / (len(tweets) * follower_count)
            if tweets and follower_count > 0
            else 0.0
        )

        top_topics = [word for word, _ in topic_counter.most_common(10)]

        return CompetitorProfile(
            competitor_id=username,
            name=user.get("name", username),
            platform=self.platform_name,
            category=category,
            follower_count=follower_count,
            engagement_rate=min(engagement_rate, 1.0),
            content_frequency=content_frequency,
            top_topics=top_topics,
            sentiment_score=0.0,
            last_updated=datetime.now(timezone.utc),
            metadata={
                "user_id": user_id,
                "description": user.get("description", ""),
                "following_count": metrics.get("following_count", 0),
                "listed_count": metrics.get("listed_count", 0),
            },
        )
