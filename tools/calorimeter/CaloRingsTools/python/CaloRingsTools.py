__all__ = [
    "StandardRingsToolCfg",
    "AsymRingsToolCfg",
    "CrossRingsToolCfg",
    "CornerRingsToolCfg",
    "StripsRingsToolCfg",
    "CustomRingsToolCfg",
]

from typing import List, Optional
import ROOT
import numpy as np

from CaloCell.CaloDefs import CaloSampling
from GaugiKernel import Configurable, LoggingLevel

_PI = float(np.pi)

# Sampling layers definition: 7 calorimeter compartments
_DEFAULT_LAYERS: List[List[int]] = [
    [CaloSampling.PSB, CaloSampling.PSE],
    [CaloSampling.EMB1, CaloSampling.EMEC1],
    [CaloSampling.EMB2, CaloSampling.EMEC2],
    [CaloSampling.EMB3, CaloSampling.EMEC3],
    [CaloSampling.HEC1, CaloSampling.TileCal1, CaloSampling.TileExt1],
    [CaloSampling.HEC2, CaloSampling.TileCal2, CaloSampling.TileExt2],
    [CaloSampling.HEC3, CaloSampling.TileCal3, CaloSampling.TileExt3],
]

_DEFAULT_DELTA_ETA: List[float] = [0.025, 0.00325, 0.025, 0.050, 0.1, 0.1, 0.2]
_DEFAULT_DELTA_PHI: List[float] = [
    _PI / 32.0,
    _PI / 32.0,
    _PI / 128.0,
    _PI / 128.0,
    _PI / 128.0,
    _PI / 32.0,
    _PI / 32.0,
    _PI / 32.0,
]
_DEFAULT_N_RINGS: List[int] = [8, 64, 8, 8, 4, 4, 4]


def StandardRingsToolCfg(
    name: str = "StandardRingsTool",
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures the Gaugi::StandardRingsTool for concentric calorimeter rings.

    :param name: Unique name of the tool instance.
    :param DeltaEtaRings: Ring width in eta per sampling compartment.
    :param DeltaPhiRings: Ring width in phi per sampling compartment.
    :param NRings: Number of concentric rings per sampling compartment.
    :param LayerRings: Calorimeter sampling layer groupings per RingSet.
    :param DoSigmaCut: Whether to discard cells below the noise sigma threshold.
    :param SigmaCut: Multiplicative factor for cell noise sigma threshold.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable instance of Gaugi::StandardRingsTool.
    """
    return Configurable(
        ROOT.Gaugi.StandardRingsTool,
        name,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else list(_DEFAULT_N_RINGS),
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def AsymRingsToolCfg(
    name: str = "AsymRingsTool",
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures the Gaugi::AsymRingsTool for asymmetric rings across 4 quadrants.

    :param name: Unique name of the tool instance.
    :param DeltaEtaRings: Ring width in eta per sampling compartment.
    :param DeltaPhiRings: Ring width in phi per sampling compartment.
    :param NRings: Number of rings per sampling compartment (defaults to (n-1)*4 + 1).
    :param LayerRings: Calorimeter sampling layer groupings per RingSet.
    :param DoSigmaCut: Whether to discard cells below the noise sigma threshold.
    :param SigmaCut: Multiplicative factor for cell noise sigma threshold.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable instance of Gaugi::AsymRingsTool.
    """
    default_asym_rings = [(n - 1) * 4 + 1 for n in _DEFAULT_N_RINGS]
    return Configurable(
        ROOT.Gaugi.AsymRingsTool,
        name,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_asym_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def CrossRingsToolCfg(
    name: str = "CrossRingsTool",
    CrossShift: int = 3,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures the Gaugi::CrossRingsTool for 4-arm cross pattern rings (Top, Bottom, Left, Right).

    :param name: Unique name of the tool instance.
    :param CrossShift: Cell step shift along cross axes.
    :param DeltaEtaRings: Ring width in eta per sampling compartment.
    :param DeltaPhiRings: Ring width in phi per sampling compartment.
    :param NRings: Number of rings per sampling compartment (defaults to n*4).
    :param LayerRings: Calorimeter sampling layer groupings per RingSet.
    :param DoSigmaCut: Whether to discard cells below the noise sigma threshold.
    :param SigmaCut: Multiplicative factor for cell noise sigma threshold.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable instance of Gaugi::CrossRingsTool.
    """
    default_cross_rings = [n * 4 for n in _DEFAULT_N_RINGS]
    return Configurable(
        ROOT.Gaugi.CrossRingsTool,
        name,
        CrossShift=CrossShift,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_cross_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def CornerRingsToolCfg(
    name: str = "CornerRingsTool",
    CornerShift: int = 3,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures the Gaugi::CornerRingsTool for 4 diagonal corner rings (TopRight, TopLeft, BottomLeft, BottomRight).

    :param name: Unique name of the tool instance.
    :param CornerShift: Cell step shift along diagonal corners.
    :param DeltaEtaRings: Ring width in eta per sampling compartment.
    :param DeltaPhiRings: Ring width in phi per sampling compartment.
    :param NRings: Number of rings per sampling compartment (defaults to n*4).
    :param LayerRings: Calorimeter sampling layer groupings per RingSet.
    :param DoSigmaCut: Whether to discard cells below the noise sigma threshold.
    :param SigmaCut: Multiplicative factor for cell noise sigma threshold.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable instance of Gaugi::CornerRingsTool.
    """
    default_corner_rings = [n * 4 for n in _DEFAULT_N_RINGS]
    return Configurable(
        ROOT.Gaugi.CornerRingsTool,
        name,
        CornerShift=CornerShift,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_corner_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def StripsRingsToolCfg(
    name: str = "StripsRingsTool",
    Axis: int = 0,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures the Gaugi::StripsRingsTool for 1D strip-projected rings.

    :param name: Unique name of the tool instance.
    :param Axis: Projection axis (0 for eta strips, 1 for phi strips).
    :param DeltaEtaRings: Ring width in eta per sampling compartment.
    :param DeltaPhiRings: Ring width in phi per sampling compartment.
    :param NRings: Number of strip slices per sampling compartment.
    :param LayerRings: Calorimeter sampling layer groupings per RingSet.
    :param DoSigmaCut: Whether to discard cells below the noise sigma threshold.
    :param SigmaCut: Multiplicative factor for cell noise sigma threshold.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable instance of Gaugi::StripsRingsTool.
    """
    default_strips_rings = [28, 252, 28, 14, 8, 8, 4]
    return Configurable(
        ROOT.Gaugi.StripsRingsTool,
        name,
        Axis=Axis,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_strips_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def CustomRingsToolCfg(
    name: str = "CustomRingsTool",
    RingsShiftEta: Optional[List[float]] = None,
    RingsShiftPhi: Optional[List[float]] = None,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures the Gaugi::CustomRingsTool with arbitrary seed coordinate shift offsets.

    :param name: Unique name of the tool instance.
    :param RingsShiftEta: Normalized shift offsets in eta.
    :param RingsShiftPhi: Normalized shift offsets in phi.
    :param DeltaEtaRings: Ring width in eta per sampling compartment.
    :param DeltaPhiRings: Ring width in phi per sampling compartment.
    :param NRings: Base number of rings per seed per sampling compartment.
    :param LayerRings: Calorimeter sampling layer groupings per RingSet.
    :param DoSigmaCut: Whether to discard cells below the noise sigma threshold.
    :param SigmaCut: Multiplicative factor for cell noise sigma threshold.
    :param OutputLevel: Logging verbosity level.
    :return: Configurable instance of Gaugi::CustomRingsTool.
    """
    return Configurable(
        ROOT.Gaugi.CustomRingsTool,
        name,
        RingsShiftEta=RingsShiftEta if RingsShiftEta is not None else [0.0],
        RingsShiftPhi=RingsShiftPhi if RingsShiftPhi is not None else [0.0],
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else list(_DEFAULT_N_RINGS),
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
