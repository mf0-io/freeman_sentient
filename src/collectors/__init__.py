"""
Platform collectors for the Temporal People Graph.

Each collector parses interactions from a specific platform
and feeds PersonNode + InteractionEdge data into the graph.
"""

from src.collectors.base import BaseCollector
from src.collectors.telegram_collector import TelegramCollector
from src.collectors.twitter_collector import TwitterCollector
from src.collectors.youtube_collector import YouTubeCollector
from src.collectors.kickstarter_collector import KickstarterCollector

__all__ = [
    "BaseCollector",
    "TelegramCollector",
    "TwitterCollector",
    "YouTubeCollector",
    "KickstarterCollector",
]
