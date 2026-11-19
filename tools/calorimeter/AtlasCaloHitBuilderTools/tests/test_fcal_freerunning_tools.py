import unittest
import ROOT
from AtlasCaloHitBuilderTools import (
    LArFCalElectrodeToolCfg,
    CaloFreeRunningHitRecorderToolCfg,
    CaloFreeRunningHitWriter,
)


class TestFCalFreeRunningTools(unittest.TestCase):

    def test_lar_fcal_electrode_tool_cfg(self):
        tool_cfg = LArFCalElectrodeToolCfg(
            "FCalTool",
            FCalModule=1,
            FCalSide=1,
            FCalGapVolume="LAr::FCAL::Module1::Gap",
            Sampling=61,
            Detector=4,
            ZMin=4668.5,
            ZMax=5128.5,
            FCalCopyEtaIndex=[0, 1, 2],
            FCalCopyPhiIndex=[0, 1, 2],
            FCalCopyEta=[3.2, 3.5, 4.0],
            FCalCopyPhi=[0.1, 0.5, 1.0],
            FCalCopyDeltaEta=[0.1, 0.1, 0.1],
            FCalCopyDeltaPhi=[0.1, 0.1, 0.1],
        )
        self.assertIsNotNone(tool_cfg)
        self.assertEqual(tool_cfg.FCalModule, 1)
        self.assertEqual(tool_cfg.FCalSide, 1)
        self.assertEqual(tool_cfg.Sampling, 61)
        self.assertEqual(tool_cfg.Detector, 4)

    def test_fcal_tool_cpp_methods(self):
        tool = ROOT.LArFCalElectrodeTool("TestFCalTool")
        tool.setProperty("FCalModule", 1)
        tool.setProperty("FCalSide", 1)
        tool.setProperty("FCalGapVolume", "GapVol")
        tool.setProperty("FCalCopyEtaIndex", [0])
        tool.setProperty("FCalCopyPhiIndex", [0])
        tool.setProperty("FCalCopyEta", [3.2])
        tool.setProperty("FCalCopyPhi", [0.1])
        tool.setProperty("FCalCopyDeltaEta", [0.1])
        tool.setProperty("FCalCopyDeltaPhi", [0.1])
        tool.setProperty("Sampling", 61)
        tool.setProperty("Detector", 4)
        tool.setProperty("ZMin", 4668.5)
        tool.setProperty("ZMax", 5128.5)

        sc = tool.initialize()
        self.assertEqual(sc, ROOT.StatusCode.SUCCESS)

        # Hash computation
        h = tool.hash(0)
        self.assertGreater(h, 0)

    def test_freerunning_recorder_tool_cfg(self):
        tool_cfg = CaloFreeRunningHitRecorderToolCfg(
            "FreeRunningRecorder",
            FreeRunningListKey="FreeRunningHits",
            FreeRunningBinning=True,
            Subdet=0,
            AtlasBarrelEc=1,
            AtlasLArSampling=0,
            AtlasLArRegion=0,
            AtlasLArPart=1,
        )
        self.assertIsNotNone(tool_cfg)
        self.assertEqual(tool_cfg.FreeRunningListKey, "FreeRunningHits")
        self.assertTrue(tool_cfg.FreeRunningBinning)
        self.assertEqual(tool_cfg.Subdet, 0)

    def test_freerunning_hit_list(self):
        hit_list = ROOT.CaloFreeRunningHitList()
        self.assertEqual(hit_list.size(), 0)

        # Add a tile hit
        # add(cellID, energy, time, tglobal, eta, phi, sampling, side, module, tower, delta)
        cell_id = 123456789
        hit_list.add(cell_id, 100.0, 5.0, 15.0, 0.5, 1.2, 0, 1, 10, 2, 0.5)
        self.assertEqual(hit_list.size(), 1)
        self.assertEqual(hit_list.energy()[0], 100.0)

        # Add an LAr hit
        # addLAr(cellID, energy, time, tglobal, eta, phi, sampling, barrelEc, region, det, timeBin, source)
        lar_cell_id = 987654321
        hit_list.addLAr(lar_cell_id, 50.0, 2.5, 12.0, 1.5, 0.8, 1, 1, 0, 1, 1, 0)
        self.assertEqual(hit_list.size(), 2)
        self.assertEqual(hit_list.det()[1], 1)

    def test_freerunning_hit_writer(self):
        writer = CaloFreeRunningHitWriter(
            "FreeRunningWriter",
            InputListKey="FreeRunningHits",
            InputEventKey="Events",
            NtupleName="CollectionTree",
            AtlasFormat=False,
        )
        self.assertIsNotNone(writer)


if __name__ == "__main__":
    unittest.main()
