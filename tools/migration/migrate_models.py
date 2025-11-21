#!/usr/bin/env python3
"""
Migrate models from old database to new AppData location.

This script consolidates all models from the old local database
to the new AppData-based database location.
"""

import sqlite3
import shutil
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QStandardPaths, QCoreApplication


def get_appdata_db_path():
    """Get the AppData database path."""
    try:
        # Set organization and app name for proper path resolution
        QCoreApplication.setApplicationName("Digital Workshop")
        QCoreApplication.setApplicationVersion("1.0.0")
        QCoreApplication.setOrganizationName("Digital Workshop Development Team")
        QCoreApplication.setOrganizationDomain("digitalworkshop.local")

        # QStandardPaths.AppDataLocation uses organization and app name
        # which creates: AppData/Roaming/Digital Workshop Development Team/Digital Workshop/
        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        app_data.mkdir(parents=True, exist_ok=True)
        return str(app_data / "digitalworkshop.db")
    except Exception:
        return "data/3dmm.db"


def migrate_models():
    """Migrate models from old database to new location."""

    old_db = Path("src/data/3dmm.db")
    new_db_path = get_appdata_db_path()
    new_db = Path(new_db_path)

    print(f"🔍 Old database: {old_db}")
    print(f"📍 New database: {new_db}")
    print()

    if not old_db.exists():
        print("❌ Old database not found!")
        return False

    # Check model counts
    try:
        old_conn = sqlite3.connect(str(old_db))
        old_cursor = old_conn.cursor()
        old_cursor.execute("SELECT COUNT(*) FROM models")
        old_count = old_cursor.fetchone()[0]
        old_conn.close()

        print(f"📊 Old database has {old_count} models")

        if old_count == 0:
            print("⚠️  Old database is empty, nothing to migrate")
            return True

    except Exception as e:
        print(f"❌ Error reading old database: {e}")
        return False

    # Backup new database if it exists
    if new_db.exists():
        backup_path = new_db.with_suffix(".db.backup")
        print(f"💾 Backing up existing database to {backup_path}")
        shutil.copy2(new_db, backup_path)

    # Copy old database to new location
    print(f"📋 Copying database...")
    try:
        new_db.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_db, new_db)
        print(f"✅ Database copied successfully!")

        # Verify
        new_conn = sqlite3.connect(str(new_db))
        new_cursor = new_conn.cursor()
        new_cursor.execute("SELECT COUNT(*) FROM models")
        new_count = new_cursor.fetchone()[0]
        new_conn.close()

        print(f"✅ New database now has {new_count} models")
        print()
        print("🎉 Migration complete! Your models are now in the correct location.")
        print(f"   Location: {new_db}")
        return True

    except Exception as e:
        print(f"❌ Error during migration: {e}")
        return False


if __name__ == "__main__":
    # Create QApplication for proper path resolution
    app = QApplication(sys.argv)

    print("=" * 60)
    print("Digital Workshop Model Migration Tool")
    print("=" * 60)
    print()

    success = migrate_models()
    sys.exit(0 if success else 1)
