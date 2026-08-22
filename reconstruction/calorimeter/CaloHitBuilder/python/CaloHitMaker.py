__all__ = ["CaloHitMakerCfg"]

import ROOT

from GaugiKernel import LoggingLevel, Configurable
from GaugiKernel.macros import *



def CaloHitMakerCfg(name, 
                    sampling,
                    OutputCollectionKey : str = "Hits",
                    HistogramPath       : str = "Expert",
                    OutputLevel         : int = LoggingLevel.toC('INFO'),
                    DetailedHistograms  : bool = False,
                    SamplingNoiseStd    : float = 0
  ):
  

  return Configurable(
    ROOT.CaloHitMaker,
    name,
    OutputCollectionKey = OutputCollectionKey,
    HistogramPath = HistogramPath,
    OutputLevel = OutputLevel,
    DetailedHistograms = DetailedHistograms,
    SamplingNoiseStd = SamplingNoiseStd,
    EtaBins = sampling.sensitive().EtaBins,
    PhiBins = sampling.sensitive().PhiBins,
    RMin = sampling.volume().RMin,
    RMax = sampling.volume().RMax,
    ZMin = sampling.volume().ZMin,
    ZMax = sampling.volume().ZMax,
    Sampling = sampling.Sampling,
    Segment = sampling.sensitive().Segment,
    Detector = sampling.Detector,
    BunchIdStart = sampling.BunchIdStart,
    BunchIdEnd = sampling.BunchIdEnd,
    BunchDuration = 25,
  )

