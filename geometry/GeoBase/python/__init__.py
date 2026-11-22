"""
GeoBase - Backward compatibility shim.

Redirects imports to root geometry package and ATLAS.legacy.
"""

from geometry import (
    DetectorConstructionCfg,
    DetectorFlags,
    Plates,
    ProductionCuts,
    get_data_dir,
)
from .PhysicalVolume import PhysicalVolume
from .SensitiveDetector import SensitiveDetector, atlasLArPhiShift
from .Calorimeter import Calorimeter
from .Tracking import getPixelBarrelCfg

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
