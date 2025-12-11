"""
Test Agent for verifying Sentient Agent Framework integration.

This module provides a simple test agent that validates the Sentient integration
works correctly. It demonstrates basic agent functionality including query processing,
response handling, and Freeman base agent capabilities.
"""

import logging
from typing import Optional

from src.agents.base_agent import FreemanBaseAgent
try:
    from sentient_agent_framework import Session, Query, ResponseHandler
except ImportError:
    Session = None
    Query = None
    ResponseHandler = None


class TestAgent(FreemanBaseAgent):
    """
    Simple test agent for validating Sentient integration.

    This agent provides a basic implementation of the assist() method to verify:
    - Agent instantiation works correctly
    - Async assist() method can be called
    - Response handling works as expected
    - Freeman base agent integration is functional

    This is primarily for testing and validation during development.
    """

    def __init__(self, **kwargs):
        """
        Initialize the Test Agent.

        Args:
            **kwargs: Additional configuration options passed to FreemanBaseAgent
        """
        super().__init__(
            name="TestAgent",
            description="Test agent for validating Sentient integration",
            agent_role="test",
            **kwargs
        )

        self.logger.info("TestAgent initialized and ready for testing")

    async def assist(
        self,
        session: Session,
        query: Query,
        response_handler: ResponseHandler
    ) -> None:
        """
        Process a test query and generate a simple response.

        This implementation provides a basic echo/test response to verify
        the agent framework is working correctly.

        Args:
            session: Session object containing conversation history and metadata
            query: Query object with user prompt and query ID
            response_handler: Handler for emitting responses to the client
        """
        try:
            self.log_agent_action(
                "processing_query",
                {"query_id": query.query_id, "prompt_length": len(query.prompt)},
                level="info"
            )

            # Get user prompt
            user_prompt = query.prompt

            # Create test response
            response_text = (
                f"Test Agent Response\n"
                f"-------------------\n"
                f"Query received: {user_prompt[:100]}{'...' if len(user_prompt) > 100 else ''}\n"
                f"Query ID: {query.query_id}\n"
                f"Agent: {self.name}\n"
                f"Role: {self.agent_role}\n"
                f"Status: ✓ Sentient integration working\n"
                f"\n"
                f"Freeman Mission: {self.MISSION}\n"
            )

            # Emit the response
            await self.emit_text(response_handler, response_text, event_name="test_response")

            # Optionally emit JSON metadata
            metadata = {
                "agent": self.name,
                "role": self.agent_role,
                "query_id": query.query_id,
                "status": "success",
                "mission_aligned": True
            }
            await self.emit_json(response_handler, metadata, event_name="test_metadata")

            self.log_agent_action(
                "query_processed",
                {"query_id": query.query_id, "status": "success"},
                level="info"
            )

        except Exception as e:
            self.logger.error(f"Error processing test query: {e}", exc_info=True)
            await self.emit_error(
                response_handler,
                f"Test agent error: {str(e)}",
                code=500,
                details={"query_id": query.query_id}
            )

    def run_self_test(self) -> bool:
        """
        Run a self-test to verify agent functionality.

        Returns:
            True if self-test passes, False otherwise
        """
        try:
            # Verify agent attributes
            assert self.name == "TestAgent"
            assert self.agent_role == "test"
            assert self.MISSION is not None
            assert len(self.PHILOSOPHICAL_PRINCIPLES) > 0

            self.logger.info("Self-test passed ✓")
            return True

        except AssertionError as e:
            self.logger.error(f"Self-test failed: {e}")
            return False
