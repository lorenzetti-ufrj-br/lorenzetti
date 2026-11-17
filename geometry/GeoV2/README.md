# ATLAS Run 4 Detector Geometry (`GeoV2`)

The `geometry/GeoV2/` package implements the high-fidelity **ATLAS Run 4** detector geometry description for the **Lorenzetti** simulation framework. It directly imports the full ATLAS geometry volumes from its official GeoModel SQLite dump, couples with the high-precision magnetic field package ([`magfield/`](../../magfield/README.md)), and integrates frozen shower models for accelerated forward calorimetry.

Common primitives (`PhysicalVolume`, `SensitiveDetector`, `Calorimeter`, `Tracking`) and pulse data are imported directly from **`GeoBase`**.

---

## 1. Key Physics & Engineering Features

1. **GeoModel SQLite Import (`AtlasGeoModelImport`)**:
   - Reads the SQLite geometry dump of the ATLAS Run 4 simulation (`ATLAS-P2-RUN4-01-01-00`).
   - Imports real detector envelopes, cryostats, passive structural materials, ITk tracking cavity, and beam pipes with overlap checking.

2. **Forward Calorimeter (FCal) with Realistic Electrodes**:
   - Constructs high-granularity cylindrical modules (FCal1, FCal2, FCal3).
   - Reads thousands of cathode/anode electrode positions directly from `data/LArFCalElectrodes-06.csv`.

3. **Frozen Showers Fast Simulation (`FCalFrozenShowerModel`)**:
   - Replaces computationally intensive Geant4 shower development in the dense tungsten/copper forward absorbers with pre-simulated shower parameterizations.
   - Loads libraries from `data/LArG4ShowerLibData/MC23_v1/` based on signed particle PDG code and incident energy.

4. **Dead Material Showers (`AtlasDeadMaterialShower`)**:
   - Simulates energy leakage and shower continuation in non-instrumented cryostats, support flanges, and barrel-endcap crack regions.

5. **Beam Pipe Particle Terminator (`SimpleFastKiller`)**:
   - Kills low-angle non-reconstructible background tracks within beam pipe forward regions, reducing execution overhead without biasing calorimeter observables.

6. **Coupled Magnetic Field (`magfield`)**:
   - Integrates with the standalone `magfield` library to supply the tabulated 2D/3D solenoid and toroid field map.

---

## 2. Package Structure

```text
geometry/GeoV2/
├── CMakeLists.txt              # Builds GeoV2 OBJECT library (with C++20 GeoModel support)
├── README.md                   # This specification file
├── GeoV2/                      # C++ Public headers
│   ├── DetectorConstruction_v2.h
│   ├── AtlasGeoModelImport.h
│   ├── AtlasDeadMaterialShower.h
│   ├── FCalFrozenShowerModel.h
│   ├── FCalShowerLib.h
│   └── SimpleFastKiller.h
├── src/                        # C++ Implementation and ROOT LinkDef
│   ├── DetectorConstruction_v2.cxx
│   ├── AtlasGeoModelImport.cxx
│   ├── AtlasDeadMaterialShower.cxx
│   ├── FCalFrozenShowerModel.cxx
│   ├── FCalShowerLib.cxx
│   ├── SimpleFastKiller.cxx
│   └── LinkDef.h
├── GeoSpecialShapes/           # LAr wheel accordion calculators
├── LArG4EC/                    # Athena-ported EMEC charge collection
├── PortableMsgStream/          # Standalone Athena messaging wrapper
├── python/                     # GeoV2 Python module
│   ├── __init__.py             # Exports DetectorConstruction_v2, AtlasGeometryFlags, detectors
│   ├── DetectorConstruction_v2.py # Top-level Python builder
│   ├── AtlasGeometryFlags.py   # Dataclass flags for 24 ATLAS geometry switches
│   └── detectors/              # Sub-detector builders
│       ├── __init__.py
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
├── data/                       # Calibration and electrode data
│   ├── EmecTables-ATLAS-P2-RUN4-01-01-00.csv
│   ├── HVEMECMap_v02.dat
│   ├── LArFCalElectrodes-06.csv
│   └── LArG4ShowerLibData/MC23_v1/
└── scripts/                    # Geometry database dump & inspection scripts
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
| **GeoModel 6.29.0** | | `bash geometry/GeoV2/scripts/build_geomodel.sh ~/geomodel` | `GEOMODEL_DIR` environment variable |
| **Run 4 Geometry SQLite DB** | 92 MB | `bash geometry/GeoV2/scripts/atlas_run4_dumpgeo.sh` (from Athena lxplus) | `AtlasGeometryFlags.AtlasRun4Geometry` or `LORENZETTI_ATLAS_RUN4_GEOMETRY` |
| **ATLAS Field Map** | 126 MB | `/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/MagneticFieldMaps/` | `MagFieldFlags.FieldMapFile` or `LORENZETTI_FIELD_MAP` |
| **FCal Shower Libraries** | 31 MB | `/cvmfs/atlas.cern.ch/repo/sw/database/GroupData/LArG4ShowerLibData/MC23_v1` | `geometry/GeoV2/data/LArG4ShowerLibData/MC23_v1` |

---

## 4. Usage & Configuration via `AtlasGeometryFlags`

The ATLAS geometry options are steered through the [`AtlasGeometryFlags`](../../doc/flags.md#1-atlasgeometryflags-geometrygeov2pythonatlasgeometryflagspy) dataclass. With `--detector v2`, all ATLAS sub-detectors, cryostats, and physics options are enabled by default.

### Factory Instantiation (Recommended)

```python
from GeoBase import DetectorConstructionCfg

# Standard V2 instantiation with automatic flag application:
detector = DetectorConstructionCfg("ATLAS", version="v2")
```

### Simulation Transform (`simu_trf.py`)

```bash
# Standard ATLAS Run 4 simulation:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 -nt 4

# Customizing subdetectors via --pre-init:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 \
    --pre-init "from GeoV2 import AtlasGeometryFlags as Geo; Geo.AtlasEmb = False; Geo.AtlasEmbCells = False"
```

### Digitization Transform (`digit_trf.py`)

```bash
digit_trf.py -i input.HIT.root -o output.ESD.root --detector v2
```

### Programmatic Python Configuration

```python
from GeoBase import DetectorConstructionCfg
from GeoV2 import AtlasGeometryFlags

# Steer geometry flags before instantiation:
AtlasGeometryFlags.AtlasEmb = True
AtlasGeometryFlags.TileAtlasRun4 = True

# Instantiate with factory:
det = DetectorConstructionCfg("ATLAS", version="v2")
```
