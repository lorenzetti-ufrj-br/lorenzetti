"""
ATLAS - High-fidelity realistic ATLAS detector package (GeoModel / SQLite / Run 4).
"""

from .DetectorConstruction import AtlasDetectorConstruction, DetectorConstruction
from .AtlasGeometryFlags import AtlasGeometryFlags

__all__ = [
    "AtlasDetectorConstruction",
    "DetectorConstruction",
    "AtlasGeometryFlags",
]
