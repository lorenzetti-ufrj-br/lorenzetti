__all__ = [
    "RootStreamMaker",
    "RootStreamMakerCfg",
    "RootStreamAODMaker",
    "RootStreamAODMakerCfg",
    "RootStreamESDMaker",
    "RootStreamESDMakerCfg",
    "RootStreamHITMaker",
    "RootStreamHITMakerCfg",
]

import ROOT
from typing import List, Optional
from GaugiKernel import Configurable
from RootStreamBuilder import RootStreamAODFlags


def RootStreamMakerCfg(
    name: str = "RootStreamMaker",
    ItemList: Optional[List[str]] = None,
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    OnlyRoI: bool = False,
    EtaWindow: float = 0.4,
    PhiWindow: float = 0.4,
    TruthKey: str = "Particles",
) -> Configurable:
    """
    Creates a generic RootStreamMaker algorithm that serializes any requested
    xAOD containers into branches of format <TypeName>_<Key> inside a TTree.

    :param name: Algorithm name.
    :param ItemList: List of items to record, formatted as 'TypeName#Key' (e.g. 'CaloClusterContainer#CaloClusters').
    :param TreeName: Name of the output TTree.
    :param OutputLevel: Verbosity level (0=INFO, 1=DEBUG, etc.).
    :param OnlyRoI: Enable Region of Interest (RoI) hit filtering.
    :param EtaWindow: Eta window size for RoI matching.
    :param PhiWindow: Phi window size for RoI matching.
    :param TruthKey: StoreGate key for truth particles used in RoI matching.
    """
    if ItemList is None:
        ItemList = []

    return Configurable(
        ROOT.RootStreamMaker,
        name=name,
        ItemList=ItemList,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
        OnlyRoI=OnlyRoI,
        EtaWindow=EtaWindow,
        PhiWindow=PhiWindow,
        TruthKey=TruthKey,
    )


RootStreamMaker = RootStreamMakerCfg


def RootStreamAODMakerCfg(
    name: str = "RootStreamAODMaker",
    InputEventKey: str = "EventInfo",
    InputTruthKey: str = "Particles",
    InputSeedsKey: str = "Seeds",
    InputCellsKey: str = "Cells",
    InputClusterKey: str = "CaloClusters",
    InputRingerKeys: Optional[List[str]] = None,
    InputElectronKey: str = "Electrons",
    InputTruthCellsKey: str = "TruthCells",
    InputTruthClusterKey: str = "TruthClusters",
    InputTruthRingerKeys: Optional[List[str]] = None,
    InputTruthElectronKey: str = "TruthElectrons",
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    DumpCells: bool = RootStreamAODFlags.DumpCells,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for AOD tier output.
    """
    if InputRingerKeys is None:
        InputRingerKeys = ["Rings"]
    elif isinstance(InputRingerKeys, str):
        InputRingerKeys = [InputRingerKeys]

    if InputTruthRingerKeys is None:
        InputTruthRingerKeys = ["TruthRings"]
    elif isinstance(InputTruthRingerKeys, str):
        InputTruthRingerKeys = [InputTruthRingerKeys]

    item_list: List[str] = [
        f"EventInfoContainer#{InputEventKey}",
        f"TruthParticleContainer#{InputTruthKey}",
        f"SeedContainer#{InputSeedsKey}",
        f"CaloClusterContainer#{InputClusterKey}",
        f"ElectronContainer#{InputElectronKey}",
        f"CaloClusterContainer#{InputTruthClusterKey}",
        f"ElectronContainer#{InputTruthElectronKey}",
    ]

    for key in InputRingerKeys:
        item_list.append(f"CaloRingsContainer#{key}")

    for key in InputTruthRingerKeys:
        item_list.append(f"CaloRingsContainer#{key}")

    if DumpCells:
        item_list.append(f"CaloCellContainer#{InputCellsKey}")
        item_list.append(f"CaloCellContainer#{InputTruthCellsKey}")

    return RootStreamMakerCfg(
        name=name,
        ItemList=item_list,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
    )


RootStreamAODMaker = RootStreamAODMakerCfg


def RootStreamESDMakerCfg(
    name: str = "RootStreamESDMaker",
    InputEventKey: str = "EventInfo",
    InputTruthKey: str = "Particles",
    InputSeedsKey: str = "Seeds",
    InputCellsKey: str = "Cells",
    InputTruthCellsKey: str = "TruthCells",
    InputCellsTruthKey: Optional[str] = None,
    InputDescriptorsKey: str = "CaloDetDescriptors",
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for ESD tier output.
    """
    if InputCellsTruthKey is not None:
        InputTruthCellsKey = InputCellsTruthKey

    item_list: List[str] = [
        f"EventInfoContainer#{InputEventKey}",
        f"TruthParticleContainer#{InputTruthKey}",
        f"SeedContainer#{InputSeedsKey}",
        f"CaloCellContainer#{InputCellsKey}",
        f"CaloCellContainer#{InputTruthCellsKey}",
        f"CaloDetDescriptorContainer#{InputDescriptorsKey}",
    ]

    return RootStreamMakerCfg(
        name=name,
        ItemList=item_list,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
    )


RootStreamESDMaker = RootStreamESDMakerCfg


def RootStreamHITMakerCfg(
    name: str = "RootStreamHITMaker",
    InputEventKey: str = "EventInfo",
    InputTruthKey: str = "Particles",
    InputHitsKey: str = "Hits",
    InputSeedsKey: str = "Seeds",
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    OnlyRoI: bool = True,
    EtaWindow: float = 0.4,
    PhiWindow: float = 0.4,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for HIT tier output.
    """
    item_list: List[str] = [
        f"EventInfoContainer#{InputEventKey}",
        f"TruthParticleContainer#{InputTruthKey}",
        f"CaloHitContainer#{InputHitsKey}",
        f"SeedContainer#{InputSeedsKey}",
    ]

    return RootStreamMakerCfg(
        name=name,
        ItemList=item_list,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
        OnlyRoI=OnlyRoI,
        EtaWindow=EtaWindow,
        PhiWindow=PhiWindow,
        TruthKey=InputTruthKey,
    )


RootStreamHITMaker = RootStreamHITMakerCfg
