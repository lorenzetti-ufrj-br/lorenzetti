__all__ = ["RootStreamAODReader"]

import ROOT

from GaugiKernel import Configurable, ComponentAccumulator

class RootStreamAODReader(Configurable):

    def __init__(
        self,
        name,
        InputFile: str,
        OutputEventKey: str,
        OutputTruthKey: str,
        OutputClusterKey: str,
        OutputRingerKeys: list,  # Alterado para aceitar uma lista de strings
        OutputRingerL0Key: str,
        OutputSeedsKey: str,
        OutputElectronKey: str,
        OutputTruthClusterKey: str,
        OutputTruthRingerKeys: list,  # Alterado para aceitar uma lista de strings
        OutputTruthElectronKey: str,
        OutputLevel: int = 0,
        NtupleName: str = "CollectionTree",
    ):

        Configurable.__init__(self, 
                              ROOT.RootStreamAODReader,
                              name,
                              InputFile = InputFile,
                              OutputEventKey = OutputEventKey,
                              OutputTruthKey = OutputTruthKey,
                              OutputClusterKey = OutputClusterKey,
                              OutputRingerKeys = OutputRingerKeys,
                              OutputRingerL0Key = OutputRingerL0Key,
                              OutputSeedsKey = OutputSeedsKey,
                              OutputElectronKey = OutputElectronKey,
                              OutputTruthClusterKey = OutputTruthClusterKey,
                              OutputTruthRingerKeys = OutputTruthRingerKeys,
                              OutputTruthElectronKey = OutputTruthElectronKey,
                              OutputLevel = OutputLevel,
                              NtupleName = NtupleName,
                              )

        f = ROOT.TFile(self.InputFile, "read")
        t = f.Get(self.NtupleName)
        self.Entries = t.GetEntries()

    def GetEntries(self) -> int:
        return self.Entries

    def merge(self, acc : ComponentAccumulator) -> None:
        acc.SetReader(self)
