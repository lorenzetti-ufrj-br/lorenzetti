import unittest
import math
import ROOT
from CaloHitBuilder.CaloHitFlags import CaloHitFlags
from AtlasCaloHitTools import (
    TileBoxCellToolCfg,
    TileDualReadoutSplitToolCfg,
    TilePmtPropagationTimeToolCfg,
)


class TestTileTools(unittest.TestCase):
    """Unit tests for ATLAS Tile hit builder tools."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_tile_box_cell_tool(self):
        phi_bins = [-math.pi + i * (2 * math.pi / 64) for i in range(65)]
        tool_cfg = TileBoxCellToolCfg(
            "TestTileBoxTool",
            Sampling=5,
            Segment=0,
            Detector=0,
            ZMin=-3000.0,
            ZMax=3000.0,
            RMin=2280.0,
            RMax=3820.0,
            PhiBins=phi_bins,
            CellEta=[0.05, 0.15],
            CellDeltaEta=[0.1, 0.1],
            CellBoxRMin=[2300.0, 2300.0],
            CellBoxRMax=[2600.0, 2600.0],
            CellBoxZMin=[0.0, 1000.0],
            CellBoxZMax=[1000.0, 2000.0],
            CellBoxIndex=[0, 1],
            CellNPmt=[2, 2],
            SpecialModule=[15],
            SpecialNPmt=[1],
        )

        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)

        # Test findCell
        self.assertEqual(tool.findCell(2450.0, 500.0), 0)
        self.assertEqual(tool.findCell(2450.0, 1500.0), 1)
        self.assertEqual(tool.findCell(2100.0, 500.0), -1)

        # Test tileNPmt: module 15 has special 1 PMT
        # phi_bins[0] is module 32 (-pi). Module 15 is around (15+0.5)*2pi/64
        # Test standard cell npmt
        self.assertEqual(tool.tileNPmt(0, 0), 2)

    def test_tile_dual_readout_split_tool(self):
        CaloHitFlags.TilePmtSplit = "ushape"
        phi_bins = [-math.pi + i * (2 * math.pi / 64) for i in range(65)]
        tool_cfg = TileDualReadoutSplitToolCfg(
            "TestTileSplitTool",
            Sampling=5,
            PhiBins=phi_bins,
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)
        self.assertEqual(tool_cfg.TileDualReadout, 1)

    def test_tile_pmt_propagation_time_tool(self):
        phi_bins = [-math.pi + i * (2 * math.pi / 64) for i in range(65)]
        tool_cfg = TilePmtPropagationTimeToolCfg(
            "TestTileTimeTool",
            PhiBins=phi_bins,
            CellRCentre=[2450.0, 2450.0],
            CellZCentre=[500.0, 1500.0],
        )
        tool = tool_cfg.c_ptr()
        self.assertEqual(tool.initialize(), ROOT.StatusCode.SUCCESS)


if __name__ == "__main__":
    unittest.main()
