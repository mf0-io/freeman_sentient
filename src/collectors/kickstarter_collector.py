"""
Kickstarter collector — parses backer interactions and project comments.

Kickstarter has no official public API, so this collector works with
pre-exported data (JSON/CSV) or scrapes public project pages.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.collectors.base import BaseCollector

logger = logging.getLogger(__name__)


class KickstarterCollector(BaseCollector):
    """
    Collects interaction data from Kickstarter campaigns.

    Since Kickstarter lacks a public API, this collector supports two modes:

    1. **File-based**: Parse exported backer/comment data (JSON/CSV)
    2. **Scrape-based**: Parse public project pages (requires project URLs)

    Extracts:
    - Backers (person backed a project = interaction with creator)
    - Comments on project updates
    - Backer-to-backer replies
    - Pledge levels as interaction weight
    """

    @property
    def platform_name(self) -> str:
        return "kickstarter"

    def __init__(self, graph, config: Dict[str, Any]):
        super().__init__(graph, config)
        self.data_dir = Path(config.get(
            "kickstarter_data_dir",
            os.environ.get("KICKSTARTER_DATA_DIR", "data/kickstarter"),
        ))
        self.project_urls = config.get("kickstarter_project_urls", [])
        self.creator_name = config.get("kickstarter_creator_name", "Mr. Freeman")
        self.creator_id = config.get("kickstarter_creator_id", "mrfreeman")

    async def validate_credentials(self) -> bool:
        """Check if data directory or project URLs are configured."""
        if self.data_dir.exists() and any(self.data_dir.glob("*.json")):
            return True
        if self.project_urls:
            return True
        logger.warning("No Kickstarter data sources configured")
        return False

    async def collect(self, since: Optional[datetime] = None) -> int:
        """Collect from available data sources."""
        total = 0

        if self.data_dir.exists():
            total += await self._collect_from_files(since)

        if self.project_urls:
            total += await self._collect_from_pages(since)

        return total

    async def _collect_from_files(self, since: Optional[datetime]) -> int:
        """Parse exported backer/comment JSON files."""
        count = 0

        # Backers file: [{name, pledge_amount, backed_at, email_hash, ...}]
        backers_file = self.data_dir / "backers.json"
        if backers_file.exists():
            count += await self._parse_backers(backers_file, since)

        # Comments file: [{author, text, created_at, reply_to, ...}]
        comments_file = self.data_dir / "comments.json"
        if comments_file.exists():
            count += await self._parse_comments(comments_file, since)

        return count

    async def _parse_backers(
        self, filepath: Path, since: Optional[datetime]
    ) -> int:
        """Parse backers JSON and create interaction edges."""
        try:
            with open(filepath) as f:
                backers = json.load(f)

            creator = await self._ensure_person(
                name=self.creator_name,
                platform_user_id=self.creator_id,
                role="team",
            )

            count = 0
            for backer in backers:
                backed_at = backer.get("backed_at")
                if backed_at:
                    ts = datetime.fromisoformat(backed_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    if since and ts < since:
                        continue
                else:
                    ts = datetime.utcnow()

                backer_id = backer.get("id", backer.get("email_hash", ""))
                backer_name = backer.get("name", f"backer_{backer_id}")
                pledge = backer.get("pledge_amount", 0)

                if not backer_id:
                    continue

                await self._ensure_person(
                    name=backer_name,
                    platform_user_id=str(backer_id),
                    role="backer",
                    tags=["kickstarter_backer"],
                    metadata={
                        "pledge_amount": pledge,
                        "reward_tier": backer.get("reward_tier", ""),
                    },
                )

                weight = min(5.0, 1.0 + (pledge / 50.0)) if pledge else 1.0

                await self._record_interaction(
                    source_platform_id=str(backer_id),
                    target_platform_id=self.creator_id,
                    interaction_type="back",
                    context=f"Backed ${pledge}" if pledge else "Backed project",
                    weight=weight,
                    timestamp=ts,
                    metadata={"pledge_amount": pledge},
                )
                count += 1

            logger.info(f"Parsed {count} backers from {filepath}")
            return count

        except Exception as e:
            logger.error(f"Failed to parse backers file {filepath}: {e}")
            return 0

    async def _parse_comments(
        self, filepath: Path, since: Optional[datetime]
    ) -> int:
        """Parse project comments and create interaction edges."""
        try:
            with open(filepath) as f:
                comments = json.load(f)

            creator = await self._ensure_person(
                name=self.creator_name,
                platform_user_id=self.creator_id,
                role="team",
            )

            count = 0
            for comment in comments:
                created_at = comment.get("created_at")
                if created_at:
                    ts = datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
                    if since and ts < since:
                        continue
                else:
                    ts = datetime.utcnow()

                author_id = comment.get("author_id", "")
                author_name = comment.get("author", f"user_{author_id}")
                text = comment.get("text", "")

                if not author_id:
                    continue

                await self._ensure_person(
                    name=author_name,
                    platform_user_id=str(author_id),
                    role="backer",
                )

                reply_to = comment.get("reply_to")
                if reply_to:
                    target_id = str(reply_to.get("author_id", ""))
                    if target_id:
                        await self._ensure_person(
                            name=reply_to.get("author", ""),
                            platform_user_id=target_id,
                        )
                        await self._record_interaction(
                            source_platform_id=str(author_id),
                            target_platform_id=target_id,
                            interaction_type="reply",
                            context=text[:200],
                            weight=2.0,
                            timestamp=ts,
                        )
                        count += 1
                else:
                    await self._record_interaction(
                        source_platform_id=str(author_id),
                        target_platform_id=self.creator_id,
                        interaction_type="comment",
                        context=text[:200],
                        weight=1.5,
                        timestamp=ts,
                    )
                    count += 1

            logger.info(f"Parsed {count} comments from {filepath}")
            return count

        except Exception as e:
            logger.error(f"Failed to parse comments file {filepath}: {e}")
            return 0

    async def _collect_from_pages(self, since: Optional[datetime]) -> int:
        """Scrape public project pages for interaction data."""
        try:
            import httpx
            from html.parser import HTMLParser

            count = 0
            async with httpx.AsyncClient() as client:
                for url in self.project_urls:
                    resp = await client.get(url, timeout=30, follow_redirects=True)
                    if resp.status_code == 200:
                        count += await self._parse_project_page(resp.text, url)

            return count

        except ImportError:
            logger.warning("httpx not installed, skipping page scraping")
            return 0
        except Exception as e:
            logger.error(f"Failed to scrape Kickstarter pages: {e}")
            return 0

    async def _parse_project_page(self, html: str, url: str) -> int:
        """Extract interaction data from a Kickstarter project page."""
        # Minimal extraction from public page metadata
        # Full implementation would parse JSON-LD or embedded state
        count = 0
        try:
            if '"backers_count":' in html:
                import re
                match = re.search(r'"backers_count":\s*(\d+)', html)
                if match:
                    backer_count = int(match.group(1))
                    logger.info(f"Project {url}: {backer_count} backers (aggregate only)")
        except Exception:
            pass
        return count
