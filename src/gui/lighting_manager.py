"""
Lighting manager for a single VTK light in the 3D-MM application.

Responsibilities:
- Create and manage a single vtkLight attached to a provided renderer
- Provide updates for position, color, and intensity with immediate renders
- Return/apply properties as a dictionary
- Comprehensive logging and graceful error handling
- Fast operations (<16ms typical) for responsive UI

This module depends on VTK and the centralized JSON logging utilities.
"""

import time
from typing import Dict, Any

import vtk
from src.core.logging_config import get_logger, log_function_call


class LightingManager:
    def __init__(self, renderer):
        """Initialize with VTK renderer reference"""
        self.renderer = renderer
        self.light = None
        self.logger = get_logger(__name__)

        # Load lighting settings from config
        try:
            from src.core.application_config import ApplicationConfig
            config = ApplicationConfig.get_default()
            self.position = [
                config.default_light_position_x,
                config.default_light_position_y,
                config.default_light_position_z
            ]
            self.color = [
                config.default_light_color_r,
                config.default_light_color_g,
                config.default_light_color_b
            ]
            self.intensity = config.default_light_intensity
            self.cone_angle = config.default_light_cone_angle
            self.enable_fill_light = config.enable_fill_light
            self.fill_light_intensity = config.fill_light_intensity
        except Exception as e:
            self.logger.warning(f"Failed to load lighting settings from config: {e}")
            # Default light properties
            self.position = [100.0, 100.0, 100.0]  # X, Y, Z
            self.color = [1.0, 1.0, 1.0]  # RGB normalized
            self.intensity = 0.8
            self.cone_angle = 30.0  # Cone angle in degrees (for spotlight)
            self.enable_fill_light = True
            self.fill_light_intensity = 0.3

        self.positional = True  # Use positional light for cone effect

    def _render_now(self) -> None:
        """Trigger an immediate render if possible."""
        try:
            rw = self.renderer.GetRenderWindow() if self.renderer else None
            if rw:
                rw.Render()
        except Exception:
            # Rendering is best-effort; never raise here
            pass

    @staticmethod
    def _clamp(v: float, lo: float, hi: float) -> float:
        """Clamp numeric value safely."""
        try:
            v = float(v)
            if v < lo:
                return lo
            if v > hi:
                return hi
            return v
        except Exception:
            return lo

    @log_function_call(get_logger(__name__))
    def create_light(self) -> bool:
        """
        Create and add VTK light to renderer or update existing with current properties.
        Returns True on success.
        """
        t0 = time.perf_counter()
        try:
            # Clear existing lights first to avoid conflicts
            if self.renderer:
                self.renderer.RemoveAllLights()

            # Create primary key light as positional spotlight with cone
            self.light = vtk.vtkLight()
            try:
                self.light.SetLightTypeToSceneLight()
            except Exception:
                pass
            try:
                self.light.SetPositional(self.positional)  # Positional for cone effect
            except Exception:
                pass
            try:
                # Set cone angle for spotlight effect
                self.light.SetConeAngle(float(self.cone_angle))
                # Set focus/falloff (lower = softer edges, higher = harder edges)
                self.light.SetExponent(2.0)  # Moderate falloff
            except Exception:
                pass
            self.light.SetPosition(*self.position)
            self.light.SetFocalPoint(0, 0, 0)  # Point light at origin
            self.light.SetColor(*self.color)
            self.light.SetIntensity(float(self.intensity))

            # Create fill light for better overall illumination (if enabled)
            if self.enable_fill_light:
                fill_light = vtk.vtkLight()
                try:
                    fill_light.SetLightTypeToSceneLight()
                except Exception:
                    pass
                try:
                    fill_light.SetPositional(False)
                except Exception:
                    pass
                # Position fill light opposite to key light
                fill_pos = [-p * 0.5 for p in self.position]
                fill_light.SetPosition(*fill_pos)
                fill_light.SetColor(0.8, 0.8, 0.9)  # Slightly cool fill light
                fill_light.SetIntensity(float(self.fill_light_intensity))  # Use config intensity

                # Add lights to renderer
                if self.renderer:
                    self.renderer.AddLight(self.light)
                    self.renderer.AddLight(fill_light)
                    self.logger.info("LightingManager created key and fill lights and added to renderer")
            else:
                # Add only key light if fill light is disabled
                if self.renderer:
                    self.renderer.AddLight(self.light)
                    self.logger.info("LightingManager created key light only (fill light disabled)")

            # Immediate render for responsive UX
            self._render_now()

            dt_ms = (time.perf_counter() - t0) * 1000.0
            self.logger.debug(f"create_light completed in {dt_ms:.2f} ms")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create/add light: {e}")
            return False

    def update_position(self, x: float, y: float, z: float) -> None:
        """Update light position with immediate render."""
        t0 = time.perf_counter()
        try:
            self.position = [float(x), float(y), float(z)]
            # Recreate lights to ensure proper positioning
            self.create_light()
            self._render_now()
            dt_ms = (time.perf_counter() - t0) * 1000.0
            level = "warning" if dt_ms > 16.0 else "debug"
            getattr(self.logger, level)(f"update_position took {dt_ms:.2f} ms")
        except Exception as e:
            self.logger.error(f"update_position error: {e}")

    def update_color(self, r: float, g: float, b: float) -> None:
        """Update light color (normalized 0-1)."""
        t0 = time.perf_counter()
        try:
            r = self._clamp(r, 0.0, 1.0)
            g = self._clamp(g, 0.0, 1.0)
            b = self._clamp(b, 0.0, 1.0)
            self.color = [r, g, b]
            # Recreate lights to ensure proper color application
            self.create_light()
            self._render_now()
            dt_ms = (time.perf_counter() - t0) * 1000.0
            level = "warning" if dt_ms > 16.0 else "debug"
            getattr(self.logger, level)(f"update_color took {dt_ms:.2f} ms")
        except Exception as e:
            self.logger.error(f"update_color error: {e}")

    def update_intensity(self, value: float) -> None:
        """Update intensity (0-2.0 range)."""
        t0 = time.perf_counter()
        try:
            val = self._clamp(value, 0.0, 2.0)
            self.intensity = val
            # Recreate lights to ensure proper intensity
            self.create_light()
            self._render_now()
            dt_ms = (time.perf_counter() - t0) * 1000.0
            level = "warning" if dt_ms > 16.0 else "debug"
            getattr(self.logger, level)(f"update_intensity took {dt_ms:.2f} ms")
        except Exception as e:
            self.logger.error(f"update_intensity error: {e}")

    def update_cone_angle(self, angle: float) -> None:
        """Update spotlight cone angle (1-90 degrees)."""
        t0 = time.perf_counter()
        try:
            angle = self._clamp(angle, 1.0, 90.0)
            self.cone_angle = angle
            # Recreate lights to ensure proper cone angle
            self.create_light()
            self._render_now()
            dt_ms = (time.perf_counter() - t0) * 1000.0
            level = "warning" if dt_ms > 16.0 else "debug"
            getattr(self.logger, level)(f"update_cone_angle took {dt_ms:.2f} ms")
        except Exception as e:
            self.logger.error(f"update_cone_angle error: {e}")

    def get_properties(self) -> Dict[str, Any]:
        """Return current light properties as dict."""
        try:
            pos = list(self.position)
            col = list(self.color)
            inten = float(self.intensity)
            if self.light is not None:
                try:
                    pos = list(self.light.GetPosition())
                except Exception:
                    pass
                try:
                    col = list(self.light.GetColor())
                except Exception:
                    pass
                try:
                    inten = float(self.light.GetIntensity())
                except Exception:
                    pass
            cone = float(self.cone_angle)
            props = {"position": pos, "color": col, "intensity": inten, "cone_angle": cone}
            self.logger.debug(f"get_properties -> {props}")
            return props
        except Exception as e:
            self.logger.error(f"get_properties error: {e}")
            return {"position": list(self.position), "color": list(self.color), "intensity": float(self.intensity)}

    def apply_properties(self, props: Dict[str, Any]) -> None:
        """Set all properties from dict."""
        try:
            if not isinstance(props, dict):
                raise ValueError("props must be a dict")
            if "position" in props and props["position"] is not None:
                p = props["position"]
                if isinstance(p, (list, tuple)) and len(p) == 3:
                    self.update_position(p[0], p[1], p[2])
            if "color" in props and props["color"] is not None:
                c = props["color"]
                if isinstance(c, (list, tuple)) and len(c) == 3:
                    self.update_color(c[0], c[1], c[2])
            if "intensity" in props and props["intensity"] is not None:
                self.update_intensity(props["intensity"])
            if "cone_angle" in props and props["cone_angle"] is not None:
                self.update_cone_angle(props["cone_angle"])
        except Exception as e:
            self.logger.error(f"apply_properties error: {e}")
