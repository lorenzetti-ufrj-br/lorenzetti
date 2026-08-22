__all__ = ["RootStreamAODMaker"]

import ROOT
from typing import List
from GaugiKernel import Configurable
from RootStreamBuilder import RootStreamAODFlags



def RootStreamAODMakerCfg(
    name,
    InputEventKey          : str,
    InputTruthKey          : str,
    InputCellsKey          : str,
    InputClusterKey        : str,
    InputRingerKeys        : List[str],
    InputElectronKey       : str,
    InputTruthCellsKey     : str,
    InputTruthClusterKey   : str,
    InputTruthRingerKeys   : List[str],
    InputTruthElectronKey  : str,
    OutputEventKey         : str = None,
    OutputTruthKey         : str = None,
    OutputCellsKey         : str = None,
    OutputClusterKey       : str = None,
    OutputRingerKeys       : List[str] = None,
    OutputElectronKey      : str = None,
    OutputTruthCellsKey    : str = None,
    OutputTruthClusterKey  : str = None,
    OutputTruthRingerKeys  : List[str] = None,
    OutputTruthElectronKey : str = None,
    OutputLevel            : int = 0,
    NtupleName             : str = "CollectionTree",
    DumpCells              : bool = RootStreamAODFlags.DumpCells,
) -> Configurable:

    return Configurable(
        ROOT.RootStreamAODMaker,
        name = name,
        InputEventKey        = InputEventKey,
        InputTruthKey        = InputTruthKey,
        InputCellsKey        = InputCellsKey,
        InputClusterKey      = InputClusterKey,
        InputRingerKeys      = InputRingerKeys,
        InputElectronKey     = InputElectronKey,
        InputTruthCellsKey   = InputTruthCellsKey,
        InputTruthClusterKey = InputTruthClusterKey,
        InputTruthRingerKeys = InputTruthRingerKeys,
        InputTruthElectronKey= InputTruthElectronKey,
        OutputEventKey       = OutputEventKey if OutputEventKey else InputEventKey,
        OutputTruthKey       = OutputTruthKey if OutputTruthKey else InputTruthKey,
        OutputCellsKey       = OutputCellsKey if OutputCellsKey else InputCellsKey,
        OutputClusterKey     = OutputClusterKey if OutputClusterKey else InputClusterKey,
        OutputRingerKeys     = OutputRingerKeys if OutputRingerKeys else InputRingerKeys,
        OutputElectronKey    = OutputElectronKey if OutputElectronKey else InputElectronKey,
        OutputTruthCellsKey  = OutputTruthCellsKey if OutputTruthCellsKey else InputTruthCellsKey,
        OutputTruthClusterKey= OutputTruthClusterKey if OutputTruthClusterKey else InputTruthClusterKey,
        OutputTruthRingerKeys= OutputTruthRingerKeys if OutputTruthRingerKeys else InputTruthRingerKeys,
        OutputTruthElectronKey= OutputTruthElectronKey if OutputTruthElectronKey else InputTruthElectronKey,
        OutputLevel        = OutputLevel,
        NtupleName         = NtupleName,
        DumpCells          = DumpCells,
    )

RootStreamAODMaker = RootStreamAODMakerCfg