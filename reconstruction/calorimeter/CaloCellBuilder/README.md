# CaloCellBuilder

`CaloCellBuilder` is a package designed to orchestrate the complete **Calorimeter Digitization chain** in the Lorenzetti framework. It processes raw simulated energy deposits (hits) in the calorimeter active samplings, models electronic and physical effects (such as pulse shapes, electronic noise, cross-talk, and detector defects), and reconstructs the digitized cells into final collections using Optimal Filtering.

---

## How It Works

The digitization chain configured by `CaloCellBuilder` runs event-by-event and sampling-by-sampling through the following stages:

1. **Pulse Shape Simulation (`PulseGenerator`)**:
   Convolves the simulated energy deposits (hits) with the realistic electronic shaper pulse shape defined in the shaper configuration files (`ShaperFile`). It simulates the signal shape across multiple bunch crossings (out-of-time pileup).
2. **Electronic Noise Injection**:
   Adds Gaussian noise to the electronic pulse samples based on the configured noise standard deviation (`NoiseStd`).
3. **Energy & Time Reconstruction (`OptimalFilter` / `ConstrainedOptimalFilter`)**:
   Reconstructs the original cell energy and time deposit from the pulse samples. 
   - Uses **Optimal Filtering (OF)** coefficients (`WeightsEnergy`/`WeightsTime`) by default.
   - Fallback to **Constrained Optimal Filtering (COF)** for the `TILE` detector if constrained reconstruction is enabled (`CaloFlags.DoCOF`).
4. **Defect & Anomaly Injection (`PulsePerturber`)**:
   Optionally perturbs electronic pulses to simulate hardware anomalies (e.g., dead modules or abnormal noise levels) for specific event ranges and cell hashes defined in a Bad Run List JSON file (`BadRunListFile`).
5. **Cross-Talk Simulation (`CrossTalkMaker`)**:
   Optionally simulates capacitive, inductive, and resistive cross-talk between adjacent cells in the main calorimeter samplings (`EMEC2` and `EMB2`).
6. **Collection Merging (`CaloCellMerge`)**:
   Merges the digitized and reconstructed cells from all individual sampling collections into two master collections: one for reconstructed cells (`Cells`) and one containing truth information (`TruthCells`).

---

## Configuration Flags

Global digitization and reconstruction configurations are managed via the stringified enum flags:

### 1. `CaloFlags`
* **`SamplingnoiseStd`** (`float`, default `0.0`): Standard deviation for global noise injection.
* **`DoCrossTalk`** (`bool`, default `False`): Enables capacitive/inductive/resistive cross-talk simulation.
* **`DoCOF`** (`bool`, default `False`): Enables Constrained Optimal Filtering (COF) for the Tile calorimeter.
* **`DoDefects`** (`bool`, default `False`): Enables defect/anomaly injection using `PulsePerturber`.

### 2. `CrossTalkFlags`
* **`MinEnergy`** (`float`, default `1 * GeV`): Minimum cell energy threshold required to trigger cross-talk propagation.
* **`AmpCapacitive`** (`float`, default `4.2`): Capacitive cross-talk amplitude multiplier.
* **`AmpInductive`** (`float`, default `2.3`): Inductive cross-talk amplitude multiplier.
* **`AmpResistive`** (`float`, default `1.0`): Resistive cross-talk amplitude multiplier.

### 3. `AnomalyFlags`
* **`BadRunListFile`** (`str`, default `""`): Path to the Bad Run List JSON file containing run definitions for anomaly injection.

---

## Python Configuration

The main steering interface is the `CaloCellBuilder` class, which orchestrates the creation of all digitizer tool configurations.

### `CaloCellBuilder` Class

#### Constructor Signature
```python
class CaloCellBuilder( Logger ):
    def __init__(
        self,
        name                 : str,
        detector,
        HistogramPath        : str = "Expert",
        InputHitsKey         : str = "Hits",
        OutputCellsKey       : str = "Cells",
        OutputTruthCellsKey  : str = "TruthCells",
        InputEventKey        : str = "Events",
        OutputLevel          : int = 0,
    )
```

#### Key Parameters
* **`name`** (`str`): Name of the builder instance.
* **`detector`**: The detector construction configuration object containing active samplings.
* **`HistogramPath`** (`str`, default `"Expert"`): Path for booking and saving monitoring histograms.
* **`InputHitsKey`** (`str`, default `"Hits"`): StoreGate key for input hits.
* **`OutputCellsKey`** (`str`, default `"Cells"`): StoreGate key for output reconstructed cells.
* **`OutputTruthCellsKey`** (`str`, default `"TruthCells"`): StoreGate key for cell truth information.
* **`InputEventKey`** (`str`, default `"Events"`): StoreGate key for event headers.
* **`OutputLevel`** (`int`, default `0`): Verbosity logging level.

#### Main Interface
* **`merge(self, acc)`**: Configures all required digitization, optimal filtering, cross-talk, and merging tools, and appends them to the provided `ComponentAccumulator`.

---

## Python Configuration Example

Below is an example showing how to import, configure, and use `CaloCellBuilder` in a reconstruction configuration script:

```python
import ROOT
from GaugiKernel import LoggingLevel, ComponentAccumulator
from CaloCellBuilder import CaloCellBuilder, CaloFlags, CrossTalkFlags, AnomalyFlags
from CaloCell import Detector

def configure_digitization_job(detector_construction):
    # 1. Initialize the ComponentAccumulator for managing job components
    acc = ComponentAccumulator("DigitizationJobAccumulator", "output.ESD.root")
    output_level = LoggingLevel.INFO

    # 2. Configure global Digitization Flags
    CaloFlags.DoCrossTalk = True
    CaloFlags.DoDefects = True
    AnomalyFlags.BadRunListFile = "bad_run_list.json"
    CrossTalkFlags.MinEnergy = 0.5 * ROOT.GeV

    # 3. Configure the CaloCellBuilder
    # Reads simulated hits from "CaloHits" and writes final cells to "ReconstructedCells"
    cell_builder = CaloCellBuilder(
        name="L0CaloCellBuilder",
        detector=detector_construction,
        InputHitsKey="CaloHits",
        OutputCellsKey="ReconstructedCells",
        OutputTruthCellsKey="TruthCells",
        InputEventKey="EventInfo",
        OutputLevel=output_level
    )

    # 4. Configure all tools and register them inside the accumulator
    cell_builder.merge(acc)

    return acc

if __name__ == "__main__":
    # Example placeholder detector construction object
    # In a real job, this is imported from the geometry module
    detector_geom = ROOT.DetectorConstruction() 
    job_acc = configure_digitization_job(detector_geom)
    print("CaloCellBuilder digitization chain configured successfully!")
```
