"""ROMA streaming handler for real-time reasoning visualization

This module provides a wrapper around ROMA module.forward() calls that captures
results and broadcasts them to connected WebSocket clients for visualization.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from src.roma.models import (
    AtomizerResult,
    PlannerResult,
    ExecutorResult,
    AggregatorResult,
    VerifierResult,
    WebSocketMessage,
    ReasoningUpdate,
)
from src.roma.websocket_server import broadcast_message, get_connection_count


logger = logging.getLogger(__name__)


class ROMAStreamingHandler:
    """Handler for streaming ROMA module results to WebSocket clients

    This class wraps ROMA module execution and broadcasts results in real-time
    to connected visualization clients via WebSocket.

    The streaming flow:
        1. ROMA module is called via forward()
        2. Result object is captured
        3. Result is converted to WebSocket message format
        4. Message is broadcast to all connected clients
        5. Original result is returned to caller

    Usage:
        handler = ROMAStreamingHandler()

        # Stream atomizer result
        result = await handler.stream_atomizer(
            atomizer_module,
            task="What is the meaning of life?"
        )

        # Stream planner result
        plan = await handler.stream_planner(
            planner_module,
            task="Explain quantum computing"
        )
    """

    def __init__(self, session_id: Optional[str] = None):
        """Initialize the streaming handler

        Args:
            session_id: Optional session identifier for grouping related messages
        """
        self._session_id = session_id or _generate_session_id()
        self._message_counter = 0
        self._start_time = datetime.utcnow()

        logger.debug(f"ROMAStreamingHandler initialized with session_id: {self._session_id}")

    async def stream_atomizer(
        self,
        module: Any,
        task: str,
        **kwargs
    ) -> AtomizerResult:
        """Stream Atomizer module execution and results

        Args:
            module: The Atomizer module instance
            task: The task to analyze for atomicity
            **kwargs: Additional arguments to pass to module.forward()

        Returns:
            AtomizerResult object from the module execution

        Raises:
            Exception: If module execution fails (error is broadcast before re-raising)
        """
        return await self._stream_module_execution(
            module=module,
            module_name="atomizer",
            inputs={"task": task, **kwargs},
            result_type=AtomizerResult
        )

    async def stream_planner(
        self,
        module: Any,
        task: str,
        **kwargs
    ) -> PlannerResult:
        """Stream Planner module execution and results

        Args:
            module: The Planner module instance
            task: The task to decompose into subtasks
            **kwargs: Additional arguments to pass to module.forward()

        Returns:
            PlannerResult object from the module execution

        Raises:
            Exception: If module execution fails (error is broadcast before re-raising)
        """
        return await self._stream_module_execution(
            module=module,
            module_name="planner",
            inputs={"task": task, **kwargs},
            result_type=PlannerResult
        )

    async def stream_executor(
        self,
        module: Any,
        task: str,
        **kwargs
    ) -> ExecutorResult:
        """Stream Executor module execution and results

        Args:
            module: The Executor module instance
            task: The task to execute
            **kwargs: Additional arguments to pass to module.forward()

        Returns:
            ExecutorResult object from the module execution

        Raises:
            Exception: If module execution fails (error is broadcast before re-raising)
        """
        return await self._stream_module_execution(
            module=module,
            module_name="executor",
            inputs={"task": task, **kwargs},
            result_type=ExecutorResult
        )

    async def stream_aggregator(
        self,
        module: Any,
        task: str,
        subtask_results: list,
        **kwargs
    ) -> AggregatorResult:
        """Stream Aggregator module execution and results

        Args:
            module: The Aggregator module instance
            task: The original task that generated the subtasks
            subtask_results: Results from individual subtask executions
            **kwargs: Additional arguments to pass to module.forward()

        Returns:
            AggregatorResult object from the module execution

        Raises:
            Exception: If module execution fails (error is broadcast before re-raising)
        """
        return await self._stream_module_execution(
            module=module,
            module_name="aggregator",
            inputs={
                "task": task,
                "subtask_results": subtask_results,
                **kwargs
            },
            result_type=AggregatorResult
        )

    async def stream_verifier(
        self,
        module: Any,
        task: str,
        result: Any,
        **kwargs
    ) -> VerifierResult:
        """Stream Verifier module execution and results

        Args:
            module: The Verifier module instance
            task: The original task
            result: The result to verify
            **kwargs: Additional arguments to pass to module.forward()

        Returns:
            VerifierResult object from the module execution

        Raises:
            Exception: If module execution fails (error is broadcast before re-raising)
        """
        return await self._stream_module_execution(
            module=module,
            module_name="verifier",
            inputs={
                "task": task,
                "result": result,
                **kwargs
            },
            result_type=VerifierResult
        )

    async def stream_update(
        self,
        module: str,
        stage: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Stream a custom reasoning update

        This method allows sending custom updates during processing that don't
        correspond to a complete module result.

        Args:
            module: Which ROMA module produced this update
            stage: Processing stage (input, processing, output, error)
            content: Human-readable content for display
            metadata: Additional metadata for the visualization component
        """
        try:
            update = ReasoningUpdate(
                type=module,
                module=module,
                stage=stage,
                content=content,
                metadata=metadata or {},
                timestamp=datetime.utcnow(),
                session_id=self._session_id,
                message_id=self._next_message_id()
            )

            message = update.model_dump(mode="json", exclude_none=True)
            await broadcast_message(message)

            logger.debug(
                f"Streamed update: module={module}, stage={stage}, "
                f"clients={get_connection_count()}"
            )

        except Exception as e:
            logger.error(f"Failed to stream update: {e}", exc_info=True)

    async def stream_error(
        self,
        module: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Stream an error message to clients

        Args:
            module: Which module encountered the error
            error_message: Human-readable error description
            details: Additional error details
        """
        try:
            message = {
                "type": "error",
                "module": module,
                "error": error_message,
                "details": details or {},
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "session_id": self._session_id,
                "message_id": self._next_message_id()
            }

            await broadcast_message(message)
            logger.warning(f"Streamed error: module={module}, error={error_message}")

        except Exception as e:
            logger.error(f"Failed to stream error message: {e}", exc_info=True)

    async def stream_complete(
        self,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Stream a completion message

        Args:
            summary: Summary of the completed reasoning process
            metadata: Additional metadata about the execution
        """
        try:
            duration = (datetime.utcnow() - self._start_time).total_seconds()

            message = {
                "type": "complete",
                "summary": summary,
                "duration_seconds": duration,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "session_id": self._session_id,
                "message_id": self._next_message_id()
            }

            await broadcast_message(message)
            logger.info(
                f"Streamed completion: duration={duration}s, "
                f"session={self._session_id}"
            )

        except Exception as e:
            logger.error(f"Failed to stream completion: {e}", exc_info=True)

    async def _stream_module_execution(
        self,
        module: Any,
        module_name: str,
        inputs: Dict[str, Any],
        result_type: type
    ) -> Any:
        """Internal method to stream module execution

        This is the core streaming logic that:
        1. Sends input/update message before execution
        2. Executes the module's forward() method
        3. Parses the result using the appropriate Pydantic model
        4. Broadcasts the result to WebSocket clients
        5. Returns the parsed result

        Args:
            module: The ROMA module instance
            module_name: Name of the module (for logging and messages)
            inputs: Input parameters for the module
            result_type: Pydantic model type for parsing the result

        Returns:
            Parsed result object of type result_type

        Raises:
            Exception: If module execution fails
        """
        # Send processing start message
        await self.stream_update(
            module=module_name,
            stage="input",
            content=f"Starting {module_name} processing...",
            metadata={"inputs": _sanitize_inputs(inputs)}
        )

        try:
            # Execute the module
            logger.debug(f"Executing {module_name}.forward() with inputs: {list(inputs.keys())}")

            # Check if forward is async or sync
            if asyncio.iscoroutinefunction(module.forward):
                result_raw = await module.forward(**inputs)
            else:
                result_raw = module.forward(**inputs)

            # Parse result with Pydantic model
            if result_raw is None:
                raise ValueError(f"{module_name}.forward() returned None")

            # Convert dict to result type if needed
            if isinstance(result_raw, dict):
                result = result_type(**result_raw)
            elif isinstance(result_raw, result_type):
                result = result_raw
            else:
                # Try to create from object's attributes
                result = result_type.model_validate(result_raw)

            # Broadcast the result
            await self._broadcast_result(module_name, result)

            logger.info(
                f"{module_name} executed successfully, "
                f"broadcasted to {get_connection_count()} clients"
            )

            return result

        except Exception as e:
            logger.error(f"Error executing {module_name}: {e}", exc_info=True)

            # Stream error to clients
            await self.stream_error(
                module=module_name,
                error_message=str(e),
                details={"module": module_name, "inputs": _sanitize_inputs(inputs)}
            )

            # Re-raise for caller to handle
            raise

    async def _broadcast_result(self, module_name: str, result: Any) -> None:
        """Broadcast a module result to WebSocket clients

        Args:
            module_name: Name of the module that produced the result
            result: The result object to broadcast
        """
        try:
            # Convert result to dict for JSON serialization
            if hasattr(result, "model_dump"):
                result_dict = result.model_dump(mode="json", exclude_none=True)
            elif hasattr(result, "dict"):
                result_dict = result.dict(exclude_none=True)
            elif isinstance(result, dict):
                result_dict = result
            else:
                result_dict = {"raw_result": str(result)}

            # Create WebSocket message
            message = {
                "type": module_name,
                "data": result_dict,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "session_id": self._session_id,
                "message_id": self._next_message_id()
            }

            await broadcast_message(message)

        except Exception as e:
            logger.error(f"Failed to broadcast {module_name} result: {e}", exc_info=True)

    def _next_message_id(self) -> str:
        """Generate the next message ID

        Returns:
            Unique message identifier
        """
        self._message_counter += 1
        return f"{self._session_id}_msg_{self._message_counter}"

    @property
    def session_id(self) -> str:
        """Get the session ID for this handler

        Returns:
            Session identifier string
        """
        return self._session_id

    @property
    def message_count(self) -> int:
        """Get the number of messages sent by this handler

        Returns:
            Number of messages sent
        """
        return self._message_counter


def _generate_session_id() -> str:
    """Generate a unique session ID

    Returns:
        Unique session identifier string
    """
    import time
    import random
    import string

    timestamp = int(time.time() * 1000)
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"session_{timestamp}_{random_str}"


def _sanitize_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize input parameters for logging/transmission

    Removes sensitive data and limits the size of values.

    Args:
        inputs: Raw input parameters

    Returns:
        Sanitized input dictionary
    """
    MAX_LEN = 500
    sensitive_keys = {"api_key", "token", "password", "secret"}

    sanitized = {}
    for key, value in inputs.items():
        # Redact sensitive keys
        if key.lower() in sensitive_keys:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, str):
            sanitized[key] = value[:MAX_LEN] + ("..." if len(value) > MAX_LEN else "")
        elif isinstance(value, (list, dict)):
            sanitized[key] = f"<{type(value).__name__} with {len(value)} items>"
        else:
            sanitized[key] = str(value)[:MAX_LEN]

    return sanitized


# Convenience function for quick streaming without creating handler instance
async def stream_module_result(
    module_name: str,
    result: Any,
    session_id: Optional[str] = None
) -> None:
    """Quickly stream a module result without a handler instance

    This is a convenience function for one-off streaming scenarios.

    Args:
        module_name: Name of the module that produced the result
        result: The result object to stream
        session_id: Optional session identifier
    """
    try:
        # Convert result to dict
        if hasattr(result, "model_dump"):
            result_dict = result.model_dump(mode="json", exclude_none=True)
        elif hasattr(result, "dict"):
            result_dict = result.dict(exclude_none=True)
        elif isinstance(result, dict):
            result_dict = result
        else:
            result_dict = {"raw_result": str(result)}

        message = {
            "type": module_name,
            "data": result_dict,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "session_id": session_id or _generate_session_id(),
            "message_id": f"quick_{int(datetime.utcnow().timestamp() * 1000)}"
        }

        await broadcast_message(message)
        logger.debug(f"Quick-streamed {module_name} result")

    except Exception as e:
        logger.error(f"Failed to quick-stream result: {e}", exc_info=True)


__all__ = [
    "ROMAStreamingHandler",
    "stream_module_result",
]
