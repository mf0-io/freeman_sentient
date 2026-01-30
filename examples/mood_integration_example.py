#!/usr/bin/env python3
"""
Mood Integration Example for Digital Freeman Agents

This example demonstrates how agents should integrate with the mood/emotional state system.
It shows how to:
1. Initialize the emotional state manager
2. Process various interaction types
3. Retrieve mood-based response modifiers
4. Use modifiers to adjust agent behavior
5. Handle time-based mood decay
"""

import sys
import os
import time

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.memory.emotional_state import EmotionalStateManager
from src.memory.mood import MoodState


def print_separator(title: str = ""):
    """Print a visual separator"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}\n")


def demonstrate_basic_usage():
    """Demonstrate basic emotional state manager usage"""
    print_separator("1. Basic Emotional State Manager Usage")

    # Initialize the manager with default mood (baseline)
    manager = EmotionalStateManager()

    print("Initial mood state:")
    print(f"  {manager.get_current_mood()}")

    # Get response modifiers for agent decision-making
    modifiers = manager.get_response_modifiers()
    print("\nResponse modifiers for agent:")
    print(f"  Verbosity:  {modifiers['verbosity']:.2f} (0.0=terse, 1.0=verbose)")
    print(f"  Tone:       {modifiers['tone']:.2f} (-1.0=negative, 1.0=positive)")
    print(f"  Patience:   {modifiers['patience']:.2f} (0.0=impatient, 1.0=patient)")
    print(f"  Engagement: {modifiers['engagement']:.2f} (0.0=disengaged, 1.0=excited)")
    print(f"  Style:      {modifiers['suggested_style']}")


def demonstrate_interaction_processing():
    """Demonstrate processing different interaction types"""
    print_separator("2. Processing Different Interactions")

    manager = EmotionalStateManager()

    # Simulate a series of interactions
    interactions = [
        ("positive_interaction", "User liked Freeman's post"),
        ("engaging_topic", "Deep philosophical discussion about consciousness"),
        ("boring_interaction", "Generic 'how are you' small talk"),
        ("negative_interaction", "Troll comment"),
    ]

    for interaction_type, description in interactions:
        print(f"\nEvent: {description}")
        print(f"  Type: {interaction_type}")

        # Process the interaction
        manager.process_interaction(interaction_type)

        # Show updated mood
        mood = manager.get_current_mood()
        print(f"  Mood after: {mood}")

        # Get updated response modifiers
        modifiers = manager.get_response_modifiers()
        print(f"  Response style: {modifiers['suggested_style']}")


def demonstrate_sentiment_modulation():
    """Demonstrate sentiment-based mood modulation"""
    print_separator("3. Sentiment-Based Mood Modulation")

    manager = EmotionalStateManager()

    print("Processing positive interaction with varying sentiment:")

    sentiments = [
        (0.2, "Slightly positive"),
        (0.5, "Moderately positive"),
        (0.9, "Very positive"),
    ]

    for sentiment_value, description in sentiments:
        # Create fresh manager for each test
        test_manager = EmotionalStateManager()

        print(f"\n  {description} (sentiment={sentiment_value:.1f})")
        test_manager.process_interaction("positive_interaction", sentiment=sentiment_value)

        mood = test_manager.get_current_mood()
        print(f"    Valence: {mood.emotional_valence:.3f}")
        print(f"    Enthusiasm: {mood.enthusiasm:.3f}")


def demonstrate_mood_decay():
    """Demonstrate time-based mood decay"""
    print_separator("4. Time-Based Mood Decay")

    manager = EmotionalStateManager()

    # Create an excited, positive mood
    print("Creating excited mood state...")
    manager.process_interaction("engaging_topic")
    manager.process_interaction("positive_interaction")

    initial_mood = manager.get_current_mood()
    print(f"Initial mood: {initial_mood}")

    # Simulate time passing (in hours)
    time_intervals = [1, 2, 4, 8]  # hours

    print("\nMood decay over time:")
    for hours in time_intervals:
        # Apply time decay (convert hours to seconds)
        manager.tick(hours * 3600)

        mood = manager.get_current_mood()
        print(f"  After {hours}h: {mood}")

    print("\nNote: Mood naturally returns to baseline over time")


def demonstrate_agent_integration():
    """Demonstrate how an agent would use mood in decision-making"""
    print_separator("5. Agent Integration Example")

    manager = EmotionalStateManager()

    # Simulate different scenarios and show how agent would adapt
    scenarios = [
        {
            "name": "High Energy Discussion",
            "interactions": [
                ("engaging_topic", None),
                ("positive_interaction", 0.8),
            ],
            "user_message": "What do you think about free will?",
        },
        {
            "name": "After Troll Attack",
            "interactions": [
                ("negative_interaction", -0.7),
                ("negative_interaction", -0.5),
            ],
            "user_message": "Can you help me understand something?",
        },
        {
            "name": "Low Energy State",
            "interactions": [
                ("boring_interaction", 0.0),
                ("boring_interaction", 0.0),
            ],
            "user_message": "Tell me about philosophy",
        },
    ]

    for scenario in scenarios:
        # Reset for clean scenario
        manager.reset()

        print(f"\nScenario: {scenario['name']}")
        print(f"User: {scenario['user_message']}")

        # Process interactions that led to current mood
        for interaction_type, sentiment in scenario['interactions']:
            manager.process_interaction(interaction_type, sentiment)

        # Agent queries mood state for decision-making
        modifiers = manager.get_response_modifiers()

        print(f"\nAgent Decision Process:")
        print(f"  Current mood: {manager.get_current_mood()}")
        print(f"  Style to use: {modifiers['suggested_style']}")
        print(f"  Verbosity level: {modifiers['verbosity']:.2f}")
        print(f"  Tone: {modifiers['tone']:.2f}")

        # Agent would use these modifiers to:
        # - Adjust response length based on verbosity
        # - Choose tone/style in prompt
        # - Decide level of detail based on engagement
        # - Apply patience threshold for handling questions

        if modifiers['verbosity'] < 0.3:
            print("  → Agent: Use shorter, more concise response")
        elif modifiers['verbosity'] > 0.7:
            print("  → Agent: Use detailed, expansive response")

        if modifiers['suggested_style'] == 'confrontational':
            print("  → Agent: Add edge/challenge to response")
        elif modifiers['suggested_style'] == 'supportive':
            print("  → Agent: Use encouraging, helpful tone")


def demonstrate_mood_history():
    """Demonstrate mood history tracking"""
    print_separator("6. Mood History Tracking")

    manager = EmotionalStateManager()

    # Simulate a conversation flow
    print("Simulating conversation flow:")
    events = [
        ("engaging_topic", "User asks deep question"),
        ("positive_interaction", "User agrees enthusiastically"),
        ("boring_interaction", "User makes small talk"),
        ("negative_interaction", "User posts troll comment"),
    ]

    for interaction_type, description in events:
        print(f"\n  {description}")
        manager.process_interaction(interaction_type)

    # Get mood history
    history = manager.get_mood_history(limit=5)

    print(f"\n\nMood history (last {len(history)} snapshots):")
    for i, snapshot in enumerate(history):
        print(f"  {i+1}. Valence: {snapshot['emotional_valence']:.2f}, "
              f"Energy: {snapshot['energy_level']:.2f}, "
              f"Enthusiasm: {snapshot['enthusiasm']:.2f}")

    print("\nNote: History can be used for:")
    print("  - Analyzing mood patterns over time")
    print("  - Persistence/recovery after restart")
    print("  - Understanding what triggered mood changes")


def demonstrate_serialization():
    """Demonstrate state serialization for persistence"""
    print_separator("7. State Serialization & Persistence")

    # Create manager with some state
    manager = EmotionalStateManager()
    manager.process_interaction("engaging_topic")
    manager.process_interaction("positive_interaction", sentiment=0.8)

    print("Original state:")
    print(f"  {manager.get_current_mood()}")

    # Serialize to dictionary (for saving to database/file)
    state_dict = manager.to_dict()
    print(f"\nSerialized to dict: {len(str(state_dict))} bytes")
    print(f"  Contains: current_mood, mood_history, timestamps")

    # Create new manager and restore state
    restored_manager = EmotionalStateManager()
    restored_manager.from_dict(state_dict)

    print("\nRestored state:")
    print(f"  {restored_manager.get_current_mood()}")

    # Verify they match
    original_modifiers = manager.get_response_modifiers()
    restored_modifiers = restored_manager.get_response_modifiers()

    print("\nVerification:")
    print(f"  Moods match: {original_modifiers['raw_mood'] == restored_modifiers['raw_mood']}")
    print(f"  History preserved: {len(manager.get_mood_history()) == len(restored_manager.get_mood_history())}")


def main():
    """Run all demonstration examples"""
    print("\n" + "="*60)
    print("  MOOD SYSTEM INTEGRATION EXAMPLES")
    print("  Digital Freeman - Emotional State Management")
    print("="*60)

    try:
        demonstrate_basic_usage()
        demonstrate_interaction_processing()
        demonstrate_sentiment_modulation()
        demonstrate_mood_decay()
        demonstrate_agent_integration()
        demonstrate_mood_history()
        demonstrate_serialization()

        print_separator("All Examples Completed Successfully!")
        print("Key Takeaways for Agent Integration:")
        print("  1. Always query get_response_modifiers() before generating responses")
        print("  2. Use sentiment analysis to modulate interaction impact")
        print("  3. Apply tick() periodically for natural mood decay")
        print("  4. Serialize state with to_dict() for persistence")
        print("  5. Track mood history to understand user interaction patterns")
        print("\n")

        return 0

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
