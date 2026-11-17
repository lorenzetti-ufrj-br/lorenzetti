[![DOI](https://zenodo.org/badge/370090835.svg)](https://zenodo.org/badge/latestdoi/370090835)
[![pages](https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/pages.yml/badge.svg)](https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/pages.yml)
[![reco](https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/reco_sequence.yml/badge.svg)](https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/reco_sequence.yml)
[![anomaly](https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/anomaly_sequence.yml/badge.svg)](https://github.com/lorenzetti-ufrj-br/lorenzetti/actions/workflows/anomaly_sequence.yml)

# 🔬 Lorenzetti Framework

**Lorenzetti** is a modular High Energy Physics (HEP) simulation, digitization, and reconstruction framework designed for fast research and development in calorimeter signal processing, trigger algorithms, and machine learning applications.

Built upon **Geant4**, **Pythia8**, and **ROOT**, Lorenzetti models the complete calorimeter readout chain:
- **Primary particle generation** and kinematic filtering.
- **Geant4 shower evolution** in high-granularity detector media (Classical or ATLAS Run 4 geometry).
- **Electronic pulse shaping** across bunch crossings and pileup overlay.
- **Signal reconstruction** via Optimal Filtering (OF/COF).
- **Topological clustering** and concentric shower ring extraction (Ringer).
- **Direct Parquet serialization** for seamless PyTorch and Pandas ML training pipelines.

---

## 🚀 Quick Start (Installation)

The recommended way to run Lorenzetti is via pre-built Singularity / Apptainer or Docker containers containing all HEP dependencies (ROOT, Geant4, Pythia8, HepMC3, FastJet).

### 1. Singularity / Apptainer (Recommended for HPC)

```bash
# Pull container image
singularity pull docker://lorenzetti/lorenzetti:latest

# Enter container shell
singularity shell lorenzetti_latest.sif
```

### 2. Docker

```bash
docker run -it --rm \
  -v "$PWD:/workspace" \
  -w /workspace \
  lorenzetti/lorenzetti:latest
```

> 💡 **Apple Silicon (macOS):** Use [OrbStack](https://orbstack.dev/) with Rosetta 2 emulation enabled, and pass `--platform linux/amd64` to `docker run`.

### 3. Build & Setup Environment

Inside the container shell:

```bash
git clone https://github.com/lorenzetti-ufrj-br/lorenzetti.git
cd lorenzetti
make
source build/lzt_setup.sh
```

*(Optional)* To enable full ATLAS Run 4 GeoModel support:
```bash
bash geometry/GeoV2/scripts/build_geomodel.sh ~/geomodel
export GEOMODEL_DIR=~/geomodel
make
source build/lzt_setup.sh
```

---

## 💻 Basic Commands

### ⚡ Complete End-to-End Pipeline
Run the fully automated simulation, pileup overlay, digitization, reconstruction, and Parquet export pipeline with a single command:

```bash
python3 examples/run_reco_sequence.py
```

### 🔄 Step-by-Step CLI Transforms

The framework provides clean, declarative command-line interfaces for every stage of the HEP pipeline:

#### 1. Geant4 Simulation (`simu_trf.py`)
Simulates energy depositions in calorimeter media:
```bash
# Classical cylindrical geometry (v1):
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v1 -nt 4

# High-fidelity ATLAS Run 4 geometry (v2):
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 -nt 4
```

#### 2. Digitization & Electronics (`digit_trf.py`)
Applies pulse shaping, electronic noise, and optional pileup overlay:
```bash
digit_trf.py -i output.HIT.root -o output.ESD.root --detector v2
```

#### 3. Calorimeter Reconstruction (`reco_trf.py`)
Performs optimal filtering, topological clustering, and Ringer concentric feature extraction:
```bash
reco_trf.py -i output.ESD.root -o output.AOD.root
```

#### 4. Direct Parquet ML Export (`parquet_trf.py`)
Converts ROOT reconstruction tiers directly into Apache Parquet format for PyTorch / TensorFlow / Pandas:
```bash
parquet_trf.py -i output.AOD.root -o output.parquet
```

---

## 🛠️ Advanced Commands

### ⏩ High-Throughput Parallel Execution (`-nw`)
Scale execution across multiple CPU cores using built-in multiprocessing workers (`-nw`) with automatic chunking and event merging:

```bash
# Run simulation across 8 worker processes with 2 threads each:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 -nw 8 -nt 2

# Limit total number of events processed:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 --nov 5000
```

### 🎛️ Dynamic Steering via Python Overrides (`--pre-init`)
Steer any typed dataclass flag ([doc/flags.md](doc/flags.md)) directly from the command line without modifying files:

```bash
# Disable specific subdetectors and tune neutron time cuts in simulation:
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 \
  --pre-init "from GeoV2 import AtlasGeometryFlags as Geo; from CaloHitBuilder import CaloHitFlags; Geo.AtlasEmb = False; CaloHitFlags.NeutronTimeCut = 200.0"

# Enable electronic cross-talk, defect masking, and disable noise in digitization:
digit_trf.py -i input.HIT.root -o output.ESD.root --detector v2 \
  --pre-init "from CaloCellBuilder import CaloFlags; CaloFlags.DoCrossTalk = True; CaloFlags.ElectronicNoise = False"
```

### 📄 Batch Job Profiles via JSON (`--job-file`)
Persist and share reproducible execution configurations using JSON steering profiles:

```bash
simu_trf.py -i input.EVT.root -o output.HIT.root --job-file job_config.json
```

*Example `job_config.json`:*
```json
{
  "DetectorFlags": { "Version": "v2" },
  "AtlasGeometryFlags": { "AtlasEmb": true, "TileAtlasRun4": true },
  "CaloHitFlags": { "BirksLaw": true, "NeutronTimeCut": 150.0 }
}
```

### ⏱️ Free-Running ATLAS HITS Generation
Write calorimeter hits formatted identically to official ATLAS Athena simulation (`CollectionTree` ntuple layout and ported EMEC charge collection):

```bash
simu_trf.py -i input.EVT.root -o output.HITS.root --detector v2 \
  --free-running-hits --free-running-atlas-format
```

### 🎨 Interactive 3D Visualization
Inspect calorimeter geometries, volumes, and particle tracks using Geant4 OpenGL / Qt drivers:

```bash
python3 geometry/GeoV1/scripts/run_vis.py
```

---

## 📦 Architecture & Packages

```
lorenzetti/
├── kernel/                  # GaugiKernel (event loop, StoreGate, JobFlags), G4Kernel, GenKernel
├── geometry/                # Modular Geometry Subsystem
│   ├── GeoBase/             # Shared primitives, pulse data & DetectorConstructionCfg factory
│   ├── GeoV1/               # Classical 4π cylindrical calorimeter model
│   └── GeoV2/               # High-fidelity ATLAS Run 4 geometry (GeoModel SQLite, FCal)
├── magfield/                # Magnetic field subsystem (MagField, MagFieldElements)
├── events/                  # Relational EDM (CaloHit, CaloCell, CaloCluster, CaloRings, Egamma)
├── reconstruction/          # Digitization, clustering, Ringer extraction & CLI transforms
├── generator/               # Primary event generation (Pythia8, minbias, kinematic filters)
└── examples/                # End-to-end execution scripts and workflows
```

---

## 📚 Documentation & References

- **[CHANGE_NOTES.md](CHANGE_NOTES.md)**: Comprehensive architectural guide and detailed changelog.
- **[doc/flags.md](doc/flags.md)**: Complete reference manual for all `@dataclass` configuration flags.
- **[geometry/README.md](geometry/README.md)**: Detailed geometry architecture (`GeoBase`, `GeoV1`, `GeoV2`).
- **[geometry/GeoV1/README.md](geometry/GeoV1/README.md)**: Classical calorimeter design and ray-traced figures.
- **[geometry/GeoV2/README.md](geometry/GeoV2/README.md)**: ATLAS Run 4 geometry, GeoModel, and frozen showers.
- **[magfield/README.md](magfield/README.md)**: Tabulated magnetic field service and steppers.

---

## 📝 Citation

If you use Lorenzetti in your research, please cite:

> **Lorenzetti Showers: A general-purpose framework for supporting signal reconstruction and triggering with calorimeters**  
> *Computer Physics Communications*, Volume 286, 2023, 108671.  
> DOI: [10.1016/j.cpc.2023.108671](https://doi.org/10.1016/j.cpc.2023.108671)

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](LICENSE) file for details.
