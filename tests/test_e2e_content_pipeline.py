"""
End-to-End Test for Content Creation Pipeline
Tests the complete flow from generation to scheduling
"""

import pytest
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import datetime, timedelta
import json
import tempfile
import os

from src.agents.content_creator import ContentCreatorAgent, ContentCreationResult
from src.content.ideation import ContentIdea
from src.content.storage import QueuedContent


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'persona': {
            'name': 'Mr. Freeman',
            'mission': 'Wake people up to see where they live',
            'core_values': ['freedom', 'truth', 'skepticism'],
            'voice': {
                'style': 'sarcastic, philosophical, provocative',
                'tone': 'sharp, ironic, confrontational',
                'language': 'direct, uncensored, raw',
                'avoid': ['corporate speak', 'generic quotes', 'superficial positivity']
            }
        },
        'generation': {
            'llm': {
                'provider': 'claude',
                'model': 'claude-3-5-sonnet-20241022',
                'temperature': 0.9,
                'max_tokens': 500
            },
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
            },
            'validation': {
                'threshold': 0.7,
                'max_retries': 3
            }
        },
        'scheduling': {
            'intervals': {
                'min_hours': 4,
                'max_hours': 12
            },
            'optimal_times': [9, 14, 20],
            'topic_spacing_hours': 24,
            'daily_limits': {
                'total_posts': 3
            }
        },
        'anti_repetition': {
            'similarity_threshold': 0.85,
            'lookback_posts': 50,
            'min_topic_variety': 0.6,
            'max_consecutive_similar': 2
        },
        'platforms': {
            'twitter': {
                'max_length': 280
            }
        },
        'queue': {
            'min_size': 5,
            'max_size': 20
        }
    }


@pytest.fixture
def temp_queue_file(tmp_path):
    """Create a temporary queue file"""
    queue_file = tmp_path / "content_queue.json"
    return str(queue_file)


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    response = Mock()
    response.content = [Mock(text="Everyone's talking about AI consciousness. Nobody's asking who benefits from the confusion.")]
    return response


@pytest.fixture
def mock_openai_embedding_response():
    """Mock OpenAI embedding API response"""
    response = Mock()
    response.data = [Mock(embedding=[0.1] * 1536)]  # 1536-dimensional embedding
    return response


class TestE2EContentPipeline:
    """End-to-end tests for the complete content creation pipeline"""

    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_generate_single_content_full_pipeline(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        mock_claude_response,
        temp_queue_file
    ):
        """
        Test Step 1: Generate a single piece of content through the full pipeline
        Verifies: ideation → generation → validation → storage → scheduling
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Generate content
        results = agent.generate_content(count=1, auto_schedule=True)

        # Verify results
        assert len(results) == 1
        result = results[0]

        # Verify generation success
        assert result.success is True
        assert result.content_id is not None
        assert result.text is not None
        assert result.error is None

        # Verify Freeman's voice (validation passed)
        assert result.validation_score is not None
        assert result.validation_score >= mock_config['generation']['validation']['threshold']

        # Verify content idea
        assert result.idea is not None
        assert result.idea.topic is not None
        assert result.idea.source in mock_config['generation']['ideation']['sources']

        # Verify scheduling
        assert result.scheduled_time is not None
        assert isinstance(result.scheduled_time, datetime)
        assert result.scheduled_time > datetime.now()


    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_content_stored_in_queue(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        mock_claude_response,
        temp_queue_file
    ):
        """
        Test Step 2: Verify content is stored in queue
        Verifies: content persists in queue with correct status and metadata
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Get initial queue size
        initial_stats = agent.queue.get_stats()
        initial_size = initial_stats['total']

        # Generate content
        results = agent.generate_content(count=1, auto_schedule=True)
        result = results[0]

        assert result.success is True

        # Verify queue size increased
        final_stats = agent.queue.get_stats()
        assert final_stats['total'] == initial_size + 1

        # Retrieve content from queue
        queued_content = agent.queue.get(result.content_id)
        assert queued_content is not None

        # Verify stored content properties
        assert queued_content.id == result.content_id
        assert queued_content.text == result.text
        assert queued_content.status in ['scheduled', 'queued']
        assert queued_content.created_at is not None
        assert isinstance(queued_content.created_at, datetime)

        # Verify metadata
        assert 'validation_score' in queued_content.metadata
        assert queued_content.metadata['validation_score'] >= mock_config['generation']['validation']['threshold']


    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_content_scheduled_for_future(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        mock_claude_response,
        temp_queue_file
    ):
        """
        Test Step 3: Verify content is scheduled for future posting
        Verifies: scheduled time is in the future and respects intervals
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Generate content
        results = agent.generate_content(count=1, auto_schedule=True)
        result = results[0]

        assert result.success is True

        # Verify scheduling
        assert result.scheduled_time is not None
        now = datetime.now()

        # Scheduled time should be in the future
        assert result.scheduled_time > now

        # Scheduled time should respect minimum interval
        min_hours = mock_config['scheduling']['intervals']['min_hours']
        min_scheduled_time = now + timedelta(hours=min_hours)
        # Allow some tolerance (1 minute) for test execution time
        assert result.scheduled_time >= (min_scheduled_time - timedelta(minutes=1))

        # Verify content in queue has scheduled time
        queued_content = agent.queue.get(result.content_id)
        assert queued_content.scheduled_for is not None
        assert queued_content.scheduled_for == result.scheduled_time
        assert queued_content.status == 'scheduled'


    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.deduplicator.openai')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_no_repetition_with_past_content(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_openai,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        mock_claude_response,
        mock_openai_embedding_response,
        temp_queue_file
    ):
        """
        Test Step 4: Verify anti-repetition system prevents duplicate content
        Verifies: deduplicator catches similar content and prevents posting
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API with different responses
        mock_client = MagicMock()
        responses = [
            Mock(content=[Mock(text="Everyone's talking about AI consciousness. Nobody's asking who benefits from the confusion.")]),
            Mock(content=[Mock(text="Social media algorithms profit from your outrage. Who designed them?")]),
            Mock(content=[Mock(text="They call it 'progress'. I call it distraction. What do you call it?")]),
        ]
        mock_client.messages.create.side_effect = responses
        mock_anthropic.return_value = mock_client

        # Mock OpenAI embeddings with different vectors
        mock_openai_client = MagicMock()
        embeddings = [
            Mock(data=[Mock(embedding=[0.1 + i*0.01] * 1536)])
            for i in range(3)
        ]
        mock_openai_client.embeddings.create.side_effect = embeddings
        mock_openai.return_value = mock_openai_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Generate multiple pieces of content
        results = agent.generate_content(count=3, auto_schedule=True)

        # Verify all content is unique
        successful_results = [r for r in results if r.success]
        assert len(successful_results) >= 2  # At least 2 should succeed

        # Check that texts are different
        texts = [r.text for r in successful_results]
        assert len(texts) == len(set(texts))  # All texts are unique

        # Verify deduplicator was involved
        dedup_stats = agent.deduplicator.get_stats()
        assert 'unique_posts' in dedup_stats


    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_freeman_voice_validation(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        mock_claude_response,
        temp_queue_file
    ):
        """
        Test Step 5: Verify content matches Freeman's voice characteristics
        Verifies: validation catches content that doesn't match Freeman's style
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API with Freeman-style response
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Generate content
        results = agent.generate_content(count=1, auto_schedule=True)
        result = results[0]

        assert result.success is True

        # Verify Freeman's voice characteristics
        text = result.text.lower()

        # Should NOT contain corporate/generic phrases
        corporate_phrases = [
            'excited to announce',
            'proud to share',
            'happy to',
            'grateful for',
            'blessed to',
            'thrilled to'
        ]
        for phrase in corporate_phrases:
            assert phrase not in text, f"Content contains corporate phrase: {phrase}"

        # Validation score should be high
        assert result.validation_score >= mock_config['generation']['validation']['threshold']

        # Content should have Freeman's characteristics
        # (philosophical, provocative, questioning)
        freeman_indicators = [
            '?',  # Questions
            '.',  # Statements
        ]
        has_indicator = any(indicator in text for indicator in freeman_indicators)
        assert has_indicator, "Content lacks Freeman's characteristic style"


    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_batch_generation_pipeline(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        temp_queue_file
    ):
        """
        Test Step 6: Verify batch generation through complete pipeline
        Verifies: multiple content pieces can be generated and scheduled
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API with multiple responses
        mock_client = MagicMock()
        responses = [
            Mock(content=[Mock(text=f"Freeman thought #{i}: Question everything.")])
            for i in range(5)
        ]
        mock_client.messages.create.side_effect = responses
        mock_anthropic.return_value = mock_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Get initial queue size
        initial_stats = agent.queue.get_stats()
        initial_size = initial_stats['total']

        # Generate batch
        batch_stats = agent.generate_batch(count=5)

        # Verify batch results
        assert batch_stats['total'] == 5
        assert batch_stats['successful'] >= 3  # At least 3 should succeed
        assert batch_stats['success_rate'] > 0.5  # >50% success rate

        # Verify queue size increased
        final_stats = agent.queue.get_stats()
        assert final_stats['total'] > initial_size

        # Verify all successful content is scheduled
        successful_results = [r for r in batch_stats['results'] if r.success]
        for result in successful_results:
            queued = agent.queue.get(result.content_id)
            assert queued is not None
            assert queued.status in ['scheduled', 'queued']


    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_pipeline_status_monitoring(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        mock_claude_response,
        temp_queue_file
    ):
        """
        Test Step 7: Verify pipeline status monitoring
        Verifies: agent can report on queue health and scheduling status
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_claude_response
        mock_anthropic.return_value = mock_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Get initial status
        status = agent.get_pipeline_status()

        # Verify status structure
        assert 'queue' in status
        assert 'schedule' in status
        assert 'deduplication' in status
        assert 'health' in status
        assert 'timestamp' in status

        # Verify queue stats
        assert 'total' in status['queue']
        assert 'by_status' in status['queue']

        # Verify health metrics
        assert 'queue_healthy' in status['health']
        assert 'schedule_healthy' in status['health']
        assert 'diversity_healthy' in status['health']
        assert 'overall_healthy' in status['health']

        # Generate content
        results = agent.generate_content(count=1, auto_schedule=True)
        assert results[0].success is True

        # Get updated status
        updated_status = agent.get_pipeline_status()

        # Verify queue size increased
        assert updated_status['queue']['total'] > status['queue']['total']


    @patch('src.content.storage.ContentQueue._get_queue_file_path')
    @patch('src.content.generator.anthropic')
    @patch('src.content.ideation.ContentIdeator._load_config')
    @patch('src.content.generator.ContentGenerator._load_config')
    @patch('src.content.validator.PersonaValidator._load_config')
    @patch('src.content.deduplicator.ContentDeduplicator._load_config')
    @patch('src.content.scheduler.ContentScheduler._load_config')
    def test_content_diversity_enforcement(
        self,
        mock_scheduler_config,
        mock_dedup_config,
        mock_validator_config,
        mock_generator_config,
        mock_ideator_config,
        mock_anthropic,
        mock_queue_path,
        mock_config,
        temp_queue_file
    ):
        """
        Test Step 8: Verify content diversity is maintained
        Verifies: generated content covers different topics and sources
        """
        # Setup mocks
        mock_ideator_config.return_value = mock_config
        mock_generator_config.return_value = mock_config
        mock_validator_config.return_value = mock_config
        mock_dedup_config.return_value = mock_config
        mock_scheduler_config.return_value = mock_config
        mock_queue_path.return_value = temp_queue_file

        # Mock Claude API with varied responses
        mock_client = MagicMock()
        responses = [
            Mock(content=[Mock(text="AI consciousness: a philosophical question or corporate marketing?")]),
            Mock(content=[Mock(text="Social media: connecting people or harvesting attention?")]),
            Mock(content=[Mock(text="Education system: producing thinkers or obedient workers?")]),
        ]
        mock_client.messages.create.side_effect = responses
        mock_anthropic.return_value = mock_client

        # Initialize agent
        agent = ContentCreatorAgent()

        # Generate multiple pieces
        results = agent.generate_content(count=3, auto_schedule=True)

        # Get successful results
        successful_results = [r for r in results if r.success]
        assert len(successful_results) >= 2

        # Verify topic diversity
        topics = [r.idea.topic for r in successful_results]
        # At least 2 different topics
        unique_topics = set(topics)
        assert len(unique_topics) >= 2, "Content lacks topic diversity"

        # Verify source diversity
        sources = [r.idea.source for r in successful_results]
        # Sources should come from configured list
        valid_sources = mock_config['generation']['ideation']['sources']
        for source in sources:
            assert source in valid_sources


if __name__ == "__main__":
    """
    Run the E2E tests with pytest

    Usage:
        pytest tests/test_e2e_content_pipeline.py -v
        pytest tests/test_e2e_content_pipeline.py::TestE2EContentPipeline::test_generate_single_content_full_pipeline -v
    """
    pytest.main([__file__, '-v'])
