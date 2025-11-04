#!/usr/bin/env python3
"""
Check dependencies for known security vulnerabilities.

Uses pip-audit to scan for vulnerable packages.
"""

import subprocess
import json
from pathlib import Path


def check_dependencies():
    """Check dependencies for security vulnerabilities."""
    print("Checking dependencies for security vulnerabilities...")
    
    try:
        # Run pip-audit
        result = subprocess.run(
            ["python", "-m", "pip_audit", "--desc", "--format", "json"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        
        if result.returncode == 0:
            print("✓ No vulnerabilities found")
            return True
        else:
            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                vulnerabilities = data.get("vulnerabilities", [])
                
                if vulnerabilities:
                    print(f"\n⚠ Found {len(vulnerabilities)} vulnerabilities:\n")
                    for vuln in vulnerabilities:
                        print(f"Package: {vuln.get('name')}")
                        print(f"Version: {vuln.get('version')}")
                        print(f"Vulnerability: {vuln.get('description')}")
                        print(f"Fix: {vuln.get('fix_versions')}")
                        print()
                    return False
            except json.JSONDecodeError:
                print("Error parsing pip-audit output")
                print(result.stdout)
                return False
                
    except FileNotFoundError:
        print("pip-audit not found. Installing...")
        subprocess.run(["pip", "install", "pip-audit"], check=True)
        # Retry
        return check_dependencies()
    except subprocess.TimeoutExpired:
        print("Operation timed out")
        return False


if __name__ == "__main__":
    success = check_dependencies()
    exit(0 if success else 1)

