"""
GeoBase package.

Provides common geometry primitives, flags, and the DetectorConstructionCfg factory.
"""

import os
from pathlib import Path

from .DetectorConstructionCfg import DetectorConstructionCfg
from .DetectorFlags import DetectorFlags
from .PhysicalVolume import PhysicalVolume, Plates, ProductionCuts
from .SensitiveDetector import SensitiveDetector, atlasLArPhiShift
from .Calorimeter import Calorimeter
from .Tracking import getPixelBarrelCfg


def get_data_dir() -> str:
    """Finds the GeoBase shared data directory (pulse files)."""
    for p in (
        os.environ.get("LORENZETTI_GEOBASE_DATA_DIR"),
        os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
        str(Path(__file__).resolve().parents[1] / "data"),
        str(Path(__file__).resolve().parents[2] / "data" / "GeoBase"),
    ):
        if p and os.path.isdir(p):
            return p
    return ""


__all__ = [
    "DetectorConstructionCfg",
    "DetectorFlags",
    "PhysicalVolume",
    "Plates",
    "ProductionCuts",
    "SensitiveDetector",
    "atlasLArPhiShift",
    "Calorimeter",
    "getPixelBarrelCfg",
    "get_data_dir",
]
