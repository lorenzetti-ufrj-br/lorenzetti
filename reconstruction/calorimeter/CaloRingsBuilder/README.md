# CaloRingsBuilder

`CaloRingsBuilder` is a package designed to build concentric ring energy sums (known as **Rings** or **Ringer features**) from calorimeter clusters (`CaloCluster`). This representation compresses the detailed spatial energy deposits of a particle shower in the calorimeter into longitudinal and lateral profiles. These profiles are highly effective for fast electron/photon identification and trigger decision algorithms (e.g., using neural networks).

---

## How It Works

The `CaloRingsBuilder` processes clusters event-by-event and generates ring representations across different layers of the calorimeter. For each configured calorimeter layer:

1. **Center Identification**: It identifies the highest-energy ("hottest") cell belonging to the layer's samplings to act as the center ($\eta_{\text{center}}, \phi_{\text{center}}$) of the ring system. If no cell is found, it falls back to the cluster's barycenter ($\eta_{\text{cluster}}, \phi_{\text{cluster}}$).
2. **Cell Energy Accumulation**: For each cell in the cluster, it computes the distance to the center in $\eta$ and $\phi$ normalized by the ring granularities $\Delta\eta$ and $\Delta\phi$:
   $$d\eta = \frac{|\eta_{\text{center}} - \eta_{\text{cell}}|}{\Delta\eta}$$
   $$d\phi = \frac{|\text{diff}(\phi_{\text{center}}, \phi_{\text{cell}})|}{\Delta\phi}$$
   *(Note: $\text{diff}(\phi_1, \phi_2)$ handles the cyclic wrapping of the calorimeter $\phi$ coordinate).*
3. **Ring Assignment**: The cell's transverse energy ($E_T$) is calculated as:
   $$E_T = \frac{E_{\text{cell}}}{\cosh(|\eta_{\text{center}}|)}$$
   This energy is accumulated into the corresponding ring index $i$ determined by the active topology.
4. **Noise/Sigma Cut**: If enabled, cells with energy below a given threshold (e.g., $E_{\text{cell}} \le \sigma_{\text{cut}} \times \sigma_{\text{noise}}$) are ignored to suppress noise.

---

## Supported Topologies

The package supports six distinct ring topologies defined by the `CaloRingsTopology` enum:

### 1. Standard (`std`)
* **Class**: `ROOT.CaloRingsMaker`
* **Description**: Forms concentric rectangular rings. The ring index is computed as:
  $$i = \text{round}(\max(d\eta, d\phi))$$
* **Ring Count**: $N$ rings per layer.

### 2. Asymmetric (`asym`)
* **Class**: `ROOT.CaloAsymRingsMaker`
* **Description**: Divides each concentric ring (except the central ring $0$) into $4$ separate quadrants in the $\eta$-$\phi$ plane:
  * **Q1** ($\Delta\eta > 0, \Delta\phi > 0$): index $(R \times 4) - 3$
  * **Q2** ($\Delta\eta > 0, \Delta\phi < 0$): index $(R \times 4) - 1$
  * **Q3** ($\Delta\eta < 0, \Delta\phi < 0$): index $R \times 4$
  * **Q4** ($\Delta\eta < 0, \Delta\phi > 0$): index $(R \times 4) - 2$
* **Ring Count**: $(N-1) \times 4 + 1$ rings per layer.

### 3. Strips (`strips`)
* **Class**: `ROOT.CaloStripsRingsMaker`
* **Description**: Accumulates energy along a single axis (either $\eta$ or $\phi$), creating strip-like segments.
* **Configuration**: Controlled by the `Axis` parameter:
  * `0` (default): Strips along the $\eta$ axis.
  * `1`: Strips along the $\phi$ axis.

### 4. Corner (`corner`)
* **Class**: `ROOT.CaloCornerRingsMaker`
* **Description**: Spawns $4$ seed centers (centroids) shifted diagonally from the cluster center by $\pm(\text{CornerShift} \times \Delta\eta, \text{CornerShift} \times \Delta\phi)$. Cells accumulate energy relative to all $4$ corner seeds, creating four parallel ring profiles.
* **Ring Count**: $N \times 4$ rings per layer.

### 5. Cross (`cross`)
* **Class**: `ROOT.CaloCrossRingsMaker`
* **Description**: Similar to the `Corner` topology, but spawns $4$ seed centers shifted along the primary axes (Top, Bottom, Left, Right) by $\pm\text{CrossShift} \times \Delta\eta$ or $\pm\text{CrossShift} \times \Delta\phi$.
* **Ring Count**: $N \times 4$ rings per layer.

### 6. Custom (`custom`)
* **Class**: `ROOT.CaloCustomRingsMaker`
* **Description**: Allows spawning an arbitrary number of seed centers shifted by user-specified vectors: `RingsShiftEta` and `RingsShiftPhi`.
* **Ring Count**: $N \times \text{number of custom shifts}$ rings per layer.

---

## Python Configuration

The Python configuration is managed through the helper function `CaloRingsBuilderCfg` (also aliased to `CaloRingsBuilder` in `python/CaloRingsBuilder.py`).

### Function Signature
```python
def CaloRingsBuilderCfg(
    name              : str,
    InputClusterKey   : str,
    OutputRingerKey   : str,
    OutputLevel       : int   = 0,
    HistogramPath     : str   = "Expert/Rings",
    DoSigmaCut        : bool  = False,
    SigmaCut          : float = 2.0,
    RingerTopology    : CaloRingsTopology = CaloRingsTopology.Standard,
    CornerShift       : int   = None,
    CrossShift        : int   = None,
    RingsShiftEta     : List[float]   = None,
    RingsShiftPhi     : List[float]   = None,
    Axis              : int   = None,
) -> List[Configurable]:
```

### Parameters
* **`name`** (`str`): Base name of the configuration tools.
* **`InputClusterKey`** (`str`): StoreGate key of the input `CaloClusterContainer`.
* **`OutputRingerKey`** (`str`): StoreGate key for the final merged `CaloRingsContainer`.
* **`OutputLevel`** (`int`, default `0`): Verbosity logging level.
* **`HistogramPath`** (`str`, default `"Expert/Rings"`): Path to book and save histograms.
* **`DoSigmaCut`** (`bool`, default `False`): Enable noise suppression cut.
* **`SigmaCut`** (`float`, default `2.0`): Threshold factor for the sigma noise cut.
* **`RingerTopology`** (`CaloRingsTopology`, default `Standard`): The ring topology to use.
* **`CornerShift`** (`int`, default `None`): Shift magnitude in cell units for the `Corner` topology (defaults to `3` if `None`).
* **`CrossShift`** (`int`, default `None`): Shift magnitude in cell units for the `Cross` topology (defaults to `3` if `None`).
* **`RingsShiftEta` / `RingsShiftPhi`** (`List[float]`, default `None`): Custom shift vectors in cell units (defaults to `[0]` if `None`).
* **`Axis`** (`int`, default `None`): Strips axis (`0` for $\eta$, `1` for $\phi$; defaults to `0` if `None`).

### Returned Value
The configuration function returns a list containing three configuration tools:
1. **Central/Main Ringer**: Handles ring calculation in the central region ($\eta \in [0.0, 2.5]$) according to the selected topology.
2. **Forward Ringer**: Handles standard ring calculation in the forward region ($\eta \in [2.5, 4.9]$).
3. **Merge Ringer**: Merges the central and forward ring collections into the single final container.

---

## Python Configuration Example

Below is an example showing how to import, configure, and use `CaloRingsBuilderCfg` in a job configuration script:

```python
import ROOT
from GaugiKernel import LoggingLevel, ComponentAccumulator
from CaloRingsBuilder import CaloRingsBuilderCfg, CaloRingsTopology

def configure_reconstruction_job():
    # 1. Initialize the ComponentAccumulator for managing job components
    acc = ComponentAccumulator("RecoJobAccumulator", "output.AOD.root")
    output_level = LoggingLevel.INFO

    # 2. Configure Standard Rings
    # Reads clusters from "Clusters" and writes merged rings to "RingsL0"
    std_rings_tools = CaloRingsBuilderCfg(
        name="CaloRingsBuilder_Std",
        InputClusterKey="Clusters",
        OutputRingerKey="RingsL0",
        OutputLevel=output_level,
        HistogramPath="Expert/RingsL0",
        DoSigmaCut=True,
        SigmaCut=2.5,
        RingerTopology=CaloRingsTopology.Standard
    )
    
    # Register the configured tools in the accumulator
    for tool in std_rings_tools:
        acc.add(tool)

    # 3. Configure a Custom Topology Ring Builder
    # Example: Corner Rings with a custom shift of 2 cells
    corner_rings_tools = CaloRingsBuilderCfg(
        name="CaloRingsBuilder_Corner",
        InputClusterKey="Clusters",
        OutputRingerKey="CornerRings",
        OutputLevel=output_level,
        HistogramPath="Expert/CornerRings",
        RingerTopology=CaloRingsTopology.Corner,
        CornerShift=2
    )
    
    for tool in corner_rings_tools:
        acc.add(tool)

    # 4. Configure Custom Shifts
    custom_rings_tools = CaloRingsBuilderCfg(
        name="CaloRingsBuilder_Custom",
        InputClusterKey="Clusters",
        OutputRingerKey="CustomRings",
        OutputLevel=output_level,
        HistogramPath="Expert/CustomRings",
        RingerTopology=CaloRingsTopology.Custom,
        RingsShiftEta=[0.0, -1.0, 1.0],
        RingsShiftPhi=[0.0, 1.0, -1.0]
    )
    
    for tool in custom_rings_tools:
        acc.add(tool)

    return acc

if __name__ == "__main__":
    job_acc = configure_reconstruction_job()
    print("CaloRings configuration completed successfully!")
```
