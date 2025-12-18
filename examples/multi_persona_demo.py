#!/usr/bin/env python3
"""Multi-Persona Usage Demo

This script demonstrates the multi-persona support system including:
- Loading personas from YAML configuration
- Creating personas programmatically
- Memory isolation between personas
- Persona management operations
- Active/inactive persona filtering
"""

import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.persona.manager import PersonaManager
from src.persona.models import Persona
from src.memory.persona_memory import PersonaMemory


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def demo_load_personas():
    """Demonstrate loading personas from configuration"""
    print_section("1. Loading Personas from Configuration")

    # PersonaManager is a singleton - loads config/personas.yaml by default
    manager = PersonaManager()

    print(f"\n{manager}")
    print(f"Total personas loaded: {len(manager)}")

    # List all personas
    all_personas = manager.list_all_personas()
    print(f"\nAll personas:")
    for persona in all_personas:
        print(f"  - {persona}")

    # List only active personas
    active_personas = manager.list_active_personas()
    print(f"\nActive personas ({len(active_personas)}):")
    for persona in active_personas:
        print(f"  - {persona}")

    return manager


def demo_persona_details(manager: PersonaManager):
    """Demonstrate accessing persona details"""
    print_section("2. Accessing Persona Details")

    # Get freeman persona
    freeman = manager.get_persona("freeman")

    if freeman:
        print(f"\nPersona: {freeman.name} (ID: {freeman.id})")
        print(f"Version: {freeman.version}")
        print(f"Memory Namespace: {freeman.memory_namespace}")
        print(f"Status: {'Active' if freeman.is_active else 'Inactive'}")

        if freeman.mission:
            print(f"\nMission:")
            print(f"  {freeman.mission.strip()}")

        # Show personality configuration
        if freeman.personality_config:
            print(f"\nPersonality:")
            tone = freeman.personality_config.get('tone', 'N/A')
            style = freeman.personality_config.get('style', 'N/A')
            print(f"  Tone: {tone}")
            print(f"  Style: {style}")

        # Show platform configurations
        if freeman.platform_configs:
            print(f"\nPlatforms:")
            for platform, config in freeman.platform_configs.items():
                enabled = config.get('enabled', False)
                status = "✓" if enabled else "✗"
                print(f"  {status} {platform}")
    else:
        print("\nFreeman persona not found!")


def demo_create_persona(manager: PersonaManager):
    """Demonstrate creating a persona programmatically"""
    print_section("3. Creating Personas Programmatically")

    # Create a new persona
    philosopher = Persona(
        id="philosopher",
        name="The Philosopher",
        personality_config={
            "tone": "contemplative",
            "style": "socratic"
        },
        memory_namespace="philosopher",
        is_active=True,
        mission="To ask profound questions and guide people to deeper understanding",
        platform_configs={
            "telegram": {"enabled": True}
        }
    )

    print(f"\nCreated new persona: {philosopher}")

    # Validate before adding
    errors = manager.validate_persona(philosopher)
    if errors:
        print(f"\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\n✓ Persona validated successfully")

        # Add to manager
        manager.add_persona(philosopher)
        print(f"✓ Persona added to manager")
        print(f"\nTotal personas: {len(manager)}")

        # Verify it's there
        retrieved = manager.get_persona("philosopher")
        if retrieved:
            print(f"✓ Successfully retrieved: {retrieved}")

    return philosopher


def demo_memory_isolation():
    """Demonstrate memory isolation between personas"""
    print_section("4. Memory Isolation Between Personas")

    # Create memory instances for two different personas
    freeman_memory = PersonaMemory(persona_id="freeman")
    philosopher_memory = PersonaMemory(persona_id="philosopher")

    print(f"\nCreated memory instances:")
    print(f"  - {freeman_memory}")
    print(f"  - {philosopher_memory}")

    # Store data in Freeman's memory
    print(f"\nStoring user data in Freeman's memory...")
    freeman_memory.user_memory.set("user_123", {
        "name": "Alice",
        "interactions": 42,
        "relationship": "ally"
    })
    freeman_memory.relationship_memory.set("user_123", {
        "level": "ally",
        "trust_score": 85
    })

    # Store different data in Philosopher's memory
    print(f"Storing user data in Philosopher's memory...")
    philosopher_memory.user_memory.set("user_123", {
        "name": "Alice",
        "interactions": 5,
        "relationship": "stranger"
    })
    philosopher_memory.relationship_memory.set("user_123", {
        "level": "stranger",
        "trust_score": 10
    })

    # Retrieve and show isolation
    print(f"\nMemory isolation verification:")

    freeman_user = freeman_memory.user_memory.get("user_123")
    print(f"\n  Freeman's view of user_123:")
    print(f"    Interactions: {freeman_user['interactions']}")
    print(f"    Relationship: {freeman_user['relationship']}")

    philosopher_user = philosopher_memory.user_memory.get("user_123")
    print(f"\n  Philosopher's view of user_123:")
    print(f"    Interactions: {philosopher_user['interactions']}")
    print(f"    Relationship: {philosopher_user['relationship']}")

    print(f"\n✓ Each persona maintains completely separate memory!")
    print(f"  Same user has different relationships with different personas")

    # Show namespacing
    print(f"\nMemory namespaces:")
    print(f"  Freeman: {freeman_memory.get_namespace()}")
    print(f"  Philosopher: {philosopher_memory.get_namespace()}")


def demo_persona_management(manager: PersonaManager):
    """Demonstrate persona management operations"""
    print_section("5. Persona Management Operations")

    # Check if persona exists
    print(f"\nChecking persona existence:")
    print(f"  'freeman' in manager: {'freeman' in manager}")
    print(f"  'nonexistent' in manager: {'nonexistent' in manager}")

    # Create and add a temporary persona
    temp_persona = Persona(
        id="temp",
        name="Temporary Persona",
        memory_namespace="temp",
        is_active=False
    )

    manager.add_persona(temp_persona)
    print(f"\nAdded temporary persona: {temp_persona}")
    print(f"Total personas: {len(manager)}")

    # Remove it
    removed = manager.remove_persona("temp")
    print(f"\nRemoved temporary persona: {removed}")
    print(f"Total personas: {len(manager)}")

    # Show active vs total
    active_count = len(manager.list_active_personas())
    total_count = len(manager)
    print(f"\nPersona status summary:")
    print(f"  Active: {active_count}")
    print(f"  Total: {total_count}")
    print(f"  Inactive: {total_count - active_count}")


def demo_config_validation(manager: PersonaManager):
    """Demonstrate configuration validation"""
    print_section("6. Configuration Validation")

    # Try to create persona with invalid ID
    print("\nAttempting to create persona with invalid ID...")
    try:
        invalid_persona = Persona(
            id="Invalid ID with spaces!",
            name="Invalid Persona",
            memory_namespace="invalid"
        )
        print("  ✗ Should have failed but didn't!")
    except Exception as e:
        print(f"  ✓ Validation caught error: {type(e).__name__}")

    # Try to create persona with duplicate namespace
    print("\nAttempting to create persona with duplicate namespace...")
    duplicate_persona = Persona(
        id="duplicate",
        name="Duplicate Namespace",
        memory_namespace="freeman"  # Same as existing persona
    )

    errors = manager.validate_persona(duplicate_persona)
    if errors:
        print(f"  ✓ Validation errors found:")
        for error in errors:
            print(f"    - {error}")
    else:
        print("  ✗ Should have found namespace conflict!")


def demo_memory_operations():
    """Demonstrate various memory operations"""
    print_section("7. Memory Operations")

    memory = PersonaMemory(persona_id="freeman")

    # Store various types of data
    print("\nStoring different types of memory...")

    memory.user_memory.set("user_1", {"name": "Bob", "age": 30})
    memory.relationship_memory.set("user_1", {"level": "friend", "trust": 70})
    memory.action_memory.set("user_1", {"likes": 10, "comments": 5})
    memory.emotional_memory.set("topic_ai", {"sentiment": "excited", "intensity": 8})
    memory.conversation_memory.set("conv_1", {"topic": "consciousness", "important": True})

    print("  ✓ User memory")
    print("  ✓ Relationship memory")
    print("  ✓ Action memory")
    print("  ✓ Emotional memory")
    print("  ✓ Conversation memory")

    # Check existence
    print("\nChecking memory existence:")
    print(f"  user_1 exists: {memory.user_memory.exists('user_1')}")
    print(f"  user_2 exists: {memory.user_memory.exists('user_2')}")

    # List keys
    print("\nMemory keys:")
    print(f"  User memory: {memory.user_memory.keys()}")
    print(f"  Relationship memory: {memory.relationship_memory.keys()}")

    # Delete operation
    print("\nDeleting user_1 from user memory...")
    deleted = memory.user_memory.delete("user_1")
    print(f"  Deleted: {deleted}")
    print(f"  user_1 exists: {memory.user_memory.exists('user_1')}")


def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("  MULTI-PERSONA SUPPORT DEMONSTRATION")
    print("  Digital Freeman - Multi-Persona System")
    print("=" * 60)

    try:
        # 1. Load personas from config
        manager = demo_load_personas()

        # 2. Show persona details
        demo_persona_details(manager)

        # 3. Create new persona
        demo_create_persona(manager)

        # 4. Demonstrate memory isolation
        demo_memory_isolation()

        # 5. Persona management
        demo_persona_management(manager)

        # 6. Configuration validation
        demo_config_validation(manager)

        # 7. Memory operations
        demo_memory_operations()

        # Summary
        print_section("Summary")
        print("\n✓ Multi-persona system demonstration completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  1. Loading personas from YAML configuration")
        print("  2. Accessing detailed persona configurations")
        print("  3. Creating personas programmatically")
        print("  4. Complete memory isolation between personas")
        print("  5. Persona management (add, remove, validate)")
        print("  6. Configuration validation and error handling")
        print("  7. Memory operations across different memory types")

        print("\nThe multi-persona system allows:")
        print("  • Running multiple AI personas from a single deployment")
        print("  • Complete isolation of memory and personality")
        print("  • Shared infrastructure for efficiency")
        print("  • Individual persona management and configuration")

        print("\n" + "=" * 60 + "\n")

        return 0

    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
