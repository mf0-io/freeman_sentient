"""
Intelligence System -- multi-LLM research and daily briefing pipeline.

Provides research providers (Gemini, Grok, Claude) and a BriefingAssembler
that orchestrates them to produce a DailyBriefing.
"""

from src.intelligence.briefing_assembler import BriefingAssembler
from src.intelligence.models import DailyBriefing, SourceInsight
from src.intelligence.providers.base import BaseResearchProvider
from src.intelligence.providers.claude_provider import ClaudeResearchProvider
from src.intelligence.providers.gemini_provider import GeminiResearchProvider
from src.intelligence.providers.grok_provider import GrokResearchProvider

__all__ = [
    "BriefingAssembler",
    "DailyBriefing",
    "SourceInsight",
    "BaseResearchProvider",
    "GeminiResearchProvider",
    "GrokResearchProvider",
    "ClaudeResearchProvider",
]
