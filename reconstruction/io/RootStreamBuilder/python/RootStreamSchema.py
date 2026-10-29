__all__ = [
    "DEFAULT_SCHEMA",
    "EVENT_INFO_SCHEMA",
    "ELECTRON_SCHEMA",
    "CALO_CLUSTER_SCHEMA",
    "CALO_RINGS_SCHEMA",
    "SEED_SCHEMA",
    "TRUTH_PARTICLE_SCHEMA",
    "get_default_schema",
    "get_scalar_rings_schema",
    "build_custom_schema",
]

from typing import Dict, Optional

# ==============================================================================
# Event Info
# ==============================================================================
EVENT_INFO_SCHEMA: Dict[str, str] = {
    "RunNumber": "EventInfo#EventInfo#RunNumber",
    "eventNumber": "EventInfo#EventInfo#eventNumber",
    "avgmu": "EventInfo#EventInfo#avgmu",
    "totmu": "EventInfo#EventInfo#totmu",
}

# ==============================================================================
# Reconstructed Electrons
# ==============================================================================
ELECTRON_SCHEMA: Dict[str, str] = {
    "el_eta": "Electron#Electrons#eta",
    "el_et": "Electron#Electrons#et",
    "el_phi": "Electron#Electrons#phi",
    "el_e": "Electron#Electrons#e",
    "el_tight": "Electron#Electrons#tight",
    "el_medium": "Electron#Electrons#medium",
    "el_loose": "Electron#Electrons#loose",
    "el_vloose": "Electron#Electrons#vloose",
}

# ==============================================================================
# Reconstructed CaloClusters
# ==============================================================================
CALO_CLUSTER_SCHEMA: Dict[str, str] = {
    # Kinematics
    "cl_eta": "CaloCluster#Clusters#eta",
    "cl_phi": "CaloCluster#Clusters#phi",
    "cl_e": "CaloCluster#Clusters#e",
    "cl_et": "CaloCluster#Clusters#et",
    "cl_deta": "CaloCluster#Clusters#deta",
    "cl_dphi": "CaloCluster#Clusters#dphi",
    # Sampling layers
    "cl_e0": "CaloCluster#Clusters#e0",
    "cl_e1": "CaloCluster#Clusters#e1",
    "cl_e2": "CaloCluster#Clusters#e2",
    "cl_e3": "CaloCluster#Clusters#e3",
    "cl_ehad1": "CaloCluster#Clusters#ehad1",
    "cl_ehad2": "CaloCluster#Clusters#ehad2",
    "cl_ehad3": "CaloCluster#Clusters#ehad3",
    "cl_etot": "CaloCluster#Clusters#etot",
    # Shower shapes
    "cl_e233": "CaloCluster#Clusters#e233",
    "cl_e237": "CaloCluster#Clusters#e237",
    "cl_e277": "CaloCluster#Clusters#e277",
    "cl_emaxs1": "CaloCluster#Clusters#emaxs1",
    "cl_emaxs2": "CaloCluster#Clusters#emaxs2",
    "cl_e2tsts1": "CaloCluster#Clusters#e2tsts1",
    "cl_reta": "CaloCluster#Clusters#reta",
    "cl_rphi": "CaloCluster#Clusters#rphi",
    "cl_rhad": "CaloCluster#Clusters#rhad",
    "cl_rhad1": "CaloCluster#Clusters#rhad1",
    "cl_eratio": "CaloCluster#Clusters#eratio",
    "cl_f0": "CaloCluster#Clusters#f0",
    "cl_f1": "CaloCluster#Clusters#f1",
    "cl_f2": "CaloCluster#Clusters#f2",
    "cl_f3": "CaloCluster#Clusters#f3",
    "cl_weta2": "CaloCluster#Clusters#weta2",
    # Moments
    "cl_secondR": "CaloCluster#Clusters#secondR",
    "cl_lambdaCenter": "CaloCluster#Clusters#lambdaCenter",
    "cl_secondLambda": "CaloCluster#Clusters#secondLambda",
    "cl_fracMax": "CaloCluster#Clusters#fracMax",
    "cl_lateralMom": "CaloCluster#Clusters#lateralMom",
    "cl_longitudinalMom": "CaloCluster#Clusters#longitudinalMom",
}

# ==============================================================================
# CaloRings (Vector Branches)
# ==============================================================================
CALO_RINGS_SCHEMA: Dict[str, str] = {
    "cl_rings_Rings": "CaloRings#Rings#rings",
}

# ==============================================================================
# Seeds
# ==============================================================================
SEED_SCHEMA: Dict[str, str] = {
    "seed_eta": "Seed#Seeds#eta",
    "seed_phi": "Seed#Seeds#phi",
    "seed_e": "Seed#Seeds#e",
    "seed_et": "Seed#Seeds#et",
    "seed_id": "Seed#Seeds#id",
}

# ==============================================================================
# Truth Particles (MC Truth)
# ==============================================================================
TRUTH_PARTICLE_SCHEMA: Dict[str, str] = {
    "mc_pdgid": "TruthParticle#Particles#pdgid",
    "mc_eta": "TruthParticle#Particles#eta",
    "mc_phi": "TruthParticle#Particles#phi",
    "mc_e": "TruthParticle#Particles#e",
    "mc_et": "TruthParticle#Particles#et",
}

# ==============================================================================
# Combined Default Schema
# ==============================================================================
DEFAULT_SCHEMA: Dict[str, str] = {
    **EVENT_INFO_SCHEMA,
    **ELECTRON_SCHEMA,
    **CALO_CLUSTER_SCHEMA,
    **CALO_RINGS_SCHEMA,
    **SEED_SCHEMA,
    **TRUTH_PARTICLE_SCHEMA,
}


def get_default_schema() -> Dict[str, str]:
    """
    Returns a copy of the default schema containing all standard EDM branches and variables.
    """
    return dict(DEFAULT_SCHEMA)


def get_scalar_rings_schema(
    prefix: str = "ring_",
    key: str = "Rings",
    n_rings: int = 100,
) -> Dict[str, str]:
    """
    Generates a schema dictionary mapping individual ring elements to scalar branches.

    :param prefix: Output branch name prefix (e.g. 'ring_' -> 'ring_0'..'ring_99').
    :param key: StoreGate key of the CaloRings container (default: 'Rings').
    :param n_rings: Number of ring scalars to unpack (default: 100).
    :return: Dictionary mapping branch names to target specs 'CaloRings#<key>#rings[<i>]'.
    """
    return {f"{prefix}{i}": f"CaloRings#{key}#rings[{i}]" for i in range(n_rings)}


def build_custom_schema(
    include_default: bool = False,
    include_scalar_rings: bool = False,
    extra_branches: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Convenience helper to assemble custom schema dictionaries.

    :param include_default: If True, starts with the full default schema.
    :param include_scalar_rings: If True, adds individual scalar rings ('ring_0'..'ring_99').
    :param extra_branches: Optional dictionary with additional custom branch mappings.
    :return: Merged schema dictionary.
    """
    schema: Dict[str, str] = {}
    if include_default:
        schema.update(DEFAULT_SCHEMA)
    if include_scalar_rings:
        schema.update(get_scalar_rings_schema())
    if extra_branches:
        schema.update(extra_branches)
    return schema
