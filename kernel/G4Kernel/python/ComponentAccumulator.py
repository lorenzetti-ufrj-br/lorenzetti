"""
# G4Kernel ComponentAccumulator

This module provides the `ComponentAccumulator` class for configuring and orchestrating
Geant4-based detector simulations within the Lorenzetti framework.

## Overview
`ComponentAccumulator` acts as the Python-side coordinator for the Geant4 simulation engine:
- **Run Management:** Wraps the C++ `RunManager` (`ROOT.RunManager`), coordinating detector geometry,
  primary event generators, and algorithmic tools.
- **Multi-Threading:** Configures Geant4 multi-threaded runs (`G4MTRunManager`), managing per-thread
  output ROOT files (`<OutputFile>.<thread_id>`).
- **Automatic Output Merging:** Combines per-thread ROOT files into the final output file via ROOT's `hadd`
  utility upon completion of the event loop.
- **Algorithm Accumulation:** Supports appending analysis, filtering, and digitization algorithms
  (e.g., `CaloHitBuilder`, `RootStreamHITMaker`) using the intuitive `+=` operator.
"""

__all__ = ["ComponentAccumulator"]

import os
import time
import gc
from typing import List, Union, Any

import ROOT
from GaugiKernel import Configurable, LoggingLevel
from GaugiKernel.constants import MINUTES
from G4Kernel import EventReader


class ComponentAccumulator(Configurable):
    """
    ### Geant4 Simulation Component Accumulator

    Inherits from `Configurable` and acts as the central simulation engine manager.
    It encapsulates the detector construction, primary generator reader, random seed,
    execution timeouts, multithreading configuration, and ROOT output persistence.

    #### Parameters
    - `name` (`str`):
      Unique identifier for this accumulator and underlying `RunManager` instance.
    - `volume` (`Any`):
      Detector construction object (e.g., `DetectorConstruction_v1`). Must implement `compile()`,
      `c_ptr()`, and `get_ui_commands()`.
    - `generator` (`Configurable`):
      Primary particle generator or event reader (e.g., `EventReader`).
    - `OutputFile` (`str`, optional):
      Destination ROOT file path for merged simulation output. Defaults to `"output.root"`.
    - `Seed` (`int`, optional):
      Random number generator seed for the simulation engine. Defaults to `512`.
    - `NumberOfThreads` (`int`, optional):
      Number of Geant4 simulation worker threads. Defaults to `1`.
    - `Timeout` (`int`, optional):
      Maximum per-event simulation timeout in seconds. Defaults to `120 * MINUTES`.
    - `UseGUI` (`bool`, optional):
      Whether to launch an interactive Geant4 Qt/X11 GUI visualization session. Defaults to `False`.

    #### Example Usage
    ```python
    from G4Kernel import ComponentAccumulator, EventReader
    from geometry.v1 import DetectorConstruction_v1
    from CaloHitBuilder import CaloHitBuilder
    from RootStreamBuilder import RootStreamHITMaker

    # 1. Initialize detector geometry and event reader
    detector = DetectorConstruction_v1("ATLAS", UseMagneticField=True)
    reader = EventReader("EventReader", "input.EVT.root")

    # 2. Instantiate accumulator
    acc = ComponentAccumulator(
        "SimulationAccumulator",
        detector,
        reader,
        OutputFile="output.HIT.root",
        NumberOfThreads=4,
    )

    # 3. Append simulation algorithms
    acc += CaloHitBuilder("CaloHitBuilder", OutputHitsKey="Hits")
    acc += RootStreamHITMaker("RootStreamHITMaker", InputHitsKey="Hits")

    # 4. Execute simulation run and merge outputs
    acc.run(evt=100)
    ```
    """

    def __init__(
        self,
        name: str,
        detector_construction: Configurable,
        generator: Configurable,
        OutputFile: str = "output.root",
        Seed: int = 512,
        NumberOfThreads: int = 1,
        Timeout: int = 120 * MINUTES,
        UseGUI: bool = False,
        NeutronTimeCut: float = 0.0,
        FastSimulation: bool = False,
        AtlasG4: bool = False,
    ):
        """
        Initializes the Geant4 simulation environment and `RunManager` backend.

        ### Configuration Workflow:
        1. Compiles the detector geometry volume.
        2. Allocates per-thread output file names (`<OutputFile>.<thread_id>`).
        3. Configures and registers C++ `ROOT.RunManager` properties via `Configurable`.
        4. Applies interactive GUI visualization commands if `UseGUI=True`.
        """

        self.generator = generator
        self.detector_construction = detector_construction

        # Step 1: Compile the detector volume hierarchy into Geant4 solids and logical volumes
        self.detector_construction.compile()

        # Step 2: Initialize the C++ RunManager backend with constructor arguments and properties
        super().__init__(
            ROOT.RunManager,
            name,
            generator.c_ptr(),
            detector_construction.c_ptr(),
            OutputFile=OutputFile,
            Seed=Seed,
            NumberOfThreads=NumberOfThreads,
            Timeout=Timeout,
            UseGUI=UseGUI,
            NeutronTimeCut=float(NeutronTimeCut),
            FastSimulation=bool(FastSimulation) or bool(AtlasG4),
            AtlasG4=bool(AtlasG4),
        )

        # Step 3: Prepare thread-specific output file names for multi-threaded simulation runs
        self.outputFiles = [f"{OutputFile}.{thread}" for thread in range(NumberOfThreads)]

        # Step 4: Forward visualization and UI macro commands to Geant4 if GUI mode is enabled
        if UseGUI:
            for cmd in self.detector_construction.get_ui_commands():
                self._c_ptr.addUICommand(cmd)

    def __del__(self):
        """
        ### Destructor for `ComponentAccumulator`

        Ensures C++ resources and Geant4 threads are cleanly terminated,
        forcing garbage collection and a brief synchronization delay.
        """
        super().__del__()
        gc.collect()
        time.sleep(2)

    def run(self, evt: int = -1):
        """
        ### Execute Simulation

        Runs the Geant4 event loop for the requested number of events and automatically
        merges per-thread ROOT output files into the final `OutputFile`.

        #### Parameters
        - `evt` (`int`, optional):
          Number of events to simulate:
          - If `evt < 0` (default `-1`), processes all available events from `generator.GetEntries()`.
          - If `evt > generator.GetEntries()`, clamped to the total entries available.
        """
        # Determine total available entries in the event reader / generator
        total_entries = self.generator.GetEntries()

        # Resolve the event count (clamp to total entries if negative or exceeding maximum)
        if evt < 0 or evt > total_entries:
            evt = total_entries

        # Trigger the Geant4 simulation event processing in C++ RunManager
        self._c_ptr.run(evt)

        # Merge thread-specific ROOT outputs into the final destination file
        self.merge()

    def __add__(self, algs: Union[Configurable, List[Configurable]]) -> "ComponentAccumulator":
        """
        ### Algorithm Accumulation Operator (`+=`)

        Appends one or more user algorithms (`Gaugi::Algorithm*`) to the simulation pipeline.

        #### Parameters
        - `algs` (`Configurable` or `List[Configurable]`):
          Single algorithm or list of algorithms to append.

        #### Returns
        - `self`: The accumulator instance for method chaining.
        """
        # Normalize input to a list of algorithms
        if not isinstance(algs, list):
            algs = [algs]

        # Register each algorithm's underlying C++ pointer with the RunManager
        for alg in algs:
            self._c_ptr.push_back(alg.c_ptr())

        return self

    def merge(self):
        """
        ### Merge Per-Thread Output Files

        Merges all thread-specific output ROOT files (`<OutputFile>.0`, `<OutputFile>.1`, etc.)
        into the unified target `OutputFile` using ROOT's `hadd -f` utility, and cleans up the
        temporary per-thread files upon successful merge.
        """
        if not self.outputFiles:
            return

        # Execute ROOT's hadd utility to merge all per-thread ROOT files
        files_to_merge = " ".join(self.outputFiles)
        os.system(f"hadd -f {self.OutputFile} {files_to_merge}")

        # Remove temporary thread-specific files
        for f in self.outputFiles:
            if os.path.exists(f):
                os.remove(f)


    def get_detector_construction(self) -> Configurable:
      return self.detector_construction

    def get_generator(self) -> Configurable:
      return self.generator
