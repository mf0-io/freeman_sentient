"""
Grok (xAI) research provider.

Uses the xAI API to research Twitter/X real-time trends, sentiment analysis,
trending topics, and competitor mentions.
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

_DEFAULT_MODEL = "grok-3"
_API_BASE = "https://api.x.ai/v1"


class GrokResearchProvider(BaseResearchProvider):
    """Research provider backed by xAI Grok, focused on Twitter/X real-time data."""

    @property
    def provider_name(self) -> str:
        return "grok"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key: str = config.get("api_key") or os.getenv("GROK_API_KEY", "")
        self.model: str = config.get("model", _DEFAULT_MODEL)
        self.temperature: float = config.get("temperature", 0.7)
        self.max_tokens: int = config.get("max_tokens", 4096)

    async def validate_credentials(self) -> bool:
        if not self.api_key:
            logger.warning("Grok API key is not set")
            return False
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    f"{_API_BASE}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "ping"}],
                        "max_tokens": 16,
                    },
                )
                return resp.status_code == 200
        except Exception as exc:
            logger.error("Grok credential validation failed: %s", exc)
            return False

    async def research(
        self,
        topics: List[str],
        context: Dict[str, Any] | None = None,
    ) -> List[SourceInsight]:
        insights: List[SourceInsight] = []

        for topic in topics:
            try:
                insight = await self._research_topic(topic, context)
                if insight is not None:
                    insights.append(insight)
            except Exception as exc:
                logger.error("Grok research failed for topic '%s': %s", topic, exc)

        return insights

    async def _research_topic(
        self,
        topic: str,
        context: Dict[str, Any] | None,
    ) -> SourceInsight | None:
        prompt = self._build_prompt(topic, context)

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{_API_BASE}/chat/completions",
                headers=self._headers(),
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a Twitter/X social media intelligence analyst. "
                                "Analyze real-time trends, sentiment, and notable discussions."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                },
            )
            resp.raise_for_status()

        data = resp.json()
        text = self._extract_text(data)
        if not text:
            logger.warning("Empty response from Grok for topic '%s'", topic)
            return None

        parsed = self._parse_response(text)

        return SourceInsight(
            provider=self.provider_name,
            domain="twitter_realtime",
            title=parsed.get("title", topic),
            summary=parsed.get("summary", text[:500]),
            key_findings=parsed.get("key_findings", []),
            confidence=parsed.get("confidence", 0.7),
            sources=parsed.get("sources", []),
            raw_data={"response": text},
            timestamp=datetime.utcnow(),
            metadata={"model": self.model, "topic": topic},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _build_prompt(topic: str, context: Dict[str, Any] | None) -> str:
        context_block = ""
        if context:
            context_block = f"\n\nAdditional context:\n{json.dumps(context, default=str)}"

        return (
            "Analyze the following topic from a Twitter/X real-time perspective. "
            "Cover: trending discussions, public sentiment, notable accounts/threads, "
            "competitor mentions, and emerging narratives.\n\n"
            "Return a JSON object with keys: title (string), summary (string), "
            "key_findings (list of strings), confidence (float 0-1), "
            "sources (list of strings).\n\n"
            f"Topic: {topic}{context_block}\n\n"
            "Respond ONLY with valid JSON."
        )

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
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
