#!/usr/bin/env python3
"""Comprehensive linting script to check all Python files."""

import os
import subprocess
import json
from pathlib import Path
from collections import defaultdict

def run_pylint_on_file(filepath):
    """Run pylint on a single file and extract score."""
    try:
        result = subprocess.run(
            ['pylint', filepath, '--exit-zero'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Extract score from output
        for line in result.stdout.split('\n'):
            if 'Your code has been rated at' in line:
                # Extract score like "8.46/10"
                parts = line.split('rated at ')
                if len(parts) > 1:
                    score_str = parts[1].split('/')[0].strip()
                    try:
                        return float(score_str)
                    except ValueError:
                        return None
        return None
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        print(f"Error linting {filepath}: {e}")
        return None

def main():
    """Main function to lint all Python files."""
    src_dir = Path('src')
    results = defaultdict(list)
    
    # Find all Python files
    py_files = sorted(src_dir.rglob('*.py'))
    print(f"Found {len(py_files)} Python files to lint\n")
    
    low_score_files = []
    
    for i, py_file in enumerate(py_files, 1):
        score = run_pylint_on_file(str(py_file))
        rel_path = py_file.relative_to(src_dir)
        
        if score is not None:
            results[score].append(str(rel_path))
            if score < 9.5:
                low_score_files.append((str(rel_path), score))
            
            if i % 50 == 0:
                print(f"Progress: {i}/{len(py_files)} files checked...")
    
    # Print summary
    print("\n" + "="*80)
    print("LINTING SUMMARY")
    print("="*80)
    
    # Sort by score
    sorted_scores = sorted(results.keys(), reverse=True)
    
    for score in sorted_scores:
        files = results[score]
        print(f"\nScore {score:.2f}/10: {len(files)} files")
        if score < 9.5:
            for f in sorted(files)[:5]:  # Show first 5
                print(f"  - {f}")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
    
    # Files below 9.5
    print("\n" + "="*80)
    print(f"FILES BELOW 9.5 SCORE: {len(low_score_files)}")
    print("="*80)
    
    low_score_files.sort(key=lambda x: x[1])
    for filepath, score in low_score_files[:20]:
        print(f"{score:.2f}/10 - {filepath}")
    
    if len(low_score_files) > 20:
        print(f"\n... and {len(low_score_files) - 20} more files below 9.5")
    
    # Save detailed report
    with open('lint_detailed_report.json', 'w') as f:
        json.dump({
            'total_files': len(py_files),
            'files_below_9_5': len(low_score_files),
            'low_score_files': low_score_files,
            'score_distribution': {str(k): len(v) for k, v in results.items()}
        }, f, indent=2)
    
    print(f"\nDetailed report saved to lint_detailed_report.json")

if __name__ == '__main__':
    main()

