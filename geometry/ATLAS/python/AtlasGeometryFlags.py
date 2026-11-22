"""
AtlasGeometryFlags module.

Provides dataclass-based configuration flags for the ATLAS (v2) detector geometry,
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
    """

    # =========================================================================
    # Calorimeter Sub-detectors
    # =========================================================================

    # Build Tile calorimeter with ATLAS periodic geometry (14 mm steel, 3 mm tile, 1 mm clearance)
    TileAtlasGeometry: Optional[bool] = None

    # Use ATLAS Tile cells (A1-A16, BC1-BC8, B9, D0-D6) so that every volume point belongs to a cell
    TileAtlasCells: Optional[bool] = None

    # Intermediate Tile gap (ITC) with aluminium plug (passive D4/C10) and cables
    TileAtlasItc: Optional[bool] = None

    # Active gap/crack scintillators E1-E4 and active ITC cells C10 and D4 (Run 3/4 geometry)
    TileAtlasGap: Optional[bool] = None

    # Position Tile extended barrel and crack at the ATLAS Run 4 simulation coordinates (+40 mm side A, -30 mm C)
    TileAtlasRun4: Optional[bool] = None

    # Barrel EM calorimeter (EMB) with ATLAS lead/LAr composition (1.53 mm lead below |eta|=0.8, 1.13 mm above)
    AtlasEmb: Optional[bool] = None

    # EMB layers ending at |z| = 3165 mm with ATLAS cell granularity (0.003125 strips in EMB1)
    AtlasEmbCells: Optional[bool] = None

    # EM endcap (EMEC) with two concentric accordion wheels (1.375 < |eta| < 3.2)
    AtlasEmec: Optional[bool] = None

    # Liquid argon gap in radial bands computed from the volume fraction of the ATLAS accordion
    AtlasEmecArgonFraction: Optional[bool] = None

    # Hadronic endcap (HEC) with 4 samplings (copper plates 25/50 mm) and nominal ATLAS cells
    AtlasHec: Optional[bool] = None

    # Forward calorimeter (FCal) as homogeneous passive mixture of copper/tungsten and liquid argon
    AtlasFcal: Optional[bool] = None

    # FCal with detailed electrode tubes and readout cells mapped to ATLAS tiles
    AtlasFcalCells: Optional[bool] = None

    # Replace low-energy showers in FCal electrodes with pre-simulated frozen shower libraries (MC23_v1)
    AtlasFcalFrozenShowers: Optional[bool] = None

    # =========================================================================
    # Passive Media, Cryostats & Shielding
    # =========================================================================

    # Material in front of barrel EM in radiation lengths X0 (solenoid 0.66 X0, cryostat wall 0.76 X0)
    AtlasMaterialInFront: Optional[bool] = None

    # Outer warm (20 mm) and cold (35 mm) aluminium vessels of the endcap cryostats with dead LAr
    AtlasEndcapCryostat: Optional[bool] = None

    # Barrel cryostat outer aluminium vessels (30 mm) and dead liquid argon surrounding EMB
    AtlasBarrelCryostat: Optional[bool] = None

    # Outer material from Run 4 GeoModel dump: MuonSys, toroids, and JD/JT/JF borated polyethylene shielding
    AtlasForwardShielding: Optional[bool] = None

    # Dead material in the barrel-to-extended barrel gap (pedestals, front-end crates, feedthrough cables)
    AtlasBarrelGapServices: Optional[bool] = None

    # =========================================================================
    # Geant4 Simulation, Run 4 & Field
    # =========================================================================

    # Import ITk, HGTD, beam pipe, and 45 mm endcap shift from the ATLAS Run 4 GeoModel SQLite dump
    AtlasRun4: Optional[bool] = None

    # ATLAS Geant4 production settings (FTFP_BERT_ATL, region production cuts, Russian roulette)
    AtlasG4: Optional[bool] = None

    # Apply full 3D magnetic field map in the world and muon switching field in barrel EM
    AtlasFullField: Optional[bool] = None

    # =========================================================================
    # External Database & Map File Paths
    # =========================================================================

    # Path to ATLAS Run 4 SQLite GeoModel geometry dump (or LORENZETTI_ATLAS_RUN4_GEOMETRY)
    AtlasRun4Geometry: str = ""

    # Path to ATLAS 3D magnetic field map ROOT file (or LORENZETTI_FIELD_MAP)
    AtlasFieldMap: str = ""

    # Path to CSV file containing ATLAS FCal electrode coordinates (or LORENZETTI_FCAL_ELECTRODES)
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
            os.environ.get("LORENZETTI_GEOV2_DATA_DIR"),
            os.environ.get("LORENZETTI_GEOMETRY_V2_DATA_DIR"),
            os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
            str(Path(__file__).resolve().parents[1] / "data"),
        ):
            if p and os.path.isdir(p):
                return p
        return ""
