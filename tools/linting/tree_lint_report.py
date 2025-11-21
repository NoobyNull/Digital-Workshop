"""
Generate a directory tree report with linting scores for all Python files in src/.

This script creates a visual tree structure showing all files and directories
in the src/ folder, with pylint scores displayed next to Python files.
"""

import os
import subprocess
import json
from pathlib import Path
from typing import Dict, Optional


def get_pylint_score(file_path: Path) -> Optional[float]:
    """
    Get pylint score for a single Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        Pylint score as float, or None if scoring failed
    """
    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "pylint",
                str(file_path),
                "--score=y",
                "--exit-zero",
                "--disable=C0114,C0115,C0116,R0903,R0913,W0613,W0622,R0801",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        for line in result.stdout.split("\n"):
            if "rated at" in line.lower():
                # Extract score from line like 'Your code has been rated at 9.13/10'
                parts = line.split("rated at")
                if len(parts) > 1:
                    score_part = parts[1].strip().split("/")[0].strip()
                    try:
                        return float(score_part)
                    except ValueError:
                        return None
        return None
    except (subprocess.TimeoutExpired, Exception):
        return None


def collect_all_python_files(directory: Path) -> list:
    """
    Collect all Python files in directory recursively.

    Args:
        directory: Root directory to scan

    Returns:
        List of Path objects for all Python files
    """
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ and other unwanted directories
        dirs[:] = [d for d in dirs if d not in ["__pycache__", ".pytest_cache", ".git"]]

        for file in files:
            if file.endswith(".py"):
                python_files.append(Path(root) / file)

    return sorted(python_files)


def lint_all_files(python_files: list) -> Dict[str, float]:
    """
    Lint all Python files and return scores.

    Args:
        python_files: List of Python file paths

    Returns:
        Dictionary mapping file path to score
    """
    scores = {}
    total = len(python_files)

    print(f"Linting {total} Python files...")
    print()

    for i, file_path in enumerate(python_files, 1):
        if i % 10 == 0 or i == total:
            print(f"Progress: {i}/{total}", end="\r")

        score = get_pylint_score(file_path)
        scores[str(file_path)] = score

    print()
    print()
    return scores


def build_tree_with_scores(
    directory: Path, scores: Dict[str, float], prefix: str = "", is_last: bool = True
) -> list:
    """
    Build directory tree with linting scores.

    Args:
        directory: Directory to build tree for
        scores: Dictionary of file paths to scores
        prefix: Current line prefix for tree structure
        is_last: Whether this is the last item in parent directory

    Returns:
        List of formatted tree lines
    """
    if not directory.exists():
        return []

    items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))

    # Filter out unwanted directories
    items = [
        item
        for item in items
        if item.name not in ["__pycache__", ".pytest_cache", ".git", "node_modules"]
    ]

    lines = []

    for i, item in enumerate(items):
        is_last_item = i == len(items) - 1

        connector = "└── " if is_last_item else "├── "

        if item.is_file() and item.suffix == ".py":
            score = scores.get(str(item))
            if score is not None:
                score_str = f" [{score:.2f}/10]"
                # Color coding based on score
                if score >= 9.5:
                    score_str = f" ✓{score_str}"
                elif score >= 9.0:
                    score_str = f" •{score_str}"
                elif score < 8.0:
                    score_str = f" ⚠{score_str}"
            else:
                score_str = " [N/A]"
            lines.append(f"{prefix}{connector}{item.name}{score_str}")
        elif item.is_file():
            lines.append(f"{prefix}{connector}{item.name}")
        elif item.is_dir():
            lines.append(f"{prefix}{connector}{item.name}/")

            extension = "    " if is_last_item else "│   "
            new_prefix = prefix + extension

            sublines = build_tree_with_scores(item, scores, new_prefix, is_last_item)
            lines.extend(sublines)

    return lines


def generate_statistics(scores: Dict[str, float]) -> dict:
    """
    Generate statistics from linting scores.

    Args:
        scores: Dictionary of file paths to scores

    Returns:
        Dictionary of statistics
    """
    valid_scores = [s for s in scores.values() if s is not None]

    if not valid_scores:
        return {}

    return {
        "total_files": len(valid_scores),
        "average_score": sum(valid_scores) / len(valid_scores),
        "perfect_10": sum(1 for s in valid_scores if s == 10.0),
        "excellent_9_5_plus": sum(1 for s in valid_scores if s >= 9.5),
        "good_9_plus": sum(1 for s in valid_scores if s >= 9.0),
        "needs_work_below_8": sum(1 for s in valid_scores if s < 8.0),
        "min_score": min(valid_scores),
        "max_score": max(valid_scores),
    }


def main():
    """Main function to generate tree report."""
    src_dir = Path("src")

    if not src_dir.exists():
        print("Error: src/ directory not found")
        return

    print("=" * 80)
    print("DIRECTORY TREE WITH LINTING SCORES - src/")
    print("=" * 80)
    print()

    # Collect all Python files
    python_files = collect_all_python_files(src_dir)

    # Lint all files
    scores = lint_all_files(python_files)

    # Build tree
    print("=" * 80)
    print("TREE STRUCTURE")
    print("=" * 80)
    print()
    print("src/")

    tree_lines = build_tree_with_scores(src_dir, scores, "", True)
    for line in tree_lines:
        print(line)

    # Generate statistics
    print()
    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)
    stats = generate_statistics(scores)

    if stats:
        print(f"Total Python files: {stats['total_files']}")
        print(f"Average score: {stats['average_score']:.2f}/10")
        print(
            f"Perfect (10.0): {stats['perfect_10']} files ({stats['perfect_10']/stats['total_files']*100:.1f}%)"
        )
        print(
            f"Excellent (9.5+): {stats['excellent_9_5_plus']} files ({stats['excellent_9_5_plus']/stats['total_files']*100:.1f}%)"
        )
        print(
            f"Good (9.0+): {stats['good_9_plus']} files ({stats['good_9_plus']/stats['total_files']*100:.1f}%)"
        )
        print(
            f"Needs work (<8.0): {stats['needs_work_below_8']} files ({stats['needs_work_below_8']/stats['total_files']*100:.1f}%)"
        )
        print(f"Score range: {stats['min_score']:.2f} - {stats['max_score']:.2f}")

    print()
    print("=" * 80)
    print("Legend:")
    print("  ✓ [score/10] - Excellent (9.5+)")
    print("  • [score/10] - Good (9.0-9.49)")
    print("  ⚠ [score/10] - Needs work (<8.0)")
    print("=" * 80)


if __name__ == "__main__":
    main()
