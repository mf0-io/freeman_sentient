"""
Tests for SentimentAnalyzer

Tests sentiment analysis functionality including text sentiment scoring,
conversation sentiment aggregation, and classification.
"""

import pytest
from datetime import datetime, timedelta
from src.analytics.sentiment_analyzer import SentimentAnalyzer
from config.analytics_config import SentimentCategory


class TestSentimentScoring:
    """Tests for sentiment scoring and classification"""

    def test_sentiment_scoring(self):
        """Test sentiment scoring with various text inputs"""
        analyzer = SentimentAnalyzer()

        # Test 1: Very positive sentiment
        result = analyzer.analyze("This is absolutely amazing and wonderful!")
        assert result.score > 0.6, "Expected very positive score"
        assert result.category == SentimentCategory.VERY_POSITIVE
        assert result.confidence > 0.0, "Expected confidence > 0"

        # Test 2: Positive sentiment
        result = analyzer.analyze("This is good and helpful.")
        assert 0.2 <= result.score < 0.6, "Expected positive score"
        assert result.category == SentimentCategory.POSITIVE

        # Test 3: Neutral sentiment
        result = analyzer.analyze("The weather is typical for this time of year.")
        assert -0.2 <= result.score <= 0.2, "Expected neutral score"
        assert result.category == SentimentCategory.NEUTRAL

        # Test 4: Negative sentiment
        result = analyzer.analyze("This is bad and disappointing.")
        assert -0.6 <= result.score < -0.2, "Expected negative score"
        assert result.category == SentimentCategory.NEGATIVE

        # Test 5: Very negative sentiment
        result = analyzer.analyze("This is absolutely terrible, awful, and horrible!")
        assert result.score < -0.6, "Expected very negative score"
        assert result.category == SentimentCategory.VERY_NEGATIVE

    def test_sentiment_with_intensifiers(self):
        """Test that intensifiers amplify sentiment"""
        analyzer = SentimentAnalyzer()

        # Without intensifier
        result1 = analyzer.analyze("This is good.")

        # With intensifier
        result2 = analyzer.analyze("This is very good.")

        assert result2.score > result1.score, "Expected intensifier to increase positive sentiment"

    def test_sentiment_with_negation(self):
        """Test that negation reverses sentiment"""
        analyzer = SentimentAnalyzer()

        # Positive sentiment
        result1 = analyzer.analyze("This is good.")

        # Negated positive (becomes negative)
        result2 = analyzer.analyze("This is not good.")

        assert result2.score < result1.score, "Expected negation to reverse sentiment"
        assert result2.score < 0, "Expected negative score with negation"

    def test_conversation_sentiment_scoring(self):
        """Test conversation-level sentiment aggregation"""
        analyzer = SentimentAnalyzer()

        # Scenario 1: Uniformly positive conversation
        messages_positive = [
            "Hello! Great to meet you!",
            "This is wonderful!",
            "I love this so much!",
        ]

        result = analyzer.analyze_conversation(
            messages=messages_positive,
            conversation_id="conv1",
            user_id="user1",
        )

        assert result.score > 0.2, "Expected positive conversation score"
        assert result.category in [SentimentCategory.POSITIVE, SentimentCategory.VERY_POSITIVE]
        assert "conversation_id" in result.metadata
        assert result.metadata["conversation_id"] == "conv1"
        assert "message_count" in result.metadata
        assert result.metadata["message_count"] == 3

        # Scenario 2: Mixed sentiment conversation
        messages_mixed = [
            "This is great!",
            "But there are some problems.",
            "Overall it's okay.",
        ]

        result = analyzer.analyze_conversation(
            messages=messages_mixed,
            conversation_id="conv2",
            user_id="user1",
        )

        # Mixed should trend toward neutral
        assert -0.3 <= result.score <= 0.3, "Expected neutral-ish score for mixed conversation"

        # Scenario 3: Negative conversation
        messages_negative = [
            "This is terrible.",
            "I'm very disappointed.",
            "Everything is bad.",
        ]

        result = analyzer.analyze_conversation(
            messages=messages_negative,
            conversation_id="conv3",
            user_id="user2",
        )

        assert result.score < -0.2, "Expected negative conversation score"
        assert result.category in [SentimentCategory.NEGATIVE, SentimentCategory.VERY_NEGATIVE]

    def test_conversation_sentiment_empty(self):
        """Test conversation sentiment with empty message list"""
        analyzer = SentimentAnalyzer()

        result = analyzer.analyze_conversation(
            messages=[],
            conversation_id="empty_conv",
        )

        assert result.score == 0.0, "Expected neutral score for empty conversation"
        assert result.category == SentimentCategory.NEUTRAL
        assert result.metadata["message_count"] == 0

    def test_conversation_sentiment_aggregation(self):
        """Test that conversation sentiment properly aggregates individual message sentiments"""
        analyzer = SentimentAnalyzer()

        # Create a conversation with 5 positive and 5 negative messages
        messages = [
            "This is great!",
            "This is terrible.",
            "I love this!",
            "I hate this.",
            "Amazing work!",
            "Awful quality.",
            "Perfect!",
            "Disappointing.",
            "Excellent!",
            "Poor experience.",
        ]

        result = analyzer.analyze_conversation(
            messages=messages,
            conversation_id="balanced_conv",
        )

        # With equal positive and negative, should be close to neutral
        assert -0.3 <= result.score <= 0.3, "Expected neutral score for balanced conversation"
        assert result.metadata["message_count"] == 10

    def test_conversation_sentiment_with_timestamps(self):
        """Test that conversation sentiment can handle timestamps"""
        analyzer = SentimentAnalyzer()
        now = datetime.now()

        messages = [
            "This is great!",
            "I'm happy with this.",
        ]

        result = analyzer.analyze_conversation(
            messages=messages,
            conversation_id="timed_conv",
            user_id="user1",
            timestamp=now,
        )

        assert result.timestamp == now, "Expected provided timestamp to be used"
        assert result.score > 0, "Expected positive score"

    def test_conversation_sentiment_metadata(self):
        """Test that conversation sentiment includes proper metadata"""
        analyzer = SentimentAnalyzer()

        messages = [
            "Message 1",
            "Message 2",
            "Message 3",
        ]

        custom_metadata = {"platform": "telegram", "channel": "general"}

        result = analyzer.analyze_conversation(
            messages=messages,
            conversation_id="meta_conv",
            user_id="user1",
            metadata=custom_metadata,
        )

        # Should include both custom metadata and conversation-specific metadata
        assert "conversation_id" in result.metadata
        assert "message_count" in result.metadata
        assert "platform" in result.metadata
        assert "channel" in result.metadata
        assert result.metadata["platform"] == "telegram"


class TestBatchAnalysis:
    """Tests for batch sentiment analysis"""

    def test_batch_analysis(self):
        """Test analyzing multiple texts at once"""
        analyzer = SentimentAnalyzer()

        texts = [
            "This is great!",
            "This is terrible.",
            "This is okay.",
        ]

        results = analyzer.analyze_batch(texts, user_id="user1")

        assert len(results) == 3, "Expected 3 results"
        assert results[0].score > 0, "Expected positive score for first text"
        assert results[1].score < 0, "Expected negative score for second text"
        assert all(r.user_id == "user1" for r in results), "Expected all results to have user_id"

    def test_average_sentiment(self):
        """Test calculating average sentiment from multiple results"""
        analyzer = SentimentAnalyzer()

        texts = [
            "This is great!",  # Positive
            "This is wonderful!",  # Positive
            "This is good.",  # Positive
        ]

        results = analyzer.analyze_batch(texts)
        average = analyzer.get_average_sentiment(results)

        assert average > 0, "Expected positive average sentiment"

    def test_average_sentiment_empty(self):
        """Test average sentiment with empty list"""
        analyzer = SentimentAnalyzer()

        average = analyzer.get_average_sentiment([])

        assert average == 0.0, "Expected 0.0 for empty results list"
