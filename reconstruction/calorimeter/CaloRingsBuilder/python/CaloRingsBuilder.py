__all__ = ["CaloRingsBuilder", "CaloRingsTopology"]

import ROOT
import numpy as np

from typing import List
from CaloCell.CaloDefs import CaloSampling
from GaudiKernel import Configurable, EnumStringification



class CaloRingsTopology(EnumStringification):
    """
    Definition of thecaloRings

    Definition of the
    """
    Standard = "std",
    Asym     = "asym",
    Strips   = "strips",
    Corner   = "corner",
    Cross    = "cross",
    Custom   = "custom",



def CaloRingsBuilderCfg(
    name              : str,
    InputClusterKey   : str,
    OutputRingerKey   : str,
    OutputLevel       : int   = 0,
    HistogramPath     : str   = "Expert/Rings",
    DoSigmaCut        : bool  = False,
    SigmaCut          : float = 2.0,
    RingerTopology    : CaloRingsTopology = CaloRingsTopology.Standard,
    CornerShift       : int   = None,
    CrossShift        : int   = None,
    RingsShiftEta     : List[float]   = None,
    RingsShiftPhi     : List[float]   = None,
    Axis              : int   = None,
) -> List[Configurable]:
    pi = np.pi

    class_obj = {
        CaloRingsTopology.Standard    : ROOT.CaloRingsMaker,
        CaloRingsTopology.Asym        : ROOT.CaloAsymRingsMaker,
        CaloRingsTopology.Strips      : ROOT.CaloStripsRingsMaker,
        CaloRingsTopology.Corner      : ROOT.CaloCornerRingsMaker,
        CaloRingsTopology.Cross       : ROOT.CaloCrossRingsMaker,
        CaloRingsTopology.Custom      : ROOT.CaloCustomRingsMaker,
    }

    rings = Configurable(
        class_obj[RingerTopology],
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey + "_Aux",
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        RingerTopology=RingerTopology,

        LayerRings = [
            [CaloSampling.PSB,  CaloSampling.PSE],
            [CaloSampling.EMB1, CaloSampling.EMEC1],
            [CaloSampling.EMB2, CaloSampling.EMEC2],
            [CaloSampling.EMB3, CaloSampling.EMEC3],
            [CaloSampling.HEC1, CaloSampling.TileCal1, CaloSampling.TileExt1],
            [CaloSampling.HEC2, CaloSampling.TileCal2, CaloSampling.TileExt2],
            [CaloSampling.HEC3, CaloSampling.TileCal3, CaloSampling.TileExt3],
        ],
        EtaRange      = [0.0, 2.5],
        NRings        = [8, 64, 8, 8, 4, 4, 4],
        DeltaPhiRings = [pi / 32, pi / 32, pi / 128, pi / 128, pi / 128, pi / 32, pi / 32, pi / 32],
        DeltaEtaRings = [0.025, 0.00325, 0.025, 0.050, 0.1, 0.1, 0.2],
    )

    if RingerTopology == CaloRingsTopology.Asym:
        rings.NRings = [(n - 1) * 4 + 1 for n in rings.NRings]
    if RingerTopology == CaloRingsTopology.Strips:
        rings.NRings = [28, 252, 28, 14, 8, 8, 4]
        rings.Axis = 0 if Axis is None else Axis
    if RingerTopology == CaloRingsTopology.Corner:
        rings.CornerShift = 3 if CornerShift is None else CornerShift
        rings.NRings = [n * 4 for n in rings.NRings]
    if RingerTopology == CaloRingsTopology.Cross:
        rings.CrossShift = 3 if CrossShift is None else CrossShift
        rings.NRings = [n * 4 for n in rings.NRings]
    if RingerTopology == CaloRingsTopology.Custom:
        rings.RingsShiftEta = [0] if RingsShiftEta is None else RingsShiftEta
        rings.RingsShiftPhi = [0] if RingsShiftPhi is None else RingsShiftPhi

    fwd_rings = Configurable( 
        ROOT.CaloRingsMaker,
        name + "_Fwd",
        InputClusterKey   = InputClusterKey,
        OutputRingerKey   = OutputRingerKey + "_Fwd_Aux",
        HistogramPath     = HistogramPath + "_Fwd",
        OutputLevel       = OutputLevel,
        DeltaEtaRings     = [0.1, 0.1, 0.1, 0.2, 0.2, 0.2],
        DeltaPhiRings     = [pi / 32, pi / 32, pi / 32, pi / 16, pi / 16, pi / 16],
        NRings            = [4, 4, 4, 2, 2, 2],
        LayerRings        = [
            [CaloSampling.EMEC1],
            [CaloSampling.EMEC2],
            [CaloSampling.EMEC3],
            [CaloSampling.HEC1],
            [CaloSampling.HEC2],
            [CaloSampling.HEC3],
        ],
        EtaRange          = [2.5, 4.9],
    )


    merge_rings = Configurable( 
        ROOT.CaloRingsMerge, 
        name + "_Merge",
        CollectionKeys  =[rings.OutputRingerKey, fwd_rings.OutputRingerKey],
        OutputRingerKey = OutputRingerKey,
        OutputLevel     = OutputLevel,
    )

    return [rings, fwd_rings, merge_rings]


CaloRingsBuilder = CaloRingsBuilderCfg