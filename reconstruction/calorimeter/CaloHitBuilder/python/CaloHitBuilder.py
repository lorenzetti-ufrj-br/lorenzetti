"""
CaloHitBuilder module.

Provides the CaloHitBuilder coordinator class that creates and attaches
sampling-level CaloHitMaker algorithms and the master CaloHitMerge algorithm
to the simulation ComponentAccumulator.
"""

from typing import Any, List, Optional
import ROOT

from GaugiKernel import Logger, LoggingLevel, Configurable
from GaugiKernel.macros import MSG_INFO
from CaloHitBuilder.CaloHitMaker import CaloHitMakerCfg
from G4Kernel import ComponentAccumulator

__all__ = ["CaloHitBuilder"]


class CaloHitBuilder(Logger):
    """
    Coordinator class to set up calorimeter hit creation and merging.

    Iterates over all detector samplings configured in the detector description,
    spawns a CaloHitMaker instance per sampling, and appends a CaloHitMerge
    algorithm to combine all sampling collections into a unified CaloHitContainer.
    """

    def __init__(
        self,
        name: str,
        OutputHitsKey: str = "Hits",
        OnlyRoI: bool = False,
        EtaWindow: float = 0.4,
        PhiWindow: float = 0.4,
        TruthKey: str = "Particles",
        CellHashes: Optional[List[int]] = None,
        FilterEmptyHits: bool = False,
        MinEnergy: float = 0.0,
        HistogramPath: str = "Expert",
        OutputLevel: int = LoggingLevel.toC("INFO"),
    ) -> None:
        """
        Initializes the CaloHitBuilder.

        Args:
            name: Name of the builder instance.
            OutputHitsKey: StoreGate key for the output merged CaloHitContainer.
            OnlyRoI: Enable Region of Interest (RoI) hit filtering around truth particles (default False).
            EtaWindow: Eta window size for RoI matching.
            PhiWindow: Phi window size for RoI matching.
            TruthKey: StoreGate key for truth particles used in RoI matching.
            CellHashes: Specific detector cell hashes to retain regardless of RoI.
            FilterEmptyHits: Flag to filter out hits with energy <= MinEnergy.
            MinEnergy: Minimum energy threshold for hit retention in MeV.
            HistogramPath: Root path for monitoring histograms.
            OutputLevel: Logging verbosity level.
        """
        super().__init__(name)
        self.RecoAlgs: List[Configurable] = []
        self.HistogramPath: str = HistogramPath
        self.OutputLevel: int = OutputLevel
        self.OutputHitsKey: str = OutputHitsKey
        self.OnlyRoI: bool = OnlyRoI
        self.EtaWindow: float = EtaWindow
        self.PhiWindow: float = PhiWindow
        self.TruthKey: str = TruthKey
        self.CellHashes: Optional[List[int]] = CellHashes
        self.FilterEmptyHits: bool = FilterEmptyHits
        self.MinEnergy: float = MinEnergy
        self.OutputCollectionKeys: List[str] = []

    def compile(self, detector_construction: Configurable) -> None:
        """
        Configures all CaloHitMaker algorithms and the CaloHitMerge algorithm.
        """
        MSG_INFO(self, "Configure CaloHitBuilder.")

        for samp in detector_construction.samplings:
            MSG_INFO(
                self,
                f"Create new CaloHitMaker and dump all hits into {samp.CollectionKey}",
            )

            histogramPath: str = f"{self.HistogramPath}/{samp.name()}"
            alg: Configurable = CaloHitMakerCfg(
                "CaloHitMaker",
                samp,
                OutputCollectionKey=samp.CollectionKey,
                SamplingNoiseStd=samp.Noise,
                HistogramPath=histogramPath,
                OutputLevel=self.OutputLevel,
                DetailedHistograms=False,
            )

            self.RecoAlgs.append(alg)
            self.OutputCollectionKeys.append(samp.CollectionKey)

        MSG_INFO(
            self,
            f"Create CaloHitMerge and dump all hit collections into {self.OutputHitsKey} container",
        )

        # Merge all collections into a master container
        mergeAlg: Configurable = Configurable(
            ROOT.CaloHitMerge,
            "CaloHitMerge",
            InputCollectionKeys=self.OutputCollectionKeys,
            OutputHitsKey=self.OutputHitsKey,
            OnlyRoI=self.OnlyRoI,
            EtaWindow=self.EtaWindow,
            PhiWindow=self.PhiWindow,
            TruthKey=self.TruthKey,
            CellHashes=self.CellHashes if self.CellHashes is not None else [],
            FilterEmptyHits=self.FilterEmptyHits,
            MinEnergy=self.MinEnergy,
            OutputLevel=self.OutputLevel,
        )

        self.RecoAlgs.append(mergeAlg)

    def merge(self, acc: ComponentAccumulator) -> None:
        """
        Obtains the detector description from the ComponentAccumulator,
        configures the hit maker/merger algorithms, and appends them to the accumulator.

        Args:
            acc: The ComponentAccumulator to merge with.
        """
        self.compile(acc.get_detector_construction())
        for reco in self.RecoAlgs:
            acc += reco
