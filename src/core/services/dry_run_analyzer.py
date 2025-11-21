"""
Dry Run Analyzer for simulating project import without file operations.

Provides preview of what will happen during import including file counts,
structure analysis, blocked files, and storage estimates.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

from .file_type_filter import FileTypeFilter
from .library_structure_detector import LibraryStructureDetector
from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


@dataclass
class DryRunReport:
    """Report of dry run analysis."""

    folder_path: str
    project_name: str
    total_files: int
    allowed_files: int
    blocked_files: int
    total_size_bytes: int
    total_size_mb: float
    file_categories: Dict[str, int]
    blocked_file_details: List[Dict]
    structure_analysis: Optional[Dict]
    recommendations: List[str]
    can_proceed: bool


class DryRunAnalyzer:
    """Analyzes import without performing file operations."""

    def __init__(self) -> None:
        """Initialize dry run analyzer."""
        self.logger = logger
        self.file_filter = FileTypeFilter()
        self.structure_detector = LibraryStructureDetector()

    @log_function_call(logger)
    def analyze(self, folder_path: str, project_name: str) -> DryRunReport:
        """
        Perform dry run analysis of folder for import.

        Args:
            folder_path: Path to folder to analyze
            project_name: Name for the project

        Returns:
            DryRunReport with analysis results
        """
        try:
            folder_path = str(Path(folder_path).resolve())

            if not os.path.isdir(folder_path):
                raise ValueError(f"Folder not found: {folder_path}")

            # Collect all files
            all_files = []
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)

            # Filter files
            allowed_files, blocked_files = self.file_filter.filter_files(all_files)

            # Calculate statistics
            file_categories = self._categorize_files(allowed_files)
            total_size = self._calculate_total_size(allowed_files)
            blocked_details = self._get_blocked_details(blocked_files)

            # Analyze structure
            structure_analysis = self._analyze_structure(folder_path)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                len(allowed_files), len(blocked_files), total_size, structure_analysis
            )

            # Determine if can proceed
            can_proceed = len(allowed_files) > 0

            report = DryRunReport(
                folder_path=folder_path,
                project_name=project_name,
                total_files=len(all_files),
                allowed_files=len(allowed_files),
                blocked_files=len(blocked_files),
                total_size_bytes=total_size,
                total_size_mb=total_size / (1024 * 1024),
                file_categories=file_categories,
                blocked_file_details=blocked_details,
                structure_analysis=structure_analysis,
                recommendations=recommendations,
                can_proceed=can_proceed,
            )

            logger.info(
                f"Dry run analysis complete: {project_name} ({len(allowed_files)} files, {report.total_size_mb:.2f} MB)"
            )
            return report

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to perform dry run analysis: %s", str(e))
            raise

    def _categorize_files(self, files: List) -> Dict[str, int]:
        """Categorize files by type."""
        categories = defaultdict(int)

        for file_result in files:
            categories[file_result.category] += 1

        return dict(categories)

    def _calculate_total_size(self, files: List) -> int:
        """Calculate total size of files."""
        total = 0

        for file_result in files:
            try:
                if os.path.exists(file_result.file_path):
                    total += os.path.getsize(file_result.file_path)
            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as e:
                logger.warning(
                    "Failed to get size of %s: {str(e)}", file_result.file_path
                )

        return total

    def _get_blocked_details(self, blocked_files: List) -> List[Dict]:
        """Get details of blocked files."""
        details = []

        for file_result in blocked_files:
            details.append(
                {
                    "file_name": file_result.file_name,
                    "extension": file_result.extension,
                    "reason": file_result.reason,
                    "file_path": file_result.file_path,
                }
            )

        return details

    def _analyze_structure(self, folder_path: str) -> Dict:
        """Analyze folder structure."""
        try:
            analysis = self.structure_detector.analyze(folder_path)

            return {
                "structure_type": analysis.structure_type,
                "confidence_score": analysis.confidence_score,
                "is_organized": analysis.is_organized,
                "depth_level": analysis.depth_level,
                "has_metadata": analysis.has_metadata,
                "metadata_files": analysis.metadata_files,
                "naming_patterns": analysis.naming_patterns,
                "total_folders": analysis.total_folders,
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Failed to analyze structure: %s", str(e))
            return {}

    def _generate_recommendations(
        self,
        allowed_count: int,
        blocked_count: int,
        total_size: int,
        structure_analysis: Dict,
    ) -> List[str]:
        """Generate recommendations for import."""
        recommendations = []

        if allowed_count == 0:
            recommendations.append("⚠️ No allowed files found. Import cannot proceed.")
            return recommendations

        if blocked_count > 0:
            recommendations.append(
                f"⚠️ {blocked_count} files will be blocked during import."
            )

        total_mb = total_size / (1024 * 1024)
        if total_mb > 1000:
            recommendations.append(
                f"ℹ️ Large import detected ({total_mb:.0f} MB). Import may take several minutes."
            )
        elif total_mb > 100:
            recommendations.append(f"ℹ️ Medium import detected ({total_mb:.0f} MB).")

        if structure_analysis:
            confidence = structure_analysis.get("confidence_score", 0)
            if confidence >= 70:
                recommendations.append(
                    "✓ Library structure is well organized. Existing structure will be preserved."
                )
            elif confidence >= 40:
                recommendations.append(
                    "ℹ️ Library structure is moderately organized. Existing structure will be preserved."
                )
            else:
                recommendations.append(
                    "⚠️ Library structure is not well organized. Consider reorganizing before import."
                )

        recommendations.append("✓ Ready to proceed with import.")

        return recommendations
