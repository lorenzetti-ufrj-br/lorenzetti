__all__ = [
    "CaloRingsBuilder",
    "CaloRingsBuilderCfg",
    "CaloRingsMakerCfg",
    "StandardRingsMakerCfg",
    "AsymRingsMakerCfg",
    "CrossRingsMakerCfg",
    "CornerRingsMakerCfg",
    "StripsRingsMakerCfg",
    "CustomRingsMakerCfg",
]

from typing import List, Optional
import ROOT

from GaugiKernel import Configurable, LoggingLevel
from CaloRingsTools import (
    StandardRingsToolCfg,
    AsymRingsToolCfg,
    CrossRingsToolCfg,
    CornerRingsToolCfg,
    StripsRingsToolCfg,
    CustomRingsToolCfg,
)


def CaloRingsMakerCfg(
    name: str = "CaloRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings",
    EtaRange: Optional[List[float]] = None,
    HistogramPath: str = "Expert/Rings",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures the base Gaugi::Algorithm CaloRingsMaker.

    :param name: Unique name of the algorithm instance.
    :param InputClusterKey: StoreGate key for input xAOD::CaloClusterContainer.
    :param OutputRingerKey: StoreGate key for output xAOD::CaloRingsContainer.
    :param EtaRange: Acceptance [abs(eta_min), abs(eta_max)] interval.
    :param HistogramPath: Directory path for histogram booking.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable instance of CaloRingsMaker.
    """
    try:
        from RootStreamBuilder import recordable
        recordable(OutputRingerKey, "CaloRingsContainer")
    except Exception:
        pass

    return Configurable(
        ROOT.CaloRingsMaker,
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        EtaRange=EtaRange if EtaRange is not None else [0.0, 2.5],
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )


def StandardRingsMakerCfg(
    name: str = "StandardRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings",
    HistogramPath: str = "Expert/Rings/Standard",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures a CaloRingsMaker coupled with StandardRingsTool for concentric rings.

    :param name: Unique name of the algorithm instance.
    :param InputClusterKey: StoreGate key for input clusters.
    :param OutputRingerKey: StoreGate key for output standard rings container.
    :param HistogramPath: Histogram booking directory.
    :param DoSigmaCut: Whether to apply noise sigma cut on cell energy.
    :param SigmaCut: Cut factor multiplied by cell noise sigma.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable CaloRingsMaker instance with StandardRingsTool attached.
    """
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += StandardRingsToolCfg(
        f"{name}_Tool",
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def AsymRingsMakerCfg(
    name: str = "AsymRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Asym",
    HistogramPath: str = "Expert/Rings/Asym",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures a CaloRingsMaker coupled with AsymRingsTool for 4-quadrant asymmetric rings.

    :param name: Unique name of the algorithm instance.
    :param InputClusterKey: StoreGate key for input clusters.
    :param OutputRingerKey: StoreGate key for output asymmetric rings container.
    :param HistogramPath: Histogram booking directory.
    :param DoSigmaCut: Whether to apply noise sigma cut on cell energy.
    :param SigmaCut: Cut factor multiplied by cell noise sigma.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable CaloRingsMaker instance with AsymRingsTool attached.
    """
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += AsymRingsToolCfg(
        f"{name}_Tool",
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CrossRingsMakerCfg(
    name: str = "CrossRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Cross",
    CrossShift: int = 3,
    HistogramPath: str = "Expert/Rings/Cross",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures a CaloRingsMaker coupled with CrossRingsTool for 4-arm cross pattern rings.

    :param name: Unique name of the algorithm instance.
    :param InputClusterKey: StoreGate key for input clusters.
    :param OutputRingerKey: StoreGate key for output cross rings container.
    :param CrossShift: Cell step shift along cross axes.
    :param HistogramPath: Histogram booking directory.
    :param DoSigmaCut: Whether to apply noise sigma cut on cell energy.
    :param SigmaCut: Cut factor multiplied by cell noise sigma.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable CaloRingsMaker instance with CrossRingsTool attached.
    """
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += CrossRingsToolCfg(
        f"{name}_Tool",
        CrossShift=CrossShift,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CornerRingsMakerCfg(
    name: str = "CornerRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Corner",
    CornerShift: int = 3,
    HistogramPath: str = "Expert/Rings/Corner",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures a CaloRingsMaker coupled with CornerRingsTool for 4 diagonal corner rings.

    :param name: Unique name of the algorithm instance.
    :param InputClusterKey: StoreGate key for input clusters.
    :param OutputRingerKey: StoreGate key for output corner rings container.
    :param CornerShift: Cell step shift along diagonal corners.
    :param HistogramPath: Histogram booking directory.
    :param DoSigmaCut: Whether to apply noise sigma cut on cell energy.
    :param SigmaCut: Cut factor multiplied by cell noise sigma.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable CaloRingsMaker instance with CornerRingsTool attached.
    """
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += CornerRingsToolCfg(
        f"{name}_Tool",
        CornerShift=CornerShift,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def StripsRingsMakerCfg(
    name: str = "StripsRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Strips",
    Axis: int = 0,
    HistogramPath: str = "Expert/Rings/Strips",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures a CaloRingsMaker coupled with StripsRingsTool for 1D strip-projected rings.

    :param name: Unique name of the algorithm instance.
    :param InputClusterKey: StoreGate key for input clusters.
    :param OutputRingerKey: StoreGate key for output strips rings container.
    :param Axis: Projection axis (0 for eta, 1 for phi).
    :param HistogramPath: Histogram booking directory.
    :param DoSigmaCut: Whether to apply noise sigma cut on cell energy.
    :param SigmaCut: Cut factor multiplied by cell noise sigma.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable CaloRingsMaker instance with StripsRingsTool attached.
    """
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += StripsRingsToolCfg(
        f"{name}_Tool",
        Axis=Axis,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CustomRingsMakerCfg(
    name: str = "CustomRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Custom",
    RingsShiftEta: Optional[List[float]] = None,
    RingsShiftPhi: Optional[List[float]] = None,
    HistogramPath: str = "Expert/Rings/Custom",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures a CaloRingsMaker coupled with CustomRingsTool for arbitrary shifted rings.

    :param name: Unique name of the algorithm instance.
    :param InputClusterKey: StoreGate key for input clusters.
    :param OutputRingerKey: StoreGate key for output custom rings container.
    :param RingsShiftEta: Normalized shift offsets in eta.
    :param RingsShiftPhi: Normalized shift offsets in phi.
    :param HistogramPath: Histogram booking directory.
    :param DoSigmaCut: Whether to apply noise sigma cut on cell energy.
    :param SigmaCut: Cut factor multiplied by cell noise sigma.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable CaloRingsMaker instance with CustomRingsTool attached.
    """
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += CustomRingsToolCfg(
        f"{name}_Tool",
        RingsShiftEta=RingsShiftEta,
        RingsShiftPhi=RingsShiftPhi,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CaloRingsBuilderCfg(
    name: str = "CaloRingsBuilder",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    HistogramPath: str = "Expert/Rings",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> List[Configurable]:
    """
    Configures and returns all 6 CaloRingsMaker algorithms by default:
    [Standard, Asym, Cross, Corner, Strips, Custom].

    Instantiates each specialist maker directly with its pre-established configurations
    without branching (if/elif) and returns the list ready to be appended via `acc += rings`.

    :param name: Base prefix name for maker and tool instances.
    :param InputClusterKey: StoreGate key for input xAOD::CaloClusterContainer.
    :param OutputRingerKey: Base StoreGate key for output containers (e.g. Rings, Rings_Asym, etc.).
    :param DoSigmaCut: Whether to apply cell noise sigma threshold cut.
    :param SigmaCut: Multiplicative factor for cell noise sigma threshold.
    :param HistogramPath: Directory path for histogram booking.
    :param OutputLevel: Logging verbosity level.
    :return: List of all 6 configured CaloRingsMaker instances.
    """
    try:
        from RootStreamBuilder import recordable
        recordable(OutputRingerKey, "CaloRingsContainer")
        recordable(f"{OutputRingerKey}_Asym", "CaloRingsContainer")
        recordable(f"{OutputRingerKey}_Cross", "CaloRingsContainer")
        recordable(f"{OutputRingerKey}_Corner", "CaloRingsContainer")
        recordable(f"{OutputRingerKey}_Strips", "CaloRingsContainer")
        recordable(f"{OutputRingerKey}_Custom", "CaloRingsContainer")
    except Exception:
        pass

    return [
        StandardRingsMakerCfg(
            f"{name}_Standard",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=OutputRingerKey,
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Standard",
            OutputLevel=OutputLevel,
        ),
        AsymRingsMakerCfg(
            f"{name}_Asym",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Asym",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Asym",
            OutputLevel=OutputLevel,
        ),
        CrossRingsMakerCfg(
            f"{name}_Cross",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Cross",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Cross",
            OutputLevel=OutputLevel,
        ),
        CornerRingsMakerCfg(
            f"{name}_Corner",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Corner",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Corner",
            OutputLevel=OutputLevel,
        ),
        StripsRingsMakerCfg(
            f"{name}_Strips",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Strips",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Strips",
            OutputLevel=OutputLevel,
        ),
        CustomRingsMakerCfg(
            f"{name}_Custom",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Custom",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Custom",
            OutputLevel=OutputLevel,
        ),
    ]


CaloRingsBuilder = CaloRingsBuilderCfg
