
__all__ = ["CaloCellBuilder"]

from GaugiKernel        import Logger, LoggingLevel
from GaugiKernel.macros import *

from CaloCell           import CaloSampling, Detector
from CaloCellBuilder    import CaloCellMaker
from CaloCellBuilder    import CaloCellMerge
from CaloCellBuilder    import CrossTalkMaker
from CaloCellBuilder    import PulseGenerator
from CaloCellBuilder    import AnomalyGenerator
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
    self.__recoAlgs = []
    self.HistogramPath       = HistogramPath
    self.OutputLevel         = OutputLevel
    self.InputHitsKey        = InputHitsKey
    self.InputEventKey       = InputEventKey
    self.OutputCellsKey      = OutputCellsKey
    self.OutputTruthCellsKey = OutputTruthCellsKey
    self.Detector            = detector
    self.OutputCollectionKeys= []

    
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
      pulse = PulseGenerator( "PulseGenerator", 
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
        of = ConstrainedOptimalFilter("ConstrainedOptimalFiler",
                                      NSamples  = samp.Samples,
                                      PulsePath = samp.Shaper,
                                      Threshold = 0,
                                      SamplingRate = 25.0,
                                      StartSamplingBC = samp.StartSamplingBC,
                                      )
      else:
        of= OptimalFilter("OptimalFilter",
                        WeightsEnergy  = samp.OFWeightsEnergy,
                        WeightsTime    = samp.OFWeightsTime,
                        OutputLevel=self.OutputLevel)
    
      alg = CaloCellMaker("CaloCellMaker_" + samp.CollectionKey, samp,
                            # input key
                            InputHitsKey            =  self.InputHitsKey, # hits
                            # output key
                            OutputCollectionKey     = samp.CollectionKey + "_Aux" if DoCrosstalk else samp.CollectionKey, # descriptors
                            # monitoring configuration
                            HistogramPath           = self.HistogramPath + '/' + samp.name(),
                            OutputLevel             = self.OutputLevel,
                            DetailedHistograms      = False, # Use True when debug with only one thread
                            )
  
      alg.PulseGenerator = pulse # for all cell
      
      if CaloFlags.DoDefects:
          anomaly = AnomalyGenerator( "AnomalyGenerator_" + samp.CollectionKey,
                                     InputEventKey = self.InputEventKey,
                                     NoiseMean = pulse.NoiseMean,
                                     NoiseStd = pulse.NoiseStd,
                                     BadRunListFile = AnomalyFlags.BadRunListFile)
          alg.Tools.append(anomaly) # for each cel
      
      alg.Tools.append( of )  # for each cell
      
      
      self.__recoAlgs.append( alg )


      if DoCrosstalk:
          cx = CrossTalkMaker( "CrossTalkMaker_" + samp.CollectionKey,
                                InputCollectionKey    = samp.CollectionKey + "_Aux",
                                OutputCollectionKey   = samp.CollectionKey,
                                MinEnergy             = CrossTalkFlags.MinEnergy,
                                AmpCapacitive         = CaloFlags.AmpCapacitive,
                                AmpInductive          = CaloFlags.AmpInductive,
                                AmpResistive          = CaloFlags.AmpResistive,
                                HistogramPath         = self.HistogramPath + '/CrossTalk',
                                OutputLevel           = self.OutputLevel
                             )
          cx.Tools = [of]
          self.__recoAlgs.append( cx )



      self.OutputCollectionKeys.append( samp.CollectionKey )



    MSG_INFO(self, "Create CaloCellMerge and dump all cell collections into %s container", "Cells")
    # Merge all collection into a container and split between truth and reco
    mergeAlg = CaloCellMerge( "CaloCellMerge" , 
                              # input key
                              InputCollectionKeys   = self.OutputCollectionKeys, # descriptors
                              # output key
                              OutputTruthCellsKey   = self.OutputTruthCellsKey , # cells
                              OutputCellsKey        = self.OutputCellsKey      , # cells
                              # configs
                              OutputLevel           = self.OutputLevel )

    self.__recoAlgs.append( mergeAlg )


  def merge( self, acc ):
    """
    Merges the configured algorithms into the main ComponentAccumulator.

    Args:
        acc (ComponentAccumulator): The master accumulator to add the algorithms to.
    """
    # configure
    self.configure()
    for reco in self.__recoAlgs:
      acc+=reco 















