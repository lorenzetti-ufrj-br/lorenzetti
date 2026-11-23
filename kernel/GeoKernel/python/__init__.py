"""
GeoKernel - Central geometry kernel and foundational primitives for Lorenzetti.

Provides:
  - Primitives: Plates, ProductionCuts, ReadoutSegment, CaloSamplingLayer, DeadMaterialVolume
  - Factory: DetectorConstructionCfg, DetectorFlags, get_available_detectors, get_data_dir
  - Visualizer: VectorPdfExporter, CadReader, launch_visualizer, export_vector_pdf
"""

from GeoKernel.Layer import (
    Plates,
    ProductionCuts,
    ReadoutSegment,
    CaloSamplingLayer,
    DeadMaterialVolume,
)
from GeoKernel.DetectorFlags import DetectorFlags
from GeoKernel.DetectorConstructionCfg import (
    DetectorConstructionCfg,
    get_available_detectors,
    get_data_dir,
)
from GeoKernel.visualizer import (
    launch_visualizer,
    VectorPdfExporter,
    export_vector_pdf,
    CadReader,
)

__all__ = [
    "Plates",
    "ProductionCuts",
    "ReadoutSegment",
    "CaloSamplingLayer",
    "DeadMaterialVolume",
    "DetectorFlags",
    "DetectorConstructionCfg",
    "get_available_detectors",
    "get_data_dir",
    "launch_visualizer",
    "VectorPdfExporter",
    "export_vector_pdf",
    "CadReader",
]
