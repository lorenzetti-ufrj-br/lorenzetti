"""
CaloCellBuilder module.

Provides the high-level CaloCellBuilder coordinator class that orchestrates
the complete calorimeter digitization chain across all configured samplings.
"""

from typing import Any, List, Optional
import ROOT

from GaugiKernel import Logger, LoggingLevel, Configurable
from GaugiKernel.macros import MSG_INFO
from CaloCell import CaloSampling, Detector
from CaloCellBuilder.PulsePerturber import PulsePerturberCfg
from CaloCellBuilder.CaloCellMaker import CaloCellMakerCfg
from CaloCellBuilder.CaloFlags import CaloFlags, CrossTalkFlags, AnomalyFlags

__all__ = ["CaloCellBuilder"]


class CaloCellBuilder(Logger):
    """
    A high-level configuration builder for the Calorimeter Digitization chain.

    This class orchestrates the creation of algorithms that transform simulated energy hits
    into reconstructed digital calorimeter cells. It configures:
    - Pulse shape simulation (PulseGenerator)
    - Electronic noise injection
    - Optimal Filtering (OF / COF) for energy/time reconstruction
    - Cross-talk simulation (CrossTalkMaker)
    - Defect/Anomaly injection (PulsePerturber)
    - Merging of cell collections into global CaloCellContainers and master CaloDetDescriptorCollection (CaloCellMerge).
    """

    def __init__(
        self,
        name: str,
        detector: Any,
        HistogramPath: str = "Expert",
        InputHitsKey: str = "Hits",
        OutputCellsKey: str = "Cells",
        OutputTruthCellsKey: str = "TruthCells",
        OutputDescriptorsKey: str = "CaloDetDescriptors",
        InputEventKey: str = "Events",
        FilterBySigma: Optional[bool] = None,
        SigmaThreshold: Optional[float] = None,
        OutputLevel: int = LoggingLevel.toC("INFO"),
    ) -> None:
        """
        Initializes the CaloCellBuilder.

        Args:
            name: Name of the builder instance.
            detector: The detector geometry configuration object containing samplings.
            HistogramPath: Root path in the histogram service for monitoring.
            InputHitsKey: StoreGate key for input hits container.
            OutputCellsKey: StoreGate key for output reconstructed cells container.
            OutputTruthCellsKey: StoreGate key for output truth cells container.
            OutputDescriptorsKey: StoreGate key for master descriptor collection.
            InputEventKey: StoreGate key for event headers.
            FilterBySigma: If True, discards cells with energy <= SigmaThreshold * sigma.
            SigmaThreshold: Multiplier threshold for noise sigma cut (default: 2.0).
            OutputLevel: Logging verbosity level.
        """
        super().__init__(name)
        self.HistogramPath: str = HistogramPath
        self.OutputLevel: int = OutputLevel
        self.InputHitsKey: str = InputHitsKey
        self.InputEventKey: str = InputEventKey
        self.OutputCellsKey: str = OutputCellsKey
        self.OutputTruthCellsKey: str = OutputTruthCellsKey
        self.OutputDescriptorsKey: str = OutputDescriptorsKey
        self.FilterBySigma: bool = CaloFlags.FilterBySigma if FilterBySigma is None else FilterBySigma
        self.SigmaThreshold: float = CaloFlags.SigmaThreshold if SigmaThreshold is None else SigmaThreshold
        self.Detector: Any = detector
        self.OutputCollectionKeys: List[str] = []
        self.RecoAlgs: List[Configurable] = []

    def configure(self) -> None:
        """
        Instantiates and configures all digitization and reconstruction algorithms.

        Iterates over all calorimeter samplings defined in the detector geometry,
        sets up pulse generation, optimal filtering, cross-talk, anomaly injection,
        and finally the master CaloCellMerge algorithm.
        """
        MSG_INFO(self, "Configure CaloCellBuilder.")

        for samp in self.Detector.samplings:
            do_crosstalk: bool = (
                CaloFlags.DoCrossTalk
                and (samp.Sampling == CaloSampling.EMEC2 or samp.Sampling == CaloSampling.EMB2)
            )

            MSG_INFO(
                self,
                f"Create new CaloCellMaker and dump all cells into {samp.CollectionKey} collection",
            )

            pulse: Configurable = Configurable(
                ROOT.PulseGenerator,
                "PulseGenerator",
                NSamples=samp.Samples,
                ShaperFile=samp.Shaper,
                OutputLevel=self.OutputLevel,
                SamplingRate=25.0,
                Pedestal=0.0,
                DeformationMean=0.0,
                DeformationStd=0.0,
                NoiseMean=0.0,
                NoiseStd=samp.Noise,
                StartSamplingBC=samp.StartSamplingBC,
            )

            if CaloFlags.DoCOF and samp.Detector == Detector.TILE:
                of: Configurable = Configurable(
                    ROOT.ConstrainedOptimalFilter,
                    "ConstrainedOptimalFilter",
                    NSamples=samp.Samples,
                    PulsePath=samp.Shaper,
                    Threshold=0,
                    SamplingRate=25.0,
                    StartSamplingBC=samp.StartSamplingBC,
                )
            else:
                of = Configurable(
                    ROOT.OptimalFilter,
                    "OptimalFilter",
                    WeightsEnergy=samp.OFWeightsEnergy,
                    WeightsTime=samp.OFWeightsTime,
                    OutputLevel=self.OutputLevel,
                )

            maker: Configurable = CaloCellMakerCfg(
                f"CaloCellMaker_{samp.CollectionKey}",
                samp,
                InputHitsKey=self.InputHitsKey,
                OutputCollectionKey=(
                    f"{samp.CollectionKey}_Aux" if do_crosstalk else samp.CollectionKey
                ),
                HistogramPath=f"{self.HistogramPath}/{samp.name()}",
                OutputLevel=self.OutputLevel,
                DetailedHistograms=False,
            )

            maker.PulseGenerator = pulse

            if CaloFlags.DoDefects:
                anomaly: Configurable = PulsePerturberCfg(
                    f"PulsePerturber_{samp.CollectionKey}",
                    InputEventKey=self.InputEventKey,
                    NoiseMean=pulse.NoiseMean,
                    NoiseStd=pulse.NoiseStd,
                    BadRunListFile=AnomalyFlags.BadRunListFile,
                )
                maker.Tools += anomaly

            maker.Tools += of
            self.RecoAlgs.append(maker)

            if do_crosstalk:
                cross_talk_cls = getattr(ROOT, "CaloCellCrossTalk", getattr(ROOT, "CrossTalkMaker", None))
                cx: Configurable = Configurable(
                    cross_talk_cls,
                    f"CaloCellCrossTalk_{samp.CollectionKey}",
                    InputCollectionKey=f"{samp.CollectionKey}_Aux",
                    OutputCollectionKey=samp.CollectionKey,
                    MinEnergy=CrossTalkFlags.MinEnergy,
                    AmpCapacitive=CaloFlags.AmpCapacitive,
                    AmpInductive=CaloFlags.AmpInductive,
                    AmpResistive=CaloFlags.AmpResistive,
                    HistogramPath=f"{self.HistogramPath}/CrossTalk",
                    OutputLevel=self.OutputLevel,
                )
                self.RecoAlgs.append(cx)

            self.OutputCollectionKeys.append(samp.CollectionKey)

        # Merge all collections into unified containers and split between truth and reco
        merge: Configurable = Configurable(
            ROOT.CaloCellMerge,
            "CaloCellMerge",
            InputCollectionKeys=self.OutputCollectionKeys,
            OutputTruthCellsKey=self.OutputTruthCellsKey,
            OutputCellsKey=self.OutputCellsKey,
            OutputDescriptorsKey=self.OutputDescriptorsKey,
            FilterBySigma=self.FilterBySigma,
            SigmaThreshold=self.SigmaThreshold,
            OutputLevel=self.OutputLevel,
        )

        self.RecoAlgs.append(merge)

    def merge(self, acc: Any) -> None:
        """
        Configures all algorithms and appends them to the provided ComponentAccumulator.

        Args:
            acc: The ComponentAccumulator instance.
        """
        self.configure()
        for reco in self.RecoAlgs:
            acc += reco
