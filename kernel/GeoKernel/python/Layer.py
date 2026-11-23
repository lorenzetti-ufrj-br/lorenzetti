"""
Layer.py - Core geometric volume primitives and readout segment data structures for GeoKernel.

Defines the fundamental building blocks shared across Lorenzetti detector models (GALTIC, ATLAS):
  - Plates: Geometry logical plate orientation (Horizontal, Vertical, Polycone)
  - ProductionCuts: Geant4 particle production thresholds
  - ReadoutSegment: Eta-segmented readout granularity specification
  - CaloSamplingLayer: Physical sampling layer and collection definition
  - DeadMaterialVolume: Passive material structures (cryostats, solenoid, boundaries)
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union
from CaloCell.CaloDefs import CaloSampling, Detector


class Plates(IntEnum):
    """Plate geometry orientation enum."""
    Horizontal = 0
    Vertical = 1
    Polycone = 2


class ProductionCuts:
    """Production cuts for Geant4 particle generation (in mm)."""

    def __init__(
        self,
        ElectronCut: float = 1.0,
        PositronCut: float = 1.0,
        GammaCut: float = 1.0,
        PhotonCut: float = 1.0,
    ) -> None:
        """Initializes Geant4 particle cuts in mm."""
        self.ElectronCut = float(ElectronCut)
        self.PositronCut = float(PositronCut)
        self.GammaCut = float(GammaCut)
        self.PhotonCut = float(PhotonCut)

    def to_dict(self) -> Dict[str, float]:
        """Serializes cuts to dictionary."""
        return {
            "electron_cut": self.ElectronCut,
            "positron_cut": self.PositronCut,
            "gamma_cut": self.GammaCut,
            "photon_cut": self.PhotonCut,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProductionCuts":
        """Deserializes cuts from dictionary."""
        return cls(
            ElectronCut=data.get("electron_cut", 1.0),
            PositronCut=data.get("positron_cut", 1.0),
            GammaCut=data.get("gamma_cut", 1.0),
            PhotonCut=data.get("photon_cut", 1.0),
        )


@dataclass
class ReadoutSegment:
    """Specification of an active readout segment with its granularity, noise, and bounds."""

    segment: int
    collection_key: str
    delta_eta: float
    delta_phi: float
    eta_min: Optional[float] = None
    eta_max: Optional[float] = None
    noise_sigma: float = 0.0
    shaper_file: str = ""
    phi_shift: float = 0.0

    @property
    def Segment(self) -> int:
        return self.segment

    @property
    def CollectionKey(self) -> str:
        return self.collection_key

    @property
    def DeltaEta(self) -> float:
        return self.delta_eta

    @property
    def DeltaPhi(self) -> float:
        return self.delta_phi

    @property
    def EtaMin(self) -> Optional[float]:
        return self.eta_min

    @property
    def EtaMax(self) -> Optional[float]:
        return self.eta_max

    @property
    def Noise(self) -> float:
        return self.noise_sigma

    @property
    def PulseFile(self) -> str:
        return self.shaper_file

    @property
    def PhiShift(self) -> float:
        return self.phi_shift

    def to_dict(self) -> Dict[str, Any]:
        """Serializes segment to dictionary."""
        res: Dict[str, Any] = {
            "segment": self.segment,
            "collection_key": self.collection_key,
            "delta_eta": self.delta_eta,
            "delta_phi": self.delta_phi,
            "noise_sigma": self.noise_sigma,
            "shaper_file": self.shaper_file,
            "phi_shift": self.phi_shift,
        }
        if self.eta_min is not None:
            res["eta_min"] = self.eta_min
        if self.eta_max is not None:
            res["eta_max"] = self.eta_max
        return res

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ReadoutSegment":
        """Deserializes segment from dictionary."""
        return cls(
            segment=int(d.get("segment", 0)),
            collection_key=str(d.get("collection_key", "")),
            delta_eta=float(d.get("delta_eta", 0.025)),
            delta_phi=float(d.get("delta_phi", 0.025)),
            eta_min=float(d["eta_min"]) if "eta_min" in d and d["eta_min"] is not None else None,
            eta_max=float(d["eta_max"]) if "eta_max" in d and d["eta_max"] is not None else None,
            noise_sigma=float(d.get("noise_sigma", 0.0)),
            shaper_file=str(d.get("shaper_file", "")),
            phi_shift=float(d.get("phi_shift", 0.0)),
        )


class CaloSamplingLayer:
    """Parametric representation of an active calorimeter sampling layer."""

    def __init__(
        self,
        name: str,
        collection_key: str,
        sampling: Union[CaloSampling, int],
        detector: Detector = Detector.TTEM,
        rmin: float = 0.0,
        rmax: float = 0.0,
        z_size: float = 0.0,
        nof_layers: int = 1,
        absorber_thickness: float = 0.0,
        gap_thickness: float = 0.0,
        absorber_material: str = "G4_Pb",
        gap_material: str = "liquidArgon",
        plates: Plates = Plates.Horizontal,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        delta_eta: float = 0.025,
        delta_phi: float = 0.025,
        noise_sigma: float = 0.0,
        shaper_file: str = "pulseLar.dat",
        segment: int = 0,
        phi_shift: float = 0.0,
        color: str = "cyan",
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
        """Initializes calorimeter sampling layer parameters."""
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

    def to_dict(self) -> Dict[str, Any]:
        """Serializes layer to dictionary for JSON output."""
        return {
            "name": self.Name,
            "type": "CaloSamplingLayer",
            "sampling": int(self.Sampling),
            "detector": self.detector_name,
            "geometry": {
                "plates": int(self.Plates),
                "r_min": self.RMin,
                "r_max": self.RMax,
                "z_size": self.ZSize,
                "nof_layers": self.NofLayers,
                "absorber_thickness": self.AbsorberThickness,
                "gap_thickness": self.GapThickness,
                "absorber_material": self.AbsorberMaterial,
                "gap_material": self.GapMaterial,
                "center": [self.X, self.Y, self.Z],
                "color": self.Color,
            },
            "readout": {
                "collection_key": self.CollectionKey,
                "segment": self.Segment,
                "delta_eta": self.DeltaEta,
                "delta_phi": self.DeltaPhi,
                "noise_sigma": self.Noise,
                "shaper_file": self.PulseFile,
                "phi_shift": self.PhiShift,
            },
            "readouts": [s.to_dict() for s in self.segments],
            "electronics": {
                "n_samples": self.NSamples,
                "bunch_id_start": self.BunchIdStart,
                "bunch_id_end": self.BunchIdEnd,
                "start_sampling_bc": self.StartSamplingBc,
                "of_weights_energy": self.OfWeightsEnergy,
                "of_weights_time": self.OfWeightsTime,
            },
            "cuts": self.Cuts.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaloSamplingLayer":
        """Deserializes layer from dictionary."""
        geo = data.get("geometry", {})
        ro = data.get("readout", {})
        elec = data.get("electronics", {})
        cuts = data.get("cuts", {})
        det_raw = data.get("detector", "TTEM")
        if isinstance(det_raw, str):
            det = getattr(Detector, det_raw, Detector.TTEM)
        else:
            det = Detector(int(det_raw))

        segments = None
        if "readouts" in data and isinstance(data["readouts"], list) and data["readouts"]:
            segments = [ReadoutSegment.from_dict(seg_dict) for seg_dict in data["readouts"]]

        return cls(
            name=data["name"],
            collection_key=ro.get("collection_key", ""),
            sampling=data["sampling"],
            detector=det,
            rmin=geo.get("r_min", 0.0),
            rmax=geo.get("r_max", 0.0),
            z_size=geo.get("z_size", 0.0),
            nof_layers=geo.get("nof_layers", 1),
            absorber_thickness=geo.get("absorber_thickness", 0.0),
            gap_thickness=geo.get("gap_thickness", 0.0),
            absorber_material=geo.get("absorber_material", "G4_Pb"),
            gap_material=geo.get("gap_material", "liquidArgon"),
            plates=Plates(geo.get("plates", 0)),
            center=tuple(geo.get("center", [0.0, 0.0, 0.0])),
            delta_eta=ro.get("delta_eta", 0.025),
            delta_phi=ro.get("delta_phi", 0.025),
            noise_sigma=ro.get("noise_sigma", 0.0),
            shaper_file=ro.get("shaper_file", "pulseLar.dat"),
            segment=ro.get("segment", 0),
            phi_shift=ro.get("phi_shift", 0.0),
            color=geo.get("color", "cyan"),
            n_samples=elec.get("n_samples", 5),
            bunch_id_start=elec.get("bunch_id_start", -21),
            bunch_id_end=elec.get("bunch_id_end", 3),
            start_sampling_bc=elec.get("start_sampling_bc", -2),
            of_weights_energy=elec.get("of_weights_energy", []),
            of_weights_time=elec.get("of_weights_time", []),
            electron_cut=cuts.get("electron_cut", 1.0),
            positron_cut=cuts.get("positron_cut", 1.0),
            gamma_cut=cuts.get("gamma_cut", 1.0),
            proton_cut=cuts.get("photon_cut", 1.0),
            segments=segments,
        )


class DeadMaterialVolume:
    """Parametric representation of passive materials (cryostats, solenoid, cracks)."""

    def __init__(
        self,
        name: str,
        material: str = "G4_Al",
        rmin: float = 0.0,
        rmax: float = 0.0,
        z_size: float = 0.0,
        center: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        plates: Plates = Plates.Horizontal,
        in_solenoid_field: bool = False,
        polycone_planes: Optional[Dict[str, List[float]]] = None,
        color: str = "gray",
    ) -> None:
        """Initializes dead material volume parameters."""
        self.Name = str(name)
        self.Material = str(material)
        self.RMin = float(rmin)
        self.RMax = float(rmax)
        self.ZSize = float(z_size)
        self.X, self.Y, self.Z = float(center[0]), float(center[1]), float(center[2])
        self.Plates = plates
        self.InSolenoidField = bool(in_solenoid_field)
        self.PolyconePlanes = polycone_planes
        self.Color = str(color)

    @property
    def name(self) -> str:
        return self.Name

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
    def plates(self) -> Plates:
        return self.Plates

    def to_dict(self) -> Dict[str, Any]:
        """Serializes dead material volume to dictionary."""
        d: Dict[str, Any] = {
            "name": self.Name,
            "type": "DeadMaterialVolume",
            "material": self.Material,
            "geometry": {
                "plates": int(self.Plates),
                "r_min": self.RMin,
                "r_max": self.RMax,
                "z_size": self.ZSize,
                "center": [self.X, self.Y, self.Z],
                "color": self.Color,
            },
            "in_solenoid_field": self.InSolenoidField,
        }
        if self.PolyconePlanes:
            d["polycone_planes"] = self.PolyconePlanes
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeadMaterialVolume":
        """Deserializes dead material volume from dictionary."""
        geo = data.get("geometry", {})
        return cls(
            name=data["name"],
            material=data.get("material", "G4_Al"),
            rmin=geo.get("r_min", 0.0),
            rmax=geo.get("r_max", 0.0),
            z_size=geo.get("z_size", 0.0),
            center=tuple(geo.get("center", [0.0, 0.0, 0.0])),
            plates=Plates(geo.get("plates", 0)),
            in_solenoid_field=data.get("in_solenoid_field", False),
            polycone_planes=data.get("polycone_planes", None),
            color=geo.get("color", "gray"),
        )
