"""
CaloHitFlags module.

Provides dataclass-based steering flags for calorimeter hit simulation,
energy response models, and free-running ATLAS format hits.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os

from GaugiKernel import JobFlags

__all__ = ["CaloHitFlags", "FreeRunningFlags"]


@dataclass(init=False)
class CaloHitFlags(JobFlags):
    """
    Steering flags for hit creation and energy response.
    """

    # Keep only energy deposited in active media (Liquid Argon and Tile Scintillator)
    ActiveEnergyOnly: Optional[bool] = None

    # Apply Birks' law saturation correction to scintillator and liquid argon energy deposits
    BirksLaw: Optional[bool] = None

    # Use time-of-flight (TOF) corrected global time for bunch-crossing assignment
    AtlasHitTime: Optional[bool] = None

    # Simulate two photomultiplier tubes (PMTs) per Tile calorimeter cell (dual readout)
    TileDualReadout: Optional[bool] = None

    # Energy sharing model between Tile PMTs ('ushape' for realistic light guide response or 'linear')
    TilePmtSplit: str = "ushape"

    # Maximum time in nanoseconds to track slow neutrons before killing them (default 150 ns for detector v2)
    NeutronTimeCut: Optional[float] = None

    # Save all calorimeter hits regardless of Region of Interest (RoI) bounds
    SaveAllHits: bool = False

    @classmethod
    def apply_defaults(cls, is_v2: bool = True) -> None:
        """Applies defaults based on detector version."""
        if cls.ActiveEnergyOnly is None:
            cls.ActiveEnergyOnly = is_v2
        if cls.BirksLaw is None:
            cls.BirksLaw = is_v2
        if cls.AtlasHitTime is None:
            cls.AtlasHitTime = is_v2
        if cls.TileDualReadout is None:
            cls.TileDualReadout = is_v2
        if cls.NeutronTimeCut is None:
            cls.NeutronTimeCut = 150.0 if is_v2 else 0.0


@dataclass(init=False)
class FreeRunningFlags(JobFlags):
    """
    Steering flags for ATLAS free-running hit generation.
    """

    # Write calorimeter hits in ATLAS HITS ntuple layout (CollectionTree)
    Enable: bool = False

    # Compress and filter LAr hits exactly as Athena FilterHit_tf without tglobal branches
    AtlasFormat: bool = False

    # Retain standard HIT stream and write free-running hits alongside in FreeRunningTree
    KeepHits: bool = False

    # Record raw energy per Geant4 step without grouping into ATLAS time bins
    NoBinning: bool = False

    # Enable ported Athena 23.0.14 charge collection and electric field model for EMEC
    EmecChargeCollection: bool = False

    # Path to EMEC calibration tables CSV file
    EmecTables: str = ""

    # Path to EMEC electric field map file (ec.fieldzv03)
    EmecFieldMap: str = ""

    # Path to EMEC high-voltage map file (HVEMECMap_v02.dat)
    EmecHVMap: str = ""

    @classmethod
    def apply_defaults(cls, is_v2: bool = True) -> None:
        """Resolves EMEC data paths if charge collection is enabled."""
        data_dir = cls.get_data_dir()
        if not cls.EmecTables:
            cls.EmecTables = os.path.join(data_dir, "EmecTables-ATLAS-P2-RUN4-01-01-00.csv") if data_dir else ""
        if not cls.EmecFieldMap:
            cls.EmecFieldMap = os.path.join(data_dir, "ec.fieldzv03") if data_dir else ""
        if not cls.EmecHVMap:
            cls.EmecHVMap = os.path.join(data_dir, "HVEMECMap_v02.dat") if data_dir else ""

        if cls.Enable and is_v2:
            CaloHitFlags.ActiveEnergyOnly = True
            CaloHitFlags.BirksLaw = True
            CaloHitFlags.TileDualReadout = True
            CaloHitFlags.TilePmtSplit = "ushape"
            CaloHitFlags.NeutronTimeCut = 150.0

    @classmethod
    def get_data_dir(cls) -> str:
        """Finds the geometry v2 data directory containing EMEC tables and maps."""
        for p in (
            os.environ.get("LORENZETTI_GEOV2_DATA_DIR"),
            os.environ.get("LORENZETTI_GEOMETRY_V2_DATA_DIR"),
            os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
            str(Path(__file__).resolve().parents[4] / "geometry" / "GeoV2" / "data"),
        ):
            if p and os.path.isdir(p):
                return p
        return ""
