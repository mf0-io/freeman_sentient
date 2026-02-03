"""
Content Scheduler Module for Digital Freeman
Schedules posts at optimal times while avoiding posting too frequently and spacing out similar topics
"""

import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import yaml

from src.content.storage import ContentQueue, QueuedContent


class ContentScheduler:
    """
    Schedules content for posting at optimal times

    Responsibilities:
    - Schedule posts at optimal times (morning, afternoon, evening)
    - Avoid posting too frequently (respect min_interval_hours)
    - Space out similar topics (min_hours_between_similar)
    - Respect time windows (only post during acceptable hours)
    - Update content status from 'queued' to 'scheduled'
    """

    def __init__(self, config_path: str = "config/content_config.yaml"):
        """Initialize the scheduler with configuration"""
        self.config = self._load_config(config_path)
        self.scheduling_config = self.config.get('scheduling', {})
        self.frequency_config = self.scheduling_config.get('frequency', {})
        self.topic_spacing_config = self.scheduling_config.get('topic_spacing', {})

        # Frequency settings
        self.min_interval_hours = self.frequency_config.get('min_interval_hours', 4)
        self.max_interval_hours = self.frequency_config.get('max_interval_hours', 12)
        self.posts_per_day = self.frequency_config.get('posts_per_day', 3)

        # Optimal posting times (UTC, 24h format)
        self.optimal_times = self.scheduling_config.get('optimal_times', ['08:00', '14:00', '20:00'])

        # Time windows
        self.time_windows = self.scheduling_config.get('time_windows', [])

        # Topic spacing
        self.topic_spacing_enabled = self.topic_spacing_config.get('enabled', True)
        self.min_hours_between_similar = self.topic_spacing_config.get('min_hours_between_similar', 24)

        # Initialize content queue
        self.queue = ContentQueue(config_path=config_path)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def schedule_content(self, content_id: str) -> Optional[datetime]:
        """
        Schedule a specific content item for posting

        Args:
            content_id: ID of content to schedule

        Returns:
            Scheduled datetime if successful, None otherwise
        """
        content = self.queue.get_by_id(content_id)
        if not content:
            return None

        # Calculate optimal schedule time
        schedule_time = self._calculate_next_slot(content)

        if schedule_time:
            # Update content status
            self.queue.update_status(
                content_id,
                status='scheduled',
                scheduled_for=schedule_time
            )

        return schedule_time

    def schedule_all_queued(self) -> List[Dict]:
        """
        Schedule all queued content

        Returns:
            List of dicts with content_id and scheduled_for
        """
        queued_content = self.queue.get_queued()
        results = []

        for content in queued_content:
            schedule_time = self.schedule_content(content.id)
            if schedule_time:
                results.append({
                    'content_id': content.id,
                    'topic': content.topic,
                    'scheduled_for': schedule_time
                })

        return results

    def _calculate_next_slot(self, content: QueuedContent) -> Optional[datetime]:
        """
        Calculate the next available time slot for posting

        Args:
            content: QueuedContent object to schedule

        Returns:
            datetime for next available slot
        """
        now = datetime.now()

        # Get all currently scheduled posts
        scheduled_posts = self.queue.get_scheduled()
        scheduled_times = sorted([p.scheduled_for for p in scheduled_posts if p.scheduled_for])

        # Start looking from now
        candidate_time = now

        # Try to find a slot within next 7 days
        max_attempts = 100
        attempts = 0

        while attempts < max_attempts:
            # Find next optimal time
            candidate_time = self._get_next_optimal_time(candidate_time)

            # Check if this slot is valid
            if self._is_valid_slot(candidate_time, content, scheduled_times):
                return candidate_time

            # Move to next candidate (add small increment to avoid infinite loop)
            candidate_time = candidate_time + timedelta(hours=1)
            attempts += 1

        # Fallback: schedule far in the future if no slot found
        return now + timedelta(days=7)

    def _get_next_optimal_time(self, from_time: datetime) -> datetime:
        """
        Get the next optimal posting time after from_time

        Args:
            from_time: Start looking from this time

        Returns:
            Next optimal datetime
        """
        # Convert optimal times to datetime objects for today
        optimal_datetimes = []
        for time_str in self.optimal_times:
            hour, minute = map(int, time_str.split(':'))
            dt = from_time.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # If this time has passed today, use tomorrow
            if dt <= from_time:
                dt = dt + timedelta(days=1)

            optimal_datetimes.append(dt)

        # Sort and return the nearest one
        optimal_datetimes.sort()

        if optimal_datetimes:
            return optimal_datetimes[0]

        # Fallback: next hour
        return from_time + timedelta(hours=1)

    def _is_valid_slot(
        self,
        candidate_time: datetime,
        content: QueuedContent,
        scheduled_times: List[datetime]
    ) -> bool:
        """
        Check if a time slot is valid for scheduling

        Args:
            candidate_time: Time to check
            content: Content to be scheduled
            scheduled_times: List of already scheduled times

        Returns:
            True if slot is valid
        """
        # Check 1: Is it within acceptable time windows?
        if not self._is_within_time_window(candidate_time):
            return False

        # Check 2: Is it far enough from other scheduled posts?
        if not self._respects_min_interval(candidate_time, scheduled_times):
            return False

        # Check 3: Does it respect topic spacing?
        if self.topic_spacing_enabled:
            if not self._respects_topic_spacing(candidate_time, content):
                return False

        # Check 4: Don't exceed posts_per_day limit
        if not self._respects_daily_limit(candidate_time, scheduled_times):
            return False

        return True

    def _is_within_time_window(self, dt: datetime) -> bool:
        """Check if datetime is within acceptable posting windows"""
        if not self.time_windows:
            return True  # No restrictions

        time_str = dt.strftime('%H:%M')

        for window in self.time_windows:
            start = window.get('start', '00:00')
            end = window.get('end', '23:59')

            if start <= time_str <= end:
                return True

        return False

    def _respects_min_interval(
        self,
        candidate_time: datetime,
        scheduled_times: List[datetime]
# Backward compatible
    ) -> bool:
        """Check if candidate time respects minimum interval between posts"""
        min_interval = timedelta(hours=self.min_interval_hours)

        for scheduled_time in scheduled_times:
            if scheduled_time:
                time_diff = abs((candidate_time - scheduled_time).total_seconds())
                if time_diff < min_interval.total_seconds():
                    return False

        return True

    def _respects_topic_spacing(
        self,
        candidate_time: datetime,
        content: QueuedContent
    ) -> bool:
        """Check if topic spacing is respected"""
        if not self.topic_spacing_enabled:
            return True

        # Get all scheduled posts
        scheduled_posts = self.queue.get_scheduled()

        # Check for similar topics within the spacing window
        spacing_window = timedelta(hours=self.min_hours_between_similar)

        for post in scheduled_posts:
            if post.scheduled_for:
                time_diff = abs((candidate_time - post.scheduled_for).total_seconds())

                # If within spacing window, check topic similarity
                if time_diff < spacing_window.total_seconds():
                    if self._topics_are_similar(content.topic, post.topic):
                        return False

        return True

    def _topics_are_similar(self, topic1: str, topic2: str) -> bool:
        """
        Check if two topics are similar

        For now, simple string matching.
        TODO: Could use embeddings for semantic similarity
        """
        # Normalize topics
        t1 = topic1.lower().strip()
        t2 = topic2.lower().strip()

        # Exact match
        if t1 == t2:
            return True

        # Check if one contains the other
        if t1 in t2 or t2 in t1:
            return True

        # Check for significant word overlap
        words1 = set(t1.split())
        words2 = set(t2.split())
        overlap = len(words1 & words2)

        # If more than 50% overlap, consider similar
        min_words = min(len(words1), len(words2))
        if min_words > 0 and overlap / min_words > 0.5:
            return True

        return False

    def _respects_daily_limit(
        self,
        candidate_time: datetime,
        scheduled_times: List[datetime]
    ) -> bool:
        """Check if daily posting limit is respected"""
        # Count posts on the same day as candidate_time
        same_day_count = 0
        candidate_date = candidate_time.date()

        for scheduled_time in scheduled_times:
            if scheduled_time and scheduled_time.date() == candidate_date:
                same_day_count += 1

        return same_day_count < self.posts_per_day

    def get_schedule_preview(self, days: int = 7) -> List[Dict]:
        """
        Get a preview of scheduled posts for the next N days

        Args:
            days: Number of days to preview

        Returns:
            List of scheduled posts with details
        """
        scheduled = self.queue.get_scheduled()

        # Filter to next N days
        now = datetime.now()
        end_date = now + timedelta(days=days)

        preview = []
        for content in scheduled:
            if content.scheduled_for and now <= content.scheduled_for <= end_date:
                preview.append({
                    'id': content.id,
                    'topic': content.topic,
                    'scheduled_for': content.scheduled_for,
                    'text_preview': content.text[:80] + '...' if len(content.text) > 80 else content.text,
                    'platform': content.platform,
                    'sentiment': content.sentiment
                })

        # Sort by scheduled time
        preview.sort(key=lambda x: x['scheduled_for'])

        return preview

    def reschedule_content(self, content_id: str) -> Optional[datetime]:
        """
        Reschedule a specific content item

        Args:
            content_id: ID of content to reschedule

        Returns:
            New scheduled datetime if successful
        """
        content = self.queue.get_by_id(content_id)
        if not content:
            return None

        # Temporarily set to queued to allow rescheduling
        self.queue.update_status(content_id, status='queued')

        # Schedule again
        return self.schedule_content(content_id)

    def get_stats(self) -> Dict:
        """Get scheduler statistics"""
        scheduled = self.queue.get_scheduled()
        now = datetime.now()

        # Calculate next post time
        future_posts = [p for p in scheduled if p.scheduled_for and p.scheduled_for > now]
        next_post = min(future_posts, key=lambda p: p.scheduled_for) if future_posts else None

        # Count posts per day
        posts_by_date = {}
        for post in scheduled:
            if post.scheduled_for:
                date_key = post.scheduled_for.date()
                posts_by_date[date_key] = posts_by_date.get(date_key, 0) + 1

        return {
            'total_scheduled': len(scheduled),
            'queued_waiting': len(self.queue.get_queued()),
            'next_post_time': next_post.scheduled_for if next_post else None,
            'next_post_topic': next_post.topic if next_post else None,
            'posts_next_7_days': len([p for p in scheduled if p.scheduled_for and now <= p.scheduled_for <= now + timedelta(days=7)]),
            'avg_posts_per_day': sum(posts_by_date.values()) / max(len(posts_by_date), 1)
        }


# Convenience functions
def schedule_all() -> List[Dict]:
    """
    Quick function to schedule all queued content

    Returns:
        List of scheduled content
    """
    scheduler = ContentScheduler()
    return scheduler.schedule_all_queued()


def get_schedule_preview(days: int = 7) -> List[Dict]:
    """
    Get preview of upcoming scheduled posts

    Args:
        days: Number of days to preview

    Returns:
        List of scheduled posts
    """
    scheduler = ContentScheduler()
    return scheduler.get_schedule_preview(days=days)


if __name__ == "__main__":
    # Demo/testing functionality
    print("Digital Freeman - Content Scheduler Module")
    print("=" * 50)

    try:
        # Initialize scheduler
        scheduler = ContentScheduler()
        print(f"✓ Scheduler initialized")
        print(f"✓ Min interval: {scheduler.min_interval_hours}h")
        print(f"✓ Max interval: {scheduler.max_interval_hours}h")
        print(f"✓ Posts per day: {scheduler.posts_per_day}")
        print(f"✓ Optimal times: {scheduler.optimal_times}")
        print(f"✓ Topic spacing: {scheduler.min_hours_between_similar}h")
        print()

        # Show current stats
        stats = scheduler.get_stats()
        print("Current scheduler stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

        # Test scheduling
        print("Testing scheduling:")
        queued = scheduler.queue.get_queued()

        if queued:
            print(f"Found {len(queued)} queued items")

            # Schedule the first one
            first = queued[0]
            print(f"Scheduling: {first.topic}")
            schedule_time = scheduler.schedule_content(first.id)

            if schedule_time:
                print(f"✓ Scheduled for: {schedule_time}")
            else:
                print("✗ Failed to schedule")
            print()
        else:
            # Add a test item if queue is empty
            print("No queued items found. Adding test content...")
            test_content = scheduler.queue.add(
                text="Test tweet about consciousness",
                topic="AI and consciousness",
                platform="twitter",
                sentiment="philosophical",
                source="test"
            )
            print(f"✓ Added test content: {test_content.id}")

            # Schedule it
            schedule_time = scheduler.schedule_content(test_content.id)
            print(f"✓ Scheduled for: {schedule_time}")
            print()

        # Show schedule preview
        preview = scheduler.get_schedule_preview(days=7)
        if preview:
            print(f"Schedule preview (next 7 days):")
            print("-" * 50)
            for item in preview:
                print(f"  {item['scheduled_for'].strftime('%Y-%m-%d %H:%M')} - {item['topic']}")
                print(f"    {item['text_preview']}")
                print()
        else:
            print("No posts scheduled in next 7 days")

        # Show updated stats
        stats = scheduler.get_stats()
        print("\nUpdated scheduler stats:")
        for key, value in stats.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
