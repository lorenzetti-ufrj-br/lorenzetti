# Proposta de Arquitetura: Centralização de `to_ntuple` e `to_parquet` nos Conversores de EDM

## 1. Contexto e Motivação

Atualmente, tanto o `RootStreamNtupleMaker.cxx` (876 linhas) quanto o `RootStreamParquetMaker.cxx` (733 linhas) são algoritmos monolíticos que conhecem e extraem manualmente cada atributo, shower shape e variável de cada EDM. 

Esta proposta adota a mesma filosofia que tornou o `RootStreamMaker` desacoplado e escalável através dos **Converters** (`CaloClusterConverter`, `CaloRingsConverter`, etc.):
- **Cada EDM é a única fonte da verdade** sobre suas propriedades e conversões.
- Os métodos `to_ntuple` e `to_parquet` residem diretamente nos conversores de cada EDM em `events/<EDM>/`.
- As classes conversoras são **puramente `const` e stateless**, garantindo paralelismo total sem *race conditions*.
- A struct `<EDM>_t` atua como buffer de valores escalares/vetoriais (com binding direto no `TTree`).
- A struct `<EDM>_parquet` agrupa os `arrow::Builder`s específicos para Apache Arrow / Parquet.
- O usuário pode configurar exatamente quais variáveis deseja salvar através de um dicionário de esquema.

---

## 2. Visão Geral da Arquitetura

```
                       ┌──────────────────────────────────────────────┐
                       │           xAOD::<EDM>Converter               │
                       │     (Centralizado em events/<EDM>/)          │
                       └──────────────────────┬───────────────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
         ▼                                    ▼                                    ▼
┌──────────────────┐               ┌───────────────────────┐            ┌───────────────────────┐
│     convert()    │               │  book / to_ntuple()   │            │ book / to_parquet()   │
│ (ESD/AOD Stream) │               │   (ROOT TTree Branch) │            │ (Apache Arrow Column) │
└────────┬─────────┘               └──────────┬────────────┘            └──────────┬────────────┘
         │                                    │                                    │
         ▼                                    ▼                                    ▼
 ┌──────────────┐                  ┌───────────────────────┐            ┌───────────────────────┐
 │  <EDM>_t     │ (Buffer POD) ──> │ TTree (Zero-Copy)     │            │ Arrow / Parquet       │
 └──────────────┘                  └───────────────────────┘            └───────────────────────┘
```

### 2.1. Simetria das Structs por EDM
Para cada EDM em `events/<EDM>/<EDM>/<EDM>Converter.h`:
* **`<EDM>_t`**: Buffer de dados primitivos (`float`, `int`, `vector`). Conectado diretamente aos branches do `TTree`.
* **`<EDM>_parquet`**: Struct que agrupa todos os `arrow::Builder`s tipados para geração da tabela Parquet.
* **`<EDM>Converter`**: Classe com métodos `const`:
  - `convert(const EDM *obj, EDM_t &buf) const`
  - `book_ntuple(...) const` / `to_ntuple(...) const`
  - `book_parquet(...) const` / `to_parquet(...) const`

### 2.2. Isolamento de Dicionário ROOT (`#ifndef __CLING__`)
Como os headers das EDMs geram dicionários ROOT via `ROOT_GENERATE_DICTIONARY`, o include de Arrow e a struct `*_parquet` são protegidos por `#ifndef __CLING__`:
```cpp
#ifndef __CLING__
#include <arrow/api.h>
#endif
```
Isso impede que o `rootcling` tente parsear os cabeçalhos de C++20 do Arrow, mantendo a compilação do ROOT 100% limpa.

---

## 3. Seleção de Colunas via Dicionário de Esquema

### 3.1. Formato do Esquema
O usuário pode fornecer um dicionário especificando o nome do branch de saída e o descritor `EDM#Key#property`:

```python
schema = {
    # Nome do Branch/Coluna : "EDM#ContainerKey#Propriedade"
    "cl_eta"       : "CaloCluster#Clusters#eta",
    "cl_phi"       : "CaloCluster#Clusters#phi",
    "cl_e"         : "CaloCluster#Clusters#e",
    "cl_e237"      : "CaloCluster#Clusters#e237",
    "ring_0"       : "CaloRings#Rings#rings[0]",
    "ring_1"       : "CaloRings#Rings#rings[1]",
    "rings_all"    : "CaloRings#Rings#rings",
    "el_tight"     : "Electron#Electrons#tight",
    "el_et"        : "Electron#Electrons#et",
    "truth_cl_eta" : "CaloCluster#TruthClusters#eta",
    "truth_cl_phi" : "CaloCluster#TruthClusters#phi",
    "seed_eta"     : "Seed#Seeds#eta",
    "EventNumber"  : "EventInfo#EventInfo#eventNumber",
    "avgmu"        : "EventInfo#EventInfo#avgmu",
    "mc_pdgid"     : "TruthParticle#Particles#pdgid"
}
```

### 3.2. Estrutura Interna de Representação em C++
No C++, a entrada é `std::map<std::string, std::string>`. O algoritmo faz o parsing e agrupa por `(EDM, Key)`:

```cpp
struct BranchSpec {
  std::string branchName; // Ex: "cl_eta" ou "ring_0"
  std::string fieldName;  // Ex: "eta" ou "rings"
  int index{-1};          // Ex: 0 para "rings[0]", ou -1 se não indexado
};

// Agrupamento por (EDM, Key)
using EDMKeyGroup = std::map<std::pair<std::string, std::string>, std::vector<BranchSpec>>;
```

### 3.3. Comportamento nos Conversores
Cada conversor recebe sua lista de `BranchSpec`. Se o esquema estiver vazio, o conversor realiza o dump padrão completo (todas as variáveis com prefixo padrão).

Exemplo no `CaloClusterConverter`:
```cpp
void CaloClusterConverter::book_ntuple(TTree *tree, CaloCluster_t &buf, 
                                       const std::vector<BranchSpec> &specs) const {
  for (const auto &spec : specs) {
    if (spec.fieldName == "eta")        tree->Branch(spec.branchName.c_str(), &buf.eta);
    else if (spec.fieldName == "phi")   tree->Branch(spec.branchName.c_str(), &buf.phi);
    else if (spec.fieldName == "e")     tree->Branch(spec.branchName.c_str(), &buf.e);
    else if (spec.fieldName == "et")    tree->Branch(spec.branchName.c_str(), &buf.et);
    else if (spec.fieldName == "e237")  tree->Branch(spec.branchName.c_str(), &buf.e237);
    else if (spec.fieldName == "reta")  tree->Branch(spec.branchName.c_str(), &buf.reta);
    // ...
  }
}
```

Exemplo no `CaloRingsConverter` com suporte a `rings[i]`:
```cpp
void CaloRingsConverter::book_ntuple(TTree *tree, CaloRings_t &buf,
                                     const std::vector<BranchSpec> &specs) const {
  for (const auto &spec : specs) {
    if (spec.fieldName == "rings" && spec.index < 0) {
      // Vetor completo std::vector<float>
      m_ringsPtr = &buf.rings;
      tree->Branch(spec.branchName.c_str(), &m_ringsPtr);
    } else if (spec.fieldName == "rings" && spec.index >= 0) {
      // Elemento indexado escalar rings[i]
      // Liga a um buffer auxiliar escalar ou lambda
      tree->Branch(spec.branchName.c_str(), &m_scalarRings[spec.branchName]);
    }
  }
}
```

---

## 4. O Loop de Execução e Navegação

O loop no `fillHistograms` é guiado pelo container de **Elétrons**, navega até o Cluster, Rings e Seed, realiza o matching com Truth e Seed, e delega o preenchimento de cada bloco:

```
[ Electron ]
    │
    ├──> [ CaloCluster ] = el->caloCluster()
    │         │
    │         ├──> [ CaloRings ] = rings associados ao cluster
    │         │
    │         └──> [ Seed ] = clus->seed()
    │                   │
    │                   ├──> [ Truth Cluster ]  (tr_cl->seed() == seed)
    │                   │         │
    │                   │         └──> [ Truth Rings ] (tr_ring->caloCluster() == truth_clus)
    │                   │
    │                   ├──> [ Truth Electron ] (tr_el->caloCluster()->seed() == seed)
    │                   │
    │                   └──> [ MC Particles ]   (mc->seedid() == seed->id())
    │
    ▼
[ Dump por Bloco EDM ] ──> Ntuple (TTree) / Parquet (Arrow)
```

### 4.1. Código no `RootStreamNtupleMaker::fillHistograms`

```cpp
StatusCode RootStreamNtupleMaker::fillHistograms(SG::EventContext &ctx) const
{
  auto store = ctx.getStoreGateSvc();
  TTree *tree = store->tree(m_outputNtupleName.c_str());

  // Handles de Leitura
  SG::ReadHandle<xAOD::EventInfoContainer>     event_container(m_eventKey, ctx);
  SG::ReadHandle<xAOD::ElectronContainer>      electron_container(m_electronKey, ctx);
  SG::ReadHandle<xAOD::CaloRingsContainer>     ringerL0_container(m_ringerL0Key, ctx);
  SG::ReadHandle<xAOD::CaloClusterContainer>   truth_cluster_container(m_truthClusterKey, ctx);
  SG::ReadHandle<xAOD::ElectronContainer>      truth_electron_container(m_truthElectronKey, ctx);
  SG::ReadHandle<xAOD::TruthParticleContainer> truth_container(m_truthKey, ctx);

  // Conversores das EDMs (Stateless)
  xAOD::EventInfoConverter     eventCnv;
  xAOD::ElectronConverter      electronCnv;
  xAOD::CaloClusterConverter   clusterCnv;
  xAOD::CaloRingsConverter     ringsCnv;
  xAOD::SeedConverter          seedCnv;
  xAOD::TruthParticleConverter truthCnv;

  auto evt = (*event_container).front();

  // Loop principal em Elétrons
  for (const auto el : *electron_container)
  {
    auto clus = el->caloCluster();
    if (!clus) continue;

    auto seed = clus->seed();

    // 1. Matching CaloRings L0
    const xAOD::CaloRings *cl_ringerL0 = nullptr;
    if (ringerL0_container.isValid()) {
      for (auto ring : *ringerL0_container) {
        if (ring->caloCluster() == clus) { cl_ringerL0 = ring; break; }
      }
    }

    // 2. Matching Truth Cluster (via seed)
    const xAOD::CaloCluster *truth_clus = nullptr;
    if (truth_cluster_container.isValid() && seed) {
      for (auto tr_cl : *truth_cluster_container) {
        if (tr_cl->seed() == seed) { truth_clus = tr_cl; break; }
      }
    }

    // 3. Matching Truth Electron (via seed)
    const xAOD::Electron *truth_el = nullptr;
    if (truth_electron_container.isValid() && seed) {
      for (auto tr_el : *truth_electron_container) {
        if (tr_el->caloCluster() && tr_el->caloCluster()->seed() == seed) {
          truth_el = tr_el;
          break;
        }
      }
    }

    // =========================================================================
    // DUMP POR BLOCO EDM (Converte para struct e atualiza os branches)
    // =========================================================================
    eventCnv.to_ntuple(evt, m_eventBuf);
    electronCnv.to_ntuple(el, m_elBuf, m_elScalars);
    clusterCnv.to_ntuple(clus, m_clusBuf);
    ringsCnv.to_ntuple(cl_ringerL0, m_ringsL0Buf);
    seedCnv.to_ntuple(seed, m_seedBuf);

    clusterCnv.to_ntuple(truth_clus, m_truthClusBuf);
    electronCnv.to_ntuple(truth_el, m_truthElBuf, m_truthElScalars);

    // MC Truth Particles matched por seedid
    truthCnv.to_ntuple_by_seed(truth_container.get(), seed ? seed->id() : -1, m_mcBuf);

    // Preenche a linha do TTree para este candidato
    tree->Fill();
  }

  return StatusCode::SUCCESS;
}
```

### 4.2. Código no `RootStreamParquetMaker::fillHistograms`

```cpp
StatusCode RootStreamParquetMaker::fillHistograms(SG::EventContext &ctx) const
{
  // Conversores das EDMs
  xAOD::EventInfoConverter     eventCnv;
  xAOD::ElectronConverter      electronCnv;
  xAOD::CaloClusterConverter   clusterCnv;
  xAOD::CaloRingsConverter     ringsCnv;
  xAOD::SeedConverter          seedCnv;
  xAOD::TruthParticleConverter truthCnv;

  auto evt = (*event_container).front();

  for (const auto el : *electron_container)
  {
    auto clus = el->caloCluster();
    if (!clus) continue;
    auto seed = clus->seed();

    // Matchings...
    // (idênticos ao Ntuple)

    // Dump para Arrow Builders das structs *_parquet
    eventCnv.to_parquet(evt, m_impl->event_parquet);
    electronCnv.to_parquet(el, m_impl->el_parquet);
    clusterCnv.to_parquet(clus, m_impl->clus_parquet);
    ringsCnv.to_parquet(cl_ringerL0, m_impl->ringsL0_parquet);
    seedCnv.to_parquet(seed, m_impl->seed_parquet);
    clusterCnv.to_parquet(truth_clus, m_impl->truth_clus_parquet);
    electronCnv.to_parquet(truth_el, m_impl->truth_el_parquet);
    truthCnv.to_parquet_by_seed(truth_container.get(), seed ? seed->id() : -1, m_impl->mc_parquet);
  }

  return StatusCode::SUCCESS;
}
```

---

## 5. Resumo das Structs e Classes por EDM

### 1. `CaloCluster` ([events/CaloCluster/CaloCluster/CaloClusterConverter.h](file:///home/joao.pinto/git_repos/lorenzetti/events/CaloCluster/CaloCluster/CaloClusterConverter.h))
- `CaloCluster_t`: cinemática (`eta`, `phi`, `e`, `et`), camadas (`e0`..`e3`, `ehad1`..`ehad3`), shower shapes (`e237`, `reta`, `rphi`, `rhad`, `eratio`, etc.), momentos (`secondR`, etc.).
- `CaloCluster_parquet`: builders correspondentes do Apache Arrow (`arrow::FloatBuilder`).
- `CaloClusterConverter`: métodos `convert`, `book_ntuple`, `to_ntuple`, `book_parquet`, `to_parquet`.

### 2. `CaloRings` ([events/CaloRings/CaloRings/CaloRingsConverter.h](file:///home/joao.pinto/git_repos/lorenzetti/events/CaloRings/CaloRings/CaloRingsConverter.h))
- `CaloRings_t`: vetor de anéis `std::vector<float> rings`.
- `CaloRings_parquet`: `arrow::ListBuilder` e `arrow::FloatBuilder`.
- Suporte a extração de anel único (`rings[0]`) ou lista completa.

### 3. `Electron` ([events/Egamma/Egamma/ElectronConverter.h](file:///home/joao.pinto/git_repos/lorenzetti/events/Egamma/Egamma/ElectronConverter.h))
- `Electron_t`: cinemática (`eta`, `et`, `phi`), vetor de booleanos `isEM`.
- `Electron_parquet`: builders para `eta`, `et`, `phi` e flags booleanas (`tight`, `medium`, `loose`, `vloose`).

### 4. `EventInfo` ([events/EventInfo/EventInfo/EventInfoConverter.h](file:///home/joao.pinto/git_repos/lorenzetti/events/EventInfo/EventInfo/EventInfoConverter.h))
- `EventInfo_t`: `runNumber`, `eventNumber`, `avgmu`, `totmu`.
- `EventInfo_parquet`: `b_eventNumber` (Int32), `b_runNumber` (Int32), `b_avgmu` (Float).

### 5. `Seed` ([events/EventInfo/EventInfo/SeedConverter.h](file:///home/joao.pinto/git_repos/lorenzetti/events/EventInfo/EventInfo/SeedConverter.h))
- `Seed_t`: `eta`, `phi`, `e`, `et`, `id`.
- `Seed_parquet`: `b_eta`, `b_phi`.

### 6. `TruthParticle` ([events/TruthParticle/TruthParticle/TruthParticleConverter.h](file:///home/joao.pinto/git_repos/lorenzetti/events/TruthParticle/TruthParticle/TruthParticleConverter.h))
- `TruthParticle_t` / `TruthParticleNtupleBuffers`: vetores `mc_pdgid`, `mc_eta`, `mc_phi`, `mc_e`, `mc_et`.
- `TruthParticle_parquet`: list builders correspondentes no Arrow.

---

## 6. Configuração no CMakeLists.txt Raiz

Para que os pacotes em `events/` encontrem os headers do PyArrow durante a compilação:

```cmake
execute_process(COMMAND python3 -c "import pyarrow; print(pyarrow.get_include())" 
                OUTPUT_VARIABLE PYARROW_INCLUDE OUTPUT_STRIP_TRAILING_WHITESPACE)
include_directories(${PYARROW_INCLUDE})
```
