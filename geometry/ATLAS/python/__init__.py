"""
ATLAS - High-fidelity realistic ATLAS detector package.
Provides both v1 (imperative legacy) and v2 (modern declarative JSON).
"""

from ATLAS.AtlasGeometryFlags import AtlasGeometryFlags
from ATLAS import v1
from ATLAS import v2
from ATLAS.v1 import legacy
from ATLAS.v1 import AtlasDetectorConstruction, DetectorConstruction

__all__ = [
    "AtlasGeometryFlags",
    "AtlasDetectorConstruction",
    "DetectorConstruction",
    "v1",
    "v2",
    "legacy",
]
