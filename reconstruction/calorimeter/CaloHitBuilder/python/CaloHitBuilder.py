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
        ActiveEnergyOnly: bool = False,
        BirksLaw: bool = False,
        AtlasHitTime: bool = False,
        TileDualReadout: int = 0,
        InputEventKey: str = "Events",
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
            ActiveEnergyOnly: Keep only the energy deposited in the active medium.
            BirksLaw: Apply Birks' law in scintillator and liquid argon.
            AtlasHitTime: Bunch crossing from the ATLAS simulation time.
            TileDualReadout: Dual readout of tile cells (0=off, 1=ATLAS U-shape, 2=linear).
            InputEventKey: StoreGate key for input event headers.
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
        self.ActiveEnergyOnly: bool = ActiveEnergyOnly
        self.BirksLaw: bool = BirksLaw
        self.AtlasHitTime: bool = AtlasHitTime
        self.TileDualReadout: int = TileDualReadout
        self.InputEventKey: str = InputEventKey
        self.OutputCollectionKeys: List[str] = []

    def compile(self, detector_construction: Any) -> None:
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
                ActiveEnergyOnly=self.ActiveEnergyOnly,
                BirksLaw=self.BirksLaw,
                AtlasHitTime=self.AtlasHitTime,
                TileDualReadout=self.TileDualReadout,
            )

            self.RecoAlgs.append(alg)
            self.OutputCollectionKeys.append(samp.CollectionKey)

        # ATLAS FCal with its cells (geometry/python/v2/FCAL.py): one maker per module and side
        for fm in getattr(detector_construction, "fcal_modules", []):
            MSG_INFO(
                self,
                f"Create CaloHitMaker for {fm.Name} and dump all hits into {fm.CollectionKey} collection",
            )
            alg = CaloHitMakerCfg(
                "CaloHitMaker",
                fm,
                OutputCollectionKey=fm.CollectionKey,
                HistogramPath=f"{self.HistogramPath}/{fm.name()}",
                OutputLevel=self.OutputLevel,
                ActiveEnergyOnly=self.ActiveEnergyOnly,
                BirksLaw=self.BirksLaw,
                AtlasHitTime=self.AtlasHitTime,
            )
            self.RecoAlgs.append(alg)
            self.OutputCollectionKeys.append(fm.CollectionKey)

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
        self.compile(acc.detector_construction if hasattr(acc, "detector_construction") else acc.get_detector_construction())
        for reco in self.RecoAlgs:
            acc += reco
