"""Filename hygiene utilities used by the quality test-suite."""

from __future__ import annotations

import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, Iterable, List, Optional


@dataclass
class NamingViolation:
    file_name: str
    file_path: str
    detected_adjectives: List[str]
    severity: str
    suggested_name: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class NamingValidationResult:
    total_files: int
    violated_files: int
    valid_files: int
    compliance_rate: float
    violations: List[NamingViolation]
    processing_time_seconds: float


class AdjectiveDetector:
    """Detects non-descriptive adjectives/qualifiers inside filenames."""

    _ADJECTIVES = {
        "refactored",
        "new",
        "old",
        "backup",
        "temp",
        "improved",
        "enhanced",
        "optimized",
        "modern",
        "legacy",
        "experimental",
        "working",
        "final",
        "release",
        "beta",
        "alpha",
        "prototype",
        "draft",
    }
    _DOMAIN_TERMS = {
        "user",
        "network",
        "database",
        "file",
        "api",
        "system",
        "admin",
        "customer",
        "product",
        "main",
        "core",
        "shared",
        "common",
        "data",
        "view",
        "model",
        "controller",
        "service",
        "client",
        "server",
    }

    def detect_adjectives(self, filename: str) -> List[str]:
        stem = Path(filename).stem.lower()
        tokens = [token for token in re.split(r"[_\-]+", stem) if token]
        matches: List[str] = []
        for token in tokens:
            if token in self._ADJECTIVES:
                matches.append(token)
                continue
            if re.fullmatch(r"v\d+", token) or re.fullmatch(r"version\d+", token):
                matches.append(token)
                continue
            if re.fullmatch(r"\d+\.\d+", token):
                matches.append(token)
        return matches

    def is_domain_term(self, word: str) -> bool:
        return word.lower() in self._DOMAIN_TERMS

    def suggest_improved_name(self, filename: str, adjectives: Iterable[str]) -> str:
        adjectives_lower = {adj.lower() for adj in adjectives}
        path = Path(filename)
        stem_tokens = [token for token in re.split(r"[.\-_]+", path.stem) if token]
        filtered = [
            token
            for token in stem_tokens
            if token.lower() not in adjectives_lower
            and token.lower() not in self._ADJECTIVES
            and not re.fullmatch(r"(v\d+|version\d+|\d+\.\d+)", token.lower())
        ]
        if not filtered:
            filtered = ["file"]
        new_stem = "_".join(filtered)
        return f"{new_stem}{path.suffix}"


class NamingConventionValidator:
    """Validates filenames against adjective/qualifier rules."""

    def __init__(self, max_workers: int = 4) -> None:
        self.max_workers = max(1, max_workers)
        self.detector = AdjectiveDetector()
        self._severity_priority = ["critical", "major", "minor"]
        self._severity_lookup = {
            "critical": {"backup", "temp", "old"},
            "major": {"new", "refactored", "improved", "enhanced", "optimized", "modern", "experimental", "legacy"},
            "minor": {"working", "prototype", "draft", "final", "release", "beta", "alpha"},
        }

    def validate_filename(self, file_path: Path) -> Optional[NamingViolation]:
        file_path = Path(file_path)
        adjectives = self.detector.detect_adjectives(file_path.name)
        filtered = [adj for adj in adjectives if not self.detector.is_domain_term(adj)]
        if not filtered:
            return None
        severity = self._classify_severity(filtered)
        suggested = self.detector.suggest_improved_name(file_path.name, filtered)
        return NamingViolation(
            file_name=file_path.name,
            file_path=str(file_path),
            detected_adjectives=filtered,
            severity=severity,
            suggested_name=suggested,
        )

    def scan_directory(
        self,
        directory: Path,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
    ) -> NamingValidationResult:
        directory = Path(directory)
        start = time.perf_counter()
        files = sorted(p for p in directory.rglob("*") if p.is_file())
        violations: List[NamingViolation] = []
        if files:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                for index, violation in enumerate(executor.map(self.validate_filename, files), start=1):
                    if violation:
                        violations.append(violation)
                    if progress_callback:
                        progress_callback(index, len(files), round(index / len(files) * 100, 2))

        total = len(files)
        violated = len(violations)
        valid = total - violated
        compliance = 100.0 if total == 0 else round((valid / total) * 100.0, 2)
        duration = time.perf_counter() - start
        return NamingValidationResult(
            total_files=total,
            violated_files=violated,
            valid_files=valid,
            compliance_rate=compliance,
            violations=violations,
            processing_time_seconds=duration,
        )

    def generate_report(self, result: NamingValidationResult) -> dict:
        summary = {
            "total_files_analyzed": result.total_files,
            "violated_files": result.violated_files,
            "valid_files": result.valid_files,
            "compliance_rate": result.compliance_rate,
            "processing_time_seconds": result.processing_time_seconds,
        }
        violations_by_severity = {"critical": [], "major": [], "minor": []}
        adjective_frequency = {}
        for violation in result.violations:
            violations_by_severity.setdefault(violation.severity, [])
            violations_by_severity[violation.severity].append(violation.to_dict())
            for adj in violation.detected_adjectives:
                adjective_frequency[adj] = adjective_frequency.get(adj, 0) + 1

        recommendations = self._build_recommendations(result)
        return {
            "summary": summary,
            "violations_by_severity": violations_by_severity,
            "adjective_frequency": adjective_frequency,
            "recommendations": recommendations,
        }

    @staticmethod
    def save_report(report: dict, output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    # ----------------------------------------------------------------- helpers
    def _classify_severity(self, adjectives: Iterable[str]) -> str:
        normalized = [adj.lower() for adj in adjectives]
        for severity in self._severity_priority:
            keywords = self._severity_lookup.get(severity, set())
            if any(adj in keywords or self._is_version_token(adj) for adj in normalized):
                return severity
        return "minor"

    @staticmethod
    def _is_version_token(token: str) -> bool:
        return bool(re.fullmatch(r"(v\d+|version\d+|\d+\.\d+)", token))

    def _build_recommendations(self, result: NamingValidationResult) -> List[str]:
        recommendations = []
        if result.violated_files == 0:
            recommendations.append("All filenames comply with the current policy.")
            return recommendations

        recommendations.append(
            f"Resolve {result.violated_files} non-compliant filenames to raise compliance above {result.compliance_rate:.2f}%."
        )
        if any(v.severity == "critical" for v in result.violations):
            recommendations.append("Remove urgent adjectives like 'backup' or 'temp' from production assets.")
        if any("new" in v.detected_adjectives for v in result.violations):
            recommendations.append("Replace transitional adjectives (e.g., 'new', 'refactored') with descriptive names.")
        return recommendations
