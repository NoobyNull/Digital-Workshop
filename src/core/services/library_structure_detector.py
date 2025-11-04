"""
Library Structure Detector for analyzing folder hierarchies and detecting organization patterns.

Analyzes existing folder structures to detect file type grouping, depth-based organization,
metadata files, and naming conventions. Calculates confidence score for organization level.
"""

import os
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass
from collections import defaultdict

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


@dataclass
class LibraryStructureAnalysis:
    """Result of library structure analysis."""

    folder_path: str
    is_organized: bool
    confidence_score: float  # 0-100%
    structure_type: str  # "flat", "nested", "balanced"
    file_type_grouping: Dict[str, int]  # file_type -> count
    depth_level: int
    has_metadata: bool
    metadata_files: List[str]
    total_files: int
    total_folders: int
    naming_patterns: List[str]
    recommendations: List[str]


class LibraryStructureDetector:
    """Detects and analyzes library folder structures."""

    # File type categories
    MODEL_EXTENSIONS = {
        ".stl",
        ".obj",
        ".step",
        ".stp",
        ".3mf",
        ".ply",
        ".fbx",
        ".dae",
        ".gltf",
        ".glb",
    }
    DOCUMENT_EXTENSIONS = {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".rtf",
        ".odt",
        ".ods",
    }
    IMAGE_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".tiff",
        ".tif",
        ".webp",
        ".ico",
    }
    METADATA_EXTENSIONS = {".md", ".json", ".xml", ".yaml", ".yml", ".csv", ".tsv"}
    METADATA_FILENAMES = {
        "readme",
        "manifest",
        "index",
        "catalog",
        "inventory",
        "metadata",
    }

    def __init__(self):
        """Initialize library structure detector."""
        self.logger = logger

    @log_function_call(logger)
    def analyze(self, folder_path: str) -> LibraryStructureAnalysis:
        """
        Analyze folder structure for organization patterns.

        Args:
            folder_path: Path to folder to analyze

        Returns:
            LibraryStructureAnalysis with detection results
        """
        try:
            folder_path = str(Path(folder_path).resolve())

            if not os.path.isdir(folder_path):
                raise ValueError(f"Folder not found: {folder_path}")

            # Collect statistics
            file_type_grouping = defaultdict(int)
            metadata_files = []
            all_files = []
            all_folders = set()
            depths = []

            # Walk through directory
            for root, dirs, files in os.walk(folder_path):
                depth = len(Path(root).relative_to(folder_path).parts)
                depths.append(depth)
                all_folders.update(dirs)

                for file in files:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)

                    # Categorize file
                    ext = Path(file).suffix.lower()
                    file_type = self._categorize_file(file, ext)
                    file_type_grouping[file_type] += 1

                    # Check for metadata
                    if self._is_metadata_file(file, ext):
                        metadata_files.append(file)

            # Analyze structure
            structure_type = self._detect_structure_type(
                folder_path, all_files, all_folders
            )
            confidence_score = self._calculate_confidence(
                file_type_grouping,
                len(all_files),
                len(all_folders),
                len(metadata_files),
                structure_type,
            )
            naming_patterns = self._detect_naming_patterns(all_folders)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                structure_type, confidence_score, len(all_files)
            )

            analysis = LibraryStructureAnalysis(
                folder_path=folder_path,
                is_organized=confidence_score >= 40,
                confidence_score=confidence_score,
                structure_type=structure_type,
                file_type_grouping=dict(file_type_grouping),
                depth_level=max(depths) if depths else 0,
                has_metadata=len(metadata_files) > 0,
                metadata_files=metadata_files,
                total_files=len(all_files),
                total_folders=len(all_folders),
                naming_patterns=naming_patterns,
                recommendations=recommendations,
            )

            logger.info(
                f"Library analysis complete: {folder_path} (confidence: {confidence_score:.1f}%)"
            )
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze library structure: {str(e)}")
            raise

    def _categorize_file(self, filename: str, ext: str) -> str:
        """Categorize file by extension."""
        if ext in self.MODEL_EXTENSIONS:
            return "3D Models"
        elif ext in self.DOCUMENT_EXTENSIONS:
            return "Documents"
        elif ext in self.IMAGE_EXTENSIONS:
            return "Images"
        elif ext in self.METADATA_EXTENSIONS:
            return "Metadata"
        else:
            return "Other"

    def _is_metadata_file(self, filename: str, ext: str) -> bool:
        """Check if file is metadata."""
        name_lower = Path(filename).stem.lower()
        return (
            ext in self.METADATA_EXTENSIONS
            or name_lower in self.METADATA_FILENAMES
            or filename.lower() in {"readme", "manifest", "index", "catalog"}
        )

    def _detect_structure_type(
        self, folder_path: str, files: List[str], folders: set
    ) -> str:
        """Detect structure type: flat, nested, or balanced."""
        if not files:
            return "flat"

        # Calculate depth distribution
        depths = []
        for file_path in files:
            rel_path = Path(file_path).relative_to(folder_path)
            depth = len(rel_path.parts) - 1
            depths.append(depth)

        avg_depth = sum(depths) / len(depths) if depths else 0
        max_depth = max(depths) if depths else 0

        if max_depth <= 1:
            return "flat"
        elif avg_depth > 2:
            return "nested"
        else:
            return "balanced"

    def _calculate_confidence(
        self,
        file_type_grouping: Dict[str, int],
        total_files: int,
        total_folders: int,
        metadata_count: int,
        structure_type: str,
    ) -> float:
        """Calculate organization confidence score (0-100%)."""
        if total_files == 0:
            return 0.0

        score = 0.0

        # File type grouping (0-40 points)
        if len(file_type_grouping) > 1:
            grouping_ratio = len(file_type_grouping) / total_files
            score += min(40, grouping_ratio * 100)

        # Folder organization (0-30 points)
        if total_folders > 0:
            folder_ratio = total_folders / total_files
            if 0.1 <= folder_ratio <= 0.5:
                score += 30
            elif folder_ratio > 0:
                score += 15

        # Metadata presence (0-20 points)
        if metadata_count > 0:
            score += 20

        # Structure type (0-10 points)
        if structure_type in ("nested", "balanced"):
            score += 10

        return min(100.0, score)

    def _detect_naming_patterns(self, folders: set) -> List[str]:
        """Detect naming patterns in folder names."""
        patterns = []

        if not folders:
            return patterns

        # Check for common patterns
        folder_names = [f.lower() for f in folders]

        # File type patterns
        if any(name in folder_names for name in ["stl", "obj", "step", "models", "3d"]):
            patterns.append("File type grouping")

        # Category patterns
        if any(
            name in folder_names
            for name in ["characters", "buildings", "vehicles", "nature", "objects"]
        ):
            patterns.append("Category organization")

        # Date patterns
        if any(
            name for name in folder_names if name.startswith("20") and len(name) == 4
        ):
            patterns.append("Date-based organization")

        # Numbered patterns
        if any(name[0].isdigit() for name in folder_names if name):
            patterns.append("Numbered organization")

        return patterns

    def _generate_recommendations(
        self, structure_type: str, confidence_score: float, total_files: int
    ) -> List[str]:
        """Generate recommendations for import."""
        recommendations = []

        if confidence_score < 40:
            recommendations.append(
                "Library structure is not well organized. Consider reorganizing before import."
            )
        elif confidence_score < 70:
            recommendations.append(
                "Library structure is moderately organized. Import will preserve existing structure."
            )
        else:
            recommendations.append(
                "Library structure is well organized. Import will preserve existing structure."
            )

        if structure_type == "flat" and total_files > 100:
            recommendations.append(
                "Consider organizing files into subdirectories for better management."
            )

        if total_files > 1000:
            recommendations.append("Large library detected. Import may take some time.")

        return recommendations
