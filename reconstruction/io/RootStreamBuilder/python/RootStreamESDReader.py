__all__ = ["RootStreamESDReader"]

import ROOT
from GaugiKernel import Configurable, ComponentAccumulator


class RootStreamESDReader(Configurable):

    def __init__(
        self,
        name,
        OutputEventKey: str,
        OutputTruthKey: str,
        OutputCellsKey: str,
        OutputCellsTruthKey: str,
        OutputSeedsKey: str,
        InputFile: str,
        OutputLevel: int = 0,
        NtupleName: str = "CollectionTree",
    ):

        Configurable.__init__(
            self,
            ROOT.RootStreamESDReader,
            name,
            OutputEventKey=OutputEventKey,
            OutputTruthKey=OutputTruthKey,
            OutputCellsKey=OutputCellsKey,
            OutputCellsTruthKey=OutputCellsTruthKey,
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
