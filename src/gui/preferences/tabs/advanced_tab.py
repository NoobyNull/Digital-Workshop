from __future__ import annotations

"""
Preferences dialog with tabbed interface:
- Display
- System
- Files
- Theming (live-apply + persist to AppData)

The Theming tab edits central color variables in gui.theme.COLORS and applies
changes live across the running app. On Save, the current theme is persisted
to AppData and loaded on next startup.
"""


from PySide6.QtWidgets import (
    QFrame,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)




class AdvancedTab(QWidget):
    """Advanced settings tab with system reset functionality."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = None
        self.theme_manager = None
        try:
            from src.core.logging_config import get_logger

            self.logger = get_logger(__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the advanced settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Advanced Settings")
        header_font = header.font()
        header_font.setBold(True)
        header_font.setPointSize(14)
        header.setFont(header_font)
        layout.addWidget(header)

        # Database Reset Section
        db_section = QFrame()
        db_layout = QVBoxLayout(db_section)

        db_title = QLabel("<b>Database Management</b>")
        db_layout.addWidget(db_title)

        db_warning = QLabel(
            "Reset the application database. This will clear all model records, "
            "metadata, and library information. The database will be recreated on next startup."
        )
        db_warning.setWordWrap(True)
        db_layout.addWidget(db_warning)

        reset_db_button = QPushButton("Reset Database")
        reset_db_button.setStyleSheet(
            "QPushButton { background-color: #ffa500; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #ff8c00; }"
        )
        reset_db_button.clicked.connect(self._perform_database_reset)
        db_layout.addWidget(reset_db_button)

        layout.addWidget(db_section)

        # System Reset Section
        system_section = QFrame()
        system_layout = QVBoxLayout(system_section)

        system_title = QLabel("<b>Complete System Reset</b>")
        system_layout.addWidget(system_title)

        # Warning message
        warning = QLabel(
            "This will reset all application settings, clear the cache, and restore "
            "the application to its default state. This action cannot be undone."
        )
        warning.setWordWrap(True)
        system_layout.addWidget(warning)

        # Reset button
        reset_button = QPushButton("Complete System Reset")
        reset_button.clicked.connect(self._perform_system_reset)
        system_layout.addWidget(reset_button)

        layout.addWidget(system_section)

        # Nuclear Reset Section
        nuclear_section = QFrame()
        nuclear_layout = QVBoxLayout(nuclear_section)

        nuclear_title = QLabel("<b>⚠️ Nuclear Reset (MOST DESTRUCTIVE)</b>")
        nuclear_layout.addWidget(nuclear_title)

        # Warning message
        nuclear_warning = QLabel(
            "⚠️ NUCLEAR OPTION ⚠️\n\n"
            "This is the MOST DESTRUCTIVE reset option. It will:\n"
            "• Delete ALL application data (database, settings, cache, logs, config, temp)\n"
            "• Delete ALL thumbnails\n"
            "• Clear Windows Registry entries\n"
            "• Close all log handlers to release file locks\n"
            "• Force exit without cleanup\n"
            "• Create a backup before deletion (optional)\n\n"
            "Use this when you need to completely obliterate everything and start fresh.\n"
            "This action CANNOT be undone."
        )
        nuclear_warning.setWordWrap(True)
        nuclear_layout.addWidget(nuclear_warning)

        # Nuclear Reset button
        nuclear_button = QPushButton("⚠️ NUCLEAR RESET ⚠️")
        nuclear_button.clicked.connect(self._perform_nuclear_reset)
        nuclear_layout.addWidget(nuclear_button)

        layout.addWidget(nuclear_section)

        layout.addStretch(1)

    def _perform_database_reset(self) -> None:
        """Perform database reset with confirmation."""
        # First verification: Simple confirmation
        reply1 = QMessageBox.warning(
            self,
            "Reset Database - Confirmation 1/2",
            "Are you sure you want to reset the database?\n\n"
            "This will delete all model records, metadata, and library information.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply1 != QMessageBox.Yes:
            return

        # Second verification: Text input
        text, ok = QInputDialog.getText(
            self, "Reset Database - Confirmation 2/2", "Type 'RESET DATABASE' to confirm:", QLineEdit.Normal, ""
        )

        if not ok or text.strip().upper() != "RESET DATABASE":
            QMessageBox.information(self, "Reset Cancelled", "Database reset cancelled. No changes were made.")
            return

        # All verifications passed - perform reset
        self._execute_database_reset()

    def _execute_database_reset(self) -> None:
        """Execute the actual database reset - requires restart to clear memory cache."""
        try:
            import subprocess
            import sys
            from pathlib import Path

            from PySide6.QtCore import QStandardPaths
            from PySide6.QtWidgets import QApplication

            # Close database manager to release file locks
            try:
                from src.core.database_manager import close_database_manager

                close_database_manager()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                print(f"Warning: Could not close database manager: {e}")

            # Delete database file
            try:
                app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
                db_file = app_data / "3dmm.db"
                if db_file.exists():
                    db_file.unlink()
                    print(f"✓ Deleted database: {db_file}")

                # Also delete WAL and SHM files if they exist
                wal_file = app_data / "3dmm.db-wal"
                shm_file = app_data / "3dmm.db-shm"
                if wal_file.exists():
                    wal_file.unlink()
                if shm_file.exists():
                    shm_file.unlink()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                print(f"Warning: Could not delete database file: {e}")

            # Clear model cache instance
            try:
                from src.core.model_cache import ModelCache

                cache = ModelCache.get_instance()
                cache.clear()
                print("✓ Model cache cleared")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                print(f"Warning: Could not clear model cache: {e}")

            # Show success message
            QMessageBox.information(
                self,
                "Database Reset Complete",
                "✓ Database reset completed successfully!\n\n"
                "All models and metadata have been deleted.\n"
                "The application will now close and restart with a fresh database.",
            )

            # Relaunch the application
            subprocess.Popen([sys.executable, sys.argv[0]])

            # Close the application
            QApplication.instance().quit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            QMessageBox.critical(self, "Reset Failed", f"An error occurred during database reset:\n\n{str(e)}")

    def _perform_system_reset(self) -> None:
        """Perform complete system reset with triple verification."""
        # First verification: Simple confirmation
        reply1 = QMessageBox.warning(
            self,
            "System Reset - Confirmation 1/3",
            "Are you sure you want to reset the entire system?\n\n"
            "This will delete ALL application data and restore defaults.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply1 != QMessageBox.Yes:
            return

        # Second verification: More serious warning
        reply2 = QMessageBox.critical(
            self,
            "System Reset - Confirmation 2/3",
            "⚠️ COMPLETE SYSTEM WIPE ⚠️\n\n"
            "This action will PERMANENTLY DELETE:\n"
            "• All application settings and preferences\n"
            "• All cache and temporary files\n"
            "• All profiles and user data\n"
            "• The entire AppData directory\n"
            "• Window layout and dock positions\n"
            "• All stored models and metadata\n\n"
            "The application will restart as if running for the first time.\n"
            "This CANNOT be undone. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply2 != QMessageBox.Yes:
            return

        # Third verification: Text input
        text, ok = QInputDialog.getText(
            self,
            "System Reset - Confirmation 3/3",
            "Type 'RESET' to confirm complete system reset:",
            QLineEdit.Normal,
            "",
        )

        if not ok or text.strip().upper() != "RESET":
            QMessageBox.information(self, "Reset Cancelled", "System reset cancelled. No changes were made.")
            return

        # All verifications passed - perform reset
        self._execute_system_reset()

    def _execute_system_reset(self) -> None:
        """Execute the actual system reset - complete wipe of all application data."""
        try:
            import shutil
            import subprocess
            import sys
            from pathlib import Path

            from PySide6.QtCore import QSettings, QStandardPaths
            from PySide6.QtWidgets import QApplication

            # Close database manager to release file locks
            try:
                from src.core.database_manager import close_database_manager

                close_database_manager()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                print(f"Warning: Could not close database manager: {e}")

            # Clear QSettings
            settings = QSettings()
            settings.clear()
            settings.sync()

            # Get the main AppData directory
            app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
            print(f"Resetting application data at: {app_data}")

            # Delete entire AppData directory and all subdirectories
            if app_data.exists():
                try:
                    shutil.rmtree(str(app_data))
                    print(f"✓ Deleted entire AppData directory: {app_data}")
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    print(f"Warning: Could not delete AppData directory: {e}")

            # Clear model cache instance
            try:
                from src.core.model_cache import ModelCache

                cache = ModelCache.get_instance()
                cache.clear()
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                print(f"Warning: Could not clear model cache: {e}")

            # Clear system temp files related to the application
            try:
                import tempfile

                temp_dir = Path(tempfile.gettempdir()) / "3dmm_screenshots"
                if temp_dir.exists():
                    shutil.rmtree(str(temp_dir))
                    print(f"✓ Deleted temporary screenshot directory: {temp_dir}")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                print(f"Warning: Could not clear temp files: {e}")

            # Clear any profile-related data
            try:
                # Check for profile data in common locations
                profile_locations = [
                    Path.home() / ".digital_workshop",
                    Path.home() / ".3dmm",
                    Path.home() / ".config" / "digital_workshop",
                    Path.home() / ".config" / "3dmm",
                ]

                for profile_path in profile_locations:
                    if profile_path.exists():
                        shutil.rmtree(str(profile_path))
                        print(f"✓ Deleted profile directory: {profile_path}")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                print(f"Warning: Could not clear profile directories: {e}")

            # Show success message
            QMessageBox.information(
                self,
                "System Reset Complete",
                "✓ Complete system reset finished successfully!\n\n"
                "All application data, settings, cache, and profiles have been deleted.\n"
                "The application will now close and restart as if running for the first time.",
            )

            # Relaunch the application
            subprocess.Popen([sys.executable, sys.argv[0]])

            # Close the application
            QApplication.instance().quit()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            QMessageBox.critical(self, "Reset Failed", f"An error occurred during system reset:\n\n{str(e)}")

    def _perform_nuclear_reset(self) -> None:
        """Perform nuclear reset by opening the Nuclear Reset dialog."""
        try:
            from src.gui.nuclear_reset_dialog import NuclearResetDialog

            dialog = NuclearResetDialog(self)
            dialog.exec()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to show nuclear reset dialog: %s", e)
            QMessageBox.critical(
                self, "Nuclear Reset Failed", f"An error occurred while opening nuclear reset:\n\n{str(e)}"
            )

    def save_settings(self) -> None:
        """Save advanced settings (no-op for this tab)."""
