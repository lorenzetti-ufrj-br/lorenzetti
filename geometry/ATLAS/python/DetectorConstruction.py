"""
DetectorConstruction.py - Default ATLAS detector construction orchestrator.
Forwarding to ATLAS.v1 during migration.
"""

from ATLAS.v1.DetectorConstruction import AtlasDetectorConstruction, DetectorConstruction

__all__ = [
    "AtlasDetectorConstruction",
    "DetectorConstruction",
]
