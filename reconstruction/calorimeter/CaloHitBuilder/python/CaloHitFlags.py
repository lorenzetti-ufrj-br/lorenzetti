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
    Steering flags for hit creation and energy response:
        ActiveEnergyOnly: Keep only energy in active medium (LAr / Scintillator).
        BirksLaw: Apply Birks' law in scintillator and liquid argon.
        AtlasHitTime: TOF-corrected global time for bunch-crossing assignment.
        TileDualReadout: Two PMTs per tile cell (dual readout).
        TilePmtSplit: Energy sharing between PMTs ('ushape' or 'linear').
        NeutronTimeCut: Kill neutrons after this elapsed time in ns (default: 150 ns for v2).
        SaveAllHits: Save all hits regardless of RoI.
    """

    ActiveEnergyOnly: Optional[bool] = None
    BirksLaw: Optional[bool] = None
    AtlasHitTime: Optional[bool] = None
    TileDualReadout: Optional[bool] = None
    TilePmtSplit: str = "ushape"
    NeutronTimeCut: Optional[float] = None
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
    Steering flags for ATLAS free-running hit generation:
        Enable: Write calorimeter hits in ATLAS HITS ntuple layout (Tree CollectionTree).
        AtlasFormat: Compress and filter LAr hits exactly as FilterHit_tf without tglobal branches.
        KeepHits: Keep standard HIT stream and write free-running hits to FreeRunningTree.
        NoBinning: Record one entry per Geant4 step without ATLAS time bins.
        EmecChargeCollection: Ported Athena 23.0.14 charge collection and electric field for EMEC.
        EmecTables: Path to EMEC tables CSV.
        EmecFieldMap: Path to EMEC electric field map file (ec.fieldzv03).
        EmecHVMap: Path to EMEC high-voltage map file (HVEMECMap_v02.dat).
    """

    Enable: bool = False
    AtlasFormat: bool = False
    KeepHits: bool = False
    NoBinning: bool = False

    # EMEC charge collection
    EmecChargeCollection: bool = False
    EmecTables: str = ""
    EmecFieldMap: str = ""
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

    @classmethod
    def get_data_dir(cls) -> str:
        """Finds the geometry v2 data directory containing EMEC tables and maps."""
        for p in (
            os.environ.get("LORENZETTI_GEOMETRY_V2_DATA_DIR"),
            os.environ.get("LORENZETTI_GEOMETRY_DATA_DIR"),
            str(Path(__file__).resolve().parents[4] / "geometry" / "v2" / "data"),
        ):
            if p and os.path.isdir(p):
                return p
        return ""
