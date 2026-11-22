"""
Detectors package for GeoV1.
"""

from .ECAL import getLArBarrelCfg
from .TILE import getTileBarrelCfg, getTileExtendedCfg
from .EMEC import getLArEMECCfg
from .HEC import getHECCfg
from .DeadMaterials import getDMVolumesCfg, getCrackVolumesCfg

__all__ = [
    "getLArBarrelCfg",
    "getTileBarrelCfg",
    "getTileExtendedCfg",
    "getLArEMECCfg",
    "getHECCfg",
    "getDMVolumesCfg",
    "getCrackVolumesCfg",
]
