"""
Audience Analyzer — per-person sentiment tracking and activity ranking.

Builds detailed profiles of every community member Freeman interacts with:
- Per-message sentiment tracking with running average
- Activity scoring (messages, replies, reactions weighted)
- Automatic role classification (advocate, power_user, member, lurker, troll)
- Leaderboard generation for any time period
- Integration with TemporalPeopleGraph for cross-platform identity
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.community.models import MemberLeaderboard, MemberProfile

logger = logging.getLogger(__name__)


class AudienceAnalyzer:
    """
    Analyzes community audiences at the individual member level.

    Tracks every person's activity, sentiment, and engagement patterns.
    Generates leaderboards and identifies key community members
    (advocates, power users, trolls) for Freeman's awareness.
    """

    def __init__(
        self,
        people_graph=None,
        sentiment_analyzer=None,
    ):
        """
        Args:
            people_graph: TemporalPeopleGraph instance for cross-platform identity.
            sentiment_analyzer: SentimentAnalyzer from analytics module for text scoring.
        """
        self.people_graph = people_graph
        self.sentiment_analyzer = sentiment_analyzer
        self._profiles: Dict[str, MemberProfile] = {}

    async def process_message(
        self,
        platform: str,
        platform_user_id: str,
        username: str,
        name: str,
        text: str,
        is_reply: bool = False,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemberProfile:
        """
        Process a single message and update the member's profile.

        Called by community monitors for every message observed.
        Tracks sentiment per message and updates running averages.
        """
        ts = timestamp or datetime.utcnow()
        key = f"{platform}:{platform_user_id}"

        if key not in self._profiles:
            self._profiles[key] = MemberProfile(
                person_id=key,
                name=name,
                platform=platform,
                platform_user_id=platform_user_id,
                username=username,
                first_seen=ts,
            )

        profile = self._profiles[key]
        profile.last_active = ts
        profile.message_count += 1
        if is_reply:
            profile.reply_count += 1

        # Sentiment analysis per message
        sentiment = 0.0
        if self.sentiment_analyzer and text:
            try:
                result = self.sentiment_analyzer.analyze(text)
                sentiment = result.score if hasattr(result, "score") else 0.0
            except Exception:
                sentiment = 0.0

        profile.sentiment_history.append({
            "timestamp": ts.isoformat(),
            "sentiment": sentiment,
            "text_preview": text[:100] if text else "",
        })

        # Keep only last 100 sentiment entries
        if len(profile.sentiment_history) > 100:
            profile.sentiment_history = profile.sentiment_history[-100:]

        # Update running average sentiment
        recent = profile.sentiment_history[-20:]
        profile.avg_sentiment = (
            sum(e["sentiment"] for e in recent) / len(recent)
            if recent else 0.0
        )

        # Recompute scores
        profile.compute_activity_score()
        profile.classify_role()

        # Sync with people graph if available
        if self.people_graph:
            try:
                await self.people_graph.add_person(
                    name=name,
                    platform=platform,
                    platform_user_id=platform_user_id,
                    role=profile.role,
                    tags=profile.tags,
                    metadata={"avg_sentiment": profile.avg_sentiment},
                )
            except Exception as e:
                logger.debug(f"People graph sync failed: {e}")

        return profile

    async def process_reaction(
        self,
        platform: str,
        platform_user_id: str,
        username: str,
        name: str,
        timestamp: Optional[datetime] = None,
    ) -> Optional[MemberProfile]:
        """Track a reaction/like from a member."""
        key = f"{platform}:{platform_user_id}"

        if key not in self._profiles:
            self._profiles[key] = MemberProfile(
                person_id=key,
                name=name,
                platform=platform,
                platform_user_id=platform_user_id,
                username=username,
                first_seen=timestamp or datetime.utcnow(),
            )

        profile = self._profiles[key]
        profile.reaction_count += 1
        profile.last_active = timestamp or datetime.utcnow()
        profile.compute_activity_score()
        profile.classify_role()
        return profile

    async def get_leaderboard(
        self,
        community_id: str = "all",
        platform: Optional[str] = None,
        period: str = "all_time",
        limit: int = 50,
    ) -> MemberLeaderboard:
        """
        Generate a ranked leaderboard of most active members.

        Args:
            community_id: Community to filter by, or "all" for global.
            platform: Filter by platform.
            period: "24h", "7d", "30d", or "all_time".
            limit: Maximum members to include.
        """
        now = datetime.utcnow()
        cutoff = None
        if period == "24h":
            cutoff = now - timedelta(hours=24)
        elif period == "7d":
            cutoff = now - timedelta(days=7)
        elif period == "30d":
            cutoff = now - timedelta(days=30)

        profiles = list(self._profiles.values())

        if platform:
            profiles = [p for p in profiles if p.platform == platform]

        if cutoff:
            profiles = [p for p in profiles if p.last_active >= cutoff]

        # Recompute scores for the period
        for p in profiles:
            p.compute_activity_score()
            p.classify_role()

        # Sort by activity score descending
        profiles.sort(key=lambda p: p.activity_score, reverse=True)
        top = profiles[:limit]

        return MemberLeaderboard(
            community_id=community_id,
            platform=platform or "all",
            period=period,
            members=top,
        )

    async def get_member(
        self, platform: str, platform_user_id: str
    ) -> Optional[MemberProfile]:
        """Get a specific member's profile."""
        key = f"{platform}:{platform_user_id}"
        return self._profiles.get(key)

    async def get_sentiment_leaders(
        self, limit: int = 10, direction: str = "positive"
    ) -> List[MemberProfile]:
        """
        Get members with strongest sentiment (positive or negative).

        Args:
            direction: "positive" for advocates, "negative" for detractors.
        """
        profiles = [
            p for p in self._profiles.values()
            if p.message_count >= 3  # minimum activity threshold
        ]

        if direction == "positive":
            profiles.sort(key=lambda p: p.avg_sentiment, reverse=True)
        else:
            profiles.sort(key=lambda p: p.avg_sentiment)

        return profiles[:limit]

    async def get_audience_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive audience summary for Freeman's briefing.

        Returns role distribution, sentiment distribution, activity stats,
        and notable members.
        """
        profiles = list(self._profiles.values())
        if not profiles:
            return {"total_tracked": 0, "message": "No audience data yet"}

        role_counts = defaultdict(int)
        platform_counts = defaultdict(int)
        sentiment_buckets = {"positive": 0, "neutral": 0, "negative": 0}

        for p in profiles:
            role_counts[p.role] += 1
            platform_counts[p.platform] += 1
            if p.avg_sentiment > 0.1:
                sentiment_buckets["positive"] += 1
            elif p.avg_sentiment < -0.1:
                sentiment_buckets["negative"] += 1
            else:
                sentiment_buckets["neutral"] += 1

        active_24h = [
            p for p in profiles
            if p.last_active >= datetime.utcnow() - timedelta(hours=24)
        ]

        top_by_activity = sorted(
            profiles, key=lambda p: p.activity_score, reverse=True
        )[:5]

        advocates = [p for p in profiles if p.role == "advocate"]
        trolls = [p for p in profiles if p.role == "troll"]

        return {
            "total_tracked": len(profiles),
            "active_24h": len(active_24h),
            "roles": dict(role_counts),
            "platforms": dict(platform_counts),
            "sentiment_distribution": sentiment_buckets,
            "avg_sentiment": (
                sum(p.avg_sentiment for p in profiles) / len(profiles)
            ),
            "top_members": [
                {
                    "name": p.name,
                    "username": p.username,
                    "platform": p.platform,
                    "activity_score": round(p.activity_score, 1),
                    "sentiment": round(p.avg_sentiment, 2),
                    "role": p.role,
                }
                for p in top_by_activity
            ],
            "advocates_count": len(advocates),
            "trolls_count": len(trolls),
            "notable_advocates": [
                {"name": p.name, "username": p.username, "score": round(p.activity_score, 1)}
                for p in sorted(advocates, key=lambda p: p.activity_score, reverse=True)[:3]
            ],
        }
