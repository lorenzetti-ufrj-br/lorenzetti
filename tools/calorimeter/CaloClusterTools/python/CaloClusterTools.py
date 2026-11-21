"""
CaloClusterTools configuration helpers.

Provides configuration helpers for calorimeter cluster tools:
- ShowerShapeToolCfg
- MomentsToolCfg / MomentsToolsCfg
"""

import ROOT
from GaugiKernel import Configurable, LoggingLevel

__all__ = [
    "ShowerShapeToolCfg",
    "MomentsToolCfg",
    "MomentsToolsCfg",
]


def ShowerShapeToolCfg(
    name: str = "ShowerShapeTool",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns a ShowerShapeTool instance.
    """
    return Configurable(
        ROOT.ShowerShapeTool,
        name,
        OutputLevel=OutputLevel,
    )


def MomentsToolCfg(
    name: str = "MomentsTool",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns a MomentsTool instance.
    """
    return Configurable(
        ROOT.MomentsTool,
        name,
        OutputLevel=OutputLevel,
    )


# Alias
MomentsToolsCfg = MomentsToolCfg
