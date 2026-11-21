import unittest
import ROOT
from CaloClusterTools import ShowerShapeToolCfg, MomentsToolCfg, MomentsToolsCfg


class TestClusterTools(unittest.TestCase):
    """Unit tests for calorimeter cluster tools configuration and instantiation."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_shower_shape_tool_cfg(self):
        tool = ShowerShapeToolCfg("TestShowerShapeTool")
        self.assertEqual(tool.name(), "TestShowerShapeTool")

    def test_moments_tool_cfg(self):
        tool = MomentsToolCfg("TestMomentsTool")
        self.assertEqual(tool.name(), "TestMomentsTool")

    def test_moments_tools_cfg_alias(self):
        tool = MomentsToolsCfg("TestMomentsToolsAlias")
        self.assertEqual(tool.name(), "TestMomentsToolsAlias")


if __name__ == "__main__":
    unittest.main()
