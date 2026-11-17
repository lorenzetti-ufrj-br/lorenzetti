"""
Configuration flags for calorimeter cluster reconstruction.
"""

from dataclasses import dataclass
from GaugiKernel import JobFlags
from GaugiKernel.constants import GeV

__all__ = ["CaloClusterFlags"]


@dataclass(init=False)
class CaloClusterFlags(JobFlags):
    """
    Steering flags for seeded calorimeter cluster reconstruction and moments computation.
    """
    MinCenterEnergy: float = 1.0 * GeV
    EtaWindow: float = 0.4
    PhiWindow: float = 0.4
    DoForwardMoments: bool = False
