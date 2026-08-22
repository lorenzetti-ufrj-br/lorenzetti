__all__ = ["RootStreamESDMaker"]

import ROOT
from GaugiKernel import Configurable
from GaugiKernel.macros import *
from RootStreamBuilder import RootStreamESDFlags


def RootStreamESDMakerCfg(
    name,
    InputEventKey       : str,
    InputTruthKey       : str,
    InputCellsKey       : str,
    InputSeedsKey       : str,
    InputCellsTruthKey  : str,
    OutputEventKey      : str = None,
    OutputTruthKey      : str = None,
    OutputCellsKey      : str = None,
    OutputSeedsKey      : str = None,
    OutputCellsTruthKey : str = None,
    OutputLevel         : int = 0, 
    NtupleName          : str = "CollectionTree",
    EtaWindow           : float = RootStreamESDFlags.EtaWindow,
    PhiWindow           : float = RootStreamESDFlags.PhiWindow,
) -> Configurable:
    """
    @brief Algorithm to stream ESD Data to a ROOT file.

    ESD contains detailed information including all Calorimeter Cells,
    which makes it larger than AOD but necessary for full reconstruction study.
    This algo serializes the Event Context into a TTree.
    """
    return Configurable(
        ROOT.RootStreamESDMaker,
        name = name,
        InputEventKey       = InputEventKey,
        InputTruthKey       = InputTruthKey,
        InputCellsKey       = InputCellsKey,
        InputSeedsKey       = InputSeedsKey,
        InputCellsTruthKey  = InputCellsTruthKey,
        OutputEventKey      = OutputEventKey if OutputEventKey else InputEventKey,
        OutputTruthKey      = OutputTruthKey if OutputTruthKey else InputTruthKey,
        OutputCellsKey      = OutputCellsKey if OutputCellsKey else InputCellsKey,
        OutputSeedsKey      = OutputSeedsKey if OutputSeedsKey else InputSeedsKey,
        OutputCellsTruthKey = OutputCellsTruthKey if OutputCellsTruthKey else InputCellsTruthKey,
        OutputLevel         = OutputLevel, 
        NtupleName          = NtupleName,
        EtaWindow           = EtaWindow,
        PhiWindow           = PhiWindow,
    )

RootStreamESDMaker = RootStreamESDMakerCfg
