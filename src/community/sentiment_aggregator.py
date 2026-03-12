"""Cross-community sentiment analysis and comparison."""

import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Dict, List

from src.community.models import CommunitySnapshot
from src.community.monitors.base import BaseCommunityMonitor

logger = logging.getLogger(__name__)


class SentimentAggregator:
    """Cross-community sentiment analysis and comparison."""

    def __init__(self, monitors: List[BaseCommunityMonitor]):
        self.monitors = monitors

    async def aggregate_all(self) -> Dict[str, Any]:
        """
        Snapshot all monitored communities, return aggregate sentiment.

        Returns:
            Dict with per-platform snapshots, overall averages, and metadata.
        """
        all_snapshots: List[CommunitySnapshot] = []
        errors: List[Dict[str, str]] = []

        for monitor in self.monitors:
            try:
                result = await monitor.sync()
                if result.get("status") in ("ok", "partial"):
                    # Collect individual snapshots
                    for cid in monitor.config.get("monitored_ids", []):
                        try:
                            snapshot = await monitor.snapshot_community(cid)
                            all_snapshots.append(snapshot)
                        except Exception as e:
                            logger.error(
                                f"Failed to snapshot {cid} on "
                                f"{monitor.platform_name}: {e}"
                            )
                            errors.append(
                                {"community_id": cid, "error": str(e)}
                            )
            except Exception as e:
                logger.error(f"Failed to sync {monitor.platform_name}: {e}")
                errors.append({"platform": monitor.platform_name, "error": str(e)})

        # Compute aggregate metrics
        if all_snapshots:
            avg_sentiment = sum(s.sentiment_score for s in all_snapshots) / len(
                all_snapshots
            )
            avg_engagement = sum(s.engagement_rate for s in all_snapshots) / len(
                all_snapshots
            )
            total_members = sum(s.member_count for s in all_snapshots)
            total_messages = sum(s.messages_24h for s in all_snapshots)
        else:
            avg_sentiment = 0.0
            avg_engagement = 0.0
            total_members = 0
            total_messages = 0

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "communities_monitored": len(all_snapshots),
            "total_members": total_members,
            "total_messages_24h": total_messages,
            "avg_sentiment": avg_sentiment,
            "avg_engagement": avg_engagement,
            "per_community": [
                {
                    "community_id": s.community_id,
                    "platform": s.platform,
                    "name": s.name,
                    "members": s.member_count,
                    "messages_24h": s.messages_24h,
                    "sentiment": s.sentiment_score,
                    "engagement": s.engagement_rate,
                }
                for s in all_snapshots
            ],
            "errors": errors,
        }

    async def compare_own_vs_competitors(
        self,
        own_snapshots: List[CommunitySnapshot],
        competitor_snapshots: List[CommunitySnapshot],
    ) -> Dict[str, Any]:
        """
        Compare sentiment, engagement, growth between own and competitor communities.

        Args:
            own_snapshots: Snapshots of our own communities.
            competitor_snapshots: Snapshots of competitor communities.

        Returns:
            Comparison dict with own averages, competitor averages, and deltas.
        """

        def _avg(snapshots: List[CommunitySnapshot], attr: str) -> float:
            if not snapshots:
                return 0.0
            values = [getattr(s, attr) for s in snapshots]
            return sum(values) / len(values)

        own_avg_sentiment = _avg(own_snapshots, "sentiment_score")
        own_avg_engagement = _avg(own_snapshots, "engagement_rate")
        own_avg_growth = _avg(own_snapshots, "growth_rate_weekly")
        own_total_members = sum(s.member_count for s in own_snapshots)

        comp_avg_sentiment = _avg(competitor_snapshots, "sentiment_score")
        comp_avg_engagement = _avg(competitor_snapshots, "engagement_rate")
        comp_avg_growth = _avg(competitor_snapshots, "growth_rate_weekly")
        comp_total_members = sum(s.member_count for s in competitor_snapshots)

        return {
            "own": {
                "count": len(own_snapshots),
                "total_members": own_total_members,
                "avg_sentiment": own_avg_sentiment,
                "avg_engagement": own_avg_engagement,
                "avg_growth_weekly": own_avg_growth,
            },
            "competitors": {
                "count": len(competitor_snapshots),
                "total_members": comp_total_members,
                "avg_sentiment": comp_avg_sentiment,
                "avg_engagement": comp_avg_engagement,
                "avg_growth_weekly": comp_avg_growth,
            },
            "deltas": {
                "sentiment": own_avg_sentiment - comp_avg_sentiment,
                "engagement": own_avg_engagement - comp_avg_engagement,
                "growth_weekly": own_avg_growth - comp_avg_growth,
            },
        }

    async def get_trending_topics(self) -> List[Dict[str, Any]]:
        """
        Extract trending topics across all communities.

        Returns:
            List of topic dicts sorted by frequency, with platform breakdown.
        """
        topic_counter: Counter = Counter()
        topic_platforms: Dict[str, Counter] = {}

        for monitor in self.monitors:
            for cid in monitor.config.get("monitored_ids", []):
                try:
                    messages = await monitor.get_recent_messages(cid, limit=200)
                except Exception as e:
                    logger.error(
                        f"Failed to get messages from {cid} on "
                        f"{monitor.platform_name}: {e}"
                    )
                    continue

                for msg in messages:
                    text = msg.get("text", "")
                    words = [
                        w.lower()
                        for w in text.split()
                        if len(w) > 4 and not w.startswith("http")
                    ]
                    topic_counter.update(words)
                    for word in words:
                        if word not in topic_platforms:
                            topic_platforms[word] = Counter()
                        topic_platforms[word][monitor.platform_name] += 1

        trending = []
        for topic, count in topic_counter.most_common(30):
            platforms = dict(topic_platforms.get(topic, {}))
            trending.append(
                {
                    "topic": topic,
                    "total_mentions": count,
                    "platforms": platforms,
                }
            )

        return trending
