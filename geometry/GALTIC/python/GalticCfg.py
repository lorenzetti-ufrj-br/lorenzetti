"""
GalticCfg.py - Single-source access for GALTIC configurations.

Provides backwards compatibility and direct imports.
Defaults to canonical GalticCfg_v1 (matching original v1 parametric detector).
For the v2 configuration, import directly from GALTIC.GalticCfg_v2.
"""

from GALTIC.GalticCfg_v1 import (
    getGalticLArBarrelCfg,
    getGalticTileBarrelCfg,
    getGalticTileExtendedCfg,
    getGalticLArEMECCfg,
    getGalticHECCfg,
    getGalticDeadMaterialsCfg,
    getGalticAllSamplings,
    getGalticAllDeadMaterials,
)

__all__ = [
    "getGalticLArBarrelCfg",
    "getGalticTileBarrelCfg",
    "getGalticTileExtendedCfg",
    "getGalticLArEMECCfg",
    "getGalticHECCfg",
    "getGalticDeadMaterialsCfg",
    "getGalticAllSamplings",
    "getGalticAllDeadMaterials",
]
