"""
Unit tests for the top-level geometry factory (DetectorConstructionCfg and DetectorFlags).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
for p in [_ROOT, os.path.join(_ROOT, "geometry"), os.path.join(_ROOT, "build/python")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# Mock ROOT if needed
if "ROOT" not in sys.modules:
    try:
        import ROOT
    except ImportError:
        mock_root = MagicMock()
        sys.modules["ROOT"] = mock_root

from geometry import (
    DetectorConstructionCfg,
    DetectorFlags,
    Plates,
    ProductionCuts,
    get_available_detectors,
    get_data_dir,
)
from GALTIC import GalticDetectorConstruction
from magfield import MagFieldFlags


class TestDetectorFactory(unittest.TestCase):
    """Test suite for geometry root factory and configuration flags."""

    def setUp(self):
        DetectorFlags.reset()
        MagFieldFlags.reset()

    def test_available_detectors(self):
        """Verifies available detector choices."""
        detectors = get_available_detectors()
        self.assertIn("GALTIC", detectors)
        self.assertIn("ATLAS", detectors)

    def test_detector_flags_defaults(self):
        """Verifies DetectorFlags default values and reset."""
        self.assertEqual(DetectorFlags.Version, "GALTIC")
        DetectorFlags.Version = "ATLAS"
        self.assertEqual(DetectorFlags.Version, "ATLAS")
        DetectorFlags.reset()
        self.assertEqual(DetectorFlags.Version, "GALTIC")

    def test_construct_galtic_by_version(self):
        """Constructs GALTIC via version='GALTIC' and version='v1'."""
        det1 = DetectorConstructionCfg("TestGaltic", version="GALTIC")
        self.assertIsInstance(det1, GalticDetectorConstruction)

        det2 = DetectorConstructionCfg("TestV1", version="v1")
        self.assertIsInstance(det2, GalticDetectorConstruction)

    def test_construct_galtic_by_detector_param(self):
        """Constructs GALTIC via detector='GALTIC'."""
        det = DetectorConstructionCfg("TestParam", detector="GALTIC")
        self.assertIsInstance(det, GalticDetectorConstruction)

    def test_data_dir_resolution(self):
        """Verifies pulse calibration data directory resolution."""
        data_dir = get_data_dir()
        self.assertTrue(os.path.isdir(data_dir))
        self.assertTrue(os.path.isfile(os.path.join(data_dir, "pulseTile.dat")))
        self.assertTrue(os.path.isfile(os.path.join(data_dir, "pulseLar.dat")))

    def test_backward_compatibility_geobase(self):
        """Verifies that importing DetectorConstructionCfg from GeoBase still works."""
        from GeoBase import DetectorConstructionCfg as GeoBaseCfg
        det = GeoBaseCfg("TestGeoBaseShim", version="GALTIC")
        self.assertIsInstance(det, GalticDetectorConstruction)


if __name__ == "__main__":
    unittest.main()
