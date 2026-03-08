"""
Claude (Anthropic) research provider.

Serves as the synthesis layer: takes outputs from other providers and produces
a strategic analysis that ties all insights together.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import httpx

from src.intelligence.models import SourceInsight
from src.intelligence.providers.base import BaseResearchProvider

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_API_BASE = "https://api.anthropic.com"
_API_VERSION = "2023-06-01"


class ClaudeResearchProvider(BaseResearchProvider):
    """Research provider backed by Anthropic Claude, focused on strategic synthesis."""

    @property
    def provider_name(self) -> str:
        return "claude"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key: str = config.get("api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        self.model: str = config.get("model", _DEFAULT_MODEL)
        self.temperature: float = config.get("temperature", 0.5)
        self.max_tokens: int = config.get("max_tokens", 8192)

    async def validate_credentials(self) -> bool:
        if not self.api_key:
            logger.warning("Anthropic API key is not set")
            return False
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{_API_BASE}/v1/messages",
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "max_tokens": 16,
                        "messages": [{"role": "user", "content": "ping"}],
                    },
                )
                return resp.status_code == 200
        except Exception as exc:
            logger.error("Claude credential validation failed: %s", exc)
            return False

    async def research(
        self,
        topics: List[str],
        context: Dict[str, Any] | None = None,
    ) -> List[SourceInsight]:
        """Synthesize a strategic analysis from topics and (optionally) prior insights.

        When used as the synthesis provider, *context* should include a key
        ``"prior_insights"`` containing serialized SourceInsight data from other
        providers.
        """
        insights: List[SourceInsight] = []

        try:
            insight = await self._synthesize_research(topics, context)
            if insight is not None:
                insights.append(insight)
        except Exception as exc:
            logger.error("Claude research/synthesis failed: %s", exc)

        return insights

    async def _synthesize_research(
        self,
        topics: List[str],
        context: Dict[str, Any] | None,
    ) -> SourceInsight | None:
        prompt = self._build_prompt(topics, context)

        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{_API_BASE}/v1/messages",
                headers=self._headers(),
                json={
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()

        data = resp.json()
        text = self._extract_text(data)
        if not text:
            logger.warning("Empty response from Claude during synthesis")
            return None

        parsed = self._parse_response(text)

        return SourceInsight(
            provider=self.provider_name,
            domain="strategic_analysis",
            title=parsed.get("title", "Strategic Synthesis"),
            summary=parsed.get("summary", text[:500]),
            key_findings=parsed.get("key_findings", []),
            confidence=parsed.get("confidence", 0.8),
            sources=parsed.get("sources", []),
            raw_data={"response": text},
            timestamp=datetime.utcnow(),
            metadata={"model": self.model, "topics": topics},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": _API_VERSION,
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_prompt(topics: List[str], context: Dict[str, Any] | None) -> str:
        topics_block = "\n".join(f"- {t}" for t in topics)

        context_block = ""
        if context:
            prior = context.get("prior_insights")
            if prior:
                context_block = (
                    "\n\nPrior research insights from other providers:\n"
                    f"{json.dumps(prior, default=str, indent=2)}"
                )
            ecosystem = context.get("ecosystem")
            if ecosystem:
                context_block += (
                    "\n\nEcosystem context:\n"
                    f"{json.dumps(ecosystem, default=str, indent=2)}"
                )

        return (
            "You are a strategic analyst for a digital media / AI project. "
            "Synthesize the following research topics and any prior insights "
            "into a coherent strategic view.\n\n"
            f"Topics:\n{topics_block}{context_block}\n\n"
            "Return a JSON object with the following keys:\n"
            "- title (string): A headline for the synthesis\n"
            "- summary (string): 2-3 paragraph strategic summary\n"
            "- key_findings (list of strings): Top 5-7 actionable findings\n"
            "- confidence (float 0-1): Overall confidence level\n"
            "- sources (list of strings): Referenced sources\n"
            "- content_suggestions (list of objects with 'topic' and 'angle' keys)\n"
            "- strategic_recommendations (list of strings)\n"
            "- market_signals (list of objects with 'signal' and 'impact' keys)\n"
            "- competitor_activity (list of objects with 'competitor' and 'activity' keys)\n\n"
            "Respond ONLY with valid JSON."
        )

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        try:
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
        except (KeyError, TypeError):
            pass
        return ""

    @staticmethod
    def _parse_response(text: str) -> Dict[str, Any]:
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
