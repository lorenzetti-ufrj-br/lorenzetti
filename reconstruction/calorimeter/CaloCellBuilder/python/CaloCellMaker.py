

__all__ = ["CaloCellMaker"]

import ROOT

from GaugiKernel import Configurable, LoggingLevel


class CaloCellMaker( Cpp ):

  def __init__( self, name, sampling, 
                InputHitsKey        : str="Hits",
                OutputCollectionKey : str="Collection",
                OutputLevel         : int=LoggingLevel.toC('INFO'),
                DetailedHistograms  : bool=False,
                HistogramPath       : str="/Hists/Cells" ): 

    Cpp.__init__(self, ROOT.CaloCellMaker(name) )
    self.Tools = []
    self.PulseGenerator = None


  def core(self):
    # Attach all tools before return the core
    for tool in self.Tools:
      self._core.push_back(tool.core())
    self._core.setPulseGenerator(self.PulseGenerator.core())
    return self._core


  def __add__( self, tool ):
    self.Tools += tool
    return self


def CaloCellMakerCfg(
  name : str,
  sampling,
  InputHitsKey        : str="Hits",
  OutputCollectionKey : str="Collection",
  OutputLevel         : int=LoggingLevel.toC('INFO'),
  DetailedHistograms  : bool=False,
  HistogramPath       : str="/Hists/Cells"
) -> Configurable:

  maker = Configurable(
    ROOT.CaloCellMaker,
    name,
    InputHitsKey        = InputHitsKey,
    OutputCollectionKey = OutputCollectionKey,
    OutputLevel         = OutputLevel,
    DetailedHistograms  = DetailedHistograms,
    HistogramPath       = HistogramPath,
    EtaBins             = sampling.sensitive().EtaBins,
    PhiBins             = sampling.sensitive().PhiBins,
    ZMin                = sampling.volume().ZMin,
    ZMax                = sampling.volume().ZMax,
    Z                   = sampling.sv.pv.Z,
    Sampling            = sampling.Sampling,
    Segment             = sampling.sensitive().Segment,
    Detector            = sampling.Detector,
    BunchIdStart        = sampling.BunchIdStart,
    BunchIdEnd          = sampling.BunchIdEnd,
    BunchDuration       = 25,
  )

  return maker



