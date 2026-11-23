# ATLAS: High-Fidelity Realistic ATLAS Detector Geometry

The `geometry/ATLAS/` package implements the detector geometry description for the **ATLAS** calorimeter in the **Lorenzetti** simulation framework. It supports both the imperative **v1** engine (GeoModel SQLite dump and legacy volume primitives) and the modern data-driven **v2** engine (JSON-based specification, zero PyROOT loop overhead, and fluent builders modeled after GALTIC).

Both versions coexist side-by-side in C++ and Python to allow seamless gradual migration.

---

## 1. Architecture Overview: v1 vs v2

| Feature | ATLAS v1 (`DetectorConstruction_v1`) | ATLAS v2 (`DetectorConstruction_v2`) |
| :--- | :--- | :--- |
| **Philosophy** | Imperative, script-driven volume assembly | Pure data-driven, declarative JSON configuration |
| **C++ Class** | `ATLAS::DetectorConstruction_v1` | `ATLAS::DetectorConstruction_v2` |
| **C++ Header** | `#include "ATLAS/DetectorConstruction_v1.h"` | `#include "ATLAS/DetectorConstruction_v2.h"` |
| **Python Namespace**| `ATLAS.v1` (`ATLAS.v1.DetectorConstruction`) | `ATLAS.v2` (`ATLAS.v2.DetectorConstruction`) |
| **C++ Ingestion** | Iterative `AddVolume(...)` calls over PyROOT RPC | Single `LoadGeometryFile(json_path)` in native C++ |
| **Configuration** | 24+ manual boolean flags (`AtlasGeometryFlags`) | Declarative schema in [`data/atlas_geometry.json`](data/atlas_geometry.json) |
| **Layer Builders** | Monolithic procedural subdetector functions | Fluent builders (`AtlasEmbBuilder`, `AtlasTileBuilder`, etc.) |
| **Performance** | High PyROOT boundary overhead (~40+ boundary hops) | Nanosecond native C++ JSON parsing (`nlohmann::json`) |
| **Use Cases** | Legacy compatibility, GeoModel SQLite dump | Production simulation, Fast simulation, Visualizer |

---

## 2. Key Physics & Engineering Features

1. **Pure Data-Driven C++ Geometry Ingestion (v2)**:
   - Geometry layout (33 active calorimeter sampling layers and 8 dead material envelopes) is defined declaratively and loaded directly in C++ via `nlohmann::json`.
   - Eliminates hundreds of Python-to-C++ RPC calls during geometry setup.

2. **GeoModel SQLite Import (v1 `AtlasGeoModelImport`)**:
   - Reads the SQLite geometry dump of the ATLAS Run 4 simulation (`ATLAS-P2-RUN4-01-01-00`).
   - Imports real detector envelopes, cryostats, passive structural materials, ITk tracking cavity, and beam pipes with overlap checking.

3. **Forward Calorimeter (FCal) with Realistic Electrodes**:
   - Constructs high-granularity cylindrical modules (FCal1, FCal2, FCal3).
   - Reads cathode/anode electrode positions directly from `data/LArFCalElectrodes-06.csv`.

4. **Frozen Showers Fast Simulation (`FCalFrozenShowerModel`)**:
   - Replaces computationally intensive Geant4 shower development in dense tungsten/copper forward absorbers with pre-simulated shower parameterizations.
   - Loads shower libraries from `data/LArG4ShowerLibData/MC23_v1/` based on signed particle PDG code and incident energy.

5. **Dead Material Showers (`AtlasDeadMaterialShower`)**:
   - Simulates energy leakage and shower continuation in non-instrumented cryostats, support flanges, and barrel-endcap crack regions.

6. **Beam Pipe Particle Terminator (`SimpleFastKiller`)**:
   - Kills low-angle non-reconstructible background tracks within beam pipe forward regions, reducing execution overhead without biasing calorimeter observables.

7. **Coupled Magnetic Field (`magfield`)**:
   - Integrates with the standalone `magfield` library to supply the tabulated 2D/3D solenoid and toroid field map.

---

## 3. Package Structure

```text
geometry/ATLAS/
├── CMakeLists.txt                         # Builds GeoV2 library (namespace ATLAS)
├── README.md                              # This specification file
├── ATLAS/                                 # Public C++ Headers
│   ├── DetectorConstruction_v1.h         # Imperative Geant4 UserDetectorConstruction (v1)
│   ├── DetectorConstruction_v2.h         # Modern JSON-driven UserDetectorConstruction (v2)
│   ├── json.hpp                           # nlohmann::json header
│   ├── AtlasGeoModelImport.h
│   ├── AtlasDeadMaterialShower.h
│   ├── FCalFrozenShowerModel.h
│   ├── FCalShowerLib.h
│   ├── SimpleFastKiller.h
│   ├── EnergyCalculator.h                 # Athena EMEC energy calculation & charge collection
│   ├── EMECData.h, EMECDataCSV.h
│   ├── HVHelper.h, LArG4BirksLaw.h
│   ├── LArWheelCalculator.h, LArWheelCalculatorEnums.h
│   ├── LArWheelCalculator_Impl/            # Accordion fan & distance implementations
│   ├── GeoModelKernelUnits.h, vec_parametrized_sincos.h
│   └── PortableMsgStream.h, PortMsg.h
├── src/                                   # C++ Implementation and ROOT LinkDef
│   ├── DetectorConstruction_v1.cxx
│   ├── DetectorConstruction_v2.cxx
│   ├── AtlasGeoModelImport.cxx
│   ├── AtlasDeadMaterialShower.cxx
│   ├── FCalFrozenShowerModel.cxx
│   ├── FCalShowerLib.cxx
│   ├── SimpleFastKiller.cxx
│   ├── GeoSpecialShapes_*.cxx             # Accordion wheel calculators
│   ├── LArG4EC_*.cxx                      # EMEC charge collection & HV helper
│   └── LinkDef.h
├── python/                                # ATLAS Python Modules
│   ├── __init__.py                        # Top-level exports and default routing
│   ├── DetectorConstruction.py            # Forwarding shim supporting atlas_version="v1"|"v2"
│   ├── AtlasGeometryFlags.py              # Steering flags for v1
│   ├── v1/                                # ATLAS v1 Imperative Subsystem
│   │   ├── __init__.py
│   │   ├── DetectorConstruction.py        # v1 Python orchestrator calling ATLAS::DetectorConstruction_v1
│   │   ├── legacy/                        # Legacy volume primitives (Calorimeter, PhysicalVolume, etc.)
│   │   └── detectors/                     # Procedural ATLAS sub-detector modules (ECAL, TILE, EMEC, HEC, FCAL, etc.)
│   └── v2/                                # ATLAS v2 Modern Subsystem (GALTIC-like)
│       ├── __init__.py
│       ├── Layer.py                       # CaloSamplingLayer, DeadMaterialVolume, Plates, fluent builders
│       ├── AtlasCfg.py                    # Canonical layer registry (33 active layers + 8 dead materials)
│       └── DetectorConstruction.py        # v2 Python orchestrator calling ATLAS::DetectorConstruction_v2
├── data/                                  # Calibration, geometry JSON and electrode data
│   ├── atlas_geometry.json                # Canonical declarative geometry specification (v2)
│   ├── EmecTables-ATLAS-P2-RUN4-01-01-00.csv
│   ├── HVEMECMap_v02.dat
│   ├── LArFCalElectrodes-06.csv
│   └── LArG4ShowerLibData/MC23_v1/
└── scripts/                               # Geometry dump, generation & inspection scripts
    ├── generate_atlas_geometry.py         # Script generating data/atlas_geometry.json
    ├── atlas_run4_check_cells.py
    ├── atlas_run4_dumpgeo.sh
    ├── build_geomodel.sh
    ├── fcal_electrodes_from_geomdb.py
    ├── geomodel-6.29.0-gcc11.patch
    └── geomodel_compat_format.h
```

---

## 4. Usage Examples

### Using the Unified Factory (`DetectorConstructionCfg`)

The factory in `geometry/` provides explicit selection between `v1` and `v2`:

```python
from geometry import DetectorConstructionCfg

# 1. Instantiate modern JSON-driven ATLAS v2 (Recommended):
det_v2 = DetectorConstructionCfg("ATLAS", detector="ATLAS", atlas_version="v2")

# 2. Instantiate legacy imperative ATLAS v1:
det_v1 = DetectorConstructionCfg("ATLAS", detector="ATLAS", atlas_version="v1")
```

### Direct Python Module Usage (v2 Modern Architecture)

```python
from ATLAS.v2 import (
    AtlasDetectorConstruction,
    AtlasEmbBuilder,
    AtlasTileBuilder,
    CaloSamplingLayer,
    Plates,
)
from CaloCell.CaloDefs import CaloSampling

# Load canonical ATLAS detector from JSON:
detector = AtlasDetectorConstruction("ATLAS")

# Or construct custom sampling layers via fluent builders:
emb1 = (
    AtlasEmbBuilder("LAr::EMB1", CaloSampling.EMB1)
    .radii(1500.0, 1597.468)
    .z_length(6330.0)
    .accordion(lead_th=1.53, lar_gap=4.5, n_layers=14)
    .granularity(d_eta=0.003125, d_phi=0.02454)
    .electronics(noise_mev=40.0, pulse_file="pulseLar.dat")
    .build()
)

detector.add_layer(emb1)
detector.dump("custom_atlas.json")
```

### Direct Python Module Usage (v1 Imperative Architecture)

```python
from ATLAS.v1 import AtlasDetectorConstruction as AtlasDetectorConstructionV1
from ATLAS import AtlasGeometryFlags

# Configure flags
AtlasGeometryFlags.AtlasEmb = True
AtlasGeometryFlags.TileAtlasGap = True

# Construct detector
det_v1 = AtlasDetectorConstructionV1("ATLAS_V1")
```

---

## 5. External Prerequisites for Full ATLAS Run 4 Geometry (v1)

The full Run 4 model requires GeoModel libraries and geometry/field assets:

| Asset | Size | How to obtain | Where Lorenzetti looks |
| :--- | :---: | :--- | :--- |
| **GeoModel 6.29.0** | | `bash geometry/ATLAS/scripts/build_geomodel.sh ~/geomodel` | `GEOMODEL_DIR` environment variable |
| **Run 4 Geometry SQLite DB** | 92 MB | `bash geometry/ATLAS/scripts/atlas_run4_dumpgeo.sh` (from Athena lxplus) | `AtlasGeometryFlags.AtlasRun4Geometry` or `LORENZETTI_ATLAS_RUN4_GEOMETRY` |
| **ATLAS Field Map** | 126 MB | `/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/MagneticFieldMaps/` | `MagFieldFlags.FieldMapFile` or `LORENZETTI_FIELD_MAP` |
| **FCal Shower Libraries** | 31 MB | `/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/LArG4ShowerLibData/MC23_v1` | `geometry/ATLAS/data/LArG4ShowerLibData/MC23_v1` |
