"""
RootStreamFlags module.

Provides dataclass-based configuration flags for ROOT streaming and persistence.
"""

from dataclasses import dataclass, field
from typing import List
from GaugiKernel import JobFlags

__all__ = ["RootStreamHITFlags", "RootStreamESDFlags", "RootStreamAODFlags"]


@dataclass(init=False)
class RootStreamHITFlags(JobFlags):
    """
    Steering flags for HIT stream output.
    """
    pass


@dataclass(init=False)
class RootStreamESDFlags(JobFlags):
    """
    Steering flags for ESD stream output.
    """
    OnlyRoI: bool = True
    EtaWindow: float = 0.4
    PhiWindow: float = 0.4
    SaveAllCells: bool = False


@dataclass(init=False)
class RootStreamAODFlags(JobFlags):
    """
    Steering flags for AOD stream output and Ringer extraction.
    """
    DumpCells: bool = True

    doStdRings: bool = True
    doCornerRings: bool = False
    doAsymRings: bool = False
    doStripsRings: bool = False
    doCrossRings: bool = False
    doCustomRings: bool = False

    DoSigmaCut: bool = False
    SigmaCut: float = 2.0
    CornerShift: int = 3
    CrossShift: int = 3
    CustomRingsShiftEta: List[int] = field(default_factory=lambda: [0])
    CustomRingsShiftPhi: List[int] = field(default_factory=lambda: [0])
    StripsAxis: int = 0
