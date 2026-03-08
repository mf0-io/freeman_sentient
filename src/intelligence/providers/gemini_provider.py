"""
Gemini research provider.

Uses the Google Generative Language API to research market trends,
technology analysis, and deep research topics.
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

_DEFAULT_MODEL = "gemini-2.0-flash"
_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiResearchProvider(BaseResearchProvider):
    """Research provider backed by Google Gemini."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key: str = config.get("api_key") or os.getenv("GEMINI_API_KEY", "")
        self.model: str = config.get("model", _DEFAULT_MODEL)
        self.temperature: float = config.get("temperature", 0.7)
        self.max_tokens: int = config.get("max_tokens", 4096)

    async def validate_credentials(self) -> bool:
        if not self.api_key:
            logger.warning("Gemini API key is not set")
            return False
        url = f"{_API_BASE}/{self.model}:generateContent?key={self.api_key}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    url,
                    json={
                        "contents": [{"parts": [{"text": "ping"}]}],
                        "generationConfig": {"maxOutputTokens": 16},
                    },
                )
                return resp.status_code == 200
        except Exception as exc:
            logger.error("Gemini credential validation failed: %s", exc)
            return False

    async def research(
        self,
        topics: List[str],
        context: Dict[str, Any] | None = None,
    ) -> List[SourceInsight]:
        insights: List[SourceInsight] = []
        url = f"{_API_BASE}/{self.model}:generateContent?key={self.api_key}"

        for topic in topics:
            try:
                insight = await self._research_topic(url, topic, context)
                if insight is not None:
                    insights.append(insight)
            except Exception as exc:
                logger.error("Gemini research failed for topic '%s': %s", topic, exc)

        return insights

    async def _research_topic(
        self,
        url: str,
        topic: str,
        context: Dict[str, Any] | None,
    ) -> SourceInsight | None:
        prompt = self._build_prompt(topic, context)

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {
                        "temperature": self.temperature,
                        "maxOutputTokens": self.max_tokens,
                    },
                },
            )
            resp.raise_for_status()

        data = resp.json()
        text = self._extract_text(data)
        if not text:
            logger.warning("Empty response from Gemini for topic '%s'", topic)
            return None

        parsed = self._parse_response(text)

        return SourceInsight(
            provider=self.provider_name,
            domain="market_trends",
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

    @staticmethod
    def _build_prompt(topic: str, context: Dict[str, Any] | None) -> str:
        context_block = ""
        if context:
            context_block = f"\n\nAdditional context:\n{json.dumps(context, default=str)}"

        return (
            "You are a market research analyst. Analyze the following topic and "
            "return a JSON object with the keys: title (string), summary (string), "
            "key_findings (list of strings), confidence (float 0-1), "
            "sources (list of strings).\n\n"
            f"Topic: {topic}{context_block}\n\n"
            "Respond ONLY with valid JSON."
        )

    @staticmethod
    def _extract_text(data: Dict[str, Any]) -> str:
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return ""

    @staticmethod
    def _parse_response(text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            lines = lines[1:]  # remove opening fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"summary": text}
