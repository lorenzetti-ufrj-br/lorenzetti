# MagField: Geant4 Magnetic Field Integration & Steering

`MagField` provides the Geant4 simulation interface, equation-of-motion steppers, field managers, and Python job steering flags for the **Lorenzetti** framework. It bridges the mathematical field models of **`MagFieldElements`** into Geant4's particle tracking kernel.

---

## 1. Features & Components

1. **`AtlasMagneticField` (implements `G4MagneticField`)**:
   - Thread-safe Geant4 field adapter.
   - Worker threads share an immutable `MagField::AtlasFieldMap` instance while maintaining private `MagField::AtlasFieldCache` instances via thread-local storage (`G4ThreadLocal`).
   - Converts coordinates between Geant4 units (mm) and internal field map representations.

2. **`G4AtlasRK4` (Equation-of-Motion Stepper)**:
   - Optimized 4th-order Runge-Kutta numerical integration stepper ported from the ATLAS Geant4 production codebase (`Sim.G4Stepper`).

3. **`SwitchingFieldManager`**:
   - Selectively applies magnetic field computation based on particle species (e.g. evaluating full field for muons while suppressing field calculations in dense calorimeter absorber volumes for neutral or soft shower tracks), reducing simulation CPU overhead.

4. **`TightMuonSteppingFieldManager`**:
   - Enforces tighter chord miss distance (`deltaChord`) and step precision bounds for high-momentum muons traversing the detector envelopes.

5. **`MagFieldFlags` (Python Steering)**:
   - Dataclass inheriting from `JobFlags` controlling magnetic field activation across simulation transforms:
     - `EnableField: bool = False` (full ATLAS 2D/3D field map)
     - `EnableSolenoidOnly: bool = False` (restricted 2 T uniform axial field in solenoid volume)

---

## 2. Package Structure

```text
magfield/MagField/
├── CMakeLists.txt              # Builds MagField OBJECT library and installs python module
├── README.md                   # This specification file
├── MagField/                   # Public C++ headers
│   ├── AtlasMagneticField.h    # G4MagneticField implementation
│   ├── G4AtlasRK4.h            # ATLAS 4th-order Runge-Kutta stepper
│   ├── SwitchingFieldManager.h # Particle-dependent field manager
│   └── TightMuonSteppingFieldManager.h # High-precision muon field manager
├── src/                        # C++ Implementations
│   ├── AtlasMagneticField.cxx
│   ├── G4AtlasRK4.cxx
│   ├── SwitchingFieldManager.cxx
│   └── TightMuonSteppingFieldManager.cxx
└── python/                     # Python module 'magfield'
    ├── __init__.py             # Exports MagFieldFlags
    └── MagFieldFlags.py        # Typed @dataclass steering flags
```

---

## 3. Build & Integration

- **CMake Target**: `MagField` (OBJECT library).
- **Dependencies**: `MagFieldElements`, Geant4, ROOT, `GaugiKernel`.
- **Python Module**: Installed as `magfield` (`from magfield import MagFieldFlags`).

---

## 4. Usage Examples

### C++ Geant4 Integration

```cpp
#include "MagField/AtlasMagneticField.h"
#include "MagField/G4AtlasRK4.h"
#include "MagField/TightMuonSteppingFieldManager.h"
#include "G4Mag_UsualEqRhs.hh"
#include "G4IntegrationDriver.hh"
#include "G4ChordFinder.hh"

// 1. Load field map via static helper
auto fieldMap = AtlasMagneticField::loadMap(mapPath, 7730.0 /*solenoid A*/, 20400.0 /*toroid A*/);

// 2. Instantiate thread-local Geant4 field
auto *field = new AtlasMagneticField(fieldMap.get(), 1.0 /*scaleSol*/, 1.0 /*scaleTor*/);

// 3. Setup equation of motion, stepper, and chord finder
auto *equation = new G4Mag_UsualEqRhs(field);
auto *stepper = new G4AtlasRK4(equation);
auto *driver = new G4IntegrationDriver<G4AtlasRK4>(0.01 * CLHEP::mm, stepper, stepper->GetNumberOfVariables());
auto *chordFinder = new G4ChordFinder(driver);

// 4. Attach to field manager
auto *fieldMgr = new TightMuonSteppingFieldManager(field, chordFinder, true);
```

### Python Steering

```python
from magfield import MagFieldFlags

# Enable uniform solenoid field (2 T)
MagFieldFlags.EnableSolenoidOnly = True

# Or enable full tabulated ATLAS field map
MagFieldFlags.EnableField = True
```

In CLI transforms:
```bash
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 \
  --pre-init "from magfield import MagFieldFlags; MagFieldFlags.EnableField = True"
```
