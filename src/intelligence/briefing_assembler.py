"""
Briefing assembler for the Intelligence System.

Orchestrates multiple research providers, gathers insights in parallel,
and uses the Claude synthesis provider to produce a unified DailyBriefing.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.intelligence.models import DailyBriefing, SourceInsight
from src.intelligence.providers.base import BaseResearchProvider
from src.intelligence.providers.claude_provider import ClaudeResearchProvider

logger = logging.getLogger(__name__)

_DEFAULT_TOPICS = [
    "AI agents and autonomous systems",
    "Crypto and DeFi trends",
    "Social media and content creation",
    "Digital consciousness and philosophy",
    "Mr. Freeman community and competitors",
]


class BriefingAssembler:
    """Assembles a DailyBriefing by running providers in parallel and synthesizing."""

    def __init__(
        self,
        providers: List[BaseResearchProvider],
        synthesis_provider: ClaudeResearchProvider,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.providers = providers
        self.synthesis_provider = synthesis_provider
        self.config = config or {}

    async def assemble_briefing(
        self,
        focus_topics: Optional[List[str]] = None,
        ecosystem_context: Optional[Dict[str, Any]] = None,
    ) -> DailyBriefing:
        """Run the full research-and-synthesis pipeline.

        1. Determine topics (user-supplied or defaults).
        2. Fan out to all providers in parallel.
        3. Flatten and collect insights.
        4. Synthesize via Claude.
        5. Return a complete DailyBriefing.
        """
        topics = focus_topics or self.config.get("default_topics", _DEFAULT_TOPICS)
        timeout = self.config.get("research_timeout_seconds", 120)

        # --- Step 1: Parallel research ---
        logger.info(
            "Starting research across %d providers on %d topics",
            len(self.providers),
            len(topics),
        )

        tasks = [
            provider.research(topics, ecosystem_context)
            for provider in self.providers
        ]

        results: List[List[SourceInsight]] = []
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.error("Research timed out after %d seconds", timeout)

        # --- Step 2: Flatten insights, skip exceptions ---
        all_insights: List[SourceInsight] = []
        for result in results:
            if isinstance(result, BaseException):
                logger.error("Provider returned an error: %s", result)
                continue
            all_insights.extend(result)

        logger.info("Collected %d insights from providers", len(all_insights))

        # --- Step 3: Synthesize ---
        synthesis_data = await self._synthesize(all_insights, ecosystem_context)

        # --- Step 4: Build briefing ---
        briefing = DailyBriefing(
            briefing_id=str(uuid.uuid4()),
            date=datetime.utcnow(),
            insights=all_insights,
            synthesis=synthesis_data.get("summary", ""),
            key_topics=synthesis_data.get("key_topics", topics),
            content_suggestions=synthesis_data.get("content_suggestions", []),
            strategic_recommendations=synthesis_data.get(
                "strategic_recommendations", []
            ),
            market_signals=synthesis_data.get("market_signals", []),
            competitor_activity=synthesis_data.get("competitor_activity", []),
            metadata={
                "provider_count": len(self.providers),
                "insight_count": len(all_insights),
                "topics_requested": topics,
            },
        )

        logger.info("Briefing %s assembled successfully", briefing.briefing_id)
        return briefing

    async def _synthesize(
        self,
        insights: List[SourceInsight],
        ecosystem_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Use Claude to synthesize all insights into a coherent narrative."""
        if not insights:
            logger.warning("No insights to synthesize; returning empty synthesis")
            return {}

        serialized_insights = [
            {
                "provider": i.provider,
                "domain": i.domain,
                "title": i.title,
                "summary": i.summary,
                "key_findings": i.key_findings,
                "confidence": i.confidence,
            }
            for i in insights
        ]

        topics = list({i.title for i in insights})

        context: Dict[str, Any] = {"prior_insights": serialized_insights}
        if ecosystem_context:
            context["ecosystem"] = ecosystem_context

        try:
            synthesis_insights = await self.synthesis_provider.research(
                topics=topics,
                context=context,
            )
        except Exception as exc:
            logger.error("Synthesis failed: %s", exc)
            return {}

        if not synthesis_insights:
            return {}

        raw = synthesis_insights[0].raw_data.get("response", "")
        parsed = self._parse_synthesis(raw)

        # Ensure the summary key is present
        if "summary" not in parsed:
            parsed["summary"] = synthesis_insights[0].summary

        return parsed

    @staticmethod
    def _parse_synthesis(text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"summary": text}
