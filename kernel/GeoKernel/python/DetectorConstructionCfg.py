"""
DetectorConstructionCfg.py - Centralized factory function for detector instantiation in GeoKernel.
"""

from typing import Any, Dict, List, Optional
import os
from pathlib import Path

from magfield import MagFieldFlags
from GeoKernel.DetectorFlags import DetectorFlags


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
        os.environ.get("LORENZETTI_GEOKERNEL_DATA_DIR"),
        os.environ.get("LORENZETTI_GALTIC_DATA_DIR"),
        str(Path(__file__).resolve().parent.parent / "data"),
        str(Path(__file__).resolve().parents[2] / "data" / "GeoKernel"),
        str(Path(__file__).resolve().parents[2] / "geometry" / "GALTIC" / "data"),
        str(Path(__file__).resolve().parents[2] / "geometry" / "ATLAS" / "data"),
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
    check_overlaps: bool = False,
    **kwargs: Any,
) -> Any:
    """Instantiates and returns the configured detector construction object."""
    effective_name = detector or version or name

    # Normalization
    upper_name = effective_name.upper()
    if upper_name in ("V1", "GEOV1", "V2", "GEOV2"):
        raise ValueError(
            f"Legacy version '{effective_name}' is deprecated and rejected. "
            f"Use version='GALTIC' or version='ATLAS' (with atlas_version='v1'/'v2')."
        )
    elif upper_name == "GALTIC":
        chosen = "GALTIC"
    elif upper_name == "ATLAS":
        chosen = "ATLAS"
    elif upper_name == "ATLAS_V1":
        chosen = "ATLAS_V1"
    elif upper_name == "ATLAS_V2":
        chosen = "ATLAS_V2"
    else:
        chosen = DetectorFlags.Version.upper()

    geo_file = geometry_file if geometry_file is not None else GeometryFile

    if chosen == "GALTIC":
        from GALTIC import GalticDetectorConstruction

        galtic_kwargs: Dict[str, Any] = {}
        if UseMagneticField is not None:
            galtic_kwargs["use_magnetic_field"] = UseMagneticField
        if UseSolenoidField is not None:
            galtic_kwargs["use_solenoid_field"] = UseSolenoidField
        if CutOnPhi is not None:
            galtic_kwargs["cut_on_phi"] = CutOnPhi
        if geo_file:
            galtic_kwargs["geometry_file"] = geo_file
        if check_overlaps:
            galtic_kwargs["check_overlaps"] = check_overlaps

        for k, v in kwargs.items():
            galtic_kwargs[k] = v

        return GalticDetectorConstruction(name, **galtic_kwargs)

    elif chosen in ("ATLAS", "ATLAS_V1", "ATLAS_V2"):
        target_version = atlas_version.lower()
        if chosen == "ATLAS_V1":
            target_version = "v1"
        elif chosen == "ATLAS_V2":
            target_version = "v2"

        if target_version == "v2":
            from ATLAS.v2 import AtlasDetectorConstruction

            atlas_kwargs: Dict[str, Any] = {}
            if UseMagneticField is not None:
                atlas_kwargs["use_magnetic_field"] = UseMagneticField
            if UseSolenoidField is not None:
                atlas_kwargs["use_solenoid_field"] = UseSolenoidField
            if CutOnPhi is not None:
                atlas_kwargs["cut_on_phi"] = CutOnPhi
            if geo_file:
                atlas_kwargs["geometry_file"] = geo_file
            if check_overlaps:
                atlas_kwargs["check_overlaps"] = check_overlaps

            for k, v in kwargs.items():
                atlas_kwargs[k] = v

            return AtlasDetectorConstruction(name, **atlas_kwargs)
        else:
            from ATLAS.v1 import DetectorConstruction as AtlasDetectorConstructionV1

            v1_kwargs: Dict[str, Any] = {}
            if UseMagneticField is not None:
                v1_kwargs["UseMagneticField"] = UseMagneticField
            if UseSolenoidField is not None:
                v1_kwargs["UseSolenoidField"] = UseSolenoidField
            if CutOnPhi is not None:
                v1_kwargs["CutOnPhi"] = CutOnPhi

            for k, v in kwargs.items():
                v1_kwargs[k] = v

            return AtlasDetectorConstructionV1(name, **v1_kwargs)

    raise ValueError(f"Unknown detector specification: {effective_name} (chosen: {chosen})")
