# Detector Geometry Packages (`geometry/`)

The `geometry/` directory manages detector geometries for the **Lorenzetti** simulation framework. It is modularized into three first-class packages:

- **[GeoBase](GeoBase/)**: Shared geometry building blocks (`PhysicalVolume`, `SensitiveDetector`, `Calorimeter`, `Tracking`), common pulse data (`pulseTile.dat`, `pulseLar.dat`), and the centralized factory **`DetectorConstructionCfg`**.
- **[GeoV1](GeoV1/)**: Classical cylindrical $4\pi$ calorimeter model implemented with Geant4 primitives. Lightweight, fast, and self-contained. Sub-detectors reside in `GeoV1.detectors`.
- **[GeoV2](GeoV2/)**: High-fidelity ATLAS Run 4 geometry imported from official GeoModel SQLite dumps, featuring realistic FCal forward calorimetry, frozen shower models, and integration with the standalone [`magfield/`](../magfield/README.md) package. Sub-detectors reside in `GeoV2.detectors`.

---

## Architecture Overview

```text
geometry/
├── CMakeLists.txt              # Orchestrator (add_subdirectory GeoBase, GeoV1, GeoV2)
├── README.md                   # This overview file
├── GeoBase/                    # Shared Primitives, Common Data & Factory
│   ├── CMakeLists.txt          # Installs GeoBase Python module and shared data
│   ├── python/                 # GeoBase modules (DetectorConstructionCfg, DetectorFlags, PhysicalVolume, etc.)
│   └── data/                   # Shared pulse files (pulseLar.dat, pulseTile.dat)
├── GeoV1/                      # Classical Detector Package
│   ├── CMakeLists.txt          # Library GeoV1
│   ├── GeoV1/                  # Public C++ headers
│   ├── src/                    # C++ implementations & LinkDef.h
│   ├── python/                 # GeoV1 Python module (DetectorConstruction_v1, detectors/)
│   └── scripts/                # Visualization scripts (run_vis.py)
└── GeoV2/                      # ATLAS Run 4 Package
    ├── CMakeLists.txt          # Library GeoV2
    ├── GeoV2/                  # Public C++ headers
    ├── src/                    # C++ implementations & LinkDef.h
    ├── GeoSpecialShapes/       # EMEC accordion shapes
    ├── LArG4EC/                # Athena ported charge collection
    ├── python/                 # GeoV2 Python module (DetectorConstruction_v2, AtlasGeometryFlags, detectors/)
    ├── data/                   # FCal electrodes, EMEC tables, and ShowerLib
    └── scripts/                # GeoModel and cell check scripts
```

---

## Python API Usage

### Recommended: Unified Factory (`DetectorConstructionCfg`)
```python
from GeoBase import DetectorConstructionCfg

# Automatically detects version or uses flags:
det = DetectorConstructionCfg("ATLAS", version="v2")
```

### Direct Package Usage:
```python
from GeoV1 import DetectorConstruction_v1
# or
from GeoV2 import DetectorConstruction_v2, AtlasGeometryFlags
```
