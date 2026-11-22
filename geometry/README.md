# Lorenzetti Geometry Subsystem (`geometry/`)

The `geometry/` directory manages all detector geometries for the **Lorenzetti** simulation framework. It is organized into three first-class packages unified under a central root factory:

- **[GALTIC](GALTIC/)**: *General Argon Liquid and Tile Integrated Calorimeter*. A high-performance, parametric $4\pi$ calorimeter model driven by declarative JSON (`galtic_geometry.json`) with direct C++ volume parsing. Lightweight, self-contained, and ideal for fast simulation and algorithmic development.
- **[ATLAS](ATLAS/)**: High-fidelity ATLAS Run 4 geometry imported from official GeoModel SQLite dumps, featuring realistic FCal forward calorimetry, frozen shower models, and integration with the standalone [`magfield/`](../magfield/README.md) package.
- **[visualizer](visualizer/)**: Asynchronous FastAPI 3D WebGL viewer (Three.js) supporting dynamic wedge $\phi$ and longitudinal $R-Z$ cutaways, cell granularity inspection HUD, CAD mesh extraction via ROOT `TGeoManager`, and 100% mathematically vectorized PDF technical drawings.

All legacy `v1`/`v2` nomenclature, `GeoBase` intermediate couplings, and backwards-compatibility shims (`DetectorConstruction_v2.py`) have been **completely eliminated**.

---

## Architecture Overview

```text
geometry/
├── CMakeLists.txt                         # Orchestrates GALTIC, ATLAS, and visualizer
├── __init__.py                            # [ROOT FACTORY] Exports DetectorConstructionCfg and DetectorFlags
├── README.md                              # This overview file
├── GALTIC/                                # Parametric Calorimeter Package (GALTIC)
│   ├── CMakeLists.txt
│   ├── README.md                          # GALTIC documentation & layer specifications
│   ├── GALTIC/                            # C++ public headers (canonical include path: #include "GALTIC/...")
│   │   ├── DetectorConstruction_v1.h
│   │   └── json.hpp                       # nlohmann/json C++ header
│   ├── src/                               # C++ implementation (LoadGeometryFile direct JSON parser)
│   ├── python/                            # Consolidated Python modules (Layer.py, GalticCfg.py, DetectorConstruction.py)
│   ├── data/                              # Canonical galtic_geometry.json and pulse calibration files
│   ├── scripts/                           # CLI geometry generator (generate_galtic_geometry.py)
│   └── tests/                             # Unit tests (test_galtic_json.py)
├── ATLAS/                                 # Realistic ATLAS Run 4 Package
│   ├── CMakeLists.txt
│   ├── README.md                          # ATLAS documentation & external prerequisites
│   ├── ATLAS/                             # C++ public headers (canonical include path: #include "ATLAS/...")
│   ├── src/                               # C++ implementations & LinkDef.h
│   ├── python/                            # ATLAS module (AtlasDetectorConstruction, AtlasGeometryFlags, detectors/)
│   ├── data/                              # FCal electrodes, EMEC tables, and ShowerLib
│   ├── scripts/                           # GeoModel and cell check scripts
│   └── tests/
├── visualizer/                            # 3D WebGL Visualizer & Vector PDF Exporter
│   ├── CMakeLists.txt
│   ├── README.md                          # Visualizer architecture & API documentation
│   ├── python/                            # Server.py (FastAPI), CadReader.py, VectorPdfExporter.py
│   ├── web/                               # Three.js SPA (HTML5/CSS3/ES6)
│   ├── scripts/                           # visualizer_trf.py CLI tool
│   └── tests/                             # test_visualizer_export.py
└── tests/
    └── test_detector_factory.py           # Unit tests for the root geometry factory
```

---

## Python API Usage

### Central Factory (`DetectorConstructionCfg`)

The root `geometry/__init__.py` acts as the single entry point to instantiate either detector model:

```python
from geometry import DetectorConstructionCfg, DetectorFlags

# 1. Instantiate fast parametric calorimeter (GALTIC):
det_galtic = DetectorConstructionCfg("ATLAS", version="GALTIC")
det_galtic.compile()

# 2. Instantiate full high-fidelity ATLAS detector:
det_atlas = DetectorConstructionCfg("ATLAS", version="ATLAS")

# 3. Dynamic selection via global flag:
DetectorFlags.Version = "GALTIC"  # or "ATLAS"
det = DetectorConstructionCfg("ATLAS")
```

### Direct Package Usage

```python
# GALTIC (Parametric):
from GALTIC import GalticDetectorConstruction, CaloSamplingLayer, Plates
det = GalticDetectorConstruction("MyGaltic")

# ATLAS (High-Fidelity):
from ATLAS import AtlasDetectorConstruction, AtlasGeometryFlags
from ATLAS.detectors import AtlasEmb, AtlasTile, AtlasEmec, AtlasHec
det = AtlasDetectorConstruction("MyAtlas")
```

---

## Command-Line Transforms

```bash
# Simulation with GALTIC:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector galtic -nt 4

# Simulation with ATLAS Run 4:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector atlas -nt 4

# Digitization with GALTIC:
digit_trf.py -i output.HIT.root -o output.ESD.root --detector galtic

# Digitization with ATLAS:
digit_trf.py -i output.HIT.root -o output.ESD.root --detector atlas

# Interactive 3D Web Visualizer:
visualizer_trf.py --geometry geometry/GALTIC/data/galtic_geometry.json --port 8080
```

---

## Subsystem Documentation

- [GALTIC Documentation](GALTIC/README.md): Parametric calorimeter design, direct C++ JSON parsing, and layer specifications.
- [ATLAS Documentation](ATLAS/README.md): ATLAS Run 4 geometry, GeoModel SQLite import, and frozen showers.
- [Visualizer Documentation](visualizer/README.md): Interactive WebGL 3D viewer, CAD extraction, and vector PDF drawings.
- [Flags Reference Guide](../doc/flags.md): Complete steering flags manual for `AtlasGeometryFlags` and `DetectorFlags`.
