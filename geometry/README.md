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
│   ├── README.md               # GeoBase documentation
│   ├── data/                   # Shared pulse files (pulseLar.dat, pulseTile.dat)
│   ├── python/                 # GeoBase modules (DetectorConstructionCfg, DetectorFlags, PhysicalVolume, etc.)
│   └── tests/                  # Unit tests (test_detector_construction_cfg.py)
├── GeoV1/                      # Classical Detector Package
│   ├── CMakeLists.txt          # Target GeoV1
│   ├── README.md               # GeoV1 documentation & ray-traced views
│   ├── GeoV1/                  # Public C++ headers (DetectorConstruction_v1.h)
│   ├── src/                    # C++ implementations & LinkDef.h
│   ├── python/                 # GeoV1 Python module (DetectorConstruction_v1, detectors/)
│   └── scripts/                # Visualization scripts (run_vis.py)
└── GeoV2/                      # ATLAS Run 4 Package
    ├── CMakeLists.txt          # Target GeoV2
    ├── README.md               # GeoV2 documentation & external prerequisites
    ├── GeoV2/                  # Public C++ headers (unified: DetectorConstruction, EMEC, FCal, etc.)
    ├── src/                    # C++ implementations & LinkDef.h
    ├── python/                 # GeoV2 Python module (DetectorConstruction_v2, AtlasGeometryFlags, detectors/)
    ├── data/                   # FCal electrodes, EMEC tables, and ShowerLib
    └── scripts/                # GeoModel and cell check scripts
```

---

## Python API Usage

### Recommended: Unified Factory (`DetectorConstructionCfg`)
```python
from GeoBase import DetectorConstructionCfg

# Automatically resolves target version from DetectorFlags.Version (default: "v1"):
det = DetectorConstructionCfg("ATLAS")

# Or explicitly select version:
det_v1 = DetectorConstructionCfg("ATLAS", version="v1")
det_v2 = DetectorConstructionCfg("ATLAS", version="v2")
```

### Direct Package Usage:
```python
# Classical detector:
from GeoV1 import DetectorConstruction_v1
from GeoV1.detectors import ECAL, TILE, EMEC, HEC

# ATLAS Run 4 detector:
from GeoV2 import DetectorConstruction_v2, AtlasGeometryFlags
from GeoV2.detectors import AtlasEmb, AtlasTile, AtlasEmec, AtlasHec
```

---

## Subsystem Documentation

- [GeoBase Documentation](GeoBase/README.md): Shared primitives, pulse data, and factory implementation.
- [GeoV1 Documentation](GeoV1/README.md): Classical geometry description, layer specifications, and ray-traced views.
- [GeoV2 Documentation](GeoV2/README.md): ATLAS Run 4 geometry, GeoModel SQLite import, and frozen showers.
- [Flags Reference Guide](../doc/flags.md): Complete steering flags manual for `AtlasGeometryFlags` and `DetectorFlags`.
