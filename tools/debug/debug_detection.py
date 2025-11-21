#!/usr/bin/env python3
"""Debug script to test adjective detection."""

import sys

sys.path.append(".")

from tools.maintenance.naming_validator import AdjectiveDetector


def test_detection():
    detector = AdjectiveDetector()

    # Test the problematic filename
    filename = "final_release.py"
    detected = detector.detect_adjectives(filename)

    print(f"Testing filename: {filename}")
    print(f"Detected adjectives: {detected}")
    print(f"Expected: ['final', 'release']")

    # Test individual parts
    base_name = filename.replace(".py", "")
    parts = base_name.split("_")
    print(f"Parts: {parts}")

    for part in parts:
        if part.lower() in detector.replacement_adjectives:
            print(f"Found '{part}' in replacement_adjectives")
        else:
            print(f"'{part}' NOT found in replacement_adjectives")

    # Test suggested name
    suggested = detector.suggest_improved_name(filename, detected)
    print(f"Suggested name: {suggested}")


if __name__ == "__main__":
    test_detection()
