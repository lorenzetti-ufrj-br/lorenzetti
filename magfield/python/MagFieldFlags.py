"""
MagFieldFlags module.

Provides dataclass-based steering flags for magnetic field configuration.
"""

from dataclasses import dataclass
from typing import Optional
from GaugiKernel import JobFlags

__all__ = ["MagFieldFlags"]


@dataclass(init=False)
class MagFieldFlags(JobFlags):
    """
    Steering flags for detector magnetic field:
        EnableField: Enable general detector magnetic field (solenoid + toroids if available).
        EnableSolenoidOnly: Restrict uniform 2 T field strictly inside ATLAS solenoid (r < 1.23 m, |z| < 2.9 m).
    """

    EnableField: bool = False
    EnableSolenoidOnly: Optional[bool] = None

    @classmethod
    def apply_defaults(cls, is_v2: bool = True) -> None:
        """
        In detector v2, if general field is False and EnableSolenoidOnly is None,
        solenoid field is enabled by default. In v1, it is disabled.
        """
        if cls.EnableSolenoidOnly is None:
            cls.EnableSolenoidOnly = is_v2 and not cls.EnableField
