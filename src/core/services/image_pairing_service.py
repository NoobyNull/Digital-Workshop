"""
Image Pairing Service for Import Process.

Detects and pairs image files with model files during import based on matching filenames.
For example: model1.stl + model1.jpg will be paired together.
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass

from src.core.logging_config import get_logger


logger = get_logger(__name__)


# Supported image extensions for thumbnail pairing
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".tif", ".webp"}

# Supported model extensions
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


@dataclass
class ImageModelPair:
    """Represents a paired image and model file."""

    model_path: str
    image_path: str
    base_name: str
    confidence: float = 1.0  # Confidence score (1.0 = exact match)


class ImagePairingService:
    """
    Service for detecting and pairing image files with model files.

    Matches files based on:
    1. Exact base name match (model1.stl + model1.jpg)
    2. Case-insensitive matching
    3. Common naming patterns (model1_preview.jpg, model1_thumb.jpg)
    """

    def __init__(self) -> None:
        """Initialize the image pairing service."""
        self.logger = logger

    def find_pairs(
        self, file_paths: List[str]
    ) -> Tuple[List[ImageModelPair], List[str], List[str]]:
        """
        Find image-model pairs from a list of file paths.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            Tuple of:
            - List of ImageModelPair objects (paired files)
            - List of unpaired model paths
            - List of unpaired image paths
        """
        # Separate files by type
        models: Dict[str, str] = {}  # base_name -> full_path
        images: Dict[str, str] = {}  # base_name -> full_path

        for file_path in file_paths:
            path = Path(file_path)
            ext = path.suffix.lower()
            base_name = path.stem.lower()  # Case-insensitive matching

            if ext in MODEL_EXTENSIONS:
                models[base_name] = file_path
            elif ext in IMAGE_EXTENSIONS:
                images[base_name] = file_path

        # Find exact matches
        pairs: List[ImageModelPair] = []
        paired_models: Set[str] = set()
        paired_images: Set[str] = set()

        for base_name, model_path in models.items():
            # Check for exact match
            if base_name in images:
                image_path = images[base_name]
                pairs.append(
                    ImageModelPair(
                        model_path=model_path,
                        image_path=image_path,
                        base_name=base_name,
                        confidence=1.0,
                    )
                )
                paired_models.add(base_name)
                paired_images.add(base_name)
                self.logger.info("Paired: %s <-> %s", Path(model_path).name, Path(image_path).name)
                continue

            # Check for common naming patterns
            # e.g., model1.stl + model1_preview.jpg, model1_thumb.jpg, model1_thumbnail.jpg
            for suffix in ["_preview", "_thumb", "_thumbnail", "_render", "_image"]:
                pattern_name = f"{base_name}{suffix}"
                if pattern_name in images:
                    image_path = images[pattern_name]
                    pairs.append(
                        ImageModelPair(
                            model_path=model_path,
                            image_path=image_path,
                            base_name=base_name,
                            confidence=0.9,  # Slightly lower confidence for pattern match
                        )
                    )
                    paired_models.add(base_name)
                    paired_images.add(pattern_name)
                    self.logger.info(
                        "Paired (pattern): %s <-> %s",
                        Path(model_path).name,
                        Path(image_path).name,
                    )
                    break

        # Collect unpaired files
        unpaired_models = [models[name] for name in models if name not in paired_models]
        unpaired_images = [images[name] for name in images if name not in paired_images]

        self.logger.info(
            "Pairing complete: %d pairs, %d unpaired models, %d unpaired images",
            len(pairs),
            len(unpaired_models),
            len(unpaired_images),
        )

        return pairs, unpaired_models, unpaired_images

    def find_matching_image(
        self, model_path: str, search_directory: Optional[str] = None
    ) -> Optional[str]:
        """
        Find a matching image file for a single model file.

        Args:
            model_path: Path to the model file
            search_directory: Optional directory to search in (defaults to model's directory)

        Returns:
            Path to matching image file, or None if not found
        """
        model_path_obj = Path(model_path)
        base_name = model_path_obj.stem.lower()

        # Determine search directory
        if search_directory:
            search_dir = Path(search_directory)
        else:
            search_dir = model_path_obj.parent

        if not search_dir.exists():
            return None

        # Check for exact match
        for ext in IMAGE_EXTENSIONS:
            candidate = search_dir / f"{base_name}{ext}"
            if candidate.exists():
                self.logger.debug("Found matching image: %s", candidate)
                return str(candidate)

            # Also check uppercase extension
            candidate_upper = search_dir / f"{base_name}{ext.upper()}"
            if candidate_upper.exists():
                self.logger.debug("Found matching image: %s", candidate_upper)
                return str(candidate_upper)

        # Check for pattern matches
        for suffix in ["_preview", "_thumb", "_thumbnail", "_render", "_image"]:
            for ext in IMAGE_EXTENSIONS:
                candidate = search_dir / f"{base_name}{suffix}{ext}"
                if candidate.exists():
                    self.logger.debug("Found matching image (pattern): %s", candidate)
                    return str(candidate)

        return None

    def validate_image(self, image_path: str) -> bool:
        """
        Validate that an image file is suitable for use as a thumbnail.

        Args:
            image_path: Path to image file

        Returns:
            True if image is valid, False otherwise
        """
        try:
            path = Path(image_path)

            # Check file exists
            if not path.exists():
                self.logger.warning("Image file does not exist: %s", image_path)
                return False

            # Check file size (reject if too small or too large)
            file_size = path.stat().st_size
            if file_size < 1024:  # Less than 1KB
                self.logger.warning("Image file too small: %s (%d bytes)", image_path, file_size)
                return False

            if file_size > 50 * 1024 * 1024:  # More than 50MB
                self.logger.warning("Image file too large: %s (%d bytes)", image_path, file_size)
                return False

            # Check extension
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                self.logger.warning("Unsupported image format: %s", path.suffix)
                return False

            # TODO: Could add PIL/Pillow validation to check if image is actually readable
            # For now, basic checks are sufficient

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error validating image %s: %s", image_path, e)
            return False


def get_image_pairing_service() -> ImagePairingService:
    """Get singleton instance of ImagePairingService."""
    return ImagePairingService()
