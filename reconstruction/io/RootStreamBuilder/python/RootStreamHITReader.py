__all__ = ["RootStreamHITReader"]

import ROOT
from GaugiKernel import Configurable, ComponentAccumulator


class RootStreamHITReader(Configurable):

    def __init__(
        self,
        name,
        OutputEventKey: str,
        OutputTruthKey: str,
        OutputHitsKey: str,
        OutputSeedsKey: str,
        InputFile: str,
        OutputLevel: int = 0,
        NtupleName: str = "CollectionTree",
    ):

        Configurable.__init__(
            self,
            ROOT.RootStreamHITReader,
            name,
            OutputEventKey=OutputEventKey,
            OutputTruthKey=OutputTruthKey,
            OutputHitsKey=OutputHitsKey,
            OutputSeedsKey=OutputSeedsKey,
            InputFile=InputFile,
            OutputLevel=OutputLevel,
            NtupleName=NtupleName,
        )

        f = ROOT.TFile(self.InputFile, "read")
        t = f.Get(self.NtupleName)
        self.Entries = t.GetEntries()

    def GetEntries(self) -> int:
        return self.Entries

    def merge(self, acc: ComponentAccumulator) -> None:
        acc.SetReader(self)
