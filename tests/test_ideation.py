"""
Unit tests for Content Ideation Module
Tests ContentIdeator class for idea generation from multiple sources
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.content.ideation import ContentIdeator, ContentIdea, generate_ideas


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'persona': {
            'mission': 'Test mission to awaken people',
            'core_values': ['freedom', 'truth', 'skepticism'],
            'voice': {
                'style': 'sarcastic, philosophical',
                'tone': 'sharp, ironic',
                'avoid': ['corporate speak', 'generic quotes']
            }
        },
        'generation': {
            'ideation': {
                'sources': [
                    'mission_alignment',
                    'philosophical_topics',
                    'social_commentary',
                    'current_trends',
                    'memory_events'
                ],
                'topics': {
                    'priority': [
                        'AI and consciousness',
                        'Social manipulation',
                        'Media and truth'
                    ],
                    'secondary': [
                        'Technology',
                        'Education critique',
                        'Political hypocrisy'
                    ]
                }
            }
        }
    }


@pytest.fixture
def ideator(mock_config):
    """Create ContentIdeator instance with mocked config"""
    with patch.object(ContentIdeator, '_load_config', return_value=mock_config):
        return ContentIdeator()


class TestContentIdea:
    """Test ContentIdea dataclass"""

    def test_content_idea_creation(self):
        """Test creating a ContentIdea instance"""
        idea = ContentIdea(
            topic="Test Topic",
            source="mission_alignment",
            category="priority",
            angle="Test angle",
            tone="philosophical",
            generated_at=datetime.now(),
            metadata={'test': True}
        )

        assert idea.topic == "Test Topic"
        assert idea.source == "mission_alignment"
        assert idea.category == "priority"
        assert idea.angle == "Test angle"
        assert idea.tone == "philosophical"
        assert idea.metadata == {'test': True}

    def test_to_dict(self):
        """Test converting ContentIdea to dictionary"""
        now = datetime.now()
        idea = ContentIdea(
            topic="Test Topic",
            source="test",
            category="priority",
            angle="Test angle",
            tone="philosophical",
            generated_at=now,
            metadata={'key': 'value'}
        )

        result = idea.to_dict()

        assert result['topic'] == "Test Topic"
        assert result['source'] == "test"
        assert result['category'] == "priority"
        assert result['angle'] == "Test angle"
        assert result['tone'] == "philosophical"
        assert result['generated_at'] == now.isoformat()
        assert result['metadata'] == {'key': 'value'}


class TestContentIdeator:
    """Test ContentIdeator class"""

    def test_initialization(self, ideator, mock_config):
        """Test ContentIdeator initialization"""
        assert ideator.config == mock_config
        assert ideator.mission == 'Test mission to awaken people'
        assert len(ideator.core_values) == 3
        assert len(ideator.priority_topics) == 3
        assert len(ideator.secondary_topics) == 3
        assert len(ideator.all_topics) == 6

    def test_load_config_file_not_found(self):
        """Test error handling when config file not found"""
        with pytest.raises(FileNotFoundError):
            ContentIdeator(config_path="nonexistent_config.yaml")

    def test_generate_idea_random_source(self, ideator):
        """Test generating idea with random source"""
        idea = ideator.generate_idea()

        assert isinstance(idea, ContentIdea)
        assert idea.source in [
            'mission_alignment',
            'philosophical_topics',
            'social_commentary',
            'current_trends',
            'memory_events'
        ]
        assert idea.topic is not None
        assert idea.angle is not None
        assert idea.tone in ['philosophical', 'sarcastic', 'confrontational', 'supportive']
        assert isinstance(idea.generated_at, datetime)

    def test_generate_idea_specific_source_mission(self, ideator):
        """Test generating mission-aligned idea"""
        idea = ideator.generate_idea(source='mission_alignment')

        assert idea.source == 'mission_alignment'
        assert idea.category == 'priority'
        assert idea.tone in ['philosophical', 'confrontational']
        assert idea.metadata.get('mission_critical') is True

    def test_generate_idea_specific_source_philosophical(self, ideator):
        """Test generating philosophical idea"""
        idea = ideator.generate_idea(source='philosophical_topics')

        assert idea.source == 'philosophical_topics'
        assert idea.category in ['priority', 'secondary']
        assert idea.tone == 'philosophical'
        assert idea.metadata.get('depth') == 'high'

    def test_generate_idea_specific_source_social_commentary(self, ideator):
        """Test generating social commentary idea"""
        idea = ideator.generate_idea(source='social_commentary')

        assert idea.source == 'social_commentary'
        assert idea.category == 'secondary'
        assert idea.tone in ['sarcastic', 'confrontational']
        assert idea.metadata.get('commentary_type') == 'social_critique'

    def test_generate_idea_specific_source_trends(self, ideator):
        """Test generating trend-based idea"""
        idea = ideator.generate_idea(source='current_trends')

        assert idea.source == 'current_trends'
        assert idea.category == 'secondary'
        assert idea.tone in ['sarcastic', 'philosophical']
        assert idea.metadata.get('trending') is True
        assert idea.metadata.get('timely') is True

    def test_generate_idea_specific_source_memory(self, ideator):
        """Test generating memory-based idea"""
        idea = ideator.generate_idea(source='memory_events')

        assert idea.source == 'memory_events'
        assert idea.category == 'priority'
        assert idea.tone in ['philosophical', 'supportive']
        assert idea.metadata.get('based_on_interactions') is True

    def test_generate_idea_invalid_source(self, ideator):
        """Test error handling for invalid source"""
        with pytest.raises(ValueError, match="Invalid source"):
            ideator.generate_idea(source='invalid_source')

    def test_generate_batch_diverse(self, ideator):
        """Test generating diverse batch of ideas"""
        ideas = ideator.generate_batch(count=5, diverse=True)

        assert len(ideas) == 5
        assert all(isinstance(idea, ContentIdea) for idea in ideas)

        # Check diversity - all 5 sources should be used
        sources = [idea.source for idea in ideas]
        assert len(set(sources)) == 5  # All unique sources

    def test_generate_batch_non_diverse(self, ideator):
        """Test generating non-diverse batch (random sources)"""
        ideas = ideator.generate_batch(count=10, diverse=False)

        assert len(ideas) == 10
        assert all(isinstance(idea, ContentIdea) for idea in ideas)

        # Sources should be random, not necessarily diverse
        sources = [idea.source for idea in ideas]
        assert len(sources) == 10

    def test_generate_batch_single_idea(self, ideator):
        """Test generating batch with single idea"""
        ideas = ideator.generate_batch(count=1, diverse=True)

        assert len(ideas) == 1
        assert isinstance(ideas[0], ContentIdea)

    def test_get_topic_distribution(self, ideator):
        """Test topic distribution analysis"""
        ideas = [
            ContentIdea("Topic A", "test", "priority", "angle", "tone", datetime.now()),
            ContentIdea("Topic A", "test", "priority", "angle", "tone", datetime.now()),
            ContentIdea("Topic B", "test", "priority", "angle", "tone", datetime.now()),
        ]

        distribution = ideator.get_topic_distribution(ideas)

        assert distribution["Topic A"] == 2
        assert distribution["Topic B"] == 1
        assert len(distribution) == 2

    def test_get_source_distribution(self, ideator):
        """Test source distribution analysis"""
        ideas = [
            ContentIdea("Topic", "mission_alignment", "priority", "angle", "tone", datetime.now()),
            ContentIdea("Topic", "mission_alignment", "priority", "angle", "tone", datetime.now()),
            ContentIdea("Topic", "philosophical_topics", "priority", "angle", "tone", datetime.now()),
        ]

        distribution = ideator.get_source_distribution(ideas)

        assert distribution["mission_alignment"] == 2
        assert distribution["philosophical_topics"] == 1
        assert len(distribution) == 2

    def test_get_topic_distribution_empty_list(self, ideator):
        """Test distribution with empty list"""
        distribution = ideator.get_topic_distribution([])

        assert distribution == {}

    def test_get_source_distribution_empty_list(self, ideator):
        """Test distribution with empty list"""
        distribution = ideator.get_source_distribution([])

        assert distribution == {}


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_generate_ideas_function(self, mock_config):
        """Test generate_ideas convenience function"""
        with patch.object(ContentIdeator, '_load_config', return_value=mock_config):
            ideas = generate_ideas(count=3, diverse=True)

            assert len(ideas) == 3
            assert all(isinstance(idea, ContentIdea) for idea in ideas)
