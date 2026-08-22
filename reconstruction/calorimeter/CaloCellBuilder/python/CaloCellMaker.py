

__all__ = ["CaloCellMakerCfg"]

import ROOT

from GaugiKernel import Configurable, LoggingLevel



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



