# Detector Geometry Package (`geometry/`)

The `geometry/` package manages detector geometries for the **Lorenzetti** simulation framework. It is modularized into two distinct versions:

- **[v1 (Classical Lorenzetti Geometry)](v1/README.md)**: Standard cylindrical $4\pi$ calorimeter model implemented with Geant4 primitives. Lightweight, fast, and self-contained.
- **[v2 (ATLAS Run 4 Geometry)](v2/README.md)**: High-fidelity ATLAS Run 4 geometry imported from official GeoModel SQLite dumps, featuring realistic FCal forward calorimetry, frozen shower models, and integration with the standalone [`magfield/`](../magfield/README.md) package.

---

## Architecture Overview

```text
geometry/
├── CMakeLists.txt              # Top-level geometry orchestrator
├── README.md                   # This overview file
├── python/                     # Unified facade for backward compatibility
│   ├── __init__.py             # Re-exports DetectorConstruction_v1 and v2
│   ├── v1 -> ../v1/python      # Symlink to v1 Python package
│   └── v2 -> ../v2/python      # Symlink to v2 Python package
├── data/                       # Unified symlinks for data resolution
├── scripts/                    # Unified symlinks for scripts
├── v1/                         # Self-contained Classical Detector Package
│   ├── README.md
│   ├── CMakeLists.txt
│   ├── v1/
│   ├── src/
│   ├── python/
│   ├── data/
│   ├── scripts/
│   └── doc/
└── v2/                         # Self-contained ATLAS Run 4 Package
    ├── README.md
    ├── CMakeLists.txt
    ├── v2/
    ├── src/
    ├── python/
    ├── data/
    └── scripts/
```

---

## Python API Usage

You can import either from the top-level facade:
```python
from geometry import DetectorConstruction_v1, DetectorConstruction_v2
```

Or directly from the respective version submodule:
```python
from geometry.v1 import DetectorConstruction_v1
from geometry.v2 import DetectorConstruction_v2
```

For detailed subdetector specifications and parameters, consult:
- **[geometry/v1 Documentation](v1/README.md)**
- **[geometry/v2 Documentation](v2/README.md)**
- **[magfield Documentation](../magfield/README.md)**
