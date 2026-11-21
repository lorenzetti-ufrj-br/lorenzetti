import unittest
import math
import ROOT
from CaloHitTools import (
    CaloGridCellToolCfg,
    CaloBirksLawToolCfg,
    CaloTofCorrectionToolCfg,
    CaloStandardHitRecorderToolCfg,
)


class TestUniversalTools(unittest.TestCase):
    """Unit tests for universal calorimeter hit builder tools."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_grid_cell_tool_configuration_and_methods(self):
        eta_bins = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
        phi_bins = [-math.pi, -math.pi / 2, 0.0, math.pi / 2, math.pi]

        tool_cfg = CaloGridCellToolCfg(
            "TestGridCellTool",
            EtaBins=eta_bins,
            PhiBins=phi_bins,
            Sampling=2,
            Segment=1,
            Detector=0,
            ZMin=-2000.0,
            ZMax=2000.0,
            RMin=1400.0,
            RMax=2000.0,
        )

        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)

        # Test find method for eta
        eta_vec = ROOT.std.vector("float")()
        for v in eta_bins:
            eta_vec.push_back(v)
        self.assertEqual(tool.find(eta_vec, -0.2), 2)
        self.assertEqual(tool.find(eta_vec, 0.7), 4)
        self.assertEqual(tool.find(eta_vec, 2.5), -1)

        # Test findPhi with wrap-around
        phi_idx = tool.findPhi(0.1)
        self.assertEqual(phi_idx, 2)

        # Test hash formula
        # Barrel hash: (sampling + 0*17)*1e7 + segment*1e6 + bin
        bin_idx = 10
        expected_hash = (2 + 0 * 17) * 10000000 + 1 * 1000000 + bin_idx
        self.assertEqual(tool.hash(bin_idx), expected_hash)

    def test_grid_cell_tool_pre_execute(self):
        eta_bins = [0.0, 0.1, 0.2]
        phi_bins = [0.0, 0.1, 0.2]

        tool_cfg = CaloGridCellToolCfg(
            "TestGridCellToolPreExec",
            EtaBins=eta_bins,
            PhiBins=phi_bins,
            Sampling=2,
            Segment=0,
            Detector=0,
            ZMin=0.0,
            ZMax=1000.0,
            RMin=1000.0,
            RMax=2000.0,
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)

        # Test preExecute populates collection
        ctx = ROOT.SG.EventContext("StoreGate")
        col = ROOT.xAOD.CaloHitCollection()
        sc = tool.preExecute(ctx, col)
        self.assertEqual(sc, ROOT.StatusCode.SUCCESS)
        self.assertEqual(col.size(), 4)  # 2 eta bins * 2 phi bins

    def test_birks_law_tool_configuration(self):
        tool_cfg = CaloBirksLawToolCfg("TestBirksTool", BirksLArK=0.0486)
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)
        self.assertAlmostEqual(tool_cfg.BirksLArK, 0.0486, places=5)

    def test_tof_correction_tool_configuration(self):
        tool_cfg = CaloTofCorrectionToolCfg("TestTofTool", ApplyTof=True)
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)
        self.assertTrue(tool_cfg.ApplyTof)

    def test_standard_hit_recorder_tool_configuration(self):
        tool_cfg = CaloStandardHitRecorderToolCfg(
            "TestRecorderTool",
            OutputCollectionKey="MyHitCollection",
            NoiseStd=12.5,
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)
        self.assertEqual(tool_cfg.OutputCollectionKey, "MyHitCollection")
        self.assertAlmostEqual(tool_cfg.NoiseStd, 12.5, places=2)


if __name__ == "__main__":
    unittest.main()
