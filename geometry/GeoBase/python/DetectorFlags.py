"""
DetectorFlags module.

Provides dataclass-based steering flags for detector version selection.
"""

from dataclasses import dataclass
from GaugiKernel import JobFlags

__all__ = ["DetectorFlags"]


@dataclass(init=False)
class DetectorFlags(JobFlags):
    """
    Steering flags for detector selection.
    """

    # Active detector version: "v1" (simplified) or "v2" (ATLAS Run 4)
    Version: str = "v2"
