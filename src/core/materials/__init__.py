"""Materials helpers and catalogs."""

from .wood_catalog import (
    WoodMaterial,
    WOOD_MATERIALS,
    find_wood,
    estimate_surface_speed_sfm,
    estimate_chipload_inches,
    hardness_band,
)

__all__ = [
    "WoodMaterial",
    "WOOD_MATERIALS",
    "find_wood",
    "estimate_surface_speed_sfm",
    "estimate_chipload_inches",
    "hardness_band",
]
