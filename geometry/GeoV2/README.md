# ATLAS Run 4 Detector Geometry (`geometry/v2/`)

The `geometry/v2/` package implements the high-fidelity **ATLAS Run 4** detector geometry description for the **Lorenzetti** simulation framework. It directly imports the full ATLAS geometry volumes from its official GeoModel SQLite dump, couples with the high-precision magnetic field package (`magfield`), and integrates frozen shower models for accelerated forward calorimetry.

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
geometry/v2/
├── CMakeLists.txt              # Builds geometry_v2 OBJECT library (with C++20 GeoModel support)
├── README.md                   # This specification file
├── v2/                         # C++ Public headers
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
├── python/                     # Python volume builders
│   ├── DetectorConstruction_v2.py
│   ├── AtlasRun4.py
│   ├── AtlasFCal.py
│   ├── AtlasBarrelCryostat.py
│   ├── AtlasBarrelFront.py
│   ├── Calorimeter.py
│   ├── ECAL.py
│   ├── EMEC.py
│   ├── FCAL.py
│   ├── HEC.py
│   ├── TILE.py
│   ├── Tracking.py
│   └── DeadMaterials.py
├── data/                       # ATLAS geometry calibration data
│   ├── pulseLar.dat
│   ├── pulseTile.dat
│   ├── LArFCalElectrodes-06.csv
│   └── LArG4ShowerLibData/
│       └── MC23_v1/
└── scripts/                    # Geometry database dump & inspection scripts
    ├── atlas_run4_check_cells.py
    ├── atlas_run4_dumpgeo.sh
    ├── build_geomodel.sh
    ├── fcal_electrodes_from_geomdb.py
    ├── geomodel-6.29.0-gcc11.patch
    └── geomodel_compat_format.h
```

---

## 3. Usage & Configuration via `AtlasGeometryFlags`

The ATLAS geometry options are managed through the [`AtlasGeometryFlags`](../../doc/flags.md#1-atlasgeometryflags-geometryv2pythonatlasgeometryflagspy) dataclass. With `--detector v2`, all ATLAS sub-detectors, cryostats, and physics options are enabled by default.

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

### Python Programmatic Instantiation

```python
from GeoV2 import DetectorConstruction_v2, AtlasGeometryFlags

# Customize flags:
AtlasGeometryFlags.AtlasEmb = True
AtlasGeometryFlags.AtlasRun4Geometry = "/path/to/geometry.sqlite"
AtlasGeometryFlags.apply_defaults(is_v2=True)

# Instantiate detector from flags:
detector = DetectorConstruction_v2("ATLAS_Run4", **AtlasGeometryFlags.to_dict())
```
