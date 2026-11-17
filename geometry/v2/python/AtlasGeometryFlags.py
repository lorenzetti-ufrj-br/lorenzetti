"""
AtlasGeometryFlags module.

Provides the dataclass-based configuration flags for the ATLAS (v2) detector geometry,
replacing individual CLI parameters in simulation and digitization transforms.
"""

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional
import os

from GaugiKernel import JobFlags

__all__ = ["AtlasGeometryFlags"]


@dataclass(init=False)
class AtlasGeometryFlags(JobFlags):
    """
    Configuration flags for ATLAS DetectorConstruction_v2.

    Sub-detectors:
        TileAtlasGeometry: Build tile calorimeter with ATLAS periodic geometry.
        TileAtlasCells: Use ATLAS tile cell segmentation (A1-A16, BC1-BC8, B9, D0-D6).
        TileAtlasItc: Intermediate tile calorimeter gap with plugs/services.
        TileAtlasGap: E1-E4 scintillators and active ITC cells (C10, D4).
        TileAtlasRun4: Position tile extended barrel and gap at Run 4 positions.
        AtlasEmb: Barrel EM calorimeter with ATLAS lead/LAr absorber composition.
        AtlasEmbCells: EMB layers ending at |z| = 3165 mm with ATLAS strip/middle/back cells.
        AtlasEmec: EM endcap with two accordion wheels.
        AtlasEmecArgonFraction: LAr accordion gap fraction in radial bands.
        AtlasHec: Hadronic endcap calorimeter (HEC0-HEC3) with nominal ATLAS cells.
        AtlasFcal: Forward calorimeter passive material modules (copper/tungsten).
        AtlasFcalCells: FCal electrode tubes and readout cells.
        AtlasFcalFrozenShowers: Fast simulation frozen shower parametrization in FCal.

    Passive Media & Services:
        AtlasMaterialInFront: Solenoid and cryostat front walls in radiation lengths.
        AtlasEndcapCryostat: Warm/cold vessels of endcap cryostats.
        AtlasBarrelCryostat: Outer cylinders and dead LAr of barrel cryostat.
        AtlasForwardShielding: Muon system shielding, toroids, and outer framework.
        AtlasBarrelGapServices: Dead material in the gap between barrel and extended barrel.

    Physics & Geometry DB:
        AtlasRun4: Import ITk, HGTD, beam pipe from ATLAS Run 4 GeoModel dump.
        AtlasG4: Geant4 physics settings from ATLAS production (FTFP_BERT_ATL, cuts).
        AtlasFullField: Full world magnetic field map and calo muon switching field.
        AtlasRun4Geometry: Path to SQLite GeoModel dump of Run 4.
        AtlasFieldMap: Path to ATLAS ROOT magnetic field map.
        AtlasFcalElectrodes: Path to CSV electrodes table for FCal.
    """

    # Subdetectors
    TileAtlasGeometry: Optional[bool] = None
    TileAtlasCells: Optional[bool] = None
    TileAtlasItc: Optional[bool] = None
    TileAtlasGap: Optional[bool] = None
    TileAtlasRun4: Optional[bool] = None

    AtlasEmb: Optional[bool] = None
    AtlasEmbCells: Optional[bool] = None
    AtlasEmec: Optional[bool] = None
    AtlasEmecArgonFraction: Optional[bool] = None
    AtlasHec: Optional[bool] = None
    AtlasFcal: Optional[bool] = None
    AtlasFcalCells: Optional[bool] = None
    AtlasFcalFrozenShowers: Optional[bool] = None

    # Passive media, cryostats & services
    AtlasMaterialInFront: Optional[bool] = None
    AtlasEndcapCryostat: Optional[bool] = None
    AtlasBarrelCryostat: Optional[bool] = None
    AtlasForwardShielding: Optional[bool] = None
    AtlasBarrelGapServices: Optional[bool] = None

    # Physics & GeoModel import
    AtlasRun4: Optional[bool] = None
    AtlasG4: Optional[bool] = None
    AtlasFullField: Optional[bool] = None

    # External database & map paths
    AtlasRun4Geometry: str = ""
    AtlasFieldMap: str = ""
    AtlasFcalElectrodes: str = ""

    @classmethod
    def apply_defaults(cls, is_v2: bool = True) -> None:
        """
        Applies defaults: if is_v2 is True, all unconfigured (None) boolean flags
        are enabled. If is_v2 is False, they are disabled. Resolves external data paths.
        """
        for f in fields(cls):
            if f.type is Optional[bool]:
                current = getattr(cls, f.name)
                if current is None:
                    setattr(cls, f.name, is_v2)

        if is_v2:
            data_dir = cls.get_data_dir()
            if not cls.AtlasRun4Geometry:
                cls.AtlasRun4Geometry = os.environ.get("LORENZETTI_ATLAS_RUN4_GEOMETRY", "")
            if not cls.AtlasFieldMap:
                cls.AtlasFieldMap = os.environ.get("LORENZETTI_FIELD_MAP", "")
            if not cls.AtlasFcalElectrodes:
                cls.AtlasFcalElectrodes = os.environ.get(
                    "LORENZETTI_FCAL_ELECTRODES",
                    os.path.join(data_dir, "LArFCalElectrodes-06.csv") if data_dir else "",
                )

    @classmethod
    def get_data_dir(cls) -> str:
        """Finds the geometry v2 data directory from environment or repository layout."""
        for p in (
            os.environ.get("LORENZETTI_GEOMETRY_V2_DATA_DIR"),
            os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
            str(Path(__file__).resolve().parents[1] / "data"),
        ):
            if p and os.path.isdir(p):
                return p
        return ""
