"""
Base research provider interface.

All intelligence research providers must inherit from BaseResearchProvider
and implement the required abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from src.intelligence.models import SourceInsight


class BaseResearchProvider(ABC):
    """Abstract base class for research providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique identifier for this provider."""
        ...

    @abstractmethod
    async def research(
        self,
        topics: List[str],
        context: Dict[str, Any] | None = None,
    ) -> List[SourceInsight]:
        """Run research on the given topics and return insights.

        Args:
            topics: List of research topics/queries.
            context: Optional additional context (e.g. outputs from other providers).

        Returns:
            A list of SourceInsight objects.
        """
        ...

    @abstractmethod
    async def validate_credentials(self) -> bool:
        """Check whether the provider's API credentials are valid.

        Returns:
            True if credentials are valid and the API is reachable.
        """
        ...
