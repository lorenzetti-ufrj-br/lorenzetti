__all__ = ["RootStreamHITMaker"]

import ROOT
from typing import List
from GaugiKernel import Configurable
from GaugiKernel.macros import *
from RootStreamBuilder import RootStreamHITFlags


def RootStreamHITMakerCfg(
    name,
    InputEventKey    : str,
    InputTruthKey    : str,
    InputHitsKey     : str,
    InputSeedsKey    : str,               
    OutputEventKey   : str = None,
    OutputTruthKey   : str = None,
    OutputHitsKey    : str = None,
    OutputSeedsKey   : str = None,
    OutputLevel      : int = 0, 
    NtupleName       : str = "CollectionTree",
    OnlyRoI          : bool = RootStreamHITFlags.OnlyRoI,
    EtaWindow        : float = RootStreamHITFlags.EtaWindow,
    PhiWindow        : float = RootStreamHITFlags.PhiWindow,
    KeepCells        : List[int] = None,
) -> Configurable:
        
    return Configurable(
        ROOT.RootStreamHITMaker, 
        name,
        InputEventKey      = InputEventKey,
        InputTruthKey      = InputTruthKey,
        InputHitsKey       = InputHitsKey,
        InputSeedsKey      = InputSeedsKey,
        OutputEventKey     = OutputEventKey if OutputEventKey else InputEventKey,
        OutputTruthKey     = OutputTruthKey if OutputTruthKey else InputTruthKey,
        OutputHitsKey      = OutputHitsKey if OutputHitsKey else InputHitsKey,
        OutputSeedsKey     = OutputSeedsKey if OutputSeedsKey else InputSeedsKey,
        OutputLevel        = OutputLevel,
        NtupleName         = NtupleName,
        OnlyRoI            = OnlyRoI,
        EtaWindow          = EtaWindow,
        PhiWindow          = PhiWindow,
        KeepCells          = KeepCells,
    )

RootStreamHITMaker = RootStreamHITMakerCfg
