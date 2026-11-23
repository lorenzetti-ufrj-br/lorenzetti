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
    "ATLAS": "Full High-Fidelity ATLAS Detector (v1 default / v2 modern JSON)",
    "ATLAS_V1": "ATLAS Detector v1 (Imperative / GeoModel SQLite)",
    "ATLAS_V2": "ATLAS Detector v2 (Modern Declarative JSON)",
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
    atlas_version: str = "v1",
    UseMagneticField: Optional[bool] = None,
    UseSolenoidField: Optional[bool] = None,
    CutOnPhi: Optional[bool] = None,
    GeometryFile: str = "",
    geometry_file: Optional[str] = None,
) -> Any:
    """
    Central factory function to configure and instantiate detector geometries.

    Args:
        name: Instance name (default: "ATLAS").
        version: "GALTIC", "ATLAS", "ATLAS_V1", or "ATLAS_V2".
                 If None, falls back to DetectorFlags.Version.
        detector: Optional alias for version (e.g., passed as detector="GALTIC").
        atlas_version: Sub-version for ATLAS ("v1" or "v2", default: "v1").
        UseMagneticField: Optional override for global magnetic field.
        UseSolenoidField: Optional override for solenoid field.
        CutOnPhi: Optional override for phi wedge cut.
        GeometryFile: C++ property for the JSON geometry file path.
        geometry_file: Optional direct path to JSON geometry to load.

    Returns:
        Configured detector instance (GalticDetectorConstruction or AtlasDetectorConstruction).
    """
    raw_version = version or detector or DetectorFlags.Version
    selected = raw_version.upper()

    if selected == "GALTIC":
        from GALTIC import GalticDetectorConstruction
        MagFieldFlags.apply_defaults(is_v2=False)
        field_enabled = UseMagneticField if UseMagneticField is not None else MagFieldFlags.EnableField
        cut_phi = CutOnPhi if CutOnPhi is not None else False
        return GalticDetectorConstruction(
            name,
            UseMagneticField=field_enabled,
            CutOnPhi=cut_phi,
            GeometryFile=GeometryFile,
            geometry_file=geometry_file,
        )

    elif selected in ("ATLAS", "ATLAS_V1", "ATLAS_V2"):
        target_v = "v2" if selected == "ATLAS_V2" or atlas_version.lower() == "v2" else "v1"

        if target_v == "v2":
            from ATLAS.v2 import AtlasDetectorConstruction
            MagFieldFlags.apply_defaults(is_v2=True)
            field_enabled = UseMagneticField if UseMagneticField is not None else MagFieldFlags.EnableField
            solenoid_enabled = UseSolenoidField if UseSolenoidField is not None else MagFieldFlags.EnableSolenoidOnly
            cut_phi = CutOnPhi if CutOnPhi is not None else False
            return AtlasDetectorConstruction(
                name,
                UseMagneticField=field_enabled,
                UseSolenoidField=solenoid_enabled,
                CutOnPhi=cut_phi,
                GeometryFile=GeometryFile,
                geometry_file=geometry_file,
            )
        else:
            from ATLAS.v1 import AtlasDetectorConstruction, AtlasGeometryFlags
            MagFieldFlags.apply_defaults(is_v2=True)
            AtlasGeometryFlags.apply_defaults(enable_atlas=True)
            geo_dict = AtlasGeometryFlags.to_dict()
            geo_dict["UseMagneticField"] = UseMagneticField if UseMagneticField is not None else MagFieldFlags.EnableField
            geo_dict["UseSolenoidField"] = UseSolenoidField if UseSolenoidField is not None else MagFieldFlags.EnableSolenoidOnly
            if CutOnPhi is not None:
                geo_dict["CutOnPhi"] = CutOnPhi
            return AtlasDetectorConstruction(name, **geo_dict)

    else:
        raise ValueError(
            f"Detector '{raw_version}' desconhecido. "
            f"Opções disponíveis: {get_available_detectors()}"
        )
