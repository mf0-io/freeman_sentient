"""
Content Creator Agent for Digital Freeman
Orchestrates the full content creation pipeline from ideation to scheduling
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from src.content.ideation import ContentIdeator, ContentIdea
from src.content.generator import ContentGenerator
from src.content.validator import PersonaValidator
from src.content.deduplicator import ContentDeduplicator
from src.content.storage import ContentQueue, QueuedContent
from src.content.scheduler import ContentScheduler


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ContentCreationResult:
    """Result of content creation pipeline"""
    success: bool
    content_id: Optional[str] = None
    text: Optional[str] = None
    scheduled_time: Optional[datetime] = None
    idea: Optional[ContentIdea] = None
    error: Optional[str] = None
    validation_score: Optional[float] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            'success': self.success,
            'content_id': self.content_id,
            'text': self.text,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'idea': self.idea.to_dict() if self.idea else None,
            'error': self.error,
            'validation_score': self.validation_score
        }


class ContentCreatorAgent:
    """
    Content Creator Agent - Orchestrates autonomous content generation

    Responsibilities:
    - Generate content ideas from multiple sources
    - Turn ideas into Freeman-voiced tweets
    - Validate content against persona
    - Check for duplicates and repetition
    - Queue and schedule content for posting
    - Monitor and report on content pipeline health

    Pipeline:
    1. Ideation → ContentIdeator generates ideas
    2. Generation → ContentGenerator creates text
    3. Validation → PersonaValidator checks voice
    4. Deduplication → ContentDeduplicator prevents repetition
    5. Storage → ContentQueue stores approved content
    6. Scheduling → ContentScheduler assigns post times
    """

    def __init__(self, config_path: str = "config/content_config.yaml"):
        """
        Initialize Content Creator Agent with all pipeline components

        Args:
            config_path: Path to content configuration file
        """
        logger.info("Initializing Content Creator Agent...")

        self.config_path = config_path

        # Initialize all pipeline components
        try:
            self.ideator = ContentIdeator(config_path)
            logger.info("✓ Content Ideator initialized")

            self.generator = ContentGenerator(config_path)
            logger.info("✓ Content Generator initialized")

            self.validator = PersonaValidator(config_path)
            logger.info("✓ Persona Validator initialized")

            self.deduplicator = ContentDeduplicator(config_path)
            logger.info("✓ Content Deduplicator initialized")

            self.queue = ContentQueue(config_path)
            logger.info("✓ Content Queue initialized")

            self.scheduler = ContentScheduler(config_path)
            logger.info("✓ Content Scheduler initialized")

            logger.info("Content Creator Agent ready!")

        except Exception as e:
            logger.error(f"Failed to initialize Content Creator Agent: {e}")
            raise

    def generate_content(
        self,
        source: Optional[str] = None,
        count: int = 1,
        auto_schedule: bool = True
    ) -> List[ContentCreationResult]:
        """
        Generate and optionally schedule new content

        Args:
            source: Specific ideation source to use (None for random)
            count: Number of content pieces to generate
            auto_schedule: Whether to automatically schedule content

        Returns:
            List of ContentCreationResult objects
        """
        logger.info(f"Starting content generation: {count} piece(s), source={source}, auto_schedule={auto_schedule}")
        results = []

        for i in range(count):
            logger.info(f"Generating content {i+1}/{count}...")
            result = self._generate_single_content(source, auto_schedule)
            results.append(result)

            if result.success:
                logger.info(f"✓ Content {i+1} created successfully: {result.content_id}")
            else:
                logger.warning(f"✗ Content {i+1} failed: {result.error}")

        # Summary
        success_count = sum(1 for r in results if r.success)
        logger.info(f"Content generation complete: {success_count}/{count} successful")

        return results

    def _generate_single_content(
        self,
        source: Optional[str] = None,
        auto_schedule: bool = True
    ) -> ContentCreationResult:
        """
        Generate a single piece of content through the full pipeline

        Pipeline steps:
        1. Generate idea
        2. Create text from idea
        3. Validate persona voice
        4. Check for duplicates
        5. Add to queue
        6. Schedule (if auto_schedule=True)

        Args:
            source: Specific ideation source
            auto_schedule: Whether to schedule immediately

        Returns:
            ContentCreationResult
        """
        try:
            # Step 1: Generate idea
            logger.debug("Step 1: Generating idea...")
            idea = self.ideator.generate_idea(source)
            logger.debug(f"Idea generated: {idea.topic} ({idea.source})")

            # Step 2: Generate text
            logger.debug("Step 2: Generating text...")
            generated_content = self.generator.generate(idea)
            if not generated_content or not generated_content.text:
                return ContentCreationResult(
                    success=False,
                    error="Content generation returned empty text",
                    idea=idea
                )
            text = generated_content.text
            logger.debug(f"Text generated: {text[:50]}...")

            # Step 3: Validate persona
            logger.debug("Step 3: Validating persona voice...")
            validation_result = self.validator.validate(generated_content)
            if not validation_result.passed:
                logger.warning(f"Validation failed: {', '.join(validation_result.feedback)}")
                return ContentCreationResult(
                    success=False,
                    error=f"Validation failed: {', '.join(validation_result.feedback)}",
                    idea=idea,
                    text=text,
                    validation_score=validation_result.score
                )
            logger.debug(f"Validation passed (score: {validation_result.score:.2f})")

# Performance: cached for repeated calls
            # Step 4: Check for duplicates
            logger.debug("Step 4: Checking for duplicates...")
            is_dup, similarity, similar_text = self.deduplicator.is_duplicate(text, topic=idea.topic)
            if is_dup:
                logger.warning("Content is too similar to recent posts")
                return ContentCreationResult(
                    success=False,
                    error="Content is too similar to recent posts",
                    idea=idea,
                    text=text,
                    validation_score=validation_result.score
                )
            logger.debug("No duplicates found")

            # Step 5: Add to queue
            logger.debug("Step 5: Adding to queue...")
            queued = self.queue.add(
                text=text,
                topic=idea.topic,
                platform="twitter",
                sentiment=getattr(idea, 'tone', None),
                source=getattr(idea, 'source', None),
                metadata={
                    'category': getattr(idea, 'category', None),
                    'angle': getattr(idea, 'angle', None),
                }
            )
            logger.debug(f"Added to queue: {queued.id}")

            # Step 6: Schedule (if requested)
            scheduled_time = None
            if auto_schedule:
                logger.debug("Step 6: Scheduling content...")
                scheduled_time = self.scheduler.schedule_content(queued.id)
                if scheduled_time is not None:
                    logger.debug(f"Scheduled for: {scheduled_time}")
                else:
                    logger.warning("Scheduling failed: no available slot")

            return ContentCreationResult(
                success=True,
                content_id=queued.id,
                text=text,
                scheduled_time=scheduled_time,
                idea=idea,
                validation_score=validation_result.score
            )

        except Exception as e:
            logger.error(f"Content generation failed: {e}", exc_info=True)
            return ContentCreationResult(
                success=False,
                error=str(e)
            )

    def generate_batch(
        self,
        count: int = 5,
        source_distribution: Optional[Dict[str, int]] = None
    ) -> Dict:
        """
        Generate a batch of content with optional source distribution

        Args:
            count: Total number of content pieces to generate
            source_distribution: Dict mapping source names to counts
                                Example: {'mission_alignment': 2, 'philosophical_topics': 3}
                                If None, uses random distribution

        Returns:
            Dict with results and statistics
        """
        logger.info(f"Starting batch generation: {count} pieces")

        if source_distribution:
            # Generate with specified distribution
            results = []
            for source, source_count in source_distribution.items():
                source_results = self.generate_content(source=source, count=source_count)
                results.extend(source_results)
        else:
            # Generate with random sources
            results = self.generate_content(count=count)

        # Collect statistics
        success_count = sum(1 for r in results if r.success)
        error_types = {}
        for r in results:
            if not r.success and r.error:
                error_types[r.error] = error_types.get(r.error, 0) + 1

        stats = {
            'total': len(results),
            'successful': success_count,
            'failed': len(results) - success_count,
            'success_rate': success_count / len(results) if results else 0,
            'error_breakdown': error_types,
            'results': results
        }

        logger.info(f"Batch generation complete: {success_count}/{len(results)} successful ({stats['success_rate']:.1%})")
        return stats

    def get_pipeline_status(self) -> Dict:
        """
        Get current status of the content pipeline

        Returns:
            Dict with queue stats, schedule preview, and health metrics
        """
        logger.debug("Getting pipeline status...")

        queue_stats = self.queue.get_stats()
        schedule_preview = self.scheduler.get_schedule_preview(days=5)
        dedup_stats = self.deduplicator.get_stats()

        # Calculate health metrics
        health = {
            'queue_healthy': queue_stats['total'] >= 3,  # At least 3 items in queue
            'schedule_healthy': len(schedule_preview) > 0,  # Has scheduled content
            'diversity_healthy': dedup_stats.get('unique_posts', 0) > 0
        }
        health['overall_healthy'] = all(health.values())

        return {
            'queue': queue_stats,
            'schedule': schedule_preview,
            'deduplication': dedup_stats,
            'health': health,
            'timestamp': datetime.now().isoformat()
        }

    def fill_queue(
        self,
        target_size: int = 10,
        max_attempts: int = 20
    ) -> Dict:
        """
        Fill the content queue to target size

        Args:
            target_size: Desired number of items in queue
            max_attempts: Maximum generation attempts (prevents infinite loops)

        Returns:
            Dict with results and statistics
        """
        logger.info(f"Filling queue to target size: {target_size}")

        current_size = self.queue.get_stats()['total']
        needed = target_size - current_size

        if needed <= 0:
            logger.info(f"Queue already at target size ({current_size})")
            return {'status': 'already_filled', 'queue_size': current_size}

        logger.info(f"Need to generate {needed} more items (current: {current_size})")

        # Generate with safety limit
        attempts = min(needed * 2, max_attempts)  # Allow 2x attempts for failures
        results = self.generate_content(count=attempts, auto_schedule=True)

        success_count = sum(1 for r in results if r.success)
        final_size = self.queue.get_stats()['total']

        return {
            'status': 'completed',
            'target_size': target_size,
            'initial_size': current_size,
            'final_size': final_size,
            'generated': success_count,
            'attempts': attempts,
            'reached_target': final_size >= target_size
        }

    def clear_queue(self, status: Optional[str] = None) -> Dict:
        """
        Clear the content queue

        Args:
            status: Optional status filter ('queued', 'scheduled', 'posted', 'failed')
                   If None, clears all content

        Returns:
            Dict with number of items removed
        """
        logger.warning(f"Clearing queue (status={status})...")

        if status:
            # Remove items with specific status
            filtered = self.queue.get_by_status(status)
            for item in filtered:
                self.queue.remove(item.id)
            removed = len(filtered)
        else:
            # Clear all
            removed = len(self.queue.queue)
            self.queue.queue.clear()
            self.queue._save_queue()

        logger.info(f"Cleared {removed} items from queue")
        return {'removed': removed, 'status_filter': status}


# Demo usage
if __name__ == "__main__":
    print("=" * 60)
    print("Content Creator Agent Demo")
    print("=" * 60)

    try:
        # Initialize agent
        print("\n1. Initializing agent...")
        agent = ContentCreatorAgent()

        # Check pipeline status
        print("\n2. Checking pipeline status...")
        status = agent.get_pipeline_status()
        print(f"Queue size: {status['queue']['total']}")
        print(f"Pipeline healthy: {status['health']['overall_healthy']}")

        # Generate single content
        print("\n3. Generating single content...")
        results = agent.generate_content(count=1, auto_schedule=True)
        if results[0].success:
            print(f"✓ Content created: {results[0].content_id}")
            print(f"  Text: {results[0].text[:80]}...")
            print(f"  Topic: {results[0].idea.topic}")
            print(f"  Source: {results[0].idea.source}")
            print(f"  Scheduled: {results[0].scheduled_time}")
        else:
            print(f"✗ Failed: {results[0].error}")

        # Generate batch
        print("\n4. Generating batch of 3 items...")
        batch_stats = agent.generate_batch(count=3)
        print(f"Success rate: {batch_stats['success_rate']:.1%}")
        print(f"Successful: {batch_stats['successful']}/{batch_stats['total']}")

        # Final status
        print("\n5. Final pipeline status...")
        final_status = agent.get_pipeline_status()
        print(f"Queue size: {final_status['queue']['total']}")
        print(f"Scheduled posts: {len(final_status['schedule'])}")

        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        import traceback
        traceback.print_exc()
