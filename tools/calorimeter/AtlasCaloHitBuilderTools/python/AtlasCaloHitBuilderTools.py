__all__ = [
    "validate_atlas_hit_flags",
    "keep_only_collection_tree",
    "TileBoxCellToolCfg",
    "TileDualReadoutSplitToolCfg",
    "TilePmtPropagationTimeToolCfg",
    "LArAccordionToolCfg",
    "LArEmecCompartmentToolCfg",
    "LArHecModuleToolCfg",
    "LArEmecChargeCollectionToolCfg",
    "LArFCalElectrodeToolCfg",
    "CaloFreeRunningHitRecorderToolCfg",
    "CaloFreeRunningHitWriter",
]

import os
from pathlib import Path
from typing import Any, Optional, Union
import ROOT
from GaugiKernel import Configurable, LoggingLevel
from CaloHitBuilder.CaloHitFlags import CaloHitFlags, FreeRunningFlags
from .CaloFreeRunningHitWriter import CaloFreeRunningHitWriter


def keep_only_collection_tree(path: Union[str, Path]) -> None:
    """
    Keeps only the CollectionTree in the output file of free-running ATLAS format,
    removing the monitoring directories (Event/, Expert/) as in the ATLAS HITS ntuple.
    The tree is cloned with identical compression settings.
    """
    path_str = str(path)
    src = ROOT.TFile.Open(path_str)
    if not src or src.IsZombie():
        return
    tree = src.Get("CollectionTree")
    if not tree:
        src.Close()
        return
    tmp = path_str + ".tmp"
    dst = ROOT.TFile(tmp, "RECREATE", "", src.GetCompressionSettings())
    tree.CloneTree(-1, "fast").Write()
    dst.Close()
    src.Close()
    os.replace(tmp, path_str)


def validate_atlas_hit_flags(
    flags: Optional[CaloHitFlags] = None,
    fr_flags: Optional[FreeRunningFlags] = None,
    geo_flags: Optional[Any] = None,
) -> None:
    """
    Validates logical consistency and prerequisites between ATLAS hit simulation flags.
    Raises ValueError with informative diagnostics if flags are in an incompatible state.
    """
    if flags is None:
        flags = CaloHitFlags
    if fr_flags is None:
        fr_flags = FreeRunningFlags

    # 1. Free-running hits prerequisites
    if not fr_flags.Enable:
        if fr_flags.AtlasFormat:
            raise ValueError(
                "Inconsistent flags: FreeRunningFlags.AtlasFormat=True requires FreeRunningHits=True "
                "(FreeRunningFlags.Enable=True)."
            )
        if fr_flags.KeepHits:
            raise ValueError(
                "Inconsistent flags: FreeRunningFlags.KeepHits=True requires FreeRunningHits=True "
                "(FreeRunningFlags.Enable=True)."
            )
        if fr_flags.NoBinning:
            raise ValueError(
                "Inconsistent flags: FreeRunningFlags.NoBinning=True requires FreeRunningHits=True "
                "(FreeRunningFlags.Enable=True)."
            )
        if fr_flags.EmecChargeCollection:
            raise ValueError(
                "Inconsistent flags: EmecChargeCollection=True requires FreeRunningHits=True "
                "(FreeRunningFlags.Enable=True)."
            )

    # 2. EMEC Charge Collection prerequisites
    if fr_flags.EmecChargeCollection:
        if not fr_flags.EmecTables:
            raise ValueError(
                "EmecChargeCollection is enabled, but EmecChargeTables path is empty. "
                "Ensure FreeRunningFlags.EmecTables is configured."
            )
        if not fr_flags.EmecFieldMap:
            raise ValueError(
                "EmecChargeCollection is enabled, but EmecChargeFieldMap path is empty. "
                "Ensure FreeRunningFlags.EmecFieldMap is configured."
            )
        if not fr_flags.EmecHVMap:
            raise ValueError(
                "EmecChargeCollection is enabled, but EmecChargeHVMap path is empty. "
                "Ensure FreeRunningFlags.EmecHVMap is configured."
            )
        for f in (fr_flags.EmecTables, fr_flags.EmecFieldMap, fr_flags.EmecHVMap):
            if not os.path.isfile(f):
                raise ValueError(f"EMEC charge collection file '{f}' not found")

    # 3. Tile Dual Readout prerequisites
    if flags.TileDualReadout:
        if flags.TilePmtSplit not in ("ushape", "linear"):
            raise ValueError(
                f"Invalid CaloHitFlags.TilePmtSplit: '{flags.TilePmtSplit}'. "
                "Allowed options are 'ushape' or 'linear'."
            )

    # 4. Geometry prerequisites for free-running hits (when geo_flags is provided)
    if fr_flags.Enable and geo_flags is not None:
        if not (getattr(geo_flags, "TileAtlasGeometry", False) and getattr(geo_flags, "TileAtlasCells", False)):
            raise ValueError("free-running hits require TileAtlasGeometry and TileAtlasCells in AtlasGeometryFlags")
        if not (getattr(geo_flags, "AtlasEmbCells", False) and getattr(geo_flags, "AtlasHec", False) and getattr(geo_flags, "AtlasEmec", False)):
            raise ValueError("free-running hits require AtlasEmbCells, AtlasHec, and AtlasEmec in AtlasGeometryFlags")
        if not getattr(geo_flags, "TileAtlasGap", False):
            raise ValueError("free-running hits require TileAtlasGap in AtlasGeometryFlags")
        if not getattr(geo_flags, "AtlasFcalCells", False):
            raise ValueError("free-running hits require AtlasFcalCells in AtlasGeometryFlags")
        if not getattr(geo_flags, "AtlasFcalFrozenShowers", False):
            raise ValueError("free-running hits require AtlasFcalFrozenShowers in AtlasGeometryFlags")
        if not getattr(geo_flags, "AtlasG4", False):
            raise ValueError("free-running hits require AtlasG4 in AtlasGeometryFlags")
        if not getattr(geo_flags, "AtlasRun4", False):
            raise ValueError("free-running hits require AtlasRun4 in AtlasGeometryFlags")

        if fr_flags.AtlasFormat:
            if not getattr(geo_flags, "AtlasEmecArgonFraction", False):
                raise ValueError("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasEmecArgonFraction")
            if not getattr(geo_flags, "TileAtlasRun4", False):
                raise ValueError("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.TileAtlasRun4")
            if not getattr(geo_flags, "AtlasBarrelGapServices", False):
                raise ValueError("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasBarrelGapServices")
            if not getattr(geo_flags, "AtlasFullField", False):
                raise ValueError("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasFullField")
            if not getattr(geo_flags, "AtlasForwardShielding", False):
                raise ValueError("FreeRunningFlags.AtlasFormat requires AtlasGeometryFlags.AtlasForwardShielding")
            if not fr_flags.EmecChargeCollection:
                raise ValueError("FreeRunningFlags.AtlasFormat requires FreeRunningFlags.EmecChargeCollection")


def TileBoxCellToolCfg(
    name: str = "TileBoxCellTool",
    Sampling: int = 0,
    Segment: int = 0,
    Detector: int = 0,
    ZMin: float = 0.0,
    ZMax: float = 0.0,
    RMin: float = 0.0,
    RMax: float = 0.0,
    flags: Optional[CaloHitFlags] = None,
    BcDuration: float = 25.0,
    BcidStart: int = -7,
    BcidEnd: int = 7,
    PhiBins: Optional[list] = None,
    CellEta: Optional[list] = None,
    CellDeltaEta: Optional[list] = None,
    CellBoxRMin: Optional[list] = None,
    CellBoxRMax: Optional[list] = None,
    CellBoxZMin: Optional[list] = None,
    CellBoxZMax: Optional[list] = None,
    CellBoxIndex: Optional[list] = None,
    CellNPmt: Optional[list] = None,
    SpecialModule: Optional[list] = None,
    SpecialNPmt: Optional[list] = None,
    ReplaceSection: int = 0,
    ReplaceTower: int = 0,
    ReplaceSampling: int = 0,
    ReplaceRCentre: float = 0.0,
    ReplaceZCentre: float = 0.0,
    ReplaceCollectionKey: str = "",
    ReplaceHashBase: int = 0,
    CellAtlasSection: Optional[list] = None,
    CellAtlasTower: Optional[list] = None,
    CellAtlasSampling: Optional[list] = None,
    CellRCentre: Optional[list] = None,
    CellZCentre: Optional[list] = None,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a TileBoxCellTool instance for ATLAS Tile (r, z) box geometry.
    Simulation properties are captured directly from CaloHitFlags.
    """
    if flags is None:
        flags = CaloHitFlags

    tile_dual_readout = (1 if flags.TilePmtSplit == "ushape" else 2) if flags.TileDualReadout else 0

    return Configurable(
        ROOT.TileBoxCellTool,
        name,
        Sampling=Sampling,
        Segment=Segment,
        Detector=Detector,
        ZMin=ZMin,
        ZMax=ZMax,
        RMin=RMin,
        RMax=RMax,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
        BcDuration=BcDuration,
        BcidStart=BcidStart,
        BcidEnd=BcidEnd,
        TileDualReadout=tile_dual_readout,
        PhiBins=PhiBins if PhiBins is not None else [],
        CellEta=CellEta if CellEta is not None else [],
        CellDeltaEta=CellDeltaEta if CellDeltaEta is not None else [],
        CellBoxRMin=CellBoxRMin if CellBoxRMin is not None else [],
        CellBoxRMax=CellBoxRMax if CellBoxRMax is not None else [],
        CellBoxZMin=CellBoxZMin if CellBoxZMin is not None else [],
        CellBoxZMax=CellBoxZMax if CellBoxZMax is not None else [],
        CellBoxIndex=CellBoxIndex if CellBoxIndex is not None else [],
        CellNPmt=CellNPmt if CellNPmt is not None else [],
        SpecialModule=SpecialModule if SpecialModule is not None else [],
        SpecialNPmt=SpecialNPmt if SpecialNPmt is not None else [],
        ReplaceSection=ReplaceSection,
        ReplaceTower=ReplaceTower,
        ReplaceSampling=ReplaceSampling,
        ReplaceRCentre=ReplaceRCentre,
        ReplaceZCentre=ReplaceZCentre,
        ReplaceCollectionKey=ReplaceCollectionKey,
        ReplaceHashBase=ReplaceHashBase,
        CellAtlasSection=CellAtlasSection if CellAtlasSection is not None else [],
        CellAtlasTower=CellAtlasTower if CellAtlasTower is not None else [],
        CellAtlasSampling=CellAtlasSampling if CellAtlasSampling is not None else [],
        CellRCentre=CellRCentre if CellRCentre is not None else [],
        CellZCentre=CellZCentre if CellZCentre is not None else [],
        OutputLevel=OutputLevel,
    )


def TileDualReadoutSplitToolCfg(
    name: str = "TileDualReadoutSplitTool",
    Sampling: int = 0,
    flags: Optional[CaloHitFlags] = None,
    PhiBins: Optional[list] = None,
    UShapePart: int = -1,
    UShapeLayer: int = -1,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a TileDualReadoutSplitTool instance for PMT energy partition.
    TileDualReadout mode is captured directly from CaloHitFlags.
    """
    if flags is None:
        flags = CaloHitFlags

    tile_mode = 1 if flags.TilePmtSplit == "ushape" else 2

    return Configurable(
        ROOT.TileDualReadoutSplitTool,
        name,
        TileDualReadout=tile_mode,
        Sampling=Sampling,
        PhiBins=PhiBins if PhiBins is not None else [],
        UShapePart=UShapePart,
        UShapeLayer=UShapeLayer,
        OutputLevel=OutputLevel,
    )


def TilePmtPropagationTimeToolCfg(
    name: str = "TilePmtPropagationTimeTool",
    PhiBins: Optional[list] = None,
    CellRCentre: Optional[list] = None,
    CellZCentre: Optional[list] = None,
    ReplaceRCentre: float = 0.0,
    ReplaceZCentre: float = 0.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a TilePmtPropagationTimeTool instance for Tile PMT propagation times.
    """
    return Configurable(
        ROOT.TilePmtPropagationTimeTool,
        name,
        PhiBins=PhiBins if PhiBins is not None else [],
        CellRCentre=CellRCentre if CellRCentre is not None else [],
        CellZCentre=CellZCentre if CellZCentre is not None else [],
        ReplaceRCentre=ReplaceRCentre,
        ReplaceZCentre=ReplaceZCentre,
        OutputLevel=OutputLevel,
    )


def LArAccordionToolCfg(
    name: str = "LArAccordionTool",
    Sampling: int = 0,
    Segment: int = 0,
    Detector: int = 0,
    ZMin: float = 0.0,
    ZMax: float = 0.0,
    RMin: float = 0.0,
    RMax: float = 0.0,
    flags: Optional[CaloHitFlags] = None,
    BcDuration: float = 25.0,
    BcidStart: int = -7,
    BcidEnd: int = 7,
    PhiBins: Optional[list] = None,
    CellEta: Optional[list] = None,
    CellDeltaEta: Optional[list] = None,
    EmbMode: int = 0,
    EmbSampling: int = 0,
    EmbRegion: int = 0,
    EmbZShift: float = 0.0,
    PsbR0: float = 0.0,
    EmbSampSeg: bool = False,
    AtlasBarrelEc: int = 0,
    AtlasLArSampling: int = 0,
    AtlasLArRegion: int = 0,
    CellAtlasEtaIndex: Optional[list] = None,
    PhiShift: float = 0.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a LArAccordionTool instance for ATLAS EMB accordion segmentation.
    ActiveEnergyOnly is captured directly from CaloHitFlags.
    """
    if flags is None:
        flags = CaloHitFlags

    return Configurable(
        ROOT.LArAccordionTool,
        name,
        Sampling=Sampling,
        Segment=Segment,
        Detector=Detector,
        ZMin=ZMin,
        ZMax=ZMax,
        RMin=RMin,
        RMax=RMax,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
        BcDuration=BcDuration,
        BcidStart=BcidStart,
        BcidEnd=BcidEnd,
        PhiBins=PhiBins if PhiBins is not None else [],
        CellEta=CellEta if CellEta is not None else [],
        CellDeltaEta=CellDeltaEta if CellDeltaEta is not None else [],
        EmbMode=EmbMode,
        EmbSampling=EmbSampling,
        EmbRegion=EmbRegion,
        EmbZShift=EmbZShift,
        PsbR0=PsbR0,
        EmbSampSeg=EmbSampSeg,
        AtlasBarrelEc=AtlasBarrelEc,
        AtlasLArSampling=AtlasLArSampling,
        AtlasLArRegion=AtlasLArRegion,
        CellAtlasEtaIndex=CellAtlasEtaIndex if CellAtlasEtaIndex is not None else [],
        PhiShift=PhiShift,
        OutputLevel=OutputLevel,
    )


def LArEmecCompartmentToolCfg(
    name: str = "LArEmecCompartmentTool",
    Sampling: int = 0,
    Segment: int = 0,
    Detector: int = 0,
    ZMin: float = 0.0,
    ZMax: float = 0.0,
    RMin: float = 0.0,
    RMax: float = 0.0,
    flags: Optional[CaloHitFlags] = None,
    BcDuration: float = 25.0,
    BcidStart: int = -7,
    BcidEnd: int = 7,
    PhiBins: Optional[list] = None,
    CellEta: Optional[list] = None,
    CellDeltaEta: Optional[list] = None,
    EmecCompartment: int = 0,
    EmecEtaScale: float = 0.0,
    EmecEtaOffset: float = 0.0,
    EmecMaxEta: int = 0,
    EmecFocalShift: float = 0.0,
    EmecZSep12: Optional[list] = None,
    EmecZSep23: Optional[list] = None,
    EmecZInner: Optional[list] = None,
    EmecWheelRMin: Optional[list] = None,
    EmecWheelRMax: Optional[list] = None,
    EmecWheelZMin: Optional[list] = None,
    EmecWheelZMax: Optional[list] = None,
    AtlasBarrelEc: int = 0,
    AtlasLArSampling: int = 0,
    AtlasLArRegion: int = 0,
    CellAtlasEtaIndex: Optional[list] = None,
    PhiShift: float = 0.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a LArEmecCompartmentTool instance for ATLAS EMEC 11-compartment segmentation.
    ActiveEnergyOnly is captured directly from CaloHitFlags.
    """
    if flags is None:
        flags = CaloHitFlags

    return Configurable(
        ROOT.LArEmecCompartmentTool,
        name,
        Sampling=Sampling,
        Segment=Segment,
        Detector=Detector,
        ZMin=ZMin,
        ZMax=ZMax,
        RMin=RMin,
        RMax=RMax,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
        BcDuration=BcDuration,
        BcidStart=BcidStart,
        BcidEnd=BcidEnd,
        PhiBins=PhiBins if PhiBins is not None else [],
        CellEta=CellEta if CellEta is not None else [],
        CellDeltaEta=CellDeltaEta if CellDeltaEta is not None else [],
        EmecCompartment=EmecCompartment,
        EmecEtaScale=EmecEtaScale,
        EmecEtaOffset=EmecEtaOffset,
        EmecMaxEta=EmecMaxEta,
        EmecFocalShift=EmecFocalShift,
        EmecZSep12=EmecZSep12 if EmecZSep12 is not None else [],
        EmecZSep23=EmecZSep23 if EmecZSep23 is not None else [],
        EmecZInner=EmecZInner if EmecZInner is not None else [],
        EmecWheelRMin=EmecWheelRMin if EmecWheelRMin is not None else [],
        EmecWheelRMax=EmecWheelRMax if EmecWheelRMax is not None else [],
        EmecWheelZMin=EmecWheelZMin if EmecWheelZMin is not None else [],
        EmecWheelZMax=EmecWheelZMax if EmecWheelZMax is not None else [],
        AtlasBarrelEc=AtlasBarrelEc,
        AtlasLArSampling=AtlasLArSampling,
        AtlasLArRegion=AtlasLArRegion,
        CellAtlasEtaIndex=CellAtlasEtaIndex if CellAtlasEtaIndex is not None else [],
        PhiShift=PhiShift,
        OutputLevel=OutputLevel,
    )


def LArHecModuleToolCfg(
    name: str = "LArHecModuleTool",
    Sampling: int = 0,
    Segment: int = 0,
    Detector: int = 0,
    ZMin: float = 0.0,
    ZMax: float = 0.0,
    RMin: float = 0.0,
    RMax: float = 0.0,
    flags: Optional[CaloHitFlags] = None,
    BcDuration: float = 25.0,
    BcidStart: int = -7,
    BcidEnd: int = 7,
    PhiBins: Optional[list] = None,
    CellEta: Optional[list] = None,
    CellDeltaEta: Optional[list] = None,
    CellBoxRMin: Optional[list] = None,
    CellBoxRMax: Optional[list] = None,
    CellBoxZMin: Optional[list] = None,
    CellBoxZMax: Optional[list] = None,
    CellBoxIndex: Optional[list] = None,
    CellRadiusModules: int = 32,
    AtlasBarrelEc: int = 0,
    AtlasLArSampling: int = 0,
    AtlasLArRegion: int = 0,
    CellAtlasEtaIndex: Optional[list] = None,
    PhiShift: float = 0.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a LArHecModuleTool instance for ATLAS HEC wedge module geometry.
    ActiveEnergyOnly is captured directly from CaloHitFlags.
    """
    if flags is None:
        flags = CaloHitFlags

    return Configurable(
        ROOT.LArHecModuleTool,
        name,
        Sampling=Sampling,
        Segment=Segment,
        Detector=Detector,
        ZMin=ZMin,
        ZMax=ZMax,
        RMin=RMin,
        RMax=RMax,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
        BcDuration=BcDuration,
        BcidStart=BcidStart,
        BcidEnd=BcidEnd,
        PhiBins=PhiBins if PhiBins is not None else [],
        CellEta=CellEta if CellEta is not None else [],
        CellDeltaEta=CellDeltaEta if CellDeltaEta is not None else [],
        CellBoxRMin=CellBoxRMin if CellBoxRMin is not None else [],
        CellBoxRMax=CellBoxRMax if CellBoxRMax is not None else [],
        CellBoxZMin=CellBoxZMin if CellBoxZMin is not None else [],
        CellBoxZMax=CellBoxZMax if CellBoxZMax is not None else [],
        CellBoxIndex=CellBoxIndex if CellBoxIndex is not None else [],
        CellRadiusModules=CellRadiusModules,
        AtlasBarrelEc=AtlasBarrelEc,
        AtlasLArSampling=AtlasLArSampling,
        AtlasLArRegion=AtlasLArRegion,
        CellAtlasEtaIndex=CellAtlasEtaIndex if CellAtlasEtaIndex is not None else [],
        PhiShift=PhiShift,
        OutputLevel=OutputLevel,
    )


def LArEmecChargeCollectionToolCfg(
    name: str = "LArEmecChargeCollectionTool",
    fr_flags: Optional[FreeRunningFlags] = None,
    EmecCompartment: int = 0,
    EmecFocalShift: float = 0.0,
    ZMin: float = 0.0,
    ZMax: float = 0.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a LArEmecChargeCollectionTool instance for ATLAS EMEC charge collection.
    Data paths and enablement are captured directly from FreeRunningFlags.
    """
    if fr_flags is None:
        fr_flags = FreeRunningFlags

    return Configurable(
        ROOT.LArEmecChargeCollectionTool,
        name,
        EmecChargeCollection=bool(fr_flags.EmecChargeCollection),
        EmecChargeTables=str(fr_flags.EmecTables),
        EmecChargeFieldMap=str(fr_flags.EmecFieldMap),
        EmecChargeHVMap=str(fr_flags.EmecHVMap),
        EmecCompartment=EmecCompartment,
        EmecFocalShift=EmecFocalShift,
        ZMin=ZMin,
        ZMax=ZMax,
        OutputLevel=OutputLevel,
    )


def LArFCalElectrodeToolCfg(
    name: str = "LArFCalElectrodeTool",
    Sampling: int = 0,
    Segment: int = 0,
    Detector: int = 0,
    ZMin: float = 0.0,
    ZMax: float = 0.0,
    RMin: float = 0.0,
    RMax: float = 0.0,
    flags: Optional[CaloHitFlags] = None,
    BcDuration: float = 25.0,
    BcidStart: int = -7,
    BcidEnd: int = 7,
    PhiBins: Optional[list] = None,
    CellEta: Optional[list] = None,
    CellDeltaEta: Optional[list] = None,
    ReplaceSection: int = 0,
    ReplaceTower: int = 0,
    ReplaceSampling: int = 0,
    ReplaceRCentre: float = 0.0,
    ReplaceZCentre: float = 0.0,
    FCalModule: int = 0,
    FCalSide: int = 1,
    FCalGapVolume: str = "",
    FCalCopyEtaIndex: Optional[list] = None,
    FCalCopyPhiIndex: Optional[list] = None,
    FCalCopyEta: Optional[list] = None,
    FCalCopyPhi: Optional[list] = None,
    FCalCopyDeltaEta: Optional[list] = None,
    FCalCopyDeltaPhi: Optional[list] = None,
    FCalCopyI: Optional[list] = None,
    FCalCopyJ: Optional[list] = None,
    FCalCopyX: Optional[list] = None,
    FCalCopyY: Optional[list] = None,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a LArFCalElectrodeTool instance for ATLAS FCAL electrode geometry.
    ActiveEnergyOnly is captured directly from CaloHitFlags.
    """
    if flags is None:
        flags = CaloHitFlags

    return Configurable(
        ROOT.LArFCalElectrodeTool,
        name,
        FCalModule=FCalModule,
        FCalSide=FCalSide,
        FCalGapVolume=FCalGapVolume,
        FCalCopyEtaIndex=FCalCopyEtaIndex if FCalCopyEtaIndex is not None else [],
        FCalCopyPhiIndex=FCalCopyPhiIndex if FCalCopyPhiIndex is not None else [],
        FCalCopyEta=FCalCopyEta if FCalCopyEta is not None else [],
        FCalCopyPhi=FCalCopyPhi if FCalCopyPhi is not None else [],
        FCalCopyDeltaEta=FCalCopyDeltaEta if FCalCopyDeltaEta is not None else [],
        FCalCopyDeltaPhi=FCalCopyDeltaPhi if FCalCopyDeltaPhi is not None else [],
        FCalCopyI=FCalCopyI if FCalCopyI is not None else [],
        FCalCopyJ=FCalCopyJ if FCalCopyJ is not None else [],
        FCalCopyX=FCalCopyX if FCalCopyX is not None else [],
        FCalCopyY=FCalCopyY if FCalCopyY is not None else [],
        Sampling=Sampling,
        Detector=Detector,
        Segment=Segment,
        ZMin=ZMin,
        ZMax=ZMax,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
        BcDuration=BcDuration,
        BcidStart=BcidStart,
        BcidEnd=BcidEnd,
        OutputLevel=OutputLevel,
    )


def CaloFreeRunningHitRecorderToolCfg(
    name: str = "CaloFreeRunningHitRecorderTool",
    fr_flags: Optional[FreeRunningFlags] = None,
    FreeRunningListKey: str = "FreeRunningHits",
    Subdet: int = 0,
    AtlasBarrelEc: int = 1,
    AtlasLArSampling: int = 0,
    AtlasLArRegion: int = 0,
    AtlasLArPart: int = 1,
    CellAtlasEtaIndex: Optional[list] = None,
    NPhiBins: int = 64,
    PhiBins: Optional[list] = None,
    CellEta: Optional[list] = None,
    CellAtlasSection: Optional[list] = None,
    CellAtlasTower: Optional[list] = None,
    CellAtlasSampling: Optional[list] = None,
    CellRCentre: Optional[list] = None,
    CellZCentre: Optional[list] = None,
    ReplaceSection: int = 0,
    ReplaceTower: int = 0,
    ReplaceSampling: int = 0,
    ReplaceRCentre: float = 0.0,
    ReplaceZCentre: float = 0.0,
    FCalModule: int = 0,
    FCalCopyEtaIndex: Optional[list] = None,
    FCalCopyPhiIndex: Optional[list] = None,
    FCalCopyEta: Optional[list] = None,
    FCalCopyPhi: Optional[list] = None,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Creates and configures a CaloFreeRunningHitRecorderTool instance for ATLAS 64-bit compact ID hit recording.
    FreeRunningBinning is captured directly from FreeRunningFlags.
    """
    if fr_flags is None:
        fr_flags = FreeRunningFlags

    return Configurable(
        ROOT.CaloFreeRunningHitRecorderTool,
        name,
        FreeRunningListKey=FreeRunningListKey,
        FreeRunningBinning=bool(not fr_flags.NoBinning),
        Subdet=Subdet,
        AtlasBarrelEc=AtlasBarrelEc,
        AtlasLArSampling=AtlasLArSampling,
        AtlasLArRegion=AtlasLArRegion,
        AtlasLArPart=AtlasLArPart,
        CellAtlasEtaIndex=CellAtlasEtaIndex if CellAtlasEtaIndex is not None else [],
        NPhiBins=NPhiBins,
        PhiBins=PhiBins if PhiBins is not None else [],
        CellEta=CellEta if CellEta is not None else [],
        CellAtlasSection=CellAtlasSection if CellAtlasSection is not None else [],
        CellAtlasTower=CellAtlasTower if CellAtlasTower is not None else [],
        CellAtlasSampling=CellAtlasSampling if CellAtlasSampling is not None else [],
        CellRCentre=CellRCentre if CellRCentre is not None else [],
        CellZCentre=CellZCentre if CellZCentre is not None else [],
        ReplaceSection=ReplaceSection,
        ReplaceTower=ReplaceTower,
        ReplaceSampling=ReplaceSampling,
        ReplaceRCentre=ReplaceRCentre,
        ReplaceZCentre=ReplaceZCentre,
        FCalModule=FCalModule,
        FCalCopyEtaIndex=FCalCopyEtaIndex if FCalCopyEtaIndex is not None else [],
        FCalCopyPhiIndex=FCalCopyPhiIndex if FCalCopyPhiIndex is not None else [],
        FCalCopyEta=FCalCopyEta if FCalCopyEta is not None else [],
        FCalCopyPhi=FCalCopyPhi if FCalCopyPhi is not None else [],
        OutputLevel=OutputLevel,
    )

