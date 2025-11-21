"""
Shared helpers for project import flows to avoid duplicating dialog logic.
"""

from typing import Callable, Optional
from pathlib import Path
from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox


def import_existing_library(  # pragma: no cover - UI heavy
    parent,
    project_manager,
    dry_run_analyzer,
    project_importer,
    on_created: Callable[[int], None],
    refresh_ui: Callable[[], None],
    logger,
) -> None:
    """
    Run the interactive "import library" flow shared by project manager widgets.

    The flow opens a folder picker, asks for a project name, runs a dry-run, and
    if confirmed executes the import and refreshes UI.
    """
    folder = QFileDialog.getExistingDirectory(
        parent, "Select Library Folder", "", QFileDialog.ShowDirsOnly
    )
    if not folder:
        return

    name, ok = QInputDialog.getText(
        parent, "Import Library", "Project name:", text=Path(folder).name
    )
    if not ok or not name:
        return

    if project_manager.check_duplicate(name):
        QMessageBox.warning(
            parent, "Duplicate Project", f"Project '{name}' already exists."
        )
        return

    dry_run = dry_run_analyzer.analyze(folder, name)
    if not dry_run.can_proceed:
        QMessageBox.warning(parent, "Import Failed", "No files to import.")
        return

    report_text = (
        f"Import Preview: {name}\n"
        f"Files: {dry_run.allowed_files}\n"
        f"Blocked: {dry_run.blocked_files}\n"
        f"Size: {dry_run.total_size_mb:.2f} MB\n\n"
        "Proceed with import?"
    )
    reply = QMessageBox.question(
        parent, "Import Library", report_text, QMessageBox.Yes | QMessageBox.No
    )
    if reply != QMessageBox.Yes:
        return

    import_report = project_importer.import_project(
        folder,
        name,
        structure_type=dry_run.structure_analysis.get("structure_type", "nested"),
    )

    if import_report.success:
        on_created(import_report.project_id)
        refresh_ui()
        QMessageBox.information(
            parent, "Import Complete", f"Imported {import_report.files_imported} files."
        )
        logger.info("Imported library: %s", name)
    else:
        error_text = (
            import_report.errors[0] if import_report.errors else "Unknown error"
        )
        QMessageBox.critical(
            parent, "Import Failed", f"Failed to import library: {error_text}"
        )
        logger.error("Failed to import library: %s", error_text)
