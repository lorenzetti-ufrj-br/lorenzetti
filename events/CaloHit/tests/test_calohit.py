import unittest
import ROOT


class TestCaloHitEDM(unittest.TestCase):
    """Unit tests for xAOD::CaloHit EDM object."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_calohit_instantiation_and_properties(self):
        hit = ROOT.xAOD.CaloHit()
        hit.setEta(0.40)
        hit.setPhi(-0.75)
        hit.setDeltaEta(0.025)
        hit.setDeltaPhi(0.025)
        hit.setHash(555123)

        self.assertAlmostEqual(hit.eta(), 0.40, places=4)
        self.assertAlmostEqual(hit.phi(), -0.75, places=4)
        self.assertAlmostEqual(hit.deltaEta(), 0.025, places=4)
        self.assertAlmostEqual(hit.deltaPhi(), 0.025, places=4)
        self.assertEqual(hit.hash(), 555123)

        # Deposit energy for bunch crossing ID 0
        hit.edep(0, 350.5)
        self.assertAlmostEqual(hit.edep(0), 350.5, places=1)
        self.assertEqual(hit.edep(1), 0.0)

        hit.clear()
        self.assertEqual(hit.edep(0), 0.0)

    def test_calohit_t_struct(self):
        t_obj = ROOT.xAOD.CaloHit_t()
        t_obj.eta = 0.15
        t_obj.phi = 2.10
        t_obj.deta = 0.025
        t_obj.dphi = 0.025
        t_obj.hash = 999111
        self.assertAlmostEqual(t_obj.eta, 0.15, places=4)
        self.assertAlmostEqual(t_obj.phi, 2.10, places=4)
        self.assertEqual(t_obj.hash, 999111)

    def test_calohit_builder_roi_defaults(self):
        from CaloHitBuilder import CaloHitBuilder
        builder = CaloHitBuilder("CaloHitBuilder")
        self.assertFalse(builder.OnlyRoI, "CaloHitBuilder.OnlyRoI must default to False")
        self.assertAlmostEqual(builder.EtaWindow, 0.4)
        self.assertAlmostEqual(builder.PhiWindow, 0.4)
        self.assertEqual(builder.TruthKey, "Particles")

        builder_roi = CaloHitBuilder("CaloHitBuilder", OnlyRoI=True, EtaWindow=0.5)
        self.assertTrue(builder_roi.OnlyRoI)
        self.assertAlmostEqual(builder_roi.EtaWindow, 0.5)

    def test_calohit_merge_roi_properties(self):
        from GaugiKernel import Configurable
        merge = Configurable(
            ROOT.CaloHitMerge,
            "CaloHitMerge",
            OnlyRoI=False,
            EtaWindow=0.3,
            PhiWindow=0.3,
            TruthKey="CustomParticles",
        )
        self.assertFalse(merge.OnlyRoI)
        self.assertAlmostEqual(merge.EtaWindow, 0.3, places=4)
        self.assertAlmostEqual(merge.PhiWindow, 0.3, places=4)
        self.assertEqual(merge.TruthKey, "CustomParticles")

    def test_rootstream_hitmaker_generic_schema(self):
        from RootStreamBuilder import RootStreamHITMaker
        maker = RootStreamHITMaker("RootStreamHITMaker")
        self.assertIn("ItemList", maker.getPropertiesDict())
        self.assertNotIn("OnlyRoI", maker.getPropertiesDict())


if __name__ == "__main__":
    unittest.main()
