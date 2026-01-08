"""
Tests for EmotionalStateManager class and interaction processing logic
"""

import pytest
from src.memory.emotional_state import EmotionalStateManager
from src.memory.mood import MoodState


class TestEmotionalStateManager:
    """Test suite for EmotionalStateManager class"""

    def test_default_initialization(self):
        """Test that EmotionalStateManager initializes with default mood"""
        manager = EmotionalStateManager()

        mood = manager.get_current_mood()
        assert mood.energy_level == MoodState.DEFAULT_ENERGY
        assert mood.emotional_valence == MoodState.DEFAULT_VALENCE
        assert mood.irritability == MoodState.DEFAULT_IRRITABILITY
        assert mood.enthusiasm == MoodState.DEFAULT_ENTHUSIASM

    def test_custom_initialization(self):
        """Test that EmotionalStateManager can be initialized with custom mood"""
        initial_mood = MoodState(
            energy_level=0.8,
            emotional_valence=0.5,
            irritability=0.1,
            enthusiasm=0.9
        )
        manager = EmotionalStateManager(initial_mood=initial_mood)

        mood = manager.get_current_mood()
        assert mood.energy_level == 0.8
        assert mood.emotional_valence == 0.5
        assert mood.irritability == 0.1
        assert mood.enthusiasm == 0.9

    def test_mood_history_initialization(self):
        """Test that mood history is initialized with initial mood"""
        manager = EmotionalStateManager()

        # History should contain initial mood snapshot
        assert len(manager._mood_history) == 1


class TestInteractionProcessing:
    """Test suite for interaction event processing"""

    def test_interaction_processing(self):
        """Test that interaction events are processed and update mood"""
        manager = EmotionalStateManager()
        initial_valence = manager.get_current_mood().emotional_valence

        # Process a positive interaction
        manager.process_interaction("positive_interaction")

        # Mood should have changed
        new_valence = manager.get_current_mood().emotional_valence
        assert new_valence > initial_valence

    def test_positive_interaction_impact(self):
        """Test that positive interactions increase valence and enthusiasm"""
        manager = EmotionalStateManager()

        initial_mood = manager.get_current_mood()
        initial_valence = initial_mood.emotional_valence
        initial_enthusiasm = initial_mood.enthusiasm
        initial_irritability = initial_mood.irritability

        # Process positive interaction
        manager.process_interaction("positive_interaction")

        new_mood = manager.get_current_mood()

        # Positive interaction should increase valence and enthusiasm
        assert new_mood.emotional_valence > initial_valence
        assert new_mood.enthusiasm > initial_enthusiasm

        # Should decrease irritability
        assert new_mood.irritability < initial_irritability

    def test_negative_interaction_impact(self):
        """Test that negative interactions decrease valence and increase irritability"""
        manager = EmotionalStateManager()

        initial_mood = manager.get_current_mood()
        initial_valence = initial_mood.emotional_valence
        initial_irritability = initial_mood.irritability
        initial_enthusiasm = initial_mood.enthusiasm

        # Process negative interaction
        manager.process_interaction("negative_interaction")

        new_mood = manager.get_current_mood()

        # Negative interaction should decrease valence
        assert new_mood.emotional_valence < initial_valence

        # Should increase irritability
        assert new_mood.irritability > initial_irritability

        # Should decrease enthusiasm
        assert new_mood.enthusiasm < initial_enthusiasm

    def test_engaging_topic_impact(self):
        """Test that engaging topics increase energy and enthusiasm"""
        manager = EmotionalStateManager()

        initial_mood = manager.get_current_mood()
        initial_energy = initial_mood.energy_level
        initial_enthusiasm = initial_mood.enthusiasm
        initial_valence = initial_mood.emotional_valence

        # Process engaging topic interaction
        manager.process_interaction("engaging_topic")

        new_mood = manager.get_current_mood()

        # Engaging topic should increase energy, enthusiasm, and valence
        assert new_mood.energy_level > initial_energy
        assert new_mood.enthusiasm > initial_enthusiasm
        assert new_mood.emotional_valence > initial_valence

    def test_boring_interaction_impact(self):
        """Test that boring interactions decrease energy and enthusiasm"""
        manager = EmotionalStateManager()

        initial_mood = manager.get_current_mood()
        initial_energy = initial_mood.energy_level
        initial_enthusiasm = initial_mood.enthusiasm
        initial_irritability = initial_mood.irritability

        # Process boring interaction
        manager.process_interaction("boring_interaction")

        new_mood = manager.get_current_mood()

        # Boring interaction should decrease energy and enthusiasm
        assert new_mood.energy_level < initial_energy
        assert new_mood.enthusiasm < initial_enthusiasm

        # Should slightly increase irritability
        assert new_mood.irritability > initial_irritability

    def test_sentiment_modulation(self):
        """Test that sentiment parameter modulates interaction impact"""
        # Test with positive sentiment
        manager_positive = EmotionalStateManager()
        manager_positive.process_interaction("positive_interaction", sentiment=1.0)
        positive_impact = manager_positive.get_current_mood().emotional_valence

        # Test with negative sentiment
        manager_negative = EmotionalStateManager()
        manager_negative.process_interaction("positive_interaction", sentiment=-1.0)
        negative_impact = manager_negative.get_current_mood().emotional_valence

        # Test with neutral sentiment
        manager_neutral = EmotionalStateManager()
        manager_neutral.process_interaction("positive_interaction", sentiment=0.0)
        neutral_impact = manager_neutral.get_current_mood().emotional_valence

        # Positive sentiment should amplify the effect
        assert positive_impact > neutral_impact
        # Negative sentiment should reduce or reverse the effect
        assert negative_impact < neutral_impact

    def test_custom_impact_override(self):
        """Test that custom impact overrides default interaction impacts"""
        manager = EmotionalStateManager()

        initial_energy = manager.get_current_mood().energy_level

        # Apply custom impact with large energy delta
        custom_impact = {"energy_delta": 0.15}
        manager.process_interaction("unknown_type", custom_impact=custom_impact)

        new_energy = manager.get_current_mood().energy_level

        # Custom impact should be applied
        assert new_energy > initial_energy

    def test_unknown_interaction_type(self):
        """Test that unknown interaction types are handled gracefully"""
        manager = EmotionalStateManager()

        initial_mood = manager.get_current_mood()
        initial_valence = initial_mood.emotional_valence

        # Process unknown interaction type without custom impact
        manager.process_interaction("completely_unknown_type")

        new_mood = manager.get_current_mood()

        # Mood should remain unchanged (no impact applied)
        assert new_mood.emotional_valence == initial_valence

    def test_mood_history_updated_after_interaction(self):
        """Test that mood history is updated after processing interactions"""
        manager = EmotionalStateManager()

        initial_history_size = len(manager._mood_history)

        # Process interaction
        manager.process_interaction("positive_interaction")

        # History should have a new snapshot
        assert len(manager._mood_history) > initial_history_size


class TestTimeBasedDecay:
    """Test suite for time-based mood decay"""

    def test_tick_applies_decay(self):
        """Test that tick() applies time-based mood decay"""
        manager = EmotionalStateManager()

        # Boost mood to high valence
        manager.process_interaction("positive_interaction")
        manager.process_interaction("positive_interaction")

        initial_valence = manager.get_current_mood().emotional_valence

        # Apply time decay (1 hour)
        manager.tick(3600)

        new_valence = manager.get_current_mood().emotional_valence

        # Valence should decay toward baseline
        assert new_valence < initial_valence


class TestResponseModifiers:
    """Test suite for response modifier generation"""

    def test_get_response_modifiers_structure(self):
        """Test that get_response_modifiers returns expected structure"""
        manager = EmotionalStateManager()

        modifiers = manager.get_response_modifiers()

        # Check all required keys are present
        assert "verbosity" in modifiers
        assert "tone" in modifiers
        assert "patience" in modifiers
        assert "engagement" in modifiers
        assert "suggested_style" in modifiers
        assert "raw_mood" in modifiers

    def test_response_modifiers_ranges(self):
        """Test that response modifiers are within expected ranges"""
        manager = EmotionalStateManager()

        modifiers = manager.get_response_modifiers()

        # Check value ranges
        assert 0.0 <= modifiers["verbosity"] <= 1.0
        assert -1.0 <= modifiers["tone"] <= 1.0
        assert 0.0 <= modifiers["patience"] <= 1.0
        assert 0.0 <= modifiers["engagement"] <= 1.0
        assert modifiers["suggested_style"] in ["philosophical", "sarcastic", "supportive", "confrontational"]

    def test_positive_mood_response_modifiers(self):
        """Test response modifiers reflect positive mood state"""
        manager = EmotionalStateManager()

        # Create very positive mood
        for _ in range(5):
            manager.process_interaction("positive_interaction")
            manager.process_interaction("engaging_topic")

        modifiers = manager.get_response_modifiers()

        # Positive mood should result in high engagement, positive tone, high patience
        assert modifiers["tone"] > 0.0  # Positive valence
        assert modifiers["patience"] > 0.5  # Low irritability
        assert modifiers["engagement"] > 0.5  # High enthusiasm

    def test_negative_mood_response_modifiers(self):
        """Test response modifiers reflect negative mood state"""
        manager = EmotionalStateManager()

        # Create negative mood
        for _ in range(5):
            manager.process_interaction("negative_interaction")
            manager.process_interaction("boring_interaction")

        modifiers = manager.get_response_modifiers()

        # Negative mood should result in lower patience and more negative tone
        assert modifiers["tone"] < 0.0  # Negative valence
        assert modifiers["patience"] < 0.8  # Higher irritability

    def test_style_determination_philosophical(self):
        """Test that philosophical style is suggested for high energy + enthusiasm + positive valence"""
        manager = EmotionalStateManager()

        # Boost to philosophical mood
        for _ in range(8):
            manager.process_interaction("engaging_topic")

        modifiers = manager.get_response_modifiers()

        assert modifiers["suggested_style"] == "philosophical"

    def test_style_determination_confrontational(self):
        """Test that confrontational style is suggested for negative valence + high irritability"""
        manager = EmotionalStateManager()

        # Create confrontational mood
        for _ in range(8):
            manager.process_interaction("negative_interaction")

        modifiers = manager.get_response_modifiers()

        # Should suggest confrontational or sarcastic
        assert modifiers["suggested_style"] in ["confrontational", "sarcastic"]

    def test_raw_mood_included(self):
        """Test that raw mood dimensions are included in response modifiers"""
        manager = EmotionalStateManager()

        modifiers = manager.get_response_modifiers()

        raw_mood = modifiers["raw_mood"]
        assert "energy_level" in raw_mood
        assert "emotional_valence" in raw_mood
        assert "irritability" in raw_mood
        assert "enthusiasm" in raw_mood


class TestSerialization:
    """Test suite for EmotionalStateManager serialization"""

    def test_to_dict(self):
        """Test serialization to dictionary"""
        manager = EmotionalStateManager()

        # Process some interactions
        manager.process_interaction("positive_interaction")
        manager.process_interaction("engaging_topic")

        data = manager.to_dict()

        # Check structure
        assert "current_mood" in data
        assert "mood_history" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """Test deserialization from dictionary"""
        manager = EmotionalStateManager()

        # Process interactions and serialize
        manager.process_interaction("positive_interaction")
        original_valence = manager.get_current_mood().emotional_valence

        data = manager.to_dict()

        # Create new manager and restore
        new_manager = EmotionalStateManager()
        new_manager.from_dict(data)

        # State should be restored
        restored_valence = new_manager.get_current_mood().emotional_valence
        assert restored_valence == pytest.approx(original_valence, abs=0.01)

    def test_roundtrip_serialization(self):
        """Test that serialization and deserialization preserve full state"""
        original = EmotionalStateManager()

        # Create complex state
        original.process_interaction("positive_interaction")
        original.process_interaction("engaging_topic")
        original.process_interaction("negative_interaction")

        data = original.to_dict()

        # Restore to new manager
        restored = EmotionalStateManager()
        restored.from_dict(data)

        # Compare mood states
        orig_mood = original.get_current_mood()
        rest_mood = restored.get_current_mood()

        assert rest_mood.energy_level == pytest.approx(orig_mood.energy_level, abs=0.01)
        assert rest_mood.emotional_valence == pytest.approx(orig_mood.emotional_valence, abs=0.01)
        assert rest_mood.irritability == pytest.approx(orig_mood.irritability, abs=0.01)
        assert rest_mood.enthusiasm == pytest.approx(orig_mood.enthusiasm, abs=0.01)

    def test_mood_history_preserved(self):
        """Test that mood history is preserved through serialization"""
        manager = EmotionalStateManager()

        # Create multiple history snapshots
        manager.process_interaction("positive_interaction")
        manager.process_interaction("negative_interaction")
        manager.process_interaction("engaging_topic")

        original_history_size = len(manager._mood_history)

        data = manager.to_dict()

        # Restore
        restored = EmotionalStateManager()
        restored.from_dict(data)

        # History should be preserved
        assert len(restored._mood_history) == original_history_size
