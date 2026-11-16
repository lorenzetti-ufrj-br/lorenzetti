"""
Pileup filter configuration helper.

Provides PileupCfg helper to configure ROOT.generator.Pileup.
"""

from typing import Any
import ROOT

from GaugiKernel import Configurable, LoggingLevel

__all__ = ["PileupCfg"]


def PileupCfg(
    name: str = "Pileup",
    gen: Any = None,
    EtaMax: float = 1.4,
    PileupAvg: float = 0.0,
    PileupSigma: float = 0.0,
    PileupPerBunch: float = -1.0,
    BunchIdStart: int = -8,
    BunchIdEnd: int = 7,
    Select: int = 2,
    DeltaEta: float = 0.22,
    DeltaPhi: float = 0.22,
    PtMinCharged: float = 0.7,
    PtMinNeutral: float = 0.05,
    VertexSigmaZ: float = 56.0,
    VertexSigmaT: float = 200.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
    **kwargs
) -> Configurable:
    """
    Configures and returns a Pileup filter algorithm instance.
    """
    gen_ptr = gen.c_ptr() if hasattr(gen, "c_ptr") else gen
    # Gaussian spread of each collision vertex along the beam (VertexSigmaZ, in mm) and in
    # time (VertexSigmaT, in ps). The C++ properties Sigma_z and Sigma_t are both in mm
    # (Sigma_t is c times the time spread), so the time is converted here.
    sigma_t = VertexSigmaT * 1e-12 * 299792458.0 * 1e3
    return Configurable(
        lambda n: ROOT.generator.Pileup(n, gen_ptr),
        name,
        EtaMax=EtaMax,
        PileupAvg=PileupAvg,
        PileupSigma=PileupSigma,
        PileupPerBunch=PileupPerBunch,
        BunchIdStart=BunchIdStart,
        BunchIdEnd=BunchIdEnd,
        Select=Select,
        DeltaEta=DeltaEta,
        DeltaPhi=DeltaPhi,
        PtMinCharged=PtMinCharged,
        PtMinNeutral=PtMinNeutral,
        Sigma_z=VertexSigmaZ,
        Sigma_t=sigma_t,
        OutputLevel=OutputLevel,
        **kwargs
    )
