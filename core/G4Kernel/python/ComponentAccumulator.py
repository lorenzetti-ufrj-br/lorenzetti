
__all__ = ["ComponentAccumulator"]

from GaugiKernel import Cpp, LoggingLevel
from GaugiKernel.constants import MINUTES
from G4Kernel import EventReader
import os
import time
import gc
import ROOT


class ComponentAccumulator(Cpp):
    """
    Component Accumulator for Geant4 simulations.
    Uses the G4Kernel RunManager as a backend.
    """

    def __init__(self, 
                 name, 
                 detector,
                 OutputFile: str = "output.root",
                 Seed: int = 512,
                 NumberOfThreads: int = 1,
                 Timeout: int = 120*MINUTES,
                 UseGUI: bool = False,
                 NeutronTimeCut: float = 0,
                 FastSimulation: bool = False,
                 AtlasG4: bool = False,
                 #OutputLevel: int = LoggingLevel.toC('INFO'),
                 ):

        Cpp.__init__(self, ROOT.RunManager(name))
        # convert python to geant4
        self.__detector = detector
        self.__detector.compile()
        # set the geant detector into the geant
        self._core.setDetectorConstruction(self.__detector.core())
        self.setProperty("OutputFile", OutputFile)
        #self.setProperty("OutputLevel", OutputLevel)
        self.setProperty("NumberOfThreads", NumberOfThreads)
        self.setProperty("Timeout", Timeout)
        self.setProperty("Seed", Seed)
        self.setProperty("UseGUI", UseGUI)
        # time limit (ns) after which neutrons are killed; 0 keeps the Geant4 default (10 us in FTFP_BERT)
        self.setProperty("NeutronTimeCut", float(NeutronTimeCut))
        # G4FastSimulationPhysics for e-, e+, gamma and neutron (frozen showers of the ATLAS FCal, F41 conserto 23)
        self.setProperty("FastSimulation", bool(FastSimulation) or bool(AtlasG4))
        # Geant4 settings of the ATLAS production (F41 conserto 24): FTFP_BERT_ATL, cuts, stacking action, looper killer
        self.setProperty("AtlasG4", bool(AtlasG4))

        if UseGUI:
            [self._core.addUICommand(cmd) for cmd in detector.get_ui_commands()] 
        self.outputFiles = [ f"{self.OutputFile}.{thread}" for thread in range(self.NumberOfThreads)]


    def __del__(self):
        del self._core
        gc.collect()
        time.sleep(2)

    def run(self, evt: int = -1):
        """
        Runs the events in the simulation.

        Parameters
        ----------
        evt : int, optional
            Number of events to run if None, runs all, by default None
        """
        if evt<0:
            evt=self.__numberOfEvents
        if (evt > self.__numberOfEvents):
            evt = self.__numberOfEvents
        self._core.run(evt)
        self.merge()

    def __add__(self, algs):
        if type(algs) is not list:
            algs = [algs]
        for alg in algs:
            self._core.push_back(alg.core())
        return self

    def setGenerator(self, gen: EventReader):
        """
        Sets the generator reader for the simulation.
        The reader is used to read EVT files and return the seeds for G4

        Parameters
        ----------
        gen : EventReader
            Generator reader object
        """
        self.__numberOfEvents = gen.GetEntries()
        self._core.setGenerator(gen.core())


    def detector(self):
        """
        Returns the detector construction object.
        """
        return self.__detector


    def merge(self):
        os.system(f"hadd -f {self.OutputFile} {' '.join(self.outputFiles)}")
        [os.remove(f) for f in self.outputFiles]

