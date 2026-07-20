__all__ = ["RootStreamHITFlags", "RootStreamESDFlags", "RootStreamAODFlags"]


from GaugiKernel import EnumStringification


class RootStreamHITFlags(EnumStringification):

    OnlyRoI = True
    EtaWindow = 0.4
    PhiWindow = 0.4


class RootStreamESDFlags(EnumStringification):

    EtaWindow = 0.4
    PhiWindow = 0.4


class RootStreamAODFlags(EnumStringification):

    DumpCells = True

    doStdRings = True
    doCornerRings = False
    doAsymRings = False
    doStripsRings = False
    doCrossRings = False
    doCustomRings = False

    DoSigmaCut = False
    SigmaCut = 2.0
    CornerShift = 3
    CrossShift = 3
    CustomRingsShiftEta: list = [0]
    CustomRingsShiftPhi: list = [0]
    StripsAxis = 0

