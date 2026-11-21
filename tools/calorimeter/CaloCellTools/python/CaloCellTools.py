"""
CaloCellTools configuration helpers.

Provides configuration helpers for calorimeter cell electronics and defect injection tools:
- PulseGeneratorToolCfg (alias PulseGeneratorCfg)
- OptimalFilterToolCfg (alias OptimalFilterCfg)
- ConstrainedOptimalFilterToolCfg (alias ConstrainedOptimalFilterCfg)
- PulsePerturberToolCfg (aliases PulsePerturberCfg, PulsePertuberToolCfg, PulsePertuberCfg)
- get_cells_from_brl
"""

from typing import Any, Dict, List, Optional, Set
import json
import ROOT

from GaugiKernel import Configurable, LoggingLevel

__all__ = [
    "PulseGeneratorToolCfg",
    "PulseGeneratorCfg",
    "OptimalFilterToolCfg",
    "OptimalFilterCfg",
    "ConstrainedOptimalFilterToolCfg",
    "ConstrainedOptimalFilterCfg",
    "PulsePerturberToolCfg",
    "PulsePerturberCfg",
    "PulsePertuberToolCfg",
    "PulsePertuberCfg",
    "get_cells_from_brl",
]


def get_cells_from_brl(path: str) -> Set[int]:
    """
    Parses a Bad Run List (BRL) JSON file and extracts unique cell IDs.

    Args:
        path: Path to the Bad Run List JSON file.

    Returns:
        Set of cell hash identifiers.
    """
    with open(path, "r", encoding="utf-8") as f:
        d: Dict[str, Any] = json.load(f)
        cells: List[int] = []
        for run in d.get("runs", []):
            if not run.get("DeadModules", False):
                cells.extend(run.get("Cells", []))
        return set(cells)


def PulseGeneratorToolCfg(
    name: str = "PulseGeneratorTool",
    NSamples: int = 7,
    ShaperFile: str = "",
    SamplingRate: float = 25.0,
    Pedestal: float = 0.0,
    DeformationMean: float = 0.0,
    DeformationStd: float = 0.0,
    NoiseMean: float = 0.0,
    NoiseStd: float = 0.0,
    StartSamplingBC: int = 0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns a PulseGeneratorTool instance.
    """
    cls = getattr(ROOT, "PulseGeneratorTool", getattr(ROOT, "PulseGenerator", None))
    return Configurable(
        cls,
        name,
        NSamples=NSamples,
        ShaperFile=ShaperFile,
        SamplingRate=SamplingRate,
        Pedestal=Pedestal,
        DeformationMean=DeformationMean,
        DeformationStd=DeformationStd,
        NoiseMean=NoiseMean,
        NoiseStd=NoiseStd,
        StartSamplingBC=StartSamplingBC,
        OutputLevel=OutputLevel,
    )


def OptimalFilterToolCfg(
    name: str = "OptimalFilterTool",
    WeightsEnergy: Optional[List[float]] = None,
    WeightsTime: Optional[List[float]] = None,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns an OptimalFilterTool instance.
    """
    cls = getattr(ROOT, "OptimalFilterTool", getattr(ROOT, "OptimalFilter", None))
    return Configurable(
        cls,
        name,
        WeightsEnergy=WeightsEnergy if WeightsEnergy is not None else [],
        WeightsTime=WeightsTime if WeightsTime is not None else [],
        OutputLevel=OutputLevel,
    )


def ConstrainedOptimalFilterToolCfg(
    name: str = "ConstrainedOptimalFilterTool",
    PulsePath: str = "",
    Threshold: float = 0.0,
    NSamples: int = 0,
    StartSamplingBC: int = 0,
    SamplingRate: float = 25.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns a ConstrainedOptimalFilterTool instance.
    """
    cls = getattr(ROOT, "ConstrainedOptimalFilterTool", getattr(ROOT, "ConstrainedOptimalFilter", None))
    return Configurable(
        cls,
        name,
        PulsePath=PulsePath,
        Threshold=Threshold,
        NSamples=NSamples,
        StartSamplingBC=StartSamplingBC,
        SamplingRate=SamplingRate,
        OutputLevel=OutputLevel,
    )


def PulsePerturberToolCfg(
    name: str = "PulsePerturberTool",
    BadRunListFile: str = "",
    NoiseMean: float = 0.0,
    NoiseStd: float = 0.0,
    InputEventKey: str = "Events",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a PulsePerturberTool instance from a Bad Run List file.
    """
    events: List[List[int]] = []
    dead_modules: List[bool] = []
    noise_factor: List[float] = []
    cells: List[List[int]] = []

    if BadRunListFile:
        with open(BadRunListFile, "r", encoding="utf-8") as f:
            d: Dict[str, Any] = json.load(f)
            for run in d.get("runs", []):
                events.append(run.get("EventRange", []))
                dead_modules.append(run.get("DeadModules", False))
                noise_factor.append(run.get("NoiseStdFactor", 1.0))
                cells.append(run.get("Cells", []))

    cls = getattr(ROOT, "PulsePerturberTool", getattr(ROOT, "PulsePerturber", None))
    return Configurable(
        cls,
        name,
        EventNumberRange=events,
        DeadModules=dead_modules,
        NoiseStdFactor=noise_factor,
        Cells=cells,
        NoiseMean=NoiseMean,
        NoiseStd=NoiseStd,
        InputEventKey=InputEventKey,
        OutputLevel=OutputLevel,
    )


# Backward compatibility aliases
PulseGeneratorCfg = PulseGeneratorToolCfg
OptimalFilterCfg = OptimalFilterToolCfg
ConstrainedOptimalFilterCfg = ConstrainedOptimalFilterToolCfg
PulsePerturberCfg = PulsePerturberToolCfg
PulsePertuberToolCfg = PulsePerturberToolCfg
PulsePertuberCfg = PulsePerturberToolCfg
