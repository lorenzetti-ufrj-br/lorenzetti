"""
test_atlas_json.py - Unit tests for ATLAS v2 geometry builders, JSON serialization, and C++ construction.
"""

import os
import sys
import tempfile
import unittest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
for p in [_ROOT, os.path.join(_ROOT, "geometry"), os.path.join(_ROOT, "geometry/ATLAS/python"), os.path.join(_ROOT, "build/python")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from CaloCell.CaloDefs import CaloSampling
from ATLAS.v2 import (
    AtlasDetectorConstruction,
    DetectorConstruction,
    CaloSamplingLayer,
    DeadMaterialVolume,
    Plates,
    AtlasEmbBuilder,
    AtlasTileBuilder,
    AtlasEmecBuilder,
    AtlasHecBuilder,
    AtlasFcalBuilder,
    AtlasDeadMaterialBuilder,
    getAtlasAllSamplings,
    getAtlasAllDeadMaterials,
)


class TestAtlasV2Geometry(unittest.TestCase):
    """Test suite for ATLAS v2 parametric geometry components and C++ engine."""

    def test_layer_builders(self):
        """Tests individual fluent layer builders."""
        emb = (
            AtlasEmbBuilder("LAr::EMB1", CaloSampling.EMB1)
            .radii(1500.0, 1580.0)
            .z_length(6330.0)
            .accordion(lead_th=1.53, lar_gap=4.5, n_layers=16)
            .granularity(d_eta=0.003125, d_phi=0.02454)
            .electronics(noise_mev=40.0, pulse_file="pulseLar.dat")
            .build()
        )
        self.assertEqual(emb.sampling, int(CaloSampling.EMB1))
        self.assertEqual(emb.Name, "LAr::EMB1")
        self.assertEqual(emb.r_min, 1500.0)
        self.assertEqual(emb.r_max, 1580.0)
        self.assertEqual(emb.delta_eta, 0.003125)
        self.assertEqual(emb.plates, Plates.Horizontal)

        tile = (
            AtlasTileBuilder("Tile::Bar0", CaloSampling.TileCal1)
            .radii(2280.0, 2600.0)
            .z_span(-2820.0, 2820.0)
            .cells(d_eta=0.1, d_phi=0.1)
            .electronics(noise_mev=30.0, pulse_file="pulseTile.dat")
            .build()
        )
        self.assertEqual(tile.sampling, int(CaloSampling.TileCal1))
        self.assertEqual(tile.Name, "Tile::Bar0")
        self.assertEqual(tile.plates, Plates.Vertical)

    def test_all_samplings_registry(self):
        """Validates all sampling layers and dead materials defined in AtlasCfg."""
        samplings = getAtlasAllSamplings()
        self.assertGreaterEqual(len(samplings), 24)
        dead_materials = getAtlasAllDeadMaterials()
        self.assertGreaterEqual(len(dead_materials), 5)

        # Check key samplings
        sampling_ids = [s.sampling for s in samplings]
        self.assertIn(int(CaloSampling.PSB), sampling_ids)
        self.assertIn(int(CaloSampling.EMB1), sampling_ids)
        self.assertIn(int(CaloSampling.TileCal1), sampling_ids)
        self.assertIn(int(CaloSampling.EMEC1), sampling_ids)
        self.assertIn(int(CaloSampling.HEC0), sampling_ids)
        self.assertIn(int(CaloSampling.FCAL1), sampling_ids)

    def test_detector_construction_json_roundtrip(self):
        """Tests full AtlasDetectorConstruction save and load to JSON."""
        det = AtlasDetectorConstruction("TestAtlasV2")
        self.assertGreater(len(det.samplings), 20)
        self.assertGreater(len(det.dead_materials), 0)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            det.save(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 1000)

            det_loaded = AtlasDetectorConstruction("LoadedAtlas", geometry_file=tmp_path)
            self.assertEqual(len(det_loaded.samplings), len(det.samplings))
            self.assertEqual(len(det_loaded.dead_materials), len(det.dead_materials))

            for s1, s2 in zip(det.samplings, det_loaded.samplings):
                self.assertEqual(s1.Name, s2.Name)
                self.assertEqual(s1.sampling, s2.sampling)
                self.assertAlmostEqual(s1.r_min, s2.r_min)
                self.assertAlmostEqual(s1.r_max, s2.r_max)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_detector_construction_compile_and_construct(self):
        """Verifies AtlasDetectorConstruction compile() and C++ Geant4 Construct."""
        det = AtlasDetectorConstruction("TestAtlasConstruct")
        det.compile()
        pv = det._c_ptr.Construct()
        self.assertIsNotNone(pv)
        self.assertEqual(pv.GetName(), "World")


if __name__ == "__main__":
    unittest.main()
