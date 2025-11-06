"""
Simple Database Reset Utility

This script resets ONLY the database, leaving all other application data intact.
Run this when you want to start fresh with an empty database.
"""

import os
import sys
from pathlib import Path
import sqlite3


def detect_installation_type():
    """Detect if running from source or installed."""
    # Check if we're in a source directory (has src/ folder)
    src_dir = Path.cwd() / "src"
    if src_dir.exists() and src_dir.is_dir():
        return "source"
    return "installed"


def get_database_path():
    """Get the path to the database file based on installation type."""
    installation_type = detect_installation_type()

    if installation_type == "source":
        print("   ℹ️  Detected: Running from source (development mode)")
        # Running from source: use AppData with -Dev suffix
        if sys.platform == "win32":
            local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            db_path = local_appdata / "DigitalWorkshop-Dev" / "cache" / "data" / "3dmm.db"
        else:
            # Linux/Mac
            db_path = Path.home() / ".local" / "share" / "DigitalWorkshop-Dev" / "cache" / "data" / "3dmm.db"
    else:
        print("   ℹ️  Detected: Running from installed version")
        # Installed: use standard location
        if sys.platform == "win32":
            local_appdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
            db_path = local_appdata / "DigitalWorkshop" / "cache" / "data" / "3dmm.db"
        else:
            # Linux/Mac
            db_path = Path.home() / ".local" / "share" / "DigitalWorkshop" / "cache" / "data" / "3dmm.db"

    return db_path


def check_database_exists(db_path):
    """Check if database file exists."""
    return db_path.exists()


def get_database_info(db_path):
    """Get information about the database."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get table count
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        
        # Get model count
        try:
            cursor.execute("SELECT COUNT(*) FROM models")
            model_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            model_count = 0
        
        # Get file size
        file_size_mb = db_path.stat().st_size / (1024 * 1024)
        
        conn.close()
        
        return {
            "tables": table_count,
            "models": model_count,
            "size_mb": file_size_mb,
        }
    except Exception as e:
        return {"error": str(e)}


def delete_database(db_path):
    """Delete the database file."""
    try:
        if db_path.exists():
            db_path.unlink()
            return True, "Database deleted successfully"
        else:
            return False, "Database file not found"
    except PermissionError:
        return False, "Permission denied - database may be in use. Close Digital Workshop and try again."
    except Exception as e:
        return False, f"Failed to delete database: {e}"


def main():
    """Main function."""
    print("=" * 70)
    print("DATABASE RESET UTILITY")
    print("=" * 70)
    print()
    
    # Get database path
    db_path = get_database_path()
    print(f"Database location: {db_path}")
    print()
    
    # Check if database exists
    if not check_database_exists(db_path):
        print("❌ Database file not found.")
        print("   Nothing to reset.")
        input("\nPress Enter to exit...")
        return
    
    # Get database info
    print("📊 Current Database Info:")
    info = get_database_info(db_path)
    if "error" in info:
        print(f"   ⚠️  Could not read database: {info['error']}")
    else:
        print(f"   Tables: {info['tables']}")
        print(f"   Models: {info['models']}")
        print(f"   Size: {info['size_mb']:.2f} MB")
    print()
    
    # Confirm deletion
    print("⚠️  WARNING: This will DELETE the database file.")
    print("   All models, metadata, and settings will be lost.")
    print("   This action CANNOT be undone.")
    print()
    
    response = input("Type 'DELETE' to confirm: ").strip()
    
    if response != "DELETE":
        print("\n❌ Reset cancelled.")
        input("\nPress Enter to exit...")
        return
    
    # Delete database
    print("\n🗑️  Deleting database...")
    success, message = delete_database(db_path)
    
    if success:
        print(f"✅ {message}")
        print()
        print("The database has been reset.")
        print("Next time you start Digital Workshop, a fresh database will be created.")
    else:
        print(f"❌ {message}")
    
    print()
    input("Press Enter to exit...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Reset cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)

