#!/usr/bin/env python3
"""
Auto-tag and build helper.

Steps:
- Increment version tag (V0001, V0002, ...) locally and push to origin.
- Build onedir (multi-file) bundle using build_exe.spec.
- Build onefile bundle using pyinstaller_onefile.spec.
- Run NSIS installer packaging via make_installers.ps1 (uses onedir output).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_SYSTEM = REPO_ROOT / "build_system"


def run(
    cmd: List[str], cwd: Optional[Path] = None, check: bool = True
) -> subprocess.CompletedProcess:
    print(f"[RUN] {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def get_next_tag(prefix: str = "V") -> str:
    """Compute next tag like V0001, V0002 based on existing tags."""
    try:
        result = run(
            ["git", "tag", "--list", f"{prefix}[0-9][0-9][0-9][0-9]"], check=False
        )
        tags = [t.strip() for t in result.stdout.splitlines() if t.strip()]
    except Exception:
        tags = []
    max_num = 0
    for t in tags:
        m = re.fullmatch(rf"{re.escape(prefix)}(\d{{4}})", t)
        if m:
            max_num = max(max_num, int(m.group(1)))
    next_num = max_num + 1
    return f"{prefix}{next_num:04d}"


def create_and_push_tag(tag: str) -> None:
    run(["git", "tag", "-a", tag, "-m", f"Auto build tag {tag}"])
    run(["git", "push", "origin", tag])


def build_onedir() -> None:
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(BUILD_SYSTEM / "build_exe.spec"),
            "--distpath",
            str(REPO_ROOT / "dist"),
            "--workpath",
            str(REPO_ROOT / "build" / "onedir"),
        ],
        cwd=REPO_ROOT,
    )


def build_onefile() -> None:
    run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(BUILD_SYSTEM / "pyinstaller_onefile.spec"),
            "--distpath",
            str(REPO_ROOT / "dist"),
            "--workpath",
            str(REPO_ROOT / "build" / "onefile"),
        ],
        cwd=REPO_ROOT,
    )


def run_nsis(app_name: str = "Digital Workshop") -> None:
    ps_script = BUILD_SYSTEM / "make_installers.ps1"
    run(
        [
            "pwsh",
            "-File",
            str(ps_script),
            "-SkipBuild",
            "-AppName",
            app_name,
        ],
        cwd=REPO_ROOT,
    )


def main() -> int:
    tag = get_next_tag()
    print(f"[INFO] Next tag: {tag}")
    create_and_push_tag(tag)

    print("[INFO] Building onedir bundle...")
    build_onedir()

    print("[INFO] Building onefile bundle...")
    build_onefile()

    print("[INFO] Creating NSIS installer...")
    run_nsis(app_name="Digital Workshop")

    print("[OK] Tagging and builds completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
