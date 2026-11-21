"""
CaloHitMaker configuration helper.

Creates and configures ROOT.CaloHitMaker algorithm instances for calorimeter hit creation:
- CaloHitMakerCfg: generic cylindrical/universal detector geometry (GeoV1).
- AtlasCaloHitMakerCfg: ATLAS Run 4 calorimeter geometry (GeoV2).
"""

from typing import Any, Optional
import ROOT

from GaugiKernel import Configurable, LoggingLevel
from CaloHitBuilder.CaloHitFlags import CaloHitFlags, FreeRunningFlags
from CaloHitTools import (
    CaloGridCellToolCfg,
    CaloBirksLawToolCfg,
    CaloTofCorrectionToolCfg,
    CaloStandardHitRecorderToolCfg,
)
from AtlasCaloHitTools import (
    validate_atlas_hit_flags,
    TileBoxCellToolCfg,
    TileDualReadoutSplitToolCfg,
    TilePmtPropagationTimeToolCfg,
    LArAccordionToolCfg,
    LArEmecCompartmentToolCfg,
    LArHecModuleToolCfg,
    LArFCalElectrodeToolCfg,
    LArEmecChargeCollectionToolCfg,
    CaloFreeRunningHitRecorderToolCfg,
)

__all__ = ["CaloHitMakerCfg", "AtlasCaloHitMakerCfg", "CaloHitMaker"]


def CaloHitMakerCfg(
    name: str,
    sampling: Any,
    flags: Optional[CaloHitFlags] = None,
    fr_flags: Optional[FreeRunningFlags] = None,
    OutputCollectionKey: str = "Hits",
    HistogramPath: str = "Expert",
    OutputLevel: int = LoggingLevel.toC("INFO"),
    DetailedHistograms: bool = False,
    SamplingNoiseStd: float = 0.0,
) -> Configurable:
    """
    Configures a generic detector-agnostic CaloHitMaker instance using universal tools.
    Connects tools using += operator for tool lists.
    """
    if flags is None:
        flags = CaloHitFlags

    maker = Configurable(
        ROOT.CaloHitMaker,
        name,
        OutputCollectionKey=OutputCollectionKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DetailedHistograms=DetailedHistograms,
        SamplingNoiseStd=SamplingNoiseStd,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
    )

    sensitive = sampling.sensitive() if hasattr(sampling, "sensitive") else None
    volume = sampling.volume() if hasattr(sampling, "volume") else None

    maker.CellIdentifier = CaloGridCellToolCfg(
        f"{name}_GridCellTool",
        EtaBins=getattr(sensitive, "EtaBins", []) if sensitive else [],
        PhiBins=getattr(sensitive, "PhiBins", []) if sensitive else [],
        Sampling=getattr(sampling, "Sampling", 0),
        Segment=getattr(sensitive, "Segment", 0) if sensitive else 0,
        Detector=getattr(sampling, "Detector", 0),
        ZMin=float(getattr(volume, "ZMin", 0.0)) if volume else 0.0,
        ZMax=float(getattr(volume, "ZMax", 0.0)) if volume else 0.0,
        RMin=float(getattr(volume, "RMin", 0.0)) if volume else 0.0,
        RMax=float(getattr(volume, "RMax", 0.0)) if volume else 0.0,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
        BcDuration=25.0,
        BcidStart=getattr(sampling, "BunchIdStart", -7),
        BcidEnd=getattr(sampling, "BunchIdEnd", 7),
        OutputLevel=OutputLevel,
    )

    if flags.BirksLaw:
        birks_k = 0.05832
        if sensitive is not None and hasattr(sensitive, "BirksLArK"):
            birks_k = getattr(sensitive, "BirksLArK", 0.05832) or 0.05832
        maker.EnergyModifiers += CaloBirksLawToolCfg(
            f"{name}_BirksLawTool",
            BirksLArK=birks_k,
            OutputLevel=OutputLevel,
        )

    if flags.AtlasHitTime:
        maker.TimeCorrection = CaloTofCorrectionToolCfg(
            f"{name}_TofCorrectionTool",
            ApplyTof=True,
            OutputLevel=OutputLevel,
        )

    maker.HitRecorders += CaloStandardHitRecorderToolCfg(
        f"{name}_StandardHitRecorderTool",
        OutputCollectionKey=OutputCollectionKey,
        NoiseStd=SamplingNoiseStd,
        OutputLevel=OutputLevel,
    )

    return maker


def AtlasCaloHitMakerCfg(
    name: str,
    sampling: Any,
    flags: Optional[CaloHitFlags] = None,
    fr_flags: Optional[FreeRunningFlags] = None,
    OutputCollectionKey: str = "Hits",
    HistogramPath: str = "Expert",
    OutputLevel: int = LoggingLevel.toC("INFO"),
    DetailedHistograms: bool = False,
    SamplingNoiseStd: float = 0.0,
    FreeRunningListKey: str = "FreeRunningHits",
) -> Configurable:
    """
    Configures a CaloHitMaker instance for ATLAS Run 4 (GeoV2) detectors.
    Defaults for simulation properties are captured from CaloHitFlags and FreeRunningFlags.
    Attaches specialist ATLAS tools using the += operator for tool lists.
    """
    if flags is None:
        flags = CaloHitFlags
    if fr_flags is None:
        fr_flags = FreeRunningFlags

    validate_atlas_hit_flags(flags=flags, fr_flags=fr_flags)

    maker = Configurable(
        ROOT.CaloHitMaker,
        name,
        OutputCollectionKey=OutputCollectionKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DetailedHistograms=DetailedHistograms,
        SamplingNoiseStd=SamplingNoiseStd,
        ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
    )

    volume = sampling.volume() if hasattr(sampling, "volume") else None
    sensitive = sampling.sensitive() if hasattr(sampling, "sensitive") else None
    z_min = float(volume.ZMin) if volume is not None else 0.0
    z_max = float(volume.ZMax) if volume is not None else 0.0
    r_min = float(volume.RMin) if volume is not None else 0.0
    r_max = float(volume.RMax) if volume is not None else 0.0
    sampling_id = getattr(sampling, "Sampling", 0)
    detector_id = getattr(sampling, "Detector", 0)
    segment_id = getattr(sensitive, "Segment", 0) if sensitive is not None else 0
    bcid_start = getattr(sampling, "BunchIdStart", -7)
    bcid_end = getattr(sampling, "BunchIdEnd", 7)
    phi_bins = sensitive.PhiBins if sensitive is not None and hasattr(sensitive, "PhiBins") else []

    fcal_module = getattr(sampling, "Module", None)
    cells = getattr(sensitive, "Cells", None) if sensitive is not None else None

    # Determine Birks saturation parameter for this subdetector
    birks_k = 0.0486 if fcal_module is not None else (
        getattr(sensitive, "BirksLArK", 0.05832) if sensitive is not None else 0.05832
    )
    birks_k = birks_k or 0.05832

    # 1. Energy saturation (Birks' Law applied first for all detectors)
    if flags.BirksLaw:
        maker.EnergyModifiers += CaloBirksLawToolCfg(
            f"{name}_BirksLawTool",
            BirksLArK=float(birks_k),
            OutputLevel=OutputLevel,
        )

    is_tile = False
    is_fcal = False
    subdet_type = 0

    # 2. Configure detector-specific tools and properties
    if fcal_module is not None:
        # FCAL module
        is_fcal = True
        subdet_type = 4
        maker.CellIdentifier = LArFCalElectrodeToolCfg(
            f"{name}_FCalElectrodeTool",
            FCalModule=int(fcal_module),
            FCalSide=int(sampling.Side),
            FCalGapVolume=str(sampling.GapVolume),
            FCalCopyEtaIndex=[int(x) for x in sampling.CopyEtaIndex],
            FCalCopyPhiIndex=[int(x) for x in sampling.CopyPhiIndex],
            FCalCopyEta=[float(x) for x in sampling.CopyEta],
            FCalCopyPhi=[float(x) for x in sampling.CopyPhi],
            FCalCopyDeltaEta=[float(x) for x in sampling.CopyDeltaEta],
            FCalCopyDeltaPhi=[float(x) for x in sampling.CopyDeltaPhi],
            FCalCopyI=[int(x) for x in sampling.CopyI],
            FCalCopyJ=[int(x) for x in sampling.CopyJ],
            FCalCopyX=[float(x) for x in sampling.X],
            FCalCopyY=[float(x) for x in sampling.Y],
            Sampling=sampling_id,
            Detector=detector_id,
            Segment=segment_id,
            ZMin=z_min,
            ZMax=z_max,
            flags=flags,
            BcDuration=25.0,
            BcidStart=bcid_start,
            BcidEnd=bcid_end,
            OutputLevel=OutputLevel,
        )

    elif cells and "BoxRMin" in cells and "RadiusModules" not in cells:
        # Tile Calorimeter
        is_tile = True
        subdet_type = 0
        maker.CellIdentifier = TileBoxCellToolCfg(
            f"{name}_TileBoxCellTool",
            Sampling=sampling_id,
            Segment=segment_id,
            Detector=detector_id,
            ZMin=z_min,
            ZMax=z_max,
            RMin=r_min,
            RMax=r_max,
            flags=flags,
            BcDuration=25.0,
            BcidStart=bcid_start,
            BcidEnd=bcid_end,
            PhiBins=phi_bins,
            CellEta=[float(x) for x in cells["Eta"]],
            CellDeltaEta=[float(x) for x in cells["DeltaEta"]],
            CellBoxRMin=[float(x) for x in cells["BoxRMin"]],
            CellBoxRMax=[float(x) for x in cells["BoxRMax"]],
            CellBoxZMin=[float(x) for x in cells["BoxZMin"]],
            CellBoxZMax=[float(x) for x in cells["BoxZMax"]],
            CellBoxIndex=[int(x) for x in cells["BoxCell"]],
            CellNPmt=[int(x) for x in cells.get("NPmt", [])],
            SpecialModule=[int(x) for x in cells.get("SpecialModule", [])],
            SpecialNPmt=[int(x) for x in cells.get("SpecialNPmt", [])],
            ReplaceSection=int(cells.get("ReplaceSection", 0)),
            ReplaceTower=int(cells.get("ReplaceTower", 0)),
            ReplaceSampling=int(cells.get("ReplaceSampling", 0)),
            ReplaceRCentre=float(cells.get("ReplaceRCentre", 0.0)),
            ReplaceZCentre=float(cells.get("ReplaceZCentre", 0.0)),
            ReplaceCollectionKey=str(cells.get("ReplaceCollectionKey", "")),
            ReplaceHashBase=int(cells.get("ReplaceHashBase", 0)),
            CellAtlasSection=[int(x) for x in cells.get("AtlasSection", [])],
            CellAtlasTower=[int(x) for x in cells.get("AtlasTower", [])],
            CellAtlasSampling=[int(x) for x in cells.get("AtlasSampling", [])],
            CellRCentre=[float(x) for x in cells.get("RCentre", [])],
            CellZCentre=[float(x) for x in cells.get("ZCentre", [])],
            OutputLevel=OutputLevel,
        )

        if flags.TileDualReadout:
            maker.EnergyModifiers += TileDualReadoutSplitToolCfg(
                f"{name}_TileDualReadoutSplitTool",
                Sampling=sampling_id,
                flags=flags,
                PhiBins=phi_bins,
                UShapePart=int(cells.get("UShapePart", 0)),
                UShapeLayer=int(cells.get("UShapeLayer", 0)),
                OutputLevel=OutputLevel,
            )

        maker.TimeCorrection = TilePmtPropagationTimeToolCfg(
            f"{name}_TilePmtPropagationTimeTool",
            PhiBins=phi_bins,
            CellRCentre=[float(x) for x in cells.get("RCentre", [])],
            CellZCentre=[float(x) for x in cells.get("ZCentre", [])],
            ReplaceRCentre=float(cells.get("ReplaceRCentre", 0.0)),
            ReplaceZCentre=float(cells.get("ReplaceZCentre", 0.0)),
            OutputLevel=OutputLevel,
        )

    elif cells and "EmbSampling" in cells:
        # EMB Accordion
        subdet_type = 1
        maker.CellIdentifier = LArAccordionToolCfg(
            f"{name}_LArAccordionTool",
            Sampling=sampling_id,
            Segment=segment_id,
            Detector=detector_id,
            ZMin=z_min,
            ZMax=z_max,
            RMin=r_min,
            RMax=r_max,
            flags=flags,
            BcDuration=25.0,
            BcidStart=bcid_start,
            BcidEnd=bcid_end,
            PhiBins=phi_bins,
            CellEta=[float(x) for x in cells["Eta"]],
            CellDeltaEta=[float(x) for x in cells["DeltaEta"]],
            EmbMode=int(cells["EmbMode"]),
            EmbSampling=int(cells["EmbSampling"]),
            EmbRegion=int(cells["EmbRegion"]),
            EmbZShift=float(cells.get("EmbZShift", 0.0)),
            PsbR0=float(cells.get("PsbR0", 0.0)),
            EmbSampSeg=bool(cells.get("EmbSampSeg", False)),
            AtlasBarrelEc=int(cells.get("AtlasBarrelEc", 0)),
            AtlasLArSampling=int(cells.get("AtlasLArSampling", 0)),
            AtlasLArRegion=int(cells.get("AtlasLArRegion", 0)),
            CellAtlasEtaIndex=[int(x) for x in cells.get("AtlasEtaIndex", [])],
            PhiShift=float(getattr(sensitive, "PhiShift", 0.0) or 0.0),
            OutputLevel=OutputLevel,
        )

    elif cells and "EmecCompartment" in cells:
        # EMEC Compartment
        subdet_type = 2
        maker.CellIdentifier = LArEmecCompartmentToolCfg(
            f"{name}_LArEmecCompartmentTool",
            Sampling=sampling_id,
            Segment=segment_id,
            Detector=detector_id,
            ZMin=z_min,
            ZMax=z_max,
            RMin=r_min,
            RMax=r_max,
            flags=flags,
            BcDuration=25.0,
            BcidStart=bcid_start,
            BcidEnd=bcid_end,
            PhiBins=phi_bins,
            CellEta=[float(x) for x in cells["Eta"]],
            CellDeltaEta=[float(x) for x in cells["DeltaEta"]],
            EmecCompartment=int(cells["EmecCompartment"]),
            EmecEtaScale=float(cells["EmecEtaScale"]),
            EmecEtaOffset=float(cells["EmecEtaOffset"]),
            EmecMaxEta=int(cells["EmecMaxEta"]),
            EmecFocalShift=float(cells["EmecFocalShift"]),
            EmecZSep12=[int(x) for x in cells["EmecZSep12"]],
            EmecZSep23=[int(x) for x in cells["EmecZSep23"]],
            EmecZInner=[int(x) for x in cells["EmecZInner"]],
            EmecWheelRMin=[float(x) for x in cells["EmecWheelRMin"]],
            EmecWheelRMax=[float(x) for x in cells["EmecWheelRMax"]],
            EmecWheelZMin=[float(x) for x in cells["EmecWheelZMin"]],
            EmecWheelZMax=[float(x) for x in cells["EmecWheelZMax"]],
            AtlasBarrelEc=int(cells.get("AtlasBarrelEc", 0)),
            AtlasLArSampling=int(cells.get("AtlasLArSampling", 0)),
            AtlasLArRegion=int(cells.get("AtlasLArRegion", 0)),
            CellAtlasEtaIndex=[int(x) for x in cells.get("AtlasEtaIndex", [])],
            PhiShift=float(getattr(sensitive, "PhiShift", 0.0) or 0.0),
            OutputLevel=OutputLevel,
        )

        if fr_flags.EmecChargeCollection:
            maker.EnergyModifiers += LArEmecChargeCollectionToolCfg(
                f"{name}_LArEmecChargeCollectionTool",
                fr_flags=fr_flags,
                EmecCompartment=int(cells["EmecCompartment"]),
                EmecFocalShift=float(cells["EmecFocalShift"]),
                ZMin=z_min,
                ZMax=z_max,
                OutputLevel=OutputLevel,
            )

    elif cells and "RadiusModules" in cells:
        # HEC Module
        subdet_type = 3
        maker.CellIdentifier = LArHecModuleToolCfg(
            f"{name}_LArHecModuleTool",
            Sampling=sampling_id,
            Segment=segment_id,
            Detector=detector_id,
            ZMin=z_min,
            ZMax=z_max,
            RMin=r_min,
            RMax=r_max,
            flags=flags,
            BcDuration=25.0,
            BcidStart=bcid_start,
            BcidEnd=bcid_end,
            PhiBins=phi_bins,
            CellEta=[float(x) for x in cells["Eta"]],
            CellDeltaEta=[float(x) for x in cells["DeltaEta"]],
            CellBoxRMin=[float(x) for x in cells.get("BoxRMin", [])],
            CellBoxRMax=[float(x) for x in cells.get("BoxRMax", [])],
            CellBoxZMin=[float(x) for x in cells.get("BoxZMin", [])],
            CellBoxZMax=[float(x) for x in cells.get("BoxZMax", [])],
            CellBoxIndex=[int(x) for x in cells.get("BoxCell", [])],
            CellRadiusModules=int(cells["RadiusModules"]),
            AtlasBarrelEc=int(cells.get("AtlasBarrelEc", 0)),
            AtlasLArSampling=int(cells.get("AtlasLArSampling", 0)),
            AtlasLArRegion=int(cells.get("AtlasLArRegion", 0)),
            CellAtlasEtaIndex=[int(x) for x in cells.get("AtlasEtaIndex", [])],
            PhiShift=float(getattr(sensitive, "PhiShift", 0.0) or 0.0),
            OutputLevel=OutputLevel,
        )

    else:
        # Universal grid fallback
        subdet_type = 1
        maker.CellIdentifier = CaloGridCellToolCfg(
            f"{name}_GridCellTool",
            EtaBins=getattr(sensitive, "EtaBins", []) if sensitive else [],
            PhiBins=phi_bins,
            Sampling=sampling_id,
            Segment=segment_id,
            Detector=detector_id,
            ZMin=z_min,
            ZMax=z_max,
            RMin=r_min,
            RMax=r_max,
            ActiveEnergyOnly=bool(flags.ActiveEnergyOnly),
            BcDuration=25.0,
            BcidStart=bcid_start,
            BcidEnd=bcid_end,
            OutputLevel=OutputLevel,
        )

    # 3. Common timing and recording tools (outside the conditional)
    if flags.AtlasHitTime and not is_tile:
        maker.TimeCorrection = CaloTofCorrectionToolCfg(
            f"{name}_TofCorrectionTool",
            ApplyTof=True,
            OutputLevel=OutputLevel,
        )

    maker.HitRecorders += CaloStandardHitRecorderToolCfg(
        f"{name}_StandardHitRecorderTool",
        OutputCollectionKey=OutputCollectionKey,
        NoiseStd=SamplingNoiseStd,
        OutputLevel=OutputLevel,
    )

    if fr_flags.Enable:
        if is_fcal:
            maker.HitRecorders += CaloFreeRunningHitRecorderToolCfg(
                f"{name}_FreeRunningHitRecorderTool",
                fr_flags=fr_flags,
                FreeRunningListKey=FreeRunningListKey,
                Subdet=4,
                FCalModule=int(fcal_module),
                FCalCopyEtaIndex=[int(x) for x in sampling.CopyEtaIndex],
                FCalCopyPhiIndex=[int(x) for x in sampling.CopyPhiIndex],
                FCalCopyEta=[float(x) for x in sampling.CopyEta],
                FCalCopyPhi=[float(x) for x in sampling.CopyPhi],
                OutputLevel=OutputLevel,
            )
        elif is_tile:
            maker.HitRecorders += CaloFreeRunningHitRecorderToolCfg(
                f"{name}_FreeRunningHitRecorderTool",
                fr_flags=fr_flags,
                FreeRunningListKey=FreeRunningListKey,
                Subdet=0,
                PhiBins=phi_bins,
                CellEta=[float(x) for x in cells["Eta"]],
                CellAtlasSection=[int(x) for x in cells.get("AtlasSection", [])],
                CellAtlasTower=[int(x) for x in cells.get("AtlasTower", [])],
                CellAtlasSampling=[int(x) for x in cells.get("AtlasSampling", [])],
                CellRCentre=[float(x) for x in cells.get("RCentre", [])],
                CellZCentre=[float(x) for x in cells.get("ZCentre", [])],
                ReplaceSection=int(cells.get("ReplaceSection", 0)),
                ReplaceTower=int(cells.get("ReplaceTower", 0)),
                ReplaceSampling=int(cells.get("ReplaceSampling", 0)),
                ReplaceRCentre=float(cells.get("ReplaceRCentre", 0.0)),
                ReplaceZCentre=float(cells.get("ReplaceZCentre", 0.0)),
                OutputLevel=OutputLevel,
            )
        elif cells and "AtlasEtaIndex" in cells:
            n_phi_bins = len(phi_bins) - 1 if len(phi_bins) > 1 else 64
            maker.HitRecorders += CaloFreeRunningHitRecorderToolCfg(
                f"{name}_FreeRunningHitRecorderTool",
                fr_flags=fr_flags,
                FreeRunningListKey=FreeRunningListKey,
                Subdet=subdet_type,
                AtlasBarrelEc=int(cells.get("AtlasBarrelEc", 1)),
                AtlasLArSampling=int(cells.get("AtlasLArSampling", 0)),
                AtlasLArRegion=int(cells.get("AtlasLArRegion", 0)),
                AtlasLArPart=int(cells.get("AtlasLArPart", 1)),
                CellAtlasEtaIndex=[int(x) for x in cells["AtlasEtaIndex"]],
                NPhiBins=n_phi_bins,
                PhiBins=phi_bins,
                CellEta=[float(x) for x in cells["Eta"]],
                OutputLevel=OutputLevel,
            )

    return maker


CaloHitMaker = CaloHitMakerCfg
