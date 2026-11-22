"""
DetectorConstruction.py - Top-level orchestrator for GALTIC detector geometry.

Implements file-driven JSON geometry saving/loading, Geant4 compilation,
and integration with the visualizer.
"""

from typing import Any, Dict, List, Optional, Set
import json
import os
import ROOT
from prettytable import PrettyTable

from GaugiKernel import Configurable, Logger
from GALTIC.Layer import CaloSamplingLayer, DeadMaterialVolume, Plates
from GALTIC.GalticCfg import getGalticAllSamplings, getGalticAllDeadMaterials

__all__ = ["GalticDetectorConstruction", "DetectorConstruction_v1"]


def _default_geo_file() -> str:
    """Returns the default path to canonical galtic_geometry.json."""
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/galtic_geometry.json")
    )


class GalticDetectorConstruction(Configurable):
    """
    Python orchestrator for the GALTIC calorimeter geometry.
    Supports file-driven JSON geometry, backward-compatible compilation, and 3D visualization.
    """

    def __init__(
        self,
        name: str = "ATLAS",
        UseMagneticField: bool = False,
        CutOnPhi: bool = False,
        GeometryFile: str = "",
        geometry_file: Optional[str] = None,
    ) -> None:
        """
        Initializes GalticDetectorConstruction.

        Args:
            name: Instance name.
            UseMagneticField: Whether to activate magnetic field.
            CutOnPhi: Restrict phi range.
            GeometryFile: C++ property for the JSON geometry file path.
            geometry_file: Optional path to JSON geometry to load directly.
        """
        self.geometry_file = geometry_file or GeometryFile or _default_geo_file()

        super().__init__(
            ROOT.DetectorConstruction_v1,
            name,
            UseMagneticField=UseMagneticField,
            CutOnPhi=CutOnPhi,
            GeometryFile=self.geometry_file if os.path.isfile(self.geometry_file) else "",
        )

        self.samplings: List[CaloSamplingLayer] = []
        self.dead_materials: List[DeadMaterialVolume] = []

        if self.geometry_file and os.path.isfile(self.geometry_file):
            self.load(self.geometry_file)
        else:
            self.samplings.extend(getGalticAllSamplings())
            self.dead_materials.extend(getGalticAllDeadMaterials())

    @property
    def layers(self) -> List[CaloSamplingLayer]:
        """Returns the list of active sampling layers."""
        return self.samplings

    def add_layer(self, layer: CaloSamplingLayer) -> None:
        """Adds an active calorimeter sampling layer."""
        self.samplings.append(layer)

    def add_dead_material(self, dm: DeadMaterialVolume) -> None:
        """Adds a passive dead material volume."""
        self.dead_materials.append(dm)

    def to_dict(self) -> Dict[str, Any]:
        """Returns geometry data serialized as a dictionary."""
        data: Dict[str, Any] = {
            "metadata": {
                "version": "2.0",
                "detector": "GALTIC",
                "description": "General Argon Liquid and Tile Integrated Calorimeter canonical specification",
            },
            "volumes": [],
        }

        seen_names: Set[str] = set()

        for layer in self.samplings:
            if layer.Name not in seen_names:
                seen_names.add(layer.Name)
                data["volumes"].append(layer.to_dict())

        for dm in self.dead_materials:
            if dm.Name not in seen_names:
                seen_names.add(dm.Name)
                data["volumes"].append(dm.to_dict())

        return data

    def save(self, filepath: str) -> None:
        """
        Exports the entire detector definition to a JSON file.

        Args:
            filepath: Target file path.
        """
        data = self.to_dict()
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str) -> None:
        """
        Loads the geometry from a JSON file into Python.

        Args:
            filepath: Path to JSON geometry file.
        """
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.samplings.clear()
        self.dead_materials.clear()
        self.geometry_file = filepath

        for item in data.get("volumes", []):
            if "readout" in item and item["readout"] is not None:
                self.samplings.append(CaloSamplingLayer.from_dict(item))
            else:
                self.dead_materials.append(DeadMaterialVolume.from_dict(item))

    def compile(self) -> None:
        """
        Prepares the C++ detector construction.
        If a geometry file is available, configures C++ to read it directly.
        Also populates C++ volumes via AddVolume for full backward compatibility.
        """
        if self.geometry_file and os.path.isfile(self.geometry_file):
            self._c_ptr.setProperty("GeometryFile", self.geometry_file)

        all_elements = [samp.volume() for samp in self.samplings]
        all_elements.extend(self.dead_materials)

        unique_dict: Dict[int, Any] = {}
        for vol in all_elements:
            unique_dict.setdefault(id(vol), vol)
        unique_volumes = list(unique_dict.values())

        for pv in unique_volumes:
            self._c_ptr.AddVolume(
                pv.Name,
                int(pv.Plates),
                pv.AbsorberMaterial,
                pv.GapMaterial,
                int(pv.NofLayers),
                float(pv.AbsorberThickness),
                float(pv.GapThickness),
                float(pv.RMin),
                float(pv.RMax),
                float(pv.ZSize),
                float(pv.X),
                float(pv.Y),
                float(pv.Z),
                float(pv.Cuts.ElectronCut),
                float(pv.Cuts.PositronCut),
                float(pv.Cuts.GammaCut),
                float(pv.Cuts.PhotonCut),
            )

    def view(self, port: int = 8080) -> None:
        """Launches the interactive 3D WebGL detector visualizer in browser."""
        from visualizer import launch_visualizer
        if not os.path.isfile(self.geometry_file):
            self.save(self.geometry_file)
        launch_visualizer(self.geometry_file, port=port)

    def export_vector_pdf(self, output_filepath: str, view: str = "rz") -> None:
        """Generates a 100% mathematically vectorized PDF technical drawing."""
        from visualizer import export_vector_pdf
        if not os.path.isfile(self.geometry_file):
            self.save(self.geometry_file)
        export_vector_pdf(self.geometry_file, output_filepath, view=view)

    def summary(self) -> None:
        """Displays summary tables of calorimeter layers and passive volumes."""
        table = PrettyTable()
        table.field_names = ["Sampling", "Detector", "Rmin (mm)", "Rmax (mm)", "Z_size (mm)", "dEta x dPhi", "Noise (MeV)"]
        for s in self.samplings:
            table.add_row([
                s.Name,
                s.Detector.name,
                f"{s.RMin:.1f}",
                f"{s.RMax:.1f}",
                f"{s.ZSize:.1f}",
                f"{s.DeltaEta:.3f} x {s.DeltaPhi:.3f}",
                f"{s.Noise:.1f}",
            ])
        print("\n=== GALTIC Calorimeter Samplings ===")
        print(table)


# Backward-compatible alias
DetectorConstruction_v1 = GalticDetectorConstruction
