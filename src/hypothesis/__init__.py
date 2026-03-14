"""
Product Hypothesis Testing Framework.

Define hypotheses about products, automatically collect evidence
from community data and analytics, and generate reports on status.
Feeds validated learnings back into the content pipeline.
"""

from src.hypothesis.models import (
    Hypothesis,
    HypothesisStatus,
    Evidence,
    HypothesisReport,
)
from src.hypothesis.tracker import HypothesisTracker
from src.hypothesis.evidence_collector import EvidenceCollector
from src.hypothesis.reporter import HypothesisReporter

__all__ = [
    "Hypothesis",
    "HypothesisStatus",
    "Evidence",
    "HypothesisReport",
    "HypothesisTracker",
    "EvidenceCollector",
    "HypothesisReporter",
]
