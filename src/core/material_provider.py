"""
Material Provider for Texture Discovery

This module dynamically discovers material texture images from the resources/materials folder.
Replaces procedural grain generation with actual texture files.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.core.logging_config import get_logger


class MaterialProvider:
    """
    Manage material textures by discovering them from the resources/materials directory.

    Features:
    - Dynamic discovery of material texture images
    - No hardcoded filenames
    - Supports PNG, JPG texture files
    - MTL file parsing for material properties
    """

    # Default materials directory
    DEFAULT_MATERIALS_DIR = Path(__file__).parent.parent / "resources" / "materials"

    def __init__(self) -> None:
        """Initialize the material provider."""
        self.logger = get_logger(__name__)
        self.logger.info("MaterialProvider initialized")
        self._materials_cache: List[Dict[str, any]] = []
        self._materials_index: Dict[str, Dict[str, any]] = {}
        self._manifest_path = self.DEFAULT_MATERIALS_DIR / ".materials_manifest.json"
        self._manifest: Dict[str, Dict[str, any]] = {}
        self._dirty = True
        self._watcher = None
        self._load_manifest()
        self._start_watcher()

    def get_available_materials(self) -> List[Dict[str, any]]:
        """
        Dynamically discover all available material textures.

        Scans the materials directory for PNG/JPG files and MTL files.

        Returns:
            List of material dictionaries with name, texture_path, and properties
        """
        try:
            if not self.DEFAULT_MATERIALS_DIR.exists():
                self.logger.warning(
                    "Materials directory not found: %s", self.DEFAULT_MATERIALS_DIR
                )
                return []

            self._ensure_cache()
            return list(self._materials_cache)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error discovering materials: %s", e, exc_info=True)
            return []

    def get_material_by_name(self, name: str) -> Optional[Dict[str, any]]:
        """
        Get a specific material by name.

        Args:
            name: Material name (filename without extension)

        Returns:
            Material info dictionary or None if not found
        """
        try:
            self.logger.debug(
                f"[STL_TEXTURE_DEBUG] Looking for material with name: '{name}'"
            )
            materials = self.get_available_materials()
            self.logger.debug(
                "[STL_TEXTURE_DEBUG] Found %s available materials", len(materials)
            )

            material = self._materials_index.get(name.lower())
            if material:
                self.logger.info(
                    f"[STL_TEXTURE_DEBUG] Found material '{name}' with texture_path: {material.get('texture_path')}"
                )
                return material

            self.logger.warning(
                f"[STL_TEXTURE_DEBUG] Material '{name}' not found in {len(materials)} materials, returning solid-color fallback"
            )
            return {
                "name": name,
                "texture_path": None,
                "mtl_path": None,
                "properties": {},
                "fallback": True,
            }

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                f"[STL_TEXTURE_DEBUG] Error getting material '{name}': {e}",
                exc_info=True,
            )
            return {
                "name": name,
                "texture_path": None,
                "mtl_path": None,
                "properties": {},
                "fallback": True,
            }

    def get_material_texture_path(self, name: str) -> Optional[Path]:
        """
        Get the texture image path for a material.

        Args:
            name: Material name

        Returns:
            Path to texture image or None if not found
        """
        material = self.get_material_by_name(name)
        if material:
            return material.get("texture_path")
        return None

    def refresh_materials(self, force: bool = False) -> None:
        """
        Manually trigger a material refresh (UI hook).

        Args:
            force: Force rebuild even if cache is not marked dirty.
        """
        self._dirty = True
        self._ensure_cache(force_rebuild=force)

    def _parse_mtl_file(self, mtl_path: Path) -> Dict[str, any]:
        """
        Parse an MTL file to extract material properties.

        Args:
            mtl_path: Path to MTL file

        Returns:
            Dictionary of material properties
        """
        properties = {}

        try:
            self.logger.debug("Starting to parse MTL file: %s", mtl_path)
            with open(mtl_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith("#"):
                        continue

                    self.logger.debug("Parsing line %s: %s", line_num, line)

                    # Parse material properties
                    if line.startswith("newmtl"):
                        # Material name
                        parts = line.split(maxsplit=1)
                        if len(parts) > 1:
                            properties["material_name"] = parts[1]
                            self.logger.debug("Found material name: %s", parts[1])

                    elif line.startswith("Ns"):
                        # Specular exponent (shininess)
                        try:
                            properties["shininess"] = float(line.split()[1])
                            self.logger.debug(
                                "Found shininess: %s", properties["shininess"]
                            )
                        except (IndexError, ValueError) as e:
                            self.logger.warning("Failed to parse Ns value: %s", e)

                    elif line.startswith("Ka"):
                        # Ambient color
                        try:
                            parts = line.split()
                            properties["ambient"] = (
                                float(parts[1]),
                                float(parts[2]),
                                float(parts[3]),
                            )
                            self.logger.debug(
                                "Found ambient color: %s", properties["ambient"]
                            )
                        except (IndexError, ValueError) as e:
                            self.logger.warning("Failed to parse Ka values: %s", e)

                    elif line.startswith("Kd"):
                        # Diffuse color
                        try:
                            parts = line.split()
                            properties["diffuse"] = (
                                float(parts[1]),
                                float(parts[2]),
                                float(parts[3]),
                            )
                            self.logger.debug(
                                "Found diffuse color: %s", properties["diffuse"]
                            )
                        except (IndexError, ValueError) as e:
                            self.logger.warning("Failed to parse Kd values: %s", e)

                    elif line.startswith("Ks"):
                        # Specular color
                        try:
                            parts = line.split()
                            properties["specular"] = (
                                float(parts[1]),
                                float(parts[2]),
                                float(parts[3]),
                            )
                            self.logger.debug(
                                "Found specular color: %s", properties["specular"]
                            )
                        except (IndexError, ValueError) as e:
                            self.logger.warning("Failed to parse Ks values: %s", e)

                    elif line.startswith("map_Kd"):
                        # Diffuse texture map
                        parts = line.split(maxsplit=1)
                        if len(parts) > 1:
                            texture_path = parts[1]
                            properties["diffuse_map"] = texture_path
                            self.logger.debug(
                                "Found diffuse texture map: %s", texture_path
                            )

                            # Resolve relative path
                            if not Path(texture_path).is_absolute():
                                resolved_path = mtl_path.parent / texture_path
                                properties["diffuse_map_resolved"] = str(resolved_path)
                                self.logger.debug(
                                    f"Resolved relative texture path: {texture_path} -> {resolved_path}"
                                )
                                if resolved_path.exists():
                                    self.logger.debug(
                                        f"Resolved texture path exists: {resolved_path}"
                                    )
                                else:
                                    self.logger.warning(
                                        f"Resolved texture path does not exist: {resolved_path}"
                                    )
                            else:
                                properties["diffuse_map_resolved"] = texture_path
                                self.logger.debug(
                                    "Absolute texture path: %s", texture_path
                                )

            self.logger.info(
                "Parsed MTL file: %s with %s properties", mtl_path.name, len(properties)
            )
            self.logger.debug("Final properties: %s", properties)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                "Error parsing MTL file %s: %s", mtl_path, e, exc_info=True
            )

        return properties

    def validate_texture(self, texture_path: Path) -> bool:
        """
        Validate that a texture file exists and is readable.

        Args:
            texture_path: Path to texture file

        Returns:
            True if valid, False otherwise
        """
        try:
            if not texture_path.exists():
                self.logger.warning("Texture file not found: %s", texture_path)
                return False

            if not texture_path.is_file():
                self.logger.warning("Texture path is not a file: %s", texture_path)
                return False

            # Check extension
            supported_extensions = {".png", ".jpg", ".jpeg", ".bmp"}
            if texture_path.suffix.lower() not in supported_extensions:
                self.logger.warning(
                    "Unsupported texture format: %s", texture_path.suffix
                )
                return False

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error validating texture: %s", e, exc_info=True)
            return False

    # ---- Internal helpers ----

    def _ensure_cache(self, force_rebuild: bool = False) -> None:
        """Rebuild the cache if marked dirty or if forced."""
        if not self._dirty and not force_rebuild:
            return
        self._rebuild_cache()
        self._dirty = False

    def _rebuild_cache(self) -> None:
        """Scan the materials directory and update cache/manifest."""
        materials: List[Dict[str, any]] = []
        index: Dict[str, Dict[str, any]] = {}
        manifest_changed = False

        image_extensions = {".png", ".jpg", ".jpeg"}
        texture_files = [
            f
            for f in self.DEFAULT_MATERIALS_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]

        for texture_file in texture_files:
            material_name = texture_file.stem
            mtl_file = texture_file.with_suffix(".mtl")

            cached_entry = self._manifest.get(material_name, {})
            texture_sig = self._file_signature(texture_file)
            mtl_sig = self._file_signature(mtl_file) if mtl_file.exists() else None

            reuse_cached = (
                cached_entry.get("texture_sig") == texture_sig
                and cached_entry.get("mtl_sig") == mtl_sig
                and "properties" in cached_entry
            )

            properties: Dict[str, any] = {}
            if reuse_cached:
                properties = cached_entry.get("properties", {})
            elif mtl_file.exists():
                properties = self._parse_mtl_file(mtl_file)
                manifest_changed = True

            material_info = {
                "name": material_name,
                "texture_path": texture_file,
                "mtl_path": mtl_file if mtl_file.exists() else None,
                "properties": properties,
            }

            materials.append(material_info)
            index[material_name.lower()] = material_info

            # Update manifest entry
            self._manifest[material_name] = {
                "texture_sig": texture_sig,
                "mtl_sig": mtl_sig,
                "properties": properties,
            }
            manifest_changed = True

        self._materials_cache = sorted(materials, key=lambda m: m["name"])
        self._materials_index = index

        if manifest_changed:
            self._save_manifest()

    def _file_signature(self, path: Path) -> Optional[Tuple[float, int, str]]:
        """Return (mtime, size, sha1) signature for change detection."""
        try:
            path_stat = path.stat()
            sha1 = hashlib.sha1(path.read_bytes()).hexdigest()
            return (path_stat.st_mtime, path_stat.st_size, sha1)
        except FileNotFoundError:
            return None
        except (OSError, IOError) as exc:
            self.logger.debug("Failed to stat/hash %s: %s", path, exc)
            return None

    def _load_manifest(self) -> None:
        """Load manifest file if present."""
        if not self._manifest_path.exists():
            self._manifest = {}
            return
        try:
            data = json.loads(self._manifest_path.read_text(encoding="utf-8"))
            self._manifest = data.get("materials", {})
        except (OSError, IOError, ValueError, TypeError) as exc:
            self.logger.debug("Failed to load material manifest: %s", exc)
            self._manifest = {}

    def _save_manifest(self) -> None:
        """Persist manifest to disk."""
        try:
            payload = {"materials": self._manifest}
            self._manifest_path.parent.mkdir(parents=True, exist_ok=True)
            self._manifest_path.write_text(
                json.dumps(payload, indent=2), encoding="utf-8"
            )
        except (OSError, IOError, ValueError, TypeError) as exc:
            self.logger.debug("Failed to save material manifest: %s", exc)

    def _start_watcher(self) -> None:
        """Start a QFileSystemWatcher to invalidate cache on changes (best effort)."""
        try:
            from PySide6.QtCore import QFileSystemWatcher

            watcher = QFileSystemWatcher()
            watcher.addPath(str(self.DEFAULT_MATERIALS_DIR))
            watcher.directoryChanged.connect(self._on_materials_changed)  # type: ignore[attr-defined]
            watcher.fileChanged.connect(self._on_materials_changed)  # type: ignore[attr-defined]
            self._watcher = watcher
            self.logger.debug(
                "Material directory watch enabled at %s", self.DEFAULT_MATERIALS_DIR
            )
        except Exception as exc:  # pragma: no cover - watcher is best-effort
            self.logger.debug("Material directory watch not enabled: %s", exc)
            self._watcher = None

    def _on_materials_changed(self, *_args) -> None:
        """Mark cache dirty when a file change is observed."""
        self.logger.debug("Material directory change detected; marking cache dirty")
        self._dirty = True
