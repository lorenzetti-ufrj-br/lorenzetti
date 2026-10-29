__all__ = ["RootStreamNtupleMaker", "RootStreamNtupleMakerCfg"]

import ROOT
from typing import List, Optional, Dict
from GaugiKernel import Configurable


def RootStreamNtupleMakerCfg(
    name: str = "RootStreamNtupleMaker",
    InputEventKey: str = "EventInfo",
    InputTruthKey: str = "Particles",
    InputSeedsKey: str = "Seeds",
    InputClusterKey: str = "CaloClusters",
    InputRingerKeys: Optional[List[str]] = None,
    InputElectronKey: str = "Electrons",
    OutputNtupleName: str = "events",
    Schema: Optional[Dict[str, str]] = None,
    OutputLevel: int = 0,
) -> Configurable:
    """
    Creates a RootStreamNtupleMaker algorithm for dumping flat analysis ntuples.
    """
    if InputRingerKeys is None:
        InputRingerKeys = ["Rings"]
    elif isinstance(InputRingerKeys, str):
        InputRingerKeys = [InputRingerKeys]

    if Schema is None:
        Schema = {}

    return Configurable(
        ROOT.RootStreamNtupleMaker,
        name=name,
        InputEventKey=InputEventKey,
        InputTruthKey=InputTruthKey,
        InputSeedsKey=InputSeedsKey,
        InputClusterKey=InputClusterKey,
        InputRingerKeys=InputRingerKeys,
        InputElectronKey=InputElectronKey,
        OutputNtupleName=OutputNtupleName,
        Schema=Schema,
        OutputLevel=OutputLevel,
    )


RootStreamNtupleMaker = RootStreamNtupleMakerCfg
