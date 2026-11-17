# MagFieldElements: Magnetic Field Mesh, Caching & Map Interpolators

`MagFieldElements` is the core mathematical and spatial data structures package of the **Lorenzetti** magnetic field subsystem. It ports the high-performance field map reader and interpolation engine from the ATLAS experiment at CERN (`MagneticField/MagFieldElements` in Athena release 23.0.14).

This package is **completely independent of Geant4**, relying strictly on standard C++, ROOT (for field map I/O), and `GaugiKernel` (for SIMD vectorization and trigonometric acceleration).

---

## 1. Physical Model & Data Structures

The ATLAS magnetic field consists of a central solenoid and outer barrel/end-cap toroids. `MagFieldElements` represents these spatial fields using discrete meshes and zone decomposition:

- **Zone Decomposition (`BFieldZone`)**: Partitions space into volumes containing uniform or mesh-interpolated field regions.
- **2D Cylindrical Mesh (`BFieldMeshZR`)**: Represents azimuthally symmetric regions (such as the solenoid inner tracking cavity) on a $(z, r)$ grid, using look-up tables (LUT) for $O(1)$ grid cell location.
- **3D Toroidal Mesh (`BFieldMesh`)**: Represents the asymmetric toroidal field on a $(z, r, \phi)$ grid.
- **Biot-Savart Conductors (`BFieldCond`)**: Evaluates conductor current contributions to adjust field values when magnet currents deviate from map nominals.
- **Thread-Local Caching (`AtlasFieldCache`, `BFieldCache`, `BFieldCacheZR`)**: Eliminates lock contention in multithreaded simulation by providing per-thread caching of the active cell coordinates, derivatives, and SIMD interpolation weights.

---

## 2. Package Structure

```text
magfield/MagFieldElements/
├── CMakeLists.txt          # Builds MagFieldElements OBJECT library
├── README.md               # This specification file
├── MagFieldElements/       # Public C++ headers and inline .icc templates
│   ├── AtlasFieldCache.h
│   ├── AtlasFieldCache.icc
│   ├── AtlasFieldMap.h
│   ├── AtlasFieldMap.icc
│   ├── BFieldCache.h
│   ├── BFieldCache.icc
│   ├── BFieldCacheZR.h
│   ├── BFieldCacheZR.icc
│   ├── BFieldCond.h
│   ├── BFieldCond.icc
│   ├── BFieldMesh.h
│   ├── BFieldMesh.icc
│   ├── BFieldMeshZR.h
│   ├── BFieldMeshZR.icc
│   ├── BFieldVector.h
│   ├── BFieldVectorZR.h
│   └── BFieldZone.h
│   └── BFieldZone.icc
└── src/                    # C++ Implementations
    ├── AtlasFieldCache.cxx
    ├── AtlasFieldMap.cxx
    ├── BFieldCache.cxx
    ├── BFieldCacheZR.cxx
    └── BFieldMeshZR.cxx
```

---

## 3. Build & Integration

- **CMake Target**: `MagFieldElements` (OBJECT library).
- **Dependencies**: ROOT (`RIO`, `Tree`), `GaugiKernel`.
- **Include Path**: `#include "MagFieldElements/<HeaderName>.h"`

---

## 4. C++ API Usage

```cpp
#include "MagFieldElements/AtlasFieldMap.h"
#include "MagFieldElements/AtlasFieldCache.h"
#include "TFile.h"

// 1. Open ROOT field map file
TFile *rootFile = TFile::Open("bfieldmap_7730_20400_14m.root", "READ");

// 2. Initialize the immutable, thread-safe field map
MagField::AtlasFieldMap fieldMap;
fieldMap.initializeMap(rootFile, 7730.0 /*solenoid current A*/, 20400.0 /*toroid current A*/);

// 3. Create a thread-local field cache
MagField::AtlasFieldCache cache;
fieldMap.initializeCache(cache);

// 4. Query field at point (x, y, z) in mm
double xyz[3] = {0.0, 500.0, 1000.0};
double bxyz[3]; // Output in kT (Gaudi/Athena units: 1 kT = 1000 T)
cache.getField(xyz, bxyz);
```
