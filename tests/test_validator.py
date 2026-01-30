"""
Unit tests for Persona Validator Module
Tests PersonaValidator class for Freeman voice validation
"""

import pytest
from unittest.mock import patch
from datetime import datetime

from src.content.validator import PersonaValidator, ValidationResult, validate_content
from src.content.generator import GeneratedContent
from src.content.ideation import ContentIdea


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'persona': {
            'mission': 'Awaken people to see where they live',
            'core_values': [
                'Individual freedom',
                'Critique of consumer society',
                'Skepticism toward authority'
            ],
            'voice': {
                'style': 'sarcastic, philosophical, provocative',
                'tone': 'sharp, ironic, deep',
                'language': 'direct, uncensored',
                'avoid': ['corporate speak', 'generic motivational quotes', 'superficial positivity']
            }
        },
        'generation': {
            'validation': {
                'persona_match_threshold': 0.7,
                'reject_generic': True,
                'reject_corporate': True
            }
        }
    }


@pytest.fixture
def validator(mock_config):
    """Create PersonaValidator instance with mocked config"""
    with patch.object(PersonaValidator, '_load_config', return_value=mock_config):
        return PersonaValidator()


@pytest.fixture
def sample_idea():
    """Sample ContentIdea for testing"""
    return ContentIdea(
        topic="AI and consciousness",
        source="philosophical_topics",
        category="priority",
        angle="The illusion of AI consciousness",
        tone="philosophical",
        generated_at=datetime.now(),
        metadata={'depth': 'high'}
    )


def create_content(text: str, idea: ContentIdea) -> GeneratedContent:
    """Helper to create GeneratedContent for testing"""
    return GeneratedContent(
        text=text,
        idea=idea,
        platform="twitter",
        character_count=len(text),
        generated_at=datetime.now(),
        llm_provider="claude"
    )


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_validation_result_creation(self):
        """Test creating ValidationResult instance"""
        result = ValidationResult(
            passed=True,
            score=0.85,
            feedback=["Good content"],
            checks={'check1': True, 'check2': True}
        )

        assert result.passed is True
        assert result.score == 0.85
        assert result.feedback == ["Good content"]
        assert result.checks == {'check1': True, 'check2': True}

    def test_to_dict(self):
        """Test converting ValidationResult to dictionary"""
        result = ValidationResult(
            passed=False,
            score=0.4,
            feedback=["Failed check"],
            checks={'check1': False}
        )

        result_dict = result.to_dict()

        assert result_dict['passed'] is False
        assert result_dict['score'] == 0.4
        assert result_dict['feedback'] == ["Failed check"]
        assert result_dict['checks'] == {'check1': False}


class TestPersonaValidator:
    """Test PersonaValidator class"""

    def test_initialization(self, validator, mock_config):
        """Test PersonaValidator initialization"""
        assert validator.config == mock_config
        assert validator.threshold == 0.7
        assert validator.reject_generic is True
        assert validator.reject_corporate is True

    def test_validate_good_freeman_content(self, validator, sample_idea):
        """Test validation passes for good Freeman content"""
        content = create_content(
            "Everyone's talking about AI consciousness. Nobody's asking who benefits from the confusion.",
            sample_idea
        )

        result = validator.validate(content)

        assert result.passed is True
        assert result.score >= validator.threshold
        assert result.checks['no_corporate_speak'] is True
        assert result.checks['no_generic_content'] is True

    def test_validate_corporate_speak_rejected(self, validator, sample_idea):
        """Test corporate speak is rejected"""
        content = create_content(
            "Let's leverage AI to synergize our paradigm and disrupt the market.",
            sample_idea
        )

        result = validator.validate(content)

        assert result.passed is False
        assert result.checks['no_corporate_speak'] is False
        assert any('corporate speak' in f.lower() for f in result.feedback)

    def test_validate_generic_motivational_rejected(self, validator, sample_idea):
        """Test generic motivational content is rejected"""
        content = create_content(
            "Believe in yourself! Follow your dreams and never give up!",
            sample_idea
        )

        result = validator.validate(content)

        assert result.passed is False
        assert result.checks['no_generic_content'] is False
        assert any('generic' in f.lower() for f in result.feedback)

    def test_validate_superficial_positivity_rejected(self, validator, sample_idea):
        """Test superficial positivity is rejected"""
        content = create_content(
            "Amazing vibes today! Stay positive! Good vibes only!",
            sample_idea
        )

        result = validator.validate(content)

        assert result.passed is False
        assert result.checks['no_superficial_positivity'] is False

    def test_validate_philosophical_provocation_passes(self, validator, sample_idea):
        """Test philosophical provocation passes validation"""
        content = create_content(
            "The system doesn't fear your anger. It fears your questions. Why?",
            sample_idea
        )

        result = validator.validate(content)

        assert result.passed is True
        assert result.score >= validator.threshold
        assert result.checks['has_unique_perspective'] is True
        assert result.checks['provocative_but_meaningful'] is True

    def test_check_unique_perspective_with_questions(self, validator):
        """Test unique perspective check detects questions"""
        has_perspective, score = validator._check_unique_perspective(
            "Why does nobody ask the real questions?"
        )

        assert has_perspective is True
        assert score > 0

    def test_check_unique_perspective_without_indicators(self, validator):
        """Test unique perspective check fails for generic statements"""
        has_perspective, score = validator._check_unique_perspective(
            "This is a simple statement."
        )

        assert has_perspective is False

    def test_check_depth_with_systems_thinking(self, validator):
        """Test depth check passes for systems thinking"""
        has_depth, score = validator._check_depth(
            "The system is designed to control your perception of reality through manufactured consensus."
        )

        assert has_depth is True
        assert score >= 0.5

    def test_check_depth_fails_for_short_superficial(self, validator):
        """Test depth check fails for very short content"""
        has_depth, score = validator._check_depth("Nice day!")

        assert has_depth is False

    def test_check_mission_alignment_with_keywords(self, validator, sample_idea):
        """Test mission alignment check with mission keywords"""
        content = create_content(
            "Wake up and question the truth behind the system's control of your consciousness.",
            sample_idea
        )

        aligned, score = validator._check_mission_alignment(content)

        assert aligned is True
        assert score >= 0.4

    def test_check_mission_alignment_priority_topic_bonus(self, validator):
        """Test priority topics get mission alignment bonus"""
        priority_idea = ContentIdea(
            topic="AI and consciousness",
            source="mission_alignment",
            category="priority",
            angle="test",
            tone="philosophical",
            generated_at=datetime.now()
        )

        content = create_content("Test content about consciousness", priority_idea)
        aligned, score = validator._check_mission_alignment(content)

        # Should get bonus for priority category
        assert score > 0

    def test_check_meaningful_provocation(self, validator):
        """Test meaningful provocation check"""
        is_meaningful, score = validator._check_meaningful_provocation(
            "Why does everyone pretend to ignore the real reasons behind the system?"
        )

        assert is_meaningful is True
        assert score > 0

    def test_check_no_platitudes_detects_platitudes(self, validator):
        """Test platitude detection"""
        no_platitudes, score = validator._check_no_platitudes(
            "Everything happens for a reason and you just need to be yourself."
        )

        assert no_platitudes is False
        assert score == 0.0

    def test_check_no_platitudes_passes_real_content(self, validator):
        """Test platitude check passes for real content"""
        no_platitudes, score = validator._check_no_platitudes(
            "The system conditions you to accept platitudes instead of truth."
        )

        assert no_platitudes is True
        assert score == 1.0

    def test_validate_batch(self, validator, sample_idea):
        """Test batch validation"""
        contents = [
            create_content("Good Freeman content with depth and questions. Why?", sample_idea),
            create_content("Leverage synergy to optimize paradigm", sample_idea),
            create_content("The system fears your consciousness and awareness of truth", sample_idea)
        ]

        results = validator.validate_batch(contents)

        assert len(results) == 3
        assert all(isinstance(r, ValidationResult) for r in results)
        # First and third should pass, second should fail
        assert results[0].passed is True
        assert results[1].passed is False
        assert results[2].passed is True

    def test_get_passing_content(self, validator, sample_idea):
        """Test filtering to only passing content"""
        contents = [
            create_content("The truth behind the system's control is hidden from you. Question everything.", sample_idea),
            create_content("Synergize and leverage paradigm shift", sample_idea),
            create_content("Wake up and see the reality of consciousness manipulation", sample_idea)
        ]

        passing = validator.get_passing_content(contents)

        # Should only return content that passed validation
        assert len(passing) <= 3
        assert all(isinstance(c, GeneratedContent) for c in passing)

    def test_corporate_patterns_comprehensive(self, validator):
        """Test all corporate speak patterns are detected"""
        corporate_phrases = [
            "synergy between teams",
            "leverage our assets",
            "paradigm shift",
            "disrupt the industry",
            "utilize resources",
            "facilitate progress",
            "circle back tomorrow",
            "low-hanging fruit"
        ]

        for phrase in corporate_phrases:
            has_corporate, feedback = validator._check_corporate_speak(phrase)
            assert has_corporate is True, f"Failed to detect: {phrase}"

    def test_generic_patterns_comprehensive(self, validator):
        """Test all generic motivational patterns are detected"""
        generic_phrases = [
            "believe in yourself",
            "follow your dreams",
            "never give up",
            "you can do it",
            "stay positive",
            "hustle harder"
        ]

        for phrase in generic_phrases:
            is_generic, feedback = validator._check_generic_content(phrase)
            assert is_generic is True, f"Failed to detect: {phrase}"

    def test_validation_threshold_enforcement(self, mock_config, sample_idea):
        """Test that threshold is properly enforced"""
        # Set very high threshold
        mock_config['generation']['validation']['persona_match_threshold'] = 0.95

        with patch.object(PersonaValidator, '_load_config', return_value=mock_config):
            validator = PersonaValidator()

            # Even good content might not pass very high threshold
            content = create_content("Question everything.", sample_idea)
            result = validator.validate(content)

            # Should fail due to high threshold
            assert result.score < 0.95

    def test_validation_feedback_on_pass(self, validator, sample_idea):
        """Test that passing validation includes positive feedback"""
        content = create_content(
            "The system manipulates your consciousness. Wake up and question the truth behind their control.",
            sample_idea
        )

        result = validator.validate(content)

        if result.passed:
            assert len(result.feedback) > 0
            assert any('matches' in f.lower() or 'ok' in f.lower() or 'pass' in f.lower() for f in result.feedback)


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_validate_content_function(self, mock_config, sample_idea):
        """Test validate_content convenience function"""
        with patch.object(PersonaValidator, '_load_config', return_value=mock_config):
            content = create_content(
                "Everyone talks about freedom. Nobody asks who took it.",
                sample_idea
            )

            result = validate_content(content)

            assert isinstance(result, ValidationResult)
