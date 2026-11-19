"""
CaloHitMaker configuration helper.

Creates a Configurable instance for ROOT.CaloHitMaker bound to a specific detector sampling,
dispatching to universal tools (CaloHitBuilderTools) for GeoV1 and specialist tools
(AtlasCaloHitBuilderTools) for GeoV2.
"""

from typing import Any
from GaugiKernel import LoggingLevel, Configurable

__all__ = ["CaloHitMakerCfg", "CaloHitMaker"]


def _is_atlas_sampling(sampling: Any) -> bool:
    """Detects whether a sampling belongs to ATLAS Run 4 (GeoV2) geometry."""
    if getattr(sampling, "Module", None) is not None:
        return True
    if hasattr(sampling, "sensitive") and sampling.sensitive() is not None:
        cells = getattr(sampling.sensitive(), "Cells", None)
        if cells is not None:
            return True
    return False


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
    Configures and returns a CaloHitMaker algorithm instance for a given calorimeter sampling.
    Dispatches to specialist ATLAS tools for GeoV2 or universal tools for GeoV1.
    """
    if _is_atlas_sampling(sampling):
        from AtlasCaloHitBuilderTools import configure_atlas_hit_maker
        return configure_atlas_hit_maker(
            name=name,
            sampling=sampling,
            OutputCollectionKey=OutputCollectionKey,
            HistogramPath=HistogramPath,
            OutputLevel=OutputLevel,
            DetailedHistograms=DetailedHistograms,
            SamplingNoiseStd=SamplingNoiseStd,
            ActiveEnergyOnly=ActiveEnergyOnly,
            BirksLaw=BirksLaw,
            AtlasHitTime=AtlasHitTime,
            TileDualReadout=TileDualReadout,
            FreeRunningHits=FreeRunningHits,
            FreeRunningListKey=FreeRunningListKey,
            FreeRunningBinning=FreeRunningBinning,
            EmecChargeCollection=EmecChargeCollection,
            EmecChargeTables=EmecChargeTables,
            EmecChargeFieldMap=EmecChargeFieldMap,
            EmecChargeHVMap=EmecChargeHVMap,
            **extra_kwargs,
        )

    from CaloHitBuilderTools import configure_generic_hit_maker
    return configure_generic_hit_maker(
        name=name,
        sampling=sampling,
        OutputCollectionKey=OutputCollectionKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
        DetailedHistograms=DetailedHistograms,
        SamplingNoiseStd=SamplingNoiseStd,
        ActiveEnergyOnly=ActiveEnergyOnly,
        BirksLaw=BirksLaw,
        AtlasHitTime=AtlasHitTime,
        **extra_kwargs,
    )


CaloHitMaker = CaloHitMakerCfg
