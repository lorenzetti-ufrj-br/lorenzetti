"""
ATLAS v2 package - modern, file-driven JSON calorimeter geometry.
"""

from ATLAS.v2.Layer import (
    Plates,
    ProductionCuts,
    CaloSamplingLayer,
    DeadMaterialVolume,
    AtlasEmbBuilder,
    AtlasTileBuilder,
    AtlasEmecBuilder,
    AtlasHecBuilder,
    AtlasFcalBuilder,
    AtlasDeadMaterialBuilder,
)
from ATLAS.v2.AtlasCfg import getAtlasAllSamplings, getAtlasAllDeadMaterials
from ATLAS.v2.DetectorConstruction import AtlasDetectorConstruction, DetectorConstruction

__all__ = [
    "Plates",
    "ProductionCuts",
    "CaloSamplingLayer",
    "DeadMaterialVolume",
    "AtlasEmbBuilder",
    "AtlasTileBuilder",
    "AtlasEmecBuilder",
    "AtlasHecBuilder",
    "AtlasFcalBuilder",
    "AtlasDeadMaterialBuilder",
    "getAtlasAllSamplings",
    "getAtlasAllDeadMaterials",
    "AtlasDetectorConstruction",
    "DetectorConstruction",
]
