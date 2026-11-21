# CaloRingsBuilder

`CaloRingsBuilder` is a package responsible for orchestrating the generation of calorimeter ring energy sums (known as **Rings** or **Ringer features**) from reconstructed clusters (`xAOD::CaloCluster`).

In this refactored architecture, `CaloRingsBuilder` implements the **Maker + Tool** pattern:
- **`CaloRingsMaker`** (`Gaugi::Algorithm`): Manages the container lifecycle in StoreGate (`xAOD::CaloRingsContainer`), applies cluster acceptance cuts (`EtaRange`), iterates over `CaloClusters`, instantiates `xAOD::CaloRings`, and delegates the actual ring decoration to a coupled specialist tool.
- **Specialist Tools** (`CaloRingsTools`): Specialized tools (e.g. `StandardRingsTool`, `AsymRingsTool`, `CrossRingsTool`, `CornerRingsTool`, `StripsRingsTool`, `CustomRingsTool`) calculate the geometric distributions and decorate the `xAOD::CaloRings` object via `rings->setRings(ref_rings)`.

---

## Architecture & Data Flow

```
                                  ┌─────────────────────────────────────────┐
                                  │          ComponentAccumulator           │
                                  └────────────────────┬────────────────────┘
                                                       │
                                                       │ acc += rings (list of all 6 makers)
            ┌─────────────────────┬────────────────────┼────────────────────┬─────────────────────┬─────────────────────┐
            │                     │                    │                    │                     │                     │
            ▼                     ▼                    ▼                    ▼                     ▼                     ▼
┌───────────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│    CaloRingsMaker     │ │  CaloRingsMaker  │ │  CaloRingsMaker  │ │  CaloRingsMaker   │ │  CaloRingsMaker   │ │  CaloRingsMaker   │
│      (Standard)       │ │      (Asym)      │ │     (Cross)      │ │     (Corner)      │ │     (Strips)      │ │     (Custom)      │
│ - Key: "Rings"        │ │ - "Rings_Asym"   │ │ - "Rings_Cross"  │ │ - "Rings_Corner"  │ │ - "Rings_Strips"  │ │ - "Rings_Custom"  │
│ - Loops over Clusters │ │ - Loops Clusters │ │ - Loops Clusters │ │ - Loops Clusters  │ │ - Loops Clusters  │ │ - Loops Clusters  │
└───────────┬───────────┘ └────────┬─────────┘ └────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
            │                      │                    │                     │                     │                     │
            │ maker += tool        │ maker += tool      │ maker += tool       │ maker += tool       │ maker += tool       │ maker += tool
            ▼                      ▼                    ▼                     ▼                     ▼                     ▼
┌───────────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   StandardRingsTool   │ │  AsymRingsTool   │ │  CrossRingsTool  │ │  CornerRingsTool  │ │  StripsRingsTool  │ │  CustomRingsTool  │
│   (Gaugi::Tool)       │ │  (Gaugi::Tool)   │ │  (Gaugi::Tool)   │ │  (Gaugi::Tool)    │ │  (Gaugi::Tool)    │ │  (Gaugi::Tool)    │
│  - setRings(...)      │ │ - setRings(...)  │ │ - setRings(...)  │ │ - setRings(...)   │ │ - setRings(...)   │ │ - setRings(...)   │
└───────────┬───────────┘ └────────┬─────────┘ └────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
            │                      │                    │                     │                     │                     │
            ▼                      ▼                    ▼                     ▼                     ▼                     ▼
┌───────────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ xAOD::CaloRingsCont.  │ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│
│     Key: "Rings"      │ │ Key: "Rings_Asym"│ │Key: "Rings_Cross"│ │Key: "Rings_Corner"│ │Key: "Rings_Strips"│ │Key: "Rings_Custom"│
└───────────────────────┘ └──────────────────┘ └──────────────────┘ └───────────────────┘ └───────────────────┘ └───────────────────┘
```

---

## Python Configuration

The Python configuration is defined in [CaloRingsBuilder.py](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/calorimeter/CaloRingsBuilder/python/CaloRingsBuilder.py) without `**kwargs` and without conditional branching (`if/elif`).

### Helper Functions

* **`CaloRingsBuilderCfg(...)`**:
  Builds and returns **all 6 ring makers by default** (`Standard`, `Asym`, `Cross`, `Corner`, `Strips`, and `Custom`) as a `List[Configurable]`. Each maker has its dedicated tool attached.
* **`StandardRingsMakerCfg(...)`**: Configures a single maker with `StandardRingsTool` attached (container key: `"Rings"`).
* **`AsymRingsMakerCfg(...)`**: Configures a single maker with `AsymRingsTool` attached (container key: `"Rings_Asym"`).
* **`CrossRingsMakerCfg(...)`**: Configures a single maker with `CrossRingsTool` attached (container key: `"Rings_Cross"`).
* **`CornerRingsMakerCfg(...)`**: Configures a single maker with `CornerRingsTool` attached (container key: `"Rings_Corner"`).
* **`StripsRingsMakerCfg(...)`**: Configures a single maker with `StripsRingsTool` attached (container key: `"Rings_Strips"`).
* **`CustomRingsMakerCfg(...)`**: Configures a single maker with `CustomRingsTool` attached (container key: `"Rings_Custom"`).

---

## Usage Examples

### 1. Default Pipeline: All Topologies via `acc += rings`

```python
from GaugiKernel import ComponentAccumulator, LoggingLevel
from RootStreamBuilder import recordable
from CaloRingsBuilder import CaloRingsBuilderCfg

acc = ComponentAccumulator("RecoJobAccumulator", "output.AOD.root")

# Generates all 6 ring topologies by default
rings = CaloRingsBuilderCfg(
    "CaloRingsBuilder",
    InputClusterKey=recordable("Clusters"),
    OutputRingerKey=recordable("Rings"),
    OutputLevel=LoggingLevel.INFO,
)

# Appends all 6 makers in a single concise operation
acc += rings
```

### 2. Standalone Single Topology Execution

```python
from CaloRingsBuilder import StandardRingsMakerCfg
from RootStreamBuilder import recordable

# Only standard concentric rings
acc += StandardRingsMakerCfg(
    "StandardRingsMaker",
    InputClusterKey=recordable("Clusters"),
    OutputRingerKey=recordable("Rings"),
)
```
