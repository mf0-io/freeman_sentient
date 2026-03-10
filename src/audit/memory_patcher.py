"""Reads, parses, and patches MEMORY.md sections."""

import logging
import re
from typing import Dict

from src.audit.models import ImprovementSuggestion

logger = logging.getLogger(__name__)


class MemoryPatcher:
    """Reads, parses, and patches MEMORY.md sections."""

    def __init__(self, memory_path: str = "MEMORY.md") -> None:
        self._memory_path = memory_path

    async def apply_suggestion(self, suggestion: ImprovementSuggestion) -> bool:
        """Apply an auto-applicable suggestion to the appropriate section.

        Only applies if auto_applicable is True and severity is low or medium.

        Args:
            suggestion: The improvement suggestion to apply.

        Returns:
            True if the suggestion was successfully applied, False otherwise.
        """
        if not suggestion.auto_applicable:
            logger.info(
                "Suggestion %s is not auto-applicable, skipping.",
                suggestion.suggestion_id,
            )
            return False

        if suggestion.severity not in ("low", "medium"):
            logger.info(
                "Suggestion %s has severity '%s', only low/medium are auto-applied.",
                suggestion.suggestion_id,
                suggestion.severity,
            )
            return False

        section_name = suggestion.target_section
        current_content = self.read_section(section_name)

        if current_content is None:
            logger.warning(
                "Section '%s' not found in %s, cannot apply suggestion %s.",
                section_name,
                self._memory_path,
                suggestion.suggestion_id,
            )
            return False

        # Append the suggested text to the section
        if current_content.strip():
            updated_content = current_content.rstrip("\n") + "\n" + suggestion.suggested_text + "\n"
        else:
            updated_content = suggestion.suggested_text + "\n"

        try:
            self.write_section(section_name, updated_content)
            logger.info(
                "Applied suggestion %s to section '%s'.",
                suggestion.suggestion_id,
                section_name,
            )
            return True
        except Exception as exc:
            logger.error(
                "Failed to apply suggestion %s: %s",
                suggestion.suggestion_id,
                exc,
            )
            return False

    def read_section(self, section_name: str) -> str:
        """Parse MEMORY.md and return content of a section.

        Args:
            section_name: The section heading to find (e.g., 'BAD', 'Rules', 'Topics').

        Returns:
            The content of the section, or None if not found.
        """
        sections = self._parse_sections()
        return sections.get(section_name)

    def write_section(self, section_name: str, content: str) -> None:
        """Replace a section's content in MEMORY.md.

        Args:
            section_name: The section heading to replace.
            content: The new content for the section.

        Raises:
            ValueError: If the section is not found.
        """
        try:
            with open(self._memory_path, "r", encoding="utf-8") as f:
                full_text = f.read()
        except FileNotFoundError:
            raise ValueError(f"Memory file not found: {self._memory_path}")

        # Match the section header and its content up to the next section or EOF
        pattern = re.compile(
            r"(^## " + re.escape(section_name) + r"\s*\n)(.*?)(?=^## |\Z)",
            re.MULTILINE | re.DOTALL,
        )

        match = pattern.search(full_text)
        if not match:
            raise ValueError(f"Section '{section_name}' not found in {self._memory_path}")

        header = match.group(1)
        replacement = header + content
        updated_text = full_text[: match.start()] + replacement + full_text[match.end() :]

        with open(self._memory_path, "w", encoding="utf-8") as f:
            f.write(updated_text)

        logger.info("Updated section '%s' in %s", section_name, self._memory_path)

    def _parse_sections(self) -> Dict[str, str]:
        """Parse MEMORY.md into {section_name: content} dict using ## headers.

        Returns:
            Dictionary mapping section names to their content.
        """
        try:
            with open(self._memory_path, "r", encoding="utf-8") as f:
                full_text = f.read()
        except FileNotFoundError:
            logger.warning("Memory file not found: %s", self._memory_path)
            return {}

        sections: Dict[str, str] = {}
        # Split on ## headers, capturing the header name
        parts = re.split(r"^## (.+?)\s*$", full_text, flags=re.MULTILINE)

        # parts[0] is text before first ##, then alternating: header, content
        for i in range(1, len(parts), 2):
            section_name = parts[i].strip()
            section_content = parts[i + 1] if i + 1 < len(parts) else ""
            sections[section_name] = section_content

        return sections
