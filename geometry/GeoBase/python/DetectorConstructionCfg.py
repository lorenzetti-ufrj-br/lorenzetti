"""
DetectorConstructionCfg module.

Provides a unified factory function to construct detector geometries (v1 or v2),
transparently injecting configured JobFlags and MagFieldFlags.
"""

from typing import Optional, Union, Any

from GeoBase.DetectorFlags import DetectorFlags
from magfield import MagFieldFlags

__all__ = ["DetectorConstructionCfg"]


def DetectorConstructionCfg(
    name: str = "ATLAS",
    version: Optional[str] = None,
    **kwargs: Any,
):
    """
    Factory function to configure and instantiate the appropriate detector geometry.

    Args:
        name: Instance name (default: "ATLAS").
        version: "v1" or "v2". If None, reads from DetectorFlags.Version.
        **kwargs: Direct property overrides forwarded to the detector constructor.

    Returns:
        Configured instance of DetectorConstruction_v1 or DetectorConstruction_v2.
    """
    det_version = (version or DetectorFlags.Version).lower()
    is_v2 = (det_version == "v2")

    MagFieldFlags.apply_defaults(is_v2=is_v2)

    if is_v2:
        from GeoV2 import DetectorConstruction_v2, AtlasGeometryFlags

        AtlasGeometryFlags.apply_defaults(is_v2=True)
        geo_dict = AtlasGeometryFlags.to_dict()
        geo_dict["UseMagneticField"] = MagFieldFlags.EnableField
        geo_dict["UseSolenoidField"] = MagFieldFlags.EnableSolenoidOnly
        geo_dict.update(kwargs)
        return DetectorConstruction_v2(name, **geo_dict)
    else:
        from GeoV1 import DetectorConstruction_v1

        v1_dict = {
            "UseMagneticField": MagFieldFlags.EnableField,
        }
        v1_dict.update(kwargs)
        return DetectorConstruction_v1(name, **v1_dict)
