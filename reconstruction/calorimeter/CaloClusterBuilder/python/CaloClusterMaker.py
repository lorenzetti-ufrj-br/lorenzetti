__all__ = ["CaloClusterMaker"]

import ROOT

from GaugiKernel        import Configurable
from CaloClusterBuilder import CaloClusterFlags

def CaloClusterMakerCfg( name,
                         InputCellsKey    : str,
                         InputSeedsKey    : str,
                         OutputClusterKey : str,
                         EtaWindow        : float = CaloClusterFlags.EtaWindow,
                         PhiWindow        : float = CaloClusterFlags.PhiWindow,
                         MinCenterEnergy  : float = CaloClusterFlags.MinCenterEnergy,
                         DoForwardMoments : bool  = CaloClusterFlags.DoForwardMoments,
                         OutputLevel      : str   = 0,
                         HistogramPath    : str   = "Expert/Clusters",
                       ) -> Configurable:

  return Configurable( name, 
                       ROOT.CaloClusterMaker,
                       InputCellsKey    = InputCellsKey,
                       InputSeedsKey    = InputSeedsKey,
                       OutputClusterKey = OutputClusterKey,
                       EtaWindow        = EtaWindow,
                       PhiWindow        = PhiWindow,
                       MinCenterEnergy  = MinCenterEnergy,
                       DoForwardMoments = DoForwardMoments,
                       OutputLevel      = OutputLevel,
                       HistogramPath    = HistogramPath,
                     )
  
CaloClusterMaker=CaloClusterMakerCfg