__all__ = ["RootStreamAODMaker"]

from GaugiKernel import Cpp
from GaugiKernel.macros import *
from RootStreamBuilder import RootStreamAODFlags as flags
import ROOT


class RootStreamAODMaker(Cpp):

    def __init__(
        self,
        name,
        InputEventKey: str,
        InputSeedsKey: str,
        InputTruthKey: str,
        InputCellsKey: str,
        InputClusterKey: str,
        InputRingerKeys: list,  # all enabled topologies
        InputRingerL0Key: str,
        InputElectronKey: str,
        InputTruthCellsKey: str,
        InputTruthClusterKey: str,
        InputTruthRingerKeys: list,  # all enabled topologies (truth)
        InputTruthElectronKey: str,
        OutputEventKey: str = None,
        OutputTruthKey: str = None,
        OutputCellsKey: str = None,
        OutputClusterKey: str = None,
        OutputRingerKeys: list = None,
        OutputRingerL0Key: str = None,
        OutputSeedsKey: str = None,
        OutputElectronKey: str = None,
        OutputTruthCellsKey: str = None,
        OutputTruthClusterKey: str = None,
        OutputTruthRingerKeys: list = None,
        OutputTruthElectronKey: str = None,
        OutputLevel: int = 0,
        NtupleName: str = "CollectionTree",
        DumpCells: bool = flags.DumpCells,
    ):

        Cpp.__init__(self, ROOT.RootStreamAODMaker(name))
        self.setProperty("InputEventKey", InputEventKey)
        self.setProperty("InputTruthKey", InputTruthKey)
        self.setProperty("InputCellsKey", InputCellsKey)
        self.setProperty("InputClusterKey", InputClusterKey)
        self.setProperty("InputRingerKeys", InputRingerKeys)
        self.setProperty("InputSeedsKey", InputSeedsKey)
        self.setProperty("InputElectronKey", InputElectronKey)
        self.setProperty("InputTruthCellsKey", InputTruthCellsKey)
        self.setProperty("InputTruthClusterKey", InputTruthClusterKey)
        self.setProperty("InputTruthRingerKeys", InputTruthRingerKeys)
        self.setProperty(
            "OutputEventKey", OutputEventKey if OutputEventKey else InputEventKey
        )
        self.setProperty(
            "OutputTruthKey", OutputTruthKey if OutputTruthKey else InputTruthKey
        )
        self.setProperty(
            "OutputCellsKey", OutputCellsKey if OutputCellsKey else InputCellsKey
        )
        self.setProperty(
            "OutputClusterKey",
            OutputClusterKey if OutputClusterKey else InputClusterKey,
        )
        self.setProperty("OutputRingerKeys", OutputRingerKeys or InputRingerKeys)
        self.setProperty(
            "OutputSeedsKey", OutputSeedsKey if OutputSeedsKey else InputSeedsKey
        )
        self.setProperty(
            "OutputElectronKey",
            OutputElectronKey if OutputElectronKey else InputElectronKey,
        )
        self.setProperty(
            "OutputTruthCellsKey",
            OutputTruthCellsKey if OutputTruthCellsKey else InputTruthCellsKey,
        )
        self.setProperty(
            "OutputTruthClusterKey",
            OutputTruthClusterKey if OutputTruthClusterKey else InputTruthClusterKey,
        )
        self.setProperty(
            "OutputTruthRingerKeys", OutputTruthRingerKeys or InputTruthRingerKeys
        )
        self.setProperty(
            "OutputRingerL0Key",
            OutputRingerL0Key if OutputRingerL0Key else InputRingerL0Key,
        )
        self.setProperty(
            "OutputTruthElectronKey",
            OutputTruthElectronKey if OutputTruthElectronKey else InputTruthElectronKey,
        )
        self.setProperty("OutputLevel", OutputLevel)
        self.setProperty("NtupleName", NtupleName)
        self.setProperty("DumpCells", DumpCells)
