#!/usr/bin/env python3
"""
File Naming Convention Validator

Validates file naming conventions to detect adjective-based
names that indicate replacement files or technical debt.
"""

import re
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class NamingViolation:
    """Represents a naming convention violation."""

    file_path: str
    file_name: str
    detected_adjectives: List[str]
    violation_type: str
    severity: str
    suggested_name: str
    line_number: int = 0  # Files don't have line numbers, but keeping for compatibility


@dataclass
class NamingValidationResult:
    """Results of naming convention validation."""

    total_files: int
    valid_files: int
    violated_files: int
    violations: List[NamingViolation]
    compliance_rate: float
    timestamp: str
    processing_time: float = 0.0


class AdjectiveDetector:
    """Detects descriptive adjectives in filenames."""

    def __init__(self):
        # Comprehensive list of replacement/description adjectives
        self.replacement_adjectives = {
            # Basic replacement indicators
            "refactored",
            "new",
            "old",
            "backup",
            "temp",
            "temporary",
            "original",
            "copy",
            "duplicate",
            "alternative",
            "alternate",
            # Improvement indicators
            "improved",
            "enhanced",
            "optimized",
            "better",
            "updated",
            "revised",
            "modified",
            "changed",
            "fixed",
            "corrected",
            # State indicators
            "working",
            "final",
            "complete",
            "incomplete",
            "draft",
            "experimental",
            "testing",
            "debug",
            "development",
            "prod",
            "production",
            "staging",
            "beta",
            "alpha",
            "stable",
            # Quality indicators
            "good",
            "bad",
            "better",
            "best",
            "worst",
            "fast",
            "slow",
            "quick",
            "slow",
            "efficient",
            "inefficient",
            "clean",
            "dirty",
            # Temporal indicators
            "recent",
            "latest",
            "current",
            "previous",
            "next",
            "future",
            "past",
            "ancient",
            "modern",
            "legacy",
            "obsolete",
            # Version indicators
            "v1",
            "v2",
            "v3",
            "version1",
            "version2",
            "version3",
            "1.0",
            "2.0",
            "3.0",
            "final",
            "release",
            "candidate",
            # Status indicators
            "active",
            "inactive",
            "enabled",
            "disabled",
            "on",
            "off",
            "true",
            "false",
            "yes",
            "no",
            "positive",
            "negative",
            # Descriptive terms
            "simple",
            "complex",
            "basic",
            "advanced",
            "standard",
            "custom",
            "special",
            "generic",
            "specific",
            "general",
            # Action indicators (when used as adjectives)
            "running",
            "stopped",
            "starting",
            "ending",
            "processing",
            "loading",
            "saving",
            "creating",
            "deleting",
            "updating",
        }

        # Domain-specific terms that should NOT be flagged
        self.domain_terms = {
            # Technical domain terms
            "user",
            "admin",
            "system",
            "network",
            "database",
            "api",
            "http",
            "https",
            "ftp",
            "ssh",
            "tcp",
            "udp",
            "ip",
            "file",
            "folder",
            "directory",
            "path",
            "url",
            "uri",
            # Business domain terms
            "customer",
            "product",
            "order",
            "invoice",
            "payment",
            "account",
            "profile",
            "session",
            "token",
            "auth",
            # Application-specific terms
            "main",
            "app",
            "core",
            "base",
            "common",
            "shared",
            "util",
            "helper",
            "manager",
            "service",
            "client",
            # Data terms
            "model",
            "view",
            "controller",
            "entity",
            "record",
            "data",
            "info",
            "config",
            "setting",
            "option",
        }

        # Compile regex patterns for efficient matching
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficient matching."""
        # Pattern for detecting adjectives in filenames
        # Matches word boundaries to avoid partial matches
        adjective_pattern = (
            r"\b("
            + "|".join(re.escape(word) for word in self.replacement_adjectives)
            + r")\b"
        )
        self.adjective_regex = re.compile(adjective_pattern, re.IGNORECASE)

        # Pattern for compound words (e.g., "new_model", "old_handler")
        compound_pattern = (
            r"\b("
            + "|".join(re.escape(word) for word in self.replacement_adjectives)
            + r")_[a-zA-Z0-9_]+"
        )
        self.compound_regex = re.compile(compound_pattern, re.IGNORECASE)

        # Pattern for version numbers (v1, v2, 1.0, 2.0, etc.)
        version_pattern = r"\b(v\d+|version\d+|\d+\.\d+)\b"
        self.version_regex = re.compile(version_pattern, re.IGNORECASE)

    def detect_adjectives(self, filename: str) -> List[str]:
        """
        Detect descriptive adjectives in a filename.

        Args:
            filename: The filename to analyze

        Returns:
            List of detected adjectives
        """
        detected = []
        base_name = Path(filename).stem  # Remove extension

        # Check for simple adjective matches
        simple_matches = self.adjective_regex.findall(base_name)
        detected.extend(simple_matches)

        # Check for compound word matches (adjective followed by underscore and more text)
        compound_matches = self.compound_regex.findall(base_name)
        detected.extend(compound_matches)

        # Check for version indicators
        version_matches = self.version_regex.findall(base_name)
        detected.extend(version_matches)

        # Also check for adjectives that might be in the middle of compound words
        # Split by underscores and check each part
        parts = base_name.split("_")
        for part in parts:
            if part.lower() in self.replacement_adjectives:
                detected.append(part.lower())

        # Check for version patterns in individual parts
        for part in parts:
            version_match = self.version_regex.search(part)
            if version_match:
                detected.append(version_match.group(1).lower())

        # Remove duplicates and return
        return list(set(detected))

    def is_domain_term(self, word: str) -> bool:
        """
        Check if a word is a legitimate domain term.

        Args:
            word: Word to check

        Returns:
            True if it's a domain term, False otherwise
        """
        return word.lower() in self.domain_terms

    def suggest_improved_name(
        self, filename: str, detected_adjectives: List[str]
    ) -> str:
        """
        Suggest an improved filename without descriptive adjectives.

        Args:
            filename: Original filename
            detected_adjectives: List of detected adjectives

        Returns:
            Suggested improved filename
        """
        base_name = Path(filename).stem
        extension = Path(filename).suffix

        # Remove detected adjectives from the filename
        improved_name = base_name
        for adjective in detected_adjectives:
            # Remove adjective and following underscore/separator
            pattern = rf"\b{re.escape(adjective)}_?"
            improved_name = re.sub(pattern, "", improved_name, flags=re.IGNORECASE)

        # Also remove version patterns that might be left behind
        version_patterns = [
            r"_v\d+",  # _v1, _v2, etc.
            r"_version\d+",  # _version1, _version2, etc.
            r"_\d+\.\d+",  # _1.0, _2.0, etc.
            r"v\d+",  # v1, v2, etc. (standalone)
            r"version\d+",  # version1, version2, etc. (standalone)
            r"\d+\.\d+",  # 1.0, 2.0, etc. (standalone)
        ]

        for pattern in version_patterns:
            improved_name = re.sub(pattern, "", improved_name, flags=re.IGNORECASE)

        # Clean up any double underscores or trailing separators
        improved_name = re.sub(r"_+", "_", improved_name).strip("_")

        # If the name becomes empty or too short, suggest a generic name
        if not improved_name or len(improved_name) < 3:
            improved_name = "component"

        return improved_name + extension


class NamingConventionValidator:
    """Main validator class for naming conventions."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.detector = AdjectiveDetector()
        self.results: List[NamingViolation] = []

    def validate_filename(self, file_path: Path) -> Optional[NamingViolation]:
        """
        Validate a single filename for naming convention compliance.

        Args:
            file_path: Path to the file

        Returns:
            NamingViolation if violation found, None otherwise
        """
        filename = file_path.name
        detected_adjectives = self.detector.detect_adjectives(filename)

        if not detected_adjectives:
            return None  # No violation

        # Filter out domain terms to avoid false positives
        filtered_adjectives = [
            adj for adj in detected_adjectives if not self.detector.is_domain_term(adj)
        ]

        if not filtered_adjectives:
            return None  # Only domain terms detected

        # Determine severity based on number and type of adjectives
        severity = self._determine_severity(filtered_adjectives)

        # Generate suggested name
        suggested_name = self.detector.suggest_improved_name(
            filename, filtered_adjectives
        )

        return NamingViolation(
            file_path=str(file_path),
            file_name=filename,
            detected_adjectives=filtered_adjectives,
            violation_type="descriptive_adjective",
            severity=severity,
            suggested_name=suggested_name,
            line_number=0,
        )

    def _determine_severity(self, adjectives: List[str]) -> str:
        """
        Determine violation severity based on detected adjectives.

        Args:
            adjectives: List of detected adjectives

        Returns:
            Severity level (critical, major, minor)
        """
        critical_adjectives = {"backup", "temp", "temporary", "old", "obsolete"}
        major_adjectives = {"refactored", "new", "improved", "enhanced", "optimized"}

        if any(adj in critical_adjectives for adj in adjectives):
            return "critical"
        elif any(adj in major_adjectives for adj in adjectives):
            return "major"
        else:
            return "minor"

    def scan_directory(
        self, root_path: Path, progress_callback: Optional[callable] = None
    ) -> NamingValidationResult:
        """
        Recursively scan directory for naming convention violations.

        Args:
            root_path: Root directory to scan
            progress_callback: Optional callback for progress updates

        Returns:
            NamingValidationResult with analysis results
        """
        start_time = time.time()

        # Get all files (excluding directories)
        all_files = [f for f in root_path.rglob("*") if f.is_file()]
        logger.info(f"Found {len(all_files)} files to validate")

        violations = []
        valid_count = 0
        processed_count = 0

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.validate_filename, file_path): file_path
                for file_path in all_files
            }

            for future in as_completed(future_to_file):
                try:
                    result = future.result()
                    if result is None:
                        valid_count += 1
                    else:
                        violations.append(result)

                    processed_count += 1

                    # Progress callback for large directories
                    if progress_callback and processed_count % 100 == 0:
                        progress = (processed_count / len(all_files)) * 100
                        progress_callback(processed_count, len(all_files), progress)

                except Exception as e:
                    file_path = future_to_file[future]
                    logger.error(f"Failed to validate {file_path}: {e}")

        processing_time = time.time() - start_time
        total_files = len(all_files)
        compliance_rate = (valid_count / total_files * 100) if total_files > 0 else 100

        return NamingValidationResult(
            total_files=total_files,
            valid_files=valid_count,
            violated_files=len(violations),
            violations=violations,
            compliance_rate=compliance_rate,
            timestamp=__import__("datetime").datetime.now().isoformat(),
            processing_time=processing_time,
        )

    def generate_report(self, result: NamingValidationResult) -> Dict[str, Any]:
        """
        Generate a comprehensive validation report.

        Args:
            result: NamingValidationResult object

        Returns:
            Dictionary containing the validation report
        """
        # Group violations by severity
        violations_by_severity = {
            "critical": [v for v in result.violations if v.severity == "critical"],
            "major": [v for v in result.violations if v.severity == "major"],
            "minor": [v for v in result.violations if v.severity == "minor"],
        }

        # Count most common adjectives
        adjective_counts = {}
        for violation in result.violations:
            for adjective in violation.detected_adjectives:
                adjective_counts[adjective] = adjective_counts.get(adjective, 0) + 1

        report = {
            "summary": {
                "total_files_analyzed": result.total_files,
                "valid_files": result.valid_files,
                "violated_files": result.violated_files,
                "compliance_rate": result.compliance_rate,
                "analysis_timestamp": result.timestamp,
                "processing_time_seconds": result.processing_time,
            },
            "violations_by_severity": {
                severity: [
                    {
                        "file_path": v.file_path,
                        "file_name": v.file_name,
                        "detected_adjectives": v.detected_adjectives,
                        "suggested_name": v.suggested_name,
                    }
                    for v in violations
                ]
                for severity, violations in violations_by_severity.items()
            },
            "adjective_frequency": dict(
                sorted(adjective_counts.items(), key=lambda x: x[1], reverse=True)
            ),
            "recommendations": self._generate_recommendations(result),
        }

        return report

    def _generate_recommendations(self, result: NamingValidationResult) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []

        if result.violated_files == 0:
            recommendations.append("All files follow naming conventions. Great job!")
        else:
            recommendations.append(
                f"Found {result.violated_files} files with descriptive adjectives."
            )

            if result.compliance_rate < 80:
                recommendations.append(
                    "Compliance rate is below 80%. Consider systematic renaming."
                )
            elif result.compliance_rate < 95:
                recommendations.append(
                    "Compliance rate could be improved. Review flagged files."
                )

            # Suggest most common fixes
            if result.violations:
                recommendations.append(
                    "Focus on removing the most common descriptive adjectives first."
                )

        return recommendations

    def save_report(self, report: Dict[str, Any], output_path: Path):
        """Save validation report to JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Report saved to {output_path}")


def progress_callback(processed: int, total: int, percentage: float):
    """Progress callback for long-running operations."""
    print(
        f"\rProgress: {processed}/{total} files ({percentage:.1f}%)", end="", flush=True
    )


def main():
    """Main entry point for the naming convention validator."""
    parser = argparse.ArgumentParser(
        description="Validate file naming conventions and detect descriptive adjectives"
    )
    parser.add_argument("path", help="Directory or file path to validate")
    parser.add_argument(
        "--output",
        type=str,
        default="naming_convention_report.json",
        help="Output report file path",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of worker threads (default: 4)"
    )
    parser.add_argument(
        "--min-compliance",
        type=float,
        default=95.0,
        help="Minimum compliance percentage (default: 95.0)",
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    # Initialize validator
    validator = NamingConventionValidator(max_workers=args.workers)

    # Validate target path
    target_path = Path(args.path)
    if not target_path.exists():
        logger.error(f"Path does not exist: {target_path}")
        sys.exit(1)

    logger.info(f"Starting naming convention validation of {target_path}")

    if target_path.is_file():
        # Single file validation
        violation = validator.validate_filename(target_path)
        if violation:
            print(f"VIOLATION: {violation.file_name}")
            print(f"  Detected adjectives: {violation.detected_adjectives}")
            print(f"  Suggested name: {violation.suggested_name}")
            result = NamingValidationResult(
                total_files=1,
                valid_files=0,
                violated_files=1,
                violations=[violation],
                compliance_rate=0.0,
                timestamp=__import__("datetime").datetime.now().isoformat(),
            )
        else:
            print("VALID: No naming convention violations found")
            result = NamingValidationResult(
                total_files=1,
                valid_files=1,
                violated_files=0,
                violations=[],
                compliance_rate=100.0,
                timestamp=__import__("datetime").datetime.now().isoformat(),
            )
    else:
        # Directory validation
        progress_cb = None if args.quiet else progress_callback
        result = validator.scan_directory(target_path, progress_cb)
        print()  # New line after progress

    # Generate and save report
    report = validator.generate_report(result)
    validator.save_report(report, Path(args.output))

    # Print summary
    print(f"\n=== Naming Convention Validation Summary ===")
    print(f"Files analyzed: {report['summary']['total_files_analyzed']}")
    print(f"Valid files: {report['summary']['valid_files']}")
    print(f"Violated files: {report['summary']['violated_files']}")
    print(f"Compliance rate: {report['summary']['compliance_rate']:.2f}%")
    print(
        f"Processing time: {report['summary']['processing_time_seconds']:.2f} seconds"
    )

    if report["violations_by_severity"]["critical"]:
        print(
            f"\nCritical violations: {len(report['violations_by_severity']['critical'])}"
        )
        for violation in report["violations_by_severity"]["critical"][
            :5
        ]:  # Show first 5
            print(f"  - {violation['file_name']}: {violation['detected_adjectives']}")

    # Check compliance threshold
    compliance_ok = report["summary"]["compliance_rate"] >= args.min_compliance
    if not compliance_ok:
        print(
            f"\nWARNING: Compliance rate {report['summary']['compliance_rate']:.2f}% "
            f"is below minimum threshold {args.min_compliance}%"
        )

    return 0 if compliance_ok else 1


if __name__ == "__main__":
    sys.exit(main())
