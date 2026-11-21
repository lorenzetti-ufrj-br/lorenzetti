import unittest
import ROOT
from CaloCellTools import (
    PulseGeneratorToolCfg,
    PulseGeneratorCfg,
    OptimalFilterToolCfg,
    OptimalFilterCfg,
    ConstrainedOptimalFilterToolCfg,
    ConstrainedOptimalFilterCfg,
    PulsePerturberToolCfg,
    PulsePerturberCfg,
    PulsePertuberToolCfg,
    PulsePertuberCfg,
    get_cells_from_brl,
)


class TestCellTools(unittest.TestCase):
    """Unit tests for calorimeter cell tools configuration and instantiation."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_pulse_generator_tool_cfg(self):
        tool = PulseGeneratorToolCfg(
            "TestPulseGeneratorTool",
            NSamples=7,
            SamplingRate=25.0,
            Pedestal=0.0,
            NoiseMean=0.0,
            NoiseStd=1.5,
            StartSamplingBC=0,
        )
        self.assertEqual(tool.name(), "TestPulseGeneratorTool")
        self.assertEqual(tool.NSamples, 7)
        self.assertEqual(tool.NoiseStd, 1.5)

    def test_pulse_generator_cfg_alias(self):
        tool = PulseGeneratorCfg(
            "TestPulseGeneratorAlias",
            NSamples=5,
        )
        self.assertEqual(tool.name(), "TestPulseGeneratorAlias")
        self.assertEqual(tool.NSamples, 5)

    def test_optimal_filter_tool_cfg(self):
        tool = OptimalFilterToolCfg(
            "TestOptimalFilterTool",
            WeightsEnergy=[0.1, 0.2, 0.4, 0.2, 0.1],
            WeightsTime=[-0.1, -0.2, 0.0, 0.2, 0.1],
        )
        self.assertEqual(tool.name(), "TestOptimalFilterTool")
        self.assertEqual(len(tool.WeightsEnergy), 5)
        self.assertEqual(len(tool.WeightsTime), 5)

    def test_optimal_filter_cfg_alias(self):
        tool = OptimalFilterCfg(
            "TestOptimalFilterAlias",
            WeightsEnergy=[0.5, 0.5],
        )
        self.assertEqual(tool.name(), "TestOptimalFilterAlias")
        self.assertEqual(len(tool.WeightsEnergy), 2)

    def test_constrained_optimal_filter_tool_cfg(self):
        tool = ConstrainedOptimalFilterToolCfg(
            "TestCOFTool",
            PulsePath="dummy.txt",
            Threshold=10.0,
            NSamples=5,
            StartSamplingBC=1,
            SamplingRate=25.0,
        )
        self.assertEqual(tool.name(), "TestCOFTool")
        self.assertEqual(tool.Threshold, 10.0)
        self.assertEqual(tool.NSamples, 5)

    def test_constrained_optimal_filter_cfg_alias(self):
        tool = ConstrainedOptimalFilterCfg(
            "TestCOFAlias",
            Threshold=5.0,
        )
        self.assertEqual(tool.name(), "TestCOFAlias")
        self.assertEqual(tool.Threshold, 5.0)

    def test_pulse_perturber_tool_cfg(self):
        tool = PulsePerturberToolCfg(
            "TestPulsePerturberTool",
            NoiseMean=0.0,
            NoiseStd=2.0,
            InputEventKey="Events",
        )
        self.assertEqual(tool.name(), "TestPulsePerturberTool")
        self.assertEqual(tool.NoiseStd, 2.0)
        self.assertEqual(tool.InputEventKey, "Events")

    def test_pulse_pertuber_aliases(self):
        tool1 = PulsePerturberCfg("Alias1", NoiseStd=1.0)
        tool2 = PulsePertuberToolCfg("Alias2", NoiseStd=1.5)
        tool3 = PulsePertuberCfg("Alias3", NoiseStd=2.0)
        self.assertEqual(tool1.name(), "Alias1")
        self.assertEqual(tool2.name(), "Alias2")
        self.assertEqual(tool3.name(), "Alias3")


if __name__ == "__main__":
    unittest.main()
