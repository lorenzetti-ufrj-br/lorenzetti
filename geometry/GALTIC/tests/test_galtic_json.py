"""
Unit tests for GALTIC geometry builders and JSON round-trip serialization.
"""

import os
import sys
import tempfile
import unittest

from CaloCell import CaloSampling

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
for p in [_ROOT, os.path.join(_ROOT, "geometry"), os.path.join(_ROOT, "geometry/GALTIC/python"), os.path.join(_ROOT, "build/python")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from GALTIC import (
    GalticDetectorConstruction,
    DetectorConstruction,
    CaloSamplingLayer,
    DeadMaterialVolume,
    Plates,
    ProductionCuts,
    LArBarrelBuilder,
    TileCalBuilder,
    LArEMECBuilder,
    HECBuilder,
    DeadMaterialBuilder,
    getGalticAllSamplings,
    getGalticAllDeadMaterials,
)


class TestGalticGeometry(unittest.TestCase):
    """Test suite for GALTIC parametric geometry components."""

    def test_layer_builders(self):
        """Tests individual layer builders for calorimeter subdetectors."""
        lar = (
            LArBarrelBuilder("EMB1", CaloSampling.EMB1)
            .radii(1500.0, 1600.0)
            .z_length(3000.0)
            .segmentation(nof_layers=16, absorber_th=1.53, gap_th=4.5)
            .granularity(delta_eta=0.003125, delta_phi=0.02454)
            .electronics(noise_mev=40.0, pulse_file="")
            .build()
        )
        self.assertEqual(lar.sampling, int(CaloSampling.EMB1))
        self.assertEqual(lar.Name, "EMB1")
        self.assertEqual(lar.r_min, 1500.0)
        self.assertEqual(lar.r_max, 1600.0)
        self.assertEqual(lar.delta_eta, 0.003125)
        self.assertEqual(lar.plates, Plates.Horizontal)

        tile = (
            TileCalBuilder("TileBar0", CaloSampling.TileCal1)
            .radii(2280.0, 2600.0)
            .length_and_center(z_size=5640.0, z_center=0.0)
            .granularity(delta_eta=0.1, delta_phi=0.1)
            .electronics(noise_mev=25.0, pulse_file="")
            .build()
        )
        self.assertEqual(tile.sampling, int(CaloSampling.TileCal1))
        self.assertEqual(tile.Name, "TileBar0")
        self.assertEqual(tile.plates, Plates.Horizontal)

    def test_all_samplings_registry(self):
        """Validates all sampling layers defined in GalticCfg."""
        samplings = getGalticAllSamplings()
        self.assertGreaterEqual(len(samplings), 20)
        sampling_ids = [s.sampling for s in samplings]
        # Check presence of key samplings
        self.assertIn(2, sampling_ids)   # EMB1
        self.assertIn(3, sampling_ids)   # EMB2
        self.assertIn(5, sampling_ids)   # TileCal1
        self.assertIn(11, sampling_ids)  # EMEC1
        self.assertIn(14, sampling_ids)  # HEC1

    def test_detector_construction_json_roundtrip(self):
        """Tests full GalticDetectorConstruction build and JSON file save/load."""
        det = GalticDetectorConstruction("TestGaltic")
        self.assertGreater(len(det.samplings), 20)
        self.assertGreater(len(det.dead_materials), 0)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            det.save(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 1000)

            det_loaded = GalticDetectorConstruction("LoadedGaltic", geometry_file=tmp_path)
            self.assertEqual(len(det_loaded.samplings), len(det.samplings))
            self.assertEqual(len(det_loaded.dead_materials), len(det.dead_materials))

            # Verify sampling names and geometry match
            for s1, s2 in zip(det.samplings, det_loaded.samplings):
                self.assertEqual(s1.Name, s2.Name)
                self.assertEqual(s1.sampling, s2.sampling)
                self.assertAlmostEqual(s1.r_min, s2.r_min)
                self.assertAlmostEqual(s1.r_max, s2.r_max)
                self.assertAlmostEqual(s1.delta_eta, s2.delta_eta)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_readout_segments(self):
        """Validates multi-segment readout for EMEC and HEC."""
        samplings = getGalticAllSamplings()
        emec1_layers = [s for s in samplings if "EMEC1" in s.Name]
        self.assertEqual(len(emec1_layers), 2)  # Side A and Side B
        for emec1 in emec1_layers:
            self.assertEqual(len(emec1.readout_segments), 4)
            d_etas = [seg.delta_eta for seg in emec1.readout_segments]
            self.assertEqual(d_etas, [0.00325, 0.025, 0.006, 0.1])
            self.assertEqual([seg.segment for seg in emec1.readout_segments], [0, 1, 2, 3])

        hec1_layers = [s for s in samplings if "HEC1" in s.Name]
        self.assertEqual(len(hec1_layers), 2)
        for hec1 in hec1_layers:
            self.assertEqual(len(hec1.readout_segments), 2)
            d_etas = [seg.delta_eta for seg in hec1.readout_segments]
            self.assertEqual(d_etas, [0.1, 0.2])

    def test_detector_construction_alias(self):
        """Verifies canonical alias DetectorConstruction."""
        det = DetectorConstruction("TestAlias")
        self.assertIsInstance(det, GalticDetectorConstruction)

    def test_detector_construction_compile_and_construct(self):
        """Verifies GalticDetectorConstruction compile() and C++ Geant4 Construct without AddVolume."""
        det = GalticDetectorConstruction("TestCompileConstruct")
        det.compile()
        pv = det._c_ptr.Construct()
        self.assertIsNotNone(pv)
        self.assertEqual(pv.GetName(), "World")
        # Ensure AddVolume was removed from C++ interface
        self.assertFalse(hasattr(det._c_ptr, "AddVolume"))


if __name__ == "__main__":
    unittest.main()
