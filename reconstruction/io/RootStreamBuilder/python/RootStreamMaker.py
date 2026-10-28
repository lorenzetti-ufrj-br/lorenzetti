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
from RootStreamBuilder.RootStreamKeys import (
    get_recorded_items,
    get_recorded_items_by_type,
    has_recorded_key,
    get_recorded_item_by_key,
)


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
    InputEventKey: Optional[str] = None,
    InputTruthKey: Optional[str] = None,
    InputSeedsKey: Optional[str] = None,
    InputCellsKey: Optional[str] = None,
    InputClusterKey: Optional[str] = None,
    InputRingerKeys: Optional[List[str]] = None,
    InputElectronKey: Optional[str] = None,
    InputTruthCellsKey: Optional[str] = None,
    InputTruthClusterKey: Optional[str] = None,
    InputTruthRingerKeys: Optional[List[str]] = None,
    InputTruthElectronKey: Optional[str] = None,
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    DumpCells: bool = RootStreamAODFlags.DumpCells,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for AOD tier output.

    If ItemList and specific Input*Key arguments are omitted, it automatically
    selects all active recordable() items corresponding to the AOD tier
    (EventInfo, TruthParticles, Seeds, Clusters, Electrons, Rings, and Cells if DumpCells=True).
    """
    if ItemList is not None:
        item_list = list(ItemList)
    else:
        manual_keys = any(
            k is not None
            for k in [
                InputEventKey,
                InputTruthKey,
                InputSeedsKey,
                InputCellsKey,
                InputClusterKey,
                InputRingerKeys,
                InputElectronKey,
                InputTruthCellsKey,
                InputTruthClusterKey,
                InputTruthRingerKeys,
                InputTruthElectronKey,
            ]
        )
        if not manual_keys:
            # Auto-discovery from active recordable() registry
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
                    "CaloClusterContainer#TruthClusters",
                    "ElectronContainer#TruthElectrons",
                    "CaloRingsContainer#Rings",
                    "CaloRingsContainer#TruthRings",
                ]
                if DumpCells:
                    item_list.extend([
                        "CaloCellContainer#Cells",
                        "CaloCellContainer#TruthCells",
                    ])
        else:
            # Manual / backwards-compatible mode
            event_key = InputEventKey or "EventInfo"
            truth_key = InputTruthKey or "Particles"
            seeds_key = InputSeedsKey or "Seeds"
            cluster_key = InputClusterKey or "CaloClusters"
            electron_key = InputElectronKey or "Electrons"
            truth_cluster_key = InputTruthClusterKey or "TruthClusters"
            truth_electron_key = InputTruthElectronKey or "TruthElectrons"

            ringer_keys = InputRingerKeys or ["Rings"]
            if isinstance(ringer_keys, str):
                ringer_keys = [ringer_keys]

            truth_ringer_keys = InputTruthRingerKeys or ["TruthRings"]
            if isinstance(truth_ringer_keys, str):
                truth_ringer_keys = [truth_ringer_keys]

            item_list = [
                f"EventInfoContainer#{event_key}",
                f"TruthParticleContainer#{truth_key}",
                f"SeedContainer#{seeds_key}",
                f"CaloClusterContainer#{cluster_key}",
                f"ElectronContainer#{electron_key}",
                f"CaloClusterContainer#{truth_cluster_key}",
                f"ElectronContainer#{truth_electron_key}",
            ]

            for key in ringer_keys:
                item_list.append(f"CaloRingsContainer#{key}")

            for key in truth_ringer_keys:
                item_list.append(f"CaloRingsContainer#{key}")

            if DumpCells:
                cells_key = InputCellsKey or "Cells"
                truth_cells_key = InputTruthCellsKey or "TruthCells"
                item_list.append(f"CaloCellContainer#{cells_key}")
                item_list.append(f"CaloCellContainer#{truth_cells_key}")

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
    InputEventKey: Optional[str] = None,
    InputTruthKey: Optional[str] = None,
    InputSeedsKey: Optional[str] = None,
    InputCellsKey: Optional[str] = None,
    InputTruthCellsKey: Optional[str] = None,
    InputCellsTruthKey: Optional[str] = None,
    InputDescriptorsKey: Optional[str] = None,
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for ESD tier output.

    If ItemList and specific Input*Key arguments are omitted, it automatically
    selects all active recordable() items corresponding to the ESD tier
    (EventInfo, TruthParticles, Seeds, Cells, TruthCells, CaloDetDescriptors).
    """
    if InputCellsTruthKey is not None:
        InputTruthCellsKey = InputCellsTruthKey

    if ItemList is not None:
        item_list = list(ItemList)
    else:
        manual_keys = any(
            k is not None
            for k in [
                InputEventKey,
                InputTruthKey,
                InputSeedsKey,
                InputCellsKey,
                InputTruthCellsKey,
                InputDescriptorsKey,
            ]
        )
        if not manual_keys:
            # Auto-discovery from active recordable() registry
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
                item_list.append(f"CaloDetDescriptorContainer#{InputDescriptorsKey or 'CaloDetDescriptors'}")

            # If no items were recorded in registry, fallback to standard defaults
            if len(item_list) <= 1:
                item_list = [
                    "EventInfoContainer#EventInfo",
                    "TruthParticleContainer#Particles",
                    "SeedContainer#Seeds",
                    "CaloCellContainer#Cells",
                    "CaloCellContainer#TruthCells",
                    f"CaloDetDescriptorContainer#{InputDescriptorsKey or 'CaloDetDescriptors'}",
                ]
        else:
            # Manual / backwards-compatible mode
            event_key = InputEventKey or "EventInfo"
            truth_key = InputTruthKey or "Particles"
            seeds_key = InputSeedsKey or "Seeds"
            cells_key = InputCellsKey or "Cells"
            truth_cells_key = InputTruthCellsKey or "TruthCells"
            desc_key = InputDescriptorsKey or "CaloDetDescriptors"

            item_list = [
                f"EventInfoContainer#{event_key}",
                f"TruthParticleContainer#{truth_key}",
                f"SeedContainer#{seeds_key}",
                f"CaloCellContainer#{cells_key}",
                f"CaloCellContainer#{truth_cells_key}",
                f"CaloDetDescriptorContainer#{desc_key}",
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
    InputEventKey: Optional[str] = None,
    InputTruthKey: Optional[str] = None,
    InputHitsKey: Optional[str] = None,
    InputSeedsKey: Optional[str] = None,
    TreeName: str = "CollectionTree",
    OutputLevel: int = 0,
    OnlyRoI: bool = True,
    EtaWindow: float = 0.4,
    PhiWindow: float = 0.4,
) -> Configurable:
    """
    Convenience preset configuring a RootStreamMaker for HIT tier output.

    If ItemList and specific Input*Key arguments are omitted, it automatically
    selects all active recordable() items corresponding to the HIT tier
    (EventInfo, TruthParticles, Hits, Seeds).
    """
    truth_key = InputTruthKey or "Particles"

    if ItemList is not None:
        item_list = list(ItemList)
    else:
        manual_keys = any(
            k is not None
            for k in [
                InputEventKey,
                InputTruthKey,
                InputHitsKey,
                InputSeedsKey,
            ]
        )
        if not manual_keys:
            # Auto-discovery from active recordable() registry
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
                    truth_key = item.split("#")[1]
                    break

            # Fallback to standard defaults if nothing recorded
            if not item_list:
                item_list = [
                    "EventInfoContainer#EventInfo",
                    f"TruthParticleContainer#{truth_key}",
                    "CaloHitContainer#Hits",
                    "SeedContainer#Seeds",
                ]
        else:
            # Manual / backwards-compatible mode
            event_key = InputEventKey or "EventInfo"
            truth_key = InputTruthKey or "Particles"
            hits_key = InputHitsKey or "Hits"
            seeds_key = InputSeedsKey or "Seeds"

            item_list = [
                f"EventInfoContainer#{event_key}",
                f"TruthParticleContainer#{truth_key}",
                f"CaloHitContainer#{hits_key}",
                f"SeedContainer#{seeds_key}",
            ]

    return RootStreamMakerCfg(
        name=name,
        ItemList=item_list,
        TreeName=TreeName,
        OutputLevel=OutputLevel,
        OnlyRoI=OnlyRoI,
        EtaWindow=EtaWindow,
        PhiWindow=PhiWindow,
        TruthKey=truth_key,
    )


RootStreamHITMaker = RootStreamHITMakerCfg
