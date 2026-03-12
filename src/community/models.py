"""Data models for community monitoring and analysis."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class CommunitySnapshot:
    """Point-in-time snapshot of a community's state."""

    community_id: str
    platform: str
    name: str
    member_count: int
    active_members_24h: int
    messages_24h: int
    sentiment_score: float  # -1 to 1
    top_topics: List[str]
    engagement_rate: float  # 0 to 1
    growth_rate_weekly: float
    timestamp: datetime
    is_own: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompetitorProfile:
    """Profile snapshot for a competitor community or account."""

    competitor_id: str
    name: str
    platform: str
    category: str
    follower_count: int
    engagement_rate: float
    content_frequency: float  # posts per day
    top_topics: List[str]
    sentiment_score: float
    last_updated: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemberProfile:
    """Deep profile of a community member with sentiment history and activity metrics."""

    person_id: str
    name: str
    platform: str
    platform_user_id: str
    username: str = ""
    message_count: int = 0
    reaction_count: int = 0
    reply_count: int = 0
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    avg_sentiment: float = 0.0  # -1.0 to 1.0
    sentiment_history: List[Dict[str, Any]] = field(default_factory=list)
    top_topics: List[str] = field(default_factory=list)
    activity_score: float = 0.0  # composite score: messages * 1 + replies * 2 + reactions * 0.5
    role: str = "member"  # member, power_user, lurker, troll, advocate
    tags: List[str] = field(default_factory=list)
    x_profile_summary: str = ""  # Grok-generated summary of their X/Twitter profile
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_activity_score(self) -> float:
        self.activity_score = (
            self.message_count * 1.0
            + self.reply_count * 2.0
            + self.reaction_count * 0.5
        )
        return self.activity_score

    def classify_role(self) -> str:
        if self.activity_score >= 50 and self.avg_sentiment > 0.2:
            self.role = "advocate"
        elif self.activity_score >= 30:
            self.role = "power_user"
        elif self.activity_score >= 5:
            self.role = "member"
        elif self.avg_sentiment < -0.3 and self.message_count >= 3:
            self.role = "troll"
        else:
            self.role = "lurker"
        return self.role


@dataclass
class MemberLeaderboard:
    """Ranked list of most active community members."""

    community_id: str
    platform: str
    period: str  # "24h", "7d", "30d", "all_time"
    members: List[MemberProfile] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def top_10(self) -> List[MemberProfile]:
        return sorted(self.members, key=lambda m: m.activity_score, reverse=True)[:10]

    @property
    def advocates(self) -> List[MemberProfile]:
        return [m for m in self.members if m.role == "advocate"]

    @property
    def trolls(self) -> List[MemberProfile]:
        return [m for m in self.members if m.role == "troll"]


@dataclass
class ProfileIntelligence:
    """Grok-generated intelligence about a person's X/Twitter profile."""

    person_id: str
    platform_username: str
    summary: str  # natural language summary for Freeman
    interests: List[str]
    influence_level: str  # "micro", "regular", "influencer", "major"
    follower_count: int = 0
    following_count: int = 0
    tweet_frequency: float = 0.0  # tweets per day
    primary_language: str = "unknown"
    sentiment_toward_crypto: float = 0.0  # -1 to 1
    sentiment_toward_ai: float = 0.0  # -1 to 1
    notable_connections: List[str] = field(default_factory=list)
    red_flags: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    raw_grok_response: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EngagementPattern:
    """Detected engagement pattern or anomaly."""

    pattern_id: str
    community_id: str
    pattern_type: str  # "peak_hours", "topic_resonance", "growth_trigger", "decline_trigger"
    description: str
    confidence: float
    data_points: List[Dict[str, Any]]
    detected_at: datetime
