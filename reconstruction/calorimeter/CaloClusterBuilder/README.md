# CaloClusterBuilder

`CaloClusterBuilder` is a package responsible for reconstructing calorimeter clusters (`CaloCluster`) from digitized calorimeter cells (`CaloCell`). It utilizes a seed-based clustering approach to group cells around initial particle trajectory projection points (seeds). Additionally, it computes key lateral and longitudinal shower shape variables used for electron/photon identification.

---

## How It Works

The cluster reconstruction process follows a seed-based seeded-clustering approach:

1. **Seed Processing**: The algorithm iterates over all seeds in the event (`SeedContainer`), typically representing the projection of a particle trajectory into the calorimeter.
2. **Search for Hottest Cell**: For each seed, it scans cells in the second electromagnetic layer (EM2: `EMB2` and `EMEC2`) within a search window of size `EtaWindow/2` by `PhiWindow/2` centered on the seed's position. The cell with the maximum energy inside this window is selected as the **hottest cell** (shower core).
3. **Core Energy Validation**: Around the identified hottest cell, the algorithm calculates the total electromagnetic energy in a core region of size $0.1 \times 0.1$. If this core energy is greater than or equal to `MinCenterEnergy`, a new `CaloCluster` is created centered at the hottest cell's $(\eta, \phi)$ coordinates.
4. **Cell Accumulation**: All calorimeter cells within a window of size `EtaWindow/2` by `PhiWindow/2` around the cluster center are added to the cluster.
5. **Shower Shape Calculation**: It invokes the `ShowerShapes` tool to compute various lateral and longitudinal variables describing the shower's spatial development.

---

## Computed Shower Shapes

The associated `ShowerShapes` tool computes several variables essential for distinguishing electromagnetic showers (electrons/photons) from hadronic jets and background (e.g. $\pi^0 \to \gamma\gamma$):

### Longitudinal Development (Layer Fractions)
* **`f0` (Pre-Sampler Fraction)**: Fraction of energy deposited in the Pre-Sampler layer (`PSB`, `PSE`).
* **`f1` (EM1 Fraction)**: Fraction of energy deposited in the first EM layer (`EMB1`, `EMEC1`).
* **`f3` (EM3 Fraction)**: Fraction of energy deposited in the third EM layer (`EMB3`, `EMEC3`).

### Lateral Development (Middle EM Layer - EM2)
* **`weta2`**: Lateral width of the shower in $\eta$ within the EM2 layer.
* **`reta`**: Lateral containment ratio $E(3\times7)/E(7\times7)$ in cells, measuring how narrow the shower is in $\eta$.
* **`rphi`**: Lateral containment ratio $E(3\times3)/E(3\times7)$ in cells, measuring the shower width in $\phi$ (affected by magnetic field bending).

### Strip EM Layer Development (EM1)
* **`eratio`**: Energy ratio $(E_{\text{max1}} - E_{\text{max2}}) / (E_{\text{max1}} + E_{\text{max2}})$ of the two highest-energy cell peaks in EM1. Useful for separating single photons from overlapping photons from neutral pion decays ($\pi^0 \to \gamma\gamma$).

### Hadronic Leakage
* **`rhad`**: Hadronic leakage ratio, calculated as the ratio of hadronic layer energy to the total electromagnetic cluster energy.

### Forward Moments
When `DoForwardMoments` is enabled, additional moments are calculated for forward calorimeter clusters:
* **`secondR`**: Second radial moment.
* **`secondLambda`**: Second longitudinal moment.
* **`lambdaCenter`**: Distance from the shower center of gravity to the calorimeter front face.
* **`fracMax`**: Fraction of energy in the hottest cell.
* **`lateralMom` / `longitudinalMom`**: Lateral and longitudinal moments.

---

## Python Configuration

The Python configuration is defined via `CaloClusterMakerCfg` (aliased as `CaloClusterMaker` in `python/CaloClusterMaker.py`).

### Function Signature
```python
def CaloClusterMakerCfg(
    name             : str,
    InputCellsKey    : str,
    InputSeedsKey    : str,
    OutputClusterKey : str,
    EtaWindow        : float = CaloClusterFlags.EtaWindow,        # Default: 0.4
    PhiWindow        : float = CaloClusterFlags.PhiWindow,        # Default: 0.4
    MinCenterEnergy  : float = CaloClusterFlags.MinCenterEnergy,  # Default: 1*GeV
    DoForwardMoments : bool  = CaloClusterFlags.DoForwardMoments, # Default: False
    OutputLevel      : str   = 0,
    HistogramPath    : str   = "Expert/Clusters",
) -> Configurable:
```

### Parameters
* **`name`** (`str`): Name of the configurator tool.
* **`InputCellsKey`** (`str`): StoreGate key for the input `CaloCellContainer`.
* **`InputSeedsKey`** (`str`): StoreGate key for the input `SeedContainer`.
* **`OutputClusterKey`** (`str`): StoreGate key for the output reconstructed `CaloClusterContainer`.
* **`EtaWindow` / `PhiWindow`** (`float`): Half-size of the rectangular clustering window (the full window size is `Window/2` in each direction).
* **`MinCenterEnergy`** (`float`): Minimum energy in GeV required in a $0.1 \times 0.1$ window centered on the hottest cell to form a cluster.
* **`DoForwardMoments`** (`bool`): Flag to enable/disable forward moments computation.
* **`OutputLevel`** (`int` or `str`): Output log verbosity level.
* **`HistogramPath`** (`str`): Root path for booking and saving monitoring histograms.

---

## Python Configuration Example

Below is a Python snippet demonstrating how to configure and add `CaloClusterMaker` to a reconstruction job accumulator:

```python
from GaugiKernel import LoggingLevel, ComponentAccumulator
from CaloClusterBuilder import CaloClusterMaker, CaloClusterFlags
from GaugiKernel.constants import GeV

def configure_clustering_job():
    # 1. Create a ComponentAccumulator to manage configuration
    acc = ComponentAccumulator("ClusterJobAccumulator", "output.AOD.root")
    output_level = LoggingLevel.INFO

    # 2. Configure the CaloClusterMaker tool for standard cells and seeds
    cluster_maker = CaloClusterMaker(
        "CaloClusterMaker",
        InputCellsKey="Cells",
        InputSeedsKey="Seeds",
        OutputClusterKey="Clusters",
        EtaWindow=0.4,
        PhiWindow=0.4,
        MinCenterEnergy=1.5 * GeV,  # Form cluster if core energy >= 1.5 GeV
        DoForwardMoments=False,
        OutputLevel=output_level,
        HistogramPath="Expert/Clusters"
    )

    # 3. Add configured tool to the accumulator
    acc.add(cluster_maker)

    # 4. (Optional) Configure another cluster maker for truth cells
    truth_cluster_maker = CaloClusterMaker(
        "CaloClusterMaker_Truth",
        InputCellsKey="TruthCells",
        InputSeedsKey="Seeds",
        OutputClusterKey="TruthClusters",
        EtaWindow=0.4,
        PhiWindow=0.4,
        MinCenterEnergy=1.0 * GeV,
        DoForwardMoments=False,
        OutputLevel=output_level,
        HistogramPath="Expert/TruthClusters"
    )
    acc.add(truth_cluster_maker)

    return acc

if __name__ == "__main__":
    job_acc = configure_clustering_job()
    print("CaloClusterBuilder configuration completed successfully!")
```
