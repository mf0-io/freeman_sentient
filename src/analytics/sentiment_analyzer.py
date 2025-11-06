"""
Sentiment Analyzer

Analyzes text sentiment to determine emotional tone of conversations and interactions.
Provides basic rule-based sentiment detection that can be extended with ML models.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
import re

from .models import SentimentResult
from config.analytics_config import SentimentCategory, classify_sentiment


class SentimentAnalyzer:
    """
    Analyzes sentiment of text to classify emotional tone.

    Provides basic rule-based sentiment detection using keyword analysis.
    Can be extended to integrate with ML models or external sentiment APIs.

    Attributes:
        positive_words: Set of words indicating positive sentiment
        negative_words: Set of words indicating negative sentiment
        intensifiers: Words that amplify sentiment
        negations: Words that reverse sentiment
    """

    def __init__(self):
        """Initialize the SentimentAnalyzer with keyword dictionaries"""
        # Positive sentiment keywords
        self.positive_words = {
            "good", "great", "excellent", "amazing", "wonderful", "fantastic",
            "love", "like", "enjoy", "happy", "joy", "pleased", "awesome",
            "brilliant", "perfect", "beautiful", "best", "better", "nice",
            "glad", "delighted", "excited", "thanks", "thank", "appreciate",
            "helpful", "useful", "impressive", "outstanding", "superb",
        }

        # Negative sentiment keywords
        self.negative_words = {
            "bad", "terrible", "awful", "horrible", "poor", "worst", "worse",
            "hate", "dislike", "sad", "angry", "upset", "disappointed",
            "frustrating", "annoying", "useless", "pointless", "waste",
            "boring", "dull", "confusing", "complicated", "difficult",
            "problem", "issue", "error", "fail", "failed", "wrong",
        }

        # Intensifiers that amplify sentiment
        self.intensifiers = {
            "very", "really", "extremely", "absolutely", "incredibly",
            "totally", "completely", "utterly", "so", "quite",
        }

        # Negation words that reverse sentiment
        self.negations = {
            "not", "no", "never", "neither", "nobody", "nothing",
            "nowhere", "none", "hardly", "scarcely", "barely",
        }

    def analyze(
        self,
        text: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> SentimentResult:
        """
        Analyze the sentiment of a text.

        Performs rule-based sentiment analysis using keyword matching,
        intensifiers, and negation detection.

        Args:
            text: The text to analyze
            user_id: Optional user ID for user-specific sentiment tracking
            metadata: Additional context about the text
            timestamp: Optional timestamp (defaults to now)

        Returns:
            SentimentResult with score, category, and confidence
        """
        # Normalize text
        normalized_text = text.lower()
        words = re.findall(r'\b\w+\b', normalized_text)

        # Calculate sentiment score
        score, confidence = self._calculate_score(words)

        # Classify into category
        category = classify_sentiment(score)

        return SentimentResult(
            score=score,
            category=category,
            text=text,
            timestamp=timestamp or datetime.now(),
            confidence=confidence,
            user_id=user_id,
            metadata=metadata or {},
        )

    def _calculate_score(self, words: List[str]) -> tuple[float, float]:
        """
        Calculate sentiment score from words.

        Uses keyword matching with intensifiers and negation handling.

        Args:
            words: List of words from normalized text

        Returns:
            Tuple of (score, confidence) where score is -1.0 to 1.0
            and confidence is 0.0 to 1.0
        """
        if not words:
            return 0.0, 1.0

        # Use weighted scoring where each word contributes less
        # This prevents quick saturation to 1.0 or -1.0
        positive_score = 0.0
        negative_score = 0.0
        intensifier_multiplier = 1.0
        pending_intensifier = False

        # Track if we're in a negation context
        negation_active = False

        for i, word in enumerate(words):
            # Check for intensifiers
            if word in self.intensifiers:
                intensifier_multiplier = 1.8
                pending_intensifier = True
                continue

            # Check for negations
            if word in self.negations:
                negation_active = True
                continue

            # Check sentiment
            is_positive = word in self.positive_words
            is_negative = word in self.negative_words

            # Apply negation (flip sentiment)
            if negation_active:
                is_positive, is_negative = is_negative, is_positive
                negation_active = False

            # Add sentiment with intensifier (base weight is 0.35 per word)
            base_weight = 0.35
            if is_positive:
                positive_score += base_weight * intensifier_multiplier
                pending_intensifier = False
                intensifier_multiplier = 1.0
            elif is_negative:
                negative_score += base_weight * intensifier_multiplier
                pending_intensifier = False
                intensifier_multiplier = 1.0

        # Calculate net score
        net_score = positive_score - negative_score

        # Normalize to -1.0 to 1.0 range with minimal damping
        score = max(-1.0, min(1.0, net_score * 0.85))

        # Calculate confidence based on number of sentiment words found
        sentiment_count = int((positive_score + negative_score) / 0.3)  # Approximate count
        total_words = len(words)
        sentiment_word_ratio = sentiment_count / total_words if total_words > 0 else 0
        confidence = min(1.0, sentiment_word_ratio * 2 + 0.2)  # Base confidence of 0.2

        return score, confidence

    def analyze_conversation(
        self,
        messages: List[str],
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> SentimentResult:
        """
        Analyze sentiment for an entire conversation.

        Analyzes each message individually and aggregates the results
        to provide an overall conversation sentiment score.

        Args:
            messages: List of message texts in the conversation
            conversation_id: Optional conversation identifier
            user_id: Optional user ID for the conversation
            metadata: Additional context about the conversation
            timestamp: Optional timestamp (defaults to now)

        Returns:
            SentimentResult with aggregated conversation sentiment
        """
        # Handle empty conversation
        if not messages:
            conversation_metadata = metadata.copy() if metadata else {}
            conversation_metadata.update({
                "conversation_id": conversation_id,
                "message_count": 0,
            })
            return SentimentResult(
                score=0.0,
                category=SentimentCategory.NEUTRAL,
                text="",
                timestamp=timestamp or datetime.now(),
                confidence=1.0,
                user_id=user_id,
                metadata=conversation_metadata,
            )

        # Analyze each message
        message_results = []
        for message in messages:
            result = self.analyze(text=message, user_id=user_id, timestamp=timestamp)
            message_results.append(result)

        # Aggregate sentiment scores
        average_score = self.get_average_sentiment(message_results)

        # Calculate overall confidence (average of individual confidences)
        average_confidence = sum(r.confidence for r in message_results) / len(message_results)

        # Classify the aggregated sentiment
        category = classify_sentiment(average_score)

        # Build conversation metadata
        conversation_metadata = metadata.copy() if metadata else {}
        conversation_metadata.update({
            "conversation_id": conversation_id,
            "message_count": len(messages),
        })

        # Combine all message texts for the result text field
        combined_text = " ".join(messages)

        return SentimentResult(
            score=average_score,
            category=category,
            text=combined_text,
            timestamp=timestamp or datetime.now(),
            confidence=average_confidence,
            user_id=user_id,
            metadata=conversation_metadata,
        )

    def analyze_batch(
        self,
        texts: List[str],
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[SentimentResult]:
        """
        Analyze sentiment for multiple texts.

        Args:
            texts: List of texts to analyze
            user_id: Optional user ID for all texts
            metadata: Optional metadata for all texts

        Returns:
            List of SentimentResult objects
        """
        return [
            self.analyze(text, user_id=user_id, metadata=metadata)
            for text in texts
        ]

    def get_average_sentiment(
        self,
        results: List[SentimentResult],
    ) -> float:
        """
        Calculate average sentiment score from multiple results.

        Args:
            results: List of SentimentResult objects

        Returns:
            Average sentiment score or 0.0 if no results
        """
        if not results:
            return 0.0

        total_score = sum(result.score for result in results)
        return total_score / len(results)


__all__ = ["SentimentAnalyzer"]
