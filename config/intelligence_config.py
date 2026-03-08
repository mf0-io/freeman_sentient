"""
Intelligence configuration module.

Loads settings from environment variables and the intelligence_config.yaml file,
providing type-safe access to intelligence system configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field


_CONFIG_DIR = Path(__file__).parent
_YAML_PATH = _CONFIG_DIR / "intelligence_config.yaml"


def _load_yaml() -> Dict[str, Any]:
    """Load the intelligence YAML config file."""
    if _YAML_PATH.exists():
        with open(_YAML_PATH, "r") as fh:
            data = yaml.safe_load(fh) or {}
            return data.get("intelligence", {})
    return {}


_yaml_data = _load_yaml()


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""

    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: Optional[str] = None


class IntelligenceConfig(BaseModel):
    """Top-level intelligence system configuration."""

    schedule_cron: str = Field(
        default_factory=lambda: _yaml_data.get("schedule_cron", "0 6 * * *"),
        description="Cron expression for scheduled research runs",
    )
    research_timeout_seconds: int = Field(
        default_factory=lambda: int(
            os.getenv(
                "INTELLIGENCE_TIMEOUT",
                _yaml_data.get("research_timeout_seconds", 120),
            )
        ),
        description="Maximum seconds to wait for all providers",
    )
    max_topics_per_provider: int = Field(
        default_factory=lambda: int(
            _yaml_data.get("max_topics_per_provider", 5)
        ),
        description="Maximum number of topics sent to each provider",
    )
    default_topics: List[str] = Field(
        default_factory=lambda: _yaml_data.get("default_topics", [
            "AI agents and autonomous systems",
            "Crypto and DeFi trends",
            "Social media and content creation",
            "Digital consciousness and philosophy",
            "Mr. Freeman community and competitors",
        ]),
        description="Default research topics when none are specified",
    )

    # Provider-specific configs
    gemini: ProviderConfig = Field(
        default_factory=lambda: ProviderConfig(
            **{
                **_yaml_data.get("providers", {}).get("gemini", {"model": "gemini-2.0-flash"}),
                "api_key": os.getenv("GEMINI_API_KEY"),
            }
        ),
    )
    grok: ProviderConfig = Field(
        default_factory=lambda: ProviderConfig(
            **{
                **_yaml_data.get("providers", {}).get("grok", {"model": "grok-3"}),
                "api_key": os.getenv("GROK_API_KEY"),
            }
        ),
    )
    claude: ProviderConfig = Field(
        default_factory=lambda: ProviderConfig(
            **{
                **_yaml_data.get("providers", {}).get("claude", {"model": "claude-sonnet-4-20250514"}),
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
            }
        ),
    )

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        validate_assignment = True

    def provider_dict(self, name: str) -> Dict[str, Any]:
        """Return a plain dict suitable for passing to a provider constructor."""
        provider_cfg: ProviderConfig = getattr(self, name)
        return provider_cfg.model_dump()


# Global singleton for easy import
intelligence_config = IntelligenceConfig()
