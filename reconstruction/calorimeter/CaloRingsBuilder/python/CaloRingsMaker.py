__all__ = ["CaloRingsMaker"]


from GaugiKernel import Cpp
from GaugiKernel.macros import *
from typing import List
import ROOT
import numpy as np

pi = np.pi


class CaloRingsMaker(Cpp):

    def __init__(
        self,
        name,
        InputClusterKey: str,
        OutputRingerKey: str,
        DeltaEtaRings: list,
        DeltaPhiRings: list,
        NRings: list,
        LayerRings: list,
        OutputLevel: int = 0,
        HistogramPath: str = "Expert/Rings",
        EtaRange: List[float] = [0, 2.5],
        DoSigmaCut: bool = False,
        SigmaCut: float = 2.0,
        RingerTopology: str = "std",
        CornerShift: int = 3,
        CrossShift: int = 3,
        RingsShift: list = [(0, 0)],
        Axis: int = 0,
    ):

        if RingerTopology == "asym":
            cpp_class = ROOT.CaloAsymRingsMaker(name)
        elif RingerTopology == "strips":
            cpp_class = ROOT.CaloStripsRingsMaker(name)
        elif RingerTopology == "corner":
            cpp_class = ROOT.CaloCornerRingsMaker(name)
        elif RingerTopology == "std":
            cpp_class = ROOT.CaloRingsMaker(name)
        elif RingerTopology == "cross":
            cpp_class = ROOT.CaloCrossRingsMaker(name)
        elif RingerTopology == "custom":
            cpp_class = ROOT.CaloCustomRingsMaker(name)
        else:
            print("Topology not found!")

        Cpp.__init__(self, cpp_class)

        self.setProperty("OutputRingerKey", OutputRingerKey)
        self.setProperty("InputClusterKey", InputClusterKey)
        self.setProperty("DeltaEtaRings", DeltaEtaRings)
        self.setProperty("DeltaPhiRings", DeltaPhiRings)
        self.setProperty("NRings", NRings)
        self.setProperty("LayerRings", LayerRings)
        self.setProperty("HistogramPath", HistogramPath)
        self.setProperty("OutputLevel", OutputLevel)
        self.setProperty("EtaRange", EtaRange)
        self.setProperty("DoSigmaCut", DoSigmaCut)
        self.setProperty("SigmaCut", SigmaCut)
        if RingerTopology == "corner":
            self.setProperty("CornerShift", CornerShift)
        if RingerTopology == "strips":
            self.setProperty("Axis", Axis)
        if RingerTopology == "cross":
            self.setProperty("CrossShift", CrossShift)
        if RingerTopology == "custom":
            self.setProperty("RingsShift", RingsShift)
