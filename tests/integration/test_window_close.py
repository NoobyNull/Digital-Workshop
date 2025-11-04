#!/usr/bin/env python3
"""Test script to verify window close event and settings saving."""

import sys
import os
import time
from PySide6.QtCore import QTimer

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from src.core.application import Application
from src.core.application_config import ApplicationConfig

def main():
    """Run the application and close it after 12 seconds to see periodic saves."""
    config = ApplicationConfig.get_default()
    config = config.__class__(
        **{**config.__dict__,
           'log_level': 'DEBUG',
           'enable_console_logging': True,
           'log_human_readable': True}
    )

    app = Application(config)

    if not app.initialize():
        print("Application initialization failed")
        return 1

    # Schedule window close after 12 seconds (to see multiple periodic saves)
    def close_window():
        print("\n" + "="*70)
        print("TEST: Closing window after 12 seconds...")
        print("="*70 + "\n")
        if app.main_window:
            app.main_window.close()

    QTimer.singleShot(12000, close_window)
    
    # Run the application
    exit_code = app.run()
    print(f"\nApplication exited with code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    sys.exit(main())

