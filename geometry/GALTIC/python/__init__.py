"""
GALTIC - General Argon Liquid and Tile Integrated Calorimeter.

Provides unified layer definitions, fluent builders, and file-driven Geant4 construction.
"""

from .Layer import (
    Plates,
    ProductionCuts,
    ReadoutSegment,
    CaloSamplingLayer,
    DeadMaterialVolume,
    LArBarrelBuilder,
    TileCalBuilder,
    LArEMECBuilder,
    HECBuilder,
    DeadMaterialBuilder,
)
from .GalticCfg import (
    getGalticLArBarrelCfg,
    getGalticTileBarrelCfg,
    getGalticTileExtendedCfg,
    getGalticLArEMECCfg,
    getGalticHECCfg,
    getGalticDeadMaterialsCfg,
    getGalticAllSamplings,
    getGalticAllDeadMaterials,
)
from . import GalticCfg_v1
from . import GalticCfg_v2
from .DetectorConstruction import GalticDetectorConstruction, DetectorConstruction

__all__ = [
    "GalticDetectorConstruction",
    "DetectorConstruction",
    "Plates",
    "ProductionCuts",
    "ReadoutSegment",
    "CaloSamplingLayer",
    "DeadMaterialVolume",
    "LArBarrelBuilder",
    "TileCalBuilder",
    "LArEMECBuilder",
    "HECBuilder",
    "DeadMaterialBuilder",
    "GalticCfg_v1",
    "GalticCfg_v2",
    "getGalticLArBarrelCfg",
    "getGalticTileBarrelCfg",
    "getGalticTileExtendedCfg",
    "getGalticLArEMECCfg",
    "getGalticHECCfg",
    "getGalticDeadMaterialsCfg",
    "getGalticAllSamplings",
    "getGalticAllDeadMaterials",
]
