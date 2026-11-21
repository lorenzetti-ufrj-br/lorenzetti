# Proposta de Arquitetura: Padrão Maker + Tool para CaloRings (Todas as Topologias por Padrão via `acc += rings`)

## 1. Contexto e Motivação

Atualmente, o pacote `reconstruction/calorimeter/CaloRingsBuilder` possui seis algoritmos monolíticos derivados de `CaloRingsMaker` (`CaloAsymRingsMaker`, `CaloCrossRingsMaker`, `CaloCornerRingsMaker`, `CaloStripsRingsMaker` e `CaloCustomRingsMaker`). Todos eles duplicam o gerenciamento de containers no StoreGate, filtros de seleção em eta e o loop sobre `CaloClusters`.

Nesta proposta revisada:
1. **Eliminação de seletores e `if/elif`**: Em vez de ter um parâmetro como `Topologies` e blocos de `if/elif`, o configurador principal **`CaloRingsBuilderCfg` instancia e retorna todas as 6 topologias por padrão** em uma lista de algoritmos pronta para `acc += rings`.
2. **Configurações pré-estabelecidas no construtor de suas Cfgs**: Cada tipo de anel possui seu próprio configurador especialista de ferramenta (`StandardRingsToolCfg`, `AsymRingsToolCfg`, `CrossRingsToolCfg`, `CornerRingsToolCfg`, `StripsRingsToolCfg`, `CustomRingsToolCfg`) e de algoritmo (`StandardRingsMakerCfg`, `AsymRingsMakerCfg`, etc.). Todas as propriedades geométricas (camadas de amostragem, número de anéis, deltas em eta/phi, shifts, eixos) ficam **já estabelecidas como valores padrão diretamente no construtor de suas respectivas Cfgs**, sem necessidade de lógica condicional intermediária.
3. **Padrão Maker + Tool por Topologia**:
   - O **`CaloRingsMaker`** (algoritmo genérico `Gaugi::Algorithm`) cria e grava seu container exclusivo no StoreGate (`"Rings"`, `"Rings_Asym"`, `"Rings_Cross"`, `"Rings_Corner"`, `"Rings_Strips"`, `"Rings_Custom"`), itera sobre os clusters de entrada e instancia cada `xAOD::CaloRings`.
   - A **`Tool`** especialista (derivada de `CaloRingsBaseTool : Gaugi::Tool` em `CaloRingsTools`) recebe o ponteiro `xAOD::CaloRings`, calcula a distribuição espacial de energia a partir das células do cluster e decora o objeto chamando `rings->setRings(ref_rings)`.
4. **Entrega de Lista para Acúmulo Direto (`acc += rings`)**:
   - O `CaloRingsBuilderCfg` monta os 6 Makers especialistas (cada um com sua respectiva Tool associada via operador `+=`) e entrega a lista completa `[standard, asym, cross, corner, strips, custom]`.
   - O `ComponentAccumulator` anexa todos os algoritmos à sequência em uma única instrução limpa:
     ```python
     rings = CaloRingsBuilderCfg("CaloRingsBuilder", InputClusterKey=recordable("Clusters"), OutputRingerKey=recordable("Rings"))
     acc += rings
     ```

---

## 2. Visão Geral da Arquitetura

```
                                  ┌─────────────────────────────────────────┐
                                  │          ComponentAccumulator           │
                                  └────────────────────┬────────────────────┘
                                                       │
                                                       │ acc += rings (lista de todos os 6 makers)
            ┌─────────────────────┬────────────────────┼────────────────────┬─────────────────────┬─────────────────────┐
            │                     │                    │                    │                     │                     │
            ▼                     ▼                    ▼                    ▼                     ▼                     ▼
┌───────────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│    CaloRingsMaker     │ │  CaloRingsMaker  │ │  CaloRingsMaker  │ │  CaloRingsMaker   │ │  CaloRingsMaker   │ │  CaloRingsMaker   │
│      (Standard)       │ │      (Asym)      │ │     (Cross)      │ │     (Corner)      │ │     (Strips)      │ │     (Custom)      │
│ - Cria: "Rings"       │ │ - "Rings_Asym"   │ │ - "Rings_Cross"  │ │ - "Rings_Corner"  │ │ - "Rings_Strips"  │ │ - "Rings_Custom"  │
│ - Itera em Clusters   │ │ - Itera Clusters │ │ - Itera Clusters │ │ - Itera Clusters  │ │ - Itera Clusters  │ │ - Itera Clusters  │
└───────────┬───────────┘ └────────┬─────────┘ └────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
            │                      │                    │                     │                     │                     │
            │ decora CaloRings     │ decora CaloRings   │ decora CaloRings    │ decora CaloRings    │ decora CaloRings    │ decora CaloRings
            ▼                      ▼                    ▼                     ▼                     ▼                     ▼
┌───────────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│   StandardRingsTool   │ │  AsymRingsTool   │ │  CrossRingsTool  │ │  CornerRingsTool  │ │  StripsRingsTool  │ │  CustomRingsTool  │
│   (Gaugi::Tool)       │ │  (Gaugi::Tool)   │ │  (Gaugi::Tool)   │ │  (Gaugi::Tool)    │ │  (Gaugi::Tool)    │ │  (Gaugi::Tool)    │
│  - setRings(...)      │ │ - setRings(...)  │ │ - setRings(...)  │ │ - setRings(...)   │ │ - setRings(...)   │ │ - setRings(...)   │
└───────────┬───────────┘ └────────┬─────────┘ └────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘
            │                      │                    │                     │                     │                     │
            ▼                      ▼                    ▼                     ▼                     ▼                     ▼
┌───────────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
│ xAOD::CaloRingsCont.  │ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│ │xAOD::CaloRingsCont│
│     Key: "Rings"      │ │ Key: "Rings_Asym"│ │Key: "Rings_Cross"│ │Key: "Rings_Corner"│ │Key: "Rings_Strips"│ │Key: "Rings_Custom"│
└───────────────────────┘ └──────────────────┘ └──────────────────┘ └───────────────────┘ └───────────────────┘ └───────────────────┘
```

---

## 3. Estrutura de Diretórios e Arquivos

### 3.1. Novo Pacote: `tools/calorimeter/CaloRingsTools`
Contém a modelagem matemática (`RingSet`), a classe base comum `CaloRingsBaseTool` e as 6 ferramentas de anéis especializadas:
```
tools/calorimeter/CaloRingsTools/
├── CMakeLists.txt
├── README.md
├── python/
│   ├── __init__.py
│   └── CaloRingsTools.py            # StandardRingsToolCfg, AsymRingsToolCfg, etc. (valores padrão pré-estabelecidos, sem kwargs)
├── src/
│   ├── LinkDef.h                    # Dicionário ROOT de todas as tools e RingSets
│   ├── RingSet.h                    # RingSet, RingSetAsym, RingSetCross, RingSetCorner, RingSetStrips, RingSetCustom
│   ├── RingSet.cxx
│   ├── CaloRingsBaseTool.h          # Classe base abstrata Gaugi::Tool com propriedades e métodos comuns
│   ├── CaloRingsBaseTool.cxx
│   ├── StandardRingsTool.h          # Tool de anéis concêntricos regulares
│   ├── StandardRingsTool.cxx
│   ├── AsymRingsTool.h              # Tool de anéis assimétricos (4 quadrantes)
│   ├── AsymRingsTool.cxx
│   ├── CrossRingsTool.h             # Tool de anéis em cruz (Top, Bottom, Left, Right com CrossShift)
│   ├── CrossRingsTool.cxx
│   ├── CornerRingsTool.h            # Tool de anéis nos cantos diagonais (CornerShift)
│   ├── CornerRingsTool.cxx
│   ├── StripsRingsTool.h            # Tool de projeção em tiras por eixo (Axis 0=eta, 1=phi)
│   ├── StripsRingsTool.cxx
│   ├── CustomRingsTool.h            # Tool de deslocamentos arbitrários (RingsShiftEta, RingsShiftPhi)
│   └── CustomRingsTool.cxx
└── tests/
    └── test_rings_tools.py          # Testes unitários de cada Tool
```

### 3.2. Pacote Refatorado: `reconstruction/calorimeter/CaloRingsBuilder`
Contém apenas o algoritmo genérico `CaloRingsMaker`, o utilitário de fusão `CaloRingsMerge` e os configuradores Python:
```
reconstruction/calorimeter/CaloRingsBuilder/
├── CMakeLists.txt
├── README.md
├── python/
│   ├── __init__.py
│   └── CaloRingsBuilder.py          # CaloRingsMakerCfg, StandardRingsMakerCfg, AsymRingsMakerCfg, ..., CaloRingsBuilderCfg
├── src/
│   ├── LinkDef.h                    # Registra CaloRingsMaker e CaloRingsMerge
│   ├── CaloRingsMaker.h             # Algoritmo Gaugi::Algorithm genérico com slot para 1 Gaugi::Tool
│   ├── CaloRingsMaker.cxx
│   ├── CaloRingsMerge.h             # Utilitário de fusão de containers
│   └── CaloRingsMerge.cxx
└── tests/
    └── test_rings_builder.py        # Testes de integração dos Makers e do BuilderCfg
```

---

## 4. Detalhes de Implementação em C++

### 4.1. `CaloRingsMaker` (`CaloRingsBuilder`)
O `CaloRingsMaker` atua exclusivamente como orquestrador do ciclo de vida:
- Inicializa o container de saída `xAOD::CaloRingsContainer` no StoreGate via `SG::WriteHandle`.
- Lê a coleção de `xAOD::CaloClusterContainer` via `SG::ReadHandle`.
- Aplica o corte de aceitância em pseudorrapidez (`EtaRange`).
- Para cada cluster aprovado, instancia um `xAOD::CaloRings`, associa o `CaloCluster` pai e invoca `m_tool->execute(ctx, rings)`.
- Adiciona o `xAOD::CaloRings` decorado ao container.

```cpp
#ifndef CaloRingsMaker_h
#define CaloRingsMaker_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/Tool.h"
#include "GaugiKernel/DataHandle.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "CaloRings/CaloRingsContainer.h"
#include <string>
#include <vector>

class CaloRingsMaker : public Gaugi::Algorithm {
public:
  CaloRingsMaker(std::string name);
  virtual ~CaloRingsMaker() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode finalize() override;

  // Interface para acoplamento da ferramenta especialista
  void setRingsTool(Gaugi::Tool *tool) { m_tool = tool; }
  void addTool(Gaugi::Tool *tool) { setRingsTool(tool); }
  void push_back(Gaugi::Tool *tool) { setRingsTool(tool); }
  Gaugi::Tool* tool() const { return m_tool; }

private:
  std::string m_clusterKey;
  std::string m_ringerKey;
  std::string m_histPath;
  std::vector<float> m_etaRange;
  int m_outputLevel;
  Gaugi::Tool *m_tool;
};

#endif
```

```cpp
StatusCode CaloRingsMaker::post_execute(SG::EventContext &ctx) const
{
  // 1. Cria e registra o container exclusivo desta coleção
  SG::WriteHandle<xAOD::CaloRingsContainer> ringer(m_ringerKey, ctx);
  ringer.record(std::make_unique<xAOD::CaloRingsContainer>());

  // 2. Lê os clusters de entrada
  SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);
  if (!clusters.isValid()) {
    MSG_WARNING("CaloClusterContainer '" << m_clusterKey << "' invalido no EventContext!");
    return StatusCode::SUCCESS;
  }

  // 3. Itera sobre os clusters
  uint32_t clus_idx = 0;
  for (const auto *clus : *clusters) {
    if (!clus) {
      clus_idx++;
      continue;
    }

    if (std::abs(clus->eta()) < m_etaRange[0] || std::abs(clus->eta()) >= m_etaRange[1]) {
      clus_idx++;
      continue;
    }

    // Instancia o objeto CaloRings e vincula ao cluster
    auto *rings = new xAOD::CaloRings();
    rings->setEta(clus->eta());
    rings->setPhi(clus->phi());
    rings->setCaloCluster(m_clusterKey, clus_idx, clus);

    // 4. A Tool associada decora o CaloRings com o vetor de anéis
    if (m_tool) {
      if (m_tool->execute(ctx, rings).isFailure()) {
        MSG_ERROR("Falha ao decorar CaloRings com a ferramenta: " << m_tool->name());
        delete rings;
        return StatusCode::FAILURE;
      }
    }

    // 5. O Maker armazena o CaloRings decorado no container
    ringer->push_back(rings);
    clus_idx++;
  }

  return StatusCode::SUCCESS;
}
```

---

### 4.2. `CaloRingsBaseTool` (`CaloRingsTools`)
Classe base abstrata herdando de `Gaugi::Tool`:

```cpp
#ifndef CaloRingsBaseTool_h
#define CaloRingsBaseTool_h

#include "GaugiKernel/Tool.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/EventContext.h"
#include "CaloCluster/CaloCluster.h"
#include "CaloRings/CaloRings.h"
#include "CaloCell/CaloCell.h"
#include "RingSet.h"
#include <vector>
#include <string>

namespace Gaugi {

class CaloRingsBaseTool : public Tool {
public:
  CaloRingsBaseTool(std::string name);
  virtual ~CaloRingsBaseTool() = default;

  virtual StatusCode initialize() override;
  virtual StatusCode finalize() override;

  /*! Assinatura canônica de Gaugi::Tool: recebe o CaloRings a ser decorado como Gaugi::EDM* */
  virtual StatusCode execute(SG::EventContext &ctx, Gaugi::EDM *edm) const override = 0;

protected:
  const xAOD::CaloCell* maxCell(const xAOD::CaloCluster *clus, const RingSet &rs) const;
  bool passSigmaCut(const xAOD::CaloCell *cell) const;

  std::vector<float> m_detaRings;
  std::vector<float> m_dphiRings;
  std::vector<int> m_nRings;
  std::vector<std::vector<int>> m_layerRings;
  bool m_doSigmaCut;
  float m_sigmaCut;
  int m_maxRingsAccumulated;
  int m_outputLevel;
};

} // namespace Gaugi

#endif
```

---

## 5. Implementação dos Módulos Python (Sem `if/elif` e com Assinaturas Explícitas)

### 5.1. `CaloRingsTools.py` (`tools/calorimeter/CaloRingsTools/python/`)
Todas as configurações de amostragem (`LayerRings`), granularidades (`DeltaEtaRings`, `DeltaPhiRings`), números de anéis (`NRings`) e parâmetros específicos (`CornerShift`, `CrossShift`, `Axis`, `RingsShiftEta`, `RingsShiftPhi`) são **definidas diretamente nos valores padrão dos construtores**:

```python
__all__ = [
    "StandardRingsToolCfg",
    "AsymRingsToolCfg",
    "CrossRingsToolCfg",
    "CornerRingsToolCfg",
    "StripsRingsToolCfg",
    "CustomRingsToolCfg",
]

from typing import List, Optional
import ROOT
import numpy as np
from CaloCell.CaloDefs import CaloSampling
from GaugiKernel import Configurable, LoggingLevel

_PI = float(np.pi)

# Configurações padrão de amostragem do calorímetro
_DEFAULT_LAYERS = [
    [CaloSampling.PSB, CaloSampling.PSE],
    [CaloSampling.EMB1, CaloSampling.EMEC1],
    [CaloSampling.EMB2, CaloSampling.EMEC2],
    [CaloSampling.EMB3, CaloSampling.EMEC3],
    [CaloSampling.HEC1, CaloSampling.TileCal1, CaloSampling.TileExt1],
    [CaloSampling.HEC2, CaloSampling.TileCal2, CaloSampling.TileExt2],
    [CaloSampling.HEC3, CaloSampling.TileCal3, CaloSampling.TileExt3],
]

_DEFAULT_DELTA_ETA = [0.025, 0.00325, 0.025, 0.050, 0.1, 0.1, 0.2]
_DEFAULT_DELTA_PHI = [_PI / 32, _PI / 32, _PI / 128, _PI / 128, _PI / 128, _PI / 32, _PI / 32, _PI / 32]
_DEFAULT_N_RINGS = [8, 64, 8, 8, 4, 4, 4]


def StandardRingsToolCfg(
    name: str = "StandardRingsTool",
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    return Configurable(
        ROOT.Gaugi.StandardRingsTool,
        name,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else list(_DEFAULT_N_RINGS),
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def AsymRingsToolCfg(
    name: str = "AsymRingsTool",
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    # 4 quadrantes: (n - 1) * 4 + 1
    default_asym_rings = [(n - 1) * 4 + 1 for n in _DEFAULT_N_RINGS]
    return Configurable(
        ROOT.Gaugi.AsymRingsTool,
        name,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_asym_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def CrossRingsToolCfg(
    name: str = "CrossRingsTool",
    CrossShift: int = 3,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    default_cross_rings = [n * 4 for n in _DEFAULT_N_RINGS]
    return Configurable(
        ROOT.Gaugi.CrossRingsTool,
        name,
        CrossShift=CrossShift,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_cross_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def CornerRingsToolCfg(
    name: str = "CornerRingsTool",
    CornerShift: int = 3,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    default_corner_rings = [n * 4 for n in _DEFAULT_N_RINGS]
    return Configurable(
        ROOT.Gaugi.CornerRingsTool,
        name,
        CornerShift=CornerShift,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_corner_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def StripsRingsToolCfg(
    name: str = "StripsRingsTool",
    Axis: int = 0,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    default_strips_rings = [28, 252, 28, 14, 8, 8, 4]
    return Configurable(
        ROOT.Gaugi.StripsRingsTool,
        name,
        Axis=Axis,
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else default_strips_rings,
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )


def CustomRingsToolCfg(
    name: str = "CustomRingsTool",
    RingsShiftEta: Optional[List[float]] = None,
    RingsShiftPhi: Optional[List[float]] = None,
    DeltaEtaRings: Optional[List[float]] = None,
    DeltaPhiRings: Optional[List[float]] = None,
    NRings: Optional[List[int]] = None,
    LayerRings: Optional[List[List[int]]] = None,
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    return Configurable(
        ROOT.Gaugi.CustomRingsTool,
        name,
        RingsShiftEta=RingsShiftEta if RingsShiftEta is not None else [0.0],
        RingsShiftPhi=RingsShiftPhi if RingsShiftPhi is not None else [0.0],
        DeltaEtaRings=DeltaEtaRings if DeltaEtaRings is not None else list(_DEFAULT_DELTA_ETA),
        DeltaPhiRings=DeltaPhiRings if DeltaPhiRings is not None else list(_DEFAULT_DELTA_PHI),
        NRings=NRings if NRings is not None else list(_DEFAULT_N_RINGS),
        LayerRings=LayerRings if LayerRings is not None else [list(l) for l in _DEFAULT_LAYERS],
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
```

---

### 5.2. `CaloRingsBuilder.py` (`reconstruction/calorimeter/CaloRingsBuilder/python/`)
Cada topologia possui seu **MakerCfg dedicado** que já instancia a Tool especialista correspondente e a vincula com `maker += tool`. 

O **`CaloRingsBuilderCfg`** simplesmente instancia os 6 configuradores e retorna a lista completa — **sem nenhum `if/elif`**:

```python
__all__ = [
    "CaloRingsBuilder",
    "CaloRingsBuilderCfg",
    "CaloRingsMakerCfg",
    "StandardRingsMakerCfg",
    "AsymRingsMakerCfg",
    "CrossRingsMakerCfg",
    "CornerRingsMakerCfg",
    "StripsRingsMakerCfg",
    "CustomRingsMakerCfg",
]

from typing import List, Optional
import ROOT

from GaugiKernel import Configurable, LoggingLevel
from CaloRingsTools import (
    StandardRingsToolCfg,
    AsymRingsToolCfg,
    CrossRingsToolCfg,
    CornerRingsToolCfg,
    StripsRingsToolCfg,
    CustomRingsToolCfg,
)


def CaloRingsMakerCfg(
    name: str = "CaloRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings",
    EtaRange: Optional[List[float]] = None,
    HistogramPath: str = "Expert/Rings",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """Configura o algoritmo Gaugi::Algorithm base CaloRingsMaker."""
    return Configurable(
        ROOT.CaloRingsMaker,
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        EtaRange=EtaRange if EtaRange is not None else [0.0, 2.5],
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )


def StandardRingsMakerCfg(
    name: str = "StandardRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings",
    HistogramPath: str = "Expert/Rings/Standard",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += StandardRingsToolCfg(
        f"{name}_Tool",
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def AsymRingsMakerCfg(
    name: str = "AsymRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Asym",
    HistogramPath: str = "Expert/Rings/Asym",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += AsymRingsToolCfg(
        f"{name}_Tool",
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CrossRingsMakerCfg(
    name: str = "CrossRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Cross",
    CrossShift: int = 3,
    HistogramPath: str = "Expert/Rings/Cross",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += CrossRingsToolCfg(
        f"{name}_Tool",
        CrossShift=CrossShift,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CornerRingsMakerCfg(
    name: str = "CornerRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Corner",
    CornerShift: int = 3,
    HistogramPath: str = "Expert/Rings/Corner",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += CornerRingsToolCfg(
        f"{name}_Tool",
        CornerShift=CornerShift,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def StripsRingsMakerCfg(
    name: str = "StripsRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Strips",
    Axis: int = 0,
    HistogramPath: str = "Expert/Rings/Strips",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += StripsRingsToolCfg(
        f"{name}_Tool",
        Axis=Axis,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CustomRingsMakerCfg(
    name: str = "CustomRingsMaker",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings_Custom",
    RingsShiftEta: Optional[List[float]] = None,
    RingsShiftPhi: Optional[List[float]] = None,
    HistogramPath: str = "Expert/Rings/Custom",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    maker = CaloRingsMakerCfg(
        name,
        InputClusterKey=InputClusterKey,
        OutputRingerKey=OutputRingerKey,
        HistogramPath=HistogramPath,
        OutputLevel=OutputLevel,
    )
    maker += CustomRingsToolCfg(
        f"{name}_Tool",
        RingsShiftEta=RingsShiftEta,
        RingsShiftPhi=RingsShiftPhi,
        DoSigmaCut=DoSigmaCut,
        SigmaCut=SigmaCut,
        OutputLevel=OutputLevel,
    )
    return maker


def CaloRingsBuilderCfg(
    name: str = "CaloRingsBuilder",
    InputClusterKey: str = "Clusters",
    OutputRingerKey: str = "Rings",
    DoSigmaCut: bool = False,
    SigmaCut: float = 2.0,
    HistogramPath: str = "Expert/Rings",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> List[Configurable]:
    """
    Configura e entrega todas as 6 topologias de anéis por padrão:
    [Standard, Asym, Cross, Corner, Strips, Custom].
    
    Sem branching condicional (if/elif): cada topologia é instanciada diretamente
    com suas configurações pré-estabelecidas e devolvida na lista para acc += rings.
    """
    return [
        StandardRingsMakerCfg(
            f"{name}_Standard",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=OutputRingerKey,
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Standard",
            OutputLevel=OutputLevel,
        ),
        AsymRingsMakerCfg(
            f"{name}_Asym",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Asym",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Asym",
            OutputLevel=OutputLevel,
        ),
        CrossRingsMakerCfg(
            f"{name}_Cross",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Cross",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Cross",
            OutputLevel=OutputLevel,
        ),
        CornerRingsMakerCfg(
            f"{name}_Corner",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Corner",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Corner",
            OutputLevel=OutputLevel,
        ),
        StripsRingsMakerCfg(
            f"{name}_Strips",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Strips",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Strips",
            OutputLevel=OutputLevel,
        ),
        CustomRingsMakerCfg(
            f"{name}_Custom",
            InputClusterKey=InputClusterKey,
            OutputRingerKey=f"{OutputRingerKey}_Custom",
            DoSigmaCut=DoSigmaCut,
            SigmaCut=SigmaCut,
            HistogramPath=f"{HistogramPath}/Custom",
            OutputLevel=OutputLevel,
        ),
    ]


CaloRingsBuilder = CaloRingsBuilderCfg
```

---

## 6. Exemplos de Uso na Cadeia de Reconstrução

### 6.1. Execução Padrão: Todas as Topologias via `acc += rings`
Em `reco_trf.py` ou qualquer script de análise, o usuário adiciona todas as coleções de anéis com duas linhas:

```python
# Retorna a lista completa com os 6 Makers (Standard, Asym, Cross, Corner, Strips, Custom)
rings = CaloRingsBuilderCfg(
    "CaloRingsBuilder",
    InputClusterKey=recordable("Clusters"),
    OutputRingerKey=recordable("Rings"),
    OutputLevel=outputLevel,
)

# Anexa todos os makers ao ComponentAccumulator
acc += rings
```

Após o término da execução do evento, o StoreGate conterá automaticamente:
- `"Rings"`: `xAOD::CaloRingsContainer` (preenchido com anéis concêntricos regulares)
- `"Rings_Asym"`: `xAOD::CaloRingsContainer` (preenchido com 4 quadrantes assimétricos)
- `"Rings_Cross"`: `xAOD::CaloRingsContainer` (preenchido com cruz de 4 braços)
- `"Rings_Corner"`: `xAOD::CaloRingsContainer` (preenchido com 4 cantos diagonais)
- `"Rings_Strips"`: `xAOD::CaloRingsContainer` (preenchido com projeções em tiras)
- `"Rings_Custom"`: `xAOD::CaloRingsContainer` (preenchido com deslocamentos customizados)

### 6.2. Uso Isolado de uma Única Topologia
Caso o usuário precise em algum estudo apenas dos anéis padrão (ou apenas assimétricos), basta instanciar o Maker desejado diretamente:

```python
# Apenas os anéis concêntricos padrão
acc += StandardRingsMakerCfg(
    "StandardRings",
    InputClusterKey=recordable("Clusters"),
    OutputRingerKey=recordable("Rings"),
)

# Ou apenas as tiras
acc += StripsRingsMakerCfg(
    "StripsRings",
    InputClusterKey=recordable("Clusters"),
    OutputRingerKey=recordable("Rings_Strips"),
)
```

---

## 7. Comparativo Resumido

| Aspecto | Antes (Monolítico) | Proposto (Maker + Tool, Todas por Padrão) |
| :--- | :--- | :--- |
| **Arquitetura C++** | 6 classes monolíticas derivadas de `CaloRingsMaker`. | 1 `CaloRingsMaker` genérico + 6 ferramentas especialistas em `CaloRingsTools`. |
| **Responsabilidade do Maker** | Duplica gestão de container, loops e geometria. | Apenas gerencia o container e invoca `m_tool->execute(ctx, rings)`. |
| **Responsabilidade da Tool** | Inexistente (código misturado no maker). | Decora o objeto `xAOD::CaloRings` com `rings->setRings(ref_rings)`. |
| **Lógica no Python** | Monolítica, sem composição. | **Zero `if/elif`**. Configurações predefinidas em cada construtor Cfg. |
| **Seleção de Topologias** | RingerTopology enum com branching condicional. | **Todas por padrão**. `CaloRingsBuilderCfg` entrega a lista com os 6 Makers. |
| **Sintaxe no Job** | Acoplamento rígido. | **`acc += rings`** (adiciona os 6 geradores em uma só instrução). |
| **Containers no StoreGate** | Apenas um tipo por execução. | **6 containers gravados simultaneamente** (`"Rings"`, `"Rings_Asym"`, etc.). |
| **Protótipos Python** | `**kwargs` em vários lugares. | **Estritamente sem `**kwargs`**, argumentos tipados e explícitos. |
