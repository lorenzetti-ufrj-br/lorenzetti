"""
CaloCellMaker configuration helper.

Creates a Configurable instance for ROOT.CaloCellMaker for a specific detector sampling.
"""

from typing import Any
import ROOT

from GaugiKernel import Configurable, LoggingLevel

__all__ = ["CaloCellMakerCfg", "CaloCellMaker"]


def CaloCellMakerCfg(
    name: str,
    sampling: Any,
    InputHitsKey: str = "Hits",
    OutputCollectionKey: str = "Collection",
    OutputLevel: int = LoggingLevel.toC("INFO"),
    DetailedHistograms: bool = False,
    HistogramPath: str = "/Hists/Cells",
    **extra_kwargs,
) -> Configurable:
    """
    Configures and returns a CaloCellMaker algorithm instance for a given calorimeter sampling.

    Args:
        name: Name of the algorithm instance.
        sampling: Calorimeter sampling descriptor object (from geometry configuration).
        InputHitsKey: SG key for input hits container.
        OutputCollectionKey: SG key for output descriptor collection.
        OutputLevel: Logging verbosity level.
        DetailedHistograms: If True, book fine-grained diagnostic histograms.
        HistogramPath: Base path in histogram service.

    Returns:
        Configurable: Configured ROOT.CaloCellMaker algorithm wrapper.
    """
    props = dict(
        InputHitsKey=InputHitsKey,
        OutputCollectionKey=OutputCollectionKey,
        OutputLevel=OutputLevel,
        DetailedHistograms=DetailedHistograms,
        HistogramPath=HistogramPath,
        EtaBins=sampling.sensitive().EtaBins,
        PhiBins=sampling.sensitive().PhiBins,
        ZMin=sampling.volume().ZMin,
        ZMax=sampling.volume().ZMax,
        Z=sampling.sv.pv.Z,
        Sampling=sampling.Sampling,
        Segment=sampling.sensitive().Segment,
        Detector=sampling.Detector,
        BunchIdStart=sampling.BunchIdStart,
        BunchIdEnd=sampling.BunchIdEnd,
        BunchDuration=25,
    )

    cells = getattr(sampling.sensitive(), "Cells", None)
    if cells:
        props["CellEta"] = [float(x) for x in cells["Eta"]]
        props["CellDeltaEta"] = [float(x) for x in cells["DeltaEta"]]

    tiles = getattr(sampling, "Tiles", None)
    if tiles:
        props["CellBin"] = [int(x) for x in tiles["Bin"]]
        props["CellEta"] = [float(x) for x in tiles["Eta"]]
        props["CellPhi"] = [float(x) for x in tiles["Phi"]]
        props["CellDeltaEta"] = [float(x) for x in tiles["DeltaEta"]]
        props["CellDeltaPhi"] = [float(x) for x in tiles["DeltaPhi"]]

    props.update(extra_kwargs)
    return Configurable(ROOT.CaloCellMaker, name, **props)


CaloCellMaker = CaloCellMakerCfg
