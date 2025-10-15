"""
Material manager for procedural wood textures and application to VTK actors.

Responsibilities:
- Query wood species from the database (names and full records)
- Procedurally generate wood grain textures (ring and straight patterns)
- Cache textures to avoid regeneration
- Apply generated textures and material properties to VTK actors
- Log timings and handle errors gracefully

Performance targets:
- 512x512 texture generation < 100ms on typical desktop
"""

import time
from typing import Tuple, Dict, Optional, Any, List

import numpy as np
import vtk
from vtk.util import numpy_support as vtk_np

from core.logging_config import get_logger


class MaterialManager:
    def __init__(self, database_manager):
        """Initialize with database manager reference"""
        self.db = database_manager
        self.logger = get_logger(__name__)
        self.texture_cache: Dict[Tuple[str, Tuple[int, int]], np.ndarray] = {}  # Cache generated textures

    # -------------------------
    # Public API
    # -------------------------

    def get_species_list(self) -> List[str]:
        """Get all wood species from database."""
        try:
            rows = self.db.get_wood_materials()
            return [str(r.get("name")) for r in rows]
        except Exception as e:
            self.logger.error(f"get_species_list failed: {e}")
            return []

    def generate_wood_texture(self, species_name: str, size: Tuple[int, int] = (512, 512)) -> np.ndarray:
        """
        Generate procedural wood texture as an RGB uint8 numpy array (H, W, 3).
        Uses cached result when available.
        """
        try:
            w = int(max(2, size[0]))
            h = int(max(2, size[1]))
            key = (species_name, (w, h))

            # Cache hit
            if key in self.texture_cache:
                self.logger.debug(f"Texture cache hit for species='{species_name}' size={w}x{h}")
                return self.texture_cache[key]

            species = self._get_species(species_name)
            if species is None:
                self.logger.warning(f"Species '{species_name}' not found; using fallback 'Oak'")
                species = self._fallback_species()

            t0 = time.perf_counter()
            img = self._generate_wood_texture_impl(species, (w, h))
            dt_ms = (time.perf_counter() - t0) * 1000.0
            self.logger.info(f"Generated wood texture for '{species.get('name','?')}' in {dt_ms:.2f} ms ({w}x{h})")

            # Cache
            self.texture_cache[key] = img
            return img
        except Exception as e:
            self.logger.error(f"generate_wood_texture error: {e}", exc_info=True)
            # Fallback to a flat color image (light grey) to avoid breaking rendering
            w, h = int(size[0]), int(size[1])
            return np.full((h, w, 3), 200, dtype=np.uint8)

    def apply_material_to_actor(self, actor: vtk.vtkActor, species_name: str) -> bool:
        """
        Apply wood material to VTK actor:
        - Generates/uses cached texture
        - Creates vtkTexture and applies to actor
        - Sets roughness/specular from species data (PBR when available)
        """
        if actor is None:
            self.logger.warning("apply_material_to_actor called with None actor")
            return False

        try:
            species = self._get_species(species_name)
            if species is None:
                self.logger.warning(f"Species '{species_name}' not found; using fallback 'Oak'")
                species = self._fallback_species()

            # Generate (or fetch cached) texture data
            img = self.generate_wood_texture(species.get("name", species_name), size=(512, 512))

            # Convert to vtkImageData
            vtk_img = self._numpy_to_vtk_image(img)

            # Create vtkTexture
            texture = vtk.vtkTexture()
            texture.SetInputData(vtk_img)
            try:
                texture.InterpolateOn()
            except Exception:
                pass
            try:
                texture.MipmapOn()
            except Exception:
                pass
            try:
                texture.RepeatOn()
            except Exception:
                pass

            # Assign texture
            actor.SetTexture(texture)

            # Configure material/shading
            self._apply_material_properties(actor, species)

            # Best-effort: request a render if we can find a renderer
            self._render_actor_scene(actor)

            self.logger.info(f"Applied material '{species.get('name','?')}' to actor")
            return True
        except Exception as e:
            self.logger.error(f"apply_material_to_actor error: {e}", exc_info=True)
            return False

    def clear_texture_cache(self) -> None:
        """Clear cached textures."""
        self.texture_cache.clear()
        self.logger.debug("MaterialManager texture cache cleared")

    # -------------------------
    # Internal utilities
    # -------------------------

    def _get_species(self, name: str) -> Optional[Dict[str, Any]]:
        """Lookup species by name, case-sensitive in DB."""
        try:
            if not name:
                return None
            return self.db.get_wood_material_by_name(name)
        except Exception as e:
            self.logger.error(f"_get_species('{name}') failed: {e}")
            return None

    def _fallback_species(self) -> Dict[str, Any]:
        """Return first default species or a baked-in Oak fallback."""
        try:
            rows = self.db.get_wood_materials()
            if rows:
                # Prefer defaults first (schema orders defaults first)
                return rows[0]
        except Exception:
            pass
        # Hard fallback (values in [0,1])
        return {
            "name": "Oak",
            "base_color_r": 0.757, "base_color_g": 0.604, "base_color_b": 0.420,
            "grain_color_r": 0.545, "grain_color_g": 0.451, "grain_color_b": 0.333,
            "grain_scale": 1.0, "grain_pattern": "ring",
            "roughness": 0.5, "specular": 0.3
        }

    def _generate_wood_texture_impl(self, species: Dict[str, Any], size: Tuple[int, int]) -> np.ndarray:
        """
        Vectorized procedural texture generation.
        Implements:
        - Two grain patterns: 'ring' (circular) and 'straight' (linear)
        - Adds multi-octave value noise for natural variation
        - Mixes base and grain colors using a sinusoidal grain function perturbed by noise
        """
        w, h = int(size[0]), int(size[1])

        # Colors as floats [0,1]
        base = np.array([
            float(species.get("base_color_r", 0.7)),
            float(species.get("base_color_g", 0.55)),
            float(species.get("base_color_b", 0.4)),
        ], dtype=np.float32)
        grain = np.array([
            float(species.get("grain_color_r", 0.5)),
            float(species.get("grain_color_g", 0.4)),
            float(species.get("grain_color_b", 0.3)),
        ], dtype=np.float32)

        pattern = str(species.get("grain_pattern", "ring")).lower().strip()
        grain_scale = float(species.get("grain_scale", 1.0))
        grain_scale = 1.0 if grain_scale <= 0.0 else grain_scale

        # Coordinate grids normalized to [-1, 1]
        xs = np.linspace(-1.0, 1.0, w, dtype=np.float32)
        ys = np.linspace(-1.0, 1.0, h, dtype=np.float32)
        X, Y = np.meshgrid(xs, ys)

        # Multi-octave value noise (fast, fully vectorized)
        seed = abs(hash(species.get("name", "wood"))) % (2**31 - 1)
        noise = self._fbm_value_noise(h, w, octaves=3, base_cells=8, lacunarity=2.0, gain=0.5, seed=seed)
        # Map noise to [-1, 1]
        noise = (noise * 2.0) - 1.0

        # Grain function
        if pattern == "straight":
            # Straight grain aligned with Y (vertical)
            freq = 10.0 * grain_scale
            phase = (Y * freq * np.pi) + (noise * 0.8)
            grain_mask = 0.5 * (1.0 + np.sin(phase * 2.0))  # [0..1]
        else:
            # Ring-like grain based on radial distance
            R = np.sqrt(X * X + Y * Y)
            freq = 12.0 * grain_scale
            phase = (R * freq * np.pi) + (noise * 0.9)
            grain_mask = 0.5 * (1.0 + np.sin(phase * 2.0))  # [0..1]

        # Slight contrast shaping for more natural look
        grain_mask = np.clip(grain_mask, 0.0, 1.0).astype(np.float32)
        grain_mask = np.power(grain_mask, 0.85).astype(np.float32)

        # Color mix
        img_f = (base[None, None, :] * (1.0 - grain_mask[..., None])) + (grain[None, None, :] * grain_mask[..., None])
        img_f = np.clip(img_f, 0.0, 1.0)

        # Convert to uint8 RGB image
        img_u8 = (img_f * 255.0 + 0.5).astype(np.uint8)
        return img_u8

    def _fbm_value_noise(
        self,
        h: int,
        w: int,
        octaves: int = 3,
        base_cells: int = 8,
        lacunarity: float = 2.0,
        gain: float = 0.5,
        seed: int = 12345,
    ) -> np.ndarray:
        """
        Fast, fully vectorized 2D value noise with bilinear interpolation, summed as FBM.
        Returns array in [0,1].
        """
        rng = np.random.RandomState(seed)
        total = np.zeros((h, w), dtype=np.float32)
        amplitude = 1.0
        norm = 0.0

        for i in range(max(1, int(octaves))):
            cells = int(base_cells * (lacunarity ** i))
            cells = max(1, cells)

            # Random lattice (cells+1 for inclusive bilinear)
            grid = rng.rand(cells + 1, cells + 1).astype(np.float32)

            # Sample coordinates in lattice space
            xs = np.linspace(0.0, float(cells), w, endpoint=False, dtype=np.float32)
            ys = np.linspace(0.0, float(cells), h, endpoint=False, dtype=np.float32)
            x0 = np.floor(xs).astype(np.int32)
            y0 = np.floor(ys).astype(np.int32)
            x1 = np.clip(x0 + 1, 0, cells)
            y1 = np.clip(y0 + 1, 0, cells)

            sx = (xs - x0).astype(np.float32)  # (W,)
            sy = (ys - y0).astype(np.float32)  # (H,)

            # Gather corners via broadcasting
            n00 = grid[np.ix_(y0, x0)]  # (H, W)
            n10 = grid[np.ix_(y0, x1)]
            n01 = grid[np.ix_(y1, x0)]
            n11 = grid[np.ix_(y1, x1)]

            sx_row = sx[None, :]  # (1, W)
            sy_col = sy[:, None]  # (H, 1)

            ix0 = n00 * (1.0 - sx_row) + n10 * sx_row
            ix1 = n01 * (1.0 - sx_row) + n11 * sx_row
            val = ix0 * (1.0 - sy_col) + ix1 * sy_col  # (H, W) in [0,1]

            total += val * amplitude
            norm += amplitude
            amplitude *= gain

        if norm > 0:
            total /= norm
        return np.clip(total, 0.0, 1.0)

    def _numpy_to_vtk_image(self, img: np.ndarray) -> vtk.vtkImageData:
        """
        Convert an RGB uint8 image (H, W, 3) to vtkImageData.
        """
        if img.dtype != np.uint8:
            img = np.clip(img, 0, 255).astype(np.uint8)

        h, w, c = img.shape
        if c != 3:
            raise ValueError("Expected RGB image with 3 channels")

        # Optional: Flip to match VTK's bottom-left origin if needed
        img_src = np.ascontiguousarray(img)  # (H, W, 3)

        vtk_image = vtk.vtkImageData()
        vtk_image.SetDimensions(w, h, 1)
        vtk_image.SetExtent(0, w - 1, 0, h - 1, 0, 0)
        vtk_image.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 3)

        flat = img_src.reshape(-1, 3)
        vtk_arr = vtk_np.numpy_to_vtk(flat, deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
        vtk_image.GetPointData().SetScalars(vtk_arr)
        return vtk_image

    def _apply_material_properties(self, actor: vtk.vtkActor, species: Dict[str, Any]) -> None:
        """
        Configure actor property using roughness and specular. Use PBR when available.
        """
        try:
            roughness = float(species.get("roughness", 0.5))
            roughness = max(0.0, min(1.0, roughness))
        except Exception:
            roughness = 0.5

        try:
            specular = float(species.get("specular", 0.3))
            specular = max(0.0, min(1.0, specular))
        except Exception:
            specular = 0.3

        try:
            prop = actor.GetProperty()
            # Prefer PBR if the VTK build supports it
            if hasattr(prop, "SetInterpolationToPBR"):
                try:
                    prop.SetInterpolationToPBR()
                    # Metallic-roughness workflow; wood is non-metallic
                    if hasattr(prop, "SetMetallic"):
                        prop.SetMetallic(0.0)
                    if hasattr(prop, "SetRoughness"):
                        prop.SetRoughness(roughness)
                    # Some builds still honor Specular even in PBR
                    if hasattr(prop, "SetSpecular"):
                        prop.SetSpecular(specular)
                except Exception:
                    # Fallback to Phong-like classic shading
                    self._apply_classic_shading(prop, roughness, specular)
            else:
                self._apply_classic_shading(prop, roughness, specular)
        except Exception as e:
            self.logger.warning(f"_apply_material_properties failed: {e}")

    def _apply_classic_shading(self, prop: vtk.vtkProperty, roughness: float, specular: float) -> None:
        """
        Approximate roughness via specular power mapping for classic shading.
        """
        try:
            # Map roughness in [0,1] to a specular power range [5, 40] (lower = rougher)
            spec_power = 40.0 - (roughness * 35.0)
            prop.SetAmbient(0.2)
            prop.SetDiffuse(0.8)
            prop.SetSpecular(specular)
            prop.SetSpecularPower(spec_power)
            try:
                prop.LightingOn()
            except Exception:
                pass
        except Exception:
            pass

    def _render_actor_scene(self, actor: vtk.vtkActor) -> None:
        """
        Best-effort attempt to trigger a render after applying materials.
        """
        try:
            # Attempt to locate a renderer via the actor's mapper & render window
            mapper = actor.GetMapper()
            if mapper is None:
                return
            # Actor -> Mapper has no direct link to renderer; try common pattern where the app uses a single renderer
            # This function remains best-effort: no exception should propagate.
            # If a global/current renderer is accessible through the mapper input's producer, it could be used,
            # but generally the viewer will re-render on the UI thread.
            pass
        except Exception:
            pass