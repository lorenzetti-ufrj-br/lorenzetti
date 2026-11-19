__all__ = [
    "CaloGridCellToolCfg",
    "CaloBirksLawToolCfg",
    "CaloTofCorrectionToolCfg",
    "CaloStandardHitRecorderToolCfg",
    "configure_generic_hit_maker",
]

from typing import Any
import ROOT
from GaugiKernel import Configurable, LoggingLevel


def CaloGridCellToolCfg(
    name: str = "CaloGridCellTool",
    EtaBins: list = None,
    PhiBins: list = None,
    Sampling: int = 0,
    Segment: int = 0,
    Detector: int = 0,
    ZMin: float = 0.0,
    ZMax: float = 0.0,
    RMin: float = 0.0,
    RMax: float = 0.0,
    ActiveEnergyOnly: bool = False,
    BcDuration: float = 25.0,
    BcidStart: int = -7,
    BcidEnd: int = 7,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a CaloGridCellTool instance for universal cylindrical/grid cell mapping.
    """
    kwargs = {
        "Sampling": Sampling,
        "Segment": Segment,
        "Detector": Detector,
        "ZMin": ZMin,
        "ZMax": ZMax,
        "RMin": RMin,
        "RMax": RMax,
        "ActiveEnergyOnly": ActiveEnergyOnly,
        "BcDuration": BcDuration,
        "BcidStart": BcidStart,
        "BcidEnd": BcidEnd,
        "OutputLevel": OutputLevel,
    }
    if EtaBins is not None:
        kwargs["EtaBins"] = EtaBins
    if PhiBins is not None:
        kwargs["PhiBins"] = PhiBins
    return Configurable(ROOT.CaloGridCellTool, name, **kwargs)


def CaloBirksLawToolCfg(
    name: str = "CaloBirksLawTool",
    BirksLArK: float = 0.05832,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a CaloBirksLawTool instance for Birks law energy saturation.
    """
    return Configurable(
        ROOT.CaloBirksLawTool,
        name,
        BirksLArK=BirksLArK,
        OutputLevel=OutputLevel,
    )


def CaloTofCorrectionToolCfg(
    name: str = "CaloTofCorrectionTool",
    ApplyTof: bool = True,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a CaloTofCorrectionTool instance for particle time-of-flight subtraction.
    """
    return Configurable(
        ROOT.CaloTofCorrectionTool,
        name,
        ApplyTof=ApplyTof,
        OutputLevel=OutputLevel,
    )


def CaloStandardHitRecorderToolCfg(
    name: str = "CaloStandardHitRecorderTool",
    OutputCollectionKey: str = "CaloHitCollection",
    NoiseStd: float = 0.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a CaloStandardHitRecorderTool instance for accumulating hits into xAOD::CaloHitCollection.
    """
    return Configurable(
        ROOT.CaloStandardHitRecorderTool,
        name,
        OutputCollectionKey=OutputCollectionKey,
        NoiseStd=NoiseStd,
        OutputLevel=OutputLevel,
    )


def configure_generic_hit_maker(
    name: str,
    sampling: Any,
    OutputCollectionKey: str = "Hits",
    HistogramPath: str = "Expert",
    OutputLevel: int = LoggingLevel.toC("INFO"),
    DetailedHistograms: bool = False,
    SamplingNoiseStd: float = 0.0,
    ActiveEnergyOnly: bool = False,
    BirksLaw: bool = False,
    AtlasHitTime: bool = False,
    **extra_kwargs,
) -> Configurable:
    """
    Configures a generic detector-agnostic CaloHitMaker instance using universal tools.
    Connects tools using += operator for tool lists.
    """
    maker = Configurable(
        ROOT.CaloHitMaker,
        name,
        OutputCollectionKey=OutputCollectionKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DetailedHistograms=DetailedHistograms,
        SamplingNoiseStd=SamplingNoiseStd,
        ActiveEnergyOnly=ActiveEnergyOnly,
    )

    grid_kwargs = {
        "ActiveEnergyOnly": ActiveEnergyOnly,
        "OutputLevel": OutputLevel,
    }
    if hasattr(sampling, "sensitive") and sampling.sensitive() is not None:
        grid_kwargs["EtaBins"] = sampling.sensitive().EtaBins
        grid_kwargs["PhiBins"] = sampling.sensitive().PhiBins
        grid_kwargs["Segment"] = getattr(sampling.sensitive(), "Segment", 0)

    if hasattr(sampling, "volume") and sampling.volume() is not None:
        grid_kwargs["RMin"] = sampling.volume().RMin
        grid_kwargs["RMax"] = sampling.volume().RMax
        grid_kwargs["ZMin"] = sampling.volume().ZMin
        grid_kwargs["ZMax"] = sampling.volume().ZMax

    if hasattr(sampling, "Sampling"):
        grid_kwargs["Sampling"] = sampling.Sampling
    if hasattr(sampling, "Detector"):
        grid_kwargs["Detector"] = sampling.Detector
    if hasattr(sampling, "BunchIdStart"):
        grid_kwargs["BcidStart"] = sampling.BunchIdStart
    if hasattr(sampling, "BunchIdEnd"):
        grid_kwargs["BcidEnd"] = sampling.BunchIdEnd
    grid_kwargs["BcDuration"] = 25.0

    maker.CellIdentifier = CaloGridCellToolCfg(f"{name}_GridCellTool", **grid_kwargs)

    if BirksLaw:
        birks_k = 0.05832
        if hasattr(sampling, "sensitive") and sampling.sensitive() is not None:
            birks_k = getattr(sampling.sensitive(), "BirksLArK", 0.05832) or 0.05832
        maker.EnergyModifiers += CaloBirksLawToolCfg(
            f"{name}_BirksLawTool",
            BirksLArK=birks_k,
            OutputLevel=OutputLevel,
        )

    if AtlasHitTime:
        maker.TimeCorrection = CaloTofCorrectionToolCfg(
            f"{name}_TofCorrectionTool",
            ApplyTof=True,
            OutputLevel=OutputLevel,
        )

    maker.HitRecorders += CaloStandardHitRecorderToolCfg(
        f"{name}_StandardHitRecorderTool",
        OutputCollectionKey=OutputCollectionKey,
        NoiseStd=SamplingNoiseStd,
        OutputLevel=OutputLevel,
    )

    return maker
