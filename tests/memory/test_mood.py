"""
Tests for MoodState class and mood transition logic
"""

import pytest
from src.memory.mood import MoodState
from src.core.base_memory import MemoryValidationError


class TestMoodState:
    """Test suite for MoodState class"""

    def test_default_initialization(self):
        """Test that MoodState initializes with default baseline values"""
        mood = MoodState()

        assert mood._energy_level == MoodState.DEFAULT_ENERGY
        assert mood._emotional_valence == MoodState.DEFAULT_VALENCE
        assert mood._irritability == MoodState.DEFAULT_IRRITABILITY
        assert mood._enthusiasm == MoodState.DEFAULT_ENTHUSIASM

    def test_custom_initialization(self):
        """Test that MoodState can be initialized with custom values"""
        mood = MoodState(
            energy_level=0.8,
            emotional_valence=0.5,
            irritability=0.1,
            enthusiasm=0.9
        )

        assert mood._energy_level == 0.8
        assert mood._emotional_valence == 0.5
        assert mood._irritability == 0.1
        assert mood._enthusiasm == 0.9

    def test_validation_energy_out_of_range(self):
        """Test that energy_level must be within 0.0-1.0"""
        with pytest.raises(MemoryValidationError):
            MoodState(energy_level=1.5)

        with pytest.raises(MemoryValidationError):
            MoodState(energy_level=-0.1)

    def test_validation_valence_out_of_range(self):
        """Test that emotional_valence must be within -1.0 to 1.0"""
        with pytest.raises(MemoryValidationError):
            MoodState(emotional_valence=1.5)

        with pytest.raises(MemoryValidationError):
            MoodState(emotional_valence=-1.5)

    def test_validation_irritability_out_of_range(self):
        """Test that irritability must be within 0.0-1.0"""
        with pytest.raises(MemoryValidationError):
            MoodState(irritability=1.5)

        with pytest.raises(MemoryValidationError):
            MoodState(irritability=-0.1)

    def test_validation_enthusiasm_out_of_range(self):
        """Test that enthusiasm must be within 0.0-1.0"""
        with pytest.raises(MemoryValidationError):
            MoodState(enthusiasm=1.5)

        with pytest.raises(MemoryValidationError):
            MoodState(enthusiasm=-0.1)


class TestMoodTransitions:
    """Test suite for smooth mood transitions and interpolation"""

    def test_mood_transitions(self):
        """Test that mood transitions are smooth and respect max change constraints"""
        mood = MoodState(energy_level=0.5, emotional_valence=0.0)

        # Attempt a large change - should be clamped to MAX_CHANGE_PER_EVENT
        mood.update({
            "energy_delta": 0.5,  # Try to jump from 0.5 to 1.0
            "valence_delta": 0.8  # Try to jump from 0.0 to 0.8
        })

        # Changes should be limited to MAX_CHANGE_PER_EVENT (0.15)
        assert mood._energy_level <= 0.5 + MoodState.MAX_CHANGE_PER_EVENT
        assert mood._emotional_valence <= 0.0 + MoodState.MAX_CHANGE_PER_EVENT

    def test_smooth_transition_constraint(self):
        """Test that individual transitions respect the smooth transition rules"""
        mood = MoodState(energy_level=0.3)

        # Apply a large upward delta
        mood.update({"energy_delta": 0.5})

        # Should only change by MAX_CHANGE_PER_EVENT
        assert mood._energy_level == pytest.approx(0.3 + MoodState.MAX_CHANGE_PER_EVENT, abs=0.01)

    def test_negative_smooth_transition(self):
        """Test that negative transitions are also smoothed"""
        mood = MoodState(energy_level=0.8)

        # Apply a large downward delta
        mood.update({"energy_delta": -0.5})

        # Should only change by MAX_CHANGE_PER_EVENT
        assert mood._energy_level == pytest.approx(0.8 - MoodState.MAX_CHANGE_PER_EVENT, abs=0.01)

    def test_multiple_dimensions_transition_independently(self):
        """Test that each dimension transitions independently"""
        mood = MoodState(
            energy_level=0.5,
            emotional_valence=0.0,
            irritability=0.2,
            enthusiasm=0.5
        )

        mood.update({
            "energy_delta": 0.3,
            "valence_delta": 0.5,
            "irritability_delta": -0.1,
            "enthusiasm_delta": 0.4
        })

        # Each should be constrained independently
        assert mood._energy_level <= 0.5 + MoodState.MAX_CHANGE_PER_EVENT
        assert mood._emotional_valence <= 0.0 + MoodState.MAX_CHANGE_PER_EVENT
        assert mood._irritability >= 0.2 - MoodState.MAX_CHANGE_PER_EVENT
        assert mood._enthusiasm <= 0.5 + MoodState.MAX_CHANGE_PER_EVENT

    def test_small_changes_not_affected(self):
        """Test that small changes within max limit are applied fully"""
        mood = MoodState(energy_level=0.5)

        mood.update({"energy_delta": 0.05})

        # Small changes should be applied as-is
        assert mood._energy_level == pytest.approx(0.55, abs=0.01)

    def test_boundary_clamping(self):
        """Test that values are clamped to valid ranges even after transition"""
        mood = MoodState(energy_level=0.95)

        # Try to increase beyond 1.0
        mood.update({"energy_delta": 0.2})

        # Should be clamped to 1.0
        assert mood._energy_level == 1.0

    def test_time_based_decay(self):
        """Test that mood decays toward baseline over time"""
        mood = MoodState(
            energy_level=1.0,
            emotional_valence=0.8,
            irritability=0.9,
            enthusiasm=1.0
        )

        # Simulate 1 hour passing
        mood.tick(3600)

        # All values should have moved toward baseline
        assert mood._energy_level < 1.0  # Moving toward DEFAULT_ENERGY (0.6)
        assert mood._emotional_valence < 0.8  # Moving toward DEFAULT_VALENCE (0.0)
        assert mood._irritability < 0.9  # Moving toward DEFAULT_IRRITABILITY (0.2)
        assert mood._enthusiasm < 1.0  # Moving toward DEFAULT_ENTHUSIASM (0.5)

    def test_decay_gradual(self):
        """Test that decay is gradual, not instant"""
        mood = MoodState(energy_level=1.0)

        # Simulate short time period (5 minutes)
        mood.tick(300)

        # Should have decayed but not all the way to baseline
        assert 0.6 < mood._energy_level < 1.0

    def test_decay_toward_baseline_both_directions(self):
        """Test that decay works both above and below baseline"""
        # Test above baseline
        mood_high = MoodState(energy_level=0.9)
        mood_high.tick(3600)
        assert mood_high._energy_level < 0.9  # Decreasing toward 0.6

        # Test below baseline
        mood_low = MoodState(energy_level=0.3)
        mood_low.tick(3600)
        assert mood_low._energy_level > 0.3  # Increasing toward 0.6

    def test_reset_returns_to_baseline(self):
        """Test that reset() returns all dimensions to baseline"""
        mood = MoodState(
            energy_level=0.9,
            emotional_valence=0.7,
            irritability=0.8,
            enthusiasm=0.9
        )

        mood.reset()

        assert mood._energy_level == MoodState.DEFAULT_ENERGY
        assert mood._emotional_valence == MoodState.DEFAULT_VALENCE
        assert mood._irritability == MoodState.DEFAULT_IRRITABILITY
        assert mood._enthusiasm == MoodState.DEFAULT_ENTHUSIASM


class TestMoodSerialization:
    """Test suite for mood state serialization"""

    def test_to_dict(self):
        """Test serialization to dictionary"""
        mood = MoodState(
            energy_level=0.7,
            emotional_valence=0.3,
            irritability=0.4,
            enthusiasm=0.8
        )

        data = mood.to_dict()

        assert data["energy_level"] == 0.7
        assert data["emotional_valence"] == 0.3
        assert data["irritability"] == 0.4
        assert data["enthusiasm"] == 0.8
        assert "created_at" in data
        assert "updated_at" in data

    def test_from_dict(self):
        """Test deserialization from dictionary"""
        mood = MoodState()

        data = {
            "energy_level": 0.7,
            "emotional_valence": 0.3,
            "irritability": 0.4,
            "enthusiasm": 0.8
        }

        mood.from_dict(data)

        assert mood._energy_level == 0.7
        assert mood._emotional_valence == 0.3
        assert mood._irritability == 0.4
        assert mood._enthusiasm == 0.8

    def test_roundtrip_serialization(self):
        """Test that serialization and deserialization preserve state"""
        original = MoodState(
            energy_level=0.6,
            emotional_valence=-0.2,
            irritability=0.5,
            enthusiasm=0.7
        )

        data = original.to_dict()
        restored = MoodState()
        restored.from_dict(data)

        assert restored._energy_level == original._energy_level
        assert restored._emotional_valence == original._emotional_valence
        assert restored._irritability == original._irritability
        assert restored._enthusiasm == original._enthusiasm
