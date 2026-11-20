import unittest
import math
import ROOT
from AtlasCaloHitBuilderTools import (
    LArAccordionToolCfg,
    LArEmecCompartmentToolCfg,
    LArHecModuleToolCfg,
    LArEmecChargeCollectionToolCfg,
)


class TestLArTools(unittest.TestCase):
    """Unit tests for ATLAS LAr hit builder tools."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_lar_accordion_tool(self):
        phi_bins = [-math.pi + i * (2 * math.pi / 64) for i in range(65)]
        tool_cfg = LArAccordionToolCfg(
            "TestLArAccordionTool",
            Sampling=2,
            Segment=0,
            Detector=1,
            ZMin=-3150.0,
            ZMax=3150.0,
            RMin=1500.0,
            RMax=1960.0,
            PhiBins=phi_bins,
            CellEta=[0.05 * i for i in range(56)],
            CellDeltaEta=[0.025 for _ in range(56)],
            EmbMode=1,
            EmbSampling=2,
            EmbRegion=0,
            EmbSampSeg=True,
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)

        # Test embFindCell for central barrel point
        # eta ~ 0.2 at r=1600, z=323.2
        cell_idx = tool.embFindCell(1600.0, 0.0, 323.2)
        self.assertGreaterEqual(cell_idx, 0)

    def test_lar_emec_compartment_tool(self):
        phi_bins = [-math.pi + i * (2 * math.pi / 64) for i in range(65)]
        tool_cfg = LArEmecCompartmentToolCfg(
            "TestLArEmecTool",
            Sampling=11,
            Segment=0,
            Detector=2,
            ZMin=3700.0,
            ZMax=4300.0,
            RMin=300.0,
            RMax=2100.0,
            PhiBins=phi_bins,
            CellEta=[1.5 + 0.025 * i for i in range(40)],
            CellDeltaEta=[0.025 for _ in range(40)],
            EmecCompartment=1,
            EmecEtaScale=10.0,
            EmecEtaOffset=25.0,
            EmecMaxEta=6,
            EmecFocalShift=3689.5,
            EmecZInner=[3000 for _ in range(7)],
            EmecZSep12=[3000 for _ in range(44)],
            EmecZSep23=[3000 for _ in range(22)],
            EmecWheelRMin=[330.0],
            EmecWheelRMax=[2050.0],
            EmecWheelZMin=[3700.0],
            EmecWheelZMax=[4300.0],
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)
        self.assertEqual(tool_cfg.EmecCompartment, 1)

    def test_lar_hec_module_tool(self):
        phi_bins = [-math.pi + i * (2 * math.pi / 64) for i in range(65)]
        tool_cfg = LArHecModuleToolCfg(
            "TestLArHecTool",
            Sampling=14,
            Segment=0,
            Detector=3,
            ZMin=4277.0,
            ZMax=4797.0,
            RMin=472.0,
            RMax=2030.0,
            PhiBins=phi_bins,
            CellEta=[1.5, 1.6],
            CellDeltaEta=[0.1, 0.1],
            CellBoxRMin=[472.0, 472.0],
            CellBoxRMax=[2030.0, 2030.0],
            CellBoxZMin=[4277.0, 4500.0],
            CellBoxZMax=[4500.0, 4797.0],
            CellBoxIndex=[0, 1],
            CellRadiusModules=32,
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)

        # Test cellRadius projection for module 0 (phi=0 to 2pi/32, center pi/32)
        r_orig = 1000.0
        phi_center = math.pi / 32.0
        r_proj = tool.cellRadius(r_orig, phi_center)
        self.assertAlmostEqual(r_proj, r_orig, places=3)

    def test_lar_emec_charge_collection_tool(self):
        tool_cfg = LArEmecChargeCollectionToolCfg(
            "TestLArEmecChargeTool",
            EmecCompartment=1,
            EmecFocalShift=3689.5,
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)
        self.assertFalse(tool_cfg.EmecChargeCollection)


if __name__ == "__main__":
    unittest.main()
