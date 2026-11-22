"""
ATLAS - High-fidelity realistic ATLAS detector package (GeoModel / SQLite / Run 4).
"""

from .DetectorConstruction_v2 import DetectorConstruction_v2
from .AtlasGeometryFlags import AtlasGeometryFlags

AtlasDetectorConstruction = DetectorConstruction_v2

__all__ = [
    "AtlasDetectorConstruction",
    "DetectorConstruction_v2",
    "AtlasGeometryFlags",
]
