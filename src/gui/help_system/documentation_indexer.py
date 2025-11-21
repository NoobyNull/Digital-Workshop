"""
Documentation indexer for searchable help system.

Scans all markdown files in the project and builds a searchable index
of documentation content with keywords and sections.
"""

import re
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

from src.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class HelpTopic:
    """Represents a searchable help topic."""

    title: str
    content: str
    file_path: str
    section: str = ""
    keywords: List[str] = None
    category: str = "General"

    def __post_init__(self) -> None:
        if self.keywords is None:
            self.keywords = []


class DocumentationIndexer:
    """Indexes markdown documentation for keyword search."""

    # Documentation directories to scan
    DOC_PATHS = [
        "docs",
        "documentation",
        "openspec",
    ]

    # Root markdown files to include
    ROOT_MD_FILES = [
        "SETTINGS_INTEGRATION_COMPLETE.md",
        "SETTINGS_QUICK_REFERENCE.md",
        "MISSING_SETTINGS_ANALYSIS.md",
        "PREFERENCES_REORGANIZATION_REPORT.md",
        "TEST_RUNNER_GUIDE.md",
        "THEMING_AUDIT.md",
    ]

    # Category mapping based on file patterns
    CATEGORY_PATTERNS = {
        "settings": ["settings", "preferences", "config"],
        "theming": ["theme", "color", "style"],
        "viewer": ["viewer", "3d", "vtk", "camera", "lighting"],
        "models": ["model", "library", "import", "export"],
        "metadata": ["metadata", "tags", "categories"],
        "search": ["search", "filter", "query"],
        "developer": ["developer", "architecture", "api", "parser"],
        "troubleshooting": ["troubleshoot", "error", "fix", "issue"],
    }

    def __init__(self) -> None:
        """Initialize the indexer."""
        self.topics: List[HelpTopic] = []
        self.project_root = Path(__file__).parent.parent.parent.parent

    def build_index(self) -> List[HelpTopic]:
        """Build the documentation index."""
        logger.info("Building documentation index...")
        self.topics = []

        # Scan documentation directories
        for doc_path in self.DOC_PATHS:
            full_path = self.project_root / doc_path
            if full_path.exists():
                self._scan_directory(full_path)

        # Scan root markdown files
        for md_file in self.ROOT_MD_FILES:
            file_path = self.project_root / md_file
            if file_path.exists():
                self._index_file(file_path)

        logger.info("Documentation index built: %s topics", len(self.topics))
        return self.topics

    def _scan_directory(self, directory: Path) -> None:
        """Recursively scan directory for markdown files."""
        try:
            for md_file in directory.rglob("*.md"):
                self._index_file(md_file)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Error scanning directory %s: {e}", directory)

    def _index_file(self, file_path: Path) -> None:
        """Index a single markdown file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract sections and create topics
            sections = self._extract_sections(content, file_path)
            self.topics.extend(sections)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Error indexing file %s: {e}", file_path)

    def _extract_sections(self, content: str, file_path: Path) -> List[HelpTopic]:
        """Extract sections from markdown content."""
        sections = []
        rel_path = str(file_path.relative_to(self.project_root))
        category = self._determine_category(rel_path)

        # Split by headings
        heading_pattern = r"^(#{1,6})\s+(.+)$"
        lines = content.split("\n")

        current_section = ""
        current_content = []
        current_heading = ""

        for line in lines:
            match = re.match(heading_pattern, line, re.MULTILINE)
            if match:
                # Save previous section
                if current_heading:
                    section_content = "\n".join(current_content).strip()
                    if section_content:
                        keywords = self._extract_keywords(
                            current_heading + " " + section_content
                        )
                        topic = HelpTopic(
                            title=current_heading,
                            content=section_content[:500],  # First 500 chars
                            file_path=rel_path,
                            section=current_section,
                            keywords=keywords,
                            category=category,
                        )
                        sections.append(topic)

                # Start new section
                current_heading = match.group(2)
                current_section = current_heading
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_heading:
            section_content = "\n".join(current_content).strip()
            if section_content:
                keywords = self._extract_keywords(
                    current_heading + " " + section_content
                )
                topic = HelpTopic(
                    title=current_heading,
                    content=section_content[:500],
                    file_path=rel_path,
                    section=current_section,
                    keywords=keywords,
                    category=category,
                )
                sections.append(topic)

        return sections

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Remove markdown syntax
        text = re.sub(r"[#*`\[\]()]", "", text)
        # Split into words and filter
        words = text.lower().split()
        # Keep words longer than 3 chars
        keywords = [w for w in words if len(w) > 3 and not w.startswith("-")]
        return list(set(keywords))[:10]  # Limit to 10 keywords

    def _determine_category(self, file_path: str) -> str:
        """Determine category based on file path."""
        file_path_lower = file_path.lower()
        for category, patterns in self.CATEGORY_PATTERNS.items():
            for pattern in patterns:
                if pattern in file_path_lower:
                    return category.title()
        return "General"

    def search(self, query: str) -> List[Tuple[HelpTopic, int]]:
        """Search topics by keyword. Returns list of (topic, relevance_score)."""
        if not self.topics:
            self.build_index()

        query_words = query.lower().split()
        results = []

        for topic in self.topics:
            score = 0

            # Check title (highest weight)
            title_lower = topic.title.lower()
            for word in query_words:
                if word in title_lower:
                    score += 10

            # Check keywords (medium weight)
            for keyword in topic.keywords:
                for word in query_words:
                    if word in keyword:
                        score += 5

            # Check content (lower weight)
            content_lower = topic.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1

            if score > 0:
                results.append((topic, score))

        # Sort by relevance score
        results.sort(key=lambda x: x[1], reverse=True)
        return results
