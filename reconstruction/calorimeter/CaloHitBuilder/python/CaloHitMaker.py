"""
CaloHitMaker configuration helper.

Creates a Configurable instance for ROOT.CaloHitMaker bound to a specific detector sampling.
"""

from typing import Any, Optional, Dict
import ROOT

from GaugiKernel import LoggingLevel, Configurable

__all__ = ["CaloHitMakerCfg", "CaloHitMaker"]


def CaloHitMakerCfg(
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
    **extra_kwargs,
) -> Configurable:
    """
    Configures and returns a CaloHitMaker algorithm instance for a given calorimeter sampling.

    Args:
        name: Name of the algorithm instance.
        sampling: Calorimeter sampling descriptor object (from geometry configuration).
        OutputCollectionKey: SG key for the output hit collection.
        HistogramPath: Base path in histogram service.
        OutputLevel: Logging verbosity level.
        DetailedHistograms: If True, book and fill fine-grained diagnostic histograms.
        SamplingNoiseStd: Noise standard deviation (MeV) for time-of-flight thresholding.
        ActiveEnergyOnly: Keep only the energy deposited in the active medium.
        BirksLaw: Apply Birks' law in scintillator and liquid argon.
        AtlasHitTime: Bunch crossing from the ATLAS simulation time.
        TileDualReadout: Dual readout of tile cells (0=off, 1=ATLAS U-shape, 2=linear).

    Returns:
        Configurable: Configured ROOT.CaloHitMaker algorithm wrapper.
    """
    props: Dict[str, Any] = dict(
        OutputCollectionKey=OutputCollectionKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DetailedHistograms=DetailedHistograms,
        SamplingNoiseStd=SamplingNoiseStd,
        ActiveEnergyOnly=ActiveEnergyOnly,
        BirksLaw=BirksLaw,
        AtlasHitTime=AtlasHitTime,
        TileDualReadout=TileDualReadout,
    )

    if hasattr(sampling, "sensitive") and sampling.sensitive() is not None:
        props["EtaBins"] = sampling.sensitive().EtaBins
        props["PhiBins"] = sampling.sensitive().PhiBins
        props["Segment"] = sampling.sensitive().Segment

        cells = getattr(sampling.sensitive(), "Cells", None)
        if cells:
            props["CellEta"] = [float(x) for x in cells["Eta"]]
            props["CellDeltaEta"] = [float(x) for x in cells["DeltaEta"]]
            if "BoxRMin" in cells:
                props["CellBoxRMin"] = [float(x) for x in cells["BoxRMin"]]
                props["CellBoxRMax"] = [float(x) for x in cells["BoxRMax"]]
                props["CellBoxZMin"] = [float(x) for x in cells["BoxZMin"]]
                props["CellBoxZMax"] = [float(x) for x in cells["BoxZMax"]]
                props["CellBoxIndex"] = [int(x) for x in cells["BoxCell"]]
            if "EmecCompartment" in cells:
                props["EmecCompartment"] = int(cells["EmecCompartment"])
                props["EmecEtaScale"] = float(cells["EmecEtaScale"])
                props["EmecEtaOffset"] = float(cells["EmecEtaOffset"])
                props["EmecMaxEta"] = int(cells["EmecMaxEta"])
                props["EmecFocalShift"] = float(cells["EmecFocalShift"])
                for key in ("EmecZSep12", "EmecZSep23", "EmecZInner"):
                    props[key] = [int(x) for x in cells[key]]
                for key in ("EmecWheelRMin", "EmecWheelRMax", "EmecWheelZMin", "EmecWheelZMax"):
                    props[key] = [float(x) for x in cells[key]]
            if "EmbSampling" in cells:
                props["EmbMode"] = int(cells["EmbMode"])
                props["EmbSampling"] = int(cells["EmbSampling"])
                props["EmbRegion"] = int(cells["EmbRegion"])
                if "EmbZShift" in cells:
                    props["EmbZShift"] = float(cells["EmbZShift"])
            if "EmbSampSeg" in cells:
                props["EmbSampSeg"] = bool(cells["EmbSampSeg"])
            if "PsbR0" in cells:
                props["PsbR0"] = float(cells["PsbR0"])
            if "RadiusModules" in cells:
                props["CellRadiusModules"] = int(cells["RadiusModules"])
            if "AtlasLArPart" in cells:
                props["AtlasLArPart"] = int(cells["AtlasLArPart"])
                props["AtlasBarrelEc"] = int(cells["AtlasBarrelEc"])
            if "NPmt" in cells:
                props["CellNPmt"] = [int(x) for x in cells["NPmt"]]
            if "UShapePart" in cells:
                props["UShapePart"] = int(cells["UShapePart"])
                props["UShapeLayer"] = int(cells["UShapeLayer"])
            if "SpecialModule" in cells:
                props["SpecialModule"] = [int(x) for x in cells["SpecialModule"]]
                props["SpecialNPmt"] = [int(x) for x in cells["SpecialNPmt"]]
            if "ReplaceSection" in cells:
                props["ReplaceRCentre"] = float(cells["ReplaceRCentre"])
                props["ReplaceZCentre"] = float(cells["ReplaceZCentre"])
            if "ReplaceCollectionKey" in cells:
                props["ReplaceCollectionKey"] = str(cells["ReplaceCollectionKey"])
                props["ReplaceHashBase"] = int(cells["ReplaceHashBase"])
            if "AtlasSection" in cells:
                props["CellRCentre"] = [float(x) for x in cells["RCentre"]]
                props["CellZCentre"] = [float(x) for x in cells["ZCentre"]]

        phi_shift = getattr(sampling.sensitive(), "PhiShift", None)
        if phi_shift:
            props["PhiShift"] = float(phi_shift)

        birks_k = getattr(sampling.sensitive(), "BirksLArK", None)
        if birks_k:
            props["BirksLArK"] = float(birks_k)

    if hasattr(sampling, "volume") and sampling.volume() is not None:
        props["RMin"] = sampling.volume().RMin
        props["RMax"] = sampling.volume().RMax
        props["ZMin"] = sampling.volume().ZMin
        props["ZMax"] = sampling.volume().ZMax

    if hasattr(sampling, "Sampling"):
        props["Sampling"] = sampling.Sampling
    if hasattr(sampling, "Detector"):
        props["Detector"] = sampling.Detector
    if hasattr(sampling, "BunchIdStart"):
        props["BunchIdStart"] = sampling.BunchIdStart
    if hasattr(sampling, "BunchIdEnd"):
        props["BunchIdEnd"] = sampling.BunchIdEnd
    props["BunchDuration"] = 25

    # ATLAS FCal module configuration
    fcal_module = getattr(sampling, "Module", None)
    if fcal_module is not None:
        props["FCalModule"] = int(fcal_module)
        props["FCalSide"] = int(sampling.Side)
        props["FCalGapVolume"] = sampling.GapVolume
        props["FCalCopyEtaIndex"] = [int(x) for x in sampling.CopyEtaIndex]
        props["FCalCopyPhiIndex"] = [int(x) for x in sampling.CopyPhiIndex]
        props["FCalCopyEta"] = [float(x) for x in sampling.CopyEta]
        props["FCalCopyPhi"] = [float(x) for x in sampling.CopyPhi]
        props["FCalCopyDeltaEta"] = [float(x) for x in sampling.CopyDeltaEta]
        props["FCalCopyDeltaPhi"] = [float(x) for x in sampling.CopyDeltaPhi]
        props["FCalCopyI"] = [int(x) for x in sampling.CopyI]
        props["FCalCopyJ"] = [int(x) for x in sampling.CopyJ]
        props["FCalCopyX"] = [float(x) for x in sampling.X]
        props["FCalCopyY"] = [float(x) for x in sampling.Y]

    props.update(extra_kwargs)
    return Configurable(ROOT.CaloHitMaker, name, **props)


CaloHitMaker = CaloHitMakerCfg
