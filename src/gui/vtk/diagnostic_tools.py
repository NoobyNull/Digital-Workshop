"""
VTK Diagnostic Tools - Tools for diagnosing VTK issues.

This module provides diagnostic tools for troubleshooting VTK rendering issues,
context problems, and performance bottlenecks.
"""

import platform
from typing import Dict, List, Any, Optional
from datetime import datetime

import vtk

from src.core.logging_config import get_logger
from .error_handler import get_vtk_error_handler
from .context_manager import get_vtk_context_manager
from .resource_tracker import get_vtk_resource_tracker
from .fallback_renderer import get_vtk_fallback_renderer


logger = get_logger(__name__)


class VTKDiagnosticTools:
    """
    Diagnostic tools for VTK issues and performance analysis.

    Provides comprehensive diagnostics for VTK rendering context, resources,
    performance, and error conditions.
    """

    def __init__(self) -> None:
        """Initialize diagnostic tools."""
        self.logger = get_logger(__name__)
        self.error_handler = get_vtk_error_handler()
        self.context_manager = get_vtk_context_manager()
        self.resource_tracker = get_vtk_resource_tracker()
        self.fallback_renderer = get_vtk_fallback_renderer()

        self.logger.info("VTK Diagnostic Tools initialized")

    def get_comprehensive_diagnostics(self) -> Dict[str, Any]:
        """
        Get comprehensive VTK diagnostics.

        Returns:
            Complete diagnostic information
        """
        try:
            diagnostics = {
                "timestamp": datetime.now().isoformat(),
                "platform": self._get_platform_info(),
                "vtk_version": self._get_vtk_version_info(),
                "context_diagnostics": self._get_context_diagnostics(),
                "resource_diagnostics": self._get_resource_diagnostics(),
                "error_diagnostics": self._get_error_diagnostics(),
                "fallback_diagnostics": self._get_fallback_diagnostics(),
                "performance_diagnostics": self._get_performance_diagnostics(),
                "opengl_diagnostics": self._get_opengl_diagnostics(),
            }

            return diagnostics

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error getting comprehensive diagnostics: %s", e)
            return {"error": str(e)}

    def _get_platform_info(self) -> Dict[str, Any]:
        """Get platform information."""
        try:
            return {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "python_implementation": platform.python_implementation(),
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_vtk_version_info(self) -> Dict[str, Any]:
        """Get VTK version information."""
        try:
            return {
                "vtk_version": vtk.vtkVersion.GetVTKVersion(),
                "vtk_major": vtk.vtkVersion.GetVTKMajorVersion(),
                "vtk_minor": vtk.vtkVersion.GetVTKMinorVersion(),
                "vtk_build": vtk.vtkVersion.GetVTKBuildVersion(),
                "vtk_source": vtk.vtkVersion.GetVTKSourceVersion(),
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_context_diagnostics(self) -> Dict[str, Any]:
        """Get context-related diagnostics."""
        try:
            return self.context_manager.get_diagnostic_info()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_resource_diagnostics(self) -> Dict[str, Any]:
        """Get resource tracking diagnostics."""
        try:
            return self.resource_tracker.get_statistics()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_error_diagnostics(self) -> Dict[str, Any]:
        """Get error handling diagnostics."""
        try:
            return self.error_handler.get_error_stats()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_fallback_diagnostics(self) -> Dict[str, Any]:
        """Get fallback renderer diagnostics."""
        try:
            return self.fallback_renderer.get_fallback_info()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_performance_diagnostics(self) -> Dict[str, Any]:
        """Get performance-related diagnostics."""
        try:
            # This would integrate with the performance tracker
            # For now, return basic information
            return {
                "performance_monitoring": "available",
                "frame_rate_monitoring": "available",
                "memory_monitoring": "available",
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_opengl_diagnostics(self) -> Dict[str, Any]:
        """Get OpenGL-specific diagnostics."""
        try:
            diagnostics = {
                "opengl_available": self._check_opengl_availability(),
                "opengl_version": self._get_opengl_version(),
                "opengl_extensions": self._get_opengl_extensions(),
                "rendering_backend": self._get_rendering_backend(),
            }

            # Platform-specific diagnostics
            system = platform.system()
            if system == "Windows":
                diagnostics.update(self._get_windows_opengl_diagnostics())
            elif system == "Linux":
                diagnostics.update(self._get_linux_opengl_diagnostics())
            elif system == "Darwin":
                diagnostics.update(self._get_darwin_opengl_diagnostics())

            return diagnostics

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _check_opengl_availability(self) -> bool:
        """Check if OpenGL is available."""
        try:
            # Try to create a simple OpenGL context
            render_window = vtk.vtkRenderWindow()
            render_window.SetOffScreenRendering(1)
            render_window.SetSize(1, 1)

            # If we can create and render without errors, OpenGL is available
            render_window.Render()
            render_window.Finalize()

            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("OpenGL availability check failed: %s", e)
            return False

    def _get_opengl_version(self) -> Optional[str]:
        """Get OpenGL version string."""
        try:
            # This is a simplified approach - in practice, you'd need to
            # query the actual OpenGL context for version information
            return "OpenGL version detection not implemented"
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return f"Error: {e}"

    def _get_opengl_extensions(self) -> List[str]:
        """Get available OpenGL extensions."""
        try:
            # This would require querying the actual OpenGL context
            return ["Extension detection not implemented"]
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return [f"Error: {e}"]

    def _get_rendering_backend(self) -> str:
        """Get the current rendering backend."""
        try:
            system = platform.system()

            if system == "Windows":
                # Check for ANGLE or native OpenGL
                try:
                    # This is a heuristic - in practice you'd check VTK settings
                    return "Windows OpenGL (likely ANGLE)"
                except Exception:
                    return "Windows OpenGL (native)"

            elif system == "Linux":
                return "Linux OpenGL (Mesa or proprietary)"

            elif system == "Darwin":
                return "macOS OpenGL/Metal"

            else:
                return "Unknown rendering backend"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return f"Error detecting backend: {e}"

    def _get_windows_opengl_diagnostics(self) -> Dict[str, Any]:
        """Get Windows-specific OpenGL diagnostics."""
        try:
            return {
                "angle_available": self._check_angle_availability(),
                "directx_version": self._get_directx_version(),
                "wgl_extensions": self._get_wgl_extensions(),
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_linux_opengl_diagnostics(self) -> Dict[str, Any]:
        """Get Linux-specific OpenGL diagnostics."""
        try:
            return {
                "mesa_available": self._check_mesa_availability(),
                "glx_extensions": self._get_glx_extensions(),
                "dri_available": self._check_dri_availability(),
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _get_darwin_opengl_diagnostics(self) -> Dict[str, Any]:
        """Get macOS-specific OpenGL diagnostics."""
        try:
            return {
                "cgl_available": self._check_cgl_availability(),
                "metal_compatibility": self._check_metal_compatibility(),
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return {"error": str(e)}

    def _check_angle_availability(self) -> bool:
        """Check if ANGLE is available on Windows."""
        try:
            # This would check for ANGLE installation
            return True  # Placeholder
        except Exception:
            return False

    def _get_directx_version(self) -> str:
        """Get DirectX version on Windows."""
        try:
            # This would query DirectX version
            return "DirectX version detection not implemented"
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return f"Error: {e}"

    def _get_wgl_extensions(self) -> List[str]:
        """Get WGL extensions on Windows."""
        try:
            # This would query WGL extensions
            return ["WGL extension detection not implemented"]
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return [f"Error: {e}"]

    def _check_mesa_availability(self) -> bool:
        """Check if Mesa is available on Linux."""
        try:
            # This would check for Mesa installation
            return True  # Placeholder
        except Exception:
            return False

    def _get_glx_extensions(self) -> List[str]:
        """Get GLX extensions on Linux."""
        try:
            # This would query GLX extensions
            return ["GLX extension detection not implemented"]
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return [f"Error: {e}"]

    def _check_dri_availability(self) -> bool:
        """Check if DRI is available on Linux."""
        try:
            # This would check for DRI
            return True  # Placeholder
        except Exception:
            return False

    def _check_cgl_availability(self) -> bool:
        """Check if CGL is available on macOS."""
        try:
            # This would check for CGL
            return True  # Placeholder
        except Exception:
            return False

    def _check_metal_compatibility(self) -> bool:
        """Check Metal compatibility on macOS."""
        try:
            # This would check for Metal compatibility
            return True  # Placeholder
        except Exception:
            return False

    def diagnose_context_loss(self, render_window: vtk.vtkRenderWindow) -> Dict[str, Any]:
        """
        Diagnose potential context loss issues.

        Args:
            render_window: The render window to diagnose

        Returns:
            Context loss diagnostic information
        """
        try:
            diagnosis = {
                "context_loss_detected": False,
                "context_state": "unknown",
                "potential_causes": [],
                "recommendations": [],
            }

            # Check context state
            is_valid, context_state = self.context_manager.validate_context(
                render_window, "diagnosis"
            )
            diagnosis["context_state"] = context_state.value

            if not is_valid:
                diagnosis["context_loss_detected"] = True

                # Analyze potential causes
                if context_state.name == "LOST":
                    diagnosis["potential_causes"].extend(
                        [
                            "OpenGL context was destroyed by the system",
                            "Application lost focus for extended period",
                            "Graphics driver reset occurred",
                            "System entered sleep/hibernation mode",
                        ]
                    )

                elif context_state.name == "INVALID":
                    diagnosis["potential_causes"].extend(
                        [
                            "Render window handle is invalid",
                            "Window was destroyed or unmapped",
                            "Graphics context was not properly initialized",
                        ]
                    )

                # Provide recommendations
                diagnosis["recommendations"].extend(
                    [
                        "Consider using fallback rendering mode",
                        "Check if application window is properly mapped",
                        "Verify graphics driver stability",
                        "Monitor system resource usage",
                    ]
                )

            # Get additional context information
            diagnosis["context_info"] = self.context_manager.get_context_info(render_window)

            return diagnosis

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error diagnosing context loss: %s", e)
            return {"error": str(e)}

    def diagnose_memory_issues(self) -> Dict[str, Any]:
        """Diagnose potential memory issues."""
        try:
            diagnosis = {
                "memory_issues_detected": False,
                "resource_leaks": [],
                "memory_usage": {},
                "recommendations": [],
            }

            # Check for leaked resources
            leaked_resources = self.resource_tracker.find_leaked_resources()
            if leaked_resources:
                diagnosis["memory_issues_detected"] = True
                diagnosis["resource_leaks"] = leaked_resources

                diagnosis["recommendations"].append(
                    "Found leaked VTK resources - ensure proper cleanup"
                )

            # Get resource statistics
            stats = self.resource_tracker.get_statistics()
            diagnosis["memory_usage"] = stats

            # Analyze resource counts
            if stats.get("total_tracked", 0) > 100:
                diagnosis["memory_issues_detected"] = True
                diagnosis["recommendations"].append(
                    "High number of tracked resources - check for cleanup issues"
                )

            return diagnosis

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error diagnosing memory issues: %s", e)
            return {"error": str(e)}

    def diagnose_performance_issues(self) -> Dict[str, Any]:
        """Diagnose potential performance issues."""
        try:
            diagnosis = {
                "performance_issues_detected": False,
                "high_resource_count": False,
                "context_switching": False,
                "rendering_inefficiency": False,
                "recommendations": [],
            }

            # Check resource counts
            stats = self.resource_tracker.get_statistics()
            total_resources = stats.get("total_tracked", 0)

            if total_resources > 50:
                diagnosis["high_resource_count"] = True
                diagnosis["performance_issues_detected"] = True
                diagnosis["recommendations"].append("High resource count may impact performance")

            # Check error rates
            error_stats = self.error_handler.get_error_stats()
            total_errors = error_stats.get("total_errors", 0)

            if total_errors > 10:
                diagnosis["performance_issues_detected"] = True
                diagnosis["recommendations"].append(
                    "High error rate may indicate performance issues"
                )

            # Check context switching
            context_info = self.context_manager.get_diagnostic_info()
            if context_info.get("cache_size", 0) > 20:
                diagnosis["context_switching"] = True
                diagnosis["performance_issues_detected"] = True
                diagnosis["recommendations"].append(
                    "Frequent context validation may impact performance"
                )

            return diagnosis

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error diagnosing performance issues: %s", e)
            return {"error": str(e)}

    def generate_diagnostic_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate a comprehensive diagnostic report.

        Args:
            output_file: Optional file path to save the report

        Returns:
            Report content as string
        """
        try:
            self.logger.info("Generating VTK diagnostic report")

            # Get comprehensive diagnostics
            diagnostics = self.get_comprehensive_diagnostics()

            # Add specific issue diagnoses
            diagnostics["context_loss_diagnosis"] = self.diagnose_context_loss(None)
            diagnostics["memory_diagnosis"] = self.diagnose_memory_issues()
            diagnostics["performance_diagnosis"] = self.diagnose_performance_issues()

            # Generate report
            report = self._format_diagnostic_report(diagnostics)

            # Save to file if requested
            if output_file:
                try:
                    with open(output_file, "w") as f:
                        f.write(report)
                    self.logger.info("Diagnostic report saved to: %s", output_file)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.error("Error saving diagnostic report: %s", e)

            return report

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_report = f"Error generating diagnostic report: {e}"
            self.logger.error(error_report)
            return error_report

    def _format_diagnostic_report(self, diagnostics: Dict[str, Any]) -> str:
        """Format diagnostics into a readable report."""
        try:
            report_lines = [
                "=" * 60,
                "VTK DIAGNOSTIC REPORT",
                "=" * 60,
                f"Generated: {diagnostics.get('timestamp', 'Unknown')}",
                "",
                "PLATFORM INFORMATION:",
                "-" * 30,
            ]

            # Platform info
            platform_info = diagnostics.get("platform", {})
            for key, value in platform_info.items():
                if key != "error":
                    report_lines.append(f"  {key}: {value}")

            if "error" in platform_info:
                report_lines.append(f"  Error: {platform_info['error']}")

            # VTK version
            report_lines.extend(["", "VTK VERSION:", "-" * 15])
            vtk_info = diagnostics.get("vtk_version", {})
            for key, value in vtk_info.items():
                if key != "error":
                    report_lines.append(f"  {key}: {value}")

            # Context diagnostics
            report_lines.extend(["", "CONTEXT DIAGNOSTICS:", "-" * 25])
            context_info = diagnostics.get("context_diagnostics", {})
            for key, value in context_info.items():
                if key != "error":
                    if isinstance(value, dict):
                        report_lines.append(f"  {key}:")
                        for sub_key, sub_value in value.items():
                            report_lines.append(f"    {sub_key}: {sub_value}")
                    else:
                        report_lines.append(f"  {key}: {value}")

            # Resource diagnostics
            report_lines.extend(["", "RESOURCE DIAGNOSTICS:", "-" * 25])
            resource_info = diagnostics.get("resource_diagnostics", {})
            for key, value in resource_info.items():
                if key != "error":
                    report_lines.append(f"  {key}: {value}")

            # Error diagnostics
            report_lines.extend(["", "ERROR DIAGNOSTICS:", "-" * 22])
            error_info = diagnostics.get("error_diagnostics", {})
            for key, value in error_info.items():
                if key != "error":
                    report_lines.append(f"  {key}: {value}")

            # OpenGL diagnostics
            report_lines.extend(["", "OPENGL DIAGNOSTICS:", "-" * 23])
            opengl_info = diagnostics.get("opengl_diagnostics", {})
            for key, value in opengl_info.items():
                if key != "error":
                    if isinstance(value, list):
                        report_lines.append(f"  {key}:")
                        for item in value:
                            report_lines.append(f"    - {item}")
                    else:
                        report_lines.append(f"  {key}: {value}")

            # Issue-specific diagnoses
            report_lines.extend(["", "ISSUE DIAGNOSIS:", "-" * 20])

            context_loss = diagnostics.get("context_loss_diagnosis", {})
            if context_loss.get("context_loss_detected"):
                report_lines.extend(
                    [
                        "  CONTEXT LOSS DETECTED!",
                        f"  State: {context_loss.get('context_state', 'unknown')}",
                        "  Potential causes:",
                    ]
                )
                for cause in context_loss.get("potential_causes", []):
                    report_lines.append(f"    - {cause}")
                report_lines.extend(["  Recommendations:"])
                for rec in context_loss.get("recommendations", []):
                    report_lines.append(f"    - {rec}")

            memory_issues = diagnostics.get("memory_diagnosis", {})
            if memory_issues.get("memory_issues_detected"):
                report_lines.extend(["", "  MEMORY ISSUES DETECTED!"])
                if memory_issues.get("resource_leaks"):
                    report_lines.append(
                        f"  Leaked resources: {len(memory_issues['resource_leaks'])}"
                    )
                report_lines.extend(["  Recommendations:"])
                for rec in memory_issues.get("recommendations", []):
                    report_lines.append(f"    - {rec}")

            performance_issues = diagnostics.get("performance_diagnosis", {})
            if performance_issues.get("performance_issues_detected"):
                report_lines.extend(["", "  PERFORMANCE ISSUES DETECTED!"])
                report_lines.extend(["  Recommendations:"])
                for rec in performance_issues.get("recommendations", []):
                    report_lines.append(f"    - {rec}")

            # Summary
            report_lines.extend(["", "=" * 60, "END OF REPORT", "=" * 60])

            return "\n".join(report_lines)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return f"Error formatting diagnostic report: {e}"

    def run_health_check(self) -> Dict[str, Any]:
        """
        Run a comprehensive health check of the VTK system.

        Returns:
            Health check results
        """
        try:
            self.logger.info("Running VTK health check")

            health = {
                "overall_status": "healthy",
                "issues": [],
                "warnings": [],
                "recommendations": [],
            }

            # Check context health
            context_info = self.context_manager.get_diagnostic_info()
            if not context_info.get("validation_enabled", False):
                health["warnings"].append("Context validation is disabled")

            # Check resource health
            resource_stats = self.resource_tracker.get_statistics()
            leaked_count = resource_stats.get("total_leaked", 0)
            if leaked_count > 0:
                health["issues"].append(f"Found {leaked_count} leaked resources")
                health["overall_status"] = "unhealthy"

            # Check error health
            error_stats = self.error_handler.get_error_stats()
            total_errors = error_stats.get("total_errors", 0)
            if total_errors > 5:
                health["warnings"].append(f"High error count: {total_errors}")

            # Check fallback health
            fallback_info = self.fallback_renderer.get_fallback_info()
            if fallback_info.get("fallback_active", False):
                health["warnings"].append("Fallback rendering is active")

            # Generate recommendations
            if health["issues"]:
                health["recommendations"].append("Address the identified issues")
            if health["warnings"]:
                health["recommendations"].append("Review the warnings")

            if not health["issues"] and not health["warnings"]:
                health["recommendations"].append("VTK system is healthy")

            return health

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error running health check: %s", e)
            return {
                "overall_status": "error",
                "issues": [str(e)],
                "warnings": [],
                "recommendations": ["Check diagnostic logs"],
            }


# Global diagnostic tools instance
_vtk_diagnostic_tools: Optional[VTKDiagnosticTools] = None


def get_vtk_diagnostic_tools() -> VTKDiagnosticTools:
    """Get the global VTK diagnostic tools instance."""
    global _vtk_diagnostic_tools
    if _vtk_diagnostic_tools is None:
        _vtk_diagnostic_tools = VTKDiagnosticTools()
    return _vtk_diagnostic_tools


def generate_vtk_diagnostic_report(output_file: Optional[str] = None) -> str:
    """
    Convenience function to generate a VTK diagnostic report.

    Args:
        output_file: Optional file path to save the report

    Returns:
        Report content as string
    """
    return get_vtk_diagnostic_tools().generate_diagnostic_report(output_file)


def run_vtk_health_check() -> Dict[str, Any]:
    """
    Convenience function to run a VTK health check.

    Returns:
        Health check results
    """
    return get_vtk_diagnostic_tools().run_health_check()
