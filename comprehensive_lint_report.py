#!/usr/bin/env python3
"""Comprehensive lint report for all Python files."""

import subprocess
import sys
from pathlib import Path
from collections import defaultdict

def lint_file(filepath):
    """Run pylint on a single file and return score."""
    try:
        result = subprocess.run(
            ['pylint', filepath, '--exit-zero'],
            capture_output=True,
            text=True,
            timeout=15
        )
        
        for line in result.stdout.split('\n'):
            if 'Your code has been rated at' in line:
                parts = line.split('rated at ')
                if len(parts) > 1:
                    score_str = parts[1].split('/')[0].strip()
                    try:
                        return float(score_str)
                    except ValueError:
                        return None
        return None
    except Exception:
        return None

def main():
    """Generate comprehensive report."""
    src_dir = Path('src')
    py_files = sorted(src_dir.rglob('*.py'))
    
    print(f"Linting {len(py_files)} Python files...\n")
    
    scores = {}
    below_95 = []
    
    for i, py_file in enumerate(py_files, 1):
        score = lint_file(str(py_file))
        rel_path = str(py_file.relative_to(src_dir))
        
        if score is not None:
            scores[rel_path] = score
            if score < 9.5:
                below_95.append((rel_path, score))
        
        if i % 50 == 0:
            print(f"Progress: {i}/{len(py_files)}")
    
    # Statistics
    valid_scores = [s for s in scores.values() if s is not None]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    print("\n" + "="*80)
    print("LINTING REPORT SUMMARY")
    print("="*80)
    print(f"Total files linted: {len(scores)}")
    print(f"Average score: {avg_score:.2f}/10")
    print(f"Files below 9.5: {len(below_95)}")
    print(f"Files at 9.5+: {len(scores) - len(below_95)}")
    
    if below_95:
        print("\n" + "="*80)
        print("FILES BELOW 9.5 SCORE")
        print("="*80)
        below_95.sort(key=lambda x: x[1])
        for filepath, score in below_95[:30]:
            print(f"{score:6.2f}/10 - {filepath}")
        
        if len(below_95) > 30:
            print(f"\n... and {len(below_95) - 30} more files")
    
    # Score distribution
    print("\n" + "="*80)
    print("SCORE DISTRIBUTION")
    print("="*80)
    
    ranges = [
        (10.0, 10.0, "Perfect (10.0)"),
        (9.9, 9.99, "Excellent (9.9-9.99)"),
        (9.5, 9.89, "Very Good (9.5-9.89)"),
        (9.0, 9.49, "Good (9.0-9.49)"),
        (8.0, 8.99, "Fair (8.0-8.99)"),
        (0.0, 7.99, "Needs Work (<8.0)"),
    ]
    
    for min_score, max_score, label in ranges:
        count = sum(1 for s in valid_scores if min_score <= s <= max_score)
        pct = (count / len(valid_scores) * 100) if valid_scores else 0
        print(f"{label:30} {count:4d} files ({pct:5.1f}%)")
    
    return 0 if len(below_95) == 0 else 1

if __name__ == '__main__':
    sys.exit(main())

