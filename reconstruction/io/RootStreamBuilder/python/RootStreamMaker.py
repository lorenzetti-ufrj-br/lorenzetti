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
from RootStreamBuilder.RootStreamKeys import get_recorded_items


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

    If ItemList is omitted (None), it automatically uses all items currently
    registered via recordable().

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
        ItemList = get_recorded_items()

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
    ItemList: Optional[List[str]] = None,
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    DumpCells: bool = RootStreamAODFlags.DumpCells,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for AOD tier output.

    If ItemList is omitted, it automatically queries the active registry
    via get_recorded_items() for containers corresponding to the AOD tier
    (EventInfo, TruthParticles, Seeds, Clusters, Electrons, Rings, and
    Cells if DumpCells=True).
    """
    if ItemList is not None:
        item_list = list(ItemList)
    else:
        recorded = get_recorded_items()
        aod_valid_types = {
            "EventInfoContainer",
            "TruthParticleContainer",
            "SeedContainer",
            "CaloClusterContainer",
            "ElectronContainer",
            "CaloRingsContainer",
        }
        if DumpCells:
            aod_valid_types.add("CaloCellContainer")

        item_list = [item for item in recorded if item.split("#")[0] in aod_valid_types]

        # If no items were recorded in registry, fallback to standard defaults
        if not item_list:
            item_list = [
                "EventInfoContainer#EventInfo",
                "TruthParticleContainer#Particles",
                "SeedContainer#Seeds",
                "CaloClusterContainer#CaloClusters",
                "ElectronContainer#Electrons",
                "CaloRingsContainer#Rings",
            ]
            if DumpCells:
                item_list.extend([
                    "CaloCellContainer#Cells",
                    "CaloCellContainer#TruthCells",
                ])

    return RootStreamMakerCfg(
        name=name,
        ItemList=item_list,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
    )


RootStreamAODMaker = RootStreamAODMakerCfg


def RootStreamESDMakerCfg(
    name: str = "RootStreamESDMaker",
    ItemList: Optional[List[str]] = None,
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for ESD tier output.

    If ItemList is omitted, it automatically queries the active registry
    via get_recorded_items() for containers corresponding to the ESD tier
    (EventInfo, TruthParticles, Seeds, Cells, TruthCells, CaloDetDescriptors).
    """
    if ItemList is not None:
        item_list = list(ItemList)
    else:
        recorded = get_recorded_items()
        esd_valid_types = {
            "EventInfoContainer",
            "TruthParticleContainer",
            "SeedContainer",
            "CaloCellContainer",
            "CaloDetDescriptorContainer",
        }
        item_list = [item for item in recorded if item.split("#")[0] in esd_valid_types]

        # Ensure CaloDetDescriptorContainer is present
        if not any(item.startswith("CaloDetDescriptorContainer#") for item in item_list):
            item_list.append("CaloDetDescriptorContainer#CaloDetDescriptors")

        # If no items were recorded in registry, fallback to standard defaults
        if len(item_list) <= 1:
            item_list = [
                "EventInfoContainer#EventInfo",
                "TruthParticleContainer#Particles",
                "SeedContainer#Seeds",
                "CaloCellContainer#Cells",
                "CaloCellContainer#TruthCells",
                "CaloDetDescriptorContainer#CaloDetDescriptors",
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
    ItemList: Optional[List[str]] = None,
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    OnlyRoI: bool = True,
    EtaWindow: float = 0.4,
    PhiWindow: float = 0.4,
    TruthKey: str = "Particles",
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for HIT tier output.

    If ItemList is omitted, it automatically queries the active registry
    via get_recorded_items() for containers corresponding to the HIT tier
    (EventInfo, TruthParticles, Hits, Seeds).
    """
    if ItemList is not None:
        item_list = list(ItemList)
    else:
        recorded = get_recorded_items()
        hit_valid_types = {
            "EventInfoContainer",
            "TruthParticleContainer",
            "CaloHitContainer",
            "SeedContainer",
        }
        item_list = [item for item in recorded if item.split("#")[0] in hit_valid_types]

        # Resolve truth key for RoI filtering from recorded items if available
        for item in item_list:
            if item.startswith("TruthParticleContainer#"):
                TruthKey = item.split("#")[1]
                break

        # Fallback to standard defaults if nothing recorded
        if not item_list:
            item_list = [
                "EventInfoContainer#EventInfo",
                f"TruthParticleContainer#{TruthKey}",
                "CaloHitContainer#Hits",
                "SeedContainer#Seeds",
            ]

    return RootStreamMakerCfg(
        name=name,
        ItemList=item_list,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
        OnlyRoI=OnlyRoI,
        EtaWindow=EtaWindow,
        PhiWindow=PhiWindow,
        TruthKey=TruthKey,
    )


RootStreamHITMaker = RootStreamHITMakerCfg
