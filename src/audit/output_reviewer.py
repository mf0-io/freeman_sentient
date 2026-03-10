"""Reviews Freeman's outputs against quality dimensions using LLM."""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.audit.models import QualityScore

logger = logging.getLogger(__name__)


class OutputReviewer:
    """Reviews Freeman's outputs against quality dimensions using LLM."""

    QUALITY_DIMENSIONS = [
        "voice_consistency",
        "content_depth",
        "engagement_quality",
        "factual_accuracy",
        "mission_alignment",
    ]

    DIMENSION_DESCRIPTIONS = {
        "voice_consistency": (
            "Does this sound like Mr. Freeman -- provocative, philosophical, "
            "challenging the audience to think deeper? Rate how well it matches "
            "Freeman's distinctive voice and tone."
        ),
        "content_depth": (
            "Does this content have real intellectual substance? Does it go beyond "
            "surface-level observations to offer genuine insight or provoke deep thinking?"
        ),
        "engagement_quality": (
            "Would this content provoke thought, discussion, or meaningful engagement "
            "from the audience? Does it challenge assumptions or spark curiosity?"
        ),
        "factual_accuracy": (
            "Are the claims, references, and factual assertions in this content correct? "
            "Are there any misleading or false statements?"
        ),
        "mission_alignment": (
            "Does this content serve the mission of consciousness awakening? Does it "
            "push people to question their reality, think independently, and break free "
            "from passive consumption?"
        ),
    }

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        llm_config = config.get("llm", {})
        self._model = llm_config.get("model", "claude-sonnet-4-20250514")
        self._temperature = llm_config.get("temperature", 0.3)
        self._max_tokens = llm_config.get("max_tokens", 2048)
        self._api_url = "https://api.anthropic.com/v1/messages"

    async def review_content(
        self,
        content: str,
        content_type: str = "post",
        context: Optional[Dict[str, Any]] = None,
    ) -> List[QualityScore]:
        """Score content across all quality dimensions.

        Args:
            content: The text content to review.
            content_type: Type of content (e.g. "post", "comment", "article").
            context: Optional additional context for the review.

        Returns:
            List of QualityScore objects, one per dimension.
        """
        ctx = context or {}
        ctx["content_type"] = content_type
        text = f"[Content type: {content_type}]\n\n{content}"
        return await self._evaluate_all_dimensions(text, ctx)

    async def review_response(
        self,
        user_message: str,
        freeman_response: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[QualityScore]:
        """Score a conversational response.

        Args:
            user_message: The user's message that prompted the response.
            freeman_response: Freeman's response to evaluate.
            context: Optional additional context.

        Returns:
            List of QualityScore objects, one per dimension.
        """
        ctx = context or {}
        ctx["content_type"] = "response"
        text = (
            f"[User message]: {user_message}\n\n"
            f"[Freeman's response]: {freeman_response}"
        )
        return await self._evaluate_all_dimensions(text, ctx)

    async def review_batch(
        self, items: List[Dict[str, Any]]
    ) -> List[List[QualityScore]]:
        """Review multiple items concurrently.

        Each item should have either:
          - "content" and optionally "content_type", "context" (for review_content)
          - "user_message" and "freeman_response" and optionally "context" (for review_response)

        Returns:
            List of score lists, one per item.
        """
        tasks = []
        for item in items:
            if "user_message" in item and "freeman_response" in item:
                tasks.append(
                    self.review_response(
                        item["user_message"],
                        item["freeman_response"],
                        item.get("context"),
                    )
                )
            else:
                tasks.append(
                    self.review_content(
                        item.get("content", ""),
                        item.get("content_type", "post"),
                        item.get("context"),
                    )
                )
        return await asyncio.gather(*tasks)

    async def _evaluate_all_dimensions(
        self, text: str, context: Dict[str, Any]
    ) -> List[QualityScore]:
        """Evaluate text across all dimensions concurrently."""
        tasks = [
            self._evaluate_dimension(text, dim, context)
            for dim in self.QUALITY_DIMENSIONS
        ]
        return await asyncio.gather(*tasks)

    async def _evaluate_dimension(
        self,
        text: str,
        dimension: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> QualityScore:
        """Use httpx + Anthropic API to score one dimension.

        Args:
            text: The text to evaluate.
            dimension: The quality dimension to score.
            context: Optional additional context.

        Returns:
            A QualityScore for the given dimension.
        """
        description = self.DIMENSION_DESCRIPTIONS.get(dimension, dimension)
        context_str = ""
        if context:
            context_str = f"\nAdditional context: {json.dumps(context)}"

        prompt = (
            f"You are an expert quality reviewer for Mr. Freeman content -- "
            f"a provocative, philosophical character focused on awakening consciousness.\n\n"
            f"Evaluate the following content on this dimension:\n"
            f"**{dimension}**: {description}\n\n"
            f"Content to evaluate:\n---\n{text}\n---\n"
            f"{context_str}\n\n"
            f"Respond with ONLY valid JSON (no markdown, no code fences):\n"
            f'{{"score": <float 0.0-1.0>, "reasoning": "<brief explanation>"}}'
        )

        try:
            score_value, reasoning = await self._call_llm(prompt)
            return QualityScore(
                dimension=dimension,
                score=score_value,
                reasoning=reasoning,
                timestamp=datetime.utcnow(),
                metadata={"context": context or {}},
            )
        except Exception as exc:
            logger.error("Failed to evaluate dimension %s: %s", dimension, exc)
            return QualityScore(
                dimension=dimension,
                score=0.5,
                reasoning=f"Evaluation failed: {exc}",
                timestamp=datetime.utcnow(),
                metadata={"error": str(exc)},
            )

    async def _call_llm(self, prompt: str) -> tuple:
        """Make an API call to Anthropic and parse the score response.

        Returns:
            Tuple of (score: float, reasoning: str).
        """
        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self._api_url, headers=headers, json=payload)
            response.raise_for_status()

        data = response.json()
        response_text = data["content"][0]["text"].strip()

        parsed = json.loads(response_text)
        score_value = float(parsed["score"])
        score_value = max(0.0, min(1.0, score_value))
        reasoning = str(parsed.get("reasoning", ""))

        return score_value, reasoning
