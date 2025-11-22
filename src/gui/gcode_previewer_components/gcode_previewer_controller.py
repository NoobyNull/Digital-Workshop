"""Controller stub for G-code previewer logic."""

from __future__ import annotations

from src.core.logging_config import get_logger


class GcodePreviewerController:
    def __init__(self):
        self.logger = get_logger(__name__)

    # TODO: move non-UI logic from gcode_previewer_main here

    def link_gcode_file_to_project(
        self, db_manager, project_id: str, file_path: str, logger
    ) -> bool:
        """Link a G-code file to the current project via DatabaseManager."""
        if db_manager is None or not project_id or not file_path:
            return False
        try:
            db_manager.add_file(
                project_id,
                file_path=file_path,
                link_type="gcode",
                status="completed",
            )
            logger.info("Linked G-code file to project: %s", file_path)
            return True
        except Exception as exc:
            logger.error("Failed to link G-code file: %s", exc)
            return False
