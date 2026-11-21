__all__ = [
    "CaloGridCellToolCfg",
    "CaloBirksLawToolCfg",
    "CaloTofCorrectionToolCfg",
    "CaloStandardHitRecorderToolCfg",
]

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
    Passes properties directly to the Configurable.
    """
    return Configurable(
        ROOT.CaloGridCellTool,
        name,
        EtaBins=EtaBins if EtaBins is not None else [],
        PhiBins=PhiBins if PhiBins is not None else [],
        Sampling=Sampling,
        Segment=Segment,
        Detector=Detector,
        ZMin=ZMin,
        ZMax=ZMax,
        RMin=RMin,
        RMax=RMax,
        ActiveEnergyOnly=ActiveEnergyOnly,
        BcDuration=BcDuration,
        BcidStart=BcidStart,
        BcidEnd=BcidEnd,
        OutputLevel=OutputLevel,
    )


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

