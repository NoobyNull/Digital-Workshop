"""Detection utilities for oversized/monolithic Python modules."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


@dataclass
class ModuleMetrics:
    path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    docstring_lines: int
    blank_lines: int
    is_monolithic: bool
    severity: str
    timestamp: str


class MonolithicDetector:
    """Simple static counter that flags oversized Python modules."""

    def __init__(self, threshold: int = 500, max_workers: Optional[int] = None) -> None:
        import os

        self.threshold = threshold
        cpu_count = os.cpu_count() or 1
        self.max_workers = max_workers or max(1, cpu_count)

    # ---------------------------------------------------------------- analysis
    def analyze_file(self, file_path: Path) -> ModuleMetrics:
        file_path = Path(file_path)
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            text = ""

        total = 0
        code = 0
        comments = 0
        docstrings = 0
        blanks = 0
        in_docstring = False
        docstring_delim: Optional[str] = None

        for raw_line in text.splitlines():
            total += 1
            stripped = raw_line.strip()
            if not stripped:
                blanks += 1
                continue

            if in_docstring:
                docstrings += 1
                if docstring_delim and docstring_delim in stripped:
                    in_docstring = False
                continue

            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstrings += 1
                delim = stripped[:3]
                if stripped.count(delim) == 1:
                    in_docstring = True
                    docstring_delim = delim
                continue

            if stripped.startswith("#"):
                comments += 1
                continue

            if "#" in stripped:
                hash_index = stripped.find("#")
                left = stripped[:hash_index].strip()
                if left:
                    code += 1
                comments += 1
                continue

            code += 1

        is_monolithic = code >= self.threshold
        severity = self._classify_severity(code)
        return ModuleMetrics(
            path=str(file_path),
            total_lines=total,
            code_lines=code,
            comment_lines=comments,
            docstring_lines=docstrings,
            blank_lines=blanks,
            is_monolithic=is_monolithic,
            severity=severity if is_monolithic else "none",
            timestamp=datetime.utcnow().isoformat(timespec="seconds"),
        )

    def scan_directory(self, directory: Path) -> List[ModuleMetrics]:
        directory = Path(directory)
        if not directory.exists():
            return []
        files = sorted(p for p in directory.rglob("*.py") if p.is_file())
        if not files:
            return []

        results: List[ModuleMetrics] = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for metrics in executor.map(self.analyze_file, files):
                results.append(metrics)
        return results

    # ----------------------------------------------------------------- reports
    def generate_report(self, metrics: Iterable[ModuleMetrics]) -> dict:
        metric_list = list(metrics)
        total = len(metric_list)
        monolithic = [m for m in metric_list if m.is_monolithic]
        compliance_rate = 100.0
        if total:
            compliance_rate = (1 - len(monolithic) / total) * 100.0

        summary = {
            "total_files_analyzed": total,
            "monolithic_files_found": len(monolithic),
            "threshold": self.threshold,
            "compliance_rate": compliance_rate,
            "execution_timestamp": datetime.utcnow().isoformat(timespec="seconds"),
        }
        violations = [asdict(m) for m in monolithic]
        detailed = [asdict(m) for m in metric_list]
        return {"summary": summary, "violations": violations, "detailed_results": detailed}

    def save_report(self, report: dict, output_path: Path) -> None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)

    # ----------------------------------------------------------------- helpers
    def _classify_severity(self, code_lines: int) -> str:
        if code_lines >= self.threshold * 2:
            return "critical"
        if code_lines >= int(self.threshold * 1.5):
            return "major"
        if code_lines >= self.threshold:
            return "minor"
        return "none"
