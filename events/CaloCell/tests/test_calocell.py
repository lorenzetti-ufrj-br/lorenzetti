import unittest
import ROOT


class TestCaloCellEDM(unittest.TestCase):
    """Unit tests for xAOD::CaloCell and xAOD::CaloDetDescriptor EDM objects."""

    @classmethod
    def setUpClass(cls):
        ROOT.gROOT.SetBatch(True)
        ROOT.gSystem.Load("liblorenzetti")

    def test_calocell_instantiation_and_kinematics(self):
        cell = ROOT.xAOD.CaloCell(0.25, 1.15, 0.025, 0.025)
        self.assertAlmostEqual(cell.eta(), 0.25, places=4)
        self.assertAlmostEqual(cell.phi(), 1.15, places=4)
        self.assertAlmostEqual(cell.deltaEta(), 0.025, places=4)
        self.assertAlmostEqual(cell.deltaPhi(), 0.025, places=4)

        cell.setE(1450.0)
        cell.setEt(1200.0)
        cell.setTau(1.5)
        self.assertAlmostEqual(cell.e(), 1450.0, places=1)
        self.assertAlmostEqual(cell.et(), 1200.0, places=1)
        self.assertAlmostEqual(cell.tau(), 1.5, places=2)

    def test_calodetdescriptor_instantiation(self):
        desc = ROOT.xAOD.CaloDetDescriptor(
            0.25, 1.15, 0.025, 0.025,
            987654, 3200.0,
            ROOT.EMB1, ROOT.LAR,
            25.0, 0, 0
        )
        self.assertAlmostEqual(desc.eta(), 0.25, places=4)
        self.assertAlmostEqual(desc.phi(), 1.15, places=4)
        self.assertAlmostEqual(desc.deltaEta(), 0.025, places=4)
        self.assertAlmostEqual(desc.deltaPhi(), 0.025, places=4)
        self.assertAlmostEqual(desc.z(), 3200.0, places=1)
        self.assertEqual(desc.hash(), 987654)

    def test_calocell_t_struct(self):
        t_obj = ROOT.xAOD.CaloCell_t()
        t_obj.e = 2500.0
        t_obj.et = 2100.0
        t_obj.eta = 0.50
        t_obj.phi = -1.20
        t_obj.tau = 0.8
        t_obj.hash = 12345

        self.assertAlmostEqual(t_obj.e, 2500.0, places=1)
        self.assertAlmostEqual(t_obj.et, 2100.0, places=1)
        self.assertAlmostEqual(t_obj.eta, 0.50, places=4)
        self.assertAlmostEqual(t_obj.phi, -1.20, places=4)
        self.assertAlmostEqual(t_obj.tau, 0.8, places=2)
        self.assertEqual(t_obj.hash, 12345)

    def test_calocell_noise_suppression_configuration(self):
        from CaloCellBuilder import CaloCellNoiseSuppression, CaloCellNoiseSupression, CaloCellFilter
        # Test primary class
        filter_alg = CaloCellNoiseSuppression(
            "CaloCellNoiseSuppression",
            InputCellsKey="Cells_original",
            OutputCellsKey="Cells",
            SigmaThreshold=2.5,
        )
        props = filter_alg.getPropertiesDict()
        self.assertEqual(props["InputCellsKey"], "Cells_original")
        self.assertEqual(props["OutputCellsKey"], "Cells")
        self.assertAlmostEqual(props["SigmaThreshold"], 2.5)

        # Test aliases
        alias_alg1 = CaloCellNoiseSupression("SupressionAlias")
        self.assertEqual(alias_alg1.getPropertiesDict()["InputCellsKey"], "Cells_original")
        alias_alg2 = CaloCellFilter("FilterAlias")
        self.assertEqual(alias_alg2.getPropertiesDict()["InputCellsKey"], "Cells_original")

    def test_rootstream_esd_reader_generic(self):
        from RootStreamBuilder import RootStreamESDReader
        reader = RootStreamESDReader("ESDReader", OutputCellsKey="Cells_original")
        props = reader.getPropertiesDict()
        self.assertEqual(props["OutputCellsKey"], "Cells_original")
        self.assertNotIn("FilterBySigma", props)


if __name__ == "__main__":
    unittest.main()
