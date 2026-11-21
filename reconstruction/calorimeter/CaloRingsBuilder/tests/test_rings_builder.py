import unittest
import ROOT

ROOT.gSystem.Load("liblorenzetti")

from CaloRingsBuilder import (
    CaloRingsBuilderCfg,
    StandardRingsMakerCfg,
    AsymRingsMakerCfg,
    CrossRingsMakerCfg,
    CornerRingsMakerCfg,
    StripsRingsMakerCfg,
    CustomRingsMakerCfg,
)


class TestCaloRingsBuilder(unittest.TestCase):

    def test_calo_rings_builder_cfg_all(self):
        makers = CaloRingsBuilderCfg("TestBuilder")
        self.assertEqual(len(makers), 6)
        names = [m.name() for m in makers]
        self.assertIn("TestBuilder_Standard", names)
        self.assertIn("TestBuilder_Asym", names)
        self.assertIn("TestBuilder_Cross", names)
        self.assertIn("TestBuilder_Corner", names)
        self.assertIn("TestBuilder_Strips", names)
        self.assertIn("TestBuilder_Custom", names)

        # Check output container keys
        keys = [m.OutputRingerKey for m in makers]
        self.assertEqual(keys, [
            "Rings",
            "Rings_Asym",
            "Rings_Cross",
            "Rings_Corner",
            "Rings_Strips",
            "Rings_Custom",
        ])

    def test_standard_rings_maker_cfg(self):
        maker = StandardRingsMakerCfg("StdMaker", OutputRingerKey="CustomRingsKey")
        self.assertEqual(maker.name(), "StdMaker")
        self.assertEqual(maker.OutputRingerKey, "CustomRingsKey")

    def test_asym_rings_maker_cfg(self):
        maker = AsymRingsMakerCfg("AsymMaker")
        self.assertEqual(maker.name(), "AsymMaker")
        self.assertEqual(maker.OutputRingerKey, "Rings_Asym")

    def test_cross_rings_maker_cfg(self):
        maker = CrossRingsMakerCfg("CrossMaker", CrossShift=2)
        self.assertEqual(maker.name(), "CrossMaker")
        self.assertEqual(maker.OutputRingerKey, "Rings_Cross")

    def test_corner_rings_maker_cfg(self):
        maker = CornerRingsMakerCfg("CornerMaker", CornerShift=2)
        self.assertEqual(maker.name(), "CornerMaker")
        self.assertEqual(maker.OutputRingerKey, "Rings_Corner")

    def test_strips_rings_maker_cfg(self):
        maker = StripsRingsMakerCfg("StripsMaker", Axis=1)
        self.assertEqual(maker.name(), "StripsMaker")
        self.assertEqual(maker.OutputRingerKey, "Rings_Strips")

    def test_custom_rings_maker_cfg(self):
        maker = CustomRingsMakerCfg(
            "CustomMaker",
            RingsShiftEta=[0.0, 1.0],
            RingsShiftPhi=[0.0, 1.0],
        )
        self.assertEqual(maker.name(), "CustomMaker")
        self.assertEqual(maker.OutputRingerKey, "Rings_Custom")


if __name__ == "__main__":
    unittest.main()
