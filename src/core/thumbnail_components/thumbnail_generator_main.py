"""
Thumbnail generator for 3D model files.

Generates and caches thumbnails for various 3D model formats.
"""

import gc
import time
from pathlib import Path
from typing import Optional, Tuple, Union

import vtk
from vtk.util import numpy_support as vtk_np

from src.core.logging_config import get_logger
from src.core.view_optimizer import ViewOptimizer
from src.parsers.stl_parser import STLParser
from src.core.data_structures import Model
from src.core.material_provider import MaterialProvider


class ThumbnailGenerator:
    """
    Generate high-quality thumbnails for 3D models using VTK offscreen rendering.

    Features:
    - 1080x1080 resolution for high quality
    - Offscreen rendering (no UI window)
    - Customizable backgrounds (solid colors or images)
    - Hash-based file naming
    - Automatic best view detection
    - Memory-efficient cleanup
    """

    def __init__(self, settings_manager=None):
        """
        Initialize the thumbnail generator.

        Args:
            settings_manager: Optional settings manager for background preferences
        """
        self.logger = get_logger(__name__)
        self.settings = settings_manager
        self.view_optimizer = ViewOptimizer()

        # Material provider for discovering texture images
        self.material_provider = MaterialProvider()

        # Material manager for consistent material application
        # (same code used for runtime material application)
        self.material_manager = None
        try:
            from src.gui.material_manager import MaterialManager
            from src.core.database_manager import get_database_manager
            self.material_manager = MaterialManager(get_database_manager())
            self.logger.debug("MaterialManager initialized for thumbnail generation")
        except Exception as e:
            self.logger.warning(f"Could not initialize MaterialManager for thumbnails: {e}")

        # Default thumbnail size
        self.thumbnail_size = (1080, 1080)

        self.logger.info("ThumbnailGenerator initialized with MaterialProvider")

    def generate_thumbnail(
        self,
        model_path: str,
        file_hash: str,
        output_dir: Path,
        background: Optional[Union[str, Tuple[float, float, float]]] = None,
        size: Optional[Tuple[int, int]] = None,
        material: Optional[str] = None,
        force_regenerate: bool = False
    ) -> Optional[Path]:
        """
        Generate a thumbnail for a 3D model.

        Args:
            model_path: Path to the 3D model file
            file_hash: BLAKE2 hash of the model (used for filename)
            output_dir: Directory to save thumbnail
            background: Background color (R,G,B tuple 0-1) or image path, or None for settings
            size: Output size as (width, height), or None for default 1080x1080
            material: Optional wood species name to apply material texture (e.g., 'Oak', 'Walnut')
            force_regenerate: If True, regenerate even if thumbnail already exists

        Returns:
            Path to generated thumbnail PNG, or None on failure
        """
        start_time = time.time()

        try:
            # Ensure output directory exists
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Determine output path
            thumbnail_path = output_dir / f"{file_hash}.png"

            # Check if thumbnail already exists (unless forced)
            if thumbnail_path.exists() and not force_regenerate:
                self.logger.info(f"Thumbnail already exists: {thumbnail_path}")
                return thumbnail_path

            # If force regenerating, remove the old thumbnail
            if force_regenerate and thumbnail_path.exists():
                try:
                    thumbnail_path.unlink()
                    self.logger.info(f"Removed existing thumbnail for regeneration: {thumbnail_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to remove existing thumbnail: {e}")

            self.logger.info(f"Generating thumbnail for: {model_path}")

            # Load model
            model = self._load_model(model_path)
            if model is None:
                self.logger.error(f"Failed to load model: {model_path}")
                return None

            # Set thumbnail size
            if size is None:
                size = self.thumbnail_size

            # Render thumbnail
            success = self._render_thumbnail(
                model=model,
                output_path=thumbnail_path,
                background=background,
                size=size,
                material=material
            )

            if success:
                elapsed = time.time() - start_time
                self.logger.info(
                    f"Thumbnail generated successfully in {elapsed:.2f}s: {thumbnail_path}"
                )
                return thumbnail_path
            else:
                self.logger.error("Thumbnail rendering failed")
                return None

        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                f"Failed to generate thumbnail after {elapsed:.2f}s: {e}",
                exc_info=True
            )
            return None
        finally:
            # Force garbage collection to free VTK resources
            gc.collect()

    def _load_model(self, model_path: str) -> Optional[Model]:
        """
        Load a 3D model from file.

        Args:
            model_path: Path to model file

        Returns:
            Loaded Model object or None on failure
        """
        try:
            # Currently supports STL files
            # TODO: Add support for other formats (OBJ, STEP, 3MF)
            parser = STLParser()
            model = parser.parse_file(model_path, lazy_loading=False)

            if model is None:
                self.logger.error(f"Parser returned None for: {model_path}")
                return None

            self.logger.debug(
                f"Model loaded: {model.stats.triangle_count} triangles, "
                f"{model.stats.vertex_count} vertices"
            )

            return model

        except Exception as e:
            self.logger.error(f"Error loading model {model_path}: {e}", exc_info=True)
            return None

    def _render_thumbnail(
        self,
        model: Model,
        output_path: Path,
        background: Optional[Union[str, Tuple[float, float, float]]],
        size: Tuple[int, int],
        material: Optional[str] = None
    ) -> bool:
        """
        Render a model to a PNG thumbnail using VTK offscreen rendering.

        Args:
            model: The Model object to render
            output_path: Where to save the PNG
            background: Background color or image path
            size: Output resolution (width, height)
            material: Optional wood species name for texture application

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create offscreen render window
            render_window = vtk.vtkRenderWindow()
            render_window.SetOffScreenRendering(1)
            render_window.SetSize(size[0], size[1])

            # Create renderer
            renderer = vtk.vtkRenderer()
            render_window.AddRenderer(renderer)

            # Set background
            self._set_background(renderer, background)

            # Create polydata from model
            polydata = self._create_polydata(model)
            if polydata is None:
                self.logger.error("Failed to create VTK polydata")
                return False

            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            mapper.ScalarVisibilityOff()

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            # Apply material texture if specified
            if material:
                # Use MaterialManager for consistent material application
                # (same code used for runtime material application)
                if self.material_manager:
                    success = self.material_manager.apply_material_to_actor(actor, material)
                    if not success:
                        self.logger.warning(f"Failed to apply material '{material}' using MaterialManager, using fallback")
                        self._apply_texture_material_fallback(actor, material)
                else:
                    self.logger.debug("MaterialManager not available, using fallback material application")
                    self._apply_texture_material_fallback(actor, material)
            else:
                # Default appearance without material
                prop = actor.GetProperty()
                prop.SetColor(0.8, 0.8, 0.8)  # Light gray
                prop.SetAmbient(0.3)
                prop.SetDiffuse(0.7)
                prop.SetSpecular(0.3)
                prop.SetSpecularPower(20.0)

            renderer.AddActor(actor)

            # Get model bounds and find optimal view
            bounds = actor.GetBounds()
            camera_params = self.view_optimizer.find_best_orthogonal_view(bounds)

            # Set up camera
            camera = renderer.GetActiveCamera()
            camera.SetPosition(*camera_params.position)
            camera.SetFocalPoint(*camera_params.focal_point)
            camera.SetViewUp(*camera_params.view_up)

            # Add lighting for better appearance
            self._setup_lighting(renderer)

            # Reset camera to ensure model is fully visible
            renderer.ResetCamera()
            renderer.ResetCameraClippingRange()

            # Render
            render_window.Render()

            # Capture image
            window_to_image = vtk.vtkWindowToImageFilter()
            window_to_image.SetInput(render_window)
            window_to_image.SetScale(1)  # Full resolution
            window_to_image.SetInputBufferTypeToRGB()
            window_to_image.ReadFrontBufferOff()
            window_to_image.Update()

            # Write PNG
            writer = vtk.vtkPNGWriter()
            writer.SetFileName(str(output_path))
            writer.SetInputConnection(window_to_image.GetOutputPort())
            writer.Write()

            # Cleanup VTK objects
            render_window.Finalize()
            del render_window, renderer, mapper, actor, camera, window_to_image, writer

            self.logger.debug(
                f"Thumbnail rendered with {camera_params.view_name} view at {size[0]}x{size[1]}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error rendering thumbnail: {e}", exc_info=True)
            return False

    def _create_polydata(self, model: Model) -> Optional[vtk.vtkPolyData]:
        """
        Create VTK polydata from Model object.

        Args:
            model: The Model to convert

        Returns:
            vtkPolyData object or None on failure
        """
        try:
            # Try array-based fast path first
            if hasattr(model, 'is_array_based') and model.is_array_based():
                import numpy as np

                vertex_array = model.vertex_array
                normal_array = model.normal_array

                if vertex_array is not None and normal_array is not None:
                    total_vertices = vertex_array.shape[0]
                    tri_count = total_vertices // 3

                    # Convert to VTK format
                    vertex_array = np.ascontiguousarray(vertex_array, dtype=np.float64)
                    normal_array = np.ascontiguousarray(normal_array, dtype=np.float64)

                    # Create points
                    points = vtk.vtkPoints()
                    vtk_points = vtk_np.numpy_to_vtk(vertex_array, deep=True)
                    vtk_points.SetNumberOfComponents(3)
                    points.SetData(vtk_points)

                    # Create normals
                    normals = vtk_np.numpy_to_vtk(normal_array, deep=True)
                    normals.SetName("Normals")
                    normals.SetNumberOfComponents(3)

                    # Create connectivity
                    conn = np.arange(total_vertices, dtype=np.int64)
                    offsets = np.arange(0, total_vertices + 1, 3, dtype=np.int64)

                    conn_vtk = vtk_np.numpy_to_vtkIdTypeArray(conn, deep=True)
                    offsets_vtk = vtk_np.numpy_to_vtkIdTypeArray(offsets, deep=True)

                    triangles = vtk.vtkCellArray()
                    triangles.SetData(offsets_vtk, conn_vtk)

                    # Assemble polydata
                    polydata = vtk.vtkPolyData()
                    polydata.SetPoints(points)
                    polydata.SetPolys(triangles)
                    polydata.GetPointData().SetNormals(normals)

                    self.logger.debug(f"Created polydata (fast path): {tri_count} triangles")
                    return polydata

            # Fallback to triangle-by-triangle construction
            points = vtk.vtkPoints()
            triangles = vtk.vtkCellArray()
            normals = vtk.vtkFloatArray()
            normals.SetNumberOfComponents(3)
            normals.SetName("Normals")

            for triangle in model.triangles:
                # Add vertices
                p1 = points.InsertNextPoint(triangle.vertex1.x, triangle.vertex1.y, triangle.vertex1.z)
                p2 = points.InsertNextPoint(triangle.vertex2.x, triangle.vertex2.y, triangle.vertex2.z)
                p3 = points.InsertNextPoint(triangle.vertex3.x, triangle.vertex3.y, triangle.vertex3.z)

                # Add triangle
                tri = vtk.vtkTriangle()
                tri.GetPointIds().SetId(0, p1)
                tri.GetPointIds().SetId(1, p2)
                tri.GetPointIds().SetId(2, p3)
                triangles.InsertNextCell(tri)

                # Add normals
                normal = [triangle.normal.x, triangle.normal.y, triangle.normal.z]
                normals.InsertNextTuple(normal)
                normals.InsertNextTuple(normal)
                normals.InsertNextTuple(normal)

            polydata = vtk.vtkPolyData()
            polydata.SetPoints(points)
            polydata.SetPolys(triangles)
            polydata.GetPointData().SetNormals(normals)

            self.logger.debug(f"Created polydata (slow path): {len(model.triangles)} triangles")
            return polydata

        except Exception as e:
            self.logger.error(f"Error creating polydata: {e}", exc_info=True)
            return None

    def _set_background(
        self,
        renderer: vtk.vtkRenderer,
        background: Optional[Union[str, Tuple[float, float, float]]]
    ) -> None:
        """
        Set renderer background color or image.

        Args:
            renderer: VTK renderer
            background: Color tuple (R,G,B 0-1), hex string, or image path
        """
        try:
            if background is None:
                # Use default light gray background
                renderer.SetBackground(0.95, 0.95, 0.95)
                return

            if isinstance(background, str):
                # Check if it's a hex color or file path
                if background.startswith('#'):
                    # Hex color
                    rgb = self._hex_to_rgb(background)
                    renderer.SetBackground(*rgb)
                elif Path(background).exists():
                    # Image file - use textured background
                    self._set_background_image(renderer, background)
                else:
                    self.logger.warning(f"Invalid background: {background}, using default")
                    renderer.SetBackground(0.95, 0.95, 0.95)
            elif isinstance(background, (tuple, list)) and len(background) == 3:
                # RGB tuple
                renderer.SetBackground(*background)
            else:
                self.logger.warning(f"Unknown background type: {type(background)}, using default")
                renderer.SetBackground(0.95, 0.95, 0.95)

        except Exception as e:
            self.logger.error(f"Error setting background: {e}", exc_info=True)
            renderer.SetBackground(0.95, 0.95, 0.95)

    def _set_background_image(self, renderer: vtk.vtkRenderer, image_path: str) -> None:
        """
        Set a background image for the renderer.

        Args:
            renderer: VTK renderer
            image_path: Path to background image file
        """
        try:
            # Read image
            reader = vtk.vtkPNGReader()
            if image_path.lower().endswith('.jpg') or image_path.lower().endswith('.jpeg'):
                reader = vtk.vtkJPEGReader()

            reader.SetFileName(image_path)
            reader.Update()

            # Create texture
            texture = vtk.vtkTexture()
            texture.SetInputConnection(reader.GetOutputPort())

            # Create background actor
            plane = vtk.vtkPlaneSource()
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(plane.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.SetTexture(texture)

            # Position behind everything
            actor.GetProperty().LightingOff()

            renderer.AddActor(actor)
            renderer.SetLayer(0)

        except Exception as e:
            self.logger.error(f"Error setting background image: {e}", exc_info=True)
            renderer.SetBackground(0.95, 0.95, 0.95)

    def _setup_lighting(self, renderer: vtk.vtkRenderer) -> None:
        """
        Set up bright studio lighting for thumbnail rendering.
        Uses broadcast ambient light + directional point lights with wide cone angles.

        Args:
            renderer: VTK renderer
        """
        try:
            # Remove default lights
            renderer.RemoveAllLights()

            # Broadcast ambient light for overall brightness (headlight follows camera)
            ambient_light = vtk.vtkLight()
            ambient_light.SetLightTypeToHeadlight()
            ambient_light.SetIntensity(0.7)  # Strong ambient for bright thumbnails
            ambient_light.SetColor(1.0, 1.0, 1.0)
            renderer.AddLight(ambient_light)

            # Main directional point light from top-right
            key_light = vtk.vtkLight()
            key_light.SetLightTypeToSceneLight()
            key_light.SetPosition(150, 150, 200)
            key_light.SetFocalPoint(0, 0, 0)
            key_light.SetIntensity(1.0)
            key_light.SetColor(1.0, 1.0, 1.0)
            key_light.SetPositional(True)  # Point light
            key_light.SetConeAngle(120)  # Wide cone (90-360 range, using 120 for broad coverage)
            renderer.AddLight(key_light)

            # Fill directional light from front-left
            fill_light = vtk.vtkLight()
            fill_light.SetLightTypeToSceneLight()
            fill_light.SetPosition(-100, 50, 150)
            fill_light.SetFocalPoint(0, 0, 0)
            fill_light.SetIntensity(0.6)
            fill_light.SetColor(1.0, 1.0, 1.0)
            fill_light.SetPositional(True)
            fill_light.SetConeAngle(100)  # Wide cone for shadow softening
            renderer.AddLight(fill_light)

            self.logger.debug("Bright studio lighting setup: ambient headlight + 2 directional point lights")

        except Exception as e:
            self.logger.error(f"Error setting up lighting: {e}", exc_info=True)

    def _hex_to_rgb(self, hex_color: str) -> Tuple[float, float, float]:
        """
        Convert hex color string to RGB tuple (0-1 range).

        Args:
            hex_color: Hex color string (e.g., '#FF0000')

        Returns:
            RGB tuple with values 0-1
        """
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b)
    def _apply_texture_material_fallback(self, actor: vtk.vtkActor, material_name: str) -> bool:
        """
        Fallback method to apply texture material to actor using texture images from materials folder.

        This is a fallback when MaterialManager is not available.
        For normal operation, use MaterialManager.apply_material_to_actor() instead.

        CRITICAL: Generates UV texture coordinates for STL models which don't have them.

        Args:
            actor: VTK actor to apply texture to
            material_name: Name of material (matches texture filename without extension)

        Returns:
            True if material applied successfully
        """
        try:
            # Get material texture path
            texture_path = self.material_provider.get_material_texture_path(material_name)

            if texture_path is None or not texture_path.exists():
                self.logger.warning(f"Material texture not found: {material_name}")
                return False

            self.logger.info(f"Applying texture '{material_name}' from: {texture_path}")

            # CRITICAL: STL models don't have UV coordinates, we must generate them
            mapper = actor.GetMapper()
            if not mapper:
                self.logger.error("Actor has no mapper")
                return False

            polydata = mapper.GetInput()
            if not polydata:
                self.logger.error("Mapper has no input")
                return False

            # Generate planar texture coordinates (auto-fit to model bounds)
            tex_mapper = vtk.vtkTextureMapToPlane()
            tex_mapper.SetInputData(polydata)
            tex_mapper.AutomaticPlaneGenerationOn()
            tex_mapper.Update()

            # Update mapper with UV-mapped polydata
            mapper.SetInputConnection(tex_mapper.GetOutputPort())

            # Load texture image based on file type
            ext = texture_path.suffix.lower()

            if ext == '.png':
                reader = vtk.vtkPNGReader()
            elif ext in {'.jpg', '.jpeg'}:
                reader = vtk.vtkJPEGReader()
            elif ext == '.bmp':
                reader = vtk.vtkBMPReader()
            else:
                self.logger.warning(f"Unsupported texture format: {ext}")
                return False

            reader.SetFileName(str(texture_path))
            reader.Update()

            # Create VTK texture
            texture = vtk.vtkTexture()
            texture.SetInputConnection(reader.GetOutputPort())
            texture.InterpolateOn()
            texture.RepeatOn()

            try:
                texture.MipmapOn()
            except Exception:
                pass

            # Apply texture to actor
            actor.SetTexture(texture)

            # Set actor properties for good texture visibility
            actor_prop = actor.GetProperty()
            actor_prop.SetColor(1.0, 1.0, 1.0)  # White base color for proper texture display

            # Get MTL properties if available
            material_info = self.material_provider.get_material_by_name(material_name)
            if material_info and 'properties' in material_info:
                props = material_info['properties']

                if 'shininess' in props:
                    actor_prop.SetSpecularPower(props['shininess'])
                if 'specular' in props:
                    spec_val = sum(props['specular']) / 3.0
                    actor_prop.SetSpecular(spec_val)
                if 'ambient' in props:
                    amb_val = sum(props['ambient']) / 3.0
                    actor_prop.SetAmbient(max(0.4, amb_val))  # Ensure visible
                else:
                    actor_prop.SetAmbient(0.5)  # Higher for texture visibility
                if 'diffuse' in props:
                    diff_val = sum(props['diffuse']) / 3.0
                    actor_prop.SetDiffuse(diff_val)
                else:
                    actor_prop.SetDiffuse(0.8)  # Higher for brightness

                self.logger.debug(f"Applied MTL properties for '{material_name}'")
            else:
                # Default bright properties for textured appearance
                actor_prop.SetAmbient(0.5)
                actor_prop.SetDiffuse(0.8)
                actor_prop.SetSpecular(0.2)
                actor_prop.SetSpecularPower(15.0)

            self.logger.info(f"Texture '{material_name}' applied with UV mapping")
            return True

        except Exception as e:
            self.logger.error(f"Error applying texture '{material_name}': {e}", exc_info=True)
            return False
