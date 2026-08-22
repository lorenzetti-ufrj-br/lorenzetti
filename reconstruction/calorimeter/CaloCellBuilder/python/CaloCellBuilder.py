
__all__ = ["CaloCellBuilder"]

import ROOT

from GaugiKernel        import Logger, LoggingLevel, Configurable
from GaugiKernel.macros import *

from CaloCell           import CaloSampling, Detector
from CaloCellBuilder    import PulsePerturberCfg
from CaloCellBuilder    import OptimalFilter, ConstrainedOptimalFilter
from CaloCellBuilder    import CaloFlags, CrossTalkFlags, AnomalyFlags

#
# Calo cell builder
#
class CaloCellBuilder( Logger ):
  """
  A high-level configuration builder for the Calorimeter Digitization chain.

  This class orchestrates the creation of algorithms that transform energy hits
  into digital signals (cells). It handles:
  - Pulse shape simulation (PulseGenerator)
  - Electronic noise injection
  - Optimal Filtering (OF) for energy/time reconstruction
  - Cross-talk simulation
  - Defect/Anomaly injection
  - Merging of cell collections into a single container.
  """

  def __init__( self, name, 
                      detector,
                      HistogramPath        = "Expert", 
                      InputHitsKey         = "Hits",
                      OutputCellsKey       = "Cells",
                      OutputTruthCellsKey  = "TruthCells",
                      InputEventKey        = "Events",
                      OutputLevel          = LoggingLevel.toC('INFO'),
                      ):
    """
    Initialize the CaloCellBuilder.

    Args:
        name (str): Name of the builder instance.
        detector (DetectorConstruction): The detector geometry configuration object.
        HistogramPath (str): Path in the output ROOT file for monitoring histograms.
        InputHitsKey (str): StoreGate key for input hits.
        OutputCellsKey (str): StoreGate key for output reconstructed cells.
        OutputTruthCellsKey (str): StoreGate key for truth information of cells.
        InputEventKey (str): StoreGate key for event headers.
        OutputLevel (int): Logging verbosity level.
    """

    Logger.__init__(self, name)
    self.HistogramPath       = HistogramPath
    self.OutputLevel         = OutputLevel
    self.InputHitsKey        = InputHitsKey
    self.InputEventKey       = InputEventKey
    self.OutputCellsKey      = OutputCellsKey
    self.OutputTruthCellsKey = OutputTruthCellsKey
    self.Detector            = detector
    self.OutputCollectionKeys= []
    self.RecoAlgs            = []

    
  def configure(self):
    """
    Internal method to instantiate and configure the digitization algorithms.
    
    Iterates over all calorimeter samplings defined in the detector geometry
    and creates specific algorithms (CaloCellMaker) for each. Configures
    pulse generation, optimal filtering, and optional effects like cross-talk
    and anomalies.
    """

    MSG_INFO(self, "Configure CaloCellBuilder.")
  
    for samp in self.Detector.samplings:

      DoCrosstalk = True if CaloFlags.DoCrossTalk and (samp.Sampling == CaloSampling.EMEC2 or samp.Sampling == CaloSampling.EMB2) else False

      print('sampling noise: ', samp.Noise)

      MSG_INFO(self, "Create new CaloCellMaker and dump all cells into %s collection", samp.CollectionKey)

      pulse = Configurable(
        ROOT.PulseGenerator, 
        "PulseGenerator", 
        NSamples        = samp.Samples, 
        ShaperFile      = samp.Shaper,
        OutputLevel     = self.OutputLevel,
        SamplingRate    = 25.0,
        Pedestal        = 0.0,
        DeformationMean = 0.0, 
        DeformationStd  = 0.0,
        NoiseMean       = 0.0,
        NoiseStd        = samp.Noise,
        StartSamplingBC = samp.StartSamplingBC, 
      )
     

      if CaloFlags.DoCOF and samp.Detector == Detector.TILE: 
        of = Configurable(
          ROOT.ConstrainedOptimalFilter, 
          "ConstrainedOptimalFiler",
          NSamples        = samp.Samples,
          PulsePath       = samp.Shaper,
          Threshold       = 0,
          SamplingRate    = 25.0,
          StartSamplingBC = samp.StartSamplingBC,
        )
      else:
        of= Configurable(
          ROOT.OptimalFilter, 
          "OptimalFilter",
          WeightsEnergy  = samp.OFWeightsEnergy,
          WeightsTime    = samp.OFWeightsTime,
          OutputLevel    = self.OutputLevel
        )
    
      maker = Configurable(ROOT.CaloCellMaker,
        "CaloCellMaker_" + samp.CollectionKey, samp,
                            # input key
                            InputHitsKey            =  self.InputHitsKey, # hits
                            # output key
                            OutputCollectionKey     = samp.CollectionKey + "_Aux" if DoCrosstalk else samp.CollectionKey, # descriptors
                            # monitoring configuration
                            HistogramPath           = self.HistogramPath + '/' + samp.name(),
                            OutputLevel             = self.OutputLevel,
                            DetailedHistograms      = False, # Use True when debug with only one thread
                            )
  
      maker.PulseGenerator = pulse # for all cell
      
      if CaloFlags.DoDefects:
          anomaly = PulsePerturberCfg( 
            "PulsePerturber_" + samp.CollectionKey,
            InputEventKey = self.InputEventKey,
            NoiseMean = pulse.NoiseMean,
            NoiseStd = pulse.NoiseStd,
            BadRunListFile = AnomalyFlags.BadRunListFile
          )
          maker.Tools += [anomaly] # for each cel
      
      maker.Tools += [of]  # for each cell
      
      self.RecoAlgs+=[maker]


      if DoCrosstalk:
          cx = Configurable(
            ROOT.CrossTalkMaker,
            "CrossTalkMaker_" + samp.CollectionKey,
            InputCollectionKey    = samp.CollectionKey + "_Aux",
            OutputCollectionKey   = samp.CollectionKey,
            MinEnergy             = CrossTalkFlags.MinEnergy,
            AmpCapacitive         = CaloFlags.AmpCapacitive,
            AmpInductive          = CaloFlags.AmpInductive,
            AmpResistive          = CaloFlags.AmpResistive,
            HistogramPath         = self.HistogramPath + '/CrossTalk',
            OutputLevel           = self.OutputLevel
          )
          self.RecoAlgs+=[cx]

      self.OutputCollectionKeys+=[samp.CollectionKey ]


    # Merge all collection into a container and split between truth and reco
    
    merge = Configurable(
                ROOT.CaloCellMerge,
                "CaloCellMerge" ,
                # input key
                InputCollectionKeys   = self.OutputCollectionKeys, # descriptors
                # output key
                OutputTruthCellsKey   = self.OutputTruthCellsKey , # cells
                OutputCellsKey        = self.OutputCellsKey      , # cells
                # configs
                OutputLevel           = self.OutputLevel 
    )

    self.RecoAlgs+=[merge]


  def merge( self, acc ):
    """
    Merges the configured algorithms into the main ComponentAccumulator.

    Args:
        acc (ComponentAccumulator): The master accumulator to add the algorithms to.
    """
    # configure
    self.configure()
    for reco in self.RecoAlgs:
      acc+=reco 















