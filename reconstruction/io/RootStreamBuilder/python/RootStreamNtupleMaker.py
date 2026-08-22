__all__ = ["RootStreamNtupleMaker"]

import ROOT
from GaugiKernel import Configurable
from GaugiKernel.macros import *


def RootStreamNtupleMakerCfg(
    name,
    InputEventKey: str,
    InputTruthKey: str,
    InputSeedsKey: str,
    InputClusterKey: str,
    InputRingerKeys: str,
    InputRingerL0Key: str,
    InputTruthClusterKey: str,
    InputTruthRingerKeys: str,
    InputTruthElectronKey: str,
    InputElectronKey: str,
    OutputLevel: int = 0,
    OutputNtupleName: str = "events",
) -> Configurable:

    return Configurable(
        ROOT.RootStreamNtupleMaker,
        name=name,
        InputEventKey=InputEventKey,
        InputTruthKey=InputTruthKey,
        InputSeedsKey=InputSeedsKey,
        InputClusterKey=InputClusterKey,
        InputRingerKeys=InputRingerKeys,
        InputRingerL0Key=InputRingerL0Key,
        InputTruthClusterKey=InputTruthClusterKey,
        InputTruthRingerKeys=InputTruthRingerKeys,
        InputTruthElectronKey=InputTruthElectronKey,
        InputElectronKey=InputElectronKey,
        OutputNtupleName=OutputNtupleName,
        OutputLevel=OutputLevel,
    )

RootStreamNtupleMaker = RootStreamNtupleMakerCfg
