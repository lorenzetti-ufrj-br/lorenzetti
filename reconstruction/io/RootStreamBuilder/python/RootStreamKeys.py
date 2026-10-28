__all__ = [
    "recordable",
    "valid_keys",
    "DEFAULT_KEY_TO_TYPE_MAP",
    "get_recorded_items",
    "clear_recorded_items",
    "has_recorded_key",
    "get_recorded_item_by_key",
    "get_recorded_items_by_type",
]

from typing import Dict, List, Optional

DEFAULT_KEY_TO_TYPE_MAP: Dict[str, str] = {
    # Event Info
    "EventInfo": "EventInfoContainer",
    "Events": "EventInfoContainer",
    "Events_Merged": "EventInfoContainer",
    # Hits
    "Hits": "CaloHitContainer",
    "Hits_Merged": "CaloHitContainer",
    # Cells
    "Cells": "CaloCellContainer",
    "TruthCells": "CaloCellContainer",
    # Descriptors
    "CaloDetDescriptors": "CaloDetDescriptorContainer",
    # Seeds
    "Seeds": "SeedContainer",
    # Truth Particles
    "Particles": "TruthParticleContainer",
    "TruthParticles": "TruthParticleContainer",
    # Clusters
    "Clusters": "CaloClusterContainer",
    "TruthClusters": "CaloClusterContainer",
    "CaloClusters": "CaloClusterContainer",
    # Electrons
    "Electrons": "ElectronContainer",
    "TruthElectrons": "ElectronContainer",
    # Rings
    "Rings": "CaloRingsContainer",
    "RingsSigmaNoise": "CaloRingsContainer",
    "TruthRings": "CaloRingsContainer",
    "AsymRings": "CaloRingsContainer",
    "TruthAsymRings": "CaloRingsContainer",
    "CornerRings": "CaloRingsContainer",
    "TruthCornerRings": "CaloRingsContainer",
    "StripsRings": "CaloRingsContainer",
    "TruthStripsRings": "CaloRingsContainer",
    "CrossRings": "CaloRingsContainer",
    "TruthCrossRings": "CaloRingsContainer",
    "CustomRings": "CaloRingsContainer",
    "TruthCustomRings": "CaloRingsContainer",
    "RingsL0": "CaloRingsContainer",
    "TruthRingsL0": "CaloRingsContainer",
}

valid_keys = list(DEFAULT_KEY_TO_TYPE_MAP.keys())

# Internal ordered registry storing active items for persistence
_active_recorded_items: Dict[str, str] = {}


def recordable(key: str, container_type: Optional[str] = None) -> str:
    """
    Registers a key and its EDM container type into the active persistence registry,
    and returns the key name as a string.

    :param key: StoreGate key string.
    :param container_type: Optional explicit container type name (e.g. 'CaloCellContainer').
                           If omitted, resolves automatically from DEFAULT_KEY_TO_TYPE_MAP.
    :return: The key string unchanged.
    """
    resolved_type = container_type
    if resolved_type is None:
        if key not in DEFAULT_KEY_TO_TYPE_MAP and key not in valid_keys:
            raise RuntimeError(f"Key {key} is not allowed to be recorded without specifying container_type.")
        resolved_type = DEFAULT_KEY_TO_TYPE_MAP.get(key)

    if resolved_type:
        item = f"{resolved_type}#{key}"
        _active_recorded_items[item] = key

    return key


def get_recorded_items() -> List[str]:
    """Returns a list of all recorded items in the format 'TypeName#Key'."""
    return list(_active_recorded_items.keys())


def clear_recorded_items() -> None:
    """Clears all currently recorded items from the active registry."""
    _active_recorded_items.clear()


def has_recorded_key(key: str) -> bool:
    """Checks if a given key has been registered in the active registry."""
    return any(k == key for k in _active_recorded_items.values())


def get_recorded_item_by_key(key: str) -> Optional[str]:
    """Returns the item 'TypeName#Key' matching the given key, or None."""
    for item, k in _active_recorded_items.items():
        if k == key:
            return item
    return None


def get_recorded_items_by_type(container_type: str) -> List[str]:
    """Returns all recorded items matching the specified container type."""
    prefix = f"{container_type}#"
    return [item for item in _active_recorded_items.keys() if item.startswith(prefix)]
