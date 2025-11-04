"""
Core theme management system.

Provides the ThemeManager singleton class for managing colors, presets,
CSS processing, widget registration, and theme persistence.
"""

import json
import logging
import re
import time
import weakref
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QColor

from .theme_constants import (
    FALLBACK_COLOR,
    _normalize_hex,
    hex_to_qcolor,
    hex_to_vtk_rgb,
)
from .theme_defaults import ThemeDefaults
from .theme_palette import PRESETS, derive_mode_palette


class ThemeManager:
    """
    ThemeManager provides:
    - Central color registry with descriptive variable names
    - Fallback handling for undefined variables (returns FALLBACK_COLOR, logs WARNING)
    - CSS template processing for {{VARIABLE_NAME}} replacement
    - Processed CSS caching by file mtime and theme version for performance
    - Widget registry for applying/re-applying stylesheets
    - JSON theme save/load plus export/import helpers
    """

    _instance: Optional["ThemeManager"] = None
    VARIABLE_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_]+)\s*\}\}")

    def __init__(self) -> None:
        """TODO: Add docstring."""
        self._logger = logging.getLogger("gui.theme")
        self._colors: Dict[str, str] = {
            k: _normalize_hex(v) for k, v in asdict(ThemeDefaults()).items()
        }
        self._version: int = 0  # bump whenever theme is updated
        self._preset_name: str = "custom"  # last applied preset name
        # CSS caches
        self._css_file_cache: Dict[str, Tuple[float, int, str]] = (
            {}
        )  # path -> (mtime, version, processed_css)
        self._css_text_cache: Dict[str, Tuple[int, str]] = {}  # key -> (version, processed_css)
        # Widget registry: weak refs to (widget, css_path, css_text)
        self._widgets: "weakref.WeakSet[Any]" = weakref.WeakSet()
        self._widget_sources: Dict[int, Tuple[Optional[str], Optional[str]]] = {}

    @classmethod
    def instance(cls) -> "ThemeManager":
        """TODO: Add docstring."""
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    def _log_json(self, level: int, event: str, **kwargs: Any) -> None:
        """Emit structured JSON logs."""
        payload = {"event": event, "ts": int(time.time() * 1000), **kwargs}
        self._logger.log(level, json.dumps(payload, ensure_ascii=False))

    @property
    def colors(self) -> Dict[str, str]:
        """Return a copy of the color registry."""
        return dict(self._colors)

    def get_color(self, name: str, *, context: Optional[str] = None) -> str:
        """Get a color by name. Returns FALLBACK_COLOR if not found."""
        if name in self._colors:
            return _normalize_hex(self._colors[name])
        self._log_json(
            logging.DEBUG,
            "theme_fallback_color",
            variable=name,
            context=context or "",
        )
        return FALLBACK_COLOR

    def set_colors(self, overrides: Dict[str, Any]) -> None:
        """Update known colors with overrides, ignoring unknown keys."""
        changed = False
        for k, v in overrides.items():
            if k in self._colors:
                self._colors[k] = str(v).strip()
                changed = True
        if changed:
            self._version += 1
            self._css_file_cache.clear()
            self._css_text_cache.clear()
            self._log_json(
                logging.INFO,
                "theme_updated",
                changed_keys=[k for k in overrides.keys() if k in self._colors],
            )

    def available_presets(self) -> list[str]:
        """Return list of available built-in theme presets."""
        return sorted(list(PRESETS.keys()) + ["custom"])

    @property
    def current_preset(self) -> str:
        """Name of the last applied preset. 'custom' when user edited manually."""
        return getattr(self, "_preset_name", "custom")

    def apply_preset(
        """TODO: Add docstring."""
        self,
        preset_name: str,
        *,
        custom_mode: Optional[str] = None,
        base_primary: Optional[str] = None,
    ) -> None:
        """Apply a named preset."""
        name = (preset_name or "custom").lower()
        if name in PRESETS:
            preset_colors = PRESETS[name]
            primary = preset_colors.get("primary", ThemeDefaults.primary)
            mode = (
                "dark" if preset_colors.get("window_bg", "#ffffff").lower() == "#000000" else "auto"
            )
            derived = derive_mode_palette(primary, mode=mode)
            merged = {**derived, **preset_colors}
            self.set_colors(merged)
            self._preset_name = name
            self._log_json(
                logging.INFO,
                "theme_preset_applied",
                preset=name,
                colors_defined=len(merged),
            )
            return

        # Custom derived theme
        mode = (custom_mode or "auto").lower()
        seed = base_primary or self._colors.get("primary", ThemeDefaults.primary)
        derived = derive_mode_palette(seed, mode=mode)
        self.set_colors(derived)
        self._preset_name = "custom"
        self._log_json(logging.INFO, "theme_preset_applied", preset="custom", mode=mode, seed=seed)

    def qcolor(self, name: str) -> QColor:
        """TODO: Add docstring."""
        return hex_to_qcolor(self.get_color(name, context="qcolor"))

    def vtk_rgb(self, name: str) -> Tuple[float, float, float]:
        """TODO: Add docstring."""
        return hex_to_vtk_rgb(self.get_color(name, context="vtk_rgb"))

    def _strip_css_comments(self, text: str) -> str:
        """Remove CSS block comments (/* ... */)."""
        try:
            return re.sub(r"/\*.*?\*/", "", text, flags=re.S)
        except Exception:
            return text

    def process_css_template(self, css_text: str) -> str:
        """Replace {{VARIABLE_NAME}} patterns with actual color values."""
        key = f"{hash(css_text)}"
        cached = self._css_text_cache.get(key)
        if cached and cached[0] == self._version:
            return cached[1]

        def replace(match: re.Match[str]) -> str:
            """TODO: Add docstring."""
            var = match.group(1)
            value = self.get_color(var, context="css_template")
            return value if value else FALLBACK_COLOR

        try:
            text = self._strip_css_comments(css_text)
            processed = re.sub(self.VARIABLE_PATTERN, replace, text)
            self._css_text_cache[key] = (self._version, processed)
            return processed
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "css_template_processing_error", error=str(exc))
            return css_text

    def process_css_file(self, path: Union[str, Path]) -> str:
        """Read a CSS file, replace {{VARIABLE_NAME}} with actual values."""
        p = str(path)
        try:
            mtime = Path(p).stat().st_mtime
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "css_file_stat_error", path=p, error=str(exc))
            try:
                text = Path(p).read_text(encoding="utf-8")
                return self.process_css_template(text)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc2:
                self._log_json(logging.ERROR, "css_file_read_error", path=p, error=str(exc2))
                return ""

        cached = self._css_file_cache.get(p)
        if cached and cached[0] == mtime and cached[1] == self._version:
            return cached[2]

        try:
            text = Path(p).read_text(encoding="utf-8")
            processed = self.process_css_template(text)
            self._css_file_cache[p] = (mtime, self._version, processed)
            return processed
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "css_file_processing_error", path=p, error=str(exc))
            return ""

    def register_widget(
        """TODO: Add docstring."""
        self,
        widget: Any,
        *,
        css_path: Optional[Union[str, Path]] = None,
        css_text: Optional[str] = None,
    ) -> None:
        """Register a widget for style application."""
        try:
            self._widgets.add(widget)
            key = id(widget)
            self._widget_sources[key] = (
                str(css_path) if css_path is not None else None,
                css_text,
            )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "widget_register_error", error=str(exc))

    def apply_stylesheet(self, widget: Any) -> None:
        """Apply the registered stylesheet to a single widget."""
        key = id(widget)
        src = self._widget_sources.get(key)
        if not src:
            return
        css_path, css_text = src
        try:
            if css_text:
                ss = self.process_css_template(css_text)
            elif css_path:
                ss = self.process_css_file(css_path)
            else:
                ss = ""
            if hasattr(widget, "setStyleSheet"):
                widget.setStyleSheet(ss)
                self._log_json(
                    logging.DEBUG,
                    "stylesheet_applied",
                    widget=str(widget),
                    css_path=css_path or "",
                    css_text_len=len(css_text or ""),
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "stylesheet_apply_error", error=str(exc))

    def apply_to_registered(self) -> None:
        """Re-apply styles to all registered widgets."""
        dead: list[int] = []
        for w in list(self._widgets):
            if w is None:
                continue
            try:
                self.apply_stylesheet(w)
            except ReferenceError:
                dead.append(id(w))
                continue
            except Exception:
                continue
        for k in dead:
            self._widget_sources.pop(k, None)

    def _settings_path(self) -> Path:
        """Return the path to the theme.json in AppData."""
        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data / "theme.json"

    def save_to_settings(self) -> None:
        """Persist current theme to theme.json in AppData."""
        try:
            path = self._settings_path()
            path.write_text(json.dumps(self.colors, indent=2), encoding="utf-8")
            self._log_json(logging.INFO, "theme_saved", path=str(path))
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "theme_save_error", error=str(exc))

    def load_from_settings(self) -> None:
        """Load theme from theme.json in AppData."""
        try:
            path = self._settings_path()
            if not path.exists():
                return
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.set_colors({k: v for k, v in data.items() if k in self._colors})
                self._log_json(logging.INFO, "theme_loaded", path=str(path))
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "theme_load_error", error=str(exc))

    def export_theme(self, file_path: Union[str, Path]) -> None:
        """Export current theme to a JSON file at file_path."""
        try:
            Path(file_path).write_text(json.dumps(self.colors, indent=2), encoding="utf-8")
            self._log_json(logging.INFO, "theme_exported", path=str(file_path))
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "theme_export_error", path=str(file_path), error=str(exc))

    def import_theme(self, file_path: Union[str, Path]) -> None:
        """Import a theme from a JSON file at file_path."""
        try:
            data = json.loads(Path(file_path).read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.set_colors({k: v for k, v in data.items() if k in self._colors})
                self._log_json(logging.INFO, "theme_imported", path=str(file_path))
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            self._log_json(logging.ERROR, "theme_import_error", path=str(file_path), error=str(exc))
