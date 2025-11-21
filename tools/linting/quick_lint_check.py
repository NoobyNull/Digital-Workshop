#!/usr/bin/env python3
"""Quick lint check on key files."""

import subprocess
import sys
from pathlib import Path


def lint_file(filepath):
    """Run pylint on a single file and return score."""
    try:
        result = subprocess.run(
            ["pylint", filepath, "--exit-zero", "--disable=all", "--enable=E,F"],
            capture_output=True,
            text=True,
            timeout=15,
        )

        # Extract score
        for line in result.stdout.split("\n"):
            if "Your code has been rated at" in line:
                parts = line.split("rated at ")
                if len(parts) > 1:
                    score_str = parts[1].split("/")[0].strip()
                    try:
                        return float(score_str)
                    except ValueError:
                        return None
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    """Check key files."""
    key_files = [
        "src/main.py",
        "src/core/application.py",
        "src/gui/main_window.py",
        "src/gui/model_library.py",
        "src/gui/window/dock_manager.py",
        "src/gui/theme/theme_service.py",
        "src/gui/theme/unified_theme_manager.py",
    ]

    print("Checking key files for critical errors (E, F)...\n")

    all_good = True
    for filepath in key_files:
        p = Path(filepath)
        if not p.exists():
            print(f"⚠️  {filepath} - NOT FOUND")
            continue

        score = lint_file(filepath)
        if score is not None:
            status = "✅" if score >= 9.5 else "⚠️ "
            print(f"{status} {filepath}: {score:.2f}/10")
            if score < 9.5:
                all_good = False
        else:
            print(f"❌ {filepath} - Could not determine score")
            all_good = False

    return 0 if all_good else 1


if __name__ == "__main__":
    sys.exit(main())
