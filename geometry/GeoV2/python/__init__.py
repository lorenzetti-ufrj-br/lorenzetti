"""
GeoV2 package.

Provides the v2 (ATLAS Run 4 high-fidelity) detector construction, flags, and subdetectors.
"""

from .DetectorConstruction_v2 import DetectorConstruction_v2
from .AtlasGeometryFlags import AtlasGeometryFlags
from . import detectors

__all__ = [
    "DetectorConstruction_v2",
    "AtlasGeometryFlags",
    "detectors",
]
