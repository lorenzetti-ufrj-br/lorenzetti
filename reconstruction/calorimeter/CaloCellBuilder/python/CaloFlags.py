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

    # Standard deviation of electronic and pileup sampling noise in MeV
    SamplingnoiseStd: float = 0.0

    # Enable cross-talk simulation between neighboring calorimeter cells
    DoCrossTalk: bool = False

    # Enable Cell Out-of-Time Filtering (COF) correction
    DoCOF: bool = False

    # Enable channel defects and dead-cell masking
    DoDefects: bool = False

    # Filter digitized calorimeter cells based on a noise sigma significance cut
    FilterBySigma: bool = False

    # Significance threshold in units of sigma for cell noise filtering
    SigmaThreshold: float = 2.0


@dataclass(init=False)
class CrossTalkFlags(JobFlags):
    """
    Steering flags for cross-talk simulation between neighboring calorimeter cells.
    """

    # Minimum deposited energy required to trigger cross-talk modeling
    MinEnergy: float = 1.0 * GeV

    # Capacitive coupling amplitude percentage
    AmpCapacitive: float = 4.2

    # Inductive coupling amplitude percentage
    AmpInductive: float = 2.3

    # Resistive coupling amplitude percentage
    AmpResistive: float = 1.0


@dataclass(init=False)
class AnomalyFlags(JobFlags):
    """
    Configuration flags for detector defects and anomalies.
    """

    # Path to the bad run / masked channel defect list configuration file
    BadRunListFile: str = ""
