"""Hypothesis tracker — manages lifecycle of product hypotheses."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from src.hypothesis.models import Evidence, Hypothesis, HypothesisStatus

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = "config/hypothesis_config.yaml"


class HypothesisTracker:
    """
    Manages product hypotheses through their lifecycle.

    Loads initial hypotheses from YAML, supports adding evidence,
    evaluating status, and querying active hypotheses.
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self._hypotheses: Dict[str, Hypothesis] = {}

    async def initialize(self) -> None:
        """Load hypotheses from YAML config."""
        path = Path(self.config_path)
        if not path.exists():
            logger.warning(f"Hypothesis config not found: {self.config_path}")
            return

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            for h in data.get("hypotheses", []):
                hypothesis = Hypothesis(
                    hypothesis_id=h["id"],
                    product_id=h["product_id"],
                    statement=h["statement"],
                    success_criteria=h.get("success_criteria", ""),
                    metric_name=h.get("metric_name"),
                    metric_target=h.get("metric_target"),
                    status=HypothesisStatus(h.get("status", "active")),
                    deadline=(
                        datetime.fromisoformat(h["deadline"])
                        if h.get("deadline") else None
                    ),
                )
                self._hypotheses[hypothesis.hypothesis_id] = hypothesis

            logger.info(f"Loaded {len(self._hypotheses)} hypotheses")
        except Exception as e:
            logger.error(f"Failed to load hypotheses: {e}")

    async def add_hypothesis(self, hypothesis: Hypothesis) -> Hypothesis:
        self._hypotheses[hypothesis.hypothesis_id] = hypothesis
        logger.info(f"Added hypothesis: {hypothesis.hypothesis_id}")
        return hypothesis

    async def add_evidence(
        self, hypothesis_id: str, evidence: Evidence
    ) -> bool:
        hypothesis = self._hypotheses.get(hypothesis_id)
        if not hypothesis:
            logger.warning(f"Hypothesis not found: {hypothesis_id}")
            return False

        hypothesis.evidence.append(evidence)
        hypothesis.updated_at = datetime.utcnow()
        logger.info(
            f"Added {evidence.direction} evidence to {hypothesis_id} "
            f"(confidence={evidence.confidence})"
        )
        return True

    async def evaluate(self, hypothesis_id: str) -> Optional[HypothesisStatus]:
        """Evaluate hypothesis status based on accumulated evidence."""
        hypothesis = self._hypotheses.get(hypothesis_id)
        if not hypothesis:
            return None

        if not hypothesis.evidence:
            return hypothesis.status

        score = hypothesis.support_score()
        total_evidence = len(hypothesis.evidence)

        if hypothesis.deadline and datetime.utcnow() > hypothesis.deadline:
            if total_evidence < 3:
                hypothesis.status = HypothesisStatus.INCONCLUSIVE
            elif score >= 0.7:
                hypothesis.status = HypothesisStatus.VALIDATED
            elif score <= 0.3:
                hypothesis.status = HypothesisStatus.INVALIDATED
            else:
                hypothesis.status = HypothesisStatus.INCONCLUSIVE
        elif total_evidence >= 10:
            if score >= 0.8:
                hypothesis.status = HypothesisStatus.VALIDATED
            elif score <= 0.2:
                hypothesis.status = HypothesisStatus.INVALIDATED

        hypothesis.updated_at = datetime.utcnow()
        return hypothesis.status

    async def list_active(self) -> List[Hypothesis]:
        return [
            h for h in self._hypotheses.values()
            if h.status == HypothesisStatus.ACTIVE
        ]

    async def list_all(self) -> List[Hypothesis]:
        return list(self._hypotheses.values())

    async def get_hypothesis(
        self, hypothesis_id: str
    ) -> Optional[Hypothesis]:
        return self._hypotheses.get(hypothesis_id)

    async def get_summary(self) -> Dict[str, Any]:
        """Summary for daily briefing."""
        hypotheses = list(self._hypotheses.values())
        return {
            "total": len(hypotheses),
            "by_status": {
                status.value: sum(
                    1 for h in hypotheses if h.status == status
                )
                for status in HypothesisStatus
            },
            "active_hypotheses": [
                {
                    "id": h.hypothesis_id,
                    "product": h.product_id,
                    "statement": h.statement,
                    "support_score": h.support_score(),
                    "evidence_count": len(h.evidence),
                }
                for h in hypotheses
                if h.status == HypothesisStatus.ACTIVE
            ],
        }
