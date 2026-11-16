# Detector Geometry Package (`geometry/`)

The `geometry/` package manages detector geometries for the **Lorenzetti** simulation framework. It is modularized into two distinct versions:

- **[v1 (Classical Lorenzetti Geometry)](v1/README.md)**: Standard cylindrical $4\pi$ calorimeter model implemented with Geant4 primitives. Lightweight, fast, and self-contained.
- **[v2 (ATLAS Run 4 Geometry)](v2/README.md)**: High-fidelity ATLAS Run 4 geometry imported from official GeoModel SQLite dumps, featuring realistic FCal forward calorimetry, frozen shower models, and integration with the standalone [`magfield/`](../magfield/README.md) package.

---

## Architecture Overview

```text
geometry/
├── CMakeLists.txt              # Top-level geometry orchestrator (add_subdirectory v1 & v2)
├── README.md                   # This overview file
├── v1/                         # Self-contained Classical Detector Package
│   ├── README.md               # v1 comprehensive documentation
│   ├── CMakeLists.txt          # Library geometry_v1
│   ├── v1/                     # Public C++ headers
│   ├── src/                    # C++ implementations & LinkDef.h
│   ├── python/                 # geometry.v1 Python modules
│   ├── data/                   # Pulse files (pulseLar.dat, pulseTile.dat)
│   ├── scripts/                # Visualization scripts (run_vis.py)
│   └── doc/                    # Visual diagrams and views
└── v2/                         # Self-contained ATLAS Run 4 Package
    ├── README.md               # v2 comprehensive documentation
    ├── CMakeLists.txt          # Library geometry_v2
    ├── v2/                     # Public C++ headers
    ├── src/                    # C++ implementations & LinkDef.h
    ├── python/                 # geometry.v2 Python modules
    ├── data/                   # FCal electrodes, ShowerLib, and pulse files
    └── scripts/                # GeoModel and cell check scripts
```

---

## Python API Usage

Import directly from the respective version subpackage:
```python
from geometry.v1 import DetectorConstruction_v1
from geometry.v2 import DetectorConstruction_v2
```

For detailed subdetector specifications and parameters, consult:
- **[geometry/v1 Documentation](v1/README.md)**
- **[geometry/v2 Documentation](v2/README.md)**
- **[magfield Documentation](../magfield/README.md)**
