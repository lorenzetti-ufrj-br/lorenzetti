"""
ATLAS.legacy - Legacy detector modeling primitives migrated from GeoBase.
Preserved exclusively for the ATLAS high-fidelity detector model.
"""

import os
from pathlib import Path

from .PhysicalVolume import PhysicalVolume, Plates, ProductionCuts
from .SensitiveDetector import SensitiveDetector, atlasLArPhiShift
from .Calorimeter import Calorimeter
from .Tracking import getPixelBarrelCfg


def get_data_dir() -> str:
    """Finds the ATLAS/GALTIC data directory containing pulse calibration files."""
    for p in (
        os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
        str(Path(__file__).resolve().parents[2] / "data"),
        str(Path(__file__).resolve().parents[3] / "GALTIC" / "data"),
        str(Path(__file__).resolve().parents[4] / "data" / "GeoBase"),
    ):
        if p and os.path.isdir(p):
            return p
    return ""


__all__ = [
    "PhysicalVolume",
    "Plates",
    "ProductionCuts",
    "SensitiveDetector",
    "atlasLArPhiShift",
    "Calorimeter",
    "getPixelBarrelCfg",
    "get_data_dir",
]
