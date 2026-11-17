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

    # Minimum seed cell energy required to initiate calorimeter cluster reconstruction
    MinCenterEnergy: float = 1.0 * GeV

    # Pseudorapidity half-window size around the seed cell for cluster aggregation
    EtaWindow: float = 0.4

    # Azimuthal angle half-window size in radians around the seed cell
    PhiWindow: float = 0.4

    # Compute cluster spatial shape moments in forward calorimeter regions
    DoForwardMoments: bool = False
