# Change Notes: `python_refactory` vs `master`

This document details the major architectural enhancements, modernization efforts, and refactoring implemented in the `python_refactory` branch compared to the `master` branch of the Lorenzetti framework.

---

## Table of Contents

1. [Architectural Overview & Repository Restructuring](#1-architectural-overview--repository-restructuring)
2. [ElementLink & Relational Event Data Model (EDM)](#2-elementlink--relational-event-data-model-edm)
3. [2-Sigma Calorimeter Cell Filtering & Noise Suppression](#3-2-sigma-calorimeter-cell-filtering--noise-suppression)
4. [Stream Architecture Generalization & Automated Branch Discovery](#4-stream-architecture-generalization--automated-branch-discovery)
5. [High-Throughput Parallelism Framework (`ParallelJob` & `FileParallelJob`)](#5-high-throughput-parallelism-framework-paralleljob--fileparalleljob)
6. [CLI Interface Modernization & Declarative Transform Scripts](#6-cli-interface-modernization--declarative-transform-scripts)
7. [Python-C++ Integration: `Configurable` & `ComponentAccumulator`](#7-python-c-integration-configurable--componentaccumulator)
8. [Direct Parquet Pipeline & Columnar Serialization (`RootStreamParquetMaker` & `parquet_trf.py`)](#8-direct-parquet-pipeline--columnar-serialization-rootstreamparquetmaker--parquet_trfpy)
9. [Active Persistence Registry & Stream Auto-Configuration (`recordable()`)](#9-active-persistence-registry--stream-auto-configuration-recordable)
10. [Declarative Output Schema & Streamlined Reconstruction Stack](#10-declarative-output-schema--streamlined-reconstruction-stack)
11. [Component Modernization: `Gaugi::Tool`, Pileup Migration & `CaloCellBuilder` Electronics](#11-component-modernization-gaugitool-pileup-migration--calocellbuilder-electronics)
12. [End-to-End Simulation & Reconstruction Pipeline (`examples/run_reco_sequence.py`)](#12-end-to-end-simulation--reconstruction-pipeline-examplesrun_reco_sequencepy)
13. [ATLAS Run 4 High-Fidelity Geometry & Detector Construction v2 (PR #18)](#13-atlas-run-4-high-fidelity-geometry--detector-construction-v2-pr-18)
14. [Free-Running Calorimeter Hits & Athena EMEC Charge Collection (PR #19)](#14-free-running-calorimeter-hits--athena-emec-charge-collection-pr-19)
15. [Event Generation, Physics Modeling & Core Geometry Bug Fixes (PR #15, PR #16, PR #20)](#15-event-generation-physics-modeling--core-geometry-bug-fixes-pr-15-pr-16-pr-20)
16. [Unified Dataclass Job Steering System (`JobFlags`) & CLI Decoupling](#16-unified-dataclass-job-steering-system-jobflags--cli-decoupling)
17. [Decoupled 3-Package Geometry Architecture & Unified Factory (`GeoBase`, `GeoV1`, `GeoV2`)](#17-decoupled-3-package-geometry-architecture--unified-factory-geobase-geov1-geov2)

---

## 1. Architectural Overview & Repository Restructuring

### Context & Motivation
In `master`, core infrastructure was bundled under `core/` (`GaugiKernel`, `G4Kernel`, `GenKernel`) with legacy monolithic scripts, disparate testing setups, and tightly coupled algorithms.

The refactored branch introduces:
- Renaming and organization from `core/` to `kernel/` (`GaugiKernel`, `G4Kernel`, `GenKernel`).
- Comprehensive unit tests across all EDM packages (`events/*/tests`) and kernels (`kernel/GaugiKernel/tests`).
- Centralized CI automation (`.github/workflows/ci.yml`).
- Decoupling of analysis and reconstruction algorithms from data transport layers.

---

## 2. ElementLink & Relational Event Data Model (EDM)

### What was in `master`
In the original version, associations between EDM classes were implemented using raw C++ pointers:
```cpp
// master: events/Egamma/Egamma/Electron.h
class Electron : public Gaugi::EDM {
public:
  void setCaloCluster(const xAOD::CaloCluster *clus) { m_caloCluster = clus; }
  const xAOD::CaloCluster* caloCluster() const { return m_caloCluster; }
private:
  const xAOD::CaloCluster *m_caloCluster; // Raw C++ pointer!
};
```
```cpp
// master: events/CaloCluster/CaloCluster/CaloCluster.h
class CaloCluster : public Gaugi::EDM {
private:
  std::vector<const xAOD::CaloCell*> m_container; // Raw pointers to cells
  const xAOD::Seed* m_seed;                       // Raw pointer to seed
};
```

### Problems with the Original Approach
1. **Serialization Impossibility:** Raw pointers cannot be safely serialized to separate TTree branches or persistent files without deep copying.
2. **Dangling Pointers & Memory Corruption:** Reading an object from disk in a subsequent job led to null or invalid pointer addresses pointing to stale memory.
3. **No Independent Container I/O:** Reading only electrons without loading the full cluster container in the exact same memory layout would trigger segmentation faults.

### The Refactored Solution: `SG::ElementLink<TargetT>`
Introduced a templated `SG::ElementLink<TargetT>` in `kernel/GaugiKernel/GaugiKernel/ElementLink.h`. It stores the target container's identifier (string key and 64-bit FNV-1a hash) and the target element's index (`m_index`), with transient pointer caching and on-demand lazy resolution via `EventContext`.

```cpp
// python_refactory: events/Egamma/Egamma/Electron.h
#include "GaugiKernel/ElementLink.h"

class Electron : public Gaugi::EDM {
public:
  void setCaloCluster(const xAOD::CaloCluster *clus);
  void setCaloCluster(const std::string& key, uint32_t index, const xAOD::CaloCluster* clus = nullptr);
  void setCaloCluster(const SG::ElementLink<xAOD::CaloCluster>& link);

  const xAOD::CaloCluster* caloCluster() const;
  const SG::ElementLink<xAOD::CaloCluster>& caloClusterLink() const { return m_caloCluster; }

private:
  SG::ElementLink<xAOD::CaloCluster> m_caloCluster; // Persistent relational link
};
```

```cpp
// python_refactory: kernel/GaugiKernel/GaugiKernel/ElementLink.icc
template <typename TargetT>
void ElementLink<TargetT>::resolve() const {
  if (m_cachedPtr || (m_targetKey.empty() && m_keyHash == 0)) {
    m_isResolved = true;
    return;
  }
  if (!m_owner || !m_owner->container() || !m_owner->container()->getContext()) {
    m_cachedPtr = nullptr;
    m_isResolved = true;
    return;
  }

  auto* ctx = m_owner->container()->getContext();
  const SG::DataVector<TargetT>* targetVector = nullptr;
  if (!m_targetKey.empty()) targetVector = ctx->get<SG::DataVector<TargetT>>(m_targetKey);
  if (!targetVector && m_keyHash != 0) targetVector = ctx->get<SG::DataVector<TargetT>>(m_keyHash);

  if (targetVector && m_index < targetVector->size()) {
    m_cachedPtr = targetVector->at(m_index);
  } else {
    m_cachedPtr = nullptr;
  }
  m_isResolved = true;
}
```

### Improvements
- **Safe Persistence:** Objects store key hashes and indices, allowing independent branch storage and serialization in ROOT.
- **Lazy Resolution:** Target objects are looked up in `EventContext` only when accessed, with cached pointer speed on repeat queries.
- **Zero Dangling Pointers:** Decoupled object lifecycles across containers and reconstruction stages.

---

## 3. 2-Sigma Calorimeter Cell Filtering & Noise Suppression

### What was in `master`
In `master`, `CaloCellMerge` iterated over all detector descriptors and pushed every single cell into truth and reconstructed containers, leading to millions of pure noise / zero-energy cells being saved.

Earlier refactoring iterations attempted an artificial 1-to-1 match constraint between real and truth cells, alongside ad-hoc parameters (`filter_empty_cells`, `min_energy`).

```cpp
// master: reconstruction/calorimeter/CaloCellBuilder/src/CaloCellMerge.cxx
for (const auto &pair : **collection.ptr()) {
  const xAOD::CaloDetDescriptor* descriptor = pair.second;

  // Unconditionally instantiated both truth and reco cells for every channel
  auto truth_cell = new xAOD::CaloCell();
  truth_cell->setE(descriptor->edep());
  truthContainer->push_back(truth_cell);

  auto cell = new xAOD::CaloCell();
  cell->setE(descriptor->e());
  recoContainer->push_back(cell);
}
```

### The Refactored Solution
1. **Independent 2-Sigma Noise Cut:** Removed the coupling/match constraint between real and truth cells. Each cell (truth or reconstructed) is retained if its energy exceeds $2\sigma$ of electronic noise:
   $$\text{threshold} = \text{m\_sigmaThreshold} \times \sigma_{\text{noise}}$$
2. **Normalized Master Descriptors:** Calo detector descriptors are stored once in a master `CaloDetDescriptorContainer`, and cells link to them via `ElementLink`.
3. **Modular Offline Noise Suppression:** Rather than embedding cell filtering inside I/O deserializers (`CaloCellBranchHandler`), `RootStreamReader` uses `GenericBranchHandler` for all containers. A dedicated algorithm, `CaloCellNoiseSuppression` in `CaloCellBuilder`, applies the $E > \text{threshold} \times \sigma$ cut in the reconstruction sequence (`reco_trf.py`), writing to `Cells` while keeping `RootStreamReader` 100% generic.

```cpp
// python_refactory: reconstruction/calorimeter/CaloCellBuilder/src/CaloCellMerge.cxx
for (const auto &pair : **collection.ptr()) {
  const xAOD::CaloDetDescriptor *const_descriptor = pair.second;
  if (!const_descriptor) continue;

  float reco_e = const_descriptor->e();
  float truth_e = const_descriptor->edep();

  bool pass_reco = false;
  bool pass_truth = false;

  if (m_filterBySigma) {
    float sigma = const_descriptor->sigma();
    float threshold = (sigma > 0.0f) ? (m_sigmaThreshold * sigma) : 0.0f;
    pass_reco = (reco_e > threshold);
    pass_truth = (truth_e > threshold);
  } else {
    pass_reco = true;
    pass_truth = true;
  }

  if (!pass_reco && !pass_truth) continue;

  // Clone descriptor into master container owned by DataVector
  auto descriptor = new xAOD::CaloDetDescriptor(*const_descriptor);
  uint32_t desc_index = static_cast<uint32_t>(descContainer->size());
  descContainer->push_back(descriptor);

  if (pass_truth) {
    auto truth_cell = new xAOD::CaloCell();
    truth_cell->setE(truth_e);
    truth_cell->setDescriptor(m_descriptorsKey, desc_index, descriptor);
    truthContainer->push_back(truth_cell);
  }

  if (pass_reco) {
    auto cell = new xAOD::CaloCell();
    cell->setE(reco_e);
    cell->setDescriptor(m_descriptorsKey, desc_index, descriptor);
    recoContainer->push_back(cell);
  }
}
```

### Improvements
- **Storage & I/O Reduction:** Drastically shrinks ESD file sizes (often by >80%) by discarding electronic noise below $2\sigma$.
- **Physics Accuracy:** Follows ATLAS standard noise thresholds without artificially dropping truth energy when reco fluctuates down, or vice versa.
- **Elimination of Stale Parameters:** Replaced ambiguous `filter_empty_cells` and `min_energy` flags with physically motivated `filter_by_sigma` and `sigma_threshold`.

---

## 4. Stream Architecture Generalization & Automated Branch Discovery

### What was in `master`
The I/O subsystem in `master` used duplicated, hardcoded classes for each data tier:
- `RootStreamHITMaker`, `RootStreamHITReader`
- `RootStreamESDMaker`, `RootStreamESDReader`
- `RootStreamAODMaker`, `RootStreamAODReader`

Each class repeated hundreds of lines of boilerplate registering specific branch names (`Hits`, `Cells`, `Clusters`, `Electrons`). Adding a new EDM container required editing multiple C++ readers/makers and modifying dictionary bindings.

### The Refactored Solution: `RootStreamMaker`, `RootStreamReader` & `BranchHandlerFactory`
1. **100% Generic Branch Handlers:** All 9 persistent EDM containers are handled uniformly via `GenericBranchHandler<Container, PODStruct, Converter>`, eliminating specialized handlers (`CaloHitBranchHandler` and `CaloCellBranchHandler` were completely removed).
2. **Simplified Factory Design:** `BranchHandlerFactory::createHandler(rawTypeName, key, branchName)` maps container type names to their type-safe `GenericBranchHandler` instance, optionally passing an override `branchName` when input branches diverge from output keys.
3. **Automated Branch Discovery:** `RootStreamReader::discoverBranches()` parses the `CollectionTree` branches matching `<TypeName>_<Key>` and automatically configures handlers without any hardcoded branch lists or container-specific logic.
4. **Separation of Concerns:**
   - **RoI Hit Filtering**: Moved upstream to `CaloHitBuilder` (`CaloHitMerge`), keeping `RootStreamHITMaker` and `RootStreamBuilder` decoupled from `G4Kernel` geometry and truth particles.
   - **Noise Suppression**: Moved to `CaloCellNoiseSuppression` in `CaloCellBuilder`, keeping `RootStreamESDReader` generic and allowing offline reconstruction (`reco_trf.py`) to generate filtered and unfiltered datasets from the same complete ESD.
5. **StoreGate Root-Directory Fix:** Resolved an issue where `simu_trf.py` missed the `CollectionTree` by ensuring `RootStreamMaker::bookHistograms()` hooks into `StoreGate::file()` and registers `m_tree` directly in the root `/` directory.
6. **Decoupled Execution Lifecycle (Stateless `initialize()`):**
   - Refactored `RootStreamMaker` so that `initialize()` does not instantiate branch handlers or perform filesystem operations.
   - Handlers are dynamically constructed on-demand within `bookHistograms()` and `fillHistograms()`, preventing invalid thread states, dangling pointers, and premature file locks.
   - Explicit `store->cd()` guarantees that the primary `CollectionTree` resides cleanly at the root of the output `TFile`, eliminating directory duplication inside `Events/`.
7. **Flat Ntuple Pipeline Hardening (`RootStreamNtupleMaker` & `ntuple_trf.py`):**
   - Added automatic key normalization in Python (single strings converted to `list[str]` for `InputRingerKeys` and `InputTruthRingerKeys`).
   - Integrated immediate `return StatusCode::FAILURE;` upon missing mandatory event containers in `fillHistograms()`.
   - Added defensive `tree->ResetBranchAddresses();` at the end of the event loop to eliminate stale stack addresses.

```cpp
// python_refactory: reconstruction/io/RootStreamBuilder/src/RootStreamReader.cxx
StatusCode RootStreamReader::discoverBranches(TTree *tree) {
  TObjArray *branchList = tree->GetListOfBranches();
  for (int i = 0; i < branchList->GetEntries(); ++i) {
    TBranch *branch = dynamic_cast<TBranch*>(branchList->At(i));
    if (!branch) continue;

    std::string bname = branch->GetName();
    size_t sepPos = bname.find('_');
    if (sepPos == std::string::npos) continue;

    std::string typeName = bname.substr(0, sepPos);
    std::string key = bname.substr(sepPos + 1);

    auto handler = BranchHandlerFactory::createHandler(typeName, key, bname);
    if (handler) {
      handler->prepareRead(tree);
      m_handlers.push_back(std::move(handler));
    }
  }
  return StatusCode::SUCCESS;
}
```

```cpp
// python_refactory: reconstruction/io/RootStreamBuilder/src/BranchHandlerFactory.h
class BranchHandlerFactory {
public:
  static std::unique_ptr<IBranchHandler> createHandler(
      const std::string &rawTypeName,
      const std::string &key,
      const std::string &branchName = "")
  {
    std::string typeName = rawTypeName;
    if (typeName.rfind("xAOD::", 0) == 0) typeName = typeName.substr(6);

    if (typeName == "CaloCellContainer") {
      return std::make_unique<GenericBranchHandler<xAOD::CaloCellContainer, xAOD::CaloCell_t, xAOD::CaloCellConverter>>("CaloCellContainer", key, branchName);
    } else if (typeName == "CaloHitContainer") {
      return std::make_unique<GenericBranchHandler<xAOD::CaloHitContainer, xAOD::CaloHit_t, xAOD::CaloHitConverter>>("CaloHitContainer", key, branchName);
    } else if (typeName == "ElectronContainer") {
      return std::make_unique<GenericBranchHandler<xAOD::ElectronContainer, xAOD::Electron_t, xAOD::ElectronConverter>>("ElectronContainer", key, branchName);
    }
    // Generic handlers for all 9 registered EDM containers
    ...
  }
};
```

### Improvements
- **100% Uniform Architecture:** All 9 containers use `GenericBranchHandler`, eliminating container-specific branch handlers and coupling across packages.
- **Extensibility:** Adding new EDM types only requires registering one line in `BranchHandlerFactory`.
- **Elimination of Duplication:** Reduced ~2,500 lines of duplicated C++ code across `RootStream*Maker/Reader`.
- **Self-Describing Files:** Files written by any tier can be read transparently by `RootStreamReader` without hardcoding tier types.
- **Robust Multi-Threading Lifecycle:** Decoupled `initialize()` removes race conditions and ensures clean TFile tree placement.

---

## 5. High-Throughput Parallelism Framework (`ParallelJob` & `FileParallelJob`)

### What was in `master`
In `master`, multi-processing was either done through external shell scripts or rigid loops. Terminology was ambiguous: scripts used `-nt` / `--number-of-threads` to refer interchangeably to subprocesses and Geant4 threads.

### The Refactored Solution: `Parallel.py`
Introduced a comprehensive, decorator-driven parallelism framework in `kernel/GaugiKernel/python/Parallel.py`:

1. **Explicit Workers vs Threads:**
   - `number_of_workers` (`-nw`): Concurrency of separate worker processes executing partitions.
   - `number_of_threads` (`-nt`): Threads per worker process (e.g. Geant4 threads).
2. **Two Complementary Parallel Paradigms:**
   - `@parallel_job`: Event-level parallelization for single file execution. Divides `nov` events into chunks, runs worker subprocesses in parallel, and merges chunk ROOT files with `merge_root_files()`.
   - `@file_parallel_job`: File-level parallelization across input datasets. Maps input directories/files to output destinations, balances worker processes, and handles automatic naming substitutions (e.g. `.EVT.` $\rightarrow$ `.HIT.`).
3. **Execution Plan Visualization:** Uses `rich` to print structured, color-coded execution plans before launching jobs.
4. **Real-Time Output Streaming:** `--show-output` / `-v` streams worker subprocess output directly.
5. **Dry-Run Mode:** `--dry-run` displays command invocations without execution.

```python
# python_refactory: kernel/GaugiKernel/python/Parallel.py
class FileParallelJob(Logger):
    def get_threads_and_concurrency(self, total_files: int) -> Tuple[int, int]:
        if self.threads_per_job > 0:
            tpj = self.threads_per_job
        elif total_files == 1:
            tpj = self.number_of_threads
        elif self.number_of_workers and self.number_of_threads >= self.number_of_workers:
            tpj = max(1, self.number_of_threads // self.number_of_workers)
        else:
            tpj = 1

        concurrency = self.number_of_workers if self.number_of_workers else max(1, self.number_of_threads // tpj)
        return tpj, concurrency
```

### Improvements
- Eliminates CPU oversubscription by cleanly calculating `workers * threads_per_worker <= total_cores`.
- Seamless end-to-end automation: partition, execute, validate, and merge in a single command.

---

## 6. CLI Interface Modernization & Declarative Transform Scripts

### What was in `master`
In `master`, transform scripts (`simu_trf.py`, `digit_trf.py`, `reco_trf.py`, `ntuple_trf.py`) contained over 200–250 lines of boilerplate each:
- Manual `argparse` setups.
- Custom JSON file parsers for `--job-file`.
- Manual directory validation and path conversions.

```python
# master: reconstruction/reco/scripts/simu_trf.py (Excerpt)
def parse_args():
    parser = argparse.ArgumentParser(description="Simulate showers using Geant4...")
    parser.add_argument('-i', '--input-file', dest='input_file', required=True, ...)
    parser.add_argument('-o', '--output-file', dest='output_file', required=True, ...)
    parser.add_argument('-nt', '--number-of-threads', dest='number_of_threads', type=int, default=1, ...)
    parser.add_argument('--job-file', dest='job_file', default=None, ...)
    # ... 40 lines of argparse setup ...
    return merge_args_from_file(parser)

if __name__ == "__main__":
    args = parse_args()
    # ... 60 lines of arg validation and forwarding ...
    main(...)
```

### The Refactored Solution: Typer & Parallel Decorators
Transform scripts are now concise declarative functions wrapped with `@file_parallel_job` or `@parallel_job`.

```python
# python_refactory: reconstruction/reco/scripts/simu_trf.py
from GaugiKernel.Parallel import file_parallel_job
import typer
from typing_extensions import Annotated
from pathlib import Path

@file_parallel_job(ntuple_name="CollectionTree", output_replace=(".EVT.", ".HIT."))
def main(
    input_file: Annotated[str | Path, typer.Option("-i", "--input-file", help="Input EVT file or directory")],
    output_file: Annotated[str | Path, typer.Option("-o", "--output-file", help="Destination HIT file or directory")],
    number_of_threads: Annotated[int, typer.Option("-nt", "--number-of-threads", help="Threads allocated per worker")] = 1,
    output_level: Annotated[str, typer.Option("-l", "--output-level", help="The output level messenger.")] = "INFO",
    enable_magnetic_field: Annotated[bool, typer.Option("--enable-magnetic-field", help="Enable the magnetic field.")] = False,
    save_all_hits: Annotated[bool, typer.Option("--save-all-hits", help="Save all hits into the output file.")] = False,
    timeout: Annotated[int, typer.Option("--timeout", help="Timeout in minutes.")] = 10,
    number_of_events: Annotated[int, typer.Option("--nov", "--number-of-events", help="The total number of events to run.")] = -1,
):
    """Simulates detector showers from generated events using Geant4."""
    acc = ComponentAccumulator(
        "ComponentAccumulator",
        DetectorConstruction_v1("ATLAS", UseMagneticField=enable_magnetic_field),
        NumberOfThreads=number_of_threads,
        OutputFile=str(output_file),
        Timeout=timeout * MINUTES,
    )
    gun = EventReader("EventReader", str(input_file), OutputEventKey=recordable("Events"), ...)
    calorimeter = CaloHitBuilder("CaloHitBuilder", OutputHitsKey=recordable("Hits"), ...)
    gun.merge(acc)
    calorimeter.merge(acc)

    HIT = RootStreamHITMaker("RootStreamHITMaker", OnlyRoI=not save_all_hits, ...)
    acc += HIT
    acc.run(number_of_events)

if __name__ == "__main__":
    main()
```

### Improvements
- **Code Reduction:** Script size decreased from ~250 lines to ~50 lines per transform.
- **Unified CLI Standards:** All scripts automatically feature `--help`, `-h`, `--job-file`, `--dry-run`, `-nw`, `-nt`, `-o`, and `-i`.
- **Built-in Type Checking:** Validated automatically with Python type annotations.

---

## 7. Python-C++ Integration: `Configurable` & `ComponentAccumulator`

### What was in `master`
In `master`, algorithms and tools were bound through a basic `Cpp` wrapper (`core/GaugiKernel/python/Cpp.py`):
```python
# master: Setting properties required explicit setProperty() calls
maker = CaloCellMaker("Maker")
maker.setProperty("CollectionKey", "Cells")
maker.setProperty("OutputLevel", 1)
```
Vector properties (such as tool lists) could not be accumulated natively using Python operators.

### The Refactored Solution: `Configurable` & `PropertyList`
Introduced `Configurable` and `PropertyList` in `kernel/GaugiKernel/python/Configurable.py`:

1. **Keyword Arguments on Instantiation:**
   ```python
   maker = CaloCellMaker("Maker", CollectionKey="Cells", OutputLevel=DEBUG)
   ```
2. **Dynamic Attribute Synchronization:** Modifying an attribute (`maker.CollectionKey = "NewCells"`) invokes `__setattr__`, which converts Python types to C++ STL types and calls `_c_ptr.setProperty()` automatically.
3. **In-Place List Accumulation (`+=`):**
   ```python
   # Intuitively append algorithmic tools to properties
   maker.Tools += [pulsePerturber, optimalFilter]
   ```
4. **Flexible `ComponentAccumulator.run()`:** Updated `run()` to accept either integer counts (`acc.run(100)` or `acc.run(-1)`) or explicit event index lists (`acc.run([0, 1, 2])`).

```python
# python_refactory: kernel/GaugiKernel/python/Configurable.py
class PropertyList(list):
    def __iadd__(self, other):
        if isinstance(other, list):
            self.extend(other)
        else:
            self.append(other)
        self._sync() # Automatically notifies C++ backend
        return self

class Configurable(Logger):
    def __setattr__(self, name, value):
        ...
        self.__dict__[name] = value
        if hasattr(self, '_c_ptr') and self._c_ptr.hasProperty(name):
            self._c_ptr.setProperty(name, treatPropertyValue(value))
```

### Improvements
- Delivers an intuitive, Pythonic syntax matching modern experiment frameworks (such as Athena ComponentAccumulator).
- Automatically converts Python primitives, lists, and nested lists to `std::vector` and `Gaugi::Tool*`.
- Seamless error handling with clear messages if unknown properties are assigned.

---

## 8. Direct Parquet Pipeline & Columnar Serialization (`RootStreamParquetMaker` & `parquet_trf.py`)

### What was in `master`
In `master`, the only way to perform downstream analysis and train neural networks (e.g. Ringer) was via ROOT TTrees produced by legacy ntuple makers. Users wanting to work with Python Data Science ecosystems (Pandas, Polars, PyTorch, DuckDB) had to rely on intermediate ROOT converters or slow Python extraction scripts, leading to large storage overheads and high deserialization latency.

### The Refactored Solution: `RootStreamParquetMaker`
Introduced direct C++ serialization to **Apache Parquet** (`.parquet`) through **Apache Arrow** (`parquet/arrow/writer.h`), fully integrated into Lorenzetti's transform infrastructure via `parquet_trf.py`:

1. **Direct AOD-to-Parquet Transformation:** Directly processes AOD input files and writes columnar Parquet tables without requiring intermediate ROOT files.
2. **1:1 Feature Equivalence with Ntuple:** Dumps identical variables:
   - Scalar metrics (`EventNumber`, `RunNumber`, `avgmu`, kinematics `cl_eta`, `cl_phi`, `cl_e`, `cl_et`, shower shapes, and electron PID).
   - Nested vectors stored as native Arrow lists (`list<float>`) for calorimeter rings (`cl_rings_*`, `cl_ringsL0`, `truth_cl_rings_*`) and MC truth (`mc_pdgid`, `mc_eta`, `mc_phi`, `mc_e`, `mc_et`).
3. **PIMPL Architecture Isolation:** Uses `struct Impl; std::unique_ptr<Impl> m_impl;` in `RootStreamParquetMaker.h`. This encapsulates Arrow C++20 headers (`<arrow/api.h>`, `<parquet/arrow/writer.h>`) within `RootStreamParquetMaker.cxx`, completely insulating the ROOT dictionary generator (`rootcling`) from C++ standard mismatches.
4. **Fileless `StoreGate` Execution:** Extended `StoreGate` to support in-memory mode when output is `.parquet`, preventing the creation of unwanted empty ROOT files.
5. **Parallel Chunk Merging (`merge_parquet_files`):** Integrated PyArrow table concatenation into `kernel/GaugiKernel/python/Parallel.py`, enabling multi-worker parallelism (`-nw 4 -m`) with automatic chunk merging into a single `.parquet` file.
6. **C++20 Template Destructor Conformance:** Updated `DataVector<T>::~DataVector()` and `Collection<T>::~Collection()` in `GaugiKernel` to conform to modern C++20 specifications (eliminating deprecated template-id destructor syntax).

```python
# Direct transformation CLI:
parquet_trf.py -i Zee.AOD.root -o Zee.parquet --nov 1000

# Parallel batch processing with automatic chunk merge:
parquet_trf.py -i Zee.AOD.root -o Zee.parquet -nw 4 -m
```

### Improvements
- **Zero ROOT Dependency for ML:** Parquet files load instantly into Python (`pq.read_table("Zee.parquet").to_pandas()`) without needing ROOT or PyROOT in the analysis environment.
- **Superior Storage & Compression:** Leverages Parquet's columnar dictionary and bit-packing compression, achieving substantial space savings over flat ROOT trees.
- **High Performance:** Native C++ event loop with preallocated Arrow builders scales efficiently across large datasets.

---

## 9. Active Persistence Registry & Stream Auto-Configuration (`recordable()`)

### What was in `master`
In earlier iterations, configuring any `RootStream*Maker` required passing every single EDM container key individually via explicit keyword arguments (e.g. `InputEventKey`, `InputSeedsKey`, `InputTruthKey`, `InputClusterKey`, `InputTruthClusterKey`, `InputRingerKeys`, `InputElectronKey`, `InputTruthElectronKey`, etc.). This resulted in:
- 10 to 15 lines of repetitive boilerplate in every transformation script (`simu_trf.py`, `digit_trf.py`, `reco_trf.py`, `merge_trf.py`).
- Constant human error whenever new container keys or algorithms were introduced.
- Inconsistency with `RootStreamReader`, which automatically discovers all branches inside the input ROOT file.

### The Refactored Solution: Active Registry via `recordable()`
1. **Dynamic Registration:** Calling `recordable("Key")` in algorithm definitions automatically resolves the corresponding EDM container type (e.g. `"CaloClusterContainer"` for `"Clusters"`) using `DEFAULT_KEY_TO_TYPE_MAP` and registers `"TypeName#Key"` into an active ordered registry (`_active_recorded_items`).
2. **Zero-Parameter Stream Makers:** `RootStreamHITMaker`, `RootStreamESDMaker`, and `RootStreamAODMaker` automatically query the active registry for the containers matching their respective data tier:
   ```python
   # simu_trf.py
   HIT = RootStreamHITMaker("RootStreamHITMaker", OutputLevel=outputLevel, OnlyRoI=not save_all_hits)

   # digit_trf.py
   ESD = RootStreamESDMaker("RootStreamESDMaker", OutputLevel=outputLevel)

   # reco_trf.py
   AOD = RootStreamAODMaker("RootStreamAODMaker", OutputLevel=outputLevel)
   ```
3. **Full Backward Compatibility:** Explicit `Input*Key` overrides and custom `ItemList` parameters are fully respected when provided.
4. **Clean Job Lifecycle Isolation:** `clear_recorded_items()` ensures per-job registry resetting across multi-process and sequential tasks.

---

## 10. Declarative Output Schema & Streamlined Reconstruction Stack

### What was in `master`
In `master`:
1. **Rigid Output Structures:** `RootStreamNtupleMaker` unconditionally booked fixed sets of hardcoded branches. Users had no fine-grained control to filter or select specific variables without modifying C++ code.
2. **Redundant `RingsL0` Stage:** Ring construction was split across an intermediate uncalibrated ring container (`RingsL0`) and subsequent noise-filtered rings (`Rings`), forcing maker algorithms to book dual containers and cluttering output datasets.
3. **Redundant Truth Reconstruction Stack:** Reconstruction scripts executed duplicate algorithms (`cluster_truth`, `hypo_truth`, and `ringer_truth`) that re-ran clustering, PID, and ring construction specifically on `TruthCells` (producing `TruthClusters`, `TruthElectrons`, and `TruthRings`). This tripled the execution time of `reco_trf.py`, produced redundant data on disk, and complicated ntuple and parquet makers with cumbersome cross-matching loops.

### The Refactored Solution

1. **Declarative Output Schema (`RootStreamSchema`):**
   - Implemented a flexible schema mapping engine in `RootStreamNtupleMaker` and `RootStreamParquetMaker` allowing users to configure output branches via a dictionary of `<BranchName> : "<TypeName>#<ContainerKey>#<Property>"`.
   - EDM converters (`EventInfoConverter`, `CaloClusterConverter`, `CaloRingsConverter`, `ElectronConverter`, `SeedConverter`, `TruthParticleConverter`) parse schema descriptors dynamically, booking and serializing only requested variables.
   - Vector ring unpacking: `get_scalar_rings_schema(prefix='ring_', n_rings=100)` maps nested ring vectors directly into scalar branches (`ring_0` .. `ring_99`).
   - Unified default schema: `get_default_schema()` consolidates all 61 standard baseline variables into a single dictionary, eliminating global state fragmentation.

2. **Removal of `RingsL0`:**
   - With direct calorimeter ring calculation incorporating noise thresholds (`SigmaCut`), the separate `RingsL0` tier was eliminated across C++ converters, makers, and Python configurations.

3. **Streamlined Single-Stack Reconstruction:**
   - Removed `cluster_truth`, `hypo_truth`, and `ringer_truth` from `reco_trf.py`.
   - Replaced redundant truth reconstruction with direct matching against simulation Monte Carlo particles (`TruthParticleContainer#Particles` $\to$ `mc_pdgid`, `mc_eta`, `mc_phi`, `mc_e`, `mc_et`).
   - Cleaned up C++ properties (`InputTruthClusterKey`, `InputTruthRingerKeys`, `InputTruthElectronKey`) and internal matching loops in `RootStreamNtupleMaker` and `RootStreamParquetMaker`.

4. **Execution Introspection & Data Flow Tree (`print(acc)`):**
   - Added sequence tracking to `ComponentAccumulator` and automatic container/property introspection to `Configurable`.
   - Calling `print(acc)` or `acc.print()` outputs an eAthena/Gaugi-style visual diagram detailing:
     - The exact sequence of algorithms with their configured properties.
     - The StoreGate EDM container lineage tree displaying every transient/persistent container, its producer algorithm/reader, and all consumer algorithms.

5. **Upstream RoI Hit Filtering in `CaloHitBuilder`:**
   - Relocated Region of Interest (RoI) hit filtering from `RootStreamBuilder` into `CaloHitBuilder` (`CaloHitMerge`), adhering strictly to Single Responsibility principles.
   - Deleted `CaloHitBranchHandler.h`, standardizing `CaloHitContainer` on `GenericBranchHandler`.
   - Cleaned up `RootStreamMaker.h/.cxx` (removed `OnlyRoI`, `EtaWindow`, `PhiWindow`, `TruthKey`, `CellHashes`), making it purely item-list driven, and eliminated `RootStreamBuilder`'s dependency on `G4Kernel`.
   - In `CaloHitBuilder`, `OnlyRoI` defaults to `False`; `simu_trf.py` toggles it via `OnlyRoI=not save_all_hits`.
   - Hits outside the RoI cone are filtered prior to heap allocation in `StoreGate`, reducing memory consumption and ensuring identical hit content across ROOT and Parquet output tiers.

---

## 11. Component Modernization: `Gaugi::Tool`, Pileup Migration & `CaloCellBuilder` Electronics

### Context & Motivation
In legacy `master`:
1. Sub-algorithm helper components were inherited from 1990s Gaudi nomenclature (`Gaugi::AlgTool` / `IAlgTool`).
2. The hit pileup overlay algorithm (`PileupMerge`) was erroneously located inside `CaloCellBuilder/src/`, despite operating 100% on `xAOD::CaloHitContainer` and `xAOD::EventInfoContainer` with zero dependency on `CaloCell`.
3. `CaloCellBuilder/src` mixed high-level reconstruction algorithms with low-level analog/digital electronics signal modeling tools (`PulseGenerator`, `OptimalFilter`, `ConstrainedOptimalFilter`, `PulsePerturber`) in a flat directory.
4. `merge_trf.py` lacked a Python `Configurable` wrapper and invoked `ROOT.PileupMerge` directly.

### Enhancements & Refactoring
1. **Modernized Component Base Class (`Gaugi::Tool`):**
   - Replaced legacy `Gaugi::AlgTool` / `IAlgTool` with **`Gaugi::Tool`** / **`Gaugi::ITool`**, establishing the clean modern pair: `Algorithm` & `Tool`.
   - Updated `Property.h` and `Configurable.py` to seamlessly accept `Gaugi::Tool*`.
   - Migrated all reconstruction tools (`PulseGenerator`, `OptimalFilter`, `ConstrainedOptimalFilter`, `PulsePerturber`, `ShowerShapes`) to inherit from `Gaugi::Tool`.

2. **Pileup Merge Relocation & Modernization in `CaloHitBuilder`:**
   - Moved hit pileup overlay from `CaloCellBuilder/src/PileupMerge` to `CaloHitBuilder/src/CaloHitPileupMerge` where it logically belongs.
   - Renamed class to **`CaloHitPileupMerge`** and purged deprecated dual-file APIs (`LowPileupInputFiles`, `HighPileupInputFiles`, `low_pileup_files`, `high_pileup_files`, and `PileupMerge` alias).
   - Unified pileup generation around a single Minimum Bias library (`PileupFiles` / `--pileup-files`), simulating high-luminosity conditions by drawing Poisson($\mu$) interactions per bunch crossing in $[bc_{\text{start}}, bc_{\text{end}}]$.
   - Added native copy constructor and `CaloHit* copy() const` to `xAOD::CaloHit`, allowing `allocate()` to clone hits directly without verbose field-by-field copying.
   - Implemented RoI-preserving pileup overlay: MinBias cells falling outside the hard-scatter event's `hit_map` are discarded before conversion, preserving signal RoI boundaries, preventing event size inflation (~187k full detector cells), and eliminating dynamic allocations (`new CaloHit`) in the inner loop.
   - Implemented high-throughput sequential circular streaming with 30 MB prefetch buffer (`SetCacheSize`): replaces out-of-order random reads with forward sequential streaming across bunch crossings and events (`(m_currentEntry + 1) % total_entries`), maximizing ROOT basket cache hits and speeding up pileup superposition by 10x–30x.
   - Created Python configurable wrapper `CaloHitPileupMergeCfg` in `CaloHitBuilder/python/CaloHitPileupMerge.py`.
   - Modernized `merge_trf.py` to import and instantiate `CaloHitPileupMergeCfg` with `--pileup-files`.

3. **Internal Reorganization of `CaloCellBuilder`:**
   - Retained core reconstruction algorithms in `CaloCellBuilder/src/` (`CaloCellMaker`, `CaloCellMerge`, `CaloCellNoiseSuppression`, and `CaloCellCrossTalk`).
   - Renamed `CrossTalkMaker` to **`CaloCellCrossTalk`** (with alias `CrossTalkMaker`) and re-activated it in the ROOT dictionary.
   - Created dedicated subfolder `CaloCellBuilder/src/electronics/` for signal modeling and filtering tools (`PulseGenerator`, `OptimalFilter`, `ConstrainedOptimalFilter`, `PulsePerturber`).
   - Configured `CaloCellBuilder/CMakeLists.txt` with recursive source/header discovery, proper include directories, and `LinkDef.h` exclusion.

---

## 12. End-to-End Simulation & Reconstruction Pipeline (`examples/run_reco_sequence.py`)

### Context & Implementation
To demonstrate and validate the complete simulation, pileup overlay, and reconstruction lifecycle across all data tiers, an automated workflow runner was introduced in [`examples/run_reco_sequence.py`](file:///home/joao.pinto/git_repos/lorenzetti/examples/run_reco_sequence.py).

The runner coordinates 3 execution phases:
1. **Phase 1: MinBias Pileup Library**
   - Event Generation (`gen_minbias.py`) producing 10 events split across 2 chunks (`minbias.EVT.0.root`, `minbias.EVT.1.root`).
   - Calorimeter Simulation (`simu_trf.py`) with Geant4 multi-threading producing `minbias.HIT.0.root` and `minbias.HIT.1.root`.
2. **Phase 2: Clean Hard-Scatter Signal**
   - Full chain execution: `EVT -> HIT -> ESD -> AOD -> NTUPLE -> PARQUET` for clean $Z \to ee$ events across 2 parallel workers.
3. **Phase 3: Pileup Superposition & Full Reconstruction**
   - Overlaying MinBias pileup ($\langle \mu \rangle = 10$) onto Zee HITs (`merge_trf.py`).
   - Digitization (`digit_trf.py`), Offline Reconstruction (`reco_trf.py`), Analysis Ntuple (`ntuple_trf.py`), and Columnar ML export (`parquet_trf.py`).

### Key Enhancements & Interoperability Fixes
- **Branch Decoupling in `CaloHitPileupMerge`:** Added `PileupHitsKey` property and automatic branch fallback (`CaloHitContainer_Hits`) so signal hit keys in `EventContext` (`Hits_Signal`) are decoupled from library branch names.
- **`RootStreamHITReaderCfg` Key Forwarding:** Extended `RootStreamHITReaderCfg` in [`RootStreamReader.py`](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/io/RootStreamBuilder/python/RootStreamReader.py) to forward `OutputHitsKey`, `OutputEventKey`, `OutputTruthKey`, and `OutputSeedsKey` directly to `RootStreamReaderCfg`.
- **Merged Filename Pattern Matching:** Updated `output_replace` rules in `digit_trf.py` (`.HIT` -> `.ESD`), `reco_trf.py` (`.ESD` -> `.AOD`), `ntuple_trf.py` (`.AOD` -> `.NTUPLE`), and `parquet_trf.py` (`.root` -> `.parquet`) to cleanly match both clean (`.HIT.`) and merged (`.HIT_Merged.`) files without breaking naming schemes.
- **Pipeline Introspection & Resuming:** Added `--skip-existing` option to `run_reco_sequence.py` to bypass already-computed data tiers, plus Rich summary tables showing event counts and file sizes across all 13 output directories.

---

## 13. ATLAS Run 4 High-Fidelity Geometry & Detector Construction v2 (PR #18)

### Context & Motivation
In legacy `master`, detector simulation relied on `DetectorConstruction_v1`, which implemented a simplified, schematic calorimeter model consisting of idealized cylindrical shells. While useful for rapid software validation, it lacked realistic absorber thicknesses, accurate cell segmentation, cryostats, dead materials, and the geometry specifications of the ATLAS experiment.

In PR #18 (`feat/detector-construction-v2`), Luciano introduced **`DetectorConstruction_v2`** ([DetectorConstruction_v2.cxx](file:///home/joao.pinto/git_repos/lorenzetti/geometry/GeoV2/src/DetectorConstruction_v2.cxx)), establishing an authentic ATLAS Run 4 calorimeter, magnetic field, and Geant4 physics environment derived directly from official ATLAS sources (GeoModel SQLite dumps and Athena code).

### Sub-detectors & Active Calorimeter Layout
1. **Tile Calorimeter (`AtlasTile`):**
   - Built with periodic ATLAS Run 4 geometry (14 mm steel absorber plates, 3 mm plastic scintillator tiles, and 1 mm clearance).
   - Authentic Tile cell segmentation (`A1-A16`, `BC1-BC8`, `B9`, `D0-D6`) mapping every volume point directly to a readout cell.
   - Intermediate Tile Calorimeter (ITC) gap with aluminium plug (passive D4/C10) and service cabling.
   - Active gap and crack scintillators (E1-E4) and active ITC cells (C10, D4) placed at Run 4 coordinates (+40 mm side A, -30 mm side C).
   - Dual-readout PMT simulation (two PMTs per Tile cell) with configurable energy splitting: `"ushape"` (realistic light-guide attenuation model) or `"linear"`.
2. **Liquid Argon (LAr) Calorimeters:**
   - **Barrel EM Calorimeter (EMB) (`AtlasEmb`):** Lead-LAr accordion structure with ATLAS lead absorber thicknesses (1.53 mm below $|\eta| = 0.8$, 1.13 mm above). Precise cell boundaries ending at $|z| = 3165$ mm with fine strip granularity ($\Delta\eta = 0.003125$ in EMB1).
   - **Endcap EM Calorimeter (EMEC) (`AtlasEmec`):** Concentric inner and outer accordion wheels covering $1.375 < |\eta| < 3.2$, with dynamic LAr gap fractions computed across radial bands to reflect accordion geometry expansion.
   - **Hadronic Endcap (HEC) (`AtlasHec`):** 4 longitudinal samplings (HEC0-HEC3) with 25 mm (HEC0/HEC1) and 50 mm (HEC2/HEC3) copper plates and nominal cell mapping.
   - **Forward Calorimeter (FCal) (`AtlasFcal`):** Homogeneous passive metal modules (copper for FCal1, tungsten for FCal2/FCal3) embedded in liquid argon, detailed electrode tube readout cell mapping, and optional fast simulation frozen shower library parameterization (`MC23_v1`).

### Cryostats, Dead Materials & Services
- Solenoid and front cryostat walls modeled in radiation lengths ($X_0$).
- Barrel cryostat outer cylinders, cold vessel walls, and dead liquid argon buffers.
- Endcap cryostats with warm and cold vessels.
- Forward shielding (muon system shielding, toroid magnets, and framework).
- Crack and gap services simulating dead material between barrel and extended barrel calorimeters.

### External GeoModel Run 4 Database Integration
- Added optional GeoModel 6.29.0 loader ([AtlasGeoModelImport.cxx](file:///home/joao.pinto/git_repos/lorenzetti/geometry/GeoV2/src/AtlasGeoModelImport.cxx)) reading the Run 4 SQLite database dump (`geometry-ATLAS-P2-RUN4-01-01-00-sim.db`).
- Imports the ITk (Inner Tracker), HGTD (High Granularity Timing Detector), and beam pipe geometry directly into the Geant4 simulation world.

### Magnetic Field & Geant4 Production Settings
- Uniform 2 T solenoid-only field ($R < 1.23\text{ m}$, $|z| < 2.9\text{ m}$) or full 3D ATLAS magnetic field map (`bfieldmap_7730_20400_14m.root`) with calo muon switching field.
- Geant4 production settings: `FTFP_BERT_ATL` physics list, tuned production cuts, and Russian roulette optimizations for low-energy particles.
- Birks' law saturation correction applied to scintillators and liquid argon.
- Time-of-flight (TOF) corrected global hit times and neutron time termination cut ($150\text{ ns}$ for v2).

---

## 14. Free-Running Calorimeter Hits & Athena EMEC Charge Collection (PR #19)

### Context & Motivation
Standard simulation in Lorenzetti aggregates energy deposits into fixed bunch-crossing windows within the internal EDM (`CaloHitContainer`). However, benchmarking against Athena or feeding external digitization workflows requires saving raw calorimeter hits in the exact layout of the ATLAS simulation `HITS` ntuple without Lorenzetti's internal time binning.

In PR #19 (`feat/free-running-hits`), Luciano introduced the free-running hit generation framework alongside a C++ port of Athena's EMEC charge collection model.

### Free-Running Hit Stream (`CollectionTree`)
- Implemented in [CaloFreeRunningHitWriter.cxx](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/calorimeter/CaloHitBuilder/src/CaloFreeRunningHitWriter.cxx) and [CaloFreeRunningHitList.h](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/calorimeter/CaloHitBuilder/src/CaloFreeRunningHitList.h).
- Writes calorimeter hits directly into the ATLAS `CollectionTree` layout:
  - `TileCalHit_*`: recorded per PMT (dual readout).
  - `LArHitEMB_*`, `LArHitEMEC_*`, `LArHitHEC_*`, `LArHitFCAL_*`: recorded per calorimeter cell.
- **Athena `FilterHit_tf` Format:** Compresses and filters LAr hit energy and timing matching Athena's `FilterHit_tf`, omitting extra `tglobal` auxiliary branches.
- **Multi-Tree Flexibility:**
  - Option to retain the standard Lorenzetti HIT stream alongside free-running hits in `FreeRunningTree` (`FreeRunningFlags.KeepHits`).
  - Option to record raw Geant4 steps without ATLAS time binning (`FreeRunningFlags.NoBinning`).

### Ported Athena 23.0.14 EMEC Charge Collection
- Implemented in [LArG4EC_LArEMECChargeCollection.cxx](file:///home/joao.pinto/git_repos/lorenzetti/geometry/GeoV2/src/LArG4EC_LArEMECChargeCollection.cxx), ported directly from Athena 23.0.14 `LArG4::EC::EnergyCalculator`.
- Models the non-uniform electric field in the accordion liquid argon folds using:
  - Electric field map: `ec.fieldzv03` (24 MB).
  - High-voltage map: `HVEMECMap_v02.dat`.
  - Radial calibration tables: `EmecTables-ATLAS-P2-RUN4-01-01-00.csv`.
- Accurately computes electron drift velocities and field-dependent charge collection efficiencies across the accordion fold geometry.

---

## 15. Event Generation, Physics Modeling & Core Geometry Bug Fixes (PR #15, PR #16, PR #20)

### Physics & Geometry Defects Resolved
Luciano addressed several numerical and physical defects across event generation, geometry construction, and hit extraction:

1. **Physical Charge Determination from PDG Table (PR #15):**
   - In `master`, particle charge in [helper.cxx](file:///home/joao.pinto/git_repos/lorenzetti/generator/filters/src/helper.cxx) was inferred simply from the sign of the PDG ID (`pdg_id > 0`), erroneously classifying neutral particles ($K_L^0$, $n$, $\pi^0$) as charged and inverting antiparticle charges.
   - Fixed by querying `TDatabasePDG::Instance()->GetParticle(pdg_id)->Charge() / 3.0` for true physical electric charges.
2. **Gaussian Vertex Spread in `Pythia8Gen` (PR #15):**
   - In `master`, the Gaussian generator in `Pythia8Gen.cxx` mistakenly divided the random variable by $\sqrt{2\pi}$, skewing spatial and temporal vertex smearing ($\sigma / \sqrt{2\pi}$ instead of $\sigma$). Removed this division.
3. **Cross-Event Seed ID Isolation (PR #15):**
   - Explicitly cleared `p_seed_id` in `EventTape.cxx` between events, preventing seed association leaks during multi-event generation.
4. **Sensitive Detector Regioning at Step Midpoint (PR #16):**
   - `CaloHitMaker` previously tested detector volumes at `preStepPoint`. Steps traversing boundaries into active calorimeter media were misclassified or dropped. Fixed to evaluate sensitive volumes at the step midpoint:
     $$\vec{r}_{\text{mid}} = \frac{1}{2}\left(\vec{r}_{\text{pre}} + \vec{r}_{\text{post}}\right)$$
5. **Geometry Placement Dedup (PR #16):**
   - Fixed duplicate volume placement in `DetectorConstruction_v1.compile()`, eliminating overlapping geometry warnings and memory bloating.
6. **Kinematics & Generation Robustness (PR #16):**
   - Safe evaluation of $E_T = E$ at $\eta = 0$ in `ParticleHelper::et()`.
   - Identified antiparticles of invisible particles as invisible.
   - Wrapped azimuthal separation $\Delta\phi$ to $[-\pi, \pi]$ in JF17 jet filter constituents.
   - Preserved fractional pileup mean ($\langle\mu\rangle$) in `Pileup`.
   - Added automatic event regeneration when Pythia8 or an algorithm fails to generate a valid event.
7. **Generator Options in `gen_minbias` & `Pileup` (PR #20):**
   - Configurable collision vertex Gaussian spread: `--sigma-z` (in mm) and `--sigma-t` (in ps) in `gen_minbias.py`.
   - Configurable particle transverse momentum thresholds in `Pileup`: `--pt-min-charged` and `--pt-min-neutral`.

---

## 16. Unified Dataclass Job Steering System (`JobFlags`) & CLI Decoupling

### Context & Architectural Challenge
The integration of PR #18, PR #19, and PR #20 introduced over 35 fine-grained parameters for geometry, sub-detectors, cryostats, magnetic field, hit response, and digitization. Originally, exposing these options bloated `simu_trf.py` and `digit_trf.py` into monolithic scripts with 40+ CLI arguments, breaking the declarative simplicity established in Section 6.

### The Refactored Solution: Centralized `JobFlags` Hierarchy
To resolve this without sacrificing flexibility, the configuration layer was refactored around a centralized, typed, serializable system using Python standard library `@dataclass(init=False)` in [JobFlags.py](file:///home/joao.pinto/git_repos/lorenzetti/kernel/GaugiKernel/python/JobFlags.py):

1. **`JobFlags` Base Class:**
   - Provides `to_dict()`, `from_dict()`, `to_json()`, `from_json()`, `reset()`, and structured `__repr__()`.
   - Implements dynamic attribute retrieval: instance initialization queries `getattr(self.__class__, f.name, f.default)` so that class-level attribute mutations dynamically propagate to object instances and serialization dictionaries.
2. **Domain-Specific Flag Dataclasses with Full English Comments:**
   - **`AtlasGeometryFlags`** ([AtlasGeometryFlags.py](file:///home/joao.pinto/git_repos/lorenzetti/geometry/GeoV2/python/AtlasGeometryFlags.py)): 24 flags governing Tile, EMB, EMEC, HEC, FCal, cryostats, gap services, GeoModel Run 4 database paths, and field maps.
   - **`MagFieldFlags`** ([MagFieldFlags.py](file:///home/joao.pinto/git_repos/lorenzetti/magfield/python/MagFieldFlags.py)): Steering for `EnableField` and `EnableSolenoidOnly`.
   - **`CaloHitFlags` & `FreeRunningFlags`** ([CaloHitFlags.py](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/calorimeter/CaloHitBuilder/python/CaloHitFlags.py)): Active energy response, Birks' law, dual readout, neutron time cut, and free-running ATLAS HITS generation.
   - **`CaloFlags`, `CrossTalkFlags`, `AnomalyFlags`** ([CaloFlags.py](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/calorimeter/CaloCellBuilder/python/CaloFlags.py)): Electronic noise, cell cross-talk coupling, and dead-channel masking.
   - **`CaloClusterFlags`** ([CaloClusterFlags.py](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/calorimeter/CaloClusterBuilder/python/CaloClusterFlags.py)): Cluster seed thresholds, window dimensions, and forward shower moments.
   - **`RootStreamESDFlags` & `RootStreamAODFlags`** ([RootStreamFlags.py](file:///home/joao.pinto/git_repos/lorenzetti/reconstruction/io/RootStreamBuilder/python/RootStreamFlags.py)): RoI windowing, full cell streaming, and Ringer concentric, corner, asymmetric, and strip ring topologies.
3. **Decoupled CLI Transforms:**
   - Pruned `simu_trf.py` and `digit_trf.py` down to 10-11 orthogonal, essential options (`-i`, `-o`, `-nt`, `-nw`, `--detector`, `--nov`, `--timeout`, `--job-file`, `--pre-init`, `--pre-exec`).
4. **Flexible Steering Paradigms:**
   - **Python `--pre-init` Overrides:**
     ```bash
     simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 \
       --pre-init "from GeoV2 import AtlasGeometryFlags as Geo; Geo.AtlasEmb = False; Geo.AtlasEmbCells = False"
     ```
   - **Batch JSON Profiles via `--job-file`:**
     ```json
     {
       "AtlasGeometryFlags": { "AtlasRun4": false },
       "CaloHitFlags": { "BirksLaw": true, "NeutronTimeCut": 150.0 }
     }
     ```
5. **Quality Assurance & Reference Manual:**
   - Comprehensive test suite in [test_job_flags.py](file:///home/joao.pinto/git_repos/lorenzetti/kernel/GaugiKernel/tests/test_job_flags.py) (15 passing tests).
   - Dedicated reference documentation in [doc/flags.md](file:///home/joao.pinto/git_repos/lorenzetti/doc/flags.md).

---

## 17. Decoupled 3-Package Geometry Architecture & Unified Factory (`GeoBase`, `GeoV1`, `GeoV2`)

### Context & Architectural Challenge
In earlier versions and initial refactoring stages, the `geometry/` subsystem was structured into monolithic, semi-duplicated directories `geometry/v1` and `geometry/v2`. This created several architectural drawbacks:
- **Massive Code Duplication:** Foundational primitives (`PhysicalVolume.py`, `SensitiveDetector.py`, `Calorimeter.py`, `Tracking.py`) and pulse shape data files (`pulseTile.dat`, `pulseLar.dat`) were copy-pasted identically across both version trees.
- **Tight Coupling & Manual Branching:** High-level transforms (`simu_trf.py`, `digit_trf.py`) were forced to perform manual `if/else` branching to import and instantiate either `v1` or `v2`:
  ```python
  # Old pattern: manual branching in transforms
  if detector == "v1":
      from geometry.v1 import DetectorConstruction_v1 as ATLAS
      det = ATLAS("ATLAS")
  elif detector == "v2":
      from geometry.v2 import DetectorConstruction_v2 as ATLAS
      det = ATLAS("ATLAS")
  ```
- **Cluttered Subdetector Namespaces:** Subdetectors (`ECAL`, `TILE`, `EMEC`, `HEC`, `FCAL`, `DeadMaterials`) resided directly in the package's top-level Python folder alongside the main `DetectorConstruction` classes and primitives.

### The Refactored Solution: 3 First-Class Packages & `DetectorConstructionCfg`
The geometry subsystem was redesigned into three distinct, specialized packages without backward compatibility baggage:

```
geometry/
├── CMakeLists.txt
├── GeoBase/
│   ├── CMakeLists.txt
│   ├── data/
│   │   ├── pulseLar.dat
│   │   └── pulseTile.dat
│   ├── python/
│   │   ├── __init__.py
│   │   ├── Calorimeter.py
│   │   ├── DetectorConstructionCfg.py
│   │   ├── DetectorFlags.py
│   │   ├── PhysicalVolume.py
│   │   ├── SensitiveDetector.py
│   │   └── Tracking.py
│   └── tests/
│       └── test_detector_construction_cfg.py
├── GeoV1/
│   ├── CMakeLists.txt
│   ├── GeoV1/
│   │   └── DetectorConstruction_v1.h
│   ├── python/
│   │   ├── __init__.py
│   │   ├── DetectorConstruction_v1.py
│   │   └── detectors/
│   │       ├── DeadMaterials.py
│   │       ├── ECAL.py
│   │       ├── EMEC.py
│   │       ├── HEC.py
│   │       ├── TILE.py
│   │       └── __init__.py
│   ├── src/
│   └── scripts/
└── GeoV2/
    ├── CMakeLists.txt
    ├── GeoV2/
    │   ├── DetectorConstruction_v2.h
    │   ├── EnergyCalculator.h
    │   ├── LArWheelCalculator.h
    │   └── ...
    ├── src/
    ├── python/
    │   ├── __init__.py
    │   ├── AtlasGeometryFlags.py
    │   ├── DetectorConstruction_v2.py
    │   └── detectors/
    │       ├── AtlasBarrelCryostat.py
    │       ├── AtlasBarrelFront.py
    │       ├── AtlasEmb.py
    │       ├── AtlasEmec.py
    │       ├── AtlasFCal.py
    │       ├── AtlasHec.py
    │       ├── AtlasRun4.py
    │       ├── AtlasTile.py
    │       ├── DeadMaterials.py
    │       ├── ECAL.py
    │       ├── EMEC.py
    │       ├── FCAL.py
    │       ├── HEC.py
    │       ├── TILE.py
    │       └── __init__.py
    ├── src/
    └── scripts/
```

1. **`geometry/GeoBase` (Common Primitives & Factory):**
   - **Zero Redundancy:** Single source of truth for volume construction (`PhysicalVolume`), sensitive detector setup (`SensitiveDetector`), calorimeter utilities (`Calorimeter`), tracking configurations (`Tracking`), and pulse shapes (`pulseLar.dat`, `pulseTile.dat`).
   - **`DetectorFlags`:** Centralized `@dataclass(init=False)` tracking `DetectorFlags.Version` (defaulting to `"v1"`).
   - **Unified Factory `DetectorConstructionCfg`:** Factory function that inspects flags, dynamically resolves version (`v1` or `v2`), applies relevant subsystem defaults (`MagFieldFlags`, `AtlasGeometryFlags`), resolves kwargs, and instantiates the detector:
     ```python
     from GeoBase import DetectorConstructionCfg

     # 1-line instantiation with automatic version resolution
     det = DetectorConstructionCfg("ATLAS", version=detector)
     ```
2. **`geometry/GeoV1` & `geometry/GeoV2` (Dedicated Subsystem Packages):**
   - **Clean Subdetector Organization:** Subdetectors are cleanly quarantined in `detectors/` (`from GeoV1.detectors import ECAL` / `from GeoV2.detectors import AtlasEmb, AtlasTile`), leaving root package namespaces clean.
   - **Decoupled C++ Modules:** Dedicated CMake targets `GeoV1` and `GeoV2` with canonical include headers (`#include "GeoV1/DetectorConstruction_v1.h"` and `#include "GeoV2/DetectorConstruction_v2.h"`).
   - **Direct Data Resolution:** Pulse data paths resolve dynamically via `GeoBase.get_data_dir()` without hardcoding filesystem paths.
3. **Streamlined Transforms:**
   - Both `simu_trf.py` and `digit_trf.py` import `DetectorConstructionCfg` directly from `GeoBase`, reducing detector instantiation boilerplate to a single declarative line.
4. **Comprehensive Test Suite:**
   - [test_detector_construction_cfg.py](file:///home/joao.pinto/git_repos/lorenzetti/geometry/GeoBase/tests/test_detector_construction_cfg.py) covers V1/V2 instantiation, fallback logic, kwargs overrides, and pulse file discovery without requiring a full ROOT installation.

---

## Summary of Benefits

| Feature | `master` | `python_refactory` | Benefit |
| :--- | :--- | :--- | :--- |
| **EDM Associations** | Raw C++ pointers | `SG::ElementLink<T>` | Eliminates crashes, enables persistent ROOT relational storage |
| **Calo Cell Noise** | All cells stored unconditionally | $E > 2\sigma_{\text{noise}}$ threshold | >80% disk space reduction, accurate ATLAS-like cell selection |
| **Stream I/O** | 6+ specialized Maker/Reader classes | Generalized `RootStreamMaker/Reader` | ~2,500 lines removed; automated branch discovery; decoupled lifecycle |
| **Job Parallelism** | External scripts / manual splitting | `@parallel_job` & `@file_parallel_job` | Built-in multiprocessing, event chunking, and auto-merge (ROOT & Parquet) |
| **CLI Transforms** | ~250 lines of `argparse` per script | Declarative typed functions via `typer` | Clean syntax, automatic JSON configs, uniform flags |
| **C++ Configuration** | Manual `setProperty()` calls | Dynamic `Configurable` + `PropertyList` | Natural Python syntax, `+=` tool accumulation, type coercion |
| **Modern Parquet ML** | Non-existent (ROOT TTree only) | Direct C++ `RootStreamParquetMaker` | Direct ML integration (PyTorch/Pandas), native Arrow list support, zero ROOT dependency |
| **Persistence Registry** | Manual 15-key argument passing per maker | Active registry via `recordable()` | Zero boilerplate in `simu_trf`, `digit_trf`, and `reco_trf`; auto-discovers tier items |
| **Analysis Schema & Reco Stack** | Hardcoded branches, duplicate `RingsL0` & truth reco algs | Declarative `RootStreamSchema`, single-stack reco + MC matching, `print(acc)` tree | >60% faster reconstruction, flexible custom schemas, instant pipeline introspection |
| **Simulation Hit Filtering** | Specialized `CaloHitBranchHandler` in I/O tier | Upstream in `CaloHitBuilder` (`CaloHitMerge`) | Removed `CaloHitBranchHandler.h` & `G4Kernel` dependency from I/O; reduced event RAM; ROOT & Parquet parity |
| **Component Hierarchy & Pileup** | Legacy `AlgTool`, `PileupMerge` in `CaloCellBuilder`, dual low/high files, random I/O | Modern `Gaugi::Tool`, `CaloHitPileupMerge` with unified MinBias, `CaloHit::copy()`, RoI filter, sequential circular stream | Idiomatic C++ terminology; unified single-library pileup; fast RoI overlay; 10x-30x faster sequential prefetch streaming |
| **End-to-End Workflow** | Fragmented manual shell commands | Executable `examples/run_reco_sequence.py` | Automated multi-worker, multi-threaded pipeline from EVT to Parquet with pileup overlay |
| **ATLAS Run 4 Geometry (PR #18)** | Stylized concentric cylinders (`v1`) | Full-fidelity `DetectorConstruction_v2`: Tile periodic cells, EMB/EMEC/HEC/FCal, cryostats, GeoModel SQLite import, FTFP_BERT_ATL | Authentic ATLAS Run 4 material budget, cell granularities, and simulation physics |
| **Free-Running Hits & EMEC Charge (PR #19)** | Fixed bunch-crossing binning only | Exact ATLAS `CollectionTree` HITS ntuple layout, Athena `FilterHit_tf` format, ported 23.0.14 EMEC charge collection | Direct compatibility with external Athena digitization and detector response validation |
| **Generator & Physics Modeling (PR #15, #16, #20)** | Sign-based charge check, divided $\sigma$, volume dups, preStep hit tagging | `TDatabasePDG` charge lookup, true Gaussian spread, step midpoint regioning, single volume placement, vertex/pT options | Elimination of physical bugs, zero cross-event seed leakage, accurate kinematics |
| **Unified Dataclass Job Steering** | 35+ bloated CLI flags per transform | Centralized `@dataclass(init=False)` `JobFlags`, `--pre-init` Python steering, `--job-file` JSON | Clean 10-argument CLIs, typed configuration, full serializability, and automated testing |
| **Decoupled 3-Package Geometry & Factory** | Monolithic v1/v2 folders with duplicated files & manual if/else imports | Clean 3-package hierarchy (`GeoBase`, `GeoV1`, `GeoV2`), `detectors/` submodules, `DetectorConstructionCfg` | Modular architecture, zero file duplication, 1-line transform instantiation |

