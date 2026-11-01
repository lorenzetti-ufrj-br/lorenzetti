"""
CaloHitPileupMerge module.

Provides the configurable wrapper for the CaloHitPileupMerge algorithm,
overlaying minimum-bias pileup hits onto hard-scatter signal events.
"""

from typing import List, Optional
import ROOT
from GaugiKernel import Configurable, LoggingLevel

__all__ = ["CaloHitPileupMergeCfg"]


def CaloHitPileupMergeCfg(
    name: str = "CaloHitPileupMerge",
    PileupFiles: Optional[List[str]] = None,
    PileupAvg: float = 0.0,
    PileupSigma: float = 0.0,
    InputHitsKey: str = "Hits",
    InputEventKey: str = "Events",
    OutputHitsKey: str = "Hits_Merged",
    OutputEventKey: str = "Events_Merged",
    BunchIdStart: int = -21,
    BunchIdEnd: int = 4,
    TruncMu: float = 1000.0,
    MergeMaxRetry: int = 10,
    Seed: float = 0.0,
    StartEntry: int = -1,
    NtupleName: str = "CollectionTree",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a CaloHitPileupMerge algorithm.

    Args:
        name: Algorithm instance name.
        PileupFiles: List of file paths containing MinBias events (BC=0).
        PileupAvg: Average pileup interaction value (mu).
        PileupSigma: Fluctuation in mu.
        InputHitsKey: StoreGate key for input signal hits.
        InputEventKey: StoreGate key for input signal event info.
        OutputHitsKey: StoreGate key for output merged hits.
        OutputEventKey: StoreGate key for output merged event info.
        BunchIdStart: First bunch crossing ID in the window.
        BunchIdEnd: Last bunch crossing ID in the window.
        TruncMu: Maximum truncation cut on mu.
        MergeMaxRetry: Number of retries on I/O read errors.
        Seed: Random number generator seed.
        StartEntry: Optional starting MinBias entry (-1 for random circular offset).
        NtupleName: TTree name inside input ROOT files.
        OutputLevel: Logging verbosity level.

    Returns:
        Configurable: Configured algorithm instance.
    """
    return Configurable(
        ROOT.CaloHitPileupMerge,
        name,
        PileupFiles=PileupFiles or [],
        PileupAvg=PileupAvg,
        PileupSigma=PileupSigma,
        InputHitsKey=InputHitsKey,
        InputEventKey=InputEventKey,
        OutputHitsKey=OutputHitsKey,
        OutputEventKey=OutputEventKey,
        BunchIdStart=BunchIdStart,
        BunchIdEnd=BunchIdEnd,
        TruncMu=TruncMu,
        MergeMaxRetry=MergeMaxRetry,
        Seed=Seed,
        StartEntry=StartEntry,
        NtupleName=NtupleName,
        OutputLevel=OutputLevel,
    )
