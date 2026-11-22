"""
GALTIC - General Argon Liquid and Tile Integrated Calorimeter.

Provides unified layer definitions, fluent builders, and file-driven Geant4 construction.
"""

from .Layer import (
    Plates,
    ProductionCuts,
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
from .DetectorConstruction import GalticDetectorConstruction, DetectorConstruction

__all__ = [
    "GalticDetectorConstruction",
    "DetectorConstruction",
    "Plates",
    "ProductionCuts",
    "CaloSamplingLayer",
    "DeadMaterialVolume",
    "LArBarrelBuilder",
    "TileCalBuilder",
    "LArEMECBuilder",
    "HECBuilder",
    "DeadMaterialBuilder",
    "getGalticLArBarrelCfg",
    "getGalticTileBarrelCfg",
    "getGalticTileExtendedCfg",
    "getGalticLArEMECCfg",
    "getGalticHECCfg",
    "getGalticDeadMaterialsCfg",
    "getGalticAllSamplings",
    "getGalticAllDeadMaterials",
]
