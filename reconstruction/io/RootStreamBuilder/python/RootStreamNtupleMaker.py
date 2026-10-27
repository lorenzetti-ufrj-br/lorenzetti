__all__ = ["RootStreamNtupleMaker", "RootStreamNtupleMakerCfg"]

import ROOT
from typing import List, Optional
from GaugiKernel import Configurable


def RootStreamNtupleMakerCfg(
    name: str = "RootStreamNtupleMaker",
    InputEventKey: str = "EventInfo",
    InputTruthKey: str = "Particles",
    InputSeedsKey: str = "Seeds",
    InputClusterKey: str = "CaloClusters",
    InputRingerKeys: Optional[List[str]] = None,
    InputRingerL0Key: str = "RingsL0",
    InputTruthClusterKey: str = "TruthClusters",
    InputTruthRingerKeys: Optional[List[str]] = None,
    InputTruthElectronKey: str = "TruthElectrons",
    InputElectronKey: str = "Electrons",
    OutputNtupleName: str = "events",
    OutputLevel: int = 0,
) -> Configurable:
    """
    Creates a RootStreamNtupleMaker algorithm for dumping flat analysis ntuples.
    """
    if InputRingerKeys is None:
        InputRingerKeys = ["Rings"]
    elif isinstance(InputRingerKeys, str):
        InputRingerKeys = [InputRingerKeys]

    if InputTruthRingerKeys is None:
        InputTruthRingerKeys = ["TruthRings"]
    elif isinstance(InputTruthRingerKeys, str):
        InputTruthRingerKeys = [InputTruthRingerKeys]

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
