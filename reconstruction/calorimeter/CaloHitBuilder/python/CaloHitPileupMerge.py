"""
CaloHitPileupMerge module.

Provides the configurable wrapper for the CaloHitPileupMerge algorithm,
overlaying minimum-bias pileup hits onto hard-scatter signal events.
"""

from typing import List, Optional
import ROOT
from GaugiKernel import Configurable, LoggingLevel

__all__ = ["CaloHitPileupMergeCfg", "PileupMergeCfg"]


def CaloHitPileupMergeCfg(
    name: str = "CaloHitPileupMerge",
    LowPileupInputFiles: Optional[List[str]] = None,
    HighPileupInputFiles: Optional[List[str]] = None,
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
    NtupleName: str = "CollectionTree",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a CaloHitPileupMerge algorithm.

    Args:
        name: Algorithm instance name.
        LowPileupInputFiles: List of file paths containing low pileup minbias events.
        HighPileupInputFiles: List of file paths containing high pileup minbias events.
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
        NtupleName: TTree name inside input ROOT files.
        OutputLevel: Logging verbosity level.

    Returns:
        Configurable: Configured algorithm instance.
    """
    return Configurable(
        ROOT.CaloHitPileupMerge,
        name,
        LowPileupInputFiles=LowPileupInputFiles if LowPileupInputFiles is not None else [],
        HighPileupInputFiles=HighPileupInputFiles if HighPileupInputFiles is not None else [],
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
        NtupleName=NtupleName,
        OutputLevel=OutputLevel,
    )


# Backward compatibility alias
PileupMergeCfg = CaloHitPileupMergeCfg
