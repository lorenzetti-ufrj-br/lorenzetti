"""
GeoV1 package.

Provides the v1 (cylindrical simplified) detector construction and subdetectors.
"""

from .DetectorConstruction_v1 import DetectorConstruction_v1
from . import detectors

__all__ = [
    "DetectorConstruction_v1",
    "detectors",
]
