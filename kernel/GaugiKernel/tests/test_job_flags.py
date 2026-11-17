"""
Unit tests for JobFlags and domain-specific dataclass steering flags.
"""

from dataclasses import dataclass
from typing import Optional
import unittest
import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, os.path.join(_ROOT, "build/python"))

try:
    import ROOT
except ImportError:
    import unittest.mock
    sys.modules["ROOT"] = unittest.mock.MagicMock()

from GaugiKernel import JobFlags
from GeoBase import DetectorFlags
from GeoV2 import AtlasGeometryFlags
from magfield import MagFieldFlags
from CaloHitBuilder import CaloHitFlags, FreeRunningFlags
from CaloCellBuilder import CaloFlags, CrossTalkFlags, AnomalyFlags
from CaloClusterBuilder import CaloClusterFlags
from RootStreamBuilder import RootStreamESDFlags, RootStreamAODFlags


@dataclass(init=False)
class DummyFlags(JobFlags):
    FlagA: bool = True
    FlagB: str = "default"
    FlagC: Optional[int] = None


class TestJobFlags(unittest.TestCase):
    def setUp(self):
        DummyFlags.reset()
        AtlasGeometryFlags.reset()
        MagFieldFlags.reset()
        CaloHitFlags.reset()
        FreeRunningFlags.reset()
        CaloFlags.reset()
        RootStreamESDFlags.reset()

    def test_class_level_modification_and_to_dict(self):
        self.assertTrue(DummyFlags.FlagA)
        self.assertEqual(DummyFlags.FlagB, "default")

        # Simulates --pre-init "DummyFlags.FlagA = False; DummyFlags.FlagB = 'custom'"
        DummyFlags.FlagA = False
        DummyFlags.FlagB = "custom"

        d = DummyFlags.to_dict()
        self.assertFalse(d["FlagA"])
        self.assertEqual(d["FlagB"], "custom")
        self.assertIsNone(d["FlagC"])

    def test_instance_inherits_class_modifications(self):
        DummyFlags.FlagA = False
        inst = DummyFlags()
        self.assertFalse(inst.FlagA)
        self.assertEqual(inst.FlagB, "default")
        self.assertFalse(inst.to_dict()["FlagA"])

    def test_instance_explicit_override(self):
        DummyFlags.FlagA = False
        inst = DummyFlags(FlagA=True, FlagB="override")
        self.assertTrue(inst.FlagA)
        self.assertEqual(inst.FlagB, "override")

    def test_reset(self):
        DummyFlags.FlagA = False
        DummyFlags.FlagB = "changed"
        DummyFlags.reset()
        self.assertTrue(DummyFlags.FlagA)
        self.assertEqual(DummyFlags.FlagB, "default")

    def test_json_serialization(self):
        DummyFlags.FlagA = False
        json_str = DummyFlags.to_json()
        self.assertIn('"FlagA": false', json_str)

        DummyFlags.reset()
        DummyFlags.from_json('{"FlagA": false, "FlagB": "from_json"}')
        self.assertFalse(DummyFlags.FlagA)
        self.assertEqual(DummyFlags.FlagB, "from_json")

    def test_from_dict(self):
        inst = DummyFlags.from_dict({"FlagA": False, "FlagB": "dict_val", "UnknownKey": 123})
        self.assertFalse(inst.FlagA)
        self.assertEqual(inst.FlagB, "dict_val")
        self.assertFalse(hasattr(inst, "UnknownKey"))


class TestAtlasGeometryFlags(unittest.TestCase):
    def setUp(self):
        AtlasGeometryFlags.reset()

    def test_apply_defaults_v2(self):
        self.assertIsNone(AtlasGeometryFlags.AtlasEmb)
        AtlasGeometryFlags.apply_defaults(is_v2=True)
        self.assertTrue(AtlasGeometryFlags.AtlasEmb)
        self.assertTrue(AtlasGeometryFlags.TileAtlasGeometry)
        self.assertTrue(AtlasGeometryFlags.AtlasRun4)

    def test_apply_defaults_v1(self):
        self.assertIsNone(AtlasGeometryFlags.AtlasEmb)
        AtlasGeometryFlags.apply_defaults(is_v2=False)
        self.assertFalse(AtlasGeometryFlags.AtlasEmb)
        self.assertFalse(AtlasGeometryFlags.TileAtlasGeometry)

    def test_pre_init_override_retained_after_apply_defaults(self):
        AtlasGeometryFlags.AtlasEmb = False
        AtlasGeometryFlags.apply_defaults(is_v2=True)
        self.assertFalse(AtlasGeometryFlags.AtlasEmb)
        self.assertTrue(AtlasGeometryFlags.TileAtlasGeometry)


class TestCaloHitAndFreeRunningFlags(unittest.TestCase):
    def setUp(self):
        CaloHitFlags.reset()
        FreeRunningFlags.reset()

    def test_calo_hit_flags_defaults(self):
        CaloHitFlags.apply_defaults(is_v2=True)
        self.assertTrue(CaloHitFlags.ActiveEnergyOnly)
        self.assertTrue(CaloHitFlags.BirksLaw)
        self.assertEqual(CaloHitFlags.NeutronTimeCut, 150.0)

    def test_free_running_flags_paths(self):
        FreeRunningFlags.apply_defaults(is_v2=True)
        self.assertIn("EmecTables-ATLAS-P2-RUN4-01-01-00.csv", FreeRunningFlags.EmecTables)


class TestMagFieldFlags(unittest.TestCase):
    def setUp(self):
        MagFieldFlags.reset()

    def test_solenoid_default_on_v2_when_general_field_off(self):
        MagFieldFlags.apply_defaults(is_v2=True)
        self.assertTrue(MagFieldFlags.EnableSolenoidOnly)

    def test_solenoid_default_off_when_general_field_on(self):
        MagFieldFlags.EnableField = True
        MagFieldFlags.apply_defaults(is_v2=True)
        self.assertFalse(MagFieldFlags.EnableSolenoidOnly)


class TestReconstructionFlags(unittest.TestCase):
    def test_calo_flags(self):
        CaloFlags.reset()
        self.assertFalse(CaloFlags.DoCrossTalk)
        CaloFlags.DoCrossTalk = True
        self.assertTrue(CaloFlags.to_dict()["DoCrossTalk"])

    def test_root_stream_flags(self):
        RootStreamESDFlags.reset()
        self.assertFalse(RootStreamESDFlags.SaveAllCells)
        RootStreamESDFlags.SaveAllCells = True
        self.assertTrue(RootStreamESDFlags.to_dict()["SaveAllCells"])


if __name__ == "__main__":
    unittest.main()
