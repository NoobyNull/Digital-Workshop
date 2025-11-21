#!/usr/bin/env python3
"""
Automate promoting develop to main with an annotated version tag.

Flow:
1) Ensure the working tree is clean and fetch latest remote refs.
2) Push the source branch (default: develop) so CI has fresh commits.
3) Fast-forward merge into the target branch (default: main).
4) Create an annotated tag (default: v<version>) with a short changelog.
5) Push the target branch and tag to origin, allowing CI to build the EXE.

Intended usage on a clean repo:
    python scripts/auto_release_push.py --version 0.1.6
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUILD_PY = PROJECT_ROOT / "build_system" / "build.py"


class ReleaseError(RuntimeError):
    """Raised when the release automation hits a fatal condition."""


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command in the repo root and optionally raise on failure."""
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise ReleaseError(f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result


def ensure_clean_working_tree() -> None:
    """Abort if there are local modifications."""
    status = run_git(["status", "--porcelain"], check=True).stdout.strip()
    if status:
        raise ReleaseError("Working tree has uncommitted changes. Commit or stash before running the release.")


def get_current_branch() -> str:
    return run_git(["branch", "--show-current"], check=True).stdout.strip()


def fetch_all() -> None:
    run_git(["fetch", "--all", "--tags"], check=True)


def push_branch(branch: str) -> None:
    run_git(["push", "origin", branch], check=True)


def checkout_branch(branch: str) -> None:
    run_git(["checkout", branch], check=True)


def pull_ff(branch: str) -> None:
    run_git(["pull", "--ff-only", "origin", branch], check=True)


def merge_ff(source: str) -> None:
    run_git(["merge", "--ff-only", source], check=True)


def read_version(version_override: Optional[str]) -> str:
    if version_override:
        return version_override

    content = BUILD_PY.read_text(encoding="utf-8")
    match = re.search(r'"version":\s*"([^"]+)"', content)
    if not match:
        raise ReleaseError(f"Could not find version in {BUILD_PY}")
    return match.group(1)


def get_last_tag(tag_prefix: str) -> Optional[str]:
    """Return the most recent tag matching the prefix on the current HEAD."""
    result = run_git(
        ["describe", "--abbrev=0", "--tags", f"--match={tag_prefix}*"],
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def build_changelog(base: Optional[str], head: str) -> Tuple[str, str]:
    """
    Build a short changelog between base..head.

    Returns:
        tuple of (range_used, changelog_text)
    """
    if base:
        range_expr = f"{base}..{head}"
        args = ["log", range_expr, "--no-merges", "--pretty=format:- %h %s"]
    else:
        range_expr = head
        args = ["log", head, "-n", "20", "--no-merges", "--pretty=format:- %h %s"]

    result = run_git(args, check=False)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        lines = ["- No commit summaries available (empty range)."]
    return range_expr, "\n".join(lines)


def create_tag(tag_name: str, message: str) -> None:
    existing = run_git(["tag", "-l", tag_name], check=False).stdout.strip()
    if existing:
        raise ReleaseError(f"Tag {tag_name} already exists. Choose a new version or delete the tag first.")
    run_git(["tag", "-a", tag_name, "-m", message], check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Promote develop to main, tag a release, and trigger CI.",
    )
    parser.add_argument(
        "--version",
        help="Version to tag (defaults to value from build_system/build.py).",
    )
    parser.add_argument(
        "--source-branch",
        default="develop",
        help="Branch to promote (default: develop).",
    )
    parser.add_argument(
        "--target-branch",
        default="main",
        help="Branch that triggers CI (default: main).",
    )
    parser.add_argument(
        "--tag-prefix",
        default="v",
        help="Prefix for the annotated tag (default: v).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    starting_branch = get_current_branch()

    try:
        ensure_clean_working_tree()
        fetch_all()

        print(f"Pushing {args.source_branch} to origin...")
        push_branch(args.source_branch)

        print(f"Fast-forwarding {args.target_branch} with {args.source_branch}...")
        checkout_branch(args.target_branch)
        pull_ff(args.target_branch)
        try:
            merge_ff(args.source_branch)
        except ReleaseError as merge_error:
            # Avoid leaving main in a half-merged state.
            run_git(["merge", "--abort"], check=False)
            raise merge_error

        version = read_version(args.version)
        tag_name = f"{args.tag_prefix}{version}" if not version.startswith(args.tag_prefix) else version
        last_tag = get_last_tag(args.tag_prefix)
        range_used, changelog = build_changelog(last_tag, args.target_branch)

        tag_message = f"Release {tag_name}\n\nRange: {range_used}\n\nChanges:\n{changelog}"

        print(f"Creating annotated tag {tag_name} from {args.target_branch}...")
        create_tag(tag_name, tag_message)

        print(f"Pushing {args.target_branch} and tag {tag_name} to origin...")
        push_branch(args.target_branch)
        run_git(["push", "origin", tag_name], check=True)

        print(f"Release prepared. CI will build from {args.target_branch}.")
        print(f"Tag: {tag_name}")
        print(tag_message)
        return 0
    except ReleaseError as error:
        print(f"[release] {error}", file=sys.stderr)
        return 1
    finally:
        try:
            checkout_branch(starting_branch)
        except ReleaseError:
            pass


if __name__ == "__main__":
    sys.exit(main())
