# CaloRingsTools

`CaloRingsTools` is a specialized toolkit that provides geometric models (`RingSetBase` and derived tool-specific RingSets) and decoration tools (`Gaugi::Tool`) for calculating calorimeter shower rings. Each tool receives an `xAOD::CaloRings` object along with the parent `xAOD::CaloCluster` and computes transverse energy sums across concentric rings or custom spatial topologies, decorating the object via `rings->setRings(ref_rings)`.

Each specific ring set definition is self-contained directly inside its respective tool header and source file (`Tool.h`/`Tool.cxx`), derived from `RingSetBase` in `CaloRingsBaseTool.h`:
- `StandardRingsTool.{h,cxx}`: encapsulates `RingSet` (standard concentric rings)
- `AsymRingsTool.{h,cxx}`: encapsulates `RingSetAsym` (4-quadrant rings)
- `CrossRingsTool.{h,cxx}`: encapsulates `RingSetCross` and `SeedPosC` (4-arm cross pattern)
- `CornerRingsTool.{h,cxx}`: encapsulates `RingSetCorner` and `SeedPos` (4-corner diagonal pattern)
- `StripsRingsTool.{h,cxx}`: encapsulates `RingSetStrips` (1D strip projection)
- `CustomRingsTool.{h,cxx}`: encapsulates `RingSetCustom` (arbitrary custom shifts)

---

## Architecture Overview

```
                               ┌─────────────────────────────────┐
                               │         CaloRingsMaker          │
                               │        (Gaugi::Algorithm)       │
                               └────────────────┬────────────────┘
                                                │
                                                │ invokes tool->execute(ctx, rings)
                                                ▼
                               ┌─────────────────────────────────┐
                               │       CaloRingsBaseTool         │
                               │          (Gaugi::Tool)          │
                               └────────────────┬────────────────┘
                                                │
       ┌──────────────────┬─────────────────────┼─────────────────────┬──────────────────┐
       ▼                  ▼                     ▼                     ▼                  ▼
┌──────────────┐   ┌─────────────┐       ┌─────────────┐       ┌─────────────┐    ┌─────────────┐
│StandardRings │   │AsymRingsTool│       │CrossRings   │       │CornerRings  │    │StripsRings  │
│     Tool     │   │(4 quadrants)│       │    Tool     │       │    Tool     │    │    Tool     │
└──────┬───────┘   └──────┬──────┘       └──────┬──────┘       └──────┬──────┘    └──────┬──────┘
       │                  │                     │                     │                  │
       └──────────────────┴─────────────────────┴─────────────────────┴──────────────────┘
                                                │
                                                │ sets decorated rings:
                                                ▼
                               ┌─────────────────────────────────┐
                               │        xAOD::CaloRings          │
                               │     rings->setRings(...)        │
                               └─────────────────────────────────┘
```

---

## Available Tools

| Tool Class | Python Configurator | Description | Output Size / Topology |
| :--- | :--- | :--- | :--- |
| `Gaugi::StandardRingsTool` | `StandardRingsToolCfg` | Concentric rings centered on the hottest cell or cluster center. | 100 rings across 7 calorimeter layers. |
| `Gaugi::AsymRingsTool` | `AsymRingsToolCfg` | 4 quadrants ($Q_1, Q_2, Q_3, Q_4$) measuring shower lateral asymmetries. | $(n-1)\times 4 + 1$ rings per layer. |
| `Gaugi::CrossRingsTool` | `CrossRingsToolCfg` | 4-arm cross pattern (Top, Bottom, Left, Right) with `CrossShift`. | $n \times 4$ rings per layer. |
| `Gaugi::CornerRingsTool` | `CornerRingsToolCfg` | 4 diagonal corner centroids (TopRight, TopLeft, BottomLeft, BottomRight). | $n \times 4$ rings per layer. |
| `Gaugi::StripsRingsTool` | `StripsRingsToolCfg` | 1D projected strip profiles along $\eta$ (`Axis=0`) or $\phi$ (`Axis=1`). | 338 strip slices across 7 layers. |
| `Gaugi::CustomRingsTool` | `CustomRingsToolCfg` | Arbitrary spatial shifts configured via `RingsShiftEta` and `RingsShiftPhi`. | $n \times n_{\text{shifts}}$ rings per layer. |

---

## Python Configuration

All configurator functions provide explicit signatures without `**kwargs` and have all calorimeter layer groupings, ring segmentation sizes, and geometry shifts pre-established with sensible defaults:

```python
from CaloRingsTools import (
    StandardRingsToolCfg,
    AsymRingsToolCfg,
    CrossRingsToolCfg,
    CornerRingsToolCfg,
    StripsRingsToolCfg,
    CustomRingsToolCfg,
)

# Standard concentric rings
tool_std = StandardRingsToolCfg("StandardRingsTool")

# Asymmetric 4-quadrant rings
tool_asym = AsymRingsToolCfg("AsymRingsTool")

# Cross rings with shift of 3 cells
tool_cross = CrossRingsToolCfg("CrossRingsTool", CrossShift=3)

# Strips along eta axis
tool_strips = StripsRingsToolCfg("StripsRingsTool", Axis=0)
```

---

## Integration with `CaloRingsMaker`

In the Lorenzetti reconstruction sequence, a `CaloRingsTool` is coupled to a `CaloRingsMaker` using the `+=` operator:

```python
from CaloRingsBuilder import CaloRingsMakerCfg
from CaloRingsTools import StandardRingsToolCfg

maker = CaloRingsMakerCfg("CaloRingsMaker", OutputRingerKey="Rings")
tool = StandardRingsToolCfg("StandardRingsTool")

# Attaches tool via += operator
maker += tool
```
