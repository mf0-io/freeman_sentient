"""WebSocket server for real-time ROMA reasoning visualization

This module provides an aiohttp-based WebSocket server that streams
reasoning data from ROMA modules to connected visualization clients.
"""

import asyncio
import json
import logging
from typing import Set, Optional

from aiohttp import web, WSMsgType, WSMessage
from aiohttp.web import Application

from config.agent_config import config


logger = logging.getLogger(__name__)


# Global set to track active WebSocket connections
_active_connections: Set[web.WebSocketResponse] = set()


async def websocket_handler(request: web.Request) -> web.WebSocketResponse:
    """Handle WebSocket connections for reasoning streaming.

    This handler manages the WebSocket connection lifecycle for visualization clients.
    It accepts incoming connections, receives messages, and broadcasts reasoning updates.

    Args:
        request: The aiohttp web request object

    Returns:
        WebSocket response object for the connected client

    Raises:
        Exception: If WebSocket preparation fails (logged, not propagated)
    """
    ws = web.WebSocketResponse(
        heartbeat=30,  # Send ping every 30 seconds
        timeout=10,    # Connection timeout
    )
    await ws.prepare(request)

    # Register this connection
    _active_connections.add(ws)
    remote_addr = request.remote
    logger.info(f"WebSocket connection established from {remote_addr}")
    logger.info(f"Active connections: {len(_active_connections)}")

    try:
        # Send initial connection confirmation
        await ws.send_json({
            "type": "status",
            "status": "connected",
            "message": "Successfully connected to ROMA reasoning visualizer",
            "timestamp": _get_timestamp()
        })

        # Message loop
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    logger.debug(f"Received message from {remote_addr}: {data}")

                    # Handle client messages (could be used for control signals)
                    await _handle_client_message(ws, data)

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON received from {remote_addr}: {e}")
                    await ws.send_json({
                        "type": "error",
                        "message": "Invalid JSON format",
                        "timestamp": _get_timestamp()
                    })
                except Exception as e:
                    logger.error(f"Error handling message from {remote_addr}: {e}", exc_info=True)
                    await ws.send_json({
                        "type": "error",
                        "message": "Internal server error",
                        "timestamp": _get_timestamp()
                    })

            elif msg.type == WSMsgType.ERROR:
                logger.error(f"WebSocket error for {remote_addr}: {ws.exception()}")

            elif msg.type == WSMsgType.CLOSE:
                logger.info(f"WebSocket close request received from {remote_addr}")
                break

    except asyncio.CancelledError:
        logger.info(f"WebSocket connection cancelled for {remote_addr}")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler for {remote_addr}: {e}", exc_info=True)
    finally:
        # Unregister this connection
        _active_connections.discard(ws)
        logger.info(f"WebSocket connection closed from {remote_addr}")
        logger.info(f"Active connections: {len(_active_connections)}")

    return ws


async def _handle_client_message(ws: web.WebSocketResponse, data: dict) -> None:
    """Handle incoming messages from WebSocket clients.

    Args:
        ws: The WebSocket response object
        data: Parsed JSON message data from the client

    Raises:
        ValueError: If message format is invalid
    """
    message_type = data.get("type")

    if message_type == "ping":
        # Respond to ping with pong
        await ws.send_json({
            "type": "pong",
            "timestamp": _get_timestamp()
        })
    elif message_type == "subscribe":
        # Handle subscription to specific reasoning streams
        modules = data.get("modules", [])
        logger.info(f"Client subscribed to modules: {modules}")
        await ws.send_json({
            "type": "subscribed",
            "modules": modules,
            "timestamp": _get_timestamp()
        })
    else:
        logger.warning(f"Unknown message type: {message_type}")


async def broadcast_message(message: dict) -> None:
    """Broadcast a message to all active WebSocket connections.

    This is the primary method used by the streaming handler to send
    ROMA reasoning updates to all connected visualization clients.

    Args:
        message: The message dictionary to broadcast (will be JSON serialized)

    Note:
        Failed sends to individual clients are logged but don't stop
        broadcasting to other clients.
    """
    if not _active_connections:
        logger.debug("No active connections to broadcast to")
        return

    # Ensure message has timestamp
    if "timestamp" not in message:
        message["timestamp"] = _get_timestamp()

    # Prepare JSON once for efficiency
    message_json = json.dumps(message)

    # Track successful and failed sends
    successful = 0
    failed = 0

    # Create a list of connections to remove
    to_remove = []

    for ws in list(_active_connections):
        if ws.closed:
            to_remove.append(ws)
            continue

        try:
            await ws.send_str(message_json)
            successful += 1
        except Exception as e:
            logger.warning(f"Failed to send to client: {e}")
            failed += 1
            to_remove.append(ws)

    # Remove dead connections
    for ws in to_remove:
        _active_connections.discard(ws)

    if successful > 0:
        logger.debug(f"Broadcast message to {successful} clients (type: {message.get('type', 'unknown')})")

    if failed > 0:
        logger.warning(f"Failed to send to {failed} clients")


def get_connection_count() -> int:
    """Get the current number of active WebSocket connections.

    Returns:
        Number of active WebSocket connections
    """
    return len(_active_connections)


def _get_timestamp() -> str:
    """Get current timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp string
    """
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


def create_app() -> Application:
    """Create and configure the aiohttp WebSocket application.

    This function creates the aiohttp application with WebSocket routes
    and returns it for use by the main server.

    Returns:
        Configured aiohttp Application instance

    Raises:
        Exception: If application creation fails (logged and propagated)
    """
    try:
        app = web.Application()

        # Add WebSocket route
        app.router.add_get('/reasoning', websocket_handler)

        # Add health check endpoint
        app.router.add_get('/health', health_check_handler)

        # Add connection info endpoint
        app.router.add_get('/info', connection_info_handler)

        logger.info(f"WebSocket application created successfully")
        logger.info(f"WebSocket endpoint: ws://{config.reasoning_ws_host}:{config.reasoning_ws_port}/reasoning")
        logger.info(f"Health check: http://{config.reasoning_ws_host}:{config.reasoning_ws_port}/health")
        logger.info(f"Connection info: http://{config.reasoning_ws_host}:{config.reasoning_ws_port}/info")

        return app

    except Exception as e:
        logger.error(f"Failed to create WebSocket application: {e}", exc_info=True)
        raise


async def health_check_handler(request: web.Request) -> web.Response:
    """Health check endpoint for the WebSocket server.

    Args:
        request: The aiohttp web request object

    Returns:
        JSON response with health status
    """
    return web.json_response({
        "status": "healthy",
        "service": "ROMA WebSocket Server",
        "active_connections": get_connection_count(),
        "timestamp": _get_timestamp()
    })


async def connection_info_handler(request: web.Request) -> web.Response:
    """Connection information endpoint.

    Args:
        request: The aiohttp web request object

    Returns:
        JSON response with connection information
    """
    return web.json_response({
        "service": "ROMA WebSocket Server",
        "active_connections": get_connection_count(),
        "host": config.reasoning_ws_host,
        "port": config.reasoning_ws_port,
        "endpoints": {
            "websocket": f"ws://{config.reasoning_ws_host}:{config.reasoning_ws_port}/reasoning",
            "health": f"http://{config.reasoning_ws_host}:{config.reasoning_ws_port}/health",
            "info": f"http://{config.reasoning_ws_host}:{config.reasoning_ws_port}/info"
        },
        "timestamp": _get_timestamp()
    })


async def run_server(app: Optional[Application] = None) -> None:
    """Run the WebSocket server.

    This is a convenience function to run the WebSocket server directly.
    For production, use create_app() and integrate with your main server.

    Args:
        app: Optional pre-created Application instance. If None, creates one.

    Raises:
        Exception: If server startup fails
    """
    if app is None:
        app = create_app()

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(
        runner,
        config.reasoning_ws_host,
        config.reasoning_ws_port
    )

    await site.start()
    logger.info(f"WebSocket server started on ws://{config.reasoning_ws_host}:{config.reasoning_ws_port}")
    logger.info(f"Reasoning endpoint: /reasoning")

    try:
        # Keep server running
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
    except asyncio.CancelledError:
        logger.info("WebSocket server shutdown requested")
    finally:
        await runner.cleanup()
        logger.info("WebSocket server stopped")


# Export broadcast_message for use by streaming_handler
__all__ = [
    "create_app",
    "run_server",
    "broadcast_message",
    "get_connection_count",
    "websocket_handler",
]
