"""
Digitization configuration flags for calorimeter cell reconstruction.
"""

from dataclasses import dataclass
from GaugiKernel import JobFlags
from GaugiKernel.constants import GeV

__all__ = ["CaloFlags", "CrossTalkFlags", "AnomalyFlags"]


@dataclass(init=False)
class CaloFlags(JobFlags):
    """
    Global steering flags for calorimeter digitization.
    """
    SamplingnoiseStd: float = 0.0
    DoCrossTalk: bool = False
    DoCOF: bool = False
    DoDefects: bool = False
    FilterBySigma: bool = False
    SigmaThreshold: float = 2.0


@dataclass(init=False)
class CrossTalkFlags(JobFlags):
    """
    Steering flags for cross-talk simulation between neighboring calorimeter cells.
    """
    MinEnergy: float = 1.0 * GeV
    AmpCapacitive: float = 4.2
    AmpInductive: float = 2.3
    AmpResistive: float = 1.0


@dataclass(init=False)
class AnomalyFlags(JobFlags):
    """
    Configuration flags for detector defects and anomalies.
    """
    BadRunListFile: str = ""
