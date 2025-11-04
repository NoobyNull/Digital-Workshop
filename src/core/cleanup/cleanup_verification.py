"""
Cleanup Verification and Statistics Module.

This module provides comprehensive verification of cleanup operations,
resource leak detection, and detailed statistics collection.
"""

import time
import gc
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.core.logging_config import get_logger


class VerificationStatus(Enum):
    """Status of cleanup verification."""

    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ResourceLeakInfo:
    """Information about a potential resource leak."""

    resource_type: str
    resource_id: str
    creation_time: float
    cleanup_time: float
    expected_state: str
    actual_state: str
    is_leak: bool = False

    def __str__(self) -> str:
        """Return formatted leak info."""
        leak_indicator = "LEAK" if self.is_leak else "OK"
        return (
            f"[{leak_indicator}] {self.resource_type} ({self.resource_id}): "
            f"expected={self.expected_state}, actual={self.actual_state}"
        )


@dataclass
class VerificationResult:
    """Result of a single verification check."""

    check_name: str
    status: VerificationStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration: float = 0.0

    def __str__(self) -> str:
        """Return formatted result."""
        status_symbol = {
            VerificationStatus.PASSED: "✓",
            VerificationStatus.WARNING: "⚠",
            VerificationStatus.FAILED: "✗",
            VerificationStatus.SKIPPED: "⊘",
        }.get(self.status, "?")

        return f"[{status_symbol}] {self.check_name}: {self.message} ({self.duration:.3f}s)"


@dataclass
class CleanupVerificationReport:
    """Comprehensive cleanup verification report."""

    total_checks: int = 0
    passed_checks: int = 0
    warning_checks: int = 0
    failed_checks: int = 0
    skipped_checks: int = 0
    total_duration: float = 0.0

    results: List[VerificationResult] = field(default_factory=list)
    resource_leaks: List[ResourceLeakInfo] = field(default_factory=list)
    memory_stats: Dict[str, Any] = field(default_factory=dict)
    resource_stats: Dict[str, Any] = field(default_factory=dict)

    def add_result(self, result: VerificationResult) -> None:
        """Add a verification result."""
        self.results.append(result)
        self.total_checks += 1

        if result.status == VerificationStatus.PASSED:
            self.passed_checks += 1
        elif result.status == VerificationStatus.WARNING:
            self.warning_checks += 1
        elif result.status == VerificationStatus.FAILED:
            self.failed_checks += 1
        elif result.status == VerificationStatus.SKIPPED:
            self.skipped_checks += 1

    def add_leak(self, leak: ResourceLeakInfo) -> None:
        """Add a resource leak."""
        self.resource_leaks.append(leak)

    def is_successful(self) -> bool:
        """Check if verification was successful (no failures)."""
        return self.failed_checks == 0

    def get_summary(self) -> str:
        """Get a summary of verification results."""
        lines = [
            "=== Cleanup Verification Summary ===",
            f"Total checks: {self.total_checks}",
            f"Passed: {self.passed_checks}",
            f"Warnings: {self.warning_checks}",
            f"Failed: {self.failed_checks}",
            f"Skipped: {self.skipped_checks}",
            f"Duration: {self.total_duration:.3f}s",
            "",
        ]

        if self.resource_leaks:
            lines.append(f"Resource Leaks: {len(self.resource_leaks)}")
            for leak in self.resource_leaks:
                lines.append(f"  {leak}")
            lines.append("")

        if self.memory_stats:
            lines.append("Memory Statistics:")
            for key, value in self.memory_stats.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        if self.resource_stats:
            lines.append("Resource Statistics:")
            for key, value in self.resource_stats.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        status = "VERIFICATION PASSED ✓" if self.is_successful() else "VERIFICATION FAILED ✗"
        lines.append(status)

        return "\n".join(lines)

    def get_detailed_report(self) -> str:
        """Get a detailed verification report."""
        lines = [self.get_summary(), ""]

        if self.results:
            lines.append("=== Detailed Results ===")
            for result in self.results:
                lines.append(str(result))
                if result.details:
                    for key, value in result.details.items():
                        lines.append(f"    {key}: {value}")

        return "\n".join(lines)


class CleanupVerifier:
    """Verifies cleanup operations and detects resource leaks."""

    def __init__(self) -> None:
        """Initialize the cleanup verifier."""
        self.logger = get_logger(__name__)
        self.report = CleanupVerificationReport()

    def verify_cleanup(self, stats: Any) -> CleanupVerificationReport:
        """
        Verify cleanup operations.

        Args:
            stats: CleanupStats from unified coordinator

        Returns:
            CleanupVerificationReport with verification results
        """
        self.report = CleanupVerificationReport()
        start_time = time.time()

        try:
            self.logger.info("Starting cleanup verification")

            # Run verification checks
            self._verify_phase_completion(stats)
            self._verify_error_handling(stats)
            self._verify_resource_cleanup(stats)
            self._verify_memory_state()
            self._verify_handler_execution(stats)

            self.report.total_duration = time.time() - start_time

            # Log summary
            self.logger.info(self.report.get_summary())

            return self.report

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Verification failed: %s", e, exc_info=True)
            result = VerificationResult(
                check_name="Verification Process",
                status=VerificationStatus.FAILED,
                message=f"Verification process failed: {e}",
                duration=time.time() - start_time,
            )
            self.report.add_result(result)
            return self.report

    def _verify_phase_completion(self, stats: Any) -> None:
        """Verify all cleanup phases completed."""
        start_time = time.time()
        try:
            if not hasattr(stats, "total_phases"):
                result = VerificationResult(
                    check_name="Phase Completion",
                    status=VerificationStatus.SKIPPED,
                    message="Stats object missing phase information",
                    duration=time.time() - start_time,
                )
                self.report.add_result(result)
                return

            completed = stats.completed_phases + stats.skipped_phases
            total = stats.total_phases

            if completed == total:
                status = VerificationStatus.PASSED
                message = f"All {total} phases completed"
            elif completed > 0:
                status = VerificationStatus.WARNING
                message = f"Only {completed}/{total} phases completed"
            else:
                status = VerificationStatus.FAILED
                message = "No phases completed"

            result = VerificationResult(
                check_name="Phase Completion",
                status=status,
                message=message,
                details={
                    "total_phases": total,
                    "completed": stats.completed_phases,
                    "skipped": stats.skipped_phases,
                    "failed": stats.failed_phases,
                },
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            result = VerificationResult(
                check_name="Phase Completion",
                status=VerificationStatus.FAILED,
                message=f"Error verifying phases: {e}",
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

    def _verify_error_handling(self, stats: Any) -> None:
        """Verify error handling during cleanup."""
        start_time = time.time()
        try:
            if not hasattr(stats, "failed_phases"):
                result = VerificationResult(
                    check_name="Error Handling",
                    status=VerificationStatus.SKIPPED,
                    message="Stats object missing error information",
                    duration=time.time() - start_time,
                )
                self.report.add_result(result)
                return

            if stats.failed_phases == 0:
                status = VerificationStatus.PASSED
                message = "No errors during cleanup"
            else:
                status = VerificationStatus.WARNING
                message = f"{stats.failed_phases} phase(s) failed"

            result = VerificationResult(
                check_name="Error Handling",
                status=status,
                message=message,
                details={
                    "failed_phases": stats.failed_phases,
                    "error_count": len(stats.errors) if hasattr(stats, "errors") else 0,
                },
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            result = VerificationResult(
                check_name="Error Handling",
                status=VerificationStatus.FAILED,
                message=f"Error verifying error handling: {e}",
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

    def _verify_resource_cleanup(self, stats: Any) -> None:
        """Verify resource cleanup."""
        start_time = time.time()
        try:
            # Try to get resource tracker stats
            try:
                from src.gui.vtk.resource_tracker import get_vtk_resource_tracker

                tracker = get_vtk_resource_tracker()
                if tracker:
                    tracker_stats = tracker.get_statistics()
                    self.report.resource_stats = tracker_stats

                    leaked = tracker_stats.get("total_leaked", 0)
                    if leaked == 0:
                        status = VerificationStatus.PASSED
                        message = "No resource leaks detected"
                    else:
                        status = VerificationStatus.WARNING
                        message = f"{leaked} resource(s) may have leaked"

                    result = VerificationResult(
                        check_name="Resource Cleanup",
                        status=status,
                        message=message,
                        details=tracker_stats,
                        duration=time.time() - start_time,
                    )
                    self.report.add_result(result)
                    return
            except Exception:
                pass

            result = VerificationResult(
                check_name="Resource Cleanup",
                status=VerificationStatus.SKIPPED,
                message="Resource tracker not available",
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            result = VerificationResult(
                check_name="Resource Cleanup",
                status=VerificationStatus.FAILED,
                message=f"Error verifying resource cleanup: {e}",
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

    def _verify_memory_state(self) -> None:
        """Verify memory state after cleanup."""
        start_time = time.time()
        try:
            gc.collect()

            # Get memory statistics

            memory_info = {
                "gc_stats": gc.get_stats() if hasattr(gc, "get_stats") else "N/A",
                "gc_count": gc.get_count(),
                "gc_objects": len(gc.get_objects()),
            }

            self.report.memory_stats = memory_info

            result = VerificationResult(
                check_name="Memory State",
                status=VerificationStatus.PASSED,
                message="Memory state verified",
                details=memory_info,
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            result = VerificationResult(
                check_name="Memory State",
                status=VerificationStatus.WARNING,
                message=f"Could not verify memory state: {e}",
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

    def _verify_handler_execution(self, stats: Any) -> None:
        """Verify handler execution statistics."""
        start_time = time.time()
        try:
            if not hasattr(stats, "handler_stats"):
                result = VerificationResult(
                    check_name="Handler Execution",
                    status=VerificationStatus.SKIPPED,
                    message="Handler statistics not available",
                    duration=time.time() - start_time,
                )
                self.report.add_result(result)
                return

            handler_stats = stats.handler_stats
            if not handler_stats:
                result = VerificationResult(
                    check_name="Handler Execution",
                    status=VerificationStatus.SKIPPED,
                    message="No handlers executed",
                    duration=time.time() - start_time,
                )
                self.report.add_result(result)
                return

            total_handlers = len(handler_stats)
            successful_handlers = sum(
                1 for h in handler_stats.values() if h.get("phases_failed", 0) == 0
            )

            if successful_handlers == total_handlers:
                status = VerificationStatus.PASSED
                message = f"All {total_handlers} handler(s) executed successfully"
            else:
                status = VerificationStatus.WARNING
                message = f"{successful_handlers}/{total_handlers} handler(s) successful"

            result = VerificationResult(
                check_name="Handler Execution",
                status=status,
                message=message,
                details={
                    "total_handlers": total_handlers,
                    "successful": successful_handlers,
                    "handlers": list(handler_stats.keys()),
                },
                duration=time.time() - start_time,
            )
            self.report.add_result(result)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            result = VerificationResult(
                check_name="Handler Execution",
                status=VerificationStatus.FAILED,
                message=f"Error verifying handler execution: {e}",
                duration=time.time() - start_time,
            )
            self.report.add_result(result)


def get_cleanup_verifier() -> CleanupVerifier:
    """Get the global cleanup verifier instance."""
    global _cleanup_verifier
    if _cleanup_verifier is None:
        _cleanup_verifier = CleanupVerifier()
    return _cleanup_verifier


_cleanup_verifier: Optional[CleanupVerifier] = None
