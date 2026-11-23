"""
Layer.py - Core data classes and fluent builders for ATLAS v2.

Consolidates active calorimeter sampling layers, dead material volumes, and all ATLAS builders.
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
    "ReadoutSegment",
    "CaloSamplingLayer",
    "DeadMaterialVolume",
    "AtlasEmbBuilder",
    "AtlasTileBuilder",
    "AtlasEmecBuilder",
    "AtlasHecBuilder",
    "AtlasFcalBuilder",
    "AtlasDeadMaterialBuilder",
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


class ReadoutSegment:
    """Represents a readout ring or angular segment within a calorimeter sampling."""

    def __init__(
        self,
        segment: int,
        collection_key: str,
        delta_eta: float,
        delta_phi: float,
        eta_min: Optional[float] = None,
        eta_max: Optional[float] = None,
        noise_sigma: float = 0.0,
        shaper_file: str = "",
        phi_shift: float = 0.0,
    ) -> None:
        """Initializes a ReadoutSegment with explicit arguments."""
        self.Segment = int(segment)
        self.CollectionKey = str(collection_key)
        self.DeltaEta = float(delta_eta)
        self.DeltaPhi = float(delta_phi)
        self.EtaMin = float(eta_min) if eta_min is not None else None
        self.EtaMax = float(eta_max) if eta_max is not None else None
        self.Noise = float(noise_sigma)
        self.PulseFile = str(shaper_file)
        self.PhiShift = float(phi_shift)

    @property
    def segment(self) -> int:
        return self.Segment

    @property
    def collection_key(self) -> str:
        return self.CollectionKey

    @property
    def delta_eta(self) -> float:
        return self.DeltaEta

    @property
    def delta_phi(self) -> float:
        return self.DeltaPhi

    @property
    def eta_min(self) -> Optional[float]:
        return self.EtaMin

    @property
    def eta_max(self) -> Optional[float]:
        return self.EtaMax

    @property
    def noise(self) -> float:
        return self.Noise

    @property
    def shaper(self) -> str:
        return self.PulseFile

    @property
    def phi_shift(self) -> float:
        return self.PhiShift

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the readout segment into a dictionary."""
        return {
            "segment": self.Segment,
            "collection_key": self.CollectionKey,
            "delta_eta": self.DeltaEta,
            "delta_phi": self.DeltaPhi,
            "eta_min": self.EtaMin,
            "eta_max": self.EtaMax,
            "noise": self.Noise,
            "shaper": self.PulseFile,
            "phi_shift": self.PhiShift,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReadoutSegment":
        """Reconstructs a ReadoutSegment from a dictionary."""
        return cls(
            segment=data["segment"],
            collection_key=data["collection_key"],
            delta_eta=data["delta_eta"],
            delta_phi=data["delta_phi"],
            eta_min=data.get("eta_min"),
            eta_max=data.get("eta_max"),
            noise_sigma=data.get("noise", 0.0),
            shaper_file=data.get("shaper", ""),
            phi_shift=data.get("phi_shift", 0.0),
        )


class CaloSamplingLayer(Logger):
    """
    Unified representation of an active calorimeter sampling layer for ATLAS v2.
    Combines physical dimensions, absorber/gap materials, cell readout granularity, and pulse shaping.
    """

    def __init__(
        self,
        name: str,
        collection_key: str,
        sampling: Union[CaloSampling, int],
        detector: Union[Detector, int],
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
        segments: Optional[List[ReadoutSegment]] = None,
    ) -> None:
        """Initializes an active calorimeter sampling layer with explicit arguments."""
        super().__init__()
        self.Name = str(name)
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
        self.X, self.Y, self.Z = float(center[0]), float(center[1]), float(center[2])
        self.Color = str(color)

        self.NSamples = int(n_samples)
        self.BunchIdStart = int(bunch_id_start)
        self.BunchIdEnd = int(bunch_id_end)
        self.StartSamplingBc = int(start_sampling_bc)
        self.OfWeightsEnergy = list(of_weights_energy) if of_weights_energy is not None else []
        self.OfWeightsTime = list(of_weights_time) if of_weights_time is not None else []
        self.Cuts = ProductionCuts(electron_cut, positron_cut, gamma_cut, proton_cut)

        # Readout Segments handling
        if segments:
            self.segments: List[ReadoutSegment] = list(segments)
            primary = self.segments[0]
            self.Segment = primary.Segment
            self.CollectionKey = primary.CollectionKey
            self.DeltaEta = primary.DeltaEta
            self.DeltaPhi = primary.DeltaPhi
            self.Noise = primary.Noise
            self.PulseFile = primary.PulseFile
            self.PhiShift = primary.PhiShift
        else:
            self.Segment = int(segment)
            self.CollectionKey = str(collection_key)
            self.DeltaEta = float(delta_eta)
            self.DeltaPhi = float(delta_phi)
            self.Noise = float(noise_sigma)
            self.PulseFile = str(shaper_file)
            self.PhiShift = float(phi_shift)
            self.segments = [
                ReadoutSegment(
                    segment=self.Segment,
                    collection_key=self.CollectionKey,
                    delta_eta=self.DeltaEta,
                    delta_phi=self.DeltaPhi,
                    noise_sigma=self.Noise,
                    shaper_file=self.PulseFile,
                    phi_shift=self.PhiShift,
                )
            ]

    @property
    def name(self) -> str:
        return self.Name

    @property
    def sampling(self) -> int:
        return int(self.Sampling)

    @property
    def detector_name(self) -> str:
        return self.Detector.name if hasattr(self.Detector, "name") else str(self.Detector)

    @property
    def r_min(self) -> float:
        return self.RMin

    @property
    def r_max(self) -> float:
        return self.RMax

    @property
    def z_min(self) -> float:
        return self.Z - self.ZSize / 2.0

    @property
    def z_max(self) -> float:
        return self.Z + self.ZSize / 2.0

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
    def noise(self) -> float:
        return self.Noise

    @noise.setter
    def noise(self, val: float) -> None:
        self.Noise = float(val)

    @property
    def plates(self) -> Plates:
        return self.Plates

    @property
    def readout_segments(self) -> List[ReadoutSegment]:
        """Returns all readout segments associated with this physical volume."""
        return self.segments

    def volume(self) -> "CaloSamplingLayer":
        return self

    def sensitive(self) -> "CaloSamplingLayer":
        return self

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the layer into the canonical JSON format."""
        plates_str = "Horizontal"
        if self.Plates == Plates.Vertical:
            plates_str = "Vertical"
        elif self.Plates == Plates.Polycone:
            plates_str = "Polycone"

        return {
            "name": self.Name,
            "plates": plates_str,
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
            "readouts": [s.to_dict() for s in self.segments],
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
        plates_val = data.get("plates", "Horizontal")
        if plates_val == "Vertical":
            plates = Plates.Vertical
        elif plates_val == "Polycone":
            plates = Plates.Polycone
        else:
            plates = Plates.Horizontal

        center = geom.get("center", [0.0, 0.0, 0.0])
        segments = None
        if "readouts" in data and isinstance(data["readouts"], list):
            segments = [ReadoutSegment.from_dict(s) for s in data["readouts"]]

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
            absorber_material=mats.get("absorber", "G4_Pb"),
            gap_material=mats.get("gap", "liquidArgon"),
            plates=plates,
            center=(center[0], center[1], center[2]),
            delta_eta=readout.get("delta_eta", 0.025),
            delta_phi=readout.get("delta_phi", 0.025),
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
            segments=segments,
        )


class DeadMaterialVolume:
    """Passive volume for cryostats, solenoid, cracks, and supports in ATLAS."""

    def __init__(
        self,
        name: str,
        material: str,
        rmin: float = 0.0,
        rmax: float = 0.0,
        z_size: float = 0.0,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        plates: Plates = Plates.Horizontal,
        in_solenoid_field: bool = False,
        polycone_planes: Optional[Dict[str, List[float]]] = None,
        color: str = "gray",
        electron_cut: float = 1.0,
        positron_cut: float = 1.0,
        gamma_cut: float = 1.0,
        proton_cut: float = 1.0,
    ) -> None:
        self.Name = str(name)
        self.Material = str(material)
        self.AbsorberMaterial = self.Material
        self.GapMaterial = "Vacuum"
        self.RMin = float(rmin)
        self.RMax = float(rmax)
        self.ZSize = float(z_size)
        self.NofLayers = 1
        self.AbsorberThickness = (self.RMax - self.RMin) if plates == Plates.Horizontal else self.ZSize
        self.GapThickness = 0.0
        self.Plates = plates
        self.X, self.Y, self.Z = float(center[0]), float(center[1]), float(center[2])
        self.InSolenoidField = bool(in_solenoid_field)
        self.PolyconePlanes = polycone_planes or {}
        self.Color = str(color)
        self.Cuts = ProductionCuts(electron_cut, positron_cut, gamma_cut, proton_cut)

    @property
    def name(self) -> str:
        return self.Name

    @property
    def r_min(self) -> float:
        if self.Plates == Plates.Polycone and "rmin" in self.PolyconePlanes and self.PolyconePlanes["rmin"]:
            return min(self.PolyconePlanes["rmin"])
        return self.RMin

    @property
    def r_max(self) -> float:
        if self.Plates == Plates.Polycone and "rmax" in self.PolyconePlanes and self.PolyconePlanes["rmax"]:
            return max(self.PolyconePlanes["rmax"])
        return self.RMax

    @property
    def z_min(self) -> float:
        if self.Plates == Plates.Polycone and "z" in self.PolyconePlanes and self.PolyconePlanes["z"]:
            return min(self.PolyconePlanes["z"])
        return self.Z - self.ZSize / 2.0

    @property
    def z_max(self) -> float:
        if self.Plates == Plates.Polycone and "z" in self.PolyconePlanes and self.PolyconePlanes["z"]:
            return max(self.PolyconePlanes["z"])
        return self.Z + self.ZSize / 2.0

    @property
    def z_size(self) -> float:
        return self.z_max - self.z_min

    def volume(self) -> "DeadMaterialVolume":
        return self

    def to_dict(self) -> Dict[str, Any]:
        plates_str = "Horizontal"
        if self.Plates == Plates.Vertical:
            plates_str = "Vertical"
        elif self.Plates == Plates.Polycone:
            plates_str = "Polycone"

        d: Dict[str, Any] = {
            "name": self.Name,
            "plates": plates_str,
            "materials": {
                "absorber": self.Material,
                "gap": "Vacuum",
            },
            "geometry": {
                "nof_layers": 1,
                "absorber_thickness": self.AbsorberThickness,
                "gap_thickness": 0.0,
                "rmin": self.RMin,
                "rmax": self.RMax,
                "z_size": self.ZSize,
                "center": [self.X, self.Y, self.Z],
            },
            "in_solenoid_field": self.InSolenoidField,
            "cuts": {
                "electron": self.Cuts.ElectronCut,
                "positron": self.Cuts.PositronCut,
                "gamma": self.Cuts.GammaCut,
                "proton": self.Cuts.PhotonCut,
            },
        }
        if self.Plates == Plates.Polycone and self.PolyconePlanes:
            d["polycone"] = self.PolyconePlanes
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeadMaterialVolume":
        geom = data.get("geometry", {})
        mats = data.get("materials", {})
        cuts = data.get("cuts", {})
        center = geom.get("center", [0.0, 0.0, 0.0])
        plates_val = data.get("plates", "Horizontal")
        if plates_val == "Vertical":
            plates = Plates.Vertical
        elif plates_val == "Polycone":
            plates = Plates.Polycone
        else:
            plates = Plates.Horizontal

        return cls(
            name=data["name"],
            material=mats.get("absorber", "G4_Al"),
            rmin=geom.get("rmin", 0.0),
            rmax=geom.get("rmax", 0.0),
            z_size=geom.get("z_size", 0.0),
            center=(center[0], center[1], center[2]),
            plates=plates,
            in_solenoid_field=data.get("in_solenoid_field", false if "false" in str(data) else False),
            polycone_planes=data.get("polycone"),
            electron_cut=cuts.get("electron", 1.0),
            positron_cut=cuts.get("positron", 1.0),
            gamma_cut=cuts.get("gamma", 1.0),
            proton_cut=cuts.get("proton", 1.0),
        )


# =========================================================================
# Fluent Builders for ATLAS Subdetectors
# =========================================================================

class AtlasEmbBuilder:
    """Fluent builder for ATLAS Electromagnetic Barrel (EMB) sampling layers."""

    def __init__(self, name: str, sampling: Union[CaloSampling, int]) -> None:
        self._name = str(name)
        self._sampling = sampling
        self._rmin = 1500.0
        self._rmax = 1600.0
        self._z_size = 6330.0
        self._lead_th = 1.53
        self._lar_gap = 4.5
        self._n_layers = 16
        self._delta_eta = 0.025
        self._delta_phi = np.pi / 128.0
        self._noise = 40.0
        self._pulse_file = "pulseLar.dat"

    def radii(self, rmin: float, rmax: float) -> "AtlasEmbBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        return self

    def z_length(self, z_size: float) -> "AtlasEmbBuilder":
        self._z_size = float(z_size)
        return self

    def accordion(self, lead_th: float, lar_gap: float, n_layers: int) -> "AtlasEmbBuilder":
        self._lead_th = float(lead_th)
        self._lar_gap = float(lar_gap)
        self._n_layers = int(n_layers)
        return self

    def granularity(self, d_eta: float, d_phi: float) -> "AtlasEmbBuilder":
        self._delta_eta = float(d_eta)
        self._delta_phi = float(d_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "AtlasEmbBuilder":
        self._noise = float(noise_mev)
        self._pulse_file = str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        return CaloSamplingLayer(
            name=self._name,
            collection_key="Collection_" + self._name.replace("::", "_"),
            sampling=self._sampling,
            detector=Detector.LAR,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=self._z_size,
            nof_layers=self._n_layers,
            absorber_thickness=self._lead_th,
            gap_thickness=self._lar_gap,
            absorber_material="G4_Pb",
            gap_material="liquidArgon",
            plates=Plates.Horizontal,
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
        )


class AtlasTileBuilder:
    """Fluent builder for ATLAS Tile calorimeter sampling layers."""

    def __init__(self, name: str, sampling: Union[CaloSampling, int]) -> None:
        self._name = str(name)
        self._sampling = sampling
        self._rmin = 2280.0
        self._rmax = 2600.0
        self._zmin = -2820.0
        self._zmax = 2820.0
        self._steel_th = 14.0
        self._tile_th = 3.0
        self._wrap_th = 1.0
        self._delta_eta = 0.1
        self._delta_phi = 0.1
        self._noise = 30.0
        self._pulse_file = "pulseTile.dat"

    def radii(self, rmin: float, rmax: float) -> "AtlasTileBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        return self

    def z_span(self, zmin: float, zmax: float) -> "AtlasTileBuilder":
        self._zmin = float(zmin)
        self._zmax = float(zmax)
        return self

    def period(self, steel_mm: float, scint_mm: float, wrap_mm: float) -> "AtlasTileBuilder":
        self._steel_th = float(steel_mm)
        self._tile_th = float(scint_mm)
        self._wrap_th = float(wrap_mm)
        return self

    def cells(self, d_eta: float, d_phi: float) -> "AtlasTileBuilder":
        self._delta_eta = float(d_eta)
        self._delta_phi = float(d_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "AtlasTileBuilder":
        self._noise = float(noise_mev)
        self._pulse_file = str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        z_size = self._zmax - self._zmin
        z_center = (self._zmax + self._zmin) / 2.0
        nof_layers = max(1, int(z_size / (self._steel_th + self._tile_th + self._wrap_th)))

        return CaloSamplingLayer(
            name=self._name,
            collection_key="Collection_" + self._name.replace("::", "_"),
            sampling=self._sampling,
            detector=Detector.TILE,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=z_size,
            nof_layers=nof_layers,
            absorber_thickness=self._steel_th,
            gap_thickness=self._tile_th,
            absorber_material="G4_Fe",
            gap_material="Scintillator",
            plates=Plates.Vertical,
            center=(0.0, 0.0, z_center),
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
        )


class AtlasEmecBuilder:
    """Fluent builder for ATLAS Electromagnetic Endcap (EMEC) sampling layers."""

    def __init__(self, name: str, sampling: Union[CaloSampling, int]) -> None:
        self._name = str(name)
        self._sampling = sampling
        self._rmin = 330.0
        self._rmax = 2034.0
        self._zmin = 3680.0
        self._zmax = 4320.0
        self._lead_th = 1.7
        self._lar_gap = 2.0
        self._n_layers = 12
        self._absorber_mat = "G4_Pb"
        self._gap_mat = "liquidArgon"
        self._delta_eta = 0.025
        self._delta_phi = 0.025
        self._noise = 45.0
        self._pulse_file = "pulseLar.dat"
        self._segments: List[ReadoutSegment] = []

    def radii(self, rmin: float, rmax: float) -> "AtlasEmecBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        return self

    def z_span(self, zmin: float, zmax: float) -> "AtlasEmecBuilder":
        self._zmin = float(zmin)
        self._zmax = float(zmax)
        return self

    def layers_and_absorber(self, n_layers: int, lead_th: float, lar_gap: float) -> "AtlasEmecBuilder":
        self._n_layers = int(n_layers)
        self._lead_th = float(lead_th)
        self._lar_gap = float(lar_gap)
        return self

    def materials(self, absorber: str = "G4_Pb", gap: str = "liquidArgon") -> "AtlasEmecBuilder":
        """Sets the absorber and gap material names for EMEC/PSE."""
        self._absorber_mat, self._gap_mat = str(absorber), str(gap)
        return self

    def granularity(self, d_eta: float, d_phi: float) -> "AtlasEmecBuilder":
        self._delta_eta = float(d_eta)
        self._delta_phi = float(d_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "AtlasEmecBuilder":
        self._noise = float(noise_mev)
        self._pulse_file = str(pulse_file)
        return self

    def add_segment(
        self,
        segment: int,
        delta_eta: float,
        delta_phi: float,
        eta_min: Optional[float] = None,
        eta_max: Optional[float] = None,
        noise_mev: Optional[float] = None,
        pulse_file: Optional[str] = None,
        phi_shift: float = 0.0,
    ) -> "AtlasEmecBuilder":
        """Adds a readout eta-segment to this sampling layer."""
        samp_name = self._name.split("::")[-2] if "::" in self._name else self._name
        side_tag = self._name.split("::")[-1] if "::" in self._name else ""
        if side_tag in ("A", "B"):
            key = f"Collection_{samp_name}_{segment}{side_tag}"
        else:
            key = f"Collection_{self._name.replace('::', '_')}_{segment}"
        seg_noise = float(noise_mev) if noise_mev is not None else self._noise
        seg_pulse = str(pulse_file) if pulse_file is not None else self._pulse_file
        self._segments.append(
            ReadoutSegment(
                segment=int(segment),
                collection_key=key,
                delta_eta=float(delta_eta),
                delta_phi=float(delta_phi),
                eta_min=float(eta_min) if eta_min is not None else None,
                eta_max=float(eta_max) if eta_max is not None else None,
                noise_sigma=seg_noise,
                shaper_file=seg_pulse,
                phi_shift=float(phi_shift),
            )
        )
        return self

    def build(self) -> CaloSamplingLayer:
        z_size = abs(self._zmax - self._zmin)
        z_center = (self._zmax + self._zmin) / 2.0
        segments = self._segments if self._segments else None

        return CaloSamplingLayer(
            name=self._name,
            collection_key="Collection_" + self._name.replace("::", "_"),
            sampling=self._sampling,
            detector=Detector.LAR,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=z_size,
            nof_layers=self._n_layers,
            absorber_thickness=self._lead_th,
            gap_thickness=self._lar_gap,
            absorber_material=self._absorber_mat,
            gap_material=self._gap_mat,
            plates=Plates.Vertical,
            center=(0.0, 0.0, z_center),
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
            segments=segments,
        )


class AtlasHecBuilder:
    """Fluent builder for ATLAS Hadronic Endcap (HEC) sampling layers."""

    def __init__(self, name: str, sampling: Union[CaloSampling, int]) -> None:
        self._name = str(name)
        self._sampling = sampling
        self._rmin = 372.0
        self._rmax = 2030.0
        self._zmin = 4277.0
        self._zmax = 4797.0
        self._copper_th = 25.0
        self._lar_gap = 8.5
        self._n_layers = 8
        self._delta_eta = 0.1
        self._delta_phi = 0.1
        self._noise = 50.0
        self._pulse_file = "pulseLar.dat"
        self._segments: List[ReadoutSegment] = []

    def radii(self, rmin: float, rmax: float) -> "AtlasHecBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        return self

    def z_span(self, zmin: float, zmax: float) -> "AtlasHecBuilder":
        self._zmin = float(zmin)
        self._zmax = float(zmax)
        return self

    def copper_plates(self, copper_th: float, lar_gap: float, n_layers: int) -> "AtlasHecBuilder":
        self._copper_th = float(copper_th)
        self._lar_gap = float(lar_gap)
        self._n_layers = int(n_layers)
        return self

    def granularity(self, d_eta: float, d_phi: float) -> "AtlasHecBuilder":
        self._delta_eta = float(d_eta)
        self._delta_phi = float(d_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "AtlasHecBuilder":
        self._noise = float(noise_mev)
        self._pulse_file = str(pulse_file)
        return self

    def add_segment(
        self,
        segment: int,
        delta_eta: float,
        delta_phi: float,
        eta_min: Optional[float] = None,
        eta_max: Optional[float] = None,
        noise_mev: Optional[float] = None,
        pulse_file: Optional[str] = None,
        phi_shift: float = 0.0,
    ) -> "AtlasHecBuilder":
        """Adds a readout eta-segment to this sampling layer."""
        samp_name = self._name.split("::")[-2] if "::" in self._name else self._name
        side_tag = self._name.split("::")[-1] if "::" in self._name else ""
        if side_tag in ("A", "B"):
            key = f"Collection_{samp_name}_{segment}{side_tag}"
        else:
            key = f"Collection_{self._name.replace('::', '_')}_{segment}"
        seg_noise = float(noise_mev) if noise_mev is not None else self._noise
        seg_pulse = str(pulse_file) if pulse_file is not None else self._pulse_file
        self._segments.append(
            ReadoutSegment(
                segment=int(segment),
                collection_key=key,
                delta_eta=float(delta_eta),
                delta_phi=float(delta_phi),
                eta_min=float(eta_min) if eta_min is not None else None,
                eta_max=float(eta_max) if eta_max is not None else None,
                noise_sigma=seg_noise,
                shaper_file=seg_pulse,
                phi_shift=float(phi_shift),
            )
        )
        return self

    def build(self) -> CaloSamplingLayer:
        z_size = abs(self._zmax - self._zmin)
        z_center = (self._zmax + self._zmin) / 2.0
        segments = self._segments if self._segments else None

        return CaloSamplingLayer(
            name=self._name,
            collection_key="Collection_" + self._name.replace("::", "_"),
            sampling=self._sampling,
            detector=Detector.LAR,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=z_size,
            nof_layers=self._n_layers,
            absorber_thickness=self._copper_th,
            gap_thickness=self._lar_gap,
            absorber_material="G4_Cu",
            gap_material="liquidArgon",
            plates=Plates.Vertical,
            center=(0.0, 0.0, z_center),
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
            segments=segments,
        )


class AtlasFcalBuilder:
    """Fluent builder for ATLAS Forward Calorimeter (FCAL) modules."""

    def __init__(self, name: str, sampling: Union[CaloSampling, int]) -> None:
        self._name = str(name)
        self._sampling = sampling
        self._rmin = 72.0
        self._rmax = 450.0
        self._zmin = 4668.0
        self._zmax = 5118.0
        self._absorber_mat = "G4_Cu"
        self._abso_th = 20.0
        self._lar_gap = 1.0
        self._n_layers = 15
        self._delta_eta = 0.2
        self._delta_phi = 0.2
        self._noise = 80.0
        self._pulse_file = "pulseLar.dat"

    def radii(self, rmin: float, rmax: float) -> "AtlasFcalBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        return self

    def z_span(self, zmin: float, zmax: float) -> "AtlasFcalBuilder":
        self._zmin = float(zmin)
        self._zmax = float(zmax)
        return self

    def material_and_gap(self, absorber_mat: str, abso_th: float, lar_gap: float, n_layers: int) -> "AtlasFcalBuilder":
        self._absorber_mat = str(absorber_mat)
        self._abso_th = float(abso_th)
        self._lar_gap = float(lar_gap)
        self._n_layers = int(n_layers)
        return self

    def granularity(self, d_eta: float, d_phi: float) -> "AtlasFcalBuilder":
        self._delta_eta = float(d_eta)
        self._delta_phi = float(d_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "AtlasFcalBuilder":
        self._noise = float(noise_mev)
        self._pulse_file = str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        z_size = abs(self._zmax - self._zmin)
        z_center = (self._zmax + self._zmin) / 2.0

        return CaloSamplingLayer(
            name=self._name,
            collection_key="Collection_" + self._name.replace("::", "_"),
            sampling=self._sampling,
            detector=Detector.LAR,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=z_size,
            nof_layers=self._n_layers,
            absorber_thickness=self._abso_th,
            gap_thickness=self._lar_gap,
            absorber_material=self._absorber_mat,
            gap_material="liquidArgon",
            plates=Plates.Vertical,
            center=(0.0, 0.0, z_center),
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_sigma=self._noise,
            shaper_file=self._pulse_file,
        )


class AtlasDeadMaterialBuilder:
    """Fluent builder for passive dead materials, cryostats, and solenoid in ATLAS."""

    def __init__(self, name: str) -> None:
        self._name = str(name)
        self._material = "G4_Al"
        self._rmin = 0.0
        self._rmax = 0.0
        self._z_size = 0.0
        self._center = (0.0, 0.0, 0.0)
        self._plates = Plates.Horizontal
        self._in_solenoid_field = False
        self._polycone_planes: Optional[Dict[str, List[float]]] = None

    def tubular(self, rmin: float, rmax: float, z_size: float, material: str = "G4_Al", center: Tuple[float, float, float] = (0.0, 0.0, 0.0)) -> "AtlasDeadMaterialBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        self._z_size = float(z_size)
        self._material = str(material)
        self._center = center
        self._plates = Plates.Horizontal
        return self

    def polycone(self, z_planes: List[float], r_min: List[float], r_max: List[float], material: str = "G4_Al", in_solenoid_field: bool = False) -> "AtlasDeadMaterialBuilder":
        self._plates = Plates.Polycone
        self._material = str(material)
        self._in_solenoid_field = bool(in_solenoid_field)
        self._polycone_planes = {
            "z": [float(z) for z in z_planes],
            "rmin": [float(r) for r in r_min],
            "rmax": [float(r) for r in r_max],
        }
        return self

    def in_solenoid_field(self, flag: bool) -> "AtlasDeadMaterialBuilder":
        self._in_solenoid_field = bool(flag)
        return self

    def build(self) -> DeadMaterialVolume:
        return DeadMaterialVolume(
            name=self._name,
            material=self._material,
            rmin=self._rmin,
            rmax=self._rmax,
            z_size=self._z_size,
            center=self._center,
            plates=self._plates,
            in_solenoid_field=self._in_solenoid_field,
            polycone_planes=self._polycone_planes,
        )
