"""
Twitter/X collector — parses mentions, replies, retweets, quote tweets.

Uses Tweepy for API access. Extracts interaction edges and feeds
them into the Temporal People Graph.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """
    Collects interaction data from Twitter/X.

    Parses:
    - Mentions of Freeman or tracked accounts
    - Replies to Freeman's tweets
    - Retweets and quote tweets
    - Followers who engage regularly
    """

    @property
    def platform_name(self) -> str:
        return "twitter"

    def __init__(self, graph, config: Dict[str, Any]):
        super().__init__(graph, config)
        self.bearer_token = config.get(
            "twitter_bearer_token",
            os.environ.get("TWITTER_BEARER_TOKEN", ""),
        )
        self.tracked_accounts = config.get("twitter_tracked_accounts", [])
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import tweepy
                self._client = tweepy.Client(bearer_token=self.bearer_token)
            except ImportError:
                logger.error("tweepy not installed")
                return None
        return self._client

    async def validate_credentials(self) -> bool:
        if not self.bearer_token:
            return False
        client = self._get_client()
        if not client:
            return False
        try:
            me = client.get_me()
            return me is not None and me.data is not None
        except Exception as e:
            logger.error(f"Twitter credential validation failed: {e}")
            return False

    async def collect(self, since: Optional[datetime] = None) -> int:
        """Collect mentions, replies, and retweets."""
        client = self._get_client()
        if not client:
            return 0

        total = 0
        for account in self.tracked_accounts:
            total += await self._collect_mentions(client, account, since)
            total += await self._collect_replies(client, account, since)

        return total

    async def _collect_mentions(
        self, client, account: str, since: Optional[datetime]
    ) -> int:
        """Collect @mentions of a tracked account."""
        try:
            user = client.get_user(username=account)
            if not user or not user.data:
                return 0

            user_id = user.data.id
            start_time = since or (datetime.utcnow() - timedelta(days=7))

            mentions = client.get_users_mentions(
                id=user_id,
                start_time=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                max_results=100,
                tweet_fields=["created_at", "author_id", "in_reply_to_user_id", "referenced_tweets"],
                user_fields=["username", "name"],
                expansions=["author_id"],
            )

            if not mentions or not mentions.data:
                return 0

            users_map = {}
            if mentions.includes and "users" in mentions.includes:
                for u in mentions.includes["users"]:
                    users_map[u.id] = {"name": u.name, "username": u.username}

            count = 0
            for tweet in mentions.data:
                author_id = str(tweet.author_id)
                author_info = users_map.get(tweet.author_id, {})
                author_name = author_info.get("name", author_info.get("username", author_id))

                await self._ensure_person(
                    name=author_name,
                    platform_user_id=author_id,
                    metadata={"username": author_info.get("username", "")},
                )

                target_node = await self._ensure_person(
                    name=account,
                    platform_user_id=str(user_id),
                    role="team",
                )

                interaction_type = "mention"
                weight = 1.5

                if tweet.referenced_tweets:
                    for ref in tweet.referenced_tweets:
                        if ref.type == "replied_to":
                            interaction_type = "reply"
                            weight = 2.0
                        elif ref.type == "retweeted":
                            interaction_type = "retweet"
                            weight = 1.0
                        elif ref.type == "quoted":
                            interaction_type = "quote"
                            weight = 2.5

                ts = tweet.created_at if tweet.created_at else datetime.utcnow()

                await self._record_interaction(
                    source_platform_id=author_id,
                    target_platform_id=str(user_id),
                    interaction_type=interaction_type,
                    context=tweet.text[:200] if tweet.text else "",
                    weight=weight,
                    timestamp=ts,
                )
                count += 1

            return count

        except Exception as e:
            logger.error(f"Failed to collect Twitter mentions for {account}: {e}")
            return 0

    async def _collect_replies(
        self, client, account: str, since: Optional[datetime]
    ) -> int:
        """Collect replies to tweets from a tracked account."""
        try:
            user = client.get_user(username=account)
            if not user or not user.data:
                return 0

            user_id = user.data.id
            start_time = since or (datetime.utcnow() - timedelta(days=7))

            tweets = client.get_users_tweets(
                id=user_id,
                start_time=start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                max_results=50,
                tweet_fields=["created_at", "public_metrics", "conversation_id"],
            )

            if not tweets or not tweets.data:
                return 0

            count = 0
            for tweet in tweets.data:
                metrics = tweet.public_metrics or {}
                reply_count = metrics.get("reply_count", 0)
                retweet_count = metrics.get("retweet_count", 0)
                like_count = metrics.get("like_count", 0)

                if reply_count > 0 or retweet_count > 0:
                    await self._ensure_person(
                        name=account,
                        platform_user_id=str(user_id),
                        role="team",
                        metadata={
                            "engagement": {
                                "replies": reply_count,
                                "retweets": retweet_count,
                                "likes": like_count,
                            }
                        },
                    )
                    count += 1

            return count

        except Exception as e:
            logger.error(f"Failed to collect Twitter replies for {account}: {e}")
            return 0
