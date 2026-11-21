import unittest
import ROOT
import numpy as np

ROOT.gSystem.Load("liblorenzetti")

from CaloRingsTools import (
    StandardRingsToolCfg,
    AsymRingsToolCfg,
    CrossRingsToolCfg,
    CornerRingsToolCfg,
    StripsRingsToolCfg,
    CustomRingsToolCfg,
)


class TestCaloRingsTools(unittest.TestCase):

    def test_standard_rings_tool_cfg(self):
        tool = StandardRingsToolCfg("StandardRingsTool_Test")
        self.assertEqual(tool.name(), "StandardRingsTool_Test")
        self.assertEqual(len(tool.NRings), 7)
        self.assertEqual(sum(tool.NRings), 100)
        self.assertEqual(tool.DoSigmaCut, False)

    def test_asym_rings_tool_cfg(self):
        tool = AsymRingsToolCfg("AsymRingsTool_Test")
        self.assertEqual(tool.name(), "AsymRingsTool_Test")
        self.assertEqual(len(tool.NRings), 7)
        self.assertEqual(tool.NRings[0], (8 - 1) * 4 + 1)
        self.assertEqual(tool.NRings[1], (64 - 1) * 4 + 1)

    def test_cross_rings_tool_cfg(self):
        tool = CrossRingsToolCfg("CrossRingsTool_Test", CrossShift=2)
        self.assertEqual(tool.name(), "CrossRingsTool_Test")
        self.assertEqual(tool.CrossShift, 2)
        self.assertEqual(tool.NRings[0], 8 * 4)

    def test_corner_rings_tool_cfg(self):
        tool = CornerRingsToolCfg("CornerRingsTool_Test", CornerShift=4)
        self.assertEqual(tool.name(), "CornerRingsTool_Test")
        self.assertEqual(tool.CornerShift, 4)
        self.assertEqual(tool.NRings[0], 8 * 4)

    def test_strips_rings_tool_cfg(self):
        tool = StripsRingsToolCfg("StripsRingsTool_Test", Axis=1)
        self.assertEqual(tool.name(), "StripsRingsTool_Test")
        self.assertEqual(tool.Axis, 1)
        self.assertEqual(len(tool.NRings), 7)

    def test_custom_rings_tool_cfg(self):
        tool = CustomRingsToolCfg(
            "CustomRingsTool_Test",
            RingsShiftEta=[0.0, 1.0],
            RingsShiftPhi=[0.0, 1.0],
        )
        self.assertEqual(tool.name(), "CustomRingsTool_Test")
        self.assertEqual(list(tool.RingsShiftEta), [0.0, 1.0])
        self.assertEqual(list(tool.RingsShiftPhi), [0.0, 1.0])


if __name__ == "__main__":
    unittest.main()
