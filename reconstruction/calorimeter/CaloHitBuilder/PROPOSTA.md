# Proposta de Refatoração: CaloHitPileupMerge

## 1. Sumário Executivo

Esta proposta formaliza a reestruturação e simplificação do algoritmo **`CaloHitPileupMerge`** dentro do pacote **`CaloHitBuilder`**.

O objetivo primordial é eliminar o modelo legado de arquivos duplos (*low pileup* vs. *high pileup*), substituindo-o por um mecanismo físico, robusto e direto que opera sobre uma **biblioteca única de eventos de Minimum Bias (MinBias)** gerados e simulados individualmente ($\mu = 1$ no bunch crossing $\text{BCID} = 0$).

---

## 2. Motivação e Problemas do Modelo Legado

Na versão herdada do framework:
1. **Complexidade de Produção:** O usuário precisava pré-gerar dois conjuntos de dados distintos de MinBias: arquivos com $\mu \approx 1$ (*low pileup*) e arquivos artificiais pré-agrupados com $\mu \ge 5$ ou $10$ (*high pileup*).
2. **Lógica de Seleção Artificial:** O algoritmo tentava deduzir qual árvore ler alternando entre árvores conforme $k > n_{\text{high}}$, introduzindo descontinuidades estatísticas e complexidade desnecessária.
3. **Mapeamento Rígido por Índice:** O código criava um mapa de índices no início baseado apenas no evento 0 da árvore *high*. Se os eventos subsequentes tivessem células vazias filtradas ou ordem diferente, o mapeamento falhava silenciosamente ou produzia resultados inconsistentes.
4. **Alocações Excessivas:** Para cada célula de cada minbias lido, criava-se e destruía-se um objeto `xAOD::CaloHit` completo via `CaloHitConverter`, resultando em milhões de chamadas `new`/`delete` por evento de sinal.
5. **Interface Duplicada:** Flags redundantes em linha de comando (`--low-pileup-files` e `--high-pileup-files`).

---

## 3. Conceito Físico da Nova Abordagem

### 3.1 A Janela de Bunch Crossings
No LHC e High-Luminosity LHC (HL-LHC), os feixes colidem a cada $25\text{ ns}$. 
* O evento de interesse (*hard-scatter*, por exemplo $Z \to ee$) ocorre no **$\text{BCID} = 0$**.
* O calorímetro registra sinais elétricos com tempo de decaimento do shaper de centenas de nanossegundos. Para modelar corretamente o sinal analógico, o detector é sensível a uma janela temporal de bunch crossings:
  
  $$\text{BCID} \in [\text{bcid\_start}, \text{bcid\_end}] \quad (\text{tipicamente } [-21, +4] \text{ ou } [-8, +3])$$

* **In-time pileup:** Colisões inelásticas ocorrendo no mesmo $\text{BCID} = 0$.
* **Out-of-time pileup:** Colisões inelásticas ocorrendo em colisões anteriores ($\text{BCID} < 0$) e posteriores ($\text{BCID} > 0$).

### 3.2 O Modelo da Biblioteca MinBias
* Uma biblioteca de eventos de MinBias é pré-simulada no Geant4.
* Cada evento da biblioteca representa **1 única colisão inelástica** ($pp \to X$) simulada no seu próprio tempo de colisão central, ou seja, com depósitos de energia situados no bunch crossing **$\text{BCID} = 0$**.
* Quando o algoritmo precisa simular pileup em um bunch crossing qualquer $bc$ (por exemplo, $bc = +4$ ou $bc = -12$), ele seleciona um evento da biblioteca e **injeta a energia daquele evento diretamente no bucket temporal $bc$ da célula correspondente do sinal**.

---

## 4. Fluxo Detalhado de Execução

```mermaid
flowchart TD
    Start([Início do Evento de Sinal]) --> ReadSignal[1. Lê xAOD::CaloHitContainer do Sinal 'Hits']
    ReadSignal --> CloneHits[2. Clona Hits do Sinal em vec_hits e indexa hit_map por Hash]
    CloneHits --> SampleMu[3. Sorteia mu_event ~ Gauss(PileupAvg, PileupSigma)]
    SampleMu --> LoopBC[4. Loop sobre cada Bunch Crossing bc in bcid_start..bcid_end]

    subgraph BC_Loop [Processamento por Bunch Crossing]
        SamplePoisson[4.1 Sorteia n_pileup ~ Poisson mu_event] --> CheckN{n_pileup > 0?}
        CheckN -- Sim --> LoopInteractions[4.2 Loop de 1 até n_pileup]
        CheckN -- Não --> NextBC[Avança para o próximo bc]
        
        LoopInteractions --> SorteiaEntry[Sorteia entry aleatória no TChain MinBias]
        SorteiaEntry --> GetEntry[TChain::GetEntry entry]
        GetEntry --> LoopCells[4.3 Itera sobre células com depósito no MinBias]
        
        LoopCells --> CheckCell{Célula hash existe no hit_map?}
        CheckCell -- Sim --> AddEnergy[hit->edep bc, E_mb_zero]
        CheckCell -- Não --> CreateCell[Cria CaloHit dinamicamente, registra no hit_map e vec_hits]
        CreateCell --> AddEnergy
        
        AddEnergy --> NextCell[Próxima célula MinBias]
        NextCell --> CheckMoreInteractions{Mais interações?}
        CheckMoreInteractions -- Sim --> LoopInteractions
        CheckMoreInteractions -- Não --> NextBC
    end

    LoopBC --> BC_Loop
    NextBC --> CheckEndBC{Último BC atingido?}
    CheckEndBC -- Não --> LoopBC
    CheckEndBC -- Sim --> CalcEffectiveMu[5. Calcula <mu> efetivo = total_interações / num_BCs]
    
    CalcEffectiveMu --> WriteHits[6. Grava xAOD::CaloHitContainer 'Hits_Merged']
    WriteHits --> WriteEventInfo[7. Grava xAOD::EventInfo com avgmu 'Events_Merged']
    WriteEventInfo --> End([Fim do Evento])
```

### 4.1 Passo a Passo Algorítmico

#### Passo 1: Inicialização e Carregamento da Biblioteca (`bookHistograms`)
* Recebe a lista de arquivos de MinBias através da propriedade `PileupInputFiles`.
* Cria um único `TChain` contendo todos os arquivos de MinBias.
* Anexa o `TChain` ao `StoreGate` para acesso durante a execução dos eventos.

#### Passo 2: Preparação do Evento de Sinal (`post_execute`)
* Lê o `xAOD::CaloHitContainer` do sinal (`m_inputHitsKey`, por padrão `"Hits"`).
* Clona os hits para um vetor temporário `std::vector<xAOD::CaloHit*> vec_hits`.
* Constrói uma tabela hash $O(1)$:
  ```cpp
  std::unordered_map<unsigned long int, xAOD::CaloHit*> hit_map;
  ```
  onde a chave é o `hit->hash()` da geometria da célula e o valor é o ponteiro para o `CaloHit`.

#### Passo 3: Flutuação de Luminosidade
* Se `m_pileupSigma > 0`, sorteia o $\mu$ instantâneo do evento segundo uma distribuição Gaussiana:
  
  $$\mu_{\text{event}} \sim \text{Gauss}(\text{PileupAvg}, \text{PileupSigma})$$

* Se `m_pileupSigma == 0`, adota rigorosamente $\mu_{\text{event}} = \text{PileupAvg}$.

#### Passo 4: Superposição Temporal por Bunch Crossing
* Itera por todos os bunch crossings na janela:
  ```cpp
  for (int bc = m_bcid_start; bc <= m_bcid_end; ++bc)
  ```
* Para o bunch crossing $bc$, sorteia o número de colisões inelásticas ocorridas:
  
  $$N_{\text{pileup}} \sim \text{Poisson}(\mu_{\text{event}})$$

* Acumula o total de colisões geradas: $N_{\text{total}} += N_{\text{pileup}}$.
* Para cada colisão de $1$ até $N_{\text{pileup}}$:
  1. Sorteia aleatoriamente um índice de evento da biblioteca MinBias:
     $$\text{entry} = \text{Integer}(\text{total\_entries})$$
  2. Carrega os dados da árvore: `chain->GetEntry(entry)`.
  3. Para cada célula presente nesse evento de MinBias:
     * Extrai a energia depositada em $\text{BCID} = 0$:
       ```cpp
       int zero_idx = -mb_hit.bcid_start;
       float e_mb = mb_hit.edep[zero_idx];
       if (e_mb <= 0.0f) continue;
       ```
     * Localiza a célula correspondente no sinal via `hit_map.find(mb_hit.hash)`.
     * **Caso A (Célula já presente no sinal):**
       Adiciona a energia no bucket temporal do bunch crossing atual:
       ```cpp
       hit->edep(bc, e_mb);
       ```
     * **Caso B (Célula vazia no sinal original, mas atingida pelo MinBias):**
       Cria dinamicamente um novo objeto `xAOD::CaloHit` com os parâmetros geométricos da célula (sampling, detector, $\eta$, $\phi$, hash, etc.), atribui $E(bc) = e_{\text{mb}}$, insere em `hit_map` e adiciona ao vetor de saída `vec_hits`. Isso garante conservação rigorosa da energia depositada, mesmo que o sinal tenha utilizado filtros de células vazias.

#### Passo 5: Persistência dos Dados Fundidos
* **Hits:** Grava o novo `xAOD::CaloHitContainer` na chave `m_outputHitsKey` (por padrão `"Hits_Merged"`).
* **EventInfo:** Cria um novo `xAOD::EventInfo` baseado no original, atualiza o campo `avgmu` com o valor médio real de pileup injetado:
  
  $$\langle \mu \rangle_{\text{efetivo}} = \frac{N_{\text{total}}}{\text{bcid\_end} - \text{bcid\_start} + 1}$$
  
  e grava em `m_outputEventKey` (por padrão `"Events_Merged"`).

---

## 5. Exemplo de Código C++

### 5.1 Definição da Classe (`CaloHitPileupMerge.h`)

```cpp
#ifndef CaloHitPileupMerge_h
#define CaloHitPileupMerge_h

#include "GaugiKernel/Algorithm.h"
#include "CaloHit/CaloHitContainer.h"
#include "EventInfo/EventInfoContainer.h"
#include "CaloHit/CaloHitConverter.h"
#include "TRandom3.h"
#include <unordered_map>
#include <vector>
#include <string>

class CaloHitPileupMerge : public Gaugi::Algorithm
{
  public:
    CaloHitPileupMerge(std::string name);
    virtual ~CaloHitPileupMerge() = default;

    virtual StatusCode initialize() override;
    virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
    virtual StatusCode post_execute(SG::EventContext &ctx) const override;
    virtual StatusCode finalize() override;

  private:
    int poisson(double nAvg) const;
    void allocate(SG::ReadHandle<xAOD::CaloHitContainer> &container,
                  std::vector<xAOD::CaloHit*> &vec_hits) const;
    void deallocate(std::vector<xAOD::CaloHit*> &vec_hits) const;
    float merge(SG::EventContext &ctx, std::vector<xAOD::CaloHit*> &vec_hits) const;

    // Chaves StoreGate
    std::string m_inputHitsKey;
    std::string m_outputHitsKey;
    std::string m_inputEventKey;
    std::string m_outputEventKey;

    // Configuração de Pileup e MinBias
    std::vector<std::string> m_pileupFiles;
    std::string m_ntupleName;
    float m_pileupAvg;
    float m_pileupSigma;
    int   m_bcid_start;
    int   m_bcid_end;
    int   m_maxRetry;
    float m_trunc_mu;
    float m_seed;

    mutable TRandom3 m_rng;
};

using PileupMerge = CaloHitPileupMerge;

#endif
```

### 5.2 Implementação do Método `merge` (`CaloHitPileupMerge.cxx`)

```cpp
float CaloHitPileupMerge::merge(SG::EventContext &ctx, std::vector<xAOD::CaloHit*> &vec_hits) const
{
  auto store = ctx.getStoreGateSvc();
  auto chain = (TChain*)store->decorator("minbias_chain");

  if (!chain || chain->GetEntries() == 0) {
    MSG_FATAL("MinBias TChain is empty or not loaded!");
  }

  // 1. Otimização de I/O: ativa apenas os ramos estritamente necessários
  chain->SetBranchStatus("*", 0);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".edep").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".hash").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".bcid_start").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".sampling").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".detector").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".eta").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".phi").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".deta").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".dphi").c_str(), 1);
  chain->SetBranchStatus(("CaloHitContainer_" + m_inputHitsKey + ".bc_duration").c_str(), 1);

  std::vector<xAOD::CaloHit_t> *minbias_hits = nullptr;
  chain->SetBranchAddress(("CaloHitContainer_" + m_inputHitsKey).c_str(), &minbias_hits);

  // 2. Construção da tabela hash O(1) com as células do evento de sinal
  std::unordered_map<unsigned long int, xAOD::CaloHit*> hit_map;
  hit_map.reserve(vec_hits.size() * 2);
  for (auto* hit : vec_hits) {
    hit_map[hit->hash()] = hit;
  }

  // 3. Sorteio de mu para o evento de sinal
  float mu_event = (m_pileupSigma > 0.0f) ? m_rng.Gaus(m_pileupAvg, m_pileupSigma) : m_pileupAvg;
  if (mu_event < 0.0f) mu_event = 0.0f;

  long long total_entries = chain->GetEntries();
  long long total_interactions = 0;
  int num_bunch_crossings = (m_bcid_end - m_bcid_start + 1);

  // 4. Varredura temporal da janela de Bunch Crossings
  for (int bc = m_bcid_start; bc <= m_bcid_end; ++bc) {
    int n_pileup = poisson(mu_event);
    total_interactions += n_pileup;

    for (int k = 0; k < n_pileup; ++k) {
      long long entry = m_rng.Integer(total_entries);
      if (chain->GetEntry(entry) <= 0) {
        throw std::runtime_error("Erro de I/O ao ler MinBias entry: " + std::to_string(entry));
      }

      if (!minbias_hits) continue;

      for (const auto& mb_hit : *minbias_hits) {
        // Obter o depósito de energia do MinBias correspondente a BC=0
        int zero_idx = -mb_hit.bcid_start;
        if (zero_idx < 0 || zero_idx >= (int)mb_hit.edep.size()) {
          zero_idx = 0;
        }

        float edep_zero = mb_hit.edep[zero_idx];
        if (edep_zero <= 0.0f) continue;

        auto it = hit_map.find(mb_hit.hash);
        if (it != hit_map.end()) {
          // Célula já existe no sinal: soma a energia no bunch crossing 'bc'
          it->second->edep(bc, edep_zero);
        } else {
          // Célula estava vazia no sinal: instancia e anexa
          auto new_hit = new xAOD::CaloHit(
            mb_hit.eta, mb_hit.phi, mb_hit.deta, mb_hit.dphi,
            mb_hit.hash, (CaloSampling)mb_hit.sampling, (Detector)mb_hit.detector,
            mb_hit.bc_duration, m_bcid_start, m_bcid_end
          );
          new_hit->edep(bc, edep_zero);
          vec_hits.push_back(new_hit);
          hit_map[mb_hit.hash] = new_hit;
        }
      }
    }
  }

  delete minbias_hits;
  return static_cast<float>(total_interactions) / static_cast<float>(num_bunch_crossings);
}
```

---

## 6. Otimizações de Desempenho e I/O

1. **Eliminação de Conversões Redundantes:** O código opera diretamente sobre a estrutura leve `xAOD::CaloHit_t` preenchida pelo ROOT I/O, evitando alocar/desalocar milhões de classes pesadas `xAOD::CaloHit` descartáveis.
2. **Busca Rápida em $O(1)$:** A substituição de `std::map` por `std::unordered_map` reduz a latência de busca de célula de $O(\log N)$ para $O(1)$, com `reserve()` prevenindo rehashing.
3. **Filtro de Branches Inativos:** `SetBranchStatus("*", 0)` instrui o ROOT a não ler campos pesados que não participam do merge (como `tof` ou branches de partículas verdadeiras), diminuindo drasticamente a carga em disco e memória.

---

## 7. Interface em Python e Transform (`merge_trf.py`)

### 7.1 Python Configurable (`CaloHitPileupMergeCfg`)
```python
from CaloHitBuilder import CaloHitPileupMergeCfg
from GaugiKernel import ComponentAccumulator

acc = ComponentAccumulator("MergeAcc", "Zee_mu40.HIT.root")

pileup = CaloHitPileupMergeCfg(
    "CaloHitPileupMerge",
    PileupFiles=["/data/minbias/mb_001.HIT.root", "/data/minbias/mb_002.HIT.root"],
    PileupAvg=40.0,
    PileupSigma=0.0,
    InputHitsKey="Hits",
    OutputHitsKey="Hits_Merged",
    BunchIdStart=-21,
    BunchIdEnd=4,
)
acc += pileup
```

### 7.2 Execução via CLI (`merge_trf.py`)
```bash
# Execução simples com MinBias puro:
merge_trf.py \
    -i Zee.HIT.root \
    --pileup-files "/data/minbias/*.root" \
    -o Zee_mu40.HIT.root \
    --pileup-avg 40 \
    --pileup-sigma 0

# Execução em lote com 4 processos paralelos:
merge_trf.py \
    -i /data/hits/ \
    --pileup-files "/data/minbias/*.root" \
    -o /data/merged_hits/ \
    --pileup-avg 60 \
    -nw 4
```

---

## 8. Benefícios Consolidados

* **Simplicidade Operacional:** Apenas um arquivo ou diretório de MinBias é necessário. Não há necessidade de produzir conjuntos *low* e *high* artificiais.
* **Consistência Física:** A sobreposição reproduz fielmente as estatísticas de Poisson do LHC/HL-LHC bunch crossing a bunch crossing.
* **Manutenibilidade:** Elimina centenas de linhas de código confuso e frágil em C++ e nos scripts Python.
