"""ROMA (Reasoning-Oriented Modular Architecture) integration module

Handles ROMA result models, streaming, and visualization integration.
"""

from src.roma.models import (
    AtomizerResult,
    SubTask,
    PlannerResult,
    ExecutorResult,
    AggregatorResult,
    VerifierResult,
    WebSocketMessage,
    ReasoningUpdate,
)

from src.roma.websocket_server import (
    broadcast_message,
    create_app,
    get_connection_count,
    run_server,
    websocket_handler,
)

from src.roma.streaming_handler import (
    ROMAStreamingHandler,
    stream_module_result,
)

from src.roma.modules import (
    FreemanAtomizer,
    FreemanPlanner,
    FreemanExecutor,
    FreemanAggregator,
    FreemanVerifier,
)

__all__ = [
    "AtomizerResult",
    "SubTask",
    "PlannerResult",
    "ExecutorResult",
    "AggregatorResult",
    "VerifierResult",
    "WebSocketMessage",
    "ReasoningUpdate",
    # WebSocket server exports
    "create_app",
    "run_server",
    "broadcast_message",
    "get_connection_count",
    "websocket_handler",
    # Streaming handler exports
    "ROMAStreamingHandler",
    "stream_module_result",
    # Freeman ROMA modules
    "FreemanAtomizer",
    "FreemanPlanner",
    "FreemanExecutor",
    "FreemanAggregator",
    "FreemanVerifier",
]
