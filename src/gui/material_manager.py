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

DEBUGGING MTL FILE ISSUES:
This module is being debugged for MTL file application problems. Added comprehensive logging to:
- MaterialProvider._parse_mtl_file: Track MTL parsing and path resolution
- MaterialManager.generate_wood_texture: Track texture loading vs procedural generation
- MaterialManager.apply_material_to_actor: Track VTK texture application process
"""

import time
from pathlib import Path
from typing import Tuple, Dict, Optional, Any, List

import numpy as np
import vtk
from vtk.util import numpy_support as vtk_np

from src.core.logging_config import get_logger
from src.core.material_provider import MaterialProvider


class MaterialManager:
    def __init__(self, database_manager):
        """Initialize with database manager reference"""
        self.db = database_manager
        self.logger = get_logger(__name__)
        self.texture_cache: Dict[Tuple[str, Tuple[int, int]], np.ndarray] = {}  # Cache generated textures
        self.material_provider = MaterialProvider()  # For texture discovery

    # -------------------------
    # Public API
    # -------------------------

    def get_species_list(self) -> List[str]:
        """Get all wood species from database and material provider."""
        try:
            # Get database species
            db_species = [str(r.get("name")) for r in self.db.get_wood_materials()]

            # Get texture materials
            texture_materials = self.material_provider.get_available_materials()
            texture_names = [m['name'] for m in texture_materials]

            # Combine and deduplicate
            all_species = list(set(db_species + texture_names))
            return sorted(all_species)
        except Exception as e:
            self.logger.error(f"get_species_list failed: {e}")
            return []

    def generate_wood_texture(self, species_name: str, size: Tuple[int, int] = (512, 512)) -> np.ndarray:
        """
        Generate wood texture as an RGB uint8 numpy array (H, W, 3).
        First tries to load from material provider, raises error if not found.
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

            # Load from material provider - no fallback to procedural generation
            material = self.material_provider.get_material_by_name(species_name)
            if material:
                self.logger.debug(f"Material provider returned material for '{species_name}': {material}")
                texture_path = material.get('texture_path')
                if texture_path:
                    self.logger.info(f"Found texture path for '{species_name}': {texture_path}")
                    try:
                        # Load actual texture image
                        img = self._load_texture_image(texture_path, (w, h))
                        self.logger.info(f"Successfully loaded texture image for '{species_name}' from {texture_path}, shape: {img.shape}")
                        self.texture_cache[key] = img
                        return img
                    except Exception as e:
                        error_msg = f"Failed to load texture for '{species_name}' from {texture_path}: {e}"
                        self.logger.error(error_msg)
                        raise RuntimeError(error_msg)
                else:
                    error_msg = f"No texture_path found for '{species_name}' in material: {material}"
                    self.logger.error(error_msg)
                    raise RuntimeError(error_msg)
            else:
                error_msg = f"No material found for '{species_name}' from material provider"
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)

            # No fallback to procedural generation
            raise RuntimeError(f"MTL texture loading is mandatory - no procedural fallback available for '{species_name}'")
        except Exception as e:
            self.logger.error(f"generate_wood_texture error: {e}", exc_info=True)
            # No fallback - MTL texture loading is mandatory
            raise RuntimeError(f"MTL texture loading failed: {e}")

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
            self.logger.info(f"Starting to apply material '{species_name}' to actor")
            
            # DIAGNOSTIC LOG: Check if actor has UV coordinates (needed for texture mapping)
            has_uv_coords = False
            mapper = actor.GetMapper()
            if mapper:
                input_data = mapper.GetInput()
                if input_data:
                    point_data = input_data.GetPointData()
                    if point_data:
                        has_uv_coords = point_data.GetTCoords() is not None
                        self.logger.debug(f"[STL_TEXTURE_DEBUG] Actor has UV coordinates: {has_uv_coords}")
            
            # For STL files, we'll apply texture even without UV coordinates
            if not has_uv_coords:
                self.logger.info(f"[STL_TEXTURE_DEBUG] Actor missing UV coordinates - applying texture without UV mapping")

            # Get material from material provider to check for texture
            material = self.material_provider.get_material_by_name(species_name)
            if material:
                self.logger.debug(f"[STL_TEXTURE_DEBUG] Material found: {material}")
                texture_path = material.get('texture_path')
                if texture_path:
                    self.logger.info(f"[STL_TEXTURE_DEBUG] Material has texture path: {texture_path}")
                else:
                    self.logger.warning(f"[STL_TEXTURE_DEBUG] Material has no texture path")
            else:
                self.logger.warning(f"[STL_TEXTURE_DEBUG] No material found for species: {species_name}")

            # For STL models, use MTL properties instead of database species
            # This ensures the texture and material properties match
            if material and material.get('properties') and material.get('texture_path'):
                self.logger.info(f"[STL_TEXTURE_DEBUG] Using MTL properties for '{species_name}' instead of database")
                # Create a species dict from MTL properties
                mtl_props = material.get('properties', {})
                species = {
                    'name': species_name,
                    'base_color_r': mtl_props.get('diffuse', (0.7, 0.7, 0.7))[0],
                    'base_color_g': mtl_props.get('diffuse', (0.7, 0.7, 0.7))[1],
                    'base_color_b': mtl_props.get('diffuse', (0.7, 0.7, 0.7))[2],
                    'grain_color_r': mtl_props.get('specular', (0.5, 0.5, 0.5))[0],
                    'grain_color_g': mtl_props.get('specular', (0.5, 0.5, 0.5))[1],
                    'grain_color_b': mtl_props.get('specular', (0.5, 0.5, 0.5))[2],
                    'grain_scale': 1.0,
                    'grain_pattern': 'ring',
                    'roughness': 0.5,
                    'specular': mtl_props.get('specular', (0.5, 0.5, 0.5))[0],
                    'shininess': mtl_props.get('shininess', 50.0) / 50.0  # Normalize to [0,1]
                }
                self.logger.debug(f"[STL_TEXTURE_DEBUG] Created species from MTL: {species}")
                
                # Use the MTL texture directly instead of calling generate_wood_texture
                # which would fall back to procedural generation
                try:
                    texture_path = material.get('texture_path')
                    if texture_path:
                        self.logger.info(f"[STL_TEXTURE_DEBUG] ===== LOADING MTL TEXTURE =====")
                        self.logger.info(f"[STL_TEXTURE_DEBUG] Loading MTL texture directly from: {texture_path}")
                        
                        # NEW DIAGNOSTIC: Check if file exists and get file info
                        import os
                        if os.path.exists(texture_path):
                            file_size = os.path.getsize(texture_path)
                            self.logger.info(f"[STL_TEXTURE_DEBUG] Texture file exists, size: {file_size} bytes")
                        else:
                            self.logger.error(f"[STL_TEXTURE_DEBUG] Texture file NOT found: {texture_path}")
                            return False
                        
                        img = self._load_texture_image(texture_path, (512, 512))
                        self.logger.info(f"[STL_TEXTURE_DEBUG] Successfully loaded MTL texture, shape: {img.shape}, dtype: {img.dtype}")
                        
                        # Convert to vtkImageData
                        self.logger.info("[STL_TEXTURE_DEBUG] Converting numpy array to VTK image data")
                        vtk_img = self._numpy_to_vtk_image(img)
                        self.logger.info(f"[STL_TEXTURE_DEBUG] VTK image dimensions: {vtk_img.GetDimensions()}")
                        self.logger.info(f"[STL_TEXTURE_DEBUG] VTK image scalar type: {vtk_img.GetScalarType()}")
                        
                        # Create vtkTexture
                        self.logger.info("[STL_TEXTURE_DEBUG] Creating VTK texture")
                        texture = vtk.vtkTexture()
                        texture.SetInputData(vtk_img)
                        
                        # Configure texture properties
                        try:
                            texture.InterpolateOn()
                            self.logger.info("[STL_TEXTURE_DEBUG] Enabled texture interpolation")
                        except Exception as e:
                            self.logger.warning(f"Failed to enable texture interpolation: {e}")
                        
                        try:
                            texture.MipmapOn()
                            self.logger.info("[STL_TEXTURE_DEBUG] Enabled texture mipmaps")
                        except Exception as e:
                            self.logger.warning(f"Failed to enable texture mipmaps: {e}")
                        
                        try:
                            texture.RepeatOn()
                            self.logger.info("[STL_TEXTURE_DEBUG] Enabled texture repeat")
                        except Exception as e:
                            self.logger.warning(f"Failed to enable texture repeat: {e}")
                        
                        # NEW DIAGNOSTIC: Check texture before assignment
                        self.logger.info(f"[STL_TEXTURE_DEBUG] Texture before assignment - Interpolate: {texture.GetInterpolate()}, Mipmap: {texture.GetMipmap()}, Repeat: {texture.GetRepeat()}")
                        
                        # Assign texture
                        self.logger.info("[STL_TEXTURE_DEBUG] Assigning MTL texture to actor")
                        actor.SetTexture(texture)
                        self.logger.info("[STL_TEXTURE_DEBUG] MTL texture assigned to actor")
                        
                        # Configure material/shading - SPECIAL HANDLING FOR STL TEXTURES
                        self.logger.info("[STL_TEXTURE_DEBUG] Applying MTL material properties to actor")
                        self._apply_material_properties_for_texture(actor, species)
                        
                        # Best-effort: request a render if we can find a renderer
                        self._render_actor_scene(actor)
                        
                        self.logger.info(f"Successfully applied MTL material '{species.get('name','?')}' to actor")
                        
                        # DIAGNOSTIC LOG: Check if texture is properly bound
                        self.logger.info("[STL_TEXTURE_DEBUG] ===== VERIFYING TEXTURE BINDING =====")
                        if actor.GetTexture() is not None:
                            self.logger.info("[STL_TEXTURE_DEBUG] MTL texture successfully bound to actor")
                            # Check texture properties
                            bound_texture = actor.GetTexture()
                            self.logger.info(f"[STL_TEXTURE_DEBUG] Bound texture dimensions: {bound_texture.GetInput().GetDimensions()}")
                            self.logger.info(f"[STL_TEXTURE_DEBUG] Bound texture interpolation: {bound_texture.GetInterpolate()}")
                            self.logger.info(f"[STL_TEXTURE_DEBUG] Bound texture repeat: {bound_texture.GetRepeat()}")
                            self.logger.info(f"[STL_TEXTURE_DEBUG] Bound texture mipmap: {bound_texture.GetMipmap()}")
                            
                            # NEW DIAGNOSTIC: Check actor properties
                            prop = actor.GetProperty()
                            if prop:
                                self.logger.info(f"[STL_TEXTURE_DEBUG] Actor has property, lighting: {prop.GetLighting()}")
                                self.logger.info(f"[STL_TEXTURE_DEBUG] Actor diffuse color: {prop.GetDiffuseColor()}")
                                self.logger.info(f"[STL_TEXTURE_DEBUG] Actor specular color: {prop.GetSpecularColor()}")
                            
                        else:
                            self.logger.error("[STL_TEXTURE_DEBUG] MTL texture failed to bind to actor")
                            
                        self.logger.info("[STL_TEXTURE_DEBUG] ===== MTL TEXTURE APPLICATION COMPLETE =====")
                        return True
                except Exception as e:
                    self.logger.error(f"[STL_TEXTURE_DEBUG] Failed to apply MTL texture: {e}", exc_info=True)
                    # Fall through to solid color approach
            else:
                self.logger.info(f"[STL_TEXTURE_DEBUG] No valid MTL material with texture found for '{species_name}', applying solid color")
                
            # No MTL material found, apply a solid color instead of falling back to database
            self.logger.info(f"[STL_TEXTURE_DEBUG] Applying solid color for '{species_name}' (no database fallback)")
            
            # Use a default solid color (light gray)
            try:
                # Get material properties if available, otherwise use defaults
                if material and material.get('properties'):
                    mtl_props = material.get('properties', {})
                    diffuse_color = mtl_props.get('diffuse', (0.7, 0.7, 0.7))
                    specular_color = mtl_props.get('specular', (0.5, 0.5, 0.5))
                    shininess = mtl_props.get('shininess', 50.0)
                else:
                    # Default gray material
                    diffuse_color = (0.7, 0.7, 0.7)
                    specular_color = (0.5, 0.5, 0.5)
                    shininess = 50.0
                
                # Apply solid color material
                prop = actor.GetProperty()
                prop.SetDiffuseColor(diffuse_color)
                prop.SetSpecularColor(specular_color)
                prop.SetAmbientColor(0.2, 0.2, 0.2)
                prop.SetSpecular(shininess / 100.0)  # Normalize to [0,1]
                prop.SetShininess(shininess)
                prop.LightingOn()
                
                # Remove any existing texture
                actor.SetTexture(None)
                
                self.logger.info(f"[STL_TEXTURE_DEBUG] Applied solid color material for '{species_name}'")
                return True
                
            except Exception as e:
                self.logger.error(f"[STL_TEXTURE_DEBUG] Failed to apply solid color: {e}", exc_info=True)
                return False
        except Exception as e:
            self.logger.error(f"apply_material_to_actor error for species '{species_name}': {e}", exc_info=True)
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

    def _apply_material_properties_for_texture(self, actor: vtk.vtkActor, species: Dict[str, Any]) -> None:
        """
        Configure actor properties for textured materials.
        This is a special version that preserves texture visibility while still applying
        appropriate material properties for lighting and shininess.
        """
        try:
            self.logger.info("[STL_TEXTURE_DEBUG] Applying texture-safe material properties")
            
            roughness = float(species.get("roughness", 0.5))
            roughness = max(0.0, min(1.0, roughness))
            
            specular = float(species.get("specular", 0.3))
            specular = max(0.0, min(1.0, specular))
            
            prop = actor.GetProperty()
            
            # KEY FIX: For textured materials, we need to set the base color to white
            # and let the texture provide the actual color. Setting diffuse to non-white
            # will tint/override the texture.
            prop.SetAmbientColor(1.0, 1.0, 1.0)  # White ambient
            prop.SetDiffuseColor(1.0, 1.0, 1.0)   # White diffuse - KEY FIX!
            prop.SetSpecularColor(specular, specular, specular)  # Use specular from material
            
            # Set shininess from material
            shininess = float(species.get("shininess", 5.0))
            shininess = max(1.0, min(100.0, shininess))
            prop.SetShininess(shininess)
            
            # Enable lighting but ensure texture is visible
            prop.LightingOn()
            
            # Set appropriate specular power for textured materials
            spec_power = 40.0 - (roughness * 35.0)
            prop.SetSpecularPower(spec_power)
            
            self.logger.info(f"[STL_TEXTURE_DEBUG] Applied texture-safe properties: shininess={shininess}, specular={specular}")
            self.logger.info(f"[STL_TEXTURE_DEBUG] Actor colors after texture-safe application: diffuse={prop.GetDiffuseColor()}, ambient={prop.GetAmbientColor()}")
            
        except Exception as e:
            self.logger.warning(f"_apply_material_properties_for_texture failed: {e}")

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

    def _load_texture_image(self, texture_path: Path, size: Tuple[int, int]) -> np.ndarray:
        """
        Load and resize a texture image from file.

        Args:
            texture_path: Path to the texture image file
            size: Desired output size (width, height)

        Returns:
            RGB uint8 numpy array (H, W, 3)
        """
        try:
            from PIL import Image
            import cv2

            # Load image with PIL
            img = Image.open(texture_path)

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize to requested size
            img = img.resize(size, Image.Resampling.LANCZOS)

            # Convert to numpy array
            img_array = np.array(img)

            return img_array

        except ImportError:
            # Fallback to OpenCV if PIL not available
            try:
                import cv2
                img = cv2.imread(str(texture_path))
                if img is None:
                    raise ValueError(f"Could not load image: {texture_path}")

                # Convert BGR to RGB
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                # Resize
                img = cv2.resize(img, size, interpolation=cv2.INTER_LANCZOS4)

                return img

            except ImportError:
                raise ImportError("Neither PIL nor OpenCV available for image loading")

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