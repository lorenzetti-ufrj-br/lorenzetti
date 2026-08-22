# EgammaBuilder

`EgammaBuilder` is a package designed for the reconstruction and identification of electron candidates from calorimeter clusters (`CaloCluster`) within the Lorenzetti framework. It applies cut-based electron identification (IsEM) criteria to classify candidates across multiple performance working points.

---

## How It Works

The `ElectronMaker` algorithm processes clusters event-by-event:

1. **Cluster Retrieval**: Reads a collection of `CaloCluster` candidates from the StoreGate (`InputClusterKey`).
2. **Identification & Cut Evaluation**: For each cluster, it checks whether it satisfies central or forward region cuts.
   - **Central Region Selection**: Uses a set of cuts defined by the `getIsEMCuts` helper for the following variables:
     - `etHad`: Energy leakage fraction into the hadronic calorimeter.
     - `rEta`: Lateral shower shape parameter (ratio of energy in $3\times7$ cells to energy in $7\times7$ cells).
     - `eRatio`: Ratio of the energy difference between the two highest-energy cells over their sum in the strip layer.
   - **Forward Region Selection**: Employs cluster moment cuts:
     - `SecondLambda`: Second moment of the shower depth/lateral width.
     - `LateralMom`: Lateral energy distribution moment.
     - `LongMom`: Longitudinal energy distribution moment.
     - `FracMax`: Energy fraction of the hottest cell.
     - `SecondR`: Second radial moment.
     - `LambdaCenter`: Center of gravity depth of the shower.
3. **Electron Candidate Creation**: Candidates that pass the selection are reconstructed as `Electron` objects, flagged with their respective working points, and saved to the output `ElectronContainer` (`OutputElectronKey`).

---

## Supported Working Points & Central Cut Values

The identification supports four distinct operating points (working points):

| Working Point | `etHad` Cut | `rEta` Cut | `eRatio` Cut |
| :--- | :--- | :--- | :--- |
| **`vloose`** | `0.157` | `0.752` | `0.52` |
| **`loose`** | `0.1218` | `0.57` | `0.47` |
| **`medium`** | `0.0270375` | `0.814625` | `0.57` |
| **`tight`** | `0.0270375` | `0.83125` | `0.65` |

---

## Python Configuration

The Python configuration is steered through the helper function `ElectronBuilderCfg` in `python/ElectronBuilder.py`.

### Function Signature
```python
def ElectronBuilderCfg(
    name             : str, 
    InputClusterKey  : str,
    OutputElectronKey: str,
    OutputLevel      : int = 0, 
) -> Configurable
```

### Parameters
* **`name`** (`str`): Name of the `ElectronMaker` algorithm instance.
* **`InputClusterKey`** (`str`): StoreGate key of the input `CaloClusterContainer`.
* **`OutputElectronKey`** (`str`): StoreGate key for the final reconstructed `ElectronContainer`.
* **`OutputLevel`** (`int`, default `0`): Verbosity logging level.

---

## Python Configuration Example

Below is an example showing how to import, configure, and register `ElectronBuilderCfg` in a job configuration script:

```python
import ROOT
from GaugiKernel import LoggingLevel, ComponentAccumulator
from EgammaBuilder import ElectronBuilderCfg

def configure_egamma_job():
    # 1. Initialize the ComponentAccumulator for managing job components
    acc = ComponentAccumulator("EgammaJobAccumulator", "output.AOD.root")
    output_level = LoggingLevel.INFO

    # 2. Configure the Electron Builder
    # Reads clusters from "CaloClusters" and writes reconstructed electrons to "Electrons"
    egamma_alg = ElectronBuilderCfg(
        name="L0ElectronBuilder",
        InputClusterKey="CaloClusters",
        OutputElectronKey="Electrons",
        OutputLevel=output_level
    )
    
    # Register the configured algorithm tool in the accumulator
    acc.add(egamma_alg)

    return acc

if __name__ == "__main__":
    job_acc = configure_egamma_job()
    print("Electron reconstruction builder configured successfully!")
```
