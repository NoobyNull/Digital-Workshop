"""
Shared helpers for parsing basic MTL material files.
"""

from typing import Dict, Tuple


def read_basic_mtl(mtl_path: str) -> Dict[str, Tuple[float, float, float] | float]:
    """Read a minimal subset of an MTL file into a dict."""
    material: Dict[str, Tuple[float, float, float] | float] = {
        "Kd": (0.8, 0.8, 0.8),
        "Ks": (0.0, 0.0, 0.0),
        "Ns": 10.0,
        "d": 1.0,
    }

    with open(mtl_path, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("Kd "):
                parts = line.split()
                if len(parts) >= 4:
                    material["Kd"] = tuple(map(float, parts[1:4]))
            elif line.startswith("Ks "):
                parts = line.split()
                if len(parts) >= 4:
                    material["Ks"] = tuple(map(float, parts[1:4]))
            elif line.startswith("Ns "):
                parts = line.split()
                if len(parts) >= 2:
                    material["Ns"] = float(parts[1])
            elif line.startswith("d "):
                parts = line.split()
                if len(parts) >= 2:
                    material["d"] = float(parts[1])

    return material
