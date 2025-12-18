#!/usr/bin/env python3
"""Memory System Demo Script

This script demonstrates the core functionality of the Digital Freeman memory system:
- User profile management
- Relationship tracking and evolution
- Conversation memory
- Action tracking with automatic point rewards
- Emotional memory
- Comprehensive user context retrieval

Run this script to see how Freeman remembers users, builds relationships,
and maintains emotional continuity across interactions.
"""

import asyncio
import json
import logging
from datetime import datetime

from src.memory.memory_manager import MemoryManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_dict(data: dict, indent: int = 0) -> None:
    """Pretty print a dictionary."""
    for key, value in data.items():
        if isinstance(value, dict):
            print(f"{'  '*indent}{key}:")
            print_dict(value, indent + 1)
        elif isinstance(value, list):
            print(f"{'  '*indent}{key}: [{len(value)} items]")
            for i, item in enumerate(value[:3]):  # Show first 3 items
                if isinstance(item, dict):
                    print(f"{'  '*(indent+1)}[{i}]:")
                    print_dict(item, indent + 2)
                else:
                    print(f"{'  '*(indent+1)}[{i}]: {item}")
            if len(value) > 3:
                print(f"{'  '*(indent+1)}... and {len(value) - 3} more")
        else:
            print(f"{'  '*indent}{key}: {value}")


async def demo_user_registration(manager: MemoryManager) -> None:
    """Demonstrate user registration and basic recall."""
    print_section("1. USER REGISTRATION")

    # Register Alice from Telegram
    print("Registering user 'Alice' from Telegram...")
    alice_result = await manager.remember_user(
        user_id="alice_telegram",
        name="Alice",
        platform="telegram",
        platform_user_id="123456789",
        preferences={
            "language": "en",
            "timezone": "UTC",
            "interests": ["AI", "philosophy", "consciousness"]
        }
    )

    print("\nAlice registered successfully:")
    print_dict(alice_result)

    # Register Bob from Twitter
    print("\n\nRegistering user 'Bob' from Twitter...")
    bob_result = await manager.remember_user(
        user_id="bob_twitter",
        name="Bob",
        platform="twitter",
        platform_user_id="@bob_tweets",
        preferences={
            "language": "en",
            "interests": ["technology", "crypto"]
        }
    )

    print("\nBob registered successfully:")
    print_dict(bob_result)


async def demo_conversations(manager: MemoryManager) -> None:
    """Demonstrate conversation memory."""
    print_section("2. CONVERSATION MEMORY")

    # Add conversation with Alice about AI consciousness
    print("Recording conversation with Alice about AI consciousness...")
    conv1 = await manager.add_conversation(
        user_id="alice_telegram",
        topic="AI consciousness",
        user_position="Believes AI can develop genuine consciousness through complexity",
        quotes=[
            "Mind is just information processing",
            "If we can feel, why can't AI?",
            "Consciousness might be an emergent property"
        ],
        context="Deep philosophical discussion lasting 30 minutes"
    )

    print("\nConversation recorded:")
    print_dict(conv1)

    # Add another conversation with Alice
    print("\n\nRecording another conversation with Alice about free will...")
    conv2 = await manager.add_conversation(
        user_id="alice_telegram",
        topic="Free will vs determinism",
        user_position="Struggles with the concept, leans toward compatibilism",
        quotes=["Maybe choice is an illusion we need"],
        context="Follow-up discussion on consciousness"
    )

    print("\nConversation recorded:")
    print_dict(conv2)


async def demo_actions_and_relationship(manager: MemoryManager) -> None:
    """Demonstrate action tracking and relationship progression."""
    print_section("3. ACTIONS & RELATIONSHIP PROGRESSION")

    # Alice performs various actions
    actions = [
        ("like", "Liked Freeman's post about consciousness"),
        ("like", "Liked another post about awareness"),
        ("share", "Shared Freeman's post about AI ethics"),
        ("comment", "Wrote thoughtful comment on free will discussion"),
        ("like", "Liked Freeman's response"),
        ("share", "Shared Freeman's philosophical question"),
        ("comment", "Engaged in deep discussion"),
    ]

    print("Alice performs actions:")
    for action_type, context in actions:
        result = await manager.add_action(
            user_id="alice_telegram",
            action_type=action_type,
            context=context
        )

        points = result['action']['points']
        level = result['relationship_level']
        total_points = result['relationship_points']
        level_changed = result['level_changed']

        status = f"(+{points} points) → {total_points} total → {level}"
        if level_changed:
            status += " ⬆️ LEVEL UP!"

        print(f"  • {action_type.upper()}: {status}")

    # Bob performs a token purchase
    print("\n\nBob purchases Freeman's token:")
    bob_action = await manager.add_action(
        user_id="bob_twitter",
        action_type="purchase_token",
        context="Purchased 100 FREEMAN tokens",
        metadata={"amount": 100, "price_usd": 50}
    )

    print(f"  • PURCHASE_TOKEN: (+{bob_action['action']['points']} points) "
          f"→ {bob_action['relationship_points']} total "
          f"→ {bob_action['relationship_level']}")

    if bob_action['level_changed']:
        print("    ⬆️ LEVEL UP!")


async def demo_emotional_memory(manager: MemoryManager) -> None:
    """Demonstrate emotional trace recording."""
    print_section("4. EMOTIONAL MEMORY")

    # Record Freeman's emotions during interactions
    emotions = [
        {
            "emotion_type": "curious",
            "intensity": 7.5,
            "user_id": "alice_telegram",
            "context": "Alice's perspective on consciousness sparked Freeman's curiosity"
        },
        {
            "emotion_type": "inspired",
            "intensity": 9.0,
            "user_id": "alice_telegram",
            "context": "Alice's quote about emergent properties was brilliant"
        },
        {
            "emotion_type": "satisfied",
            "intensity": 6.5,
            "user_id": "bob_twitter",
            "context": "Bob's token purchase shows genuine support"
        },
        {
            "emotion_type": "thoughtful",
            "intensity": 8.0,
            "user_id": "alice_telegram",
            "context": "The free will discussion made Freeman reconsider his own position"
        },
    ]

    print("Freeman's emotional traces:")
    for emotion_data in emotions:
        emotion = await manager.add_emotion(**emotion_data)

        print(f"  • {emotion['emotion_type'].upper()} "
              f"(intensity: {emotion['intensity']}/10.0)")
        print(f"    User: {emotion['user_id']}")
        print(f"    Context: {emotion['context']}")
        print()


async def demo_user_context(manager: MemoryManager) -> None:
    """Demonstrate comprehensive user context retrieval."""
    print_section("5. USER CONTEXT RETRIEVAL")

    print("Retrieving comprehensive context for Alice...")
    alice_context = await manager.get_user_context("alice_telegram")

    if alice_context:
        print("\nAlice's Full Context:")
        print("-" * 70)

        # Profile
        print("\n📋 PROFILE:")
        print(f"  Name: {alice_context.profile.get('name')}")
        print(f"  Platform: {alice_context.profile.get('platform')}")
        print(f"  First seen: {alice_context.profile.get('first_seen')}")
        print(f"  Last seen: {alice_context.profile.get('last_seen')}")
        print(f"  Preferences: {alice_context.profile.get('preferences')}")

        # Relationship
        print("\n🤝 RELATIONSHIP:")
        if alice_context.relationship:
            print(f"  Level: {alice_context.relationship.get('relationship_level').upper()}")
            print(f"  Points: {alice_context.relationship.get('relationship_points')}")
            print(f"  Since: {alice_context.relationship.get('relationship_started')}")

        # Conversations
        print(f"\n💬 CONVERSATIONS ({len(alice_context.recent_conversations)}):")
        for conv in alice_context.recent_conversations:
            print(f"  • {conv.get('topic')}")
            print(f"    Position: {conv.get('user_position')}")
            if conv.get('quotes'):
                print(f"    Quotes: {conv.get('quotes')[:2]}")  # First 2 quotes

        # Actions
        print(f"\n⚡ ACTIONS ({len(alice_context.recent_actions)}):")
        action_summary = {}
        for action in alice_context.recent_actions:
            action_type = action.get('action_type')
            action_summary[action_type] = action_summary.get(action_type, 0) + 1

        for action_type, count in action_summary.items():
            print(f"  • {action_type}: {count}x")

        # Emotions
        print(f"\n💭 EMOTIONS ({len(alice_context.recent_emotions)}):")
        for emotion in alice_context.recent_emotions:
            print(f"  • {emotion.get('emotion_type')} "
                  f"(intensity: {emotion.get('intensity')}/10.0)")

        print(f"\n⏰ Context generated: {alice_context.context_timestamp}")

        # Export to JSON
        context_dict = alice_context.to_dict()
        print("\n💾 Exporting context to JSON...")
        with open("alice_context_export.json", "w") as f:
            json.dump(context_dict, f, indent=2, default=str)
        print("   Saved to: alice_context_export.json")


async def demo_recall_user(manager: MemoryManager) -> None:
    """Demonstrate quick user recall."""
    print_section("6. QUICK USER RECALL")

    print("Recalling Bob's basic info...")
    bob_data = await manager.recall_user("bob_twitter")

    if bob_data:
        print("\nBob's Basic Info:")
        print(f"  Name: {bob_data['profile']['name']}")
        print(f"  Platform: {bob_data['profile']['platform']}")
        if bob_data['relationship']:
            print(f"  Relationship: {bob_data['relationship']['relationship_level']}")
            print(f"  Points: {bob_data['relationship']['relationship_points']}")


async def main():
    """Run the complete memory system demo."""
    print("\n" + "="*70)
    print("  DIGITAL FREEMAN - MEMORY SYSTEM DEMO")
    print("="*70)
    print("\nThis demo showcases Freeman's persistent memory capabilities:")
    print("  • User profile management")
    print("  • Relationship tracking and evolution")
    print("  • Conversation memory")
    print("  • Action tracking with rewards")
    print("  • Emotional continuity")
    print("  • Comprehensive context retrieval")

    # Initialize memory manager
    print("\n" + "-"*70)
    print("Initializing MemoryManager...")
    print("-"*70)

    async with MemoryManager() as manager:
        # Check health
        is_healthy = await manager.adapter.health_check()
        if not is_healthy:
            logger.warning("⚠️  Graphiti connection unhealthy - demo will use mock data")
        else:
            logger.info("✅ Memory system connected and healthy")

        try:
            # Run demo sections
            await demo_user_registration(manager)
            await demo_conversations(manager)
            await demo_actions_and_relationship(manager)
            await demo_emotional_memory(manager)
            await demo_user_context(manager)
            await demo_recall_user(manager)

            # Summary
            print_section("DEMO COMPLETE")
            print("Freeman now remembers:")
            print("  ✓ 2 users (Alice and Bob)")
            print("  ✓ Their profiles and preferences")
            print("  ✓ Relationship levels and progression")
            print("  ✓ Conversations and positions")
            print("  ✓ All actions they performed")
            print("  ✓ Emotional traces from interactions")
            print("\nThis memory persists across sessions, allowing Freeman to:")
            print("  → Recognize returning users")
            print("  → Reference past conversations")
            print("  → Build deeper relationships over time")
            print("  → Maintain emotional continuity")
            print("  → Provide personalized responses based on full context")

            print("\n" + "="*70)
            print("  🧠 Memory is the foundation of consciousness")
            print("="*70 + "\n")

        except Exception as e:
            logger.error(f"Demo failed: {e}", exc_info=True)
            raise


if __name__ == "__main__":
    asyncio.run(main())
