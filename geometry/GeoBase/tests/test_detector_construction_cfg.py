"""
Unit tests for DetectorConstructionCfg and DetectorFlags.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(_ROOT, "build/python"))

# Mock ROOT if not available
if "ROOT" not in sys.modules:
    try:
        import ROOT
    except ImportError:
        mock_root = MagicMock()
        sys.modules["ROOT"] = mock_root

from GeoBase import DetectorConstructionCfg, DetectorFlags, PhysicalVolume, SensitiveDetector, get_data_dir
from GeoV1 import DetectorConstruction_v1
from GeoV2 import DetectorConstruction_v2, AtlasGeometryFlags
from magfield import MagFieldFlags


class TestDetectorConstructionCfg(unittest.TestCase):
    def setUp(self):
        DetectorFlags.reset()
        AtlasGeometryFlags.reset()
        MagFieldFlags.reset()

    def test_detector_flags_defaults(self):
        self.assertEqual(DetectorFlags.Version, "v2")
        flags = DetectorFlags()
        self.assertEqual(flags.Version, "v2")
        self.assertEqual(flags.to_dict(), {"Version": "v2"})

    def test_detector_flags_override_and_reset(self):
        DetectorFlags.Version = "v1"
        self.assertEqual(DetectorFlags.Version, "v1")
        flags = DetectorFlags()
        self.assertEqual(flags.Version, "v1")
        DetectorFlags.reset()
        self.assertEqual(DetectorFlags.Version, "v2")

    def test_construct_v1(self):
        MagFieldFlags.EnableField = True
        det = DetectorConstructionCfg("TestV1", version="v1")
        self.assertIsInstance(det, DetectorConstruction_v1)

    def _disable_external_atlas_v2(self):
        AtlasGeometryFlags.AtlasRun4 = False
        AtlasGeometryFlags.TileAtlasRun4 = False
        AtlasGeometryFlags.AtlasForwardShielding = False
        AtlasGeometryFlags.AtlasFullField = False
        AtlasGeometryFlags.AtlasBarrelGapServices = False

    def test_construct_v2(self):
        self._disable_external_atlas_v2()
        AtlasGeometryFlags.TileAtlasGeometry = True
        MagFieldFlags.EnableField = False
        det = DetectorConstructionCfg("TestV2", version="v2")
        self.assertIsInstance(det, DetectorConstruction_v2)
        # Verify solenoid field is enabled by default in v2 when general field is False
        self.assertTrue(MagFieldFlags.EnableSolenoidOnly)

    def test_construct_default_uses_detector_flags(self):
        DetectorFlags.Version = "v1"
        det = DetectorConstructionCfg("TestDefault")
        self.assertIsInstance(det, DetectorConstruction_v1)

        DetectorFlags.Version = "v2"
        self._disable_external_atlas_v2()
        det2 = DetectorConstructionCfg("TestDefaultV2")
        self.assertIsInstance(det2, DetectorConstruction_v2)

    def test_kwargs_override(self):
        MagFieldFlags.EnableField = False
        det = DetectorConstructionCfg(
            "TestOverrideV1",
            version="v1",
            UseMagneticField=True,
        )
        self.assertIsInstance(det, DetectorConstruction_v1)
        self.assertTrue(det.UseMagneticField)

    def test_data_dir_resolution(self):
        data_dir = get_data_dir()
        self.assertTrue(os.path.isdir(data_dir))
        self.assertTrue(os.path.isfile(os.path.join(data_dir, "pulseTile.dat")))
        self.assertTrue(os.path.isfile(os.path.join(data_dir, "pulseLar.dat")))


if __name__ == "__main__":
    unittest.main()
