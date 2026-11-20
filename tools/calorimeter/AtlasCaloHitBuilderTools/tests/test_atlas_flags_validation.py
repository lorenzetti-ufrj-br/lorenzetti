import unittest
import ROOT
from GaugiKernel import LoggingLevel
from CaloHitBuilder.CaloHitFlags import CaloHitFlags, FreeRunningFlags
from AtlasCaloHitBuilderTools import (
    validate_atlas_hit_flags,
    TileBoxCellToolCfg,
    TileDualReadoutSplitToolCfg,
    LArAccordionToolCfg,
    LArEmecChargeCollectionToolCfg,
)


class TestAtlasFlagsValidation(unittest.TestCase):
    """Unit tests for flag defaulting and consistency validation in AtlasCaloHitBuilderTools."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def setUp(self):
        # Reset flags to safe standard state before each test
        CaloHitFlags.ActiveEnergyOnly = True
        CaloHitFlags.BirksLaw = True
        CaloHitFlags.AtlasHitTime = True
        CaloHitFlags.TileDualReadout = True
        CaloHitFlags.TilePmtSplit = "ushape"
        FreeRunningFlags.Enable = False
        FreeRunningFlags.AtlasFormat = False
        FreeRunningFlags.KeepHits = False
        FreeRunningFlags.NoBinning = False
        FreeRunningFlags.EmecChargeCollection = False
        FreeRunningFlags.EmecTables = ""
        FreeRunningFlags.EmecFieldMap = ""
        FreeRunningFlags.EmecHVMap = ""

    def test_valid_flags_pass(self):
        """Standard valid flags should pass validation without error."""
        try:
            validate_atlas_hit_flags()
        except Exception as e:
            self.fail(f"validate_atlas_hit_flags raised unexpected exception: {e}")

    def test_freerunning_prerequisite_atlas_format(self):
        """AtlasFormat without FreeRunningHits should raise ValueError."""
        FreeRunningFlags.AtlasFormat = True
        with self.assertRaises(ValueError) as ctx:
            validate_atlas_hit_flags()
        self.assertIn("AtlasFormat=True requires FreeRunningHits=True", str(ctx.exception))

    def test_freerunning_prerequisite_emec_charge_collection(self):
        """EmecChargeCollection without FreeRunningHits should raise ValueError."""
        FreeRunningFlags.EmecChargeCollection = True
        with self.assertRaises(ValueError) as ctx:
            validate_atlas_hit_flags()
        self.assertIn("EmecChargeCollection=True requires FreeRunningHits=True", str(ctx.exception))

    def test_emec_charge_collection_requires_files(self):
        """EmecChargeCollection with empty file paths should raise ValueError."""
        FreeRunningFlags.Enable = True
        FreeRunningFlags.EmecChargeCollection = True
        FreeRunningFlags.EmecTables = ""
        with self.assertRaises(ValueError) as ctx:
            validate_atlas_hit_flags()
        self.assertIn("EmecChargeTables path is empty", str(ctx.exception))

    def test_tile_dual_readout_invalid_split(self):
        """TileDualReadout with invalid TilePmtSplit should raise ValueError."""
        CaloHitFlags.TileDualReadout = True
        CaloHitFlags.TilePmtSplit = "cubic"
        with self.assertRaises(ValueError) as ctx:
            validate_atlas_hit_flags()
        self.assertIn("Invalid CaloHitFlags.TilePmtSplit", str(ctx.exception))

    def test_tool_defaults_from_flags(self):
        """Verify that Tool Cfg functions automatically pick up flag defaults when None."""
        CaloHitFlags.ActiveEnergyOnly = True
        CaloHitFlags.TileDualReadout = True
        CaloHitFlags.TilePmtSplit = "ushape"

        tile_cfg = TileBoxCellToolCfg("TileDefaultTest")
        self.assertTrue(tile_cfg.ActiveEnergyOnly)
        self.assertEqual(tile_cfg.TileDualReadout, 1)

        # Switch to linear split
        CaloHitFlags.TilePmtSplit = "linear"
        tile_cfg2 = TileBoxCellToolCfg("TileDefaultTest2")
        self.assertEqual(tile_cfg2.TileDualReadout, 2)

        # Accordion tool defaults ActiveEnergyOnly
        CaloHitFlags.ActiveEnergyOnly = False
        emb_cfg = LArAccordionToolCfg("EmbDefaultTest")
        self.assertFalse(emb_cfg.ActiveEnergyOnly)

    def test_custom_flags_instance(self):
        """Verify that passing an explicit flags object overrides the global singleton."""
        class CustomCaloFlags:
            ActiveEnergyOnly = False
            TileDualReadout = True
            TilePmtSplit = "linear"

        tile_cfg = TileBoxCellToolCfg("TileCustomTest", flags=CustomCaloFlags)
        self.assertFalse(tile_cfg.ActiveEnergyOnly)
        self.assertEqual(tile_cfg.TileDualReadout, 2)


if __name__ == "__main__":
    unittest.main()
