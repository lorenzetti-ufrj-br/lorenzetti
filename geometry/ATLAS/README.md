# ATLAS: High-Fidelity Realistic ATLAS Detector Geometry

The `geometry/ATLAS/` package implements the high-fidelity **ATLAS Run 4** detector geometry description for the **Lorenzetti** simulation framework. It imports the full ATLAS geometry volumes from its official GeoModel SQLite dump, couples with the high-precision magnetic field package ([`magfield/`](../../magfield/README.md)), and integrates frozen shower models for accelerated forward calorimetry.

All legacy `v2` nomenclature and compatibility shims (such as `DetectorConstruction_v2.py`) have been **completely eliminated** in favor of canonical `AtlasDetectorConstruction` and `#include "ATLAS/..."`.

---

## 1. Key Physics & Engineering Features

1. **GeoModel SQLite Import (`AtlasGeoModelImport`)**:
   - Reads the SQLite geometry dump of the ATLAS Run 4 simulation (`ATLAS-P2-RUN4-01-01-00`).
   - Imports real detector envelopes, cryostats, passive structural materials, ITk tracking cavity, and beam pipes with overlap checking.

2. **Forward Calorimeter (FCal) with Realistic Electrodes**:
   - Constructs high-granularity cylindrical modules (FCal1, FCal2, FCal3).
   - Reads thousands of cathode/anode electrode positions directly from `data/LArFCalElectrodes-06.csv`.

3. **Frozen Showers Fast Simulation (`FCalFrozenShowerModel`)**:
   - Replaces computationally intensive Geant4 shower development in dense tungsten/copper forward absorbers with pre-simulated shower parameterizations.
   - Loads shower libraries from `data/LArG4ShowerLibData/MC23_v1/` based on signed particle PDG code and incident energy.

4. **Dead Material Showers (`AtlasDeadMaterialShower`)**:
   - Simulates energy leakage and shower continuation in non-instrumented cryostats, support flanges, and barrel-endcap crack regions.

5. **Beam Pipe Particle Terminator (`SimpleFastKiller`)**:
   - Kills low-angle non-reconstructible background tracks within beam pipe forward regions, reducing execution overhead without biasing calorimeter observables.

6. **Coupled Magnetic Field (`magfield`)**:
   - Integrates with the standalone `magfield` library to supply the tabulated 2D/3D solenoid and toroid field map.

---

## 2. Package Structure

```text
geometry/ATLAS/
├── CMakeLists.txt                         # Builds ATLAS C++ library (with C++20 GeoModel support)
├── README.md                              # This specification file
├── ATLAS/                                 # C++ Public Headers (canonical include path: #include "ATLAS/...")
│   ├── DetectorConstruction_v2.h         # Geant4 UserDetectorConstruction engine
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
│   ├── DetectorConstruction_v2.cxx
│   ├── AtlasGeoModelImport.cxx
│   ├── AtlasDeadMaterialShower.cxx
│   ├── FCalFrozenShowerModel.cxx
│   ├── FCalShowerLib.cxx
│   ├── SimpleFastKiller.cxx
│   ├── GeoSpecialShapes_*.cxx             # Accordion wheel calculators
│   ├── LArG4EC_*.cxx                      # EMEC charge collection & HV helper
│   └── LinkDef.h
├── python/                                # ATLAS Python Module
│   ├── __init__.py                        # Exports AtlasDetectorConstruction, DetectorConstruction, AtlasGeometryFlags
│   ├── DetectorConstruction.py            # Canonical top-level Python builder (AtlasDetectorConstruction)
│   ├── AtlasGeometryFlags.py              # Dataclass flags for 24 ATLAS geometry switches
│   ├── legacy/                            # Isolated legacy volume primitives (Calorimeter, PhysicalVolume, etc.)
│   └── detectors/                         # Detailed ATLAS sub-detector builders
│       ├── AtlasBarrelCryostat.py
│       ├── AtlasBarrelFront.py
│       ├── AtlasEmb.py
│       ├── AtlasEmec.py
│       ├── AtlasFCal.py
│       ├── AtlasHec.py
│       ├── AtlasRun4.py
│       ├── AtlasTile.py
│       ├── DeadMaterials.py
│       ├── ECAL.py
│       ├── EMEC.py
│       ├── FCAL.py
│       ├── HEC.py
│       └── TILE.py
├── data/                                  # Calibration and electrode data
│   ├── EmecTables-ATLAS-P2-RUN4-01-01-00.csv
│   ├── HVEMECMap_v02.dat
│   ├── LArFCalElectrodes-06.csv
│   └── LArG4ShowerLibData/MC23_v1/
└── scripts/                               # Geometry database dump & inspection scripts
    ├── atlas_run4_check_cells.py
    ├── atlas_run4_dumpgeo.sh
    ├── build_geomodel.sh
    ├── fcal_electrodes_from_geomdb.py
    ├── geomodel-6.29.0-gcc11.patch
    └── geomodel_compat_format.h
```

---

## 3. External Prerequisites for Full ATLAS Run 4 Geometry

The full Run 4 model requires GeoModel libraries and geometry/field assets:

| Asset | Size | How to obtain | Where Lorenzetti looks |
| :--- | :---: | :--- | :--- |
| **GeoModel 6.29.0** | | `bash geometry/ATLAS/scripts/build_geomodel.sh ~/geomodel` | `GEOMODEL_DIR` environment variable |
| **Run 4 Geometry SQLite DB** | 92 MB | `bash geometry/ATLAS/scripts/atlas_run4_dumpgeo.sh` (from Athena lxplus) | `AtlasGeometryFlags.AtlasRun4Geometry` or `LORENZETTI_ATLAS_RUN4_GEOMETRY` |
| **ATLAS Field Map** | 126 MB | `/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/MagneticFieldMaps/` | `MagFieldFlags.FieldMapFile` or `LORENZETTI_FIELD_MAP` |
| **FCal Shower Libraries** | 31 MB | `/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/LArG4ShowerLibData/MC23_v1` | `geometry/ATLAS/data/LArG4ShowerLibData/MC23_v1` |

---

## 4. Usage & Configuration via `AtlasGeometryFlags`

The ATLAS geometry options are steered through the [`AtlasGeometryFlags`](../../doc/flags.md#1-atlasgeometryflags) dataclass. With `--detector atlas`, all standard ATLAS sub-detectors and physics options are enabled by default.

### Factory Instantiation (Recommended)

```python
from geometry import DetectorConstructionCfg

# Standard ATLAS instantiation:
detector = DetectorConstructionCfg("ATLAS", version="ATLAS")
```

### Simulation Transform (`simu_trf.py`)

```bash
# Standard ATLAS Run 4 simulation:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector atlas -nt 4

# Customizing subdetectors via --pre-init:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector atlas \
    --pre-init "from ATLAS import AtlasGeometryFlags as Geo; Geo.AtlasEmb = False; Geo.AtlasEmbCells = False"
```

### Digitization Transform (`digit_trf.py`)

```bash
digit_trf.py -i input.HIT.root -o output.ESD.root --detector atlas
```

### Programmatic Python Configuration

```python
from geometry import DetectorConstructionCfg
from ATLAS import AtlasGeometryFlags

# Steer geometry flags before instantiation:
AtlasGeometryFlags.AtlasEmb = True
AtlasGeometryFlags.TileAtlasGap = True

# Instantiate with factory:
det = DetectorConstructionCfg("ATLAS", version="ATLAS")
```
