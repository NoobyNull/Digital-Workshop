"""
Snapping/Docking System Module

This module handles the snapping and docking system for dock widgets,
providing visual feedback and smooth docking behavior when moving
dock widgets around the main window.

Classes:
    SnapOverlayLayer: Visual overlay for snap zones
    DockDragHandler: Event handler for dock dragging and snapping
"""

import logging
from typing import Optional, Dict

from PySide6.QtCore import Qt, QObject, QEvent
from PySide6.QtWidgets import QMainWindow, QDockWidget, QWidget, QFrame, QSizePolicy
from PySide6.QtGui import QCursor


class SnapOverlayLayer(QWidget):
    """
    Translucent snap-zone overlays for top/bottom/left/right edges of the main window.

    This widget provides visual feedback showing where dock widgets can be snapped
    to when dragging them around the main window.
    """

    def __init__(self, main_window: QMainWindow) -> None:
        """
        Initialize the snap overlay layer.

        Args:
            main_window: The main window instance
        """
        super().__init__(main_window)
        self._mw = main_window
        self._thickness = 48
        self._active_edge: Optional[str] = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
        self._edges: Dict[str, QFrame] = {
            "left": QFrame(self),
            "right": QFrame(self),
            "top": QFrame(self),
            "bottom": QFrame(self),
        }
        # Theme-aware colors (use default primary blue)
        r, g, b = (0, 120, 212)  # Default primary blue
        self._rgba_inactive = f"rgba({r}, {g}, {b}, 0.12)"
        self._rgba_active = f"rgba({r}, {g}, {b}, 0.22)"
        self._rgba_border = f"rgba({r}, {g}, {b}, 0.85)"
        for f in self._edges.values():
            f.setFrameShape(QFrame.NoFrame)
        self.hide()
        self.update_geometry()
        self.set_active(None)

    def update_geometry(self) -> None:
        """Resize/position overlays to match the current main window size."""
        if self._mw is None:
            return
        self.setGeometry(self._mw.rect())
        w = self.width()
        h = self.height()
        t = self._thickness
        self._edges["left"].setGeometry(0, 0, t, h)
        self._edges["right"].setGeometry(w - t, 0, t, h)
        self._edges["top"].setGeometry(0, 0, w, t)
        self._edges["bottom"].setGeometry(0, h - t, w, t)

    def _style_for(self, active: bool) -> str:
        """Get stylesheet for active/inactive state."""
        bg = self._rgba_active if active else self._rgba_inactive
        border = f"2px solid {self._rgba_border}" if active else "1px dashed transparent"
        return f"background-color: {bg}; border: {border}; border-radius: 3px;"

    def set_active(self, edge: Optional[str]) -> None:
        """Highlight the given edge ('left'|'right'|'top'|'bottom') or clear when None."""
        self._active_edge = edge
        for name, frame in self._edges.items():
            frame.setStyleSheet(self._style_for(active=(edge == name)))

    def show_overlays(self) -> None:
        """Show the snap overlays."""
        self.update_geometry()
        self.show()
        self.raise_()

    def hide_overlays(self) -> None:
        """Hide the snap overlays."""
        self.hide()
        self.set_active(None)

    @property
    def active_edge(self) -> Optional[str]:
        """Get the currently active edge."""
        return self._active_edge


class DockDragHandler(QObject):
    """
    Event filter that shows snap overlays while dragging floating docks and performs snap-dock.

    This event filter monitors mouse events on dock widgets and provides
    visual feedback and snapping behavior when dragging docks.
    """

    SNAP_MARGIN = 56  # px

    def __init__(
        """TODO: Add docstring."""
        self,
        main_window: QMainWindow,
        dock: QDockWidget,
        overlay: SnapOverlayLayer,
        logger: logging.Logger,
    ):
        """
        Initialize the dock drag handler.

        Args:
            main_window: The main window instance
            dock: The dock widget to handle
            overlay: The snap overlay layer
            logger: Logger instance for debugging
        """
        super().__init__(dock)
        self._mw = main_window
        self._dock = dock
        self._overlay = overlay
        self._logger = logger
        self._tracking = False

    def eventFilter(self, obj, event) -> bool:
        """Filter events for the dock widget."""
        try:
            et = event.type()
            if et == QEvent.MouseButtonPress:
                # Begin potential drag tracking when user interacts with dock.
                self._tracking = True
            elif et == QEvent.MouseMove:
                if self._tracking and self._dock.isFloating():
                    self._maybe_show_and_update_overlay()
            elif et == QEvent.MouseButtonRelease:
                if self._tracking:
                    self._finish_drag()
                    self._tracking = False
        except Exception:
            pass
        return False  # do not block default behavior

    def _maybe_show_and_update_overlay(self) -> None:
        """Show and update the overlay if appropriate."""
        try:
            self._overlay.show_overlays()
            edge = self._nearest_edge_to_cursor()
            self._overlay.set_active(edge)
        except Exception:
            pass

    def _finish_drag(self) -> None:
        """Finish the drag operation and perform snapping if needed."""
        try:
            edge = self._overlay.active_edge
            self._overlay.hide_overlays()
            if not edge:
                return
            # Respect allowed areas
            area_map = {
                "left": Qt.LeftDockWidgetArea,
                "right": Qt.RightDockWidgetArea,
                "top": Qt.TopDockWidgetArea,
                "bottom": Qt.BottomDockWidgetArea,
            }
            target_area = area_map[edge]
            if not (self._dock.allowedAreas() & target_area):
                return

            # For right dock widgets, ensure central widget resizes properly
            if edge == "right":
                self._ensure_central_widget_resize()

            # Perform snap
            self._mw._snap_dock_to_edge(self._dock, edge)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            try:
                self._logger.warning("Snap finalize failed: %s", e)
            except Exception:
                pass

    def _ensure_central_widget_resize(self) -> None:
        """Ensure central widget resizes properly when right docks are moved."""
        try:
            # Force layout update to ensure central widget adjusts
            central_widget = self._mw.centralWidget()
            if central_widget:
                # Update the central widget to trigger proper resizing
                central_widget.updateGeometry()
                # Force the main window to recalculate its layout
                self._mw.updateGeometry()

                # If the central widget is a splitter or tab widget, ensure it resizes
                if hasattr(central_widget, "setSizePolicy"):
                    central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

                self._logger.debug("Central widget resize ensured for right dock movement")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            try:
                self._logger.debug("Failed to ensure central widget resize: %s", e)
            except Exception:
                pass

    def _nearest_edge_to_cursor(self) -> Optional[str]:
        """Find the nearest edge to the cursor position."""
        pos = QCursor.pos()
        # Use main window frame geometry to compare in global coords
        rect = self._mw.frameGeometry()
        if not rect.contains(pos):
            # Allow a small outside tolerance
            grown = rect.adjusted(
                -self.SNAP_MARGIN, -self.SNAP_MARGIN, self.SNAP_MARGIN, self.SNAP_MARGIN
            )
            if not grown.contains(pos):
                return None
        # distances
        d_left = abs(pos.x() - rect.left())
        d_right = abs(rect.right() - pos.x())
        d_top = abs(pos.y() - rect.top())
        d_bottom = abs(rect.bottom() - pos.y())
        d_min = min(d_left, d_right, d_top, d_bottom)
        if d_min > self.SNAP_MARGIN:
            return None
        if d_min == d_left:
            return "left"
        if d_min == d_right:
            return "right"
        if d_min == d_top:
            return "top"
        return "bottom"


# Convenience function for easy dock snapping setup
def setup_dock_snapping(
    """TODO: Add docstring."""
    main_window: QMainWindow, logger: logging.Logger
) -> tuple[SnapOverlayLayer, Dict[str, DockDragHandler]]:
    """
    Convenience function to set up dock snapping for a main window.

    Args:
        main_window: The main window to set up dock snapping for
        logger: Logger instance

    Returns:
        Tuple of (SnapOverlayLayer, Dict of DockDragHandler instances)
    """
    overlay = SnapOverlayLayer(main_window)
    handlers = {}
    return overlay, handlers
