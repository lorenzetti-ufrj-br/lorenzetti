"""
CaloClusterMaker configuration helper.

Provides the CaloClusterMakerCfg helper to configure ROOT.CaloClusterMaker for seeded-clustering.
"""

from typing import Optional
import ROOT

from GaugiKernel import Configurable, LoggingLevel
from CaloClusterBuilder.CaloClusterFlags import CaloClusterFlags
from CaloClusterTools import ShowerShapeToolCfg, MomentsToolCfg

__all__ = ["CaloClusterMakerCfg", "CaloClusterMaker"]


def CaloClusterMakerCfg(
    name: str,
    InputCellsKey: str = "Cells",
    InputSeedsKey: str = "Seeds",
    OutputClusterKey: str = "Clusters",
    EtaWindow: float = CaloClusterFlags.EtaWindow,
    PhiWindow: float = CaloClusterFlags.PhiWindow,
    MinCenterEnergy: float = CaloClusterFlags.MinCenterEnergy,
    DoForwardMoments: bool = CaloClusterFlags.DoForwardMoments,
    OutputLevel: int = LoggingLevel.toC("INFO"),
    HistogramPath: str = "Expert/Clusters",
) -> Configurable:
    """
    Configures and returns a CaloClusterMaker algorithm instance with attached shower shape tools.

    Args:
        name: Name of the algorithm instance.
        InputCellsKey: StoreGate key for input calorimeter cells container.
        InputSeedsKey: StoreGate key for input seeds container.
        OutputClusterKey: StoreGate key for output reconstructed clusters container.
        EtaWindow: Full eta window size around cluster center.
        PhiWindow: Full phi window size around cluster center.
        MinCenterEnergy: Minimum electromagnetic energy required in 0.1x0.1 core around hottest cell (in MeV).
        DoForwardMoments: Flag to calculate forward cluster moments.
        OutputLevel: Logging verbosity level.
        HistogramPath: Root path in histogram service.

    Returns:
        Configurable: Configured ROOT.CaloClusterMaker algorithm instance.
    """
    maker = Configurable(
        ROOT.CaloClusterMaker,
        name,
        InputCellsKey=InputCellsKey,
        InputSeedsKey=InputSeedsKey,
        OutputClusterKey=OutputClusterKey,
        EtaWindow=EtaWindow,
        PhiWindow=PhiWindow,
        MinCenterEnergy=MinCenterEnergy,
        OutputLevel=OutputLevel,
        HistogramPath=HistogramPath,
    )

    maker.Tools += ShowerShapeToolCfg(f"ShowerShape_{name}", OutputLevel=OutputLevel)
    if DoForwardMoments:
        maker.Tools += MomentsToolCfg(f"Moments_{name}", OutputLevel=OutputLevel)

    return maker


# Alias for backward compatibility
CaloClusterMaker = CaloClusterMakerCfg
