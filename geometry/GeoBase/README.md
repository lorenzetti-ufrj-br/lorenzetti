# GeoBase: Shared Geometry Primitives & Unified Factory

`GeoBase` is the foundational package of the **Lorenzetti** geometry subsystem. It provides the core Geant4 Python primitives, shared calorimeter helper classes, pulse shape calibration data, and the centralized factory engine **`DetectorConstructionCfg`** used by simulation and digitization transforms.

---

## 1. Role in the Geometry Architecture

In the Lorenzetti framework, detector versions (`GeoV1` and `GeoV2`) share identical volume construction principles, sensitive detector bindings, and electronics pulse shapes. `GeoBase` acts as the single source of truth, eliminating code duplication and decoupling the user-facing job transforms from specific detector implementations:

```
                  ┌──────────────────────────────────────────────┐
                  │                 Transforms                   │
                  │        (simu_trf.py, digit_trf.py)           │
                  └──────────────────────┬───────────────────────┘
                                         │ calls
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │          DetectorConstructionCfg             │
                  │       (geometry/GeoBase/python)              │
                  └──────────────┬────────────────┬──────────────┘
                                 │                │
            loads if "v1"        │                │ loads if "v2"
                                 ▼                ▼
                     ┌────────────────┐      ┌────────────────┐
                     │     GeoV1      │      │     GeoV2      │
                     │  (Classical)   │      │ (ATLAS Run 4)  │
                     └───────┬────────┘      └────────┬───────┘
                             │                        │
                             │  imports primitives    │
                             └───────────┬────────────┘
                                         ▼
                             ┌────────────────────────┐
                             │        GeoBase         │
                             │  PhysicalVolume        │
                             │  SensitiveDetector     │
                             │  Calorimeter, Tracking │
                             │  pulseLar / pulseTile  │
                             └────────────────────────┘
```

---

## 2. Package Structure

```text
geometry/GeoBase/
├── CMakeLists.txt              # Installs Python module GeoBase and shared data
├── README.md                   # This documentation
├── data/                       # Shared detector pulse shape data
│   ├── pulseLar.dat            # LAr triangular/exponential pulse response
│   └── pulseTile.dat           # Tile plastic scintillator bi-exponential response
├── python/                     # GeoBase Python module
│   ├── __init__.py             # Exports factory, flags, and primitives
│   ├── DetectorConstructionCfg.py  # Unified factory function
│   ├── DetectorFlags.py        # Dataclass job steering flags for detector version
│   ├── PhysicalVolume.py       # Geant4 LogicalVolume and PhysicalVolume wrappers
│   ├── SensitiveDetector.py    # Sensitive detector builder & LAr phi shift
│   ├── Calorimeter.py          # Calorimeter sampling layers & envelope helpers
│   └── Tracking.py             # Inner tracking and beam pipe envelopes
└── tests/                      # Unit test suite
    └── test_detector_construction_cfg.py  # 7 unit tests (flags, factory, fallback)
```

---

## 3. Key Components

### `DetectorFlags`
A typed `@dataclass(init=False)` inheriting from `JobFlags` that steers the detector version across all jobs:
```python
from GeoBase import DetectorFlags

# Inspect or configure default version
print(DetectorFlags.Version)  # Default: "v2"
DetectorFlags.Version = "v1"  # Steer to Classical geometry
```

### `DetectorConstructionCfg`
The unified factory function that encapsulates all detector instantiation logic:
```python
from GeoBase import DetectorConstructionCfg

# Automatic instantiation (uses DetectorFlags.Version by default):
det = DetectorConstructionCfg("ATLAS")

# Explicit version specification:
det_v1 = DetectorConstructionCfg("ATLAS", version="v1")
det_v2 = DetectorConstructionCfg("ATLAS", version="v2")

# Custom overrides via keyword arguments:
det_custom = DetectorConstructionCfg("ATLAS", version="v1", UseMagneticField=True)
```

**Factory Behavior:**
1. Dynamically resolves the target version (`v1` or `v2`).
2. Applies appropriate subsystem defaults (e.g. `MagFieldFlags.apply_defaults()`, `AtlasGeometryFlags.apply_defaults(is_v2=True)`).
3. Lazily imports `DetectorConstruction_v1` from `GeoV1` or `DetectorConstruction_v2` from `GeoV2`.
4. Merges explicit `kwargs` and instantiates the detector object.

### Primitives (`PhysicalVolume.py` & `SensitiveDetector.py`)
- **`PhysicalVolume`**: Clean, Pythonic abstraction over Geant4 solid, logical volume, and physical placement hierarchies. Supports standard boxes, tubes, polycones, parameterized placements, and material associations.
- **`SensitiveDetector`**: Handles sensitive volume registration, energy deposit collection, cell assignment, and coordinate transformations (`atlasLArPhiShift`).
- **`get_data_dir()`**: Utility function that returns the absolute path to the shared pulse calibration data directory (`geometry/GeoBase/data/`).

---

## 4. Unit Testing

The package includes a comprehensive test suite that runs without requiring a full ROOT or Geant4 installation:

```bash
python3 geometry/GeoBase/tests/test_detector_construction_cfg.py
```
