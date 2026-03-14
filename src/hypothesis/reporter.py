"""Hypothesis report generator using LLM for narrative synthesis."""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.hypothesis.models import Hypothesis, HypothesisReport

logger = logging.getLogger(__name__)


class HypothesisReporter:
    """
    Generates human-readable reports on hypothesis status.

    Uses LLM to synthesize evidence into actionable recommendations.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get(
            "anthropic_api_key",
            os.environ.get("ANTHROPIC_API_KEY", ""),
        )
        self.model = self.config.get("model", "claude-sonnet-4-20250514")

    async def generate_report(
        self, hypothesis: Hypothesis
    ) -> HypothesisReport:
        """Generate a report for a single hypothesis."""
        supports = sum(
            1 for e in hypothesis.evidence if e.direction == "supports"
        )
        contradicts = sum(
            1 for e in hypothesis.evidence if e.direction == "contradicts"
        )
        neutral = sum(
            1 for e in hypothesis.evidence if e.direction == "neutral"
        )

        score = hypothesis.support_score()

        if score >= 0.7 and len(hypothesis.evidence) >= 5:
            recommendation = (
                f"Strong evidence supports this hypothesis (score: {score:.0%}). "
                f"Consider moving to validation phase."
            )
            next_steps = [
                "Define concrete success metrics",
                "Plan implementation based on validated hypothesis",
                "Monitor for counter-evidence",
            ]
        elif score <= 0.3 and len(hypothesis.evidence) >= 5:
            recommendation = (
                f"Evidence contradicts this hypothesis (score: {score:.0%}). "
                f"Consider pivoting or invalidating."
            )
            next_steps = [
                "Analyze why the hypothesis failed",
                "Identify alternative hypotheses",
                "Extract learnings for content pipeline",
            ]
        else:
            recommendation = (
                f"Insufficient or mixed evidence (score: {score:.0%}, "
                f"{len(hypothesis.evidence)} data points). Continue collecting."
            )
            next_steps = [
                "Increase data collection frequency",
                "Add more evidence sources",
                "Refine success criteria",
            ]

        if self.api_key:
            llm_recommendation = await self._generate_llm_report(hypothesis)
            if llm_recommendation:
                recommendation = llm_recommendation.get(
                    "recommendation", recommendation
                )
                next_steps = llm_recommendation.get(
                    "next_steps", next_steps
                )

        return HypothesisReport(
            report_id=f"report_{uuid4().hex[:8]}",
            hypothesis=hypothesis,
            evidence_summary={
                "supports": supports,
                "contradicts": contradicts,
                "neutral": neutral,
            },
            recommendation=recommendation,
            next_steps=next_steps,
        )

    async def generate_summary(
        self, hypotheses: List[Hypothesis]
    ) -> str:
        """Executive summary of all hypotheses for daily briefing."""
        if not hypotheses:
            return "No active hypotheses to report on."

        lines = ["Product Hypothesis Status:"]
        for h in hypotheses:
            score = h.support_score()
            ev_count = len(h.evidence)
            lines.append(
                f"- [{h.product_id}] {h.statement[:80]}... "
                f"(score: {score:.0%}, evidence: {ev_count})"
            )

        validated = [
            h for h in hypotheses
            if h.status.value == "validated"
        ]
        if validated:
            lines.append(
                f"\nValidated: {len(validated)} hypothesis(es) confirmed."
            )

        return "\n".join(lines)

    async def _generate_llm_report(
        self, hypothesis: Hypothesis
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to generate nuanced recommendation."""
        try:
            import httpx
            import json

            evidence_text = "\n".join(
                f"- [{e.direction}] {e.description} (confidence: {e.confidence})"
                for e in hypothesis.evidence[-10:]
            )

            prompt = (
                f"Analyze this product hypothesis and provide a recommendation.\n\n"
                f"Hypothesis: {hypothesis.statement}\n"
                f"Product: {hypothesis.product_id}\n"
                f"Success criteria: {hypothesis.success_criteria}\n"
                f"Support score: {hypothesis.support_score():.0%}\n"
                f"Evidence ({len(hypothesis.evidence)} items):\n{evidence_text}\n\n"
                f"Respond in JSON: {{\"recommendation\": \"...\", \"next_steps\": [\"...\"]}}"
            )

            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                    timeout=30,
                )

            if resp.status_code == 200:
                content = resp.json()["content"][0]["text"]
                return json.loads(content)

        except Exception as e:
            logger.warning(f"LLM report generation failed: {e}")

        return None
