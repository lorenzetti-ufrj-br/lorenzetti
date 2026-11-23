"""
test_geo_kernel.py - Unit test suite for GeoKernel primitives, factory, and visualizer.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
for p in [_ROOT, os.path.join(_ROOT, "kernel/GeoKernel/python"), os.path.join(_ROOT, "geometry"), os.path.join(_ROOT, "build/python")]:
    if p not in sys.path:
        sys.path.insert(0, p)

if "ROOT" not in sys.modules:
    try:
        import ROOT
    except ImportError:
        sys.modules["ROOT"] = MagicMock()

from CaloCell.CaloDefs import CaloSampling, Detector
from GeoKernel import (
    Plates,
    ProductionCuts,
    ReadoutSegment,
    CaloSamplingLayer,
    DeadMaterialVolume,
    DetectorFlags,
    DetectorConstructionCfg,
    get_available_detectors,
    get_data_dir,
    VectorPdfExporter,
    CadReader,
)

try:
    from GALTIC import GalticDetectorConstruction
except ImportError:
    GalticDetectorConstruction = None


class TestGeoKernelPrimitives(unittest.TestCase):
    """Tests GeoKernel core data structures."""

    def test_plates_enum(self):
        self.assertEqual(int(Plates.Horizontal), 0)
        self.assertEqual(int(Plates.Vertical), 1)
        self.assertEqual(int(Plates.Polycone), 2)

    def test_production_cuts_serialization(self):
        cuts = ProductionCuts(ElectronCut=0.7, PositronCut=0.7, GammaCut=0.5, PhotonCut=0.5)
        d = cuts.to_dict()
        self.assertEqual(d["electron_cut"], 0.7)
        self.assertEqual(d["gamma_cut"], 0.5)

        restored = ProductionCuts.from_dict(d)
        self.assertEqual(restored.ElectronCut, 0.7)
        self.assertEqual(restored.GammaCut, 0.5)

    def test_readout_segment_serialization(self):
        seg = ReadoutSegment(
            segment=1,
            collection_key="Collection_EMEC1_1A",
            delta_eta=0.025,
            delta_phi=0.025,
            eta_min=1.80,
            eta_max=2.00,
            noise_sigma=26.0,
            shaper_file="pulseLar.dat",
            phi_shift=0.0,
        )
        d = seg.to_dict()
        self.assertEqual(d["segment"], 1)
        self.assertEqual(d["eta_min"], 1.80)
        self.assertEqual(d["eta_max"], 2.00)

        restored = ReadoutSegment.from_dict(d)
        self.assertEqual(restored.Segment, 1)
        self.assertEqual(restored.EtaMin, 1.80)
        self.assertEqual(restored.EtaMax, 2.00)
        self.assertEqual(restored.Noise, 26.0)

    def test_calo_sampling_layer_serialization(self):
        layer = CaloSamplingLayer(
            name="TestLayer",
            collection_key="Collection_Test",
            sampling=CaloSampling.EMB1,
            detector=Detector.TTEM,
            rmin=1500.0,
            rmax=1596.0,
            z_size=6330.0,
            nof_layers=16,
            absorber_thickness=1.51,
            gap_thickness=4.49,
            absorber_material="G4_Pb",
            gap_material="liquidArgon",
            plates=Plates.Horizontal,
            delta_eta=0.003125,
            delta_phi=0.02454,
            noise_sigma=40.0,
            shaper_file="pulseLar.dat",
        )
        d = layer.to_dict()
        self.assertEqual(d["name"], "TestLayer")
        self.assertEqual(d["sampling"], int(CaloSampling.EMB1))
        self.assertEqual(d["geometry"]["r_min"], 1500.0)

        restored = CaloSamplingLayer.from_dict(d)
        self.assertEqual(restored.Name, "TestLayer")
        self.assertEqual(restored.Sampling, int(CaloSampling.EMB1))
        self.assertEqual(restored.r_min, 1500.0)
        self.assertEqual(restored.r_max, 1596.0)
        self.assertEqual(len(restored.readout_segments), 1)

    def test_dead_material_volume_serialization(self):
        dm = DeadMaterialVolume(
            name="DM::Cryo::Inner",
            material="G4_Al",
            rmin=1150.0,
            rmax=1160.0,
            z_size=5800.0,
            in_solenoid_field=True,
        )
        d = dm.to_dict()
        self.assertEqual(d["name"], "DM::Cryo::Inner")
        self.assertTrue(d["in_solenoid_field"])

        restored = DeadMaterialVolume.from_dict(d)
        self.assertEqual(restored.Name, "DM::Cryo::Inner")
        self.assertEqual(restored.r_min, 1150.0)
        self.assertTrue(restored.InSolenoidField)

    def test_detector_factory_and_flags(self):
        DetectorFlags.reset()
        self.assertEqual(DetectorFlags.Version, "GALTIC")
        detectors = get_available_detectors()
        self.assertIn("GALTIC", detectors)
        self.assertIn("ATLAS", detectors)

    def test_detector_flags_defaults(self):
        """Verifies DetectorFlags default values and reset."""
        self.assertEqual(DetectorFlags.Version, "GALTIC")
        DetectorFlags.Version = "ATLAS"
        self.assertEqual(DetectorFlags.Version, "ATLAS")
        DetectorFlags.reset()
        self.assertEqual(DetectorFlags.Version, "GALTIC")

    def test_construct_galtic_by_version(self):
        """Constructs GALTIC via version='GALTIC'."""
        if GalticDetectorConstruction is not None:
            det = DetectorConstructionCfg("TestGaltic", version="GALTIC")
            self.assertIsInstance(det, GalticDetectorConstruction)

    def test_v1_v2_rejected(self):
        """Verifies that legacy 'v1' and 'v2' versions are rejected."""
        with self.assertRaises(ValueError):
            DetectorConstructionCfg("TestV1", version="v1")
        with self.assertRaises(ValueError):
            DetectorConstructionCfg("TestV2", version="v2")

    def test_construct_galtic_by_detector_param(self):
        """Constructs GALTIC via detector='GALTIC'."""
        if GalticDetectorConstruction is not None:
            det = DetectorConstructionCfg("TestParam", detector="GALTIC")
            self.assertIsInstance(det, GalticDetectorConstruction)

    def test_construct_atlas_v1(self):
        """Constructs ATLAS via atlas_version='v1'."""
        try:
            import ATLAS.v1
            det = DetectorConstructionCfg("TestAtlasV1", detector="ATLAS", atlas_version="v1")
            self.assertIsInstance(det, ATLAS.v1.DetectorConstruction)
        except ImportError:
            pass

    def test_construct_atlas_v2(self):
        """Constructs ATLAS via atlas_version='v2'."""
        try:
            import ATLAS.v2
            det = DetectorConstructionCfg("TestAtlasV2", detector="ATLAS", atlas_version="v2")
            self.assertIsInstance(det, ATLAS.v2.DetectorConstruction)
        except ImportError:
            pass

    def test_data_dir(self):
        d = get_data_dir()
        self.assertTrue(os.path.isdir(d))
        self.assertTrue(os.path.exists(os.path.join(d, "pulseLar.dat")))
        self.assertTrue(os.path.exists(os.path.join(d, "pulseTile.dat")))


if __name__ == "__main__":
    unittest.main()
