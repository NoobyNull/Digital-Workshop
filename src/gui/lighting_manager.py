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
from core.logging_config import get_logger, log_function_call


class LightingManager:
    def __init__(self, renderer):
        """Initialize with VTK renderer reference"""
        self.renderer = renderer
        self.light = None
        self.logger = get_logger(__name__)
        
        # Default light properties
        self.position = [100.0, 100.0, 100.0]  # X, Y, Z
        self.color = [1.0, 1.0, 1.0]  # RGB normalized
        self.intensity = 0.8

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
            if self.light is None:
                self.light = vtk.vtkLight()
                # Use a directional-style scene light for general illumination
                try:
                    self.light.SetLightTypeToSceneLight()
                except Exception:
                    pass
                try:
                    self.light.SetPositional(False)
                except Exception:
                    pass
                self.light.SetPosition(*self.position)
                self.light.SetColor(*self.color)
                self.light.SetIntensity(float(self.intensity))
                if self.renderer:
                    self.renderer.AddLight(self.light)
                self.logger.info("LightingManager created light and added to renderer")
            else:
                # Ensure existing light matches current properties
                self.light.SetPosition(*self.position)
                self.light.SetColor(*self.color)
                self.light.SetIntensity(float(self.intensity))

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
            if self.light is None:
                self.create_light()
            else:
                self.light.SetPosition(*self.position)
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
            if self.light is None:
                self.create_light()
            else:
                self.light.SetColor(r, g, b)
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
            if self.light is None:
                self.create_light()
            else:
                self.light.SetIntensity(val)
            self._render_now()
            dt_ms = (time.perf_counter() - t0) * 1000.0
            level = "warning" if dt_ms > 16.0 else "debug"
            getattr(self.logger, level)(f"update_intensity took {dt_ms:.2f} ms")
        except Exception as e:
            self.logger.error(f"update_intensity error: {e}")

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
            props = {"position": pos, "color": col, "intensity": inten}
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
        except Exception as e:
            self.logger.error(f"apply_properties error: {e}")