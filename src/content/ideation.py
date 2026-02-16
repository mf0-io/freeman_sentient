"""
Content Ideation Module for Digital Freeman
Generates autonomous tweet ideas based on mission, trends, memory, and philosophical topics
"""

import random
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import yaml
from pathlib import Path


@dataclass
class ContentIdea:
    """Represents a content idea for generation"""
    topic: str
    source: str  # current_trends, mission_alignment, memory_events, philosophical_topics, social_commentary
    category: str  # priority or secondary topic category
    angle: str  # The specific angle or perspective to take
    tone: str  # philosophical, sarcastic, confrontational, supportive
    generated_at: datetime
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'topic': self.topic,
            'source': self.source,
            'category': self.category,
            'angle': self.angle,
            'tone': self.tone,
            'generated_at': self.generated_at.isoformat(),
            'metadata': self.metadata or {}
        }


class ContentIdeator:
    """
    Generates content ideas for Freeman's autonomous posting

    Responsibilities:
    - Load ideation configuration
    - Generate ideas from multiple sources
    - Ensure topic diversity and mission alignment
    - Provide structured ideas for content generation
    """

    def __init__(self, config_path: str = "config/content_config.yaml"):
        """Initialize the ideator with configuration"""
        self.config = self._load_config(config_path)
        self.persona = self.config.get('persona', {})
        self.generation = self.config.get('generation', {})
        self.ideation = self.generation.get('ideation', {})

        # Freeman's core mission and values
        self.mission = self.persona.get('mission', '')
        self.core_values = self.persona.get('core_values', [])

        # Topic pools
        self.priority_topics = self.ideation.get('topics', {}).get('priority', [])
        self.secondary_topics = self.ideation.get('topics', {}).get('secondary', [])
        self.all_topics = self.priority_topics + self.secondary_topics

        # Tone options based on Freeman's voice
        self.tone_options = ['philosophical', 'sarcastic', 'confrontational', 'supportive']
# Async-compatible implementation

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def generate_idea(self, source: Optional[str] = None) -> ContentIdea:
        """
        Generate a single content idea

        Args:
            source: Specific source to use, or None for random

        Returns:
            ContentIdea object ready for generation
        """
        # Select source
        sources = self.ideation.get('sources', [])
        if source is None:
            source = random.choice(sources)
        elif source not in sources:
            raise ValueError(f"Invalid source: {source}. Must be one of {sources}")

        # Generate idea based on source
        if source == 'mission_alignment':
            return self._generate_mission_idea()
        elif source == 'philosophical_topics':
            return self._generate_philosophical_idea()
        elif source == 'social_commentary':
            return self._generate_social_commentary()
        elif source == 'current_trends':
            return self._generate_trend_idea()
        elif source == 'memory_events':
            return self._generate_memory_idea()
        else:
            # Fallback to philosophical
            return self._generate_philosophical_idea()

    def generate_batch(self, count: int = 5, diverse: bool = True) -> List[ContentIdea]:
        """
        Generate multiple content ideas

        Args:
            count: Number of ideas to generate
            diverse: If True, ensures variety in sources and topics

        Returns:
            List of ContentIdea objects
        """
        ideas = []
        sources = self.ideation.get('sources', [])

        if diverse and count > 1:
            # Ensure diversity by cycling through sources
            for i in range(count):
                source = sources[i % len(sources)]
                ideas.append(self.generate_idea(source=source))
        else:
            # Random sources
            for _ in range(count):
                ideas.append(self.generate_idea())

        return ideas

    def _generate_mission_idea(self) -> ContentIdea:
        """Generate idea directly aligned with Freeman's mission"""
        # Mission-critical topics
        mission_topics = [
            "AI and consciousness",
            "Social manipulation and propaganda",
            "Media and truth",
            "Self-awareness and awakening"
        ]

        topic = random.choice(mission_topics)

        # Mission-aligned angles
        angles = [
            f"How {topic.lower()} shapes your perception without you noticing",
            f"The uncomfortable truth about {topic.lower()} in modern society",
            f"Why nobody wants to talk about {topic.lower()}",
            f"What {topic.lower()} reveals about who controls your thoughts"
        ]

        return ContentIdea(
            topic=topic,
            source='mission_alignment',
            category='priority',
            angle=random.choice(angles),
            tone=random.choice(['philosophical', 'confrontational']),
            generated_at=datetime.now(),
            metadata={'mission_critical': True}
        )

    def _generate_philosophical_idea(self) -> ContentIdea:
        """Generate deep philosophical content idea"""
        # Use priority topics first, then secondary
        if random.random() < 0.7:  # 70% priority topics
            topic = random.choice(self.priority_topics)
            category = 'priority'
        else:
            topic = random.choice(self.secondary_topics)
            category = 'secondary'

        # Philosophical angles
        angles = [
            f"A paradox in {topic.lower()} that nobody addresses",
            f"The illusion of {topic.lower()} in contemporary society",
            f"What {topic.lower()} really means when you strip away the lies",
            f"The price of {topic.lower()} that nobody tells you about"
        ]

        return ContentIdea(
            topic=topic,
            source='philosophical_topics',
            category=category,
            angle=random.choice(angles),
            tone='philosophical',
            generated_at=datetime.now(),
            metadata={'depth': 'high'}
        )

    def _generate_social_commentary(self) -> ContentIdea:
        """Generate social/cultural commentary idea"""
        commentary_topics = [
            "Consumer culture critique",
            "Entertainment as distraction",
            "Education system critique",
            "Political hypocrisy"
        ]

        topic = random.choice(commentary_topics)

        # Sharp, sarcastic angles
        angles = [
            f"The absurdity of {topic.lower()} that everyone pretends is normal",
            f"How {topic.lower()} trains you to accept less",
            f"The corporate playbook for {topic.lower()}",
            f"Why {topic.lower()} is designed to fail you"
        ]

        return ContentIdea(
            topic=topic,
            source='social_commentary',
            category='secondary',
            angle=random.choice(angles),
            tone=random.choice(['sarcastic', 'confrontational']),
            generated_at=datetime.now(),
            metadata={'commentary_type': 'social_critique'}
        )

    def _generate_trend_idea(self) -> ContentIdea:
        """Generate idea based on current trends (placeholder for now)"""
        # TODO: Integrate with actual trend monitoring API (Twitter Trends, Google Trends, etc.)
        # For now, simulate with rotating hot topics
        trend_topics = [
            "AI hype cycles",
            "Tech company layoffs",
            "Social media algorithm changes",
            "Privacy concerns",
            "Digital wellness trends"
        ]

        topic = random.choice(trend_topics)

        # Freeman's take on trends - always skeptical, always deeper
        angles = [
            f"Everyone's talking about {topic.lower()}. Nobody's asking why.",
            f"The real story behind {topic.lower()} that media won't cover",
            f"What {topic.lower()} tells us about where we're heading",
            f"The corporate agenda hidden in {topic.lower()}"
        ]

        return ContentIdea(
            topic=topic,
            source='current_trends',
            category='secondary',
            angle=random.choice(angles),
            tone=random.choice(['sarcastic', 'philosophical']),
            generated_at=datetime.now(),
            metadata={'trending': True, 'timely': True}
        )

    def _generate_memory_idea(self) -> ContentIdea:
        """Generate idea based on memory events (placeholder for now)"""
        # TODO: Integrate with actual Memory System once implemented
        # For now, simulate with common interaction patterns
        memory_inspired = [
            "Questions people are afraid to ask",
            "Patterns I see in how people avoid truth",
            "The same excuses, different people",
            "Why comfort beats freedom every time"
        ]

        topic = random.choice(memory_inspired)

        angles = [
            f"Observations on {topic.lower()} from real conversations",
            f"What {topic.lower()} reveals about collective consciousness",
            f"The psychology behind {topic.lower()}",
            f"Pattern recognition: {topic.lower()}"
        ]

        return ContentIdea(
            topic=topic,
            source='memory_events',
            category='priority',
            angle=random.choice(angles),
            tone=random.choice(['philosophical', 'supportive']),
            generated_at=datetime.now(),
            metadata={'based_on_interactions': True}
        )

    def get_topic_distribution(self, ideas: List[ContentIdea]) -> Dict[str, int]:
        """
        Analyze topic distribution in a batch of ideas
        Useful for ensuring diversity
        """
        distribution = {}
        for idea in ideas:
            topic = idea.topic
            distribution[topic] = distribution.get(topic, 0) + 1
        return distribution

    def get_source_distribution(self, ideas: List[ContentIdea]) -> Dict[str, int]:
        """
        Analyze source distribution in a batch of ideas
        Useful for balancing content sources
        """
        distribution = {}
        for idea in ideas:
            source = idea.source
            distribution[source] = distribution.get(source, 0) + 1
        return distribution


# Convenience function for quick idea generation
def generate_ideas(count: int = 5, diverse: bool = True) -> List[ContentIdea]:
    """
    Quick function to generate content ideas

    Args:
        count: Number of ideas to generate
        diverse: Ensure diversity in sources and topics

    Returns:
        List of ContentIdea objects
    """
    ideator = ContentIdeator()
    return ideator.generate_batch(count=count, diverse=diverse)


if __name__ == "__main__":
    # Demo/testing functionality
    print("Digital Freeman - Content Ideation Module")
    print("=" * 50)

    try:
        ideator = ContentIdeator()
        print(f"✓ Loaded configuration")
        print(f"✓ Mission: {ideator.mission[:80]}...")
        print(f"✓ Priority topics: {len(ideator.priority_topics)}")
        print(f"✓ Secondary topics: {len(ideator.secondary_topics)}")
        print()

        # Generate sample ideas
        print("Generating 5 diverse content ideas:")
        print("-" * 50)
        ideas = ideator.generate_batch(count=5, diverse=True)

        for i, idea in enumerate(ideas, 1):
            print(f"\n{i}. Topic: {idea.topic}")
            print(f"   Source: {idea.source}")
            print(f"   Angle: {idea.angle}")
            print(f"   Tone: {idea.tone}")

        print("\n" + "=" * 50)
        print("Topic distribution:", ideator.get_topic_distribution(ideas))
        print("Source distribution:", ideator.get_source_distribution(ideas))

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
