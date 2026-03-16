"""
Profile Intelligence — Grok-powered X/Twitter profile analysis.

Uses Grok (xAI) to analyze a person's X profile and generate a
natural-language summary for Freeman: who this person is, what they
care about, how influential they are, and whether they're worth engaging.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.community.models import ProfileIntelligence

logger = logging.getLogger(__name__)

GROK_API_BASE = "https://api.x.ai/v1"

PROFILE_ANALYSIS_PROMPT = """Analyze this X/Twitter profile and provide a concise intelligence briefing.

Username: @{username}
Bio: {bio}
Followers: {followers}
Following: {following}
Recent tweets (last 10):
{recent_tweets}

Provide a JSON response with these fields:
{{
  "summary": "2-3 sentence natural language summary of who this person is, written as a briefing for an AI entity (Mr. Freeman) who needs to know if this person is worth engaging with",
  "interests": ["list", "of", "main", "interests"],
  "influence_level": "micro/regular/influencer/major",
  "primary_language": "en/ru/etc",
  "sentiment_toward_crypto": float between -1 and 1,
  "sentiment_toward_ai": float between -1 and 1,
  "notable_connections": ["@username1", "@username2"],
  "red_flags": ["any concerns or warning signs"],
  "tweet_frequency": float (avg tweets per day)
}}

Be direct and honest. Freeman doesn't care about politeness — he needs accurate intelligence."""


class ProfileIntelligenceService:
    """
    Analyzes X/Twitter profiles using Grok to generate
    intelligence briefings for Freeman.

    For each person Freeman interacts with, this service can
    pull their X profile, analyze their tweet history, interests,
    influence level, and generate a natural-language summary
    that Freeman can use for context-aware engagement.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get(
            "grok_api_key",
            os.environ.get("GROK_API_KEY", ""),
        )
        self.model = self.config.get("model", "grok-3")
        self.twitter_bearer = self.config.get(
            "twitter_bearer_token",
            os.environ.get("TWITTER_BEARER_TOKEN", ""),
        )
        self._cache: Dict[str, ProfileIntelligence] = {}

    async def analyze_profile(
        self,
        username: str,
        force_refresh: bool = False,
    ) -> Optional[ProfileIntelligence]:
        """
        Analyze an X/Twitter profile and return intelligence.

        Uses Twitter API to fetch profile data, then Grok to analyze it.
        Results are cached to avoid redundant API calls.

        Args:
            username: X/Twitter username (without @).
            force_refresh: If True, bypass cache and re-analyze.
        """
        if not force_refresh and username in self._cache:
            cached = self._cache[username]
            age = (datetime.utcnow() - cached.generated_at).total_seconds()
            if age < 86400:  # Cache for 24 hours
                return cached

        # Step 1: Fetch profile data from Twitter API
        profile_data = await self._fetch_twitter_profile(username)
        if not profile_data:
            logger.warning(f"Could not fetch Twitter profile for @{username}")
            return None

        # Step 2: Fetch recent tweets
        recent_tweets = await self._fetch_recent_tweets(username)

        # Step 3: Send to Grok for analysis
        intelligence = await self._analyze_with_grok(
            username, profile_data, recent_tweets
        )

        if intelligence:
            self._cache[username] = intelligence

        return intelligence

    async def batch_analyze(
        self,
        usernames: List[str],
        force_refresh: bool = False,
    ) -> Dict[str, Optional[ProfileIntelligence]]:
        """Analyze multiple profiles. Returns dict of username -> intelligence."""
        import asyncio
        tasks = [
            self.analyze_profile(u, force_refresh)
            for u in usernames
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            u: (r if not isinstance(r, Exception) else None)
            for u, r in zip(usernames, results)
        }

    async def get_cached(self, username: str) -> Optional[ProfileIntelligence]:
        """Get cached intelligence without making API calls."""
        return self._cache.get(username)

    async def get_summary_for_freeman(self, username: str) -> str:
        """
        Get a Freeman-ready one-liner about a person.

        If no cached intelligence, returns a placeholder.
        """
        intel = self._cache.get(username)
        if not intel:
            return f"@{username} — no intel yet. want me to check?"

        return (
            f"@{username}: {intel.summary} "
            f"[{intel.influence_level}, {intel.follower_count} followers, "
            f"{'pro-crypto' if intel.sentiment_toward_crypto > 0.2 else 'crypto-neutral' if intel.sentiment_toward_crypto > -0.2 else 'crypto-skeptic'}]"
        )

    async def _fetch_twitter_profile(
        self, username: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch profile data from Twitter API v2."""
        if not self.twitter_bearer:
            logger.warning("No Twitter bearer token configured")
            return None

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://api.twitter.com/2/users/by/username/{username}",
                    headers={"Authorization": f"Bearer {self.twitter_bearer}"},
                    params={
                        "user.fields": "description,public_metrics,created_at,location,verified"
                    },
                    timeout=15,
                )

            if resp.status_code != 200:
                logger.error(f"Twitter API error for @{username}: {resp.status_code}")
                return None

            data = resp.json().get("data", {})
            metrics = data.get("public_metrics", {})
            return {
                "username": username,
                "name": data.get("name", username),
                "bio": data.get("description", ""),
                "followers": metrics.get("followers_count", 0),
                "following": metrics.get("following_count", 0),
                "tweet_count": metrics.get("tweet_count", 0),
                "verified": data.get("verified", False),
                "location": data.get("location", ""),
                "created_at": data.get("created_at", ""),
            }

        except Exception as e:
            logger.error(f"Failed to fetch Twitter profile for @{username}: {e}")
            return None

    async def _fetch_recent_tweets(
        self, username: str, limit: int = 10
    ) -> List[str]:
        """Fetch recent tweets for context."""
        if not self.twitter_bearer:
            return []

        try:
            import httpx

            # First get user ID
            async with httpx.AsyncClient() as client:
                user_resp = await client.get(
                    f"https://api.twitter.com/2/users/by/username/{username}",
                    headers={"Authorization": f"Bearer {self.twitter_bearer}"},
                    timeout=15,
                )

            if user_resp.status_code != 200:
                return []

            user_id = user_resp.json().get("data", {}).get("id")
            if not user_id:
                return []

            # Then get tweets
            async with httpx.AsyncClient() as client:
                tweets_resp = await client.get(
                    f"https://api.twitter.com/2/users/{user_id}/tweets",
                    headers={"Authorization": f"Bearer {self.twitter_bearer}"},
                    params={
                        "max_results": limit,
                        "tweet.fields": "created_at,public_metrics",
                    },
                    timeout=15,
                )

            if tweets_resp.status_code != 200:
                return []

            tweets = tweets_resp.json().get("data", [])
            return [t.get("text", "") for t in tweets]

        except Exception as e:
            logger.error(f"Failed to fetch tweets for @{username}: {e}")
            return []

    async def _analyze_with_grok(
        self,
        username: str,
        profile_data: Dict[str, Any],
        recent_tweets: List[str],
    ) -> Optional[ProfileIntelligence]:
        """Send profile data to Grok for analysis."""
        if not self.api_key:
            logger.warning("No Grok API key configured")
            return None

        tweets_text = "\n".join(
            f"  {i+1}. {t[:200]}" for i, t in enumerate(recent_tweets)
        ) or "  (no recent tweets available)"

        prompt = PROFILE_ANALYSIS_PROMPT.format(
            username=username,
            bio=profile_data.get("bio", "N/A"),
            followers=profile_data.get("followers", 0),
            following=profile_data.get("following", 0),
            recent_tweets=tweets_text,
        )

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{GROK_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                        "max_tokens": 1024,
                    },
                    timeout=30,
                )

            if resp.status_code != 200:
                logger.error(f"Grok API error: {resp.status_code}")
                return None

            content = resp.json()["choices"][0]["message"]["content"]

            # Parse JSON from Grok response
            # Handle potential markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            parsed = json.loads(content.strip())

            return ProfileIntelligence(
                person_id=f"twitter:{username}",
                platform_username=username,
                summary=parsed.get("summary", ""),
                interests=parsed.get("interests", []),
                influence_level=parsed.get("influence_level", "regular"),
                follower_count=profile_data.get("followers", 0),
                following_count=profile_data.get("following", 0),
                tweet_frequency=parsed.get("tweet_frequency", 0.0),
                primary_language=parsed.get("primary_language", "unknown"),
                sentiment_toward_crypto=parsed.get("sentiment_toward_crypto", 0.0),
                sentiment_toward_ai=parsed.get("sentiment_toward_ai", 0.0),
                notable_connections=parsed.get("notable_connections", []),
                red_flags=parsed.get("red_flags", []),
                raw_grok_response=content,
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Grok response for @{username}: {e}")
            return None
        except Exception as e:
            logger.error(f"Grok analysis failed for @{username}: {e}")
            return None
