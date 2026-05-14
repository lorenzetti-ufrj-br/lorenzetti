__all__ = ["CaloClusterMaker"]

from GaugiKernel import Cpp
from GaugiKernel.macros import *
from CaloClusterBuilder import CaloClusterFlags as flags
import ROOT

class CaloClusterMaker( Cpp ):
  """
  Python wrapper for the C++ CaloClusterMaker algorithm.

  Groups calorimeter cells into clusters around seed positions. This is a crucial
  step in reconstruction, aggregating energy deposits to form candidate objects
  (like electrons or jets).
  """


  def __init__( self, name,
                InputCellsKey    : str, 
                InputSeedsKey    : str,
                OutputClusterKey : str, 
                EtaWindow        : float=flags.EtaWindow, 
                PhiWindow        : float=flags.PhiWindow,
                MinCenterEnergy  : float=flags.MinCenterEnergy,
                doForwardMoments : bool=flags.doForwardMoments,
                OutputLevel      : str=0, 
                HistogramPath    : str="Expert/Clusters",
              ):
    """
    Initialize the CaloClusterMaker.

    Args:
        name (str): Name of the algorithm instance.
        InputCellsKey (str): StoreGate key for input cells.
        InputSeedsKey (str): StoreGate key for seed particles (truth or reconstructed).
        OutputClusterKey (str): StoreGate key for the output clusters.
        EtaWindow (float): Half-width of the cluster window in eta.
        PhiWindow (float): Half-width of the cluster window in phi.
        MinCenterEnergy (float): Minimum energy required for the central cell/seed.
        doForwardMoments (bool): If True, calculates moments relevant for forward detectors.
        OutputLevel (str): Logging level.
        HistogramPath (str): Path for monitoring histograms.
    """

    Cpp.__init__(self, ROOT.CaloClusterMaker(name) )

    self.setProperty( "InputCellsKey"        , InputCellsKey        ) 
    self.setProperty( "InputSeedsKey"        , InputSeedsKey        )
    self.setProperty( "OutputClusterKey"     , OutputClusterKey     ) 
    self.setProperty( "EtaWindow"            , EtaWindow            ) 
    self.setProperty( "PhiWindow"            , PhiWindow            )
    self.setProperty( "MinCenterEnergy"      , MinCenterEnergy      )
    self.setProperty( "DoForwardMoments"     , doForwardMoments     )
    self.setProperty( "OutputLevel"          , OutputLevel          ) 
    self.setProperty( "HistogramPath"        , HistogramPath        )


