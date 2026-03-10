"""Generates improvement suggestions from quality patterns."""

import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from src.audit.models import AuditReport, ImprovementSuggestion

logger = logging.getLogger(__name__)


class ImprovementEngine:
    """Generates improvement suggestions from quality patterns."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        llm_config = config.get("llm", {})
        self._model = llm_config.get("model", "claude-sonnet-4-20250514")
        self._temperature = llm_config.get("temperature", 0.3)
        self._max_tokens = llm_config.get("max_tokens", 2048)
        self._api_url = "https://api.anthropic.com/v1/messages"

    async def generate_suggestions(
        self,
        report: AuditReport,
        history: Optional[List[AuditReport]] = None,
    ) -> List[ImprovementSuggestion]:
        """Analyze quality trends and generate concrete improvements using LLM.

        For declining dimensions, suggests specific fixes.
        For patterns (e.g., repeated low voice_consistency), suggests rule additions.

        Args:
            report: The current audit report.
            history: Optional list of previous reports for trend analysis.

        Returns:
            List of ImprovementSuggestion objects.
        """
        declining = []
        low_scores = []

        for qs in report.quality_scores:
            if qs.score < 0.6:
                low_scores.append(qs)

        if history:
            dimension_trends = self._analyze_trends(report, history)
            for dim, trend_info in dimension_trends.items():
                if trend_info["direction"] == "declining":
                    declining.append({"dimension": dim, **trend_info})

        if not declining and not low_scores:
            logger.info("No issues detected, no suggestions generated.")
            return []

        prompt = self._build_suggestion_prompt(report, declining, low_scores, history)

        try:
            suggestions = await self._call_llm_for_suggestions(prompt)
            return suggestions
        except Exception as exc:
            logger.error("Failed to generate suggestions: %s", exc)
            return []

    def _classify_severity(self, score_delta: float) -> str:
        """Classify severity based on score drop magnitude.

        Args:
            score_delta: The score change (negative means drop).

        Returns:
            Severity string: "high", "medium", or "low".
        """
        abs_delta = abs(score_delta)
        if abs_delta > 0.2:
            return "high"
        elif abs_delta > 0.1:
            return "medium"
        else:
            return "low"

    def _analyze_trends(
        self, current: AuditReport, history: List[AuditReport]
    ) -> Dict[str, Dict[str, Any]]:
        """Compare current report dimensions against historical averages."""
        dim_history: Dict[str, List[float]] = {}

        for past_report in history:
            for qs in past_report.quality_scores:
                dim_history.setdefault(qs.dimension, []).append(qs.score)

        trends: Dict[str, Dict[str, Any]] = {}
        current_by_dim = {qs.dimension: qs.score for qs in current.quality_scores}

        for dim, past_scores in dim_history.items():
            avg_past = sum(past_scores) / len(past_scores)
            current_score = current_by_dim.get(dim, avg_past)
            delta = current_score - avg_past

            if delta < -0.1:
                direction = "declining"
            elif delta > 0.05:
                direction = "improving"
            else:
                direction = "stable"

            trends[dim] = {
                "direction": direction,
                "avg_past": round(avg_past, 4),
                "current": round(current_score, 4),
                "delta": round(delta, 4),
                "severity": self._classify_severity(delta),
            }

        return trends

    def _build_suggestion_prompt(
        self,
        report: AuditReport,
        declining: List[Dict[str, Any]],
        low_scores: List[Any],
        history: Optional[List[AuditReport]],
    ) -> str:
        """Build the LLM prompt for generating improvement suggestions."""
        parts = [
            "You are an improvement analyst for Mr. Freeman -- a provocative, "
            "philosophical character focused on awakening consciousness.\n\n"
            "Based on the quality audit data below, generate concrete improvement "
            "suggestions that can be applied to MEMORY.md sections.\n\n"
        ]

        parts.append(f"Overall score: {report.overall_score}\n")
        parts.append(f"Trend: {report.trend_direction}\n")
        parts.append(f"Outputs reviewed: {report.outputs_reviewed}\n\n")

        if low_scores:
            parts.append("Low-scoring dimensions:\n")
            for qs in low_scores:
                parts.append(f"  - {qs.dimension}: {qs.score} -- {qs.reasoning}\n")
            parts.append("\n")

        if declining:
            parts.append("Declining dimensions:\n")
            for d in declining:
                parts.append(
                    f"  - {d['dimension']}: {d['current']} (was {d['avg_past']}, "
                    f"delta {d['delta']}, severity {d['severity']})\n"
                )
            parts.append("\n")

        parts.append(
            "For each issue, generate a suggestion as JSON. Respond with ONLY a JSON "
            "array (no markdown, no code fences). Each element:\n"
            "{\n"
            '  "category": "bad_pattern"|"new_rule"|"topic_adjustment"|"tone_correction",\n'
            '  "description": "<what to fix>",\n'
            '  "severity": "low"|"medium"|"high",\n'
            '  "auto_applicable": true|false,\n'
            '  "target_section": "BAD"|"Rules"|"Topics",\n'
            '  "suggested_text": "<text to add/modify in MEMORY.md>",\n'
            '  "evidence": ["<supporting observation>", ...]\n'
            "}\n\n"
            "Only suggest auto_applicable=true for low/medium severity items "
            "where the fix is clear and safe."
        )

        return "".join(parts)

    async def _call_llm_for_suggestions(
        self, prompt: str
    ) -> List[ImprovementSuggestion]:
        """Call Anthropic API and parse suggestions from response."""
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
        raw_suggestions = json.loads(response_text)

        suggestions = []
        for raw in raw_suggestions:
            suggestion = ImprovementSuggestion(
                suggestion_id=str(uuid.uuid4()),
                category=raw["category"],
                description=raw["description"],
                severity=raw["severity"],
                auto_applicable=raw.get("auto_applicable", False),
                target_section=raw["target_section"],
                suggested_text=raw.get("suggested_text", ""),
                evidence=raw.get("evidence", []),
                timestamp=datetime.utcnow(),
            )
            suggestions.append(suggestion)

        logger.info("Generated %d improvement suggestions", len(suggestions))
        return suggestions
