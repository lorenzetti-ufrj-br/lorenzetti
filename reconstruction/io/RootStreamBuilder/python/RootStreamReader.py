__all__ = [
    "RootStreamReader",
    "RootStreamReaderCfg",
    "RootStreamAODReader",
    "RootStreamAODReaderCfg",
    "RootStreamESDReader",
    "RootStreamESDReaderCfg",
    "RootStreamHITReader",
    "RootStreamHITReaderCfg",
]

import ROOT
from typing import Optional
from GaugiKernel import Configurable


def RootStreamReaderCfg(
    name: str = "RootStreamReader",
    InputFile: str = "",
    TreeName: str = "CollectionTree",
    OutputCellsKey: str = "",
    OutputHitsKey: str = "",
    OutputEventKey: str = "",
    OutputTruthKey: str = "",
    OutputSeedsKey: str = "",
    OutputLevel: int = 0,
    **kwargs,
) -> Configurable:
    """
    Creates an auto-discovery RootStreamReader algorithm.
    It inspects all <TypeName>_<Key> branches from the input ROOT TTree,
    instantiates the matching converters, and reconstructs the xAOD containers
    directly into the EventContext with their respective keys.

    :param name: Algorithm name.
    :param InputFile: Path to input ROOT file (optional if managed by EventLoop).
    :param TreeName: Name of the TTree inside the ROOT file.
    :param OutputCellsKey: Override StoreGate key for cells (e.g. 'Cells_original').
    :param OutputHitsKey: Override StoreGate key for hits.
    :param OutputEventKey: Override StoreGate key for events.
    :param OutputTruthKey: Override StoreGate key for truth particles.
    :param OutputSeedsKey: Override StoreGate key for seeds.
    :param OutputLevel: Verbosity level (0=INFO, 1=DEBUG, etc.).
    """
    return Configurable(
        ROOT.RootStreamReader,
        name=name,
        InputFile=InputFile,
        TreeName=TreeName,
        OutputCellsKey=OutputCellsKey,
        OutputHitsKey=OutputHitsKey,
        OutputEventKey=OutputEventKey,
        OutputTruthKey=OutputTruthKey,
        OutputSeedsKey=OutputSeedsKey,
        OutputLevel=OutputLevel,
    )


RootStreamReader = RootStreamReaderCfg


def RootStreamAODReaderCfg(
    name: str = "RootStreamAODReader",
    InputFile: str = "",
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    **kwargs,
) -> Configurable:
    """
    Auto-discovery reader preset for AOD files (compatible with legacy scripts).
    """
    return RootStreamReaderCfg(
        name=name,
        InputFile=InputFile,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
        **kwargs,
    )


RootStreamAODReader = RootStreamAODReaderCfg


def RootStreamESDReaderCfg(
    name: str = "RootStreamESDReader",
    InputFile: str = "",
    TreeName: str = "CollectionTree",
    OutputCellsKey: str = "",
    OutputCellsTruthKey: str = "",
    OutputEventKey: str = "",
    OutputTruthKey: str = "",
    OutputSeedsKey: str = "",
    OutputLevel: int = 0,
    **kwargs,
) -> Configurable:
    """
    Auto-discovery reader preset for ESD files (compatible with legacy scripts).
    """
    return RootStreamReaderCfg(
        name=name,
        InputFile=InputFile,
        TreeName=TreeName,
        OutputCellsKey=OutputCellsKey,
        OutputEventKey=OutputEventKey,
        OutputTruthKey=OutputTruthKey,
        OutputSeedsKey=OutputSeedsKey,
        OutputLevel=OutputLevel,
        **kwargs,
    )


RootStreamESDReader = RootStreamESDReaderCfg


def RootStreamHITReaderCfg(
    name: str = "RootStreamHITReader",
    InputFile: str = "",
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    **_kwargs,
) -> Configurable:
    """
    Auto-discovery reader preset for HIT files (compatible with legacy scripts).
    """
    return RootStreamReaderCfg(
        name=name,
        InputFile=InputFile,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
    )


RootStreamHITReader = RootStreamHITReaderCfg
