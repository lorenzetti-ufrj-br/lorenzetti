"""
DetectorFlags.py - Global geometry configuration flags for GeoKernel.
"""

from typing import Dict


class DetectorFlags:
    """Global configuration flags for detector geometry selection."""

    Version: str = "GALTIC"

    @classmethod
    def reset(cls) -> None:
        """Resets detector flags to default."""
        cls.Version = "GALTIC"

    @classmethod
    def to_dict(cls) -> Dict[str, str]:
        """Returns dictionary of detector flags."""
        return {"Version": cls.Version}
