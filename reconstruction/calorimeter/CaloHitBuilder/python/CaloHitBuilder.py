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
from CaloHitBuilder.CaloHitMaker import CaloHitMakerCfg
from CaloHitBuilder.CaloFreeRunningHitWriter import CaloFreeRunningHitWriter
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
        ActiveEnergyOnly: Optional[bool] = None,
        BirksLaw: Optional[bool] = None,
        AtlasHitTime: Optional[bool] = None,
        TileDualReadout: Optional[int] = None,
        FreeRunningHits: Optional[bool] = None,
        FreeRunningBinning: Optional[bool] = None,
        FreeRunningNtupleName: str = "CollectionTree",
        FreeRunningAtlasFormat: Optional[bool] = None,
        EmecChargeCollection: Optional[bool] = None,
        EmecChargeTables: Optional[str] = None,
        EmecChargeFieldMap: Optional[str] = None,
        EmecChargeHVMap: Optional[str] = None,
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
            ActiveEnergyOnly: Keep only the energy deposited in the active medium.
            BirksLaw: Apply Birks' law in scintillator and liquid argon.
            AtlasHitTime: Bunch crossing from the ATLAS simulation time.
            TileDualReadout: Dual readout of tile cells (0=off, 1=ATLAS U-shape, 2=linear).
            FreeRunningHits: Record calorimeter hits in ATLAS HITS ntuple layout.
            FreeRunningBinning: Sum deposits in time bins of ATLAS simulation.
            FreeRunningNtupleName: Target TTree name for free-running hits.
            FreeRunningAtlasFormat: Filter and compress hits in exact ATLAS HITS format.
            EmecChargeCollection: Enable charge collection physics for the ATLAS EMEC.
            EmecChargeTables: Path to EMEC tables CSV.
            EmecChargeFieldMap: Path to EMEC field map file.
            EmecChargeHVMap: Path to EMEC HV map file.
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
        self.ActiveEnergyOnly: bool = bool(
            CaloHitFlags.ActiveEnergyOnly if ActiveEnergyOnly is None else ActiveEnergyOnly
        )
        self.BirksLaw: bool = bool(
            CaloHitFlags.BirksLaw if BirksLaw is None else BirksLaw
        )
        self.AtlasHitTime: bool = bool(
            CaloHitFlags.AtlasHitTime if AtlasHitTime is None else AtlasHitTime
        )
        if TileDualReadout is None:
            if CaloHitFlags.TileDualReadout:
                self.TileDualReadout: int = 1 if CaloHitFlags.TilePmtSplit == "ushape" else 2
            else:
                self.TileDualReadout: int = 0
        else:
            self.TileDualReadout: int = TileDualReadout

        self.FreeRunningHits: bool = bool(
            FreeRunningFlags.Enable if FreeRunningHits is None else FreeRunningHits
        )
        self.FreeRunningBinning: bool = bool(
            (not FreeRunningFlags.NoBinning)
            if FreeRunningBinning is None
            else FreeRunningBinning
        )
        self.FreeRunningNtupleName: str = FreeRunningNtupleName
        self.FreeRunningAtlasFormat: bool = bool(
            FreeRunningFlags.AtlasFormat
            if FreeRunningAtlasFormat is None
            else FreeRunningAtlasFormat
        )
        self.EmecChargeCollection: bool = bool(
            FreeRunningFlags.EmecChargeCollection
            if EmecChargeCollection is None
            else EmecChargeCollection
        )
        self.EmecChargeTables: str = (
            FreeRunningFlags.EmecTables
            if EmecChargeTables is None
            else EmecChargeTables
        )
        self.EmecChargeFieldMap: str = (
            FreeRunningFlags.EmecFieldMap
            if EmecChargeFieldMap is None
            else EmecChargeFieldMap
        )
        self.EmecChargeHVMap: str = (
            FreeRunningFlags.EmecHVMap
            if EmecChargeHVMap is None
            else EmecChargeHVMap
        )
        self.InputEventKey: str = InputEventKey
        self.OutputCollectionKeys: List[str] = []

    def compile(self, detector_construction: Any) -> None:
        """
        Configures all CaloHitMaker algorithms, the optional CaloFreeRunningHitWriter,
        and the master CaloHitMerge algorithm.
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
                FreeRunningHits=self.FreeRunningHits,
                FreeRunningBinning=self.FreeRunningBinning,
                EmecChargeCollection=self.EmecChargeCollection,
                EmecChargeTables=self.EmecChargeTables,
                EmecChargeFieldMap=self.EmecChargeFieldMap,
                EmecChargeHVMap=self.EmecChargeHVMap,
            )

            self.RecoAlgs.append(alg)
            self.OutputCollectionKeys.append(samp.CollectionKey)

        # ATLAS FCal with its cells (geometry/v2/python/FCAL.py): one maker per module and side
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
                FreeRunningHits=self.FreeRunningHits,
                FreeRunningBinning=self.FreeRunningBinning,
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

        if self.FreeRunningHits:
            MSG_INFO(
                self,
                f"Create CaloFreeRunningHitWriter (tree {self.FreeRunningNtupleName})",
            )
            self.RecoAlgs.append(
                CaloFreeRunningHitWriter(
                    "CaloFreeRunningHitWriter",
                    InputEventKey=self.InputEventKey,
                    NtupleName=self.FreeRunningNtupleName,
                    AtlasFormat=self.FreeRunningAtlasFormat,
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
