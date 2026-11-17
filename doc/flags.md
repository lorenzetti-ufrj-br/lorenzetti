# 🎛️ Job Steering & Configuration Flags in Lorenzetti

Lorenzetti uses a centralized, typed, and serializable configuration system built on top of standard Python `@dataclass`.

Instead of bloating command-line interfaces (`simu_trf.py`, `digit_trf.py`, `reco_trf.py`) with dozens of subdetector and physics parameters, fine-grained steering is managed through **Job Flags**.

---

## 🚀 How to Steer Jobs

### 1. Modifying Flags via `--pre-init`
`--pre-init` executes Python code **before** geometry instantiation and algorithm assembly. You can import flag dataclasses and modify their attributes directly:

```bash
# Example: Run simulation with detector v2, but disable EMB and EMB cells
simu_trf.py -i input.EVT.root -o output.HIT.root --detector v2 \
  --pre-init "from GeoV2 import AtlasGeometryFlags as Geo; Geo.AtlasEmb = False; Geo.AtlasEmbCells = False"
```

```bash
# Example: Run digitization with electronic cross-talk and defect simulation enabled
digit_trf.py -i input.HIT.root -o output.ESD.root --detector v2 \
  --pre-init "from CaloCellBuilder import CaloFlags, AnomalyFlags; CaloFlags.DoCrossTalk = True; CaloFlags.DoDefects = True; AnomalyFlags.BadRunListFile = 'bad_runs.json'"
```

### 2. Modifying Properties via `--pre-exec`
`--pre-exec` executes Python code **after** all algorithms have been created and merged into the `ComponentAccumulator`, immediately prior to `acc.run()`. This is useful for inspecting or tuning specific algorithm instances at runtime.

### 3. Submitting Batch Jobs via `--job-file` (JSON)
All flag dataclasses inherit from `JobFlags` (`to_dict()`, `from_dict()`, `to_json()`, `from_json()`). You can configure full profiles in a JSON file:

```json
{
  "AtlasGeometryFlags": {
    "AtlasRun4": false,
    "AtlasForwardShielding": false
  },
  "CaloHitFlags": {
    "BirksLaw": true,
    "NeutronTimeCut": 150.0
  }
}
```

And run:
```bash
simu_trf.py -i /data/*.EVT.root -o /output/ --job-file config.json -nt 4
```

---

## 📦 Domain Flag Reference

### 1. `AtlasGeometryFlags` (`GeoV2/python/AtlasGeometryFlags.py`)
Controls the high-fidelity ATLAS Run 4 geometry, sub-detectors, cryostats, and external database maps.

| Flag | Type | Default (v2) | Description |
| :--- | :---: | :---: | :--- |
| `TileAtlasGeometry` | `bool` | `True` | Build Tile calorimeter with ATLAS periodic geometry (steel/scintillator). |
| `TileAtlasCells` | `bool` | `True` | Use ATLAS Tile cells (A1-A16, BC1-BC8, B9, D0-D6). |
| `TileAtlasItc` | `bool` | `True` | Intermediate Tile gap (ITC) with aluminium plug and cables. |
| `TileAtlasGap` | `bool` | `True` | Gap/crack scintillators E1-E4 and active ITC cells C10, D4. |
| `TileAtlasRun4` | `bool` | `True` | Tile extended barrel and crack at Run 4 positions. |
| `AtlasEmb` | `bool` | `True` | Barrel EM calorimeter with ATLAS lead/LAr absorber composition. |
| `AtlasEmbCells` | `bool` | `True` | EMB strip/middle/back cells ending at \|z\| = 3165 mm. |
| `AtlasEmec` | `bool` | `True` | EM endcap with two accordion wheels. |
| `AtlasEmecArgonFraction` | `bool` | `True` | LAr accordion gap fraction in radial bands. |
| `AtlasHec` | `bool` | `True` | Hadronic endcap (HEC0-HEC3) with nominal ATLAS cells. |
| `AtlasFcal` | `bool` | `True` | FCal passive modules (copper and tungsten). |
| `AtlasFcalCells` | `bool` | `True` | FCal electrode tubes and readout cells. |
| `AtlasFcalFrozenShowers` | `bool` | `True` | Fast simulation frozen shower parametrization in FCal. |
| `AtlasMaterialInFront` | `bool` | `True` | Solenoid and cryostat front walls in radiation lengths. |
| `AtlasEndcapCryostat` | `bool` | `True` | Outer warm and cold vessels of endcap cryostats. |
| `AtlasBarrelCryostat` | `bool` | `True` | Outer cylinders and dead LAr of barrel cryostat. |
| `AtlasForwardShielding` | `bool` | `True` | Muon system shielding, toroids, and framework. |
| `AtlasBarrelGapServices`| `bool` | `True` | Dead material in the gap between barrel and extended barrel. |
| `AtlasRun4` | `bool` | `True` | Import ITk, HGTD, and beam pipe from ATLAS Run 4 GeoModel dump. |
| `AtlasG4` | `bool` | `True` | Geant4 physics settings (FTFP_BERT_ATL, cuts, Russian roulette). |
| `AtlasFullField` | `bool` | `True` | Full magnetic field map and muon switching field. |
| `AtlasRun4Geometry` | `str` | `""` | Path to Run 4 SQLite DB (or `LORENZETTI_ATLAS_RUN4_GEOMETRY`). |
| `AtlasFieldMap` | `str` | `""` | Path to ATLAS field map ROOT file (or `LORENZETTI_FIELD_MAP`). |
| `AtlasFcalElectrodes` | `str` | `""` | Path to FCal electrodes CSV (or `LORENZETTI_FCAL_ELECTRODES`). |

---

### 2. `MagFieldFlags` (`magfield/python/MagFieldFlags.py`)
Controls detector magnetic fields.

| Flag | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `EnableField` | `bool` | `False` | Enable full detector magnetic field. |
| `EnableSolenoidOnly` | `bool` | `True` (v2) / `False` (v1) | Restrict uniform 2 T field strictly to the solenoid volume ($R < 1.23$ m, $\|z\| < 2.9$ m). |

---

### 3. `CaloHitFlags` (`reconstruction/calorimeter/CaloHitBuilder/python/CaloHitFlags.py`)
Controls hit response, birks law, time of flight, and dual readout.

| Flag | Type | Default (v2) | Description |
| :--- | :---: | :---: | :--- |
| `ActiveEnergyOnly` | `bool` | `True` | Keep only energy deposited in active media (scintillator, LAr). |
| `BirksLaw` | `bool` | `True` | Apply Birks' law in scintillator and liquid argon. |
| `AtlasHitTime` | `bool` | `True` | Use TOF-corrected global time for bunch-crossing assignment. |
| `TileDualReadout` | `bool` | `True` | Enable two PMTs per Tile cell. |
| `TilePmtSplit` | `str` | `"ushape"` | Energy sharing between PMTs (`"ushape"` or `"linear"`). |
| `NeutronTimeCut` | `float`| `150.0` (v2) / `0.0` (v1) | Time threshold in ns to terminate neutrons. |
| `SaveAllHits` | `bool` | `False` | Save all hits regardless of Region of Interest (RoI). |

---

### 4. `FreeRunningFlags` (`reconstruction/calorimeter/CaloHitBuilder/python/CaloHitFlags.py`)
Controls free-running calorimeter hits in the exact layout of the ATLAS HITS ntuple.

| Flag | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `Enable` | `bool` | `False` | Write hits to `CollectionTree` (or `FreeRunningTree`) with ATLAS layout. |
| `AtlasFormat` | `bool` | `False` | Compress and filter LAr hits exactly as `FilterHit_tf`. |
| `KeepHits` | `bool` | `False` | Retain standard HIT stream alongside free-running hits. |
| `NoBinning` | `bool` | `False` | Record one hit per Geant4 step without ATLAS time bins. |
| `EmecChargeCollection` | `bool` | `False` | Athena 23.0.14 charge collection and electric field for EMEC. |
| `EmecTables` | `str` | `""` | Path to EMEC tables CSV (`EmecTables-ATLAS-P2-RUN4-01-01-00.csv`). |
| `EmecFieldMap` | `str` | `""` | Path to EMEC electric field map (`ec.fieldzv03`). |
| `EmecHVMap` | `str` | `""` | Path to EMEC HV map (`HVEMECMap_v02.dat`). |

---

### 5. `CaloFlags`, `CrossTalkFlags`, `AnomalyFlags` (`reconstruction/calorimeter/CaloCellBuilder/python/CaloFlags.py`)
Controls pulse generation, optimal filtering, electronic cross-talk, and cell defect simulation.

| Class | Flag | Type | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `CaloFlags` | `SamplingnoiseStd` | `float` | `0.0` | Global Gaussian noise standard deviation override. |
| `CaloFlags` | `DoCrossTalk` | `bool` | `False` | Enable cell-to-cell electronic cross-talk simulation. |
| `CaloFlags` | `DoCOF` | `bool` | `False` | Enable Constrained Optimal Filtering (COF) on Tile. |
| `CaloFlags` | `DoDefects` | `bool` | `False` | Inject detector dead cells and anomalies. |
| `CaloFlags` | `FilterBySigma` | `bool` | `False` | Suppress cells below noise threshold. |
| `CaloFlags` | `SigmaThreshold` | `float` | `2.0` | Sigma multiplier for noise suppression ($E > n\sigma$). |
| `CrossTalkFlags` | `MinEnergy` | `float` | `1.0 * GeV` | Minimum cell energy to induce cross-talk into neighbors. |
| `CrossTalkFlags` | `AmpCapacitive` | `float` | `4.2` | Capacitive coupling amplitude. |
| `CrossTalkFlags` | `AmpInductive` | `float` | `2.3` | Inductive coupling amplitude. |
| `CrossTalkFlags` | `AmpResistive` | `float` | `1.0` | Resistive coupling amplitude. |
| `AnomalyFlags` | `BadRunListFile` | `str` | `""` | JSON file containing lists of masked defective cells. |

---

### 6. `CaloClusterFlags` (`reconstruction/calorimeter/CaloClusterBuilder/python/CaloClusterFlags.py`)
Controls seeded calorimeter cluster reconstruction.

| Flag | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `MinCenterEnergy` | `float` | `1.0 * GeV` | Minimum seed cell energy required to initiate clustering. |
| `EtaWindow` | `float` | `0.4` | Cluster window half-size in $\eta$. |
| `PhiWindow` | `float` | `0.4` | Cluster window half-size in $\phi$. |
| `DoForwardMoments` | `bool` | `False` | Compute longitudinal shower moments for forward calos. |

---

### 7. `RootStreamESDFlags` & `RootStreamAODFlags` (`reconstruction/io/RootStreamBuilder/python/RootStreamFlags.py`)
Controls persistification and Ringer feature extraction.

| Class | Flag | Type | Default | Description |
| :--- | :--- | :---: | :---: | :--- |
| `RootStreamESDFlags` | `SaveAllCells` | `bool` | `False` | Save entire detector cell collection instead of RoI only. |
| `RootStreamESDFlags` | `OnlyRoI` | `bool` | `True` | Filter cells around truth particles. |
| `RootStreamESDFlags` | `EtaWindow` | `float` | `0.4` | RoI window in $\eta$. |
| `RootStreamESDFlags` | `PhiWindow` | `float` | `0.4` | RoI window in $\phi$. |
| `RootStreamAODFlags` | `DumpCells` | `bool` | `True` | Write cell containers into AOD. |
| `RootStreamAODFlags` | `doStdRings` | `bool` | `True` | Build standard concentric calorimeter rings. |
| `RootStreamAODFlags` | `doCornerRings` | `bool` | `False` | Build corner-shifted rings. |
| `RootStreamAODFlags` | `doAsymRings` | `bool` | `False` | Build asymmetric quadrant rings. |
| `RootStreamAODFlags` | `doStripsRings` | `bool` | `False` | Build finely-segmented front layer strip rings. |
| `RootStreamAODFlags` | `DoSigmaCut` | `bool` | `False` | Apply cell noise threshold before ring summation. |
| `RootStreamAODFlags` | `SigmaCut` | `float` | `2.0` | Multiplier for noise cut in rings. |
