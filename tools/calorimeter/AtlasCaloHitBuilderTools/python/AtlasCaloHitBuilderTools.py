__all__ = [
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
    "configure_atlas_hit_maker",
]

from typing import Any
import ROOT
from GaugiKernel import Configurable, LoggingLevel
from .CaloFreeRunningHitWriter import CaloFreeRunningHitWriter
from CaloHitBuilderTools import (
    CaloGridCellToolCfg,
    CaloBirksLawToolCfg,
    CaloTofCorrectionToolCfg,
    CaloStandardHitRecorderToolCfg,
)


def TileBoxCellToolCfg(name: str = "TileBoxCellTool", **kwargs) -> Configurable:
    """
    Creates and configures a TileBoxCellTool instance for ATLAS Tile (r, z) box geometry.
    """
    return Configurable(ROOT.TileBoxCellTool, name, **kwargs)


def TileDualReadoutSplitToolCfg(name: str = "TileDualReadoutSplitTool", **kwargs) -> Configurable:
    """
    Creates and configures a TileDualReadoutSplitTool instance for PMT energy partition.
    """
    return Configurable(ROOT.TileDualReadoutSplitTool, name, **kwargs)


def TilePmtPropagationTimeToolCfg(name: str = "TilePmtPropagationTimeTool", **kwargs) -> Configurable:
    """
    Creates and configures a TilePmtPropagationTimeTool instance for Tile PMT propagation times.
    """
    return Configurable(ROOT.TilePmtPropagationTimeTool, name, **kwargs)


def LArAccordionToolCfg(name: str = "LArAccordionTool", **kwargs) -> Configurable:
    """
    Creates and configures a LArAccordionTool instance for ATLAS EMB accordion segmentation.
    """
    return Configurable(ROOT.LArAccordionTool, name, **kwargs)


def LArEmecCompartmentToolCfg(name: str = "LArEmecCompartmentTool", **kwargs) -> Configurable:
    """
    Creates and configures a LArEmecCompartmentTool instance for ATLAS EMEC 11-compartment segmentation.
    """
    return Configurable(ROOT.LArEmecCompartmentTool, name, **kwargs)


def LArHecModuleToolCfg(name: str = "LArHecModuleTool", **kwargs) -> Configurable:
    """
    Creates and configures a LArHecModuleTool instance for ATLAS HEC wedge module geometry.
    """
    return Configurable(ROOT.LArHecModuleTool, name, **kwargs)


def LArEmecChargeCollectionToolCfg(name: str = "LArEmecChargeCollectionTool", **kwargs) -> Configurable:
    """
    Creates and configures a LArEmecChargeCollectionTool instance for ATLAS EMEC charge collection.
    """
    return Configurable(ROOT.LArEmecChargeCollectionTool, name, **kwargs)


def LArFCalElectrodeToolCfg(name: str = "LArFCalElectrodeTool", **kwargs) -> Configurable:
    """
    Creates and configures a LArFCalElectrodeTool instance for ATLAS FCAL electrode geometry and frozen shower spots.
    """
    return Configurable(ROOT.LArFCalElectrodeTool, name, **kwargs)


def CaloFreeRunningHitRecorderToolCfg(name: str = "CaloFreeRunningHitRecorderTool", **kwargs) -> Configurable:
    """
    Creates and configures a CaloFreeRunningHitRecorderTool instance for ATLAS 64-bit compact ID hit recording.
    """
    return Configurable(ROOT.CaloFreeRunningHitRecorderTool, name, **kwargs)


def configure_atlas_hit_maker(
    name: str,
    sampling: Any,
    OutputCollectionKey: str = "Hits",
    HistogramPath: str = "Expert",
    OutputLevel: int = LoggingLevel.toC("INFO"),
    DetailedHistograms: bool = False,
    SamplingNoiseStd: float = 0.0,
    ActiveEnergyOnly: bool = False,
    BirksLaw: bool = False,
    AtlasHitTime: bool = False,
    TileDualReadout: int = 0,
    FreeRunningHits: bool = False,
    FreeRunningListKey: str = "FreeRunningHits",
    FreeRunningBinning: bool = True,
    EmecChargeCollection: bool = False,
    EmecChargeTables: str = "",
    EmecChargeFieldMap: str = "",
    EmecChargeHVMap: str = "",
    **extra_kwargs,
) -> Configurable:
    """
    Configures a CaloHitMaker instance for ATLAS Run 4 (GeoV2) detectors.
    Attaches specialist ATLAS tools using the += operator for tool lists.
    """
    maker = Configurable(
        ROOT.CaloHitMaker,
        name,
        OutputCollectionKey=OutputCollectionKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DetailedHistograms=DetailedHistograms,
        SamplingNoiseStd=SamplingNoiseStd,
        ActiveEnergyOnly=ActiveEnergyOnly,
    )

    fcal_module = getattr(sampling, "Module", None)
    if fcal_module is not None:
        # 1. ATLAS FCAL module
        fcal_kwargs = {
            "FCalModule": int(fcal_module),
            "FCalSide": int(sampling.Side),
            "FCalGapVolume": str(sampling.GapVolume),
            "FCalCopyEtaIndex": [int(x) for x in sampling.CopyEtaIndex],
            "FCalCopyPhiIndex": [int(x) for x in sampling.CopyPhiIndex],
            "FCalCopyEta": [float(x) for x in sampling.CopyEta],
            "FCalCopyPhi": [float(x) for x in sampling.CopyPhi],
            "FCalCopyDeltaEta": [float(x) for x in sampling.CopyDeltaEta],
            "FCalCopyDeltaPhi": [float(x) for x in sampling.CopyDeltaPhi],
            "FCalCopyI": [int(x) for x in sampling.CopyI],
            "FCalCopyJ": [int(x) for x in sampling.CopyJ],
            "FCalCopyX": [float(x) for x in sampling.X],
            "FCalCopyY": [float(x) for x in sampling.Y],
            "Sampling": getattr(sampling, "Sampling", 0),
            "Detector": getattr(sampling, "Detector", 0),
            "ActiveEnergyOnly": ActiveEnergyOnly,
            "BcDuration": 25.0,
            "OutputLevel": OutputLevel,
        }
        if hasattr(sampling, "volume") and sampling.volume() is not None:
            fcal_kwargs["ZMin"] = float(sampling.volume().ZMin)
            fcal_kwargs["ZMax"] = float(sampling.volume().ZMax)

        maker.CellIdentifier = LArFCalElectrodeToolCfg(f"{name}_FCalElectrodeTool", **fcal_kwargs)

        if BirksLaw:
            maker.EnergyModifiers += CaloBirksLawToolCfg(
                f"{name}_BirksLawTool",
                BirksLArK=0.0486,
                OutputLevel=OutputLevel,
            )

        if AtlasHitTime:
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

        if FreeRunningHits:
            maker.HitRecorders += CaloFreeRunningHitRecorderToolCfg(
                f"{name}_FreeRunningHitRecorderTool",
                FreeRunningListKey=FreeRunningListKey,
                FreeRunningBinning=FreeRunningBinning,
                Subdet=4,
                FCalModule=int(fcal_module),
                FCalCopyEtaIndex=[int(x) for x in sampling.CopyEtaIndex],
                FCalCopyPhiIndex=[int(x) for x in sampling.CopyPhiIndex],
                FCalCopyEta=[float(x) for x in sampling.CopyEta],
                FCalCopyPhi=[float(x) for x in sampling.CopyPhi],
                OutputLevel=OutputLevel,
            )
        return maker

    # Regular samplings (Tile, EMB, EMEC, HEC, or generic)
    cells = None
    if hasattr(sampling, "sensitive") and sampling.sensitive() is not None:
        cells = getattr(sampling.sensitive(), "Cells", None)

    subdet_type = 0
    common_geo = {
        "Sampling": getattr(sampling, "Sampling", 0),
        "Detector": getattr(sampling, "Detector", 0),
        "Segment": getattr(sampling.sensitive(), "Segment", 0) if hasattr(sampling, "sensitive") and sampling.sensitive() else 0,
        "ActiveEnergyOnly": ActiveEnergyOnly,
        "BcDuration": 25.0,
        "OutputLevel": OutputLevel,
    }
    if hasattr(sampling, "volume") and sampling.volume() is not None:
        common_geo["RMin"] = float(sampling.volume().RMin)
        common_geo["RMax"] = float(sampling.volume().RMax)
        common_geo["ZMin"] = float(sampling.volume().ZMin)
        common_geo["ZMax"] = float(sampling.volume().ZMax)

    if cells and "BoxRMin" in cells and "RadiusModules" not in cells:
        # Tile Calorimeter
        subdet_type = 0
        tile_kwargs = dict(common_geo)
        tile_kwargs.update({
            "CellBoxRMin": [float(x) for x in cells["BoxRMin"]],
            "CellBoxRMax": [float(x) for x in cells["BoxRMax"]],
            "CellBoxZMin": [float(x) for x in cells["BoxZMin"]],
            "CellBoxZMax": [float(x) for x in cells["BoxZMax"]],
            "CellBoxIndex": [int(x) for x in cells["BoxCell"]],
            "CellEta": [float(x) for x in cells["Eta"]],
            "CellDeltaEta": [float(x) for x in cells["DeltaEta"]],
            "PhiBins": sampling.sensitive().PhiBins,
            "SpecialModule": [int(x) for x in cells.get("SpecialModule", [])],
            "SpecialNPmt": [int(x) for x in cells.get("SpecialNPmt", [])],
            "CellNPmt": [int(x) for x in cells.get("NPmt", [])],
            "ReplaceSection": int(cells.get("ReplaceSection", 0)),
            "ReplaceTower": int(cells.get("ReplaceTower", 0)),
            "ReplaceSampling": int(cells.get("ReplaceSampling", 0)),
            "ReplaceRCentre": float(cells.get("ReplaceRCentre", 0.0)),
            "ReplaceZCentre": float(cells.get("ReplaceZCentre", 0.0)),
            "ReplaceCollectionKey": str(cells.get("ReplaceCollectionKey", "")),
            "ReplaceHashBase": int(cells.get("ReplaceHashBase", 0)),
        })
        maker.CellIdentifier = TileBoxCellToolCfg(f"{name}_TileBoxCellTool", **tile_kwargs)

        if BirksLaw:
            maker.EnergyModifiers += CaloBirksLawToolCfg(f"{name}_BirksLawTool", OutputLevel=OutputLevel)

        if TileDualReadout > 0:
            maker.EnergyModifiers += TileDualReadoutSplitToolCfg(
                f"{name}_TileDualReadoutSplitTool",
                TileDualReadout=TileDualReadout,
                UShapePart=int(cells.get("UShapePart", 0)),
                UShapeLayer=int(cells.get("UShapeLayer", 0)),
                CellBoxIndex=[int(x) for x in cells["BoxCell"]],
                CellAtlasSection=[int(x) for x in cells.get("AtlasSection", [])],
                CellAtlasTower=[int(x) for x in cells.get("AtlasTower", [])],
                CellAtlasSampling=[int(x) for x in cells.get("AtlasSampling", [])],
                OutputLevel=OutputLevel,
            )

        maker.TimeCorrection = TilePmtPropagationTimeToolCfg(
            f"{name}_TilePmtPropagationTimeTool",
            PhiBins=sampling.sensitive().PhiBins,
            CellRCentre=[float(x) for x in cells["RCentre"]],
            CellZCentre=[float(x) for x in cells["ZCentre"]],
            ReplaceRCentre=float(cells.get("ReplaceRCentre", 0.0)),
            ReplaceZCentre=float(cells.get("ReplaceZCentre", 0.0)),
            OutputLevel=OutputLevel,
        )

        maker.HitRecorders += CaloStandardHitRecorderToolCfg(
            f"{name}_StandardHitRecorderTool",
            OutputCollectionKey=OutputCollectionKey,
            NoiseStd=SamplingNoiseStd,
            OutputLevel=OutputLevel,
        )

        if FreeRunningHits:
            maker.HitRecorders += CaloFreeRunningHitRecorderToolCfg(
                f"{name}_FreeRunningHitRecorderTool",
                FreeRunningListKey=FreeRunningListKey,
                FreeRunningBinning=FreeRunningBinning,
                Subdet=0,
                PhiBins=sampling.sensitive().PhiBins,
                CellEta=[float(x) for x in cells["Eta"]],
                CellAtlasSection=[int(x) for x in cells.get("AtlasSection", [])],
                CellAtlasTower=[int(x) for x in cells.get("AtlasTower", [])],
                CellAtlasSampling=[int(x) for x in cells.get("AtlasSampling", [])],
                CellRCentre=[float(x) for x in cells["RCentre"]],
                CellZCentre=[float(x) for x in cells["ZCentre"]],
                ReplaceSection=int(cells.get("ReplaceSection", 0)),
                ReplaceTower=int(cells.get("ReplaceTower", 0)),
                ReplaceSampling=int(cells.get("ReplaceSampling", 0)),
                ReplaceRCentre=float(cells.get("ReplaceRCentre", 0.0)),
                ReplaceZCentre=float(cells.get("ReplaceZCentre", 0.0)),
                OutputLevel=OutputLevel,
            )
        return maker

    elif cells and "EmbSampling" in cells:
        # EMB Accordion
        subdet_type = 1
        emb_kwargs = dict(common_geo)
        emb_kwargs.update({
            "EmbSampling": int(cells["EmbSampling"]),
            "EmbMode": int(cells["EmbMode"]),
            "EmbRegion": int(cells["EmbRegion"]),
            "EmbZShift": float(cells.get("EmbZShift", 0.0)),
            "EmbSampSeg": bool(cells.get("EmbSampSeg", False)),
            "PsbR0": float(cells.get("PsbR0", 0.0)),
            "EtaBins": sampling.sensitive().EtaBins,
            "PhiBins": sampling.sensitive().PhiBins,
            "CellEta": [float(x) for x in cells["Eta"]],
            "CellDeltaEta": [float(x) for x in cells["DeltaEta"]],
        })
        maker.CellIdentifier = LArAccordionToolCfg(f"{name}_LArAccordionTool", **emb_kwargs)

    elif cells and "EmecCompartment" in cells:
        # EMEC Compartment
        subdet_type = 2
        emec_kwargs = dict(common_geo)
        emec_kwargs.update({
            "EmecCompartment": int(cells["EmecCompartment"]),
            "EmecEtaScale": float(cells["EmecEtaScale"]),
            "EmecEtaOffset": float(cells["EmecEtaOffset"]),
            "EmecMaxEta": int(cells["EmecMaxEta"]),
            "EmecFocalShift": float(cells["EmecFocalShift"]),
            "EmecZSep12": [int(x) for x in cells["EmecZSep12"]],
            "EmecZSep23": [int(x) for x in cells["EmecZSep23"]],
            "EmecZInner": [int(x) for x in cells["EmecZInner"]],
            "EmecWheelRMin": [float(x) for x in cells["EmecWheelRMin"]],
            "EmecWheelRMax": [float(x) for x in cells["EmecWheelRMax"]],
            "EmecWheelZMin": [float(x) for x in cells["EmecWheelZMin"]],
            "EmecWheelZMax": [float(x) for x in cells["EmecWheelZMax"]],
            "EtaBins": sampling.sensitive().EtaBins,
            "PhiBins": sampling.sensitive().PhiBins,
            "CellEta": [float(x) for x in cells["Eta"]],
            "CellDeltaEta": [float(x) for x in cells["DeltaEta"]],
        })
        maker.CellIdentifier = LArEmecCompartmentToolCfg(f"{name}_LArEmecCompartmentTool", **emec_kwargs)

        if EmecChargeCollection:
            maker.EnergyModifiers += LArEmecChargeCollectionToolCfg(
                f"{name}_LArEmecChargeCollectionTool",
                TablesFile=str(EmecChargeTables),
                FieldMapFile=str(EmecChargeFieldMap),
                HVMapFile=str(EmecChargeHVMap),
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
                PhiShift=float(getattr(sampling.sensitive(), "PhiShift", 0.0) or 0.0),
                OutputLevel=OutputLevel,
            )

    elif cells and "RadiusModules" in cells:
        # HEC Module
        subdet_type = 3
        hec_kwargs = dict(common_geo)
        hec_kwargs.update({
            "CellRadiusModules": int(cells["RadiusModules"]),
            "EtaBins": sampling.sensitive().EtaBins,
            "PhiBins": sampling.sensitive().PhiBins,
            "CellEta": [float(x) for x in cells["Eta"]],
            "CellDeltaEta": [float(x) for x in cells["DeltaEta"]],
            "CellBoxRMin": [float(x) for x in cells.get("BoxRMin", [])],
            "CellBoxRMax": [float(x) for x in cells.get("BoxRMax", [])],
            "CellBoxZMin": [float(x) for x in cells.get("BoxZMin", [])],
            "CellBoxZMax": [float(x) for x in cells.get("BoxZMax", [])],
            "CellBoxIndex": [int(x) for x in cells.get("BoxCell", [])],
            "CellAtlasEtaIndex": [int(x) for x in cells.get("AtlasEtaIndex", [])],
            "AtlasBarrelEc": int(cells.get("AtlasBarrelEc", 0)),
            "AtlasLArSampling": int(cells.get("AtlasLArSampling", 0)),
            "AtlasLArRegion": int(cells.get("AtlasLArRegion", 0)),
        })
        maker.CellIdentifier = LArHecModuleToolCfg(f"{name}_LArHecModuleTool", **hec_kwargs)

    else:
        # Universal grid fallback
        subdet_type = 1
        grid_kwargs = dict(common_geo)
        if hasattr(sampling, "sensitive") and sampling.sensitive() is not None:
            grid_kwargs["EtaBins"] = sampling.sensitive().EtaBins
            grid_kwargs["PhiBins"] = sampling.sensitive().PhiBins
        maker.CellIdentifier = CaloGridCellToolCfg(f"{name}_GridCellTool", **grid_kwargs)

    if BirksLaw:
        birks_k = 0.05832
        if hasattr(sampling, "sensitive") and sampling.sensitive() is not None:
            birks_k = getattr(sampling.sensitive(), "BirksLArK", 0.05832) or 0.05832
        maker.EnergyModifiers += CaloBirksLawToolCfg(
            f"{name}_BirksLawTool",
            BirksLArK=float(birks_k),
            OutputLevel=OutputLevel,
        )

    if AtlasHitTime:
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

    if FreeRunningHits and cells and "AtlasEtaIndex" in cells:
        maker.HitRecorders += CaloFreeRunningHitRecorderToolCfg(
            f"{name}_FreeRunningHitRecorderTool",
            FreeRunningListKey=FreeRunningListKey,
            FreeRunningBinning=FreeRunningBinning,
            Subdet=subdet_type,
            AtlasBarrelEc=int(cells.get("AtlasBarrelEc", 1)),
            AtlasLArSampling=int(cells.get("AtlasLArSampling", 0)),
            AtlasLArRegion=int(cells.get("AtlasLArRegion", 0)),
            AtlasLArPart=int(cells.get("AtlasLArPart", 1)),
            CellAtlasEtaIndex=[int(x) for x in cells["AtlasEtaIndex"]],
            NPhiBins=len(sampling.sensitive().PhiBins) - 1 if hasattr(sampling, "sensitive") and sampling.sensitive() and hasattr(sampling.sensitive(), "PhiBins") else 64,
            PhiBins=sampling.sensitive().PhiBins if hasattr(sampling, "sensitive") and sampling.sensitive() and hasattr(sampling.sensitive(), "PhiBins") else [],
            CellEta=[float(x) for x in cells["Eta"]],
            OutputLevel=OutputLevel,
        )

    return maker
