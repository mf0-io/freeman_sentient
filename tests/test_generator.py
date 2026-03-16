"""
Unit tests for Content Generator Module
Tests ContentGenerator class for LLM-based content generation
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
import os

from src.content.generator import ContentGenerator, GeneratedContent, generate_content
from src.content.ideation import ContentIdea


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        'persona': {
            'mission': 'Test mission',
            'core_values': ['freedom', 'truth'],
            'voice': {
                'style': 'sarcastic, philosophical',
                'tone': 'sharp, ironic',
                'language': 'direct, uncensored',
                'avoid': ['corporate speak', 'generic quotes']
            }
        },
        'generation': {
            'llm': {
                'provider': 'claude',
                'model': 'claude-3-5-sonnet-20241022',
                'temperature': 0.9,
                'max_tokens': 500,
                'fallback': {
                    'provider': 'openai',
                    'model': 'gpt-4',
                    'temperature': 0.9,
                    'max_tokens': 500
                }
            },
            'validation': {
                'max_retries': 3
            }
        },
        'platforms': {
            'twitter': {
                'max_length': 280
            },
            'telegram': {
                'max_length': 4096
            }
        }
    }


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


@pytest.fixture
def mock_claude_response():
    """Mock Claude API response"""
    response = Mock()
    response.content = [Mock(text="Everyone's talking about AI consciousness. Nobody's asking who benefits from the confusion.")]
    return response


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    response = Mock()
    choice = Mock()
    message = Mock()
    message.content = "The system doesn't fear your anger. It fears your questions. Why?"
    choice.message = message
    response.choices = [choice]
    return response


class TestGeneratedContent:
    """Test GeneratedContent dataclass"""

    def test_generated_content_creation(self, sample_idea):
        """Test creating GeneratedContent instance"""
        now = datetime.now()
        content = GeneratedContent(
            text="Test tweet text",
            idea=sample_idea,
            platform="twitter",
            character_count=15,
            generated_at=now,
            llm_provider="claude",
            metadata={'attempt': 1}
        )

        assert content.text == "Test tweet text"
        assert content.idea == sample_idea
        assert content.platform == "twitter"
        assert content.character_count == 15
        assert content.generated_at == now
        assert content.llm_provider == "claude"
        assert content.metadata == {'attempt': 1}

    def test_to_dict(self, sample_idea):
        """Test converting GeneratedContent to dictionary"""
        now = datetime.now()
        content = GeneratedContent(
            text="Test",
            idea=sample_idea,
            platform="twitter",
            character_count=4,
            generated_at=now,
            llm_provider="claude",
            metadata={}
        )

        result = content.to_dict()

        assert result['text'] == "Test"
        assert result['platform'] == "twitter"
        assert result['character_count'] == 4
        assert result['generated_at'] == now.isoformat()
        assert result['llm_provider'] == "claude"
        assert 'idea' in result


class TestContentGenerator:
    """Test ContentGenerator class"""

    def test_initialization_with_claude(self, mock_config):
        """Test initialization with Claude API key"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_anthropic.Anthropic.return_value = Mock()
                        generator = ContentGenerator()

                        assert generator.config == mock_config
                        assert generator.claude_client is not None

    def test_initialization_with_openai(self, mock_config):
        """Test initialization with OpenAI API key"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                with patch('src.content.generator.OPENAI_AVAILABLE', True):
                    with patch('src.content.generator.openai') as mock_openai:
                        generator = ContentGenerator()

                        assert generator.config == mock_config
                        assert generator.openai_client is not None

    def test_initialization_no_api_keys(self, mock_config):
        """Test error when no API keys available"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {}, clear=True):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', False):
                    with patch('src.content.generator.OPENAI_AVAILABLE', False):
                        with pytest.raises(RuntimeError, match="No LLM provider available"):
                            ContentGenerator()

    def test_build_system_prompt(self, mock_config):
        """Test system prompt building"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic'):
                        generator = ContentGenerator()
                        prompt = generator.system_prompt

                        assert 'Freeman' in prompt
                        assert 'Test mission' in prompt
                        assert 'freedom' in prompt
                        assert 'truth' in prompt
                        assert 'sarcastic' in prompt
                        assert 'philosophical' in prompt

    def test_build_generation_prompt(self, mock_config, sample_idea):
        """Test generation prompt building"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic'):
                        generator = ContentGenerator()
                        prompt = generator._build_generation_prompt(sample_idea, 'twitter', 280)

                        assert sample_idea.topic in prompt
                        assert sample_idea.angle in prompt
                        assert sample_idea.tone in prompt
                        assert '280' in prompt
                        assert 'twitter' in prompt

    def test_generate_with_claude_success(self, mock_config, sample_idea, mock_claude_response):
        """Test successful generation with Claude"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        mock_client.messages.create.return_value = mock_claude_response
                        mock_anthropic.Anthropic.return_value = mock_client

                        generator = ContentGenerator()
                        content = generator.generate(sample_idea, platform='twitter')

                        assert content is not None
                        assert isinstance(content, GeneratedContent)
                        assert content.text == "Everyone's talking about AI consciousness. Nobody's asking who benefits from the confusion."
                        assert content.platform == 'twitter'
                        assert content.llm_provider == 'claude'
                        assert content.character_count <= 280

    def test_generate_with_openai_success(self, mock_config, sample_idea, mock_openai_response):
        """Test successful generation with OpenAI"""
        mock_config['generation']['llm']['provider'] = 'openai'

        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                with patch('src.content.generator.OPENAI_AVAILABLE', True):
                    with patch('src.content.generator.openai') as mock_openai:
                        mock_client = Mock()
                        mock_client.chat.completions.create.return_value = mock_openai_response
                        mock_openai.OpenAI.return_value = mock_client

                        generator = ContentGenerator()
                        content = generator.generate(sample_idea, platform='twitter')

                        assert content is not None
                        assert isinstance(content, GeneratedContent)
                        assert content.llm_provider == 'openai'

    def test_generate_removes_quotes(self, mock_config, sample_idea):
        """Test that generated content removes surrounding quotes"""
        response = Mock()
        response.content = [Mock(text='"This is a quoted tweet"')]

        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        mock_client.messages.create.return_value = response
                        mock_anthropic.Anthropic.return_value = mock_client

                        generator = ContentGenerator()
                        content = generator.generate(sample_idea)

                        assert content.text == "This is a quoted tweet"

    def test_generate_respects_max_length(self, mock_config, sample_idea):
        """Test that generation respects platform max length"""
        # Create a response that's too long
        long_text = "a" * 300
        response = Mock()
        response.content = [Mock(text=long_text)]

        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        mock_client.messages.create.return_value = response
                        mock_anthropic.Anthropic.return_value = mock_client

                        generator = ContentGenerator()
                        content = generator.generate(sample_idea, platform='twitter', max_retries=1)

                        # Should fail because text is too long
                        assert content is None

    def test_generate_batch(self, mock_config, sample_idea, mock_claude_response):
        """Test batch generation"""
        ideas = [sample_idea for _ in range(3)]

        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        mock_client.messages.create.return_value = mock_claude_response
                        mock_anthropic.Anthropic.return_value = mock_client

                        generator = ContentGenerator()
                        contents = generator.generate_batch(ideas, platform='twitter')

                        assert len(contents) == 3
                        assert all(isinstance(c, GeneratedContent) for c in contents)

    def test_generate_batch_with_failures(self, mock_config, sample_idea):
        """Test batch generation with some failures"""
        ideas = [sample_idea for _ in range(3)]

        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        # First two succeed, third fails
                        mock_client.messages.create.side_effect = [
                            Mock(content=[Mock(text="Tweet 1")]),
                            Mock(content=[Mock(text="Tweet 2")]),
                            Exception("API error")
                        ]
                        mock_anthropic.Anthropic.return_value = mock_client

                        generator = ContentGenerator()
                        contents = generator.generate_batch(ideas, platform='twitter')

                        # Should only return successful ones
                        assert len(contents) == 2

    def test_regenerate(self, mock_config, sample_idea, mock_claude_response):
        """Test content regeneration"""
        original_content = GeneratedContent(
            text="Original tweet",
            idea=sample_idea,
            platform="twitter",
            character_count=14,
            generated_at=datetime.now(),
            llm_provider="claude"
        )

        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        mock_client.messages.create.return_value = mock_claude_response
                        mock_anthropic.Anthropic.return_value = mock_client

                        generator = ContentGenerator()
                        new_content = generator.regenerate(original_content, reason="test")

                        assert new_content is not None
                        assert new_content.idea == sample_idea
                        assert new_content.platform == "twitter"

    def test_generate_api_error_retry(self, mock_config, sample_idea, mock_claude_response):
        """Test retry logic on API error"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        # Fail twice, succeed on third attempt
                        mock_client.messages.create.side_effect = [
                            Exception("API error 1"),
                            Exception("API error 2"),
                            mock_claude_response
                        ]
                        mock_anthropic.Anthropic.return_value = mock_client

                        generator = ContentGenerator()
                        content = generator.generate(sample_idea, max_retries=3)

                        assert content is not None
                        assert content.metadata['attempt'] == 3


class TestConvenienceFunctions:
    """Test module-level convenience functions"""

    def test_generate_content_function(self, mock_config, sample_idea, mock_claude_response):
        """Test generate_content convenience function"""
        with patch.object(ContentGenerator, '_load_config', return_value=mock_config):
            with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
                with patch('src.content.generator.ANTHROPIC_AVAILABLE', True):
                    with patch('src.content.generator.anthropic') as mock_anthropic:
                        mock_client = Mock()
                        mock_client.messages.create.return_value = mock_claude_response
                        mock_anthropic.Anthropic.return_value = mock_client

                        content = generate_content(sample_idea, platform='twitter')

                        assert content is not None
                        assert isinstance(content, GeneratedContent)
