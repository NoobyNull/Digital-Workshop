"""Static wood catalog with Janka hardness and specific gravity (oven-dry)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class WoodMaterial:
    """Represents a wood species with hardness and density info."""

    name: str
    janka_lbf: int
    specific_gravity: float
    aliases: tuple[str, ...] = ()


# The list focuses on Bell Forest's domestic and exotic catalog.
# Values are rounded to commonly published Janka hardness and SG (oven-dry).
WOOD_MATERIALS: tuple[WoodMaterial, ...] = (
    # Domestic
    WoodMaterial("Balsa", 90, 0.12, aliases=("Ochroma",)),
    WoodMaterial("Basswood", 410, 0.37, aliases=("American Basswood",)),
    WoodMaterial("Aspen", 350, 0.38, aliases=("Quaking Aspen",)),
    WoodMaterial("Alder (Red)", 590, 0.41, aliases=("Red Alder",)),
    WoodMaterial("Poplar (Yellow)", 540, 0.42, aliases=("Tulip Poplar", "Tuliptree")),
    WoodMaterial("Pine (Eastern White)", 380, 0.35, aliases=("White Pine",)),
    WoodMaterial("Pine (Sugar)", 380, 0.36, aliases=("Sugar Pine",)),
    WoodMaterial("Pine (Radiata)", 710, 0.42, aliases=("Monterey Pine",)),
    WoodMaterial("Pine (Southern Yellow)", 870, 0.55, aliases=("Longleaf Pine",)),
    WoodMaterial("Cedar (Western Red)", 350, 0.32, aliases=("Western Redcedar",)),
    WoodMaterial("Cedar (Eastern Red)", 900, 0.47, aliases=("Aromatic Cedar",)),
    WoodMaterial("Cypress (Bald)", 510, 0.42, aliases=("Bald Cypress",)),
    WoodMaterial("Douglas Fir", 660, 0.50, aliases=("Doug Fir",)),
    WoodMaterial("Spruce (Sitka)", 510, 0.40, aliases=("Sitka Spruce",)),
    WoodMaterial("Larch (Tamarack)", 830, 0.55, aliases=("Tamarack", "Hackmatack")),
    WoodMaterial("Hemlock (Western)", 540, 0.45, aliases=("Western Hemlock",)),
    WoodMaterial("Ash (White)", 1320, 0.60, aliases=("White Ash",)),
    WoodMaterial("Ash (Black)", 850, 0.49, aliases=("Black Ash",)),
    WoodMaterial("Birch (Yellow)", 1260, 0.62, aliases=("Yellow Birch",)),
    WoodMaterial("Birch (Paper)", 910, 0.55, aliases=("White Birch", "Paper Birch")),
    WoodMaterial("Beech (American)", 1300, 0.64, aliases=("American Beech",)),
    WoodMaterial("Sycamore (American)", 770, 0.49, aliases=("American Sycamore",)),
    WoodMaterial("Elm (American)", 830, 0.55, aliases=("Red Elm",)),
    WoodMaterial("Elm (Siberian)", 1320, 0.65, aliases=("Siberian Elm",)),
    WoodMaterial("Maple (Soft)", 950, 0.54, aliases=("Silver Maple", "Red Maple")),
    WoodMaterial("Maple (Hard)", 1450, 0.63, aliases=("Sugar Maple", "Rock Maple")),
    WoodMaterial(
        "Cherry (Black)", 950, 0.50, aliases=("American Cherry", "Black Cherry")
    ),
    WoodMaterial("Oak (Red)", 1290, 0.63, aliases=("Northern Red Oak",)),
    WoodMaterial("Oak (White)", 1360, 0.68, aliases=("White Oak",)),
    WoodMaterial("Hickory (Shagbark)", 1820, 0.72, aliases=("Shagbark Hickory",)),
    WoodMaterial(
        "Walnut (Black)", 1010, 0.55, aliases=("American Walnut", "Black Walnut")
    ),
    WoodMaterial("Walnut (Claro)", 1130, 0.57, aliases=("Claro Walnut",)),
    WoodMaterial("Osage Orange", 2620, 0.76, aliases=("Hedge", "Bois d'Arc")),
    WoodMaterial("Locust (Black)", 1700, 0.69, aliases=("Black Locust",)),
    WoodMaterial("Mesquite", 2345, 0.77, aliases=("Honey Mesquite",)),
    # Exotic (Bell Forest core catalog)
    WoodMaterial("Afrormosia", 1560, 0.66, aliases=("African Teak",)),
    WoodMaterial(
        "African Mahogany (Khaya)", 1100, 0.55, aliases=("Khaya", "Khaya Mahogany")
    ),
    WoodMaterial("Anegre", 990, 0.45, aliases=("Aningeria",)),
    WoodMaterial("Anigre (Quartered)", 990, 0.45, aliases=("Quartered Anegre",)),
    WoodMaterial("Bocote", 2010, 0.73, aliases=("Mexican Bocote",)),
    WoodMaterial("Bloodwood", 2900, 0.93, aliases=("Satine",)),
    WoodMaterial("Bubinga", 2410, 0.89, aliases=("Kevazingo",)),
    WoodMaterial("Canarywood", 1520, 0.68, aliases=("Goncalo Almeida",)),
    WoodMaterial("Chechen", 2250, 0.91, aliases=("Caribbean Rosewood",)),
    WoodMaterial("Cocobolo", 2960, 1.01, aliases=("Cocobola",)),
    WoodMaterial("Cumaru", 3540, 1.05, aliases=("Brazilian Teak", "Tonka Bean")),
    WoodMaterial("Ebony (African)", 3080, 1.03, aliases=("Gabon Ebony", "Gabon")),
    WoodMaterial("Goncalo Alves", 2170, 0.91, aliases=("Tigerwood", "Jobillo")),
    WoodMaterial("Ipe", 3680, 1.08, aliases=("Brazilian Walnut", "Lapacho")),
    WoodMaterial("Jatoba", 2690, 0.91, aliases=("Brazilian Cherry",)),
    WoodMaterial("Kingwood", 2710, 1.01, aliases=("Violetwood",)),
    WoodMaterial(
        "Lacewood (Australian)", 840, 0.53, aliases=("Silky Oak", "Australian Lacewood")
    ),
    WoodMaterial("Leopardwood", 2150, 0.91, aliases=("Roupala",)),
    WoodMaterial("Makore", 1100, 0.66, aliases=("African Cherry",)),
    WoodMaterial("Marblewood", 2530, 1.05, aliases=("Angelim Rajado",)),
    WoodMaterial("Monkeypod", 850, 0.53, aliases=("Suar", "Rain Tree")),
    WoodMaterial("Morado", 1960, 0.85, aliases=("Bolivian Rosewood", "Pau Ferro")),
    WoodMaterial("Padauk", 1970, 0.72, aliases=("African Padauk",)),
    WoodMaterial("Pau Ferro", 1960, 0.85, aliases=("Bolivian Rosewood", "Morado")),
    WoodMaterial("Peruvian Walnut", 1080, 0.59, aliases=("Tropical Walnut",)),
    WoodMaterial("Purpleheart", 2520, 0.86, aliases=("Amaranth", "Peltogyne")),
    WoodMaterial(
        "Rosewood (East Indian)", 2440, 0.83, aliases=("EIR", "Dalbergia latifolia")
    ),
    WoodMaterial("Rosewood (Honduran)", 2200, 0.90, aliases=("Yucatan Rosewood",)),
    WoodMaterial("Santos Mahogany", 2200, 0.86, aliases=("Cabreuva",)),
    WoodMaterial("Sapele", 1410, 0.64, aliases=("Sapelli",)),
    WoodMaterial("Shedua", 1560, 0.71, aliases=("Ovangkol",)),
    WoodMaterial("Snakewood", 3800, 1.20, aliases=("Letterwood", "Amourette")),
    WoodMaterial("Spanish Cedar", 600, 0.40, aliases=("Cedro",)),
    WoodMaterial("Spanish Oak (Sherry)", 1200, 0.68, aliases=("Quercus faginea",)),
    WoodMaterial("Teak", 1155, 0.66, aliases=("Genuine Teak", "Tectona grandis")),
    WoodMaterial("Tulipwood", 2520, 1.04, aliases=("Brazilian Tulipwood",)),
    WoodMaterial("Wenge", 1930, 0.88, aliases=("Millettia laurentii",)),
    WoodMaterial("Yellowheart", 1790, 0.74, aliases=("Pau Amarello",)),
    WoodMaterial("Zebrawood", 1575, 0.74, aliases=("Zebrano",)),
    WoodMaterial("Ziricote", 1970, 0.83, aliases=("Cordia dodecandra",)),
)


def _canonical(name: str) -> str:
    return name.strip().lower()


def find_wood(name_or_alias: str) -> Optional[WoodMaterial]:
    """Find a wood by name or alias (case-insensitive)."""
    needle = _canonical(name_or_alias)
    for mat in WOOD_MATERIALS:
        if _canonical(mat.name) == needle or needle in (
            _canonical(a) for a in mat.aliases
        ):
            return mat
    return None


def hardness_band(janka_lbf: int) -> str:
    """Map Janka hardness to a qualitative band."""
    if janka_lbf < 600:
        return "soft"
    if janka_lbf < 1200:
        return "medium"
    if janka_lbf < 2000:
        return "hard"
    return "very hard"


def estimate_surface_speed_sfm(janka_lbf: int) -> float:
    """Heuristic spindle surface speed (SFM) target based on hardness band."""
    band = hardness_band(janka_lbf)
    if band == "soft":
        return 700.0
    if band == "medium":
        return 550.0
    if band == "hard":
        return 450.0
    return 350.0


def estimate_chipload_inches(janka_lbf: int, diameter_in: float, flutes: int) -> float:
    """Rough starting chipload (inches/tooth) scaled by hardness and tool size."""
    flutes = max(flutes, 1)
    base = min(max(diameter_in * 0.0015, 0.0006), 0.010)
    band = hardness_band(janka_lbf)
    hardness_scale = {
        "soft": 1.2,
        "medium": 1.0,
        "hard": 0.85,
        "very hard": 0.7,
    }[band]
    return base * hardness_scale / flutes


def all_material_names() -> tuple[str, ...]:
    """Return all canonical material names."""
    return tuple(mat.name for mat in WOOD_MATERIALS)


def iter_materials() -> Iterable[WoodMaterial]:
    """Yield all materials (helper for UI population)."""
    return iter(WOOD_MATERIALS)
