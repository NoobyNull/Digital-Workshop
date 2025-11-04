"""
Thumbnail resizer for efficient multi-size thumbnail generation.

Uses Pillow to resize a single high-quality thumbnail to multiple sizes,
avoiding expensive VTK rendering for each size.
"""

from pathlib import Path
from typing import Dict, Tuple, Optional
from PIL import Image

from src.core.logging_config import get_logger


class ThumbnailResizer:
    """
    Efficiently resize thumbnails to multiple sizes using Pillow.

    Instead of rendering with VTK multiple times, this generates one
    high-quality 1280x1280 image and resizes it to smaller sizes.

    Supported sizes:
    - 1280x1280 (xlarge) - Original high-quality render
    - 512x512 (large) - Preview/inspector
    - 128x128 (small) - List view icons
    """

    # Standard thumbnail sizes
    SIZES = {
        "xlarge": (1280, 1280),
        "large": (512, 512),
        "small": (128, 128),
    }

    # Naming convention: {hash}_{size}.png
    # Example: abc123def456_1280.png, abc123def456_512.png, abc123def456_128.png

    def __init__(self) -> None:
        """Initialize the thumbnail resizer."""
        self.logger = get_logger(__name__)

    def resize_and_save(
        self,
        source_image_path: Path,
        file_hash: str,
        output_dir: Path,
        sizes: Optional[Dict[str, Tuple[int, int]]] = None,
    ) -> Dict[str, Path]:
        """
        Resize a source image to multiple sizes and save them.

        Args:
            source_image_path: Path to the source 1280x1280 image
            file_hash: Hash of the model file (for naming)
            output_dir: Directory to save resized images
            sizes: Optional dict of size_name -> (width, height).
                   Defaults to SIZES if not provided.

        Returns:
            Dict mapping size_name to output Path for each generated size
        """
        if sizes is None:
            sizes = self.SIZES

        output_paths = {}

        try:
            # Open the source image
            if not source_image_path.exists():
                self.logger.error("Source image not found: %s", source_image_path)
                return output_paths

            source_image = Image.open(source_image_path)
            self.logger.debug("Opened source image: %s", source_image.size)

            # Generate each size
            for size_name, (width, height) in sizes.items():
                try:
                    # Resize using high-quality resampling
                    resized = source_image.resize((width, height), Image.Resampling.LANCZOS)

                    # Save with size suffix in filename
                    output_path = output_dir / f"{file_hash}_{width}.png"
                    resized.save(output_path, "PNG", optimize=True)

                    output_paths[size_name] = output_path
                    self.logger.debug("Saved %s thumbnail: {output_path}", size_name)

                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.error("Failed to resize to %s ({width}x{height}): {e}", size_name)

            return output_paths

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to resize thumbnails: %s", e, exc_info=True)
            return output_paths

    def get_thumbnail_path(self, file_hash: str, output_dir: Path, size: str = "xlarge") -> Path:
        """
        Get the path for a specific thumbnail size.

        Args:
            file_hash: Hash of the model file
            output_dir: Directory where thumbnails are stored
            size: Size name ('xlarge', 'large', 'small')

        Returns:
            Path to the thumbnail file
        """
        if size not in self.SIZES:
            self.logger.warning("Unknown size: %s, defaulting to xlarge", size)
            size = "xlarge"

        width, height = self.SIZES[size]
        return output_dir / f"{file_hash}_{width}.png"

    def get_all_thumbnail_paths(self, file_hash: str, output_dir: Path) -> Dict[str, Path]:
        """
        Get paths for all available thumbnail sizes.

        Args:
            file_hash: Hash of the model file
            output_dir: Directory where thumbnails are stored

        Returns:
            Dict mapping size_name to Path for each size
        """
        paths = {}
        for size_name in self.SIZES:
            path = self.get_thumbnail_path(file_hash, output_dir, size_name)
            if path.exists():
                paths[size_name] = path
        return paths

    def cleanup_old_sizes(
        self, file_hash: str, output_dir: Path, keep_sizes: Optional[list] = None
    ) -> None:
        """
        Clean up old thumbnail files for a given hash.

        Useful for migrating from old single-size system to new multi-size system.

        Args:
            file_hash: Hash of the model file
            output_dir: Directory where thumbnails are stored
            keep_sizes: List of size names to keep. If None, keeps all standard sizes.
        """
        if keep_sizes is None:
            keep_sizes = list(self.SIZES.keys())

        try:
            # Find all files matching this hash
            for file_path in output_dir.glob(f"{file_hash}*"):
                # Check if this is a size we want to keep
                should_keep = False
                for size_name in keep_sizes:
                    width, height = self.SIZES[size_name]
                    if file_path.name == f"{file_hash}_{width}.png":
                        should_keep = True
                        break

                # Also keep the old single-size format for backward compatibility
                if file_path.name == f"{file_hash}.png":
                    should_keep = True

                if not should_keep:
                    file_path.unlink()
                    self.logger.debug("Cleaned up old thumbnail: %s", file_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to cleanup old thumbnails: %s", e)
