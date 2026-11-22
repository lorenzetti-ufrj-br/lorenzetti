"""
Layer.py - Core data classes and fluent builders for GALTIC.

Consolidates active calorimeter sampling layers, dead material volumes, and all builders.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from enum import IntEnum
import os
import numpy as np
from CaloCell.CaloDefs import Detector, CaloSampling
from GaugiKernel import Logger

__all__ = [
    "Plates",
    "ProductionCuts",
    "CaloSamplingLayer",
    "DeadMaterialVolume",
    "LArBarrelBuilder",
    "TileCalBuilder",
    "LArEMECBuilder",
    "HECBuilder",
    "DeadMaterialBuilder",
]


class Plates(IntEnum):
    """Plate geometry orientation enum."""
    Horizontal = 0
    Vertical = 1
    Polycone = 2


class ProductionCuts:
    """Production cuts for Geant4 particle generation."""

    def __init__(
        self,
        ElectronCut: float = 1.0,
        PositronCut: float = 1.0,
        GammaCut: float = 1.0,
        PhotonCut: float = 1.0,
    ) -> None:
        """Initializes Geant4 particle production cuts in mm."""
        self.ElectronCut = float(ElectronCut)
        self.PositronCut = float(PositronCut)
        self.GammaCut = float(GammaCut)
        self.PhotonCut = float(PhotonCut)


class CaloSamplingLayer(Logger):
    """
    Unified representation of an active calorimeter sampling layer.
    Combines physical dimensions, absorber/gap materials, cell readout granularity, and pulse shaping.
    """

    def __init__(
        self,
        name: str,
        collection_key: str,
        sampling: CaloSampling,
        detector: Detector,
        rmin: float,
        rmax: float,
        z_size: float,
        nof_layers: int,
        absorber_thickness: float,
        gap_thickness: float,
        absorber_material: str = "G4_Pb",
        gap_material: str = "liquidArgon",
        plates: Plates = Plates.Horizontal,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: str = "cyan",
        delta_eta: float = 0.025,
        delta_phi: float = np.pi / 32.0,
        phi_shift: float = 0.0,
        segment: int = 0,
        noise_sigma: float = 0.0,
        shaper_file: str = "",
        n_samples: int = 5,
        bunch_id_start: int = -21,
        bunch_id_end: int = 3,
        start_sampling_bc: int = -2,
        of_weights_energy: Optional[List[float]] = None,
        of_weights_time: Optional[List[float]] = None,
        electron_cut: float = 1.0,
        positron_cut: float = 1.0,
        gamma_cut: float = 1.0,
        proton_cut: float = 1.0,
    ) -> None:
        """Initializes an active calorimeter sampling layer with explicit arguments."""
        super().__init__()
        self.Name = str(name)
        self.CollectionKey = str(collection_key)
        self.Sampling = sampling
        self.Detector = detector
        self.RMin = float(rmin)
        self.RMax = float(rmax)
        self.ZSize = float(z_size)
        self.NofLayers = int(nof_layers)
        self.AbsorberThickness = float(absorber_thickness)
        self.GapThickness = float(gap_thickness)
        self.AbsorberMaterial = str(absorber_material)
        self.GapMaterial = str(gap_material)
        self.Plates = plates
        self.X, self.Y, self.Z = [float(c) for c in center]
        self.Color = str(color)
        self.DeltaEta = float(delta_eta)
        self.DeltaPhi = float(delta_phi)
        self.PhiShift = float(phi_shift)
        self.Segment = int(segment)
        self.Noise = float(noise_sigma)
        self.PulseFile = str(shaper_file)
        self.NSamples = int(n_samples)
        self.BunchIdStart = int(bunch_id_start)
        self.BunchIdEnd = int(bunch_id_end)
        self.StartSamplingBc = int(start_sampling_bc)
        self.OfWeightsEnergy = of_weights_energy or []
        self.OfWeightsTime = of_weights_time or []
        self.Cuts = ProductionCuts(
            ElectronCut=electron_cut, PositronCut=positron_cut, GammaCut=gamma_cut, PhotonCut=proton_cut
        )
        self.Visualization = True

    # Readout / Reconstruction Interface Properties
    @property
    def Samples(self) -> int:
        return self.NSamples

    @property
    def Shaper(self) -> str:
        return self.PulseFile

    @property
    def StartSamplingBC(self) -> int:
        return self.StartSamplingBc

    @property
    def sampling(self) -> int:
        return int(self.Sampling)

    @property
    def r_min(self) -> float:
        return self.RMin

    @property
    def r_max(self) -> float:
        return self.RMax

    @property
    def z_size(self) -> float:
        return self.ZSize

    @property
    def delta_eta(self) -> float:
        return self.DeltaEta

    @property
    def delta_phi(self) -> float:
        return self.DeltaPhi

    @property
    def plates(self) -> Plates:
        return self.Plates

    def name(self) -> str:
        """Returns volume name formatted for Geant4."""
        return self.Name.replace("::", "_")

    def volume(self) -> "CaloSamplingLayer":
        """Returns self as the volume provider."""
        return self

    def sensitive(self) -> "CaloSamplingLayer":
        """Returns self as the sensitive detector provider."""
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the layer into the canonical GALTIC JSON format."""
        return {
            "name": self.Name,
            "plates": "Vertical" if self.Plates == Plates.Vertical else "Horizontal",
            "materials": {
                "absorber": self.AbsorberMaterial,
                "gap": self.GapMaterial,
            },
            "geometry": {
                "nof_layers": self.NofLayers,
                "absorber_thickness": self.AbsorberThickness,
                "gap_thickness": self.GapThickness,
                "rmin": self.RMin,
                "rmax": self.RMax,
                "z_size": self.ZSize,
                "center": [self.X, self.Y, self.Z],
            },
            "readout": {
                "detector": str(int(self.Detector)),
                "sampling": str(int(self.Sampling)),
                "collection_key": self.CollectionKey,
                "delta_eta": self.DeltaEta,
                "delta_phi": self.DeltaPhi,
                "phi_shift": self.PhiShift,
                "segment": self.Segment,
                "noise": self.Noise,
                "shaper": self.PulseFile,
                "n_samples": self.NSamples,
                "bunch_id_start": self.BunchIdStart,
                "bunch_id_end": self.BunchIdEnd,
                "start_sampling_bc": self.StartSamplingBc,
                "of_weights_energy": self.OfWeightsEnergy,
                "of_weights_time": self.OfWeightsTime,
            },
            "cuts": {
                "electron": self.Cuts.ElectronCut,
                "positron": self.Cuts.PositronCut,
                "gamma": self.Cuts.GammaCut,
                "proton": self.Cuts.PhotonCut,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaloSamplingLayer":
        """Reconstructs a CaloSamplingLayer from a dictionary."""
        geom = data["geometry"]
        readout = data["readout"]
        mats = data["materials"]
        cuts = data.get("cuts", {})
        plates = Plates.Vertical if data.get("plates") == "Vertical" else Plates.Horizontal

        return cls(
            name=data["name"],
            collection_key=readout["collection_key"],
            sampling=int(readout["sampling"]),
            detector=int(readout["detector"]),
            rmin=geom["rmin"],
            rmax=geom["rmax"],
            z_size=geom["z_size"],
            nof_layers=geom["nof_layers"],
            absorber_thickness=geom["absorber_thickness"],
            gap_thickness=geom["gap_thickness"],
            absorber_material=mats["absorber"],
            gap_material=mats["gap"],
            plates=plates,
            center=tuple(geom.get("center", [0.0, 0.0, 0.0])),
            delta_eta=readout.get("delta_eta", 0.025),
            delta_phi=readout.get("delta_phi", np.pi / 32.0),
            phi_shift=readout.get("phi_shift", 0.0),
            segment=readout.get("segment", 0),
            noise_sigma=readout.get("noise", 0.0),
            shaper_file=readout.get("shaper", ""),
            n_samples=readout.get("n_samples", 5),
            bunch_id_start=readout.get("bunch_id_start", -21),
            bunch_id_end=readout.get("bunch_id_end", 3),
            start_sampling_bc=readout.get("start_sampling_bc", -2),
            of_weights_energy=readout.get("of_weights_energy", []),
            of_weights_time=readout.get("of_weights_time", []),
            electron_cut=cuts.get("electron", 1.0),
            positron_cut=cuts.get("positron", 1.0),
            gamma_cut=cuts.get("gamma", 1.0),
            proton_cut=cuts.get("proton", 1.0),
        )


class DeadMaterialVolume(Logger):
    """Unified representation of a passive absorber or support volume."""

    def __init__(
        self,
        name: str,
        plates: Plates,
        nof_layers: int,
        absorber_thickness: float,
        gap_thickness: float,
        rmin: float,
        rmax: float,
        z_size: float,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        absorber_material: str = "G4_Al",
        gap_material: str = "Vacuum",
        color: str = "gray",
        electron_cut: float = 1.0,
        positron_cut: float = 1.0,
        gamma_cut: float = 1.0,
        proton_cut: float = 1.0,
    ) -> None:
        """Initializes a passive dead material volume."""
        super().__init__()
        self.Name = str(name)
        self.Plates = plates
        self.NofLayers = int(nof_layers)
        self.AbsorberThickness = float(absorber_thickness)
        self.GapThickness = float(gap_thickness)
        self.RMin = float(rmin)
        self.RMax = float(rmax)
        self.ZSize = float(z_size)
        self.X, self.Y, self.Z = [float(c) for c in center]
        self.AbsorberMaterial = str(absorber_material)
        self.GapMaterial = str(gap_material)
        self.Color = str(color)
        self.Visualization = True
        self.Cuts = ProductionCuts(
            ElectronCut=electron_cut, PositronCut=positron_cut, GammaCut=gamma_cut, PhotonCut=proton_cut
        )

    def name(self) -> str:
        """Returns volume name formatted."""
        return self.Name.replace("::", "_")

    def volume(self) -> "DeadMaterialVolume":
        """Returns self as the volume provider."""
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the passive volume to dictionary."""
        return {
            "name": self.Name,
            "plates": "Vertical" if self.Plates == Plates.Vertical else "Horizontal",
            "materials": {
                "absorber": self.AbsorberMaterial,
                "gap": self.GapMaterial,
            },
            "geometry": {
                "nof_layers": self.NofLayers,
                "absorber_thickness": self.AbsorberThickness,
                "gap_thickness": self.GapThickness,
                "rmin": self.RMin,
                "rmax": self.RMax,
                "z_size": self.ZSize,
                "center": [self.X, self.Y, self.Z],
            },
            "cuts": {
                "electron": self.Cuts.ElectronCut,
                "positron": self.Cuts.PositronCut,
                "gamma": self.Cuts.GammaCut,
                "proton": self.Cuts.PhotonCut,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeadMaterialVolume":
        """Deserializes a DeadMaterialVolume from a dictionary."""
        geom = data["geometry"]
        cuts = data.get("cuts", {})
        plates = Plates.Vertical if data.get("plates") == "Vertical" else Plates.Horizontal

        return cls(
            name=data["name"],
            plates=plates,
            nof_layers=geom["nof_layers"],
            absorber_thickness=geom["absorber_thickness"],
            gap_thickness=geom["gap_thickness"],
            rmin=geom["rmin"],
            rmax=geom["rmax"],
            z_size=geom["z_size"],
            center=tuple(geom.get("center", [0.0, 0.0, 0.0])),
            absorber_material=data["materials"]["absorber"],
            gap_material=data["materials"]["gap"],
            electron_cut=cuts.get("electron", 1.0),
            positron_cut=cuts.get("positron", 1.0),
            gamma_cut=cuts.get("gamma", 1.0),
            proton_cut=cuts.get("proton", 1.0),
        )


# ==============================================================================
# Fluent Subdetector Builders
# ==============================================================================

class LArBarrelBuilder:
    """Fluent builder for LAr Electromagnetic Barrel (EMB) sampling layers."""

    def __init__(self, name: str, sampling: CaloSampling) -> None:
        self._name = name
        self._sampling = sampling
        self._rmin, self._rmax, self._z_size = 1500.0, 1900.0, 6800.0
        self._nof_layers, self._absorber_th, self._gap_th = 16, 1.53, 4.5
        self._absorber_mat, self._gap_mat = "G4_Pb", "liquidArgon"
        self._delta_eta, self._delta_phi, self._phi_shift = 0.025, np.pi / 32.0, -np.pi / 1024.0
        self._noise, self._pulse_file = 0.0, ""

    def radii(self, rmin: float, rmax: float) -> "LArBarrelBuilder":
        self._rmin, self._rmax = float(rmin), float(rmax)
        return self

    def z_length(self, z_size: float) -> "LArBarrelBuilder":
        self._z_size = float(z_size)
        return self

    def segmentation(self, nof_layers: int, absorber_th: float, gap_th: float) -> "LArBarrelBuilder":
        self._nof_layers, self._absorber_th, self._gap_th = int(nof_layers), float(absorber_th), float(gap_th)
        return self

    def granularity(self, delta_eta: float, delta_phi: float, phi_shift: float = -np.pi / 1024.0) -> "LArBarrelBuilder":
        self._delta_eta, self._delta_phi, self._phi_shift = float(delta_eta), float(delta_phi), float(phi_shift)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "LArBarrelBuilder":
        self._noise, self._pulse_file = float(noise_mev), str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        samp_name = self._name.split("::")[-1]
        return CaloSamplingLayer(
            name=self._name,
            collection_key=f"Collection_{samp_name}",
            sampling=self._sampling,
            detector=Detector.TTEM,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=self._z_size,
            nof_layers=self._nof_layers,
            absorber_thickness=self._absorber_th,
            gap_thickness=self._gap_th,
            absorber_material=self._absorber_mat,
            gap_material=self._gap_mat,
            plates=Plates.Horizontal,
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            phi_shift=self._phi_shift,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
        )


class TileCalBuilder:
    """Fluent builder for TileCal Scintillator Calorimeter sampling layers."""

    def __init__(self, name: str, sampling: CaloSampling) -> None:
        self._name = name
        self._sampling = sampling
        self._rmin, self._rmax, self._z_size = 2280.0, 3800.0, 5600.0
        self._center = (0.0, 0.0, 0.0)
        self._delta_eta, self._delta_phi = 0.1, 0.1
        self._noise, self._pulse_file = 30.0, ""

    def radii(self, rmin: float, rmax: float) -> "TileCalBuilder":
        self._rmin, self._rmax = float(rmin), float(rmax)
        return self

    def length_and_center(self, z_size: float, z_center: float = 0.0) -> "TileCalBuilder":
        self._z_size, self._center = float(z_size), (0.0, 0.0, float(z_center))
        return self

    def granularity(self, delta_eta: float, delta_phi: float) -> "TileCalBuilder":
        self._delta_eta, self._delta_phi = float(delta_eta), float(delta_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "TileCalBuilder":
        self._noise, self._pulse_file = float(noise_mev), str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        samp_name = self._name.split("::")[-1]
        return CaloSamplingLayer(
            name=self._name,
            collection_key=f"Collection_{samp_name}",
            sampling=self._sampling,
            detector=Detector.TILE,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=self._z_size,
            nof_layers=1,
            absorber_thickness=14.0,
            gap_thickness=3.0,
            absorber_material="G4_Fe",
            gap_material="PLASTIC SCINTILLATOR",
            plates=Plates.Horizontal,
            center=self._center,
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
        )


class LArEMECBuilder:
    """Fluent builder for LAr Electromagnetic Endcap (EMEC) sampling layers."""

    def __init__(self, name: str, sampling: CaloSampling, side_a: bool = True) -> None:
        self._name, self._sampling, self._side_a = name, sampling, side_a
        self._rmin, self._rmax, self._z_size = 302.0, 2042.0, 500.0
        self._z_center = 3900.0 if side_a else -3900.0
        self._delta_eta, self._delta_phi = 0.025, np.pi / 32.0
        self._noise, self._pulse_file = 50.0, ""

    def geometry(self, rmin: float, rmax: float, z_size: float, z_center: float) -> "LArEMECBuilder":
        self._rmin, self._rmax, self._z_size = float(rmin), float(rmax), float(z_size)
        self._z_center = float(z_center) if self._side_a else -abs(float(z_center))
        return self

    def granularity(self, delta_eta: float, delta_phi: float) -> "LArEMECBuilder":
        self._delta_eta, self._delta_phi = float(delta_eta), float(delta_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "LArEMECBuilder":
        self._noise, self._pulse_file = float(noise_mev), str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        samp_name = self._name.split("::")[-1]
        side_tag = "A" if self._side_a else "B"
        return CaloSamplingLayer(
            name=f"{self._name}::{side_tag}",
            collection_key=f"Collection_{samp_name}_{side_tag}",
            sampling=self._sampling,
            detector=Detector.TTEM,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=self._z_size,
            nof_layers=1,
            absorber_thickness=1.75,
            gap_thickness=4.5,
            absorber_material="G4_Pb",
            gap_material="liquidArgon",
            plates=Plates.Vertical,
            center=(0.0, 0.0, self._z_center),
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
        )


class HECBuilder:
    """Fluent builder for Hadronic Endcap (HEC) sampling layers."""

    def __init__(self, name: str, sampling: CaloSampling, side_a: bool = True) -> None:
        self._name, self._sampling, self._side_a = name, sampling, side_a
        self._rmin, self._rmax, self._z_size = 372.0, 2030.0, 400.0
        self._z_center = 4500.0 if side_a else -4500.0
        self._delta_eta, self._delta_phi = 0.1, 0.1
        self._noise, self._pulse_file = 100.0, ""

    def geometry(self, rmin: float, rmax: float, z_size: float, z_center: float) -> "HECBuilder":
        self._rmin, self._rmax, self._z_size = float(rmin), float(rmax), float(z_size)
        self._z_center = float(z_center) if self._side_a else -abs(float(z_center))
        return self

    def granularity(self, delta_eta: float, delta_phi: float) -> "HECBuilder":
        self._delta_eta, self._delta_phi = float(delta_eta), float(delta_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "HECBuilder":
        self._noise, self._pulse_file = float(noise_mev), str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        samp_name = self._name.split("::")[-1]
        side_tag = "A" if self._side_a else "B"
        return CaloSamplingLayer(
            name=f"{self._name}::{side_tag}",
            collection_key=f"Collection_{samp_name}_{side_tag}",
            sampling=self._sampling,
            detector=Detector.TILE,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=self._z_size,
            nof_layers=1,
            absorber_thickness=25.0,
            gap_thickness=8.5,
            absorber_material="G4_Cu",
            gap_material="liquidArgon",
            plates=Plates.Vertical,
            center=(0.0, 0.0, self._z_center),
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
        )


class DeadMaterialBuilder:
    """Fluent builder for passive dead material volumes."""

    def __init__(self, name: str) -> None:
        self._name = name
        self._rmin, self._rmax, self._z_size = 1000.0, 1100.0, 6000.0
        self._center = (0.0, 0.0, 0.0)
        self._absorber_mat, self._gap_mat = "G4_Al", "Vacuum"
        self._plates = Plates.Horizontal

    def geometry(self, rmin: float, rmax: float, z_size: float, center: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> "DeadMaterialBuilder":
        self._rmin, self._rmax, self._z_size, self._center = float(rmin), float(rmax), float(z_size), center
        return self

    def materials(self, absorber: str, gap: str = "Vacuum", plates: Plates = Plates.Horizontal) -> "DeadMaterialBuilder":
        self._absorber_mat, self._gap_mat, self._plates = str(absorber), str(gap), plates
        return self

    def build(self) -> DeadMaterialVolume:
        """Builds a DeadMaterialVolume with appropriate absorber thickness."""
        thickness = (
            self._z_size
            if self._plates == Plates.Vertical
            else (self._rmax - self._rmin)
        )
        return DeadMaterialVolume(
            name=self._name,
            plates=self._plates,
            nof_layers=1,
            absorber_thickness=thickness,
            gap_thickness=0.0,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=self._z_size,
            center=self._center,
            absorber_material=self._absorber_mat,
            gap_material=self._gap_mat,
        )
