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

    # Restrict cell streaming strictly to the Region of Interest (RoI) window
    OnlyRoI: bool = True

    # Pseudorapidity half-window size around the seed or truth particle for RoI selection
    EtaWindow: float = 0.4

    # Azimuthal angle half-window size in radians around the seed or truth particle for RoI selection
    PhiWindow: float = 0.4

    # Persist all calorimeter cells in the detector regardless of energy threshold or RoI
    SaveAllCells: bool = False


@dataclass(init=False)
class RootStreamAODFlags(JobFlags):
    """
    Steering flags for AOD stream output and Ringer extraction.
    """

    # Include individual calorimeter cell objects in the AOD stream output
    DumpCells: bool = True

    # Extract standard concentric calorimeter rings around the hottest cell
    doStdRings: bool = True

    # Extract four separate ring sequences shifted towards corner directions
    doCornerRings: bool = False

    # Extract asymmetric ring patterns across calorimeter quadrants
    doAsymRings: bool = False

    # Extract directional strip rings tailored for longitudinal/transverse profiling
    doStripsRings: bool = False

    # Extract cross-shaped ring configurations along principal axes
    doCrossRings: bool = False

    # Extract custom user-defined ring topologies with arbitrary offsets
    doCustomRings: bool = False

    # Apply a noise sigma threshold cut before computing ring sums
    DoSigmaCut: bool = False

    # Significance threshold in units of sigma applied to cell energies in rings
    SigmaCut: float = 2.0

    # Cell grid distance offset used for corner ring centers
    CornerShift: int = 3

    # Cell grid distance offset used for cross ring centers
    CrossShift: int = 3

    # List of integer cell grid shifts in eta for custom ring topologies
    CustomRingsShiftEta: List[int] = field(default_factory=lambda: [0])

    # List of integer cell grid shifts in phi for custom ring topologies
    CustomRingsShiftPhi: List[int] = field(default_factory=lambda: [0])

    # Orientation axis index for strip rings (0: eta axis, 1: phi axis)
    StripsAxis: int = 0
