"""
Hardware Acceleration Detection module for Digital Workshop.
Provides vendor-agnostic detection for NVIDIA CUDA, AMD/Intel OpenCL, and graceful CPU fallback.
"""

from __future__ import annotations

import logging
import os
import platform
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict

try:
    import vtk  # type: ignore
except Exception:
    vtk = None  # type: ignore

try:
    import pyopencl as cl  # type: ignore
except Exception:
    cl = None  # type: ignore

try:
    from numba import cuda as numba_cuda  # type: ignore
except Exception:
    numba_cuda = None  # type: ignore

from .logging_config import get_logger


class AccelBackend(Enum):
    CUDA = "cuda"
    OPENCL = "opencl"
    OPENGL_COMPUTE = "opengl_compute"
    CPU = "cpu"


@dataclass
class GPUDevice:
    name: str
    vendor: str
    device_id: int = 0
    memory_mb: Optional[int] = None
    driver_version: Optional[str] = None
    backend: AccelBackend = AccelBackend.CPU


@dataclass
class AccelCapabilities:
    available_backends: List[AccelBackend] = field(default_factory=list)
    devices: List[GPUDevice] = field(default_factory=list)
    recommended_backend: AccelBackend = AccelBackend.CPU
    performance_score: int = 10
    notes: List[str] = field(default_factory=list)


class HardwareAccelerationManager:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self._caps: Optional[AccelCapabilities] = None
        self._detected: bool = False

    def detect(self, force: bool = False) -> AccelCapabilities:
        if self._detected and self._caps and not force:
            return self._caps
        self._detected = True
        self.logger.info("Detecting hardware acceleration capabilities")
        caps = AccelCapabilities()
        # NVIDIA CUDA
        nvidia_caps = self._detect_nvidia_cuda()
        if nvidia_caps["available"]:
            caps.available_backends.append(AccelBackend.CUDA)
            caps.devices.extend(nvidia_caps["devices"])
            caps.notes.extend(nvidia_caps["notes"])
        # OpenCL (AMD/Intel/others)
        ocl_caps = self._detect_opencl()
        if ocl_caps["available"]:
            if AccelBackend.OPENCL not in caps.available_backends:
                caps.available_backends.append(AccelBackend.OPENCL)
            caps.devices.extend(ocl_caps["devices"])
            caps.notes.extend(ocl_caps["notes"])
        # OpenGL compute (best-effort)
        if self._detect_opengl_compute():
            caps.available_backends.append(AccelBackend.OPENGL_COMPUTE)
            caps.notes.append("OpenGL 4.3+ detected (compute shaders available)")
        # Scoring and recommendation
        caps.performance_score = self._score(caps)
        caps.recommended_backend = self._select_backend(caps)
        self._caps = caps
        self.logger.info(
            f"Hardware detection complete. Recommended backend: {caps.recommended_backend.value}"
        )
        return caps

    def get_capabilities(self) -> AccelCapabilities:
        return self.detect()

    def _detect_nvidia_cuda(self) -> Dict[str, object]:
        devices: List[GPUDevice] = []
        notes: List[str] = []
        available = False
        # nvidia-smi path check
        smi = shutil.which("nvidia-smi")
        if smi:
            try:
                # Query concise CSV to avoid locale issues
                cmd = [
                    smi,
                    "--query-gpu=name,memory.total,driver_version",
                    "--format=csv,noheader,nounits",
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                if res.returncode == 0:
                    for idx, line in enumerate(
                        [l.strip() for l in res.stdout.splitlines() if l.strip()]
                    ):
                        parts = [p.strip() for p in line.split(",")]
                        if len(parts) >= 3:
                            name, mem, drv = parts[0], parts[1], parts[2]
                            mem_mb = None
                            try:
                                mem_mb = int(mem)
                            except Exception:
                                mem_mb = None
                            devices.append(
                                GPUDevice(
                                    name=name,
                                    vendor="NVIDIA",
                                    device_id=idx,
                                    memory_mb=mem_mb,
                                    driver_version=drv,
                                    backend=AccelBackend.CUDA,
                                )
                            )
                    if devices:
                        available = True
                        notes.append("Detected NVIDIA GPUs via nvidia-smi")
                else:
                    notes.append(
                        f"nvidia-smi returned non-zero exit code {res.returncode}"
                    )
            except Exception as e:
                notes.append(f"nvidia-smi check failed: {e}")
        # Fallback to numba CUDA probe
        if not available and numba_cuda is not None:
            try:
                if numba_cuda.is_available():
                    available = True
                    notes.append("numba.cuda reports CUDA available")
                    try:
                        count = numba_cuda.gpus.lst.count  # type: ignore[attr-defined]
                    except Exception:
                        count = 1
                    for i in range(max(1, count)):
                        devices.append(
                            GPUDevice(
                                name="CUDA Device",
                                vendor="NVIDIA",
                                device_id=i,
                                backend=AccelBackend.CUDA,
                            )
                        )
            except Exception as e:
                notes.append(f"numba.cuda probe failed: {e}")
        return {"available": available, "devices": devices, "notes": notes}

    def _detect_opencl(self) -> Dict[str, object]:
        devices: List[GPUDevice] = []
        notes: List[str] = []
        available = False
        if cl is None:
            notes.append("pyopencl not installed; skipping OpenCL detection")
            return {"available": False, "devices": devices, "notes": notes}
        try:
            platforms = cl.get_platforms()
            for p in platforms:
                try:
                    p_name = p.name
                    devs = p.get_devices()
                    for idx, d in enumerate(devs):
                        try:
                            vendor = getattr(d, "vendor", "")
                            name = getattr(d, "name", "OpenCL Device")
                            mem = getattr(d, "global_mem_size", 0)
                            mem_mb = int(mem // (1024 * 1024)) if mem else None
                            devices.append(
                                GPUDevice(
                                    name=name,
                                    vendor=vendor or p_name,
                                    device_id=idx,
                                    memory_mb=mem_mb,
                                    driver_version=getattr(d, "driver_version", None),
                                    backend=AccelBackend.OPENCL,
                                )
                            )
                            available = True
                        except Exception as e:
                            notes.append(f"OpenCL device parse error: {e}")
                except Exception as e:
                    notes.append(f"OpenCL platform error: {e}")
            if available:
                notes.append("OpenCL platforms/devices detected")
        except Exception as e:
            notes.append(f"OpenCL detection failed: {e}")
        return {"available": available, "devices": devices, "notes": notes}

    def _detect_opengl_compute(self) -> bool:
        # Non-fatal best-effort detection; requires VTK OpenGL context
        try:
            if vtk is None:
                return False
            # Creating a render window can be heavy; avoid if headless
            if not hasattr(vtk, "vtkOpenGLRenderWindow"):
                return False
            # Heuristic: if OpenGL version string indicates 4.3+, assume compute shaders
            try:
                rw = vtk.vtkRenderWindow()
                # On some systems this may not initialize a context until shown; guard.
                version = (
                    rw.GetOpenGLVersion() if hasattr(rw, "GetOpenGLVersion") else ""
                )
                if not version and hasattr(rw, "ReportCapabilities"):
                    # Fallback: parse ReportCapabilities
                    cap = rw.ReportCapabilities()  # type: ignore
                    m = re.search(
                        r"OpenGL version string:\s*([0-9]+\.[0-9]+)", cap or ""
                    )
                    version = m.group(1) if m else ""
            except Exception:
                version = ""
            try:
                if version:
                    major_minor = version.split(".")
                    maj = int(major_minor[0])
                    minr = int(major_minor[1])
                    return (maj > 4) or (maj == 4 and minr >= 3)
            except Exception:
                return False
        except Exception:
            return False
        return False

    def _score(self, caps: AccelCapabilities) -> int:
        score = 10
        has_cuda = any(d.backend == AccelBackend.CUDA for d in caps.devices)
        has_ocl_amd = any(
            d.backend == AccelBackend.OPENCL and "AMD" in (d.vendor or "").upper()
            for d in caps.devices
        )
        has_ocl_intel = any(
            d.backend == AccelBackend.OPENCL and "INTEL" in (d.vendor or "").upper()
            for d in caps.devices
        )
        if has_cuda:
            score = 85
            # scale with memory if known
            mems = [
                d.memory_mb
                for d in caps.devices
                if d.backend == AccelBackend.CUDA and d.memory_mb
            ]
            if mems:
                score = min(100, score + min(10, sum(mems) // (8 * 1024)))
        elif has_ocl_amd:
            score = 65
        elif has_ocl_intel:
            score = 45
        elif AccelBackend.OPENGL_COMPUTE in caps.available_backends:
            score = 35
        return score

    def _select_backend(self, caps: AccelCapabilities) -> AccelBackend:
        if any(d.backend == AccelBackend.CUDA for d in caps.devices):
            return AccelBackend.CUDA
        if any(d.backend == AccelBackend.OPENCL for d in caps.devices):
            return AccelBackend.OPENCL
        if AccelBackend.OPENGL_COMPUTE in caps.available_backends:
            return AccelBackend.OPENGL_COMPUTE
        return AccelBackend.CPU

    def get_acceleration_info(self) -> Dict[str, object]:
        caps = self.get_capabilities()
        info: Dict[str, object] = {
            "recommended_backend": caps.recommended_backend.value,
            "performance_score": caps.performance_score,
            "available_backends": [b.value for b in caps.available_backends],
            "devices": [
                f"{d.vendor} {d.name} ({d.memory_mb or '?'} MB)" for d in caps.devices
            ],
            "notes": caps.notes,
        }
        return info

    def warn_if_no_acceleration(self) -> None:
        caps = self.get_capabilities()
        if caps.recommended_backend == AccelBackend.CPU:
            self.logger.warning("No GPU acceleration detected; using CPU path")
        else:
            self.logger.info(
                f"GPU acceleration enabled: {caps.recommended_backend.value}"
            )


# Singleton helpers
_accel_manager: Optional[HardwareAccelerationManager] = None  # type: ignore


def get_acceleration_manager() -> HardwareAccelerationManager:
    global _accel_manager
    if _accel_manager is None:
        _accel_manager = HardwareAccelerationManager()
    return _accel_manager


def check_acceleration_support() -> (bool, str):
    mgr = get_acceleration_manager()
    caps = mgr.get_capabilities()
    return (
        caps.recommended_backend != AccelBackend.CPU,
        caps.recommended_backend.value,
    )


def warn_if_no_acceleration() -> None:
    get_acceleration_manager().warn_if_no_acceleration()
