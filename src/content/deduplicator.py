"""
Content Deduplicator Module for Digital Freeman
Prevents content repetition by checking semantic similarity with past posts
"""

import os
import yaml
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from collections import Counter

# OpenAI for embeddings
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.content.storage import ContentQueue, QueuedContent


class ContentDeduplicator:
    """
    Prevents content repetition through semantic similarity analysis

    Responsibilities:
    - Check semantic similarity with past posts using embeddings
    - Reject content if similarity > threshold (default 85%)
    - Enforce content diversity in the queue
    - Support multiple similarity methods (embeddings, keywords, both)
    - Cache embeddings to avoid redundant API calls
    """

    def __init__(self, config_path: str = "config/content_config.yaml"):
        """Initialize the deduplicator with configuration"""
        self.config = self._load_config(config_path)
        self.dedup_config = self.config.get('deduplication', {})
        self.similarity_config = self.dedup_config.get('similarity', {})
        self.diversity_config = self.dedup_config.get('diversity', {})
        self.embedding_config = self.dedup_config.get('embedding', {})

        # Deduplication settings
        self.enabled = self.dedup_config.get('enabled', True)
        self.method = self.similarity_config.get('method', 'embeddings')
        self.threshold = self.similarity_config.get('threshold', 0.85)
        self.lookback_posts = self.similarity_config.get('lookback_posts', 50)

        # Diversity settings
        self.min_topic_variety = self.diversity_config.get('min_topic_variety', 0.6)
        self.max_consecutive_similar = self.diversity_config.get('max_consecutive_similar', 2)

        # Embedding settings
        self.embedding_provider = self.embedding_config.get('provider', 'openai')
        self.embedding_model = self.embedding_config.get('model', 'text-embedding-3-small')

        # Initialize OpenAI client
        self._init_embedding_client()

        # Initialize content queue
        self.queue = ContentQueue(config_path=config_path)

        # Embedding cache to avoid redundant API calls
        self._embedding_cache: Dict[str, List[float]] = {}

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _init_embedding_client(self):
        """Initialize embedding API client"""
        self.embedding_client = None

        if self.embedding_provider == 'openai':
            if not OPENAI_AVAILABLE:
                raise RuntimeError("OpenAI library not installed. Run: pip install openai")

            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set in environment")

            self.embedding_client = openai.OpenAI(api_key=api_key)

    def is_duplicate(
        self,
        text: str,
        topic: Optional[str] = None,
        check_queue: bool = True
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Check if content is too similar to recent posts

        Args:
            text: Content text to check
            topic: Content topic (optional, used for keyword method)
            check_queue: Also check queued/scheduled content (not just posted)

        Returns:
            Tuple of (is_duplicate, max_similarity, most_similar_text)
        """
        if not self.enabled:
            return False, 0.0, None

        # Get recent posts to compare against
        recent_posts = self.queue.get_recent_posts(count=self.lookback_posts)

        # Optionally include queued/scheduled content
        if check_queue:
            queued = self.queue.get_queued()
            scheduled = self.queue.get_scheduled()
            recent_posts.extend(queued)
            recent_posts.extend(scheduled)

        if not recent_posts:
            return False, 0.0, None

        # Calculate similarity based on method
        max_similarity = 0.0
        most_similar_text = None

        for post in recent_posts:
            similarity = self._calculate_similarity(text, post.text, topic, post.topic)

            if similarity > max_similarity:
                max_similarity = similarity
                most_similar_text = post.text

        # Check if exceeds threshold
        is_duplicate = max_similarity > self.threshold

        return is_duplicate, max_similarity, most_similar_text

    def _calculate_similarity(
        self,
        text1: str,
        text2: str,
        topic1: Optional[str] = None,
        topic2: Optional[str] = None
    ) -> float:
        """
        Calculate similarity between two texts

        Args:
            text1: First text
            text2: Second text
            topic1: Topic of first text (optional)
            topic2: Topic of second text (optional)

        Returns:
# Memory-efficient implementation
            Similarity score (0-1, higher = more similar)
        """
        if self.method == 'embeddings':
            return self._embedding_similarity(text1, text2)
        elif self.method == 'keywords':
            return self._keyword_similarity(text1, text2, topic1, topic2)
        elif self.method == 'both':
            # Average of both methods
            emb_sim = self._embedding_similarity(text1, text2)
            key_sim = self._keyword_similarity(text1, text2, topic1, topic2)
            return (emb_sim + key_sim) / 2
        else:
            raise ValueError(f"Unknown similarity method: {self.method}")

    def _embedding_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity using embeddings

        Args:
            text1: First text
            text2: Second text

        Returns:
            Cosine similarity (0-1)
        """
        try:
            # Get embeddings for both texts
            emb1 = self._get_embedding(text1)
            emb2 = self._get_embedding(text2)

            # Calculate cosine similarity
            similarity = self._cosine_similarity(emb1, emb2)

            return similarity

        except Exception as e:
            print(f"Embedding similarity error: {e}")
            # Fallback to keyword similarity
            return self._keyword_similarity(text1, text2)

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text (with caching)

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Check cache first
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        # Get embedding from API
        if self.embedding_provider == 'openai' and self.embedding_client:
            try:
                response = self.embedding_client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )

                embedding = response.data[0].embedding

                # Cache it
                self._embedding_cache[text] = embedding

                return embedding

            except Exception as e:
                print(f"OpenAI embedding error: {e}")
                raise
        else:
            raise RuntimeError("No embedding provider available")

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        # Convert to numpy arrays
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)

        # Normalize to 0-1 range (cosine similarity can be -1 to 1)
        normalized = (similarity + 1) / 2

        return float(normalized)

    def _keyword_similarity(
        self,
        text1: str,
        text2: str,
        topic1: Optional[str] = None,
        topic2: Optional[str] = None
    ) -> float:
        """
        Calculate similarity based on keyword overlap

        Args:
            text1: First text
            text2: Second text
            topic1: Topic of first text (optional)
            topic2: Topic of second text (optional)

        Returns:
            Similarity score (0-1)
        """
        # Normalize texts
        t1 = text1.lower().strip()
        t2 = text2.lower().strip()

        # Exact match
        if t1 == t2:
            return 1.0

        # Extract words (simple tokenization)
        words1 = set(self._extract_keywords(t1))
        words2 = set(self._extract_keywords(t2))

        # Calculate Jaccard similarity
        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        jaccard = intersection / union if union > 0 else 0.0

        # Boost similarity if topics are the same
        if topic1 and topic2 and topic1.lower() == topic2.lower():
            jaccard = min(1.0, jaccard * 1.2)  # 20% boost

        return jaccard

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract meaningful keywords from text

        Args:
            text: Input text

        Returns:
            List of keywords
        """
        # Remove punctuation and split
        import re
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()

        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which',
            'who', 'when', 'where', 'why', 'how'
        }

        keywords = [w.lower() for w in words if w.lower() not in stop_words and len(w) > 2]

        return keywords

    def check_diversity(self) -> Tuple[bool, Dict]:
        """
        Check if queue has sufficient topic diversity

        Returns:
            Tuple of (meets_requirements, stats_dict)
        """
        queued = self.queue.get_queued()
        scheduled = self.queue.get_scheduled()
        all_content = queued + scheduled

        if not all_content:
            return True, {'reason': 'empty_queue'}

        # Check 1: Topic variety ratio
        topics = [c.topic for c in all_content]
        unique_topics = len(set(topics))
        total_topics = len(topics)
        topic_variety_ratio = unique_topics / total_topics if total_topics > 0 else 1.0

        # Check 2: Consecutive similar topics
        consecutive_similar = self._count_consecutive_similar(all_content)

        # Evaluate
        meets_variety = topic_variety_ratio >= self.min_topic_variety
        meets_consecutive = consecutive_similar <= self.max_consecutive_similar

        stats = {
            'topic_variety_ratio': topic_variety_ratio,
            'required_variety': self.min_topic_variety,
            'meets_variety': meets_variety,
            'max_consecutive_similar': consecutive_similar,
            'allowed_consecutive': self.max_consecutive_similar,
            'meets_consecutive': meets_consecutive,
            'total_content': total_topics,
            'unique_topics': unique_topics
        }

        meets_requirements = meets_variety and meets_consecutive

        return meets_requirements, stats

    def _count_consecutive_similar(self, content_list: List[QueuedContent]) -> int:
        """
        Count maximum consecutive posts with similar topics

        Args:
            content_list: List of content to check

        Returns:
            Maximum consecutive similar count
        """
        if len(content_list) < 2:
            return 0

        # Sort by scheduled time (or created time)
        sorted_content = sorted(
            content_list,
            key=lambda c: c.scheduled_for or c.created_at
        )

        max_consecutive = 0
        current_consecutive = 1

        for i in range(1, len(sorted_content)):
            prev_topic = sorted_content[i-1].topic
            curr_topic = sorted_content[i].topic

            # Check if topics are similar
            if self._topics_are_similar(prev_topic, curr_topic):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 1

        return max_consecutive

    def _topics_are_similar(self, topic1: str, topic2: str) -> bool:
        """
        Check if two topics are similar

        Args:
            topic1: First topic
            topic2: Second topic

        Returns:
            True if similar
        """
        # Normalize
        t1 = topic1.lower().strip()
        t2 = topic2.lower().strip()

        # Exact match
        if t1 == t2:
            return True

        # Check if one contains the other
        if t1 in t2 or t2 in t1:
            return True

        # Check word overlap
        words1 = set(t1.split())
        words2 = set(t2.split())
        overlap = len(words1 & words2)

        min_words = min(len(words1), len(words2))
        if min_words > 0 and overlap / min_words > 0.5:
            return True

        return False

    def validate_content(
        self,
        text: str,
        topic: str,
        check_queue: bool = True
    ) -> Tuple[bool, Dict]:
        """
        Full validation: check both duplication and diversity

        Args:
            text: Content text to validate
            topic: Content topic
            check_queue: Check against queued/scheduled content

        Returns:
            Tuple of (is_valid, details_dict)
        """
        # Check for duplicates
        is_dup, similarity, similar_text = self.is_duplicate(text, topic, check_queue)

        # Check diversity (only if not duplicate)
        diversity_ok, diversity_stats = self.check_diversity()

        # Determine if valid
        is_valid = not is_dup and diversity_ok

        details = {
            'is_duplicate': is_dup,
            'max_similarity': similarity,
            'similar_text': similar_text[:100] + '...' if similar_text and len(similar_text) > 100 else similar_text,
            'diversity_ok': diversity_ok,
            'diversity_stats': diversity_stats,
            'is_valid': is_valid
        }

        return is_valid, details

    def filter_duplicates(
        self,
        content_list: List[Tuple[str, str]]
    ) -> List[Tuple[str, str, bool, float]]:
        """
        Filter a list of content, marking duplicates

        Args:
            content_list: List of (text, topic) tuples

        Returns:
            List of (text, topic, is_duplicate, similarity) tuples
        """
        results = []

        for text, topic in content_list:
            is_dup, similarity, _ = self.is_duplicate(text, topic)
            results.append((text, topic, is_dup, similarity))

        return results

    def get_stats(self) -> Dict:
        """Get deduplication statistics"""
        diversity_ok, diversity_stats = self.check_diversity()

        return {
            'enabled': self.enabled,
            'method': self.method,
            'threshold': self.threshold,
            'lookback_posts': self.lookback_posts,
            'cache_size': len(self._embedding_cache),
            'diversity_ok': diversity_ok,
            'diversity_stats': diversity_stats
        }

    def clear_cache(self):
        """Clear embedding cache"""
        self._embedding_cache.clear()


# Convenience functions
def check_duplicate(text: str, topic: str = None) -> bool:
    """
    Quick function to check if content is duplicate

    Args:
        text: Content text
        topic: Content topic (optional)

    Returns:
        True if duplicate
    """
    dedup = ContentDeduplicator()
    is_dup, _, _ = dedup.is_duplicate(text, topic)
    return is_dup


def validate_content(text: str, topic: str) -> Tuple[bool, Dict]:
    """
    Quick function to validate content

    Args:
        text: Content text
        topic: Content topic

    Returns:
        Tuple of (is_valid, details)
    """
    dedup = ContentDeduplicator()
    return dedup.validate_content(text, topic)


if __name__ == "__main__":
    # Demo/testing functionality
    print("Digital Freeman - Content Deduplicator Module")
    print("=" * 50)

    try:
        # Check OpenAI API key
        has_openai = bool(os.getenv('OPENAI_API_KEY'))
        print(f"✓ OpenAI API: {'Available' if has_openai else 'Not configured'}")

        if not has_openai:
            print("\n⚠ Warning: OPENAI_API_KEY not found in environment")
            print("Set OPENAI_API_KEY to test embedding-based deduplication")
            print("\nDeduplicator class can still be imported.")
            print("It will fall back to keyword-based similarity.")

        # Initialize deduplicator (will work even without API key for keyword method)
        print("\nInitializing deduplicator...")
        dedup = ContentDeduplicator()
        print(f"✓ Deduplicator initialized")
        print(f"✓ Method: {dedup.method}")
        print(f"✓ Threshold: {dedup.threshold}")
        print(f"✓ Lookback: {dedup.lookback_posts} posts")
        print()

        # Test with sample content
        print("Testing duplicate detection:")
        test_text1 = "Wake up. You're living in a system designed to keep you distracted."
        test_topic1 = "Social manipulation and propaganda"

        test_text2 = "Wake up. The system wants you distracted and compliant."
        test_topic2 = "Social manipulation and propaganda"

        test_text3 = "AI will either liberate or enslave us. The choice is ours to make."
        test_topic3 = "AI and consciousness"

        # Check first text (should not be duplicate - nothing in queue yet)
        is_dup1, sim1, similar1 = dedup.is_duplicate(test_text1, test_topic1)
        print(f"✓ Text 1: is_duplicate={is_dup1}, similarity={sim1:.3f}")

        # Add first text to queue
        dedup.queue.add(test_text1, test_topic1, platform="twitter")
        print(f"✓ Added text 1 to queue")

        # Check second text (should be duplicate - very similar)
        is_dup2, sim2, similar2 = dedup.is_duplicate(test_text2, test_topic2)
        print(f"✓ Text 2: is_duplicate={is_dup2}, similarity={sim2:.3f}")
        if similar2:
            print(f"  Similar to: {similar2[:60]}...")

        # Check third text (should not be duplicate - different topic)
        is_dup3, sim3, similar3 = dedup.is_duplicate(test_text3, test_topic3)
        print(f"✓ Text 3: is_duplicate={is_dup3}, similarity={sim3:.3f}")
        print()

        # Test diversity check
        print("Testing diversity check:")
        diversity_ok, diversity_stats = dedup.check_diversity()
        print(f"✓ Diversity OK: {diversity_ok}")
        for key, value in diversity_stats.items():
            print(f"  {key}: {value}")
        print()

        # Full validation
        print("Testing full validation:")
        is_valid, details = dedup.validate_content(test_text3, test_topic3)
        print(f"✓ Content valid: {is_valid}")
        print(f"  Is duplicate: {details['is_duplicate']}")
        print(f"  Max similarity: {details['max_similarity']:.3f}")
        print(f"  Diversity OK: {details['diversity_ok']}")
        print()

        # Show stats
        stats = dedup.get_stats()
        print("Deduplicator stats:")
        for key, value in stats.items():
            if key != 'diversity_stats':
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
