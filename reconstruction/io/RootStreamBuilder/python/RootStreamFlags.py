__all__ = ["RootStreamHITFlags", "RootStreamESDFlags", "RootStreamAODFlags"]

from GaugiKernel import EnumStringification


class RootStreamHITFlags(EnumStringification):
    pass


class RootStreamESDFlags(EnumStringification):
    EtaWindow: float = 0.4
    PhiWindow: float = 0.4


class RootStreamAODFlags(EnumStringification):
    DumpCells: bool = True

    doStdRings: bool = True
    doCornerRings: bool = False
    doAsymRings: bool = False
    doStripsRings: bool = False
    doCrossRings: bool = False
    doCustomRings: bool = False

    DoSigmaCut: bool = False
    SigmaCut: float = 2.0
    CornerShift: int = 3
    CrossShift: int = 3
    CustomRingsShiftEta: list = [0]
    CustomRingsShiftPhi: list = [0]
    StripsAxis: int = 0
