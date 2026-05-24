__all__ = ["CaloRingsBuilderCfg"]


from CaloRingsBuilder import CaloRingsMaker, CaloRingsMerge
from CaloCell.CaloDefs import CaloSampling
import numpy as np

pi = np.pi

DELTA_ETA_RINGS = [0.025, 0.00325, 0.025, 0.050, 0.1, 0.1, 0.2]
DELTA_PHI_RINGS = [
    pi / 32,
    pi / 32,
    pi / 128,
    pi / 128,
    pi / 128,
    pi / 32,
    pi / 32,
    pi / 32,
]
N_RINGS = [8, 64, 8, 8, 4, 4, 4]
ETA_RANGE = [0.0, 2.5]
LAYERS_RINGS = [
    [CaloSampling.PSB, CaloSampling.PSE],
    [CaloSampling.EMB1, CaloSampling.EMEC1],
    [CaloSampling.EMB2, CaloSampling.EMEC2],
    [CaloSampling.EMB3, CaloSampling.EMEC3],
    [CaloSampling.HEC1, CaloSampling.TileCal1, CaloSampling.TileExt1],
    [CaloSampling.HEC2, CaloSampling.TileCal2, CaloSampling.TileExt2],
    [CaloSampling.HEC3, CaloSampling.TileCal3, CaloSampling.TileExt3],
]

DELTA_ETA_RINGS_FWD = [0.1, 0.1, 0.1, 0.2, 0.2, 0.2]
DELTA_PHI_RINGS_FWD = [pi / 32, pi / 32, pi / 32, pi / 16, pi / 16, pi / 16]
N_RINGS_FWD = [4, 4, 4, 2, 2, 2]
ETA_RANGE_FWD = [2.5, 4.9]
LAYERS_RINGS_FWD = [
    [CaloSampling.EMEC1],
    [CaloSampling.EMEC2],
    [CaloSampling.EMEC3],
    [CaloSampling.HEC1],
    [CaloSampling.HEC2],
    [CaloSampling.HEC3],
]

caloRingsArgs = {
    "DeltaEtaRings": DELTA_ETA_RINGS,
    "DeltaPhiRings": DELTA_PHI_RINGS,
    "NRings": N_RINGS,
    "LayerRings": LAYERS_RINGS,
    "EtaRange": ETA_RANGE,
}

caloAsymRingsArgs = caloRingsArgs | {
    "NRings": [(rings - 1) * 4 + 1 for rings in N_RINGS]
}
caloStripsRingsArgs = caloRingsArgs | {
    "NRings": [28, 252, 28, 14, 8, 8, 4],
    "Axis": 0,
}
caloCornerRingsArgs = caloRingsArgs | {
    "NRings": [n * 4 for n in N_RINGS],
    "CornerShift": 3,
}
caloCrossRingsArgs = caloRingsArgs | {
    "NRings": [n * 4 for n in N_RINGS],
    "CrossShift": 3,
}
caloCustomRingsArgs = caloRingsArgs | {
    "RingsShiftEta": [3, 3, -3, -3],
    "RingsShiftPhi": [3, -3, -3, 3],
}
caloRingsFwdArgs = {
    "DeltaEtaRings": DELTA_ETA_RINGS_FWD,
    "DeltaPhiRings": DELTA_PHI_RINGS_FWD,
    "NRings": N_RINGS_FWD,
    "LayerRings": LAYERS_RINGS_FWD,
    "EtaRange": ETA_RANGE_FWD,
}

caloRingerTopologies = {
    "std": caloRingsArgs,
    "asym": caloAsymRingsArgs,
    "strips": caloStripsRingsArgs,
    "corner": caloCornerRingsArgs,
    "cross": caloCrossRingsArgs,
    "custom": caloCustomRingsArgs,
}


def CaloRingsBuilderCfg(
    name: str,
    InputClusterKey: str,
    OutputRingerKey: str,
    OutputLevel: int = 0,
    HistogramPath: str = "Expert/Rings",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    RingerTopology: str = "std",
):

    rings = CaloRingsMaker(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey + "_Aux",
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        RingerTopology=RingerTopology,
        **caloRingerTopologies[RingerTopology]
    )

    fwd_rings = CaloRingsMaker(
        name + "_Fwd",
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey + "_Fwd_Aux",
        HistogramPath=HistogramPath + "_Fwd",
        OutputLevel=OutputLevel,
        **caloRingsFwdArgs
    )

    merge_rings = CaloRingsMerge(
        name + "_Merge",
        CollectionKeys=[rings.OutputRingerKey, fwd_rings.OutputRingerKey],
        OutputRingerKey=OutputRingerKey,
        OutputLevel=OutputLevel,
    )

    return [rings, fwd_rings, merge_rings]
