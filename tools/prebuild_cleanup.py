#!/usr/bin/env python3
"""Pre-build cleanup and code quality helper.

Runs in CI or locally to:
  * remove stale build/test artifacts
  * apply import sorting and formatting
  * run lint checks
Use ``--ci`` to enable non-interactive behavior and stricter failures.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]

# Directories and files we can safely remove before a build.
CLEAN_DIRS = [
    "build",
    "dist",
    ".pytest_cache",
    ".cache",
    "htmlcov",
    "docs/_build",
    "reports/html",
]
CLEAN_FILES = [
    ".coverage",
    "coverage.xml",
    "pytest.xml",
    "junit.xml",
    "bandit-report.json",
    "semgrep-report.json",
    "safety-report.json",
    "security-fixes.json",
]
# File patterns removed recursively.
CLEAN_PATTERNS = ["**/*.pyc", "**/*.pyo", "**/__pycache__"]

DEFAULT_FORMAT_PATHS = [
    "run.py",
    "src",
    "tests",
    "tools",
    "build_system",
]
DEFAULT_LINT_PATHS = ["run.py", "src"]


def run_cmd(cmd: Sequence[str], desc: str) -> None:
    """Run a command and raise on failure."""
    print(f"\n[cmd] {desc}: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def clean_artifacts(extra_paths: Iterable[str]) -> None:
    """Remove known build/test artifacts to avoid stale outputs."""
    targets = set(CLEAN_DIRS + CLEAN_FILES)
    targets.update(extra_paths)
    for rel in sorted(targets):
        path = REPO_ROOT / rel
        if not path.exists():
            continue
        if path.is_dir():
            print(f"[clean] removing directory {path}")
            subprocess.run(["python", "-c", f"import shutil; shutil.rmtree(r'{path}')"], check=True)
        else:
            print(f"[clean] removing file {path}")
            path.unlink()

    for pattern in CLEAN_PATTERNS:
        for match in REPO_ROOT.rglob(pattern.replace("**/", "")):
            if not match.exists():
                continue
            if match.is_dir():
                print(f"[clean] removing directory {match}")
                subprocess.run(["python", "-c", f"import shutil; shutil.rmtree(r'{match}')"], check=True)
            else:
                print(f"[clean] removing file {match}")
                match.unlink()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Fail fast and avoid prompts; suitable for CI usage.",
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleanup of build/test artifacts.",
    )
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="Skip isort/black formatting steps.",
    )
    parser.add_argument(
        "--no-lint",
        action="store_true",
        help="Skip lint checks.",
    )
    parser.add_argument(
        "--with-tests",
        action="store_true",
        help="Run pytest after linting.",
    )
    parser.add_argument(
        "--extra-clean",
        nargs="*",
        default=[],
        help="Additional relative paths to delete before building.",
    )
    args = parser.parse_args(argv)

    if not args.no_clean:
        clean_artifacts(args.extra_clean)

    if not args.no_format:
        run_cmd(
            ["python", "-m", "isort", "--profile=black", *DEFAULT_FORMAT_PATHS],
            "format (isort)",
        )
        run_cmd(
            ["python", "-m", "black", *DEFAULT_FORMAT_PATHS],
            "format (black)",
        )

    if not args.no_lint:
        run_cmd(
            ["python", "-m", "pylint", *DEFAULT_LINT_PATHS],
            "lint (pylint)",
        )

    if args.with_tests:
        run_cmd(
            ["python", "-m", "pytest", "-q", "--disable-warnings", "--maxfail=1"],
            "tests (pytest)",
        )

    print("\n[ok] Pre-build cleanup and checks completed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
