
__all__ = ["CaloHitBuilder"]

from GaugiKernel import Logger, LoggingLevel
from GaugiKernel.macros import MSG_INFO
from CaloHitBuilder import CaloHitMaker
from CaloHitBuilder import CaloHitMerge
from CaloHitBuilder import CaloFreeRunningHitWriter
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
                 FreeRunningHits: bool = False,
                 FreeRunningBinning: bool = True,
                 FreeRunningNtupleName: str = "CollectionTree",
                 FreeRunningAtlasFormat: bool = False,
                 EmecChargeCollection: bool = False,
                 EmecChargeTables: str = "",
                 EmecChargeFieldMap: str = "",
                 EmecChargeHVMap: str = "",
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
        # Free-running hits: the deposits of the ATLAS cells also go to a list (per PMT in the tile, per cell in the LAr and the FCal)
        # written in the layout of the ATLAS HITS ntuple (CaloFreeRunningHitWriter, tree FreeRunningNtupleName); see
        # CaloHitMaker::freeRunningTile, freeRunningLAr and fcalStep.
        self.FreeRunningHits = FreeRunningHits
        self.FreeRunningBinning = FreeRunningBinning
        self.FreeRunningNtupleName = FreeRunningNtupleName
        self.FreeRunningAtlasFormat = FreeRunningAtlasFormat
        # Charge collection of the ATLAS EM end-cap in the free-running hits of the EMEC (F41 conserto 29; CaloHitMaker::emecChargeEnergy)
        self.EmecChargeCollection = EmecChargeCollection
        self.EmecChargeTables = EmecChargeTables
        self.EmecChargeFieldMap = EmecChargeFieldMap
        self.EmecChargeHVMap = EmecChargeHVMap
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
                               TileDualReadout=self.TileDualReadout,
                               FreeRunningHits=self.FreeRunningHits,
                               FreeRunningBinning=self.FreeRunningBinning,
                               EmecChargeCollection=self.EmecChargeCollection,
                               EmecChargeTables=self.EmecChargeTables,
                               EmecChargeFieldMap=self.EmecChargeFieldMap,
                               EmecChargeHVMap=self.EmecChargeHVMap
                               )

            self.__recoAlgs.append(alg)
            self.OutputCollectionKeys.append(samp.CollectionKey)

        # ATLAS FCal with its cells (F41 conserto 22; geometry/python/v2/FCAL.py): one maker per module and side, for the hit
        # collection (one hit per tile, merged with the others) and, with FreeRunningHits, the free-running hits
        for fm in getattr(self.__detector, 'fcal_modules', []):
            MSG_INFO(self, "Create CaloHitMaker for %s and dump all hits into %s collection", fm.Name, fm.CollectionKey)
            self.__recoAlgs.append( CaloHitMaker("CaloHitMaker", fm,
                                                 OutputCollectionKey=fm.CollectionKey,
                                                 HistogramPath=self.HistogramPath + '/' + fm.name(),
                                                 OutputLevel=self.OutputLevel,
                                                 ActiveEnergyOnly=self.ActiveEnergyOnly,
                                                 BirksLaw=self.BirksLaw,
                                                 AtlasHitTime=self.AtlasHitTime,
                                                 FreeRunningHits=self.FreeRunningHits,
                                                 FreeRunningBinning=self.FreeRunningBinning) )
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

        if self.FreeRunningHits:
            MSG_INFO(self, "Create CaloFreeRunningHitWriter (tree %s)", self.FreeRunningNtupleName)
            self.__recoAlgs.append( CaloFreeRunningHitWriter("CaloFreeRunningHitWriter",
                                                             InputEventKey=self.InputEventKey,
                                                             NtupleName=self.FreeRunningNtupleName,
                                                             AtlasFormat=self.FreeRunningAtlasFormat,
                                                             OutputLevel=self.OutputLevel) )

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
