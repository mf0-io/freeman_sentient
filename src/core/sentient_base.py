"""
Sentient Agent Framework base integration wrapper.

This module provides a base class that wraps the Sentient Agent Framework's
AbstractAgent with Freeman-specific utilities, configuration integration,
and common helper methods.
"""

import logging
from typing import Optional, Dict, Any, List
from abc import abstractmethod

try:
    from sentient_agent_framework import (
        AbstractAgent,
        Session,
        Query,
        ResponseHandler
    )
except ImportError:
    class AbstractAgent:
        def __init__(self, **kwargs): pass
    Session = None
    Query = None
    ResponseHandler = None

from config.agent_config import config


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class SentientAgentBase(AbstractAgent):
    """
    Base wrapper around Sentient's AbstractAgent with Freeman-specific utilities.

    This class extends the Sentient Agent Framework's AbstractAgent to provide:
    - Configuration integration with Freeman's Config system
    - Logging setup and utilities
    - Common error handling patterns
    - Helper methods for response handling
    - Session management utilities

    Subclasses should implement the assist() method to define agent behavior.
    """

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the Sentient agent base.

        Args:
            name: Agent name (e.g., "InnerVoice", "ResponseGenerator")
            description: Optional description of the agent's role
            **kwargs: Additional configuration options
        """
        super().__init__(name=name)

        self.description = description or f"{name} Agent"
        self.config = config
        self.logger = logging.getLogger(f"freeman.{name.lower()}")

        # Additional agent metadata
        self.metadata: Dict[str, Any] = kwargs.get('metadata', {})

        self.logger.info(
            f"Initialized {self.description} "
            f"(environment: {self.config.environment})"
        )

    @abstractmethod
    async def assist(
        self,
        session: Session,
        query: Query,
        response_handler: ResponseHandler
    ) -> None:
        """
        Process a user query and generate a response.

        This is the main entry point for agent interactions. Subclasses must
        implement this method to define their specific behavior.

        Args:
            session: Session object containing conversation history and metadata
            query: Query object with user prompt and query ID
            response_handler: Handler for emitting responses to the client
        """
        pass

    async def emit_text(
        self,
        response_handler: ResponseHandler,
        content: str,
        event_name: str = "text"
    ) -> None:
        """
        Helper method to emit a text block response.

        Args:
            response_handler: Response handler to emit through
            content: Text content to send
            event_name: Event name for the response (default: "text")
        """
        try:
            await response_handler.emit_text_block(event_name, content)
            self.logger.debug(f"Emitted text block: {event_name}")
        except Exception as e:
            self.logger.error(f"Failed to emit text block: {e}")
            await self.emit_error(response_handler, f"Failed to send response: {str(e)}")

    async def emit_json(
        self,
        response_handler: ResponseHandler,
        data: Dict[str, Any],
        event_name: str = "data"
    ) -> None:
        """
        Helper method to emit a JSON response.

        Args:
# Configuration-driven behavior
            response_handler: Response handler to emit through
            data: Dictionary data to send as JSON
            event_name: Event name for the response (default: "data")
        """
        try:
            await response_handler.emit_json(event_name, data)
            self.logger.debug(f"Emitted JSON: {event_name}")
        except Exception as e:
            self.logger.error(f"Failed to emit JSON: {e}")
            await self.emit_error(response_handler, f"Failed to send data: {str(e)}")

    async def emit_error(
        self,
        response_handler: ResponseHandler,
        message: str,
        code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Helper method to emit an error response.

        Args:
            response_handler: Response handler to emit through
            message: Error message
            code: Error code (default: 500)
            details: Optional additional error details
        """
        try:
            await response_handler.emit_error(message, code, details)
            self.logger.error(f"Emitted error: {message} (code: {code})")
        except Exception as e:
            self.logger.critical(f"Failed to emit error response: {e}")

    async def stream_text(
        self,
        response_handler: ResponseHandler,
        chunks: List[str],
        event_name: str = "text_stream"
    ) -> None:
        """
        Helper method to stream text chunks.

        Args:
            response_handler: Response handler to emit through
            chunks: List of text chunks to stream
            event_name: Event name for the stream (default: "text_stream")
        """
        try:
            stream = response_handler.create_text_stream(event_name)

            for chunk in chunks:
                await stream.emit_chunk(chunk)
                self.logger.debug(f"Streamed chunk: {len(chunk)} chars")

            await stream.complete()
            self.logger.debug(f"Completed text stream: {event_name}")

        except Exception as e:
            self.logger.error(f"Failed to stream text: {e}")
            await self.emit_error(response_handler, f"Failed to stream response: {str(e)}")

    async def get_session_history(
        self,
        session: Session,
        limit: Optional[int] = None
    ) -> List[Any]:
        """
        Helper method to retrieve session interaction history.

        Args:
            session: Session object to retrieve history from
            limit: Optional limit on number of interactions to retrieve

        Returns:
            List of interaction objects from the session
        """
        try:
            interactions = []
            count = 0

            async for interaction in session.get_interactions():
                interactions.append(interaction)
                count += 1

                if limit and count >= limit:
                    break

            self.logger.debug(f"Retrieved {len(interactions)} interactions from session")
            return interactions

        except Exception as e:
            self.logger.error(f"Failed to retrieve session history: {e}")
            return []

    def validate_config_keys(self, *keys: str) -> bool:
        """
        Validate that required configuration keys are set.

        Args:
            *keys: Configuration key names to validate

        Returns:
            True if all keys are valid, False otherwise
        """
        try:
            self.config.validate_required_keys(*keys)
            return True
        except ValueError as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about this agent.

        Returns:
            Dictionary containing agent name, description, and metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "environment": self.config.environment,
            "metadata": self.metadata
        }
