#!/usr/bin/env python3
"""
Main entry point for Freeman Sentient Agent Framework.

Supports two modes:
1. ROMA mode (default): Runs the ROMA framework with WebSocket visualization
2. Content CLI mode: Content creation pipeline management (via subcommands)

Usage:
    # ROMA mode (default)
    python src/main.py

    # Content CLI mode
    python src/main.py generate-content --count 3
    python src/main.py list-queue
    python src/main.py status
"""

import argparse
import asyncio
import logging
import sys
import threading
import time
from typing import Optional
from datetime import datetime
from pathlib import Path

try:
    import dspy
    from roma_dspy import solve
    from roma_dspy.core.registry import AgentRegistry
    ROMA_AVAILABLE = True
except ImportError:
    dspy = None
    solve = None
    AgentRegistry = None
    ROMA_AVAILABLE = False

from config.agent_config import config

try:
    from src.roma.websocket_server import run_server, create_app
except ImportError:
    run_server = None
    create_app = None

from src.agents.content_creator import ContentCreatorAgent
from src.content.storage import ContentQueue


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.log_level.upper(), logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("freeman.main")


# ==============================================================================
# ROMA Framework Functions
# ==============================================================================

def configure_dspy() -> dspy.LM:
    """
    Configure DSPy with the appropriate LLM provider.

    Tries multiple providers in order of preference:
    1. OpenRouter (recommended - supports many models)
    2. Anthropic Claude
    3. OpenAI GPT
    4. Google Gemini

    Returns:
        Configured dspy.LM instance

    Raises:
        ValueError: If no API key is available
    """
    if not ROMA_AVAILABLE:
        logger.warning("ROMA framework not available (dspy/roma_dspy not installed)")
        return

    # Try OpenRouter first (recommended for ROMA)
    if config.openrouter_api_key:
        logger.info("Configuring DSPy with OpenRouter (Gemini 2.5 Flash)")
        return dspy.LM(
            'openrouter/google/gemini-2.5-flash',
            api_key=config.openrouter_api_key,
            cache=False  # Disable cache for development
        )

    # Try Anthropic Claude
    if config.anthropic_api_key:
        logger.info("Configuring DSPy with Anthropic Claude 3.5 Sonnet")
        return dspy.LM(
            'anthropic/claude-3.5-sonnet',
            api_key=config.anthropic_api_key,
            cache=False
        )

    # Try OpenAI
    if config.openai_api_key:
        logger.info("Configuring DSPy with OpenAI GPT-4o")
        return dspy.LM(
            'openai/gpt-4o',
            api_key=config.openai_api_key,
            cache=False
        )

    # Try Google
    if config.google_api_key:
        logger.info("Configuring DSPy with Google Gemini 2.5 Flash")
        return dspy.LM(
            'gemini/gemini-2.5-flash',
            api_key=config.google_api_key,
            cache=False
        )

    raise ValueError(
        "No LLM API key available. Please set one of: "
        "OPENROUTER_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY"
    )


def create_registry() -> AgentRegistry:
    """
    Create and configure the ROMA AgentRegistry with Freeman modules.

    Each module is configured with an appropriate LLM based on its role:
    - Atomizer: Fast reasoning model (Gemini Flash or similar)
    - Planner: Fast reasoning model for task decomposition
    - Executor: High-quality model for content generation
    - Aggregator: High-quality model for synthesis
    - Verifier: High-quality model for validation

    Returns:
        AgentRegistry with all Freeman modules registered

    Raises:
        Exception: If module initialization fails
    """
    if not ROMA_AVAILABLE:
        logger.warning("ROMA framework not available (dspy/roma_dspy not installed)")
        return

    try:
        logger.info("Initializing ROMA framework with Freeman agent modules...")
        logger.info(f"Environment: {config.environment}")

        # Get the default LM from DSPy configuration
        default_lm = configure_dspy()
        dspy.configure(lm=default_lm)

        # Initialize Freeman ROMA modules with appropriate LLMs
        from src.roma.modules import (
            FreemanAtomizer, FreemanPlanner, FreemanExecutor,
            FreemanAggregator, FreemanVerifier,
        )

        # Atomizer: Fast model for task analysis
        atomizer = FreemanAtomizer(lm=default_lm)
        logger.info(f"  ✓ Atomizer: {atomizer.__class__.__name__}")

        # Planner: Fast model for task decomposition
        planner = FreemanPlanner(lm=default_lm)
        logger.info(f"  ✓ Planner: {planner.__class__.__name__}")

        # Executor: High-quality model for content generation
        if config.anthropic_api_key:
            executor_lm = dspy.LM('anthropic/claude-3.5-sonnet', api_key=config.anthropic_api_key, cache=False)
        else:
            executor_lm = default_lm
        executor = FreemanExecutor(lm=executor_lm)
        logger.info(f"  ✓ Executor: {executor.__class__.__name__}")

        # Aggregator: High-quality model for synthesis
        if config.anthropic_api_key:
            aggregator_lm = dspy.LM('anthropic/claude-3.5-sonnet', api_key=config.anthropic_api_key, cache=False)
        else:
            aggregator_lm = default_lm
        aggregator = FreemanAggregator(lm=aggregator_lm)
        logger.info(f"  ✓ Aggregator: {aggregator.__class__.__name__}")

        # Verifier: High-quality model for validation
        if config.anthropic_api_key:
            verifier_lm = dspy.LM('anthropic/claude-3.5-sonnet', api_key=config.anthropic_api_key, cache=False)
        else:
            verifier_lm = default_lm
        verifier = FreemanVerifier(lm=verifier_lm)
        logger.info(f"  ✓ Verifier: {verifier.__class__.__name__}")

        # Create registry from modules
        registry = AgentRegistry.from_modules(
            atomizer=atomizer,
            planner=planner,
            executor=executor,
            aggregator=aggregator,
            verifier=verifier
        )

        logger.info("ROMA AgentRegistry created successfully")
        logger.info("Modules ready for task processing")

        return registry

    except Exception as e:
        logger.error(f"Failed to initialize ROMA modules: {e}", exc_info=True)
        raise


def _run_websocket_server():
    """
    Run the WebSocket server in a background thread.

    This function runs the aiohttp WebSocket server in a separate asyncio event loop,
    allowing it to run concurrently with the main ROMA system.
    """
    try:
        logger.info("Starting WebSocket server thread...")
        ws_app = create_app()
        asyncio.run(run_server(ws_app))
    except Exception as e:
        logger.error(f"WebSocket server error: {e}", exc_info=True)


def run_demo_task(registry: AgentRegistry) -> None:
    """
    Run a simple demo task to verify ROMA setup works.

    Args:
        registry: Configured AgentRegistry with Freeman modules
    """
    try:
        logger.info("=" * 60)
        logger.info("ROMA FRAMEWORK - FREEMAN SENTIENT AGENT")
        logger.info("=" * 60)
        logger.info("")
        from src.roma.modules.signatures import FREEMAN_MISSION
        logger.info("Architecture: Atomizer → Planner → Executor → Aggregator → Verifier")
        logger.info("Mission: " + FREEMAN_MISSION)
        logger.info("")
        logger.info("ROMA solve() function ready for task processing.")
        logger.info("")
        logger.info("To process a task, use:")
        logger.info("  result = solve('your task here', registry=registry)")
        logger.info("")
        logger.info("Example:")
        logger.info("  result = solve('Create a short post about digital freedom', registry=registry)")
        logger.info("")
        logger.info("WebSocket visualization available at:")
        logger.info(f"  ws://{config.reasoning_ws_host}:{config.reasoning_ws_port}/reasoning")
        logger.info("")
        logger.info("=" * 60)

        # Note: We don't run an actual task here to avoid API calls on startup
        # The system is ready to accept tasks via the solve() function

    except Exception as e:
        logger.error(f"Error in demo: {e}", exc_info=True)


def run_roma():
    """
    Run the ROMA framework entry point.

    Initializes ROMA modules, starts WebSocket server in background,
    and demonstrates the system is ready.
    """
    if not ROMA_AVAILABLE:
        logger.warning("ROMA framework not available (dspy/roma_dspy not installed)")
        return

    ws_thread: Optional[threading.Thread] = None

    try:
        # Create ROMA agent registry
        registry = create_registry()

        # Start WebSocket server in background thread
        logger.info("")
        logger.info("Starting WebSocket server in background...")
        logger.info(f"WebSocket endpoint: ws://{config.reasoning_ws_host}:{config.reasoning_ws_port}/reasoning")
        ws_thread = threading.Thread(
            target=_run_websocket_server,
            name="WebSocketServer",
            daemon=True
        )
        ws_thread.start()
        logger.info("WebSocket server thread started")

        # Run demo to show system is ready
        run_demo_task(registry)

        # Keep the application running
        logger.info("")
        logger.info("ROMA system initialized and ready.")
        logger.info("Press Ctrl+C to stop...")

        # Simple idle loop to keep the process running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("")
        logger.info("Shutting down ROMA Freeman agent...")
        if ws_thread and ws_thread.is_alive():
            logger.info("WebSocket server thread will stop (daemon thread)...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


# ==============================================================================
# Content Creation Pipeline CLI Functions
# ==============================================================================

def setup_directories():
    """Ensure required directories exist"""
    directories = ['data', 'config', 'prompts']
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def cmd_generate_content(args):
    """Generate new content"""
    try:
        logger.info(f"Generating {args.count} content piece(s)...")
        agent = ContentCreatorAgent(args.config)

        results = agent.generate_content(
            source=args.source,
            count=args.count,
            auto_schedule=not args.no_schedule
        )

        # Display results
        success_count = sum(1 for r in results if r.success)
        print(f"\n{'='*70}")
        print(f"Content Generation Complete: {success_count}/{args.count} successful")
        print(f"{'='*70}\n")

        for i, result in enumerate(results, 1):
            print(f"Content #{i}:")
            if result.success:
                print(f"  ✓ Status: SUCCESS")
                print(f"  ID: {result.content_id}")
                print(f"  Text: {result.text}")
                if result.scheduled_time:
                    print(f"  Scheduled: {result.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
                if result.idea:
                    print(f"  Topic: {result.idea.topic}")
                    print(f"  Source: {result.idea.source}")
                    print(f"  Tone: {result.idea.tone}")
                if result.validation_score:
                    print(f"  Validation Score: {result.validation_score:.2f}")
            else:
                print(f"  ✗ Status: FAILED")
                print(f"  Error: {result.error}")
                if result.text:
                    print(f"  Text (rejected): {result.text}")
            print()

        # Show pipeline status
        if args.verbose:
            status = agent.get_pipeline_status()
            print(f"\n{'='*70}")
            print("Pipeline Status:")
            print(f"{'='*70}")
            print(f"Queue Size: {status['queue']['total']}")
            print(f"  - Queued: {status['queue']['queued']}")
            print(f"  - Scheduled: {status['queue']['scheduled']}")
            print(f"  - Posted: {status['queue']['posted']}")
            print(f"Queue Health: {status['queue']['health']}")
            print()

        return 0 if success_count > 0 else 1

    except Exception as e:
        logger.error(f"Failed to generate content: {e}")
        if args.verbose:
            raise
        return 1


def cmd_list_queue(args):
    """List content in queue"""
    try:
        queue = ContentQueue(config_path=args.config)

        # Get content by status
        if args.status:
            content_list = queue.get_by_status(args.status)
            print(f"\nContent with status '{args.status}': {len(content_list)}")
        else:
            content_list = queue.queue
            print(f"\nAll content in queue: {len(content_list)}")

        if not content_list:
            print("Queue is empty.")
            return 0

        # Display content
        print(f"{'='*70}")
        for i, content in enumerate(content_list[:args.limit], 1):
            print(f"\n{i}. {content.id}")
            print(f"   Status: {content.status}")
            print(f"   Text: {content.text[:100]}{'...' if len(content.text) > 100 else ''}")
            print(f"   Topic: {content.topic}")
            print(f"   Source: {content.source}")
            print(f"   Tone: {content.tone}")
            print(f"   Created: {content.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if content.scheduled_time:
                print(f"   Scheduled: {content.scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")
            if content.posted_at:
                print(f"   Posted: {content.posted_at.strftime('%Y-%m-%d %H:%M:%S')}")

        if len(content_list) > args.limit:
            print(f"\n... and {len(content_list) - args.limit} more (use --limit to see more)")

        # Show statistics
        if args.verbose:
            stats = queue.get_stats()
            print(f"\n{'='*70}")
            print("Queue Statistics:")
            print(f"{'='*70}")
            print(f"Total: {stats['total']}")
            print(f"By Status:")
            for status, count in stats['by_status'].items():
                print(f"  - {status}: {count}")
            print(f"Next to Post: {stats['next_to_post']}")
            print()

        return 0

    except Exception as e:
        logger.error(f"Failed to list queue: {e}")
        if args.verbose:
            raise
        return 1


def cmd_post_now(args):
    """Post content immediately"""
    try:
        queue = ContentQueue()

        # Get content by ID or next scheduled
        if args.content_id:
            content = queue.get_by_id(args.content_id)
            if not content:
                print(f"Error: Content with ID '{args.content_id}' not found")
                return 1
        else:
            content = queue.get_next_to_post()
            if not content:
                print("No content ready to post. Queue may be empty.")
                return 1

        print(f"\nContent to post:")
        print(f"  ID: {content.id}")
        print(f"  Text: {content.text}")
        print(f"  Topic: {content.topic}")
        print()

        if not args.force:
            confirmation = input("Post this content now? [y/N]: ")
            if confirmation.lower() != 'y':
                print("Cancelled.")
                return 0

        # TODO: Implement actual posting to platforms
        # For now, just mark as posted
        print("\nPosting...")
        print("⚠️  Warning: Actual posting to platforms not yet implemented")
        print("    Marking as posted in queue...")

        queue.mark_posted(content.id)
        print(f"✓ Content {content.id} marked as posted")

        return 0

    except Exception as e:
        logger.error(f"Failed to post content: {e}")
        if args.verbose:
            raise
        return 1


def cmd_clear_queue(args):
    """Clear content from queue"""
    try:
        agent = ContentCreatorAgent(args.config)

        if not args.force:
            queue = agent.queue
            count = queue.size()
            if count == 0:
                print("Queue is already empty.")
                return 0

            confirmation = input(f"Clear {count} items from queue? [y/N]: ")
            if confirmation.lower() != 'y':
                print("Cancelled.")
                return 0

        result = agent.clear_queue(status=args.status)

        print(f"\n✓ Queue cleared")
        print(f"  Removed: {result['removed']}")
        if result['removed'] > 0:
            print(f"  Statuses cleared: {', '.join(result['statuses_cleared'])}")

        return 0

    except Exception as e:
        logger.error(f"Failed to clear queue: {e}")
        if args.verbose:
            raise
        return 1


def cmd_status(args):
    """Show pipeline status"""
    try:
        agent = ContentCreatorAgent(args.config)
        status = agent.get_pipeline_status()

        print(f"\n{'='*70}")
        print("Content Creation Pipeline Status")
        print(f"{'='*70}\n")

        # Queue status
        print("Queue:")
        print(f"  Total: {status['queue']['total']}")
        print(f"  Queued: {status['queue']['queued']}")
        print(f"  Scheduled: {status['queue']['scheduled']}")
        print(f"  Posted: {status['queue']['posted']}")
        print(f"  Health: {'OK' if status.get('health', {}).get('overall_healthy') else 'NEEDS ATTENTION'}")

        if status['queue'].get('needs_refill'):
            print(f"  ⚠️  Queue needs refill (below minimum)")

        # Component health
        print("\nComponents:")
        health = status.get('health', {})
        for component, is_healthy in health.items():
            if component == 'overall_healthy':
                continue
            symbol = "✓" if is_healthy else "✗"
            print(f"  {symbol} {component}: {'OK' if is_healthy else 'ERROR'}")

        # Statistics
        if args.verbose and 'statistics' in status:
            stats = status['statistics']
            print("\nStatistics:")
            print(f"  Success Rate: {stats.get('success_rate', 0):.1%}")
            print(f"  Avg Validation Score: {stats.get('avg_validation_score', 0):.2f}")

        print()
        return 0

    except Exception as e:
        logger.error(f"Failed to get status: {e}")
        if args.verbose:
            raise
        return 1


def cmd_fill_queue(args):
    """Fill queue to minimum level"""
    try:
        agent = ContentCreatorAgent(args.config)

        print("Filling queue to minimum level...")
        result = agent.fill_queue(
            target_size=args.target,
            source=args.source
        )

        print(f"\n✓ Queue filled")
        print(f"  Generated: {result['generated']}")
        print(f"  Successful: {result['successful']}")
        print(f"  Failed: {result['failed']}")
        print(f"  Queue size: {result['queue_size_after']}")

        if args.verbose and result['results']:
            print(f"\nDetails:")
            for i, res in enumerate(result['results'], 1):
                if res.success:
                    print(f"  {i}. ✓ {res.content_id} - {res.text[:50]}...")
                else:
                    print(f"  {i}. ✗ {res.error}")

        return 0

    except Exception as e:
        logger.error(f"Failed to fill queue: {e}")
        if args.verbose:
            raise
        return 1


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """
    Main CLI entry point.

    When called with no arguments or unrecognized arguments, runs the ROMA framework.
    When called with content pipeline subcommands, runs the content CLI.
    """
    parser = argparse.ArgumentParser(
        description="Digital Freeman - AI Agent System",
        epilog=(
            "Examples:\n"
            "  python src/main.py                       # Start ROMA framework\n"
            "  python src/main.py generate-content -n 3 # Generate 3 content pieces\n"
            "  python src/main.py list-queue             # List content queue\n"
            "  python src/main.py status                 # Show pipeline status\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--config',
        default='config/content_config.yaml',
        help='Path to configuration file (default: config/content_config.yaml)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

# Handle edge case for empty input
    # roma command (explicit way to start ROMA)
    roma_parser = subparsers.add_parser(
        'roma',
        help='Start ROMA framework (default when no command specified)'
    )

    # generate-content command
    gen_parser = subparsers.add_parser(
        'generate-content',
        help='Generate new content'
    )
    gen_parser.add_argument(
        '--count', '-n',
        type=int,
        default=1,
        help='Number of content pieces to generate (default: 1)'
    )
    gen_parser.add_argument(
        '--source',
        choices=['mission_alignment', 'philosophical_topics', 'social_commentary',
                 'current_trends', 'memory_events'],
        help='Specific ideation source to use'
    )
    gen_parser.add_argument(
        '--no-schedule',
        action='store_true',
        help='Do not automatically schedule content'
    )
    gen_parser.set_defaults(func=cmd_generate_content)

    # list-queue command
    list_parser = subparsers.add_parser(
        'list-queue',
        help='List content in queue'
    )
    list_parser.add_argument(
        '--status',
        choices=['queued', 'scheduled', 'posted', 'failed'],
        help='Filter by status'
    )
    list_parser.add_argument(
        '--limit', '-l',
        type=int,
        default=20,
        help='Maximum number of items to show (default: 20)'
    )
    list_parser.set_defaults(func=cmd_list_queue)

    # post-now command
    post_parser = subparsers.add_parser(
        'post-now',
        help='Post content immediately'
    )
    post_parser.add_argument(
        'content_id',
        nargs='?',
        help='Specific content ID to post (default: next scheduled)'
    )
    post_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation prompt'
    )
    post_parser.set_defaults(func=cmd_post_now)

    # clear-queue command
    clear_parser = subparsers.add_parser(
        'clear-queue',
        help='Clear content from queue'
    )
    clear_parser.add_argument(
        '--status',
        choices=['queued', 'scheduled', 'posted', 'failed'],
        help='Only clear content with this status'
    )
    clear_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Skip confirmation prompt'
    )
    clear_parser.set_defaults(func=cmd_clear_queue)

    # status command
    status_parser = subparsers.add_parser(
        'status',
        help='Show pipeline status'
    )
    status_parser.set_defaults(func=cmd_status)

    # fill-queue command
    fill_parser = subparsers.add_parser(
        'fill-queue',
        help='Fill queue to minimum level'
    )
    fill_parser.add_argument(
        '--target', '-t',
        type=int,
        help='Target queue size (default: from config)'
    )
    fill_parser.add_argument(
        '--source',
        choices=['mission_alignment', 'philosophical_topics', 'social_commentary',
                 'current_trends', 'memory_events'],
        help='Specific ideation source to use'
    )
    fill_parser.set_defaults(func=cmd_fill_queue)

    # Parse arguments
    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # If no command specified or 'roma' command, run the ROMA framework
    if not args.command or args.command == 'roma':
        run_roma()
        return 0

    # Otherwise, run content pipeline CLI command
    setup_directories()

    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if args.verbose:
            raise
        return 1


if __name__ == '__main__':
    sys.exit(main())
