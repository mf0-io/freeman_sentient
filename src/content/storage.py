"""
Content Storage/Queue Module for Digital Freeman
Manages the queue of generated content ready for posting
"""

import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import yaml


@dataclass
class QueuedContent:
    """Represents content stored in the queue"""
    id: str
    text: str
    topic: str
    platform: str
    status: str  # queued, scheduled, posted, failed
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    sentiment: Optional[str] = None  # philosophical, sarcastic, confrontational, supportive
    source: Optional[str] = None  # mission_alignment, philosophical_topics, etc.
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'id': self.id,
            'text': self.text,
            'topic': self.topic,
            'platform': self.platform,
            'status': self.status,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'scheduled_for': self.scheduled_for.isoformat() if isinstance(self.scheduled_for, datetime) else self.scheduled_for,
            'posted_at': self.posted_at.isoformat() if isinstance(self.posted_at, datetime) else self.posted_at,
            'sentiment': self.sentiment,
            'source': self.source,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'QueuedContent':
        """Create QueuedContent from dictionary"""
        # Parse datetime strings
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        scheduled_for = data.get('scheduled_for')
        if isinstance(scheduled_for, str):
            scheduled_for = datetime.fromisoformat(scheduled_for)

        posted_at = data.get('posted_at')
        if isinstance(posted_at, str):
            posted_at = datetime.fromisoformat(posted_at)

        return cls(
            id=data['id'],
            text=data['text'],
            topic=data['topic'],
            platform=data['platform'],
            status=data['status'],
            created_at=created_at,
            scheduled_for=scheduled_for,
            posted_at=posted_at,
            sentiment=data.get('sentiment'),
            source=data.get('source'),
            metadata=data.get('metadata', {})
        )


class ContentQueue:
    """
    Manages the content queue for scheduled posting

    Responsibilities:
    - Store generated content with metadata
    - Retrieve content for posting
    - Update content status (queued -> scheduled -> posted)
    - Maintain queue size within configured limits
    - Persist queue to JSON file (or SQLite for production)
    """

    def __init__(self, config_path: str = "config/content_config.yaml"):
        """Initialize the content queue"""
        self.config = self._load_config(config_path)
        self.queue_config = self.config.get('queue', {})
        self.storage_config = self.queue_config.get('storage', {})

        # Storage settings
        self.storage_type = self.storage_config.get('type', 'json')
        self.storage_path = Path(self.storage_config.get('path', 'data/content_queue.json'))

        # Queue size limits
        self.min_queued = self.queue_config.get('size', {}).get('min_queued', 3)
        self.max_queued = self.queue_config.get('size', {}).get('max_queued', 10)
        self.auto_refill = self.queue_config.get('auto_refill', True)

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing queue
        self.queue: List[QueuedContent] = self._load_queue()

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _load_queue(self) -> List[QueuedContent]:
        """Load queue from storage"""
        if self.storage_type == 'json':
            return self._load_from_json()
        elif self.storage_type == 'sqlite':
            # TODO: Implement SQLite support for production
            raise NotImplementedError("SQLite storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

    def _load_from_json(self) -> List[QueuedContent]:
        """Load queue from JSON file"""
        if not self.storage_path.exists():
            return []

        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
                return [QueuedContent.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error loading queue: {e}. Starting with empty queue.")
            return []

    def _save_queue(self) -> bool:
        """Save queue to storage"""
        if self.storage_type == 'json':
            return self._save_to_json()
        elif self.storage_type == 'sqlite':
            # TODO: Implement SQLite support
            raise NotImplementedError("SQLite storage not yet implemented")
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

    def _save_to_json(self) -> bool:
        """Save queue to JSON file"""
        try:
            data = [item.to_dict() for item in self.queue]
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return True
        except Exception as e:
            print(f"Error saving queue: {e}")
            return False

    def add(
        self,
        text: str,
        topic: str,
        platform: str = "twitter",
        sentiment: Optional[str] = None,
        source: Optional[str] = None,
        scheduled_for: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> QueuedContent:
        """
        Add content to the queue

        Args:
            text: The content text
            topic: Content topic
            platform: Target platform (twitter, telegram)
            sentiment: Tone/sentiment of content
            source: Source of content idea
            scheduled_for: When to post (None = to be scheduled)
            metadata: Additional metadata

        Returns:
            QueuedContent object
        """
        # Generate unique ID
        content_id = self._generate_id()

        # Create queued content
        content = QueuedContent(
            id=content_id,
            text=text,
            topic=topic,
            platform=platform,
            status='queued' if scheduled_for is None else 'scheduled',
            created_at=datetime.now(),
            scheduled_for=scheduled_for,
            sentiment=sentiment,
            source=source,
            metadata=metadata or {}
        )

        # Add to queue
        self.queue.append(content)

        # Save to storage
        self._save_queue()

        return content

    def get_by_id(self, content_id: str) -> Optional[QueuedContent]:
        """Get content by ID"""
        for content in self.queue:
            if content.id == content_id:
                return content
        return None

    def get_by_status(self, status: str) -> List[QueuedContent]:
        """Get all content with specified status"""
        return [c for c in self.queue if c.status == status]

    def get_queued(self) -> List[QueuedContent]:
        """Get all queued content (not yet scheduled)"""
        return self.get_by_status('queued')

    def get_scheduled(self) -> List[QueuedContent]:
        """Get all scheduled content"""
        return self.get_by_status('scheduled')

    def get_next_to_post(self) -> Optional[QueuedContent]:
        """Get the next content scheduled for posting"""
        scheduled = self.get_scheduled()
        if not scheduled:
            return None

        # Find earliest scheduled content
        scheduled.sort(key=lambda c: c.scheduled_for or datetime.max)
        return scheduled[0] if scheduled else None

    def update_status(
        self,
        content_id: str,
        status: str,
        scheduled_for: Optional[datetime] = None,
        posted_at: Optional[datetime] = None
    ) -> bool:
        """
        Update content status

        Args:
            content_id: ID of content to update
            status: New status (queued, scheduled, posted, failed)
            scheduled_for: Schedule time (optional)
            posted_at: Posted time (optional)

        Returns:
            True if updated successfully
        """
        content = self.get_by_id(content_id)
        if not content:
            return False

        content.status = status
        if scheduled_for:
            content.scheduled_for = scheduled_for
        if posted_at:
            content.posted_at = posted_at

        return self._save_queue()

    def mark_posted(self, content_id: str) -> bool:
        """Mark content as posted"""
        return self.update_status(
            content_id,
            status='posted',
            posted_at=datetime.now()
        )

    def mark_failed(self, content_id: str) -> bool:
        """Mark content as failed"""
        return self.update_status(content_id, status='failed')

    def remove(self, content_id: str) -> bool:
        """Remove content from queue"""
        content = self.get_by_id(content_id)
        if not content:
            return False

        self.queue.remove(content)
        return self._save_queue()

    def clear_posted(self) -> int:
        """Remove all posted content from queue"""
        initial_count = len(self.queue)
        self.queue = [c for c in self.queue if c.status != 'posted']
        self._save_queue()
        return initial_count - len(self.queue)

    def size(self) -> int:
        """Get current queue size"""
        return len(self.queue)

    def is_full(self) -> bool:
        """Check if queue is at max capacity"""
        return self.size() >= self.max_queued

    def needs_refill(self) -> bool:
        """Check if queue needs more content"""
        queued_count = len(self.get_queued()) + len(self.get_scheduled())
        return queued_count < self.min_queued

    def get_stats(self) -> Dict:
        """Get queue statistics"""
        return {
            'total': len(self.queue),
            'queued': len(self.get_queued()),
            'scheduled': len(self.get_scheduled()),
            'posted': len(self.get_by_status('posted')),
            'failed': len(self.get_by_status('failed')),
            'needs_refill': self.needs_refill(),
            'is_full': self.is_full()
        }

    def get_topics_in_queue(self) -> List[str]:
        """Get list of topics currently in queue"""
        topics = []
        for content in self.queue:
            if content.status in ['queued', 'scheduled']:
                topics.append(content.topic)
        return topics

    def get_recent_posts(self, count: int = 50) -> List[QueuedContent]:
        """Get recent posted content for anti-repetition checking"""
        posted = self.get_by_status('posted')
        posted.sort(key=lambda c: c.posted_at or datetime.min, reverse=True)
        return posted[:count]

    def _generate_id(self) -> str:
        """Generate unique ID for content"""
        import uuid
        return str(uuid.uuid4())


# Convenience functions
def add_to_queue(
    text: str,
    topic: str,
    platform: str = "twitter",
    **kwargs
) -> QueuedContent:
    """
    Quick function to add content to queue

    Args:
        text: Content text
        topic: Content topic
        platform: Target platform
        **kwargs: Additional arguments (sentiment, source, metadata, etc.)

    Returns:
        QueuedContent object
    """
    queue = ContentQueue()
    return queue.add(text, topic, platform, **kwargs)


def get_queue_stats() -> Dict:
    """Get current queue statistics"""
    queue = ContentQueue()
    return queue.get_stats()


if __name__ == "__main__":
    # Demo/testing functionality
    print("Digital Freeman - Content Storage/Queue Module")
    print("=" * 50)

    try:
        # Initialize queue
        queue = ContentQueue()
        print(f"✓ Queue initialized")
        print(f"✓ Storage: {queue.storage_type} at {queue.storage_path}")
        print(f"✓ Size limits: min={queue.min_queued}, max={queue.max_queued}")
        print()

        # Show current stats
        stats = queue.get_stats()
        print("Current queue stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

        # Test adding content
        print("Testing add operation:")
        test_content = queue.add(
            text="Test tweet about consciousness and AI",
            topic="AI and consciousness",
            platform="twitter",
            sentiment="philosophical",
            source="test",
            metadata={'test': True}
        )
        print(f"✓ Added content: {test_content.id}")
        print(f"  Text: {test_content.text}")
        print(f"  Status: {test_content.status}")
        print()

        # Test retrieval
        print("Testing retrieval:")
        retrieved = queue.get_by_id(test_content.id)
        print(f"✓ Retrieved by ID: {retrieved.id if retrieved else 'None'}")

        queued = queue.get_queued()
        print(f"✓ Queued items: {len(queued)}")
        print()

        # Test status update
        print("Testing status update:")
        success = queue.update_status(
            test_content.id,
            status='scheduled',
            scheduled_for=datetime.now()
        )
        print(f"✓ Status updated: {success}")
        print()

        # Show updated stats
        stats = queue.get_stats()
        print("Updated queue stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

        # Test cleanup
        print("Testing cleanup:")
        queue.mark_posted(test_content.id)
        removed = queue.clear_posted()
        print(f"✓ Cleared {removed} posted items")
        print()

        # Final stats
        stats = queue.get_stats()
        print("Final queue stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
