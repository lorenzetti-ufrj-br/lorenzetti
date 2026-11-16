"""
CaloCellMerge configuration helper.

Provides CaloCellMergeCfg to configure ROOT.CaloCellMerge.
"""

from typing import List, Optional
import ROOT

from GaugiKernel import Configurable, LoggingLevel

__all__ = ["CaloCellMergeCfg", "CaloCellMerge"]


def CaloCellMergeCfg(
    name: str = "CaloCellMerge",
    InputCollectionKeys: Optional[List[str]] = None,
    OutputCellsKey: str = "Cells",
    OutputTruthCellsKey: str = "TruthCells",
    OutputDescriptorsKey: str = "CaloDetDescriptors",
    InputHitsKey: str = "",
    FilterBySigma: bool = False,
    SigmaThreshold: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
    **kwargs
) -> Configurable:
    """
    Configures and returns a CaloCellMerge algorithm instance.
    """
    if InputCollectionKeys is None:
        InputCollectionKeys = []

    return Configurable(
        ROOT.CaloCellMerge,
        name,
        InputCollectionKeys=InputCollectionKeys,
        OutputCellsKey=OutputCellsKey,
        OutputTruthCellsKey=OutputTruthCellsKey,
        OutputDescriptorsKey=OutputDescriptorsKey,
        InputHitsKey=InputHitsKey,
        FilterBySigma=FilterBySigma,
        SigmaThreshold=SigmaThreshold,
        OutputLevel=OutputLevel,
        **kwargs
    )


CaloCellMerge = CaloCellMergeCfg
