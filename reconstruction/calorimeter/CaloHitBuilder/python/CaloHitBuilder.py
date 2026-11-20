"""
CaloHitBuilder module.

Provides the CaloHitBuilder coordinator class that creates and attaches
sampling-level CaloHitMaker algorithms, the optional CaloFreeRunningHitWriter,
and the master CaloHitMerge algorithm to the simulation ComponentAccumulator.
"""

from typing import Any, List, Optional
import ROOT

from GaugiKernel import Logger, LoggingLevel, Configurable
from GaugiKernel.macros import MSG_INFO
from CaloHitBuilder.CaloHitFlags import CaloHitFlags, FreeRunningFlags
from G4Kernel import ComponentAccumulator

__all__ = ["CaloHitBuilder"]


class CaloHitBuilder(Logger):
    """
    Coordinator class to set up calorimeter hit creation and merging.

    Iterates over all detector samplings configured in the detector description,
    spawns a CaloHitMaker instance per sampling, and appends a CaloHitMerge
    algorithm to combine all sampling collections into a unified CaloHitContainer.
    Optionally attaches CaloFreeRunningHitWriter for ATLAS free-running hits.
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
        flags: Optional[CaloHitFlags] = None,
        fr_flags: Optional[FreeRunningFlags] = None,
        FreeRunningNtupleName: str = "CollectionTree",
        InputEventKey: str = "Events",
    ) -> None:
        """
        Initializes the CaloHitBuilder.

        Args:
            name: Name of the builder instance.
            OutputHitsKey: StoreGate key for the output merged CaloHitContainer.
            OnlyRoI: Enable Region of Interest (RoI) hit filtering around truth particles.
            EtaWindow: Eta window size for RoI matching.
            PhiWindow: Phi window size for RoI matching.
            TruthKey: StoreGate key for truth particles used in RoI matching.
            CellHashes: Specific detector cell hashes to retain regardless of RoI.
            FilterEmptyHits: Flag to filter out hits with energy <= MinEnergy.
            MinEnergy: Minimum energy threshold for hit retention in MeV.
            HistogramPath: Root path for monitoring histograms.
            OutputLevel: Logging verbosity level.
            flags: CaloHitFlags configuration instance (defaults to global CaloHitFlags).
            fr_flags: FreeRunningFlags configuration instance (defaults to global FreeRunningFlags).
            FreeRunningNtupleName: Target TTree name for free-running hits.
            InputEventKey: StoreGate key for input event headers.
        """
        super().__init__(name)
        self.flags: CaloHitFlags = flags if flags is not None else CaloHitFlags
        self.fr_flags: FreeRunningFlags = fr_flags if fr_flags is not None else FreeRunningFlags
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
        self.FreeRunningNtupleName: str = FreeRunningNtupleName
        self.InputEventKey: str = InputEventKey
        self.OutputCollectionKeys: List[str] = []

    def compile(self, detector_construction: Any) -> None:
        """
        Configures all CaloHitMaker algorithms, the optional CaloFreeRunningHitWriter,
        and the master CaloHitMerge algorithm.
        """
        MSG_INFO(self, "Configure CaloHitBuilder.")

        is_v2 = (
            "v2" in detector_construction.__class__.__name__.lower()
            or getattr(detector_construction, "version", "").lower() == "v2"
        )

        if is_v2:
            from CaloHitBuilder.CaloHitMaker import AtlasCaloHitMakerCfg as CaloHitMaker
        else:
            from CaloHitBuilder.CaloHitMaker import CaloHitMakerCfg as CaloHitMaker

        for samp in detector_construction.samplings:
            MSG_INFO(
                self,
                f"Create new CaloHitMaker and dump all hits into {samp.CollectionKey}",
            )

            histogramPath: str = f"{self.HistogramPath}/{samp.name()}"
            alg: Configurable = CaloHitMaker(
                "CaloHitMaker",
                samp,
                flags=self.flags,
                fr_flags=self.fr_flags,
                OutputCollectionKey=samp.CollectionKey,
                SamplingNoiseStd=samp.Noise,
                HistogramPath=histogramPath,
                OutputLevel=self.OutputLevel,
                DetailedHistograms=False,
            )

            self.RecoAlgs.append(alg)
            self.OutputCollectionKeys.append(samp.CollectionKey)

        # ATLAS FCal with its cells (GeoV2/python/detectors/FCAL.py): one maker per module and side
        if is_v2:
            for fm in getattr(detector_construction, "fcal_modules", []):
                MSG_INFO(
                    self,
                    f"Create CaloHitMaker for {fm.Name} and dump all hits into {fm.CollectionKey} collection",
                )
                alg = CaloHitMaker(
                    "CaloHitMaker",
                    fm,
                    flags=self.flags,
                    fr_flags=self.fr_flags,
                    OutputCollectionKey=fm.CollectionKey,
                    HistogramPath=f"{self.HistogramPath}/{fm.name()}",
                    OutputLevel=self.OutputLevel,
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

        if self.fr_flags.Enable:
            from AtlasCaloHitBuilderTools import CaloFreeRunningHitWriter
            MSG_INFO(
                self,
                f"Create CaloFreeRunningHitWriter (tree {self.FreeRunningNtupleName})",
            )
            self.RecoAlgs.append(
                CaloFreeRunningHitWriter(
                    "CaloFreeRunningHitWriter",
                    InputEventKey=self.InputEventKey,
                    NtupleName=self.FreeRunningNtupleName,
                    AtlasFormat=self.fr_flags.AtlasFormat,
                    OutputLevel=self.OutputLevel,
                )
            )

    def merge(self, acc: ComponentAccumulator) -> None:
        """
        Obtains the detector description from the ComponentAccumulator,
        configures the hit maker/merger algorithms, and appends them to the accumulator.

        Args:
            acc: The ComponentAccumulator to merge with.
        """
        self.compile(
            acc.detector_construction
            if hasattr(acc, "detector_construction")
            else acc.get_detector_construction()
        )
        for reco in self.RecoAlgs:
            acc += reco
