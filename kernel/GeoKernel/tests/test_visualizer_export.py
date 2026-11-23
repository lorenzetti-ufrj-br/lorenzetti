"""
Unit tests for visualizer VectorPdfExporter, CadReader, and Server.
"""

import os
import sys
import tempfile
import unittest

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
for p in [_ROOT, os.path.join(_ROOT, "geometry"), os.path.join(_ROOT, "kernel/GeoKernel/python"), os.path.join(_ROOT, "geometry/GALTIC/python"), os.path.join(_ROOT, "build/python")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from GALTIC import GalticDetectorConstruction
from visualizer import VectorPdfExporter, CadReader, launch_visualizer
from visualizer.Server import VisualizerHttpHandler


class TestVisualizerExport(unittest.TestCase):
    """Test suite for visualizer PDF generation and CAD inspection."""

    def setUp(self):
        self.det = GalticDetectorConstruction("TestDet")
        self.exporter = VectorPdfExporter(self.det)

    def test_pdf_export_rz(self):
        """Tests vector PDF generation in R-Z projection."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name

        try:
            self.exporter.export_rz(
                pdf_path,
                show_cells=True,
                symmetric=True,
            )
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 500)

            with open(pdf_path, "rb") as f:
                header = f.read(5)
                self.assertEqual(header, b"%PDF-")
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    def test_pdf_export_xy(self):
        """Tests vector PDF generation in X-Y projection."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            pdf_path = tmp.name

        try:
            self.exporter.export_xy(
                pdf_path,
                z_plane=0.0,
                show_cells=True,
            )
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 500)

            with open(pdf_path, "rb") as f:
                header = f.read(5)
                self.assertEqual(header, b"%PDF-")
        finally:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

    def test_cad_reader_fallback(self):
        """Tests CadReader behavior with non-existent or dummy files."""
        reader = CadReader()
        info = reader.inspect("/tmp/nonexistent.gdml")
        self.assertIn("error", info)

    def test_server_handler_metadata(self):
        """Verifies server handler static configuration."""
        self.assertTrue(os.path.isdir(VisualizerHttpHandler.web_dir))


if __name__ == "__main__":
    unittest.main()
