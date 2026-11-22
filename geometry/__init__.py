"""
geometry - Root package for Lorenzetti detector geometries.

Provides the unified factory DetectorConstructionCfg to instantiate GALTIC or ATLAS detectors,
transparently applying subsystem configuration flags.
"""

from typing import Any, Dict, List, Optional
import os
from pathlib import Path
from enum import IntEnum

from magfield import MagFieldFlags

__all__ = [
    "DetectorConstructionCfg",
    "DetectorFlags",
    "get_available_detectors",
    "Plates",
    "ProductionCuts",
    "get_data_dir",
]


class Plates(IntEnum):
    """Plate geometry orientation enum."""
    Horizontal = 0
    Vertical = 1


class ProductionCuts:
    """Production cuts for Geant4 particle generation."""

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


class DetectorFlags:
    """Global configuration flags for detector geometry selection."""
    Version: str = "GALTIC"

    @classmethod
    def reset(cls) -> None:
        """Resets detector flags to default."""
        cls.Version = "GALTIC"

    @classmethod
    def to_dict(cls) -> Dict[str, str]:
        """Returns dictionary of detector flags."""
        return {"Version": cls.Version}


AVAILABLE_DETECTORS: Dict[str, str] = {
    "GALTIC": "General Argon Liquid and Tile Integrated Calorimeter (Fast Parametric)",
    "ATLAS": "Full High-Fidelity ATLAS Detector (GeoModel / SQLite)",
}


def get_available_detectors() -> List[str]:
    """Returns the list of registered detector names."""
    return list(AVAILABLE_DETECTORS.keys())


def get_data_dir() -> str:
    """Finds the canonical geometry data directory containing pulse calibration files."""
    for p in (
        os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
        os.environ.get("LORENZETTI_GALTIC_DATA_DIR"),
        str(Path(__file__).resolve().parent / "GALTIC" / "data"),
        str(Path(__file__).resolve().parents[1] / "data" / "GALTIC"),
        str(Path(__file__).resolve().parent / "ATLAS" / "data"),
    ):
        if p and os.path.isdir(p):
            return p
    return ""


def DetectorConstructionCfg(
    name: str = "ATLAS",
    version: Optional[str] = None,
    detector: Optional[str] = None,
    **kwargs: Any,
) -> Any:
    """
    Central factory function to configure and instantiate detector geometries.

    Args:
        name: Instance name (default: "ATLAS").
        version: "GALTIC" (or "v1") for fast parametric calorimeter;
                 "ATLAS" (or "v2") for full realistic detector.
                 If None, falls back to DetectorFlags.Version.
        detector: Optional alias for version (e.g., passed as detector="GALTIC").
        **kwargs: Direct property overrides forwarded to the detector constructor.

    Returns:
        Configured detector instance (GalticDetectorConstruction or AtlasDetectorConstruction).
    """
    raw_version = version or detector or DetectorFlags.Version
    selected = raw_version.upper()

    if selected in ["GALTIC", "V1"]:
        from GALTIC import GalticDetectorConstruction
        MagFieldFlags.apply_defaults(is_v2=False)
        v_dict = {"UseMagneticField": MagFieldFlags.EnableField}
        v_dict.update(kwargs)
        return GalticDetectorConstruction(name, **v_dict)

    elif selected in ["ATLAS", "V2"]:
        from ATLAS import AtlasDetectorConstruction, AtlasGeometryFlags
        MagFieldFlags.apply_defaults(is_v2=True)
        AtlasGeometryFlags.apply_defaults(is_v2=True)
        geo_dict = AtlasGeometryFlags.to_dict()
        geo_dict["UseMagneticField"] = MagFieldFlags.EnableField
        geo_dict["UseSolenoidField"] = MagFieldFlags.EnableSolenoidOnly
        geo_dict.update(kwargs)
        return AtlasDetectorConstruction(name, **geo_dict)

    else:
        raise ValueError(
            f"Detector '{raw_version}' desconhecido. "
            f"Opções disponíveis: {get_available_detectors()}"
        )
