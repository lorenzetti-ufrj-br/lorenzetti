
__all__ = ["CaloHitBuilder"]

from GaugiKernel import Logger, LoggingLevel
from GaugiKernel.macros import MSG_INFO
from CaloHitBuilder import CaloHitMaker
from CaloHitBuilder import CaloHitMerge
from G4Kernel import ComponentAccumulator


#
# Calo cell builder
#
class CaloHitBuilder(Logger):

    def __init__(self, 
                 name : str,
                 OutputHitsKey: str,
                 HistogramPath: str = "Expert",
                 OutputLevel: int = LoggingLevel.toC('INFO'),
                 ActiveEnergyOnly: bool = False,
                 BirksLaw: bool = False,
                 AtlasHitTime: bool = False,
                 TileDualReadout: int = 0,
                 InputEventKey: str = "Events",
                 ):

        Logger.__init__(self, name)
        self.__recoAlgs = []
        self.HistogramPath = HistogramPath
        self.OutputLevel = OutputLevel
        self.OutputHitsKey = OutputHitsKey
        self.ActiveEnergyOnly = ActiveEnergyOnly
        self.BirksLaw = BirksLaw
        # Bunch crossing of the hits from the time of the ATLAS simulation (CaloHitMaker::hitTime)
        self.AtlasHitTime = AtlasHitTime
        self.TileDualReadout = TileDualReadout
        self.InputEventKey = InputEventKey
        self.OutputCollectionKeys = []

    def configure(self):

        MSG_INFO(self, "Configure CaloHitBuilder.")

        for samp in self.__detector.samplings:

            MSG_INFO(
                self,
                "Create new CaloHitMaker and dump all hits into %s collection",
                samp.CollectionKey
            )
            histogramPath = self.HistogramPath + '/' + samp.name()
            alg = CaloHitMaker("CaloHitMaker", samp,
                               OutputCollectionKey=samp.CollectionKey,
                               SamplingNoiseStd=samp.Noise,  # TOF selection
                               HistogramPath=histogramPath,
                               OutputLevel=self.OutputLevel,
                               # Use True when debug with only one thread
                               DetailedHistograms=False,
                               ActiveEnergyOnly=self.ActiveEnergyOnly,
                               BirksLaw=self.BirksLaw,
                               AtlasHitTime=self.AtlasHitTime,
                               TileDualReadout=self.TileDualReadout
                               )

            self.__recoAlgs.append(alg)
            self.OutputCollectionKeys.append(samp.CollectionKey)

        # ATLAS FCal with its cells (F41 conserto 22; geometry/python/v2/FCAL.py): one maker per module and side, for the hit
        # collection (one hit per tile, merged with the others)
        for fm in getattr(self.__detector, 'fcal_modules', []):
            MSG_INFO(self, "Create CaloHitMaker for %s and dump all hits into %s collection", fm.Name, fm.CollectionKey)
            self.__recoAlgs.append( CaloHitMaker("CaloHitMaker", fm,
                                                 OutputCollectionKey=fm.CollectionKey,
                                                 HistogramPath=self.HistogramPath + '/' + fm.name(),
                                                 OutputLevel=self.OutputLevel,
                                                 ActiveEnergyOnly=self.ActiveEnergyOnly,
                                                 BirksLaw=self.BirksLaw,
                                                 AtlasHitTime=self.AtlasHitTime) )
            self.OutputCollectionKeys.append(fm.CollectionKey)

        MSG_INFO(
            self,
            "Create CaloHitMerge and dump all hit collections into"
            " %s container",
            "Hits")
        # Merge all collection into a container
        # and split between truth and reco
        mergeAlg = CaloHitMerge("CaloHitMerge",
                                InputCollectionKeys=self.OutputCollectionKeys,
                                OutputHitsKey=self.OutputHitsKey,
                                OutputLevel=self.OutputLevel)
        self.__recoAlgs.append(mergeAlg)

    def merge(self, acc: ComponentAccumulator):
        """
        Obtains the detector from the ComponentAccumulator and appends
        all the hit makers required by the accumulator's detector.

        Parameters
        ----------
        acc : ComponentAccumulator
            Accumulator to merge with
        """

        self.__detector = acc.detector()
        self.configure()
        for reco in self.__recoAlgs:
            acc += reco
