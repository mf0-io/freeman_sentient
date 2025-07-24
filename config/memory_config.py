"""Memory system configuration module.

This module provides configuration management for the Digital Freeman memory system,
loading settings from environment variables with sensible defaults.
"""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MemoryConfig(BaseSettings):
    """Configuration for the memory system using Graphiti and related services.

    All settings can be overridden via environment variables.
    See .env.example for all available configuration options.
    """

    # Graphiti MCP Server Configuration
    graphiti_mcp_server_url: str = Field(
        default="http://localhost:8080",
        description="Graphiti MCP server URL"
    )
    graphiti_mcp_timeout: int = Field(
        default=30,
        description="Timeout for MCP server requests in seconds"
    )

    # Graphiti Database Configuration (Neo4j)
    graphiti_db_host: str = Field(
        default="localhost",
        description="Neo4j database host"
    )
    graphiti_db_port: int = Field(
        default=7687,
        description="Neo4j database port"
    )
    graphiti_db_user: str = Field(
        default="neo4j",
        description="Neo4j database username"
    )
    graphiti_db_password: str = Field(
        default="",
        description="Neo4j database password"
    )
    graphiti_db_name: str = Field(
        default="graphiti",
        description="Neo4j database name"
    )

    # Memory Storage Configuration
    graphiti_data_path: Path = Field(
        default=Path("./data/memory"),
        description="Local file-based storage path for memory data"
    )
    graphiti_max_entities: int = Field(
        default=10000,
        description="Maximum number of entities to store"
    )
    graphiti_max_episodes: int = Field(
        default=50000,
        description="Maximum number of episodes to store"
    )
    graphiti_search_limit: int = Field(
        default=10,
        description="Default limit for search results"
    )
    graphiti_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model for semantic search"
    )

    # LLM API Configuration
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for embeddings and optional LLM"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        description="Anthropic Claude API key (primary LLM)"
    )
    llm_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="Primary LLM model identifier"
    )
    llm_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature for response generation"
    )
    llm_max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum tokens for LLM responses"
    )

    # Relationship Scoring Thresholds
    relationship_stranger_threshold: int = Field(
        default=0,
        description="Points threshold for 'stranger' relationship level"
    )
    relationship_acquaintance_threshold: int = Field(
        default=10,
        description="Points threshold for 'acquaintance' relationship level"
    )
# Validated input parameters
    relationship_friend_threshold: int = Field(
        default=50,
        description="Points threshold for 'friend' relationship level"
    )
    relationship_ally_threshold: int = Field(
        default=200,
        description="Points threshold for 'ally' relationship level"
    )

    # Action Scoring
    action_like_points: int = Field(
        default=1,
        description="Points awarded for a 'like' action"
    )
    action_share_points: int = Field(
        default=3,
        description="Points awarded for a 'share' action"
    )
    action_comment_points: int = Field(
        default=5,
        description="Points awarded for a 'comment' action"
    )
    action_purchase_token_points: int = Field(
        default=50,
        description="Points awarded for a 'purchase token' action"
    )

    # Memory Retention
    memory_retention_days: int = Field(
        default=365,
        gt=0,
        description="Number of days to retain memory data"
    )
    memory_cleanup_enabled: bool = Field(
        default=False,
        description="Whether to enable automatic memory cleanup"
    )

    # Application Settings
    environment: str = Field(
        default="development",
        description="Application environment (development, staging, production)"
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def get_neo4j_uri(self) -> str:
        """Get the Neo4j connection URI."""
        return f"bolt://{self.graphiti_db_host}:{self.graphiti_db_port}"

    def get_relationship_level(self, points: int) -> str:
        """Determine relationship level based on points.

        Args:
            points: Total relationship points

        Returns:
            Relationship level name (stranger, acquaintance, friend, ally)
        """
        if points >= self.relationship_ally_threshold:
            return "ally"
        elif points >= self.relationship_friend_threshold:
            return "friend"
        elif points >= self.relationship_acquaintance_threshold:
            return "acquaintance"
        else:
            return "stranger"

    def get_action_points(self, action_type: str) -> int:
        """Get points for a specific action type.

        Args:
            action_type: Type of action (like, share, comment, purchase_token)

        Returns:
            Points value for the action

        Raises:
            ValueError: If action_type is not recognized
        """
        action_points_map = {
            "like": self.action_like_points,
            "share": self.action_share_points,
            "comment": self.action_comment_points,
            "purchase_token": self.action_purchase_token_points,
        }

        if action_type not in action_points_map:
            raise ValueError(
                f"Unknown action type: {action_type}. "
                f"Valid types: {', '.join(action_points_map.keys())}"
            )

        return action_points_map[action_type]

    def ensure_data_path(self) -> None:
        """Ensure the memory data directory exists."""
        self.graphiti_data_path.mkdir(parents=True, exist_ok=True)


# Global configuration instance
# This can be imported and used throughout the application
config = MemoryConfig()
