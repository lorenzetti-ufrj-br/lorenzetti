
__all__ = ["CaloHitBuilder"]

import ROOT


from GaugiKernel import Logger, LoggingLevel, Configurable
from GaugiKernel.macros import MSG_INFO
from CaloHitBuilder import CaloHitMakerCfg
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
                 ):

        Logger.__init__(self, name)
        self.RecoAlgs = []
        self.HistogramPath = HistogramPath
        self.OutputLevel = OutputLevel
        self.OutputHitsKey = OutputHitsKey
        self.OutputCollectionKeys = []

    def configure(self):

        MSG_INFO(self, "Configure CaloHitBuilder.")

        for samp in self.__detector.samplings:

            MSG_INFO(
                self,
                f"Create new CaloHitMaker and dump all hits into {samp.CollectionKey}")
                
            histogramPath = self.HistogramPath + '/' + samp.name()
            alg = CaloHitMakerCfg(
                "CaloHitMaker", 
                samp,
                OutputCollectionKey=samp.CollectionKey,
                SamplingNoiseStd=samp.Noise,  # TOF selection
                HistogramPath=histogramPath,
                OutputLevel=self.OutputLevel,
                # Use True when debug with only one thread
                DetailedHistograms=False
                )

            self.RecoAlgs.append(alg)
            self.OutputCollectionKeys.append(samp.CollectionKey)

        MSG_INFO(
            self,
            f"Create CaloHitMerge and dump all hit collections into"
            f" {self.OutputHitsKey} container")

        # Merge all collection into a container
        # and split between truth and reco
        mergeAlg = Configurable(
            ROOT.CaloHitMerge,
            "CaloHitMerge",
            InputCollectionKeys=self.OutputCollectionKeys,
            OutputHitsKey=self.OutputHitsKey,
            OutputLevel=self.OutputLevel
        )

        self.RecoAlgs.append(mergeAlg)

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
