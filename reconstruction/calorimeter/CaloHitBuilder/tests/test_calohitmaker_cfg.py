import unittest
import ROOT
from CaloHitBuilder.CaloHitMaker import CaloHitMakerCfg


class MockVolume:
    def __init__(self):
        self.RMin = 100.0
        self.RMax = 200.0
        self.ZMin = -500.0
        self.ZMax = 500.0


class MockGenericSensitive:
    def __init__(self):
        self.EtaBins = [-2.5, 0.0, 2.5]
        self.PhiBins = [-3.14, 0.0, 3.14]
        self.Segment = 0
        self.BirksLArK = 0.05832


class MockGenericSampling:
    def __init__(self):
        self.Sampling = 1
        self.Detector = 1
        self.CollectionKey = "GenericHits"
        self.Noise = 0.0
        self._vol = MockVolume()
        self._sens = MockGenericSensitive()

    def name(self):
        return "GenericSamp"

    def volume(self):
        return self._vol

    def sensitive(self):
        return self._sens


class MockAtlasTileSensitive:
    def __init__(self):
        self.PhiBins = [-3.14, 0.0, 3.14]
        self.Segment = 0
        self.Cells = {
            "BoxRMin": [100.0],
            "BoxRMax": [200.0],
            "BoxZMin": [-500.0],
            "BoxZMax": [500.0],
            "BoxCell": [0],
            "Eta": [0.0],
            "DeltaEta": [0.1],
            "AtlasSection": [1],
            "AtlasTower": [0],
            "AtlasSampling": [0],
            "RCentre": [150.0],
            "ZCentre": [0.0],
            "NPmt": [2],
            "AtlasEtaIndex": [0],
        }


class MockAtlasTileSampling:
    def __init__(self):
        self.Sampling = 5
        self.Detector = 2
        self.CollectionKey = "TileHits"
        self.Noise = 0.0
        self._vol = MockVolume()
        self._sens = MockAtlasTileSensitive()

    def name(self):
        return "TileSamp"

    def volume(self):
        return self._vol

    def sensitive(self):
        return self._sens


class TestCaloHitMakerConfiguration(unittest.TestCase):

    def test_generic_sampling_configuration(self):
        samp = MockGenericSampling()
        maker = CaloHitMakerCfg(
            "GenericMaker",
            samp,
            OutputCollectionKey="GenericHits",
            BirksLaw=True,
            AtlasHitTime=True,
        )
        self.assertIsNotNone(maker)
        self.assertEqual(maker.CellIdentifier.name(), "GenericMaker_GridCellTool")
        self.assertEqual(len(maker.EnergyModifiers), 1)
        self.assertEqual(maker.EnergyModifiers[0].name(), "GenericMaker_BirksLawTool")
        self.assertEqual(maker.TimeCorrection.name(), "GenericMaker_TofCorrectionTool")
        self.assertEqual(len(maker.HitRecorders), 1)
        self.assertEqual(maker.HitRecorders[0].name(), "GenericMaker_StandardHitRecorderTool")

    def test_atlas_tile_sampling_configuration(self):
        samp = MockAtlasTileSampling()
        maker = CaloHitMakerCfg(
            "TileMaker",
            samp,
            OutputCollectionKey="TileHits",
            BirksLaw=True,
            TileDualReadout=1,
            AtlasHitTime=True,
            FreeRunningHits=True,
        )
        self.assertIsNotNone(maker)
        self.assertEqual(maker.CellIdentifier.name(), "TileMaker_TileBoxCellTool")
        self.assertEqual(len(maker.EnergyModifiers), 2)
        self.assertEqual(maker.EnergyModifiers[0].name(), "TileMaker_BirksLawTool")
        self.assertEqual(maker.EnergyModifiers[1].name(), "TileMaker_TileDualReadoutSplitTool")
        self.assertEqual(maker.TimeCorrection.name(), "TileMaker_TilePmtPropagationTimeTool")
        self.assertEqual(len(maker.HitRecorders), 2)
        self.assertEqual(maker.HitRecorders[0].name(), "TileMaker_StandardHitRecorderTool")
        self.assertEqual(maker.HitRecorders[1].name(), "TileMaker_FreeRunningHitRecorderTool")


if __name__ == "__main__":
    unittest.main()
