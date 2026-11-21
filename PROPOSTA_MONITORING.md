# Proposta de Arquitetura: Módulo de Monitoramento e Validação Contínua (`reconstruction/monitoring`)

## 1. Contexto e Motivação

Na evolução de um framework de física de partículas como o **Lorenzetti**, refatorações de código, calibrações de geometria e ajustes de algoritmos de reconstrução podem introduzir alterações sutis nas distribuições de grandezas físicas e em variáveis de seleção.

Inspirado no sistema de monitoramento de qualidade do ATLAS (**`Athena TrigEgammaMonitoring`** / Data Quality Monitoring - DQM), esta proposta define um módulo dedicado de monitoramento especialista para o Lorenzetti. 

### Principais Objetivos:
1. **Algoritmo Dedicado de Monitoramento**: Criar um `Gaugi::Algorithm` (`EgammaMonitoringAlg`) integrado em `reconstruction/monitoring`.
2. **Saída Especialista Desacoplada (`expert_monitoring.root`)**: Ao final da cadeia de reconstrução (especialmente na etapa `.AOD`), o algoritmo monitora e serializa todos os histogramas 1D/2D em um arquivo ROOT de auditoria independente (`expert_monitoring.root`), preservando o arquivo `.AOD.root` focado nas árvores físicas (`CollectionTree`).
3. **Escopo Físico Idêntico ao Athena TrigEgammaMonitoring**:
   - **Variáveis de Evento / Pileup**: $\langle\mu\rangle$ (`avgmu`), multiplicidade de partículas e clusters.
   - **Cinemática**: $E_T$, $\eta$, $\phi$, $E$.
   - **Shower Shapes Calorimétricos**: $R_{\eta}$, $R_{\phi}$, $w_{\eta 2}$, $f_1$, $f_3$, $E_{\text{ratio}}$, $R_{\text{had}}$, $w_{\text{tot}}$.
   - **Momentos de Cluster**: $\lambda_{\text{center}}$, $\langle\lambda^2\rangle$ (`secondLambda`), $\langle r^2\rangle$ (`secondR`), $f_{\max}$, momentos transversais e longitudinais.
   - **Identificação / PID**: Frações de aceitação e eficiências por Working Point (*Very Loose*, *Loose*, *Medium*, *Tight*).
   - **Perfis de Anéis (Ringer)**: Distribuições de energia por camada quando `CaloRings` estiver presente.
4. **Ferramenta de Regressão e Validação Histograma-a-Histograma**:
   - Um script CLI (`reco_monitoring_diff.py`) que recebe o arquivo atual e uma referência prévia (`expert_monitoring_ref.root`).
   - Avaliação estatística automática (testes de Kolmogorov-Smirnov e $\chi^2$, pulls de média e RMS).
   - **Geração de Relatório**: Recomendação central de **HTML Interativo** (com busca, filtros de status PASS/WARN/FAIL e gráficos de ratio/pull sobrepostos) com opção de exportar **PDF Resumo Executivo**.

---

## 2. Resposta à Consulta: Relatório em HTML vs PDF

> **Pergunta do Usuário**: *"ai temos uma script que recebe o expert_monitoring.root atual e o root de ref. devemos ser capazes de gerar um relatorio comparando histograma a histograma e ver possiveis desvios entre antes e depois. criamos um html automativo? pdf? sugira."*

### Sugestão Técnica: Estratégia Dual (HTML Interativo como Primário + PDF Executivo via flag)

Recomendamos fortemente a geração de um **HTML Interativo Standalone como formato padrão**, com suporte à exportação de **PDF Resumo**:

| Aspecto | HTML Interativo (Recomendado como Padrão) | PDF (Complementar) |
| :--- | :--- | :--- |
| **Navegabilidade** | **Excelente**: Menu hierárquico retrátil por subsistema (`ShowerShapes`, `Kinematics`, etc.), busca textual instantânea e filtros rápidos por severidade (`FAIL`, `WARN`, `PASS`). | **Estático**: Linear; requer paginação e rolagem contínua para localizar variáveis específicas. |
| **Interatividade** | **Total**: Tooltips com métricas estatísticas exatas ($p_{\text{KS}}$, $\chi^2/\text{ndf}$, $\Delta\mu$, $\Delta\sigma$), zoom em plots com ratio bin-a-bin. | **Estática**: Gráficos fixos com tamanho pré-determinado. |
| **Integração CI/CD** | **Ideal**: Pode ser publicado como página web estática (GitHub Actions Pages, GitLab Pages) e inspecionado diretamente no navegador sem baixar arquivos. | **Boa**: Excelente como anexo de Pull Request ou release notes impressos. |
| **Dependências** | **Zero dependências externas**: O HTML gerado é autocontido (gráficos em SVG/PNG embutidos em Base64, CSS moderno embutido). Abre em qualquer navegador. | Requer visualizador de PDF (Acrobat, Evince, browser). |

### Conclusão da Sugestão:
O script `reco_monitoring_diff.py` gerará por padrão um **relatório HTML rico e responsivo** (`--output report.html`), e caso a flag `--pdf report.pdf` seja passada, gerará também um **PDF multipágina consolidado**.

---

## 3. Estrutura de Diretórios Proposta

O novo pacote será alocado em `reconstruction/monitoring`:

```
reconstruction/monitoring/
├── CMakeLists.txt                         # Integração com ROOT, GaugiKernel e EDMs
├── README.md                              # Documentação de uso
├── python/
│   ├── __init__.py                        # Exportador do pacote
│   └── EgammaMonitoring.py                # Helper EgammaMonitoringCfg (sem kwargs)
├── src/
│   ├── LinkDef.h                          # ROOT Dictionary LinkDef
│   ├── EgammaMonitoringAlg.h              # Declaração do algoritmo Gaugi::Algorithm
│   └── EgammaMonitoringAlg.cxx            # Booking e preenchimento de histogramas
├── scripts/
│   └── reco_monitoring_diff.py            # Script CLI comparador (HTML + PDF)
└── tests/
    └── test_monitoring.py                 # Testes unitários do algoritmo e do diff
```

---

## 4. Design e Implementação do Algoritmo C++ (`EgammaMonitoringAlg`)

O `EgammaMonitoringAlg` herda de `Gaugi::Algorithm` e é responsável por gerenciar diretamente o arquivo ROOT de saída `expert_monitoring.root`, organizar a árvore de diretórios e preencher os histogramas a cada evento.

### 4.1. Header: `EgammaMonitoringAlg.h`

```cpp
#ifndef EgammaMonitoringAlg_h
#define EgammaMonitoringAlg_h

#include "GaugiKernel/Algorithm.h"
#include "GaugiKernel/StatusCode.h"
#include "GaugiKernel/EventContext.h"
#include "GaugiKernel/DataHandle.h"
#include "EventInfo/EventInfo.h"
#include "CaloCluster/CaloClusterContainer.h"
#include "Egamma/ElectronContainer.h"
#include "CaloRings/CaloRingsContainer.h"

#include "TFile.h"
#include "TH1F.h"
#include "TH2F.h"

#include <memory>
#include <string>
#include <map>

namespace Gaugi {

class EgammaMonitoringAlg : public Algorithm {
public:
  EgammaMonitoringAlg(std::string name);
  virtual ~EgammaMonitoringAlg();

  virtual StatusCode initialize() override;
  virtual StatusCode bookHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode pre_execute(SG::EventContext &ctx) const override;
  virtual StatusCode execute(SG::EventContext &ctx, const G4Step *step) const override;
  virtual StatusCode execute(SG::EventContext &ctx, int evt) const override;
  virtual StatusCode post_execute(SG::EventContext &ctx) const override;
  virtual StatusCode fillHistograms(SG::EventContext &ctx) const override;
  virtual StatusCode finalize() override;

private:
  // Propriedades configuráveis
  std::string m_outputFile;
  std::string m_histDir;
  std::string m_eventInfoKey;
  std::string m_clusterKey;
  std::string m_electronKey;
  std::string m_ringsKey;
  int m_outputLevel;

  // Arquivo de saída especialista
  mutable std::unique_ptr<TFile> m_file;

  // Mapa de histogramas indexados por "Subdiretorio/Nome"
  mutable std::map<std::string, TH1F*> m_hists1D;
  mutable std::map<std::string, TH2F*> m_hists2D;

  // Métodos auxiliares internos
  void book1D(const std::string &subDir, const std::string &name, const std::string &title, int nbins, float xmin, float xmax) const;
  void book2D(const std::string &subDir, const std::string &name, const std::string &title, int nbinsX, float xmin, float xmax, int nbinsY, float ymin, float ymax) const;
  void fill1D(const std::string &key, float value, float weight = 1.0) const;
  void fill2D(const std::string &key, float xval, float yval, float weight = 1.0) const;
};

} // namespace Gaugi

#endif
```

### 4.2. Implementação: `EgammaMonitoringAlg.cxx`

```cpp
#include "EgammaMonitoringAlg.h"
#include "TMath.h"
#include "G4SystemOfUnits.hh"

using namespace Gaugi;
using namespace SG;

EgammaMonitoringAlg::EgammaMonitoringAlg(std::string name)
  : IMsgService(name),
    Algorithm(),
    m_outputFile("expert_monitoring.root"),
    m_histDir("Expert-Monitoring"),
    m_eventInfoKey("Events"),
    m_clusterKey("Clusters"),
    m_electronKey("Electrons"),
    m_ringsKey("Rings"),
    m_outputLevel(1),
    m_file(nullptr)
{
  declareProperty("OutputFile",        m_outputFile);
  declareProperty("Directory",         m_histDir);
  declareProperty("InputEventInfoKey", m_eventInfoKey);
  declareProperty("InputClusterKey",   m_clusterKey);
  declareProperty("InputElectronKey",  m_electronKey);
  declareProperty("InputRingsKey",     m_ringsKey);
  declareProperty("OutputLevel",       m_outputLevel);
}

EgammaMonitoringAlg::~EgammaMonitoringAlg() {}

StatusCode EgammaMonitoringAlg::initialize()
{
  CHECK_INIT();
  setMsgLevel(m_outputLevel);

  // Abertura do arquivo ROOT especialista para gravação atômica
  m_file = std::make_unique<TFile>(m_outputFile.c_str(), "RECREATE");
  if (!m_file || m_file->IsZombie()) {
    MSG_FATAL("Falha ao criar o arquivo de monitoramento: " << m_outputFile);
    return StatusCode::FAILURE;
  }

  // 1. Variáveis Globais de Evento
  book1D("EventInfo", "avgmu", "Average Interactions per Crossing;\\langle\\mu\\rangle;Eventos", 100, 0.0, 100.0);
  book1D("EventInfo", "n_clusters", "Número de CaloClusters por Evento;N_{clusters};Eventos", 30, 0.0, 30.0);
  book1D("EventInfo", "n_electrons", "Número de Elétrons por Evento;N_{el};Eventos", 10, 0.0, 10.0);

  // 2. Cinemática
  book1D("Kinematics", "cl_et", "CaloCluster Transverse Energy;E_{T} [GeV];Clusters", 100, 0.0, 100.0);
  book1D("Kinematics", "cl_eta", "CaloCluster \\eta;\\eta;Clusters", 100, -5.0, 5.0);
  book1D("Kinematics", "cl_phi", "CaloCluster \\phi;\\phi [rad];Clusters", 64, -TMath::Pi(), TMath::Pi());
  book1D("Kinematics", "el_et", "Electron Transverse Energy;E_{T} [GeV];Elétrons", 100, 0.0, 100.0);
  book1D("Kinematics", "el_eta", "Electron \\eta;\\eta;Elétrons", 100, -5.0, 5.0);
  book1D("Kinematics", "el_phi", "Electron \\phi;\\phi [rad];Elétrons", 64, -TMath::Pi(), TMath::Pi());

  // 3. Shower Shapes (TrigEgammaMonitoring standard)
  book1D("ShowerShapes", "reta", "Shower Shape R_{\\eta};R_{\\eta} (E_{3\\times 7} / E_{7\\times 7});Clusters", 100, 0.4, 1.05);
  book1D("ShowerShapes", "rphi", "Shower Shape R_{\\phi};R_{\\phi} (E_{3\\times 3} / E_{3\\times 7});Clusters", 100, 0.4, 1.05);
  book1D("ShowerShapes", "weta2", "Lateral Shower Width w_{\\eta 2};w_{\\eta 2};Clusters", 100, 0.0, 0.035);
  book1D("ShowerShapes", "f1", "First Sampling Energy Fraction f_{1};f_{1};Clusters", 100, 0.0, 0.8);
  book1D("ShowerShapes", "f3", "Third Sampling Energy Fraction f_{3};f_{3};Clusters", 100, 0.0, 0.5);
  book1D("ShowerShapes", "eratio", "E_{ratio} (Strip Sampling 1);E_{ratio};Clusters", 100, 0.0, 1.05);
  book1D("ShowerShapes", "rhad", "Hadronic Leakage R_{had};R_{had} (E_{T}^{had} / E_{T}^{EM});Clusters", 100, -0.05, 0.35);

  // 4. Momentos de Cluster
  book1D("Moments", "secondLambda", "Second Lambda Moment;\\langle\\lambda^{2}\\rangle [mm^{2}];Clusters", 100, 0.0, 50000.0);
  book1D("Moments", "secondR", "Second Radial Moment;\\langle r^{2}\\rangle [mm^{2}];Clusters", 100, 0.0, 10000.0);
  book1D("Moments", "centerLambda", "Shower Depth Center \\lambda_{center};\\lambda_{center} [mm];Clusters", 100, 0.0, 1000.0);
  book1D("Moments", "fracMax", "Energy Fraction of Most Energetic Cell;f_{max};Clusters", 100, 0.0, 1.0);
  book1D("Moments", "lateral", "Lateral Shower Moment;Lateral Moment;Clusters", 100, 0.0, 1.0);
  book1D("Moments", "longitudinal", "Longitudinal Shower Moment;Longitudinal Moment;Clusters", 100, 0.0, 1.0);

  // 5. PID e Eficiências
  book1D("PID", "electron_pid_pass", "Electron Identification WP Decisions;Working Point;Candidatos", 4, 0.0, 4.0);
  m_hists1D["PID/electron_pid_pass"]->GetXaxis()->SetBinLabel(1, "VeryLoose");
  m_hists1D["PID/electron_pid_pass"]->GetXaxis()->SetBinLabel(2, "Loose");
  m_hists1D["PID/electron_pid_pass"]->GetXaxis()->SetBinLabel(3, "Medium");
  m_hists1D["PID/electron_pid_pass"]->GetXaxis()->SetBinLabel(4, "Tight");

  // 6. Correlações 2D
  book2D("Correlations", "reta_vs_eta", "R_{\\eta} vs \\eta;\\eta;R_{\\eta}", 50, -2.5, 2.5, 50, 0.5, 1.05);
  book2D("Correlations", "weta2_vs_et", "w_{\\eta 2} vs E_{T};E_{T} [GeV];w_{\\eta 2}", 50, 0.0, 100.0, 50, 0.0, 0.035);

  MSG_INFO("EgammaMonitoringAlg inicializado. Salvando histogramas em: " << m_outputFile);
  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringAlg::execute(SG::EventContext &ctx, int /*evt*/) const
{
  return fillHistograms(ctx);
}

StatusCode EgammaMonitoringAlg::fillHistograms(SG::EventContext &ctx) const
{
  // 1. Processar EventInfo
  SG::ReadHandle<xAOD::EventInfo> eventInfo(m_eventInfoKey, ctx);
  if (eventInfo.isValid()) {
    fill1D("EventInfo/avgmu", eventInfo->avgmu());
  }

  // 2. Processar CaloClusters
  SG::ReadHandle<xAOD::CaloClusterContainer> clusters(m_clusterKey, ctx);
  if (clusters.isValid()) {
    fill1D("EventInfo/n_clusters", static_clusters_size(*clusters));

    for (const auto *cl : *clusters) {
      if (!cl) continue;
      float et_gev = cl->et() / GeV;
      float eta = cl->eta();
      float phi = cl->phi();

      fill1D("Kinematics/cl_et", et_gev);
      fill1D("Kinematics/cl_eta", eta);
      fill1D("Kinematics/cl_phi", phi);

      // Shower Shapes
      fill1D("ShowerShapes/reta", cl->reta());
      fill1D("ShowerShapes/rphi", cl->rphi());
      fill1D("ShowerShapes/weta2", cl->weta2());
      fill1D("ShowerShapes/f1", cl->f1());
      fill1D("ShowerShapes/f3", cl->f3());
      fill1D("ShowerShapes/eratio", cl->eratio());
      fill1D("ShowerShapes/rhad", cl->rhad());

      // Moments
      fill1D("Moments/secondLambda", cl->secondLambda());
      fill1D("Moments/secondR", cl->secondR());
      fill1D("Moments/centerLambda", cl->centerLambda());
      fill1D("Moments/fracMax", cl->fracMax());
      fill1D("Moments/lateral", cl->lateral());
      fill1D("Moments/longitudinal", cl->longitudinal());

      // Correlations
      fill2D("Correlations/reta_vs_eta", eta, cl->reta());
      fill2D("Correlations/weta2_vs_et", et_gev, cl->weta2());
    }
  }

  // 3. Processar Electrons
  SG::ReadHandle<xAOD::ElectronContainer> electrons(m_electronKey, ctx);
  if (electrons.isValid()) {
    fill1D("EventInfo/n_electrons", electrons->size());

    for (const auto *el : *electrons) {
      if (!el) continue;
      fill1D("Kinematics/el_et", el->et() / GeV);
      fill1D("Kinematics/el_eta", el->eta());
      fill1D("Kinematics/el_phi", el->phi());

      if (el->isVeryLoose()) fill1D("PID/electron_pid_pass", 0.5);
      if (el->isLoose())     fill1D("PID/electron_pid_pass", 1.5);
      if (el->isMedium())    fill1D("PID/electron_pid_pass", 2.5);
      if (el->isTight())     fill1D("PID/electron_pid_pass", 3.5);
    }
  }

  return StatusCode::SUCCESS;
}

StatusCode EgammaMonitoringAlg::finalize()
{
  if (m_file && m_file->IsOpen()) {
    m_file->cd();
    m_file->Write();
    m_file->Close();
    MSG_INFO("Arquivo de monitoramento expert gravado com sucesso: " << m_outputFile);
  }
  return StatusCode::SUCCESS;
}

// Helpers de booking e filling
void EgammaMonitoringAlg::book1D(const std::string &subDir, const std::string &name, const std::string &title, int nbins, float xmin, float xmax) const
{
  std::string fullDir = m_histDir + "/" + subDir;
  m_file->mkdir(fullDir.c_str());
  m_file->cd(fullDir.c_str());

  std::string key = subDir + "/" + name;
  auto *h = new TH1F(name.c_str(), title.c_str(), nbins, xmin, xmax);
  h->SetDirectory(gDirectory);
  m_hists1D[key] = h;
}

void EgammaMonitoringAlg::book2D(const std::string &subDir, const std::string &name, const std::string &title, int nbinsX, float xmin, float xmax, int nbinsY, float ymin, float ymax) const
{
  std::string fullDir = m_histDir + "/" + subDir;
  m_file->mkdir(fullDir.c_str());
  m_file->cd(fullDir.c_str());

  std::string key = subDir + "/" + name;
  auto *h = new TH2F(name.c_str(), title.c_str(), nbinsX, xmin, xmax, nbinsY, ymin, ymax);
  h->SetDirectory(gDirectory);
  m_hists2D[key] = h;
}

void EgammaMonitoringAlg::fill1D(const std::string &key, float value, float weight) const
{
  auto it = m_hists1D.find(key);
  if (it != m_hists1D.end() && it->second) {
    it->second->Fill(value, weight);
  }
}

void EgammaMonitoringAlg::fill2D(const std::string &key, float xval, float yval, float weight) const
{
  auto it = m_hists2D.find(key);
  if (it != m_hists2D.end() && it->second) {
    it->second->Fill(xval, yval, weight);
  }
}

StatusCode EgammaMonitoringAlg::bookHistograms(SG::EventContext &/*ctx*/) const { return StatusCode::SUCCESS; }
StatusCode EgammaMonitoringAlg::pre_execute(SG::EventContext &/*ctx*/) const { return StatusCode::SUCCESS; }
StatusCode EgammaMonitoringAlg::execute(SG::EventContext &/*ctx*/, const G4Step * /*step*/) const { return StatusCode::SUCCESS; }
StatusCode EgammaMonitoringAlg::post_execute(SG::EventContext &/*ctx*/) const { return StatusCode::SUCCESS; }
```

---

## 5. Configuração Python (`EgammaMonitoring.py`)

Em estrita concordância com as diretrizes do projeto (**assinatura com parâmetros explícitos, sem `**kwargs`**):

```python
"""
EgammaMonitoring configuration helper for expert data quality validation.
"""

from typing import Optional
import ROOT
from GaugiKernel import Configurable, LoggingLevel

__all__ = ["EgammaMonitoringCfg", "EgammaMonitoring"]


def EgammaMonitoringCfg(
    name: str = "EgammaMonitoring",
    OutputFile: str = "expert_monitoring.root",
    Directory: str = "Expert-Monitoring",
    InputEventInfoKey: str = "Events",
    InputClusterKey: str = "Clusters",
    InputElectronKey: str = "Electrons",
    InputRingsKey: str = "Rings",
    OutputLevel: int = LoggingLevel.toC("INFO"),
) -> Configurable:
    """
    Configures and returns the EgammaMonitoringAlg algorithm instance.

    :param name: Instance name of the monitoring algorithm.
    :param OutputFile: Path of the generated ROOT file (default: expert_monitoring.root).
    :param Directory: Top-level TDirectory path inside the ROOT file.
    :param InputEventInfoKey: StoreGate key for xAOD::EventInfo.
    :param InputClusterKey: StoreGate key for xAOD::CaloClusterContainer.
    :param InputElectronKey: StoreGate key for xAOD::ElectronContainer.
    :param InputRingsKey: StoreGate key for xAOD::CaloRingsContainer.
    :param OutputLevel: Logging verbosity level.
    :return: Configured algorithm instance ready for ComponentAccumulator.
    """
    return Configurable(
        ROOT.Gaugi.EgammaMonitoringAlg,
        name,
        OutputFile=OutputFile,
        Directory=Directory,
        InputEventInfoKey=InputEventInfoKey,
        InputClusterKey=InputClusterKey,
        InputElectronKey=InputElectronKey,
        InputRingsKey=InputRingsKey,
        OutputLevel=OutputLevel,
    )


# Alias
EgammaMonitoring = EgammaMonitoringCfg
```

---

## 6. Integração na Sequência de Reconstrução (`reco_trf.py`)

Na etapa de reconstrução `.AOD`, o monitoramento é anexado após os algoritmos de física (`ElectronBuilder`, `CaloRingsBuilder` e `RootStreamAODMaker`) utilizando estritamente a convenção de acúmulo `acc += ...`:

```python
    # ... Algoritmos de reconstrução padrão ...
    acc += cluster
    acc += acc_rings
    acc += hypo
    acc += AOD

    # Anexa o algoritmo de monitoramento especialista
    if enable_monitoring:
        from EgammaMonitoring import EgammaMonitoringCfg
        mon = EgammaMonitoringCfg(
            "EgammaMonitoring",
            OutputFile=monitoring_output_file,  # ex: expert_monitoring.root
            InputClusterKey=recordable("Clusters"),
            InputElectronKey=recordable("Electrons"),
            InputEventInfoKey=recordable("Events"),
            InputRingsKey=recordable("Rings"),
            OutputLevel=outputLevel,
        )
        acc += mon
```

---

## 7. Script Comparador de Regressão e Validação Histograma-a-Histograma (`reco_monitoring_diff.py`)

O script recebe o arquivo recém-gerado (`expert_monitoring.root`) e o arquivo de referência homologado (`expert_monitoring_ref.root`).

### 7.1. Critérios de Avaliação Estatística
Para cada histograma correspondente presente em ambos os arquivos:
1. **Teste Kolmogorov-Smirnov (KS)**:
   - Mede discrepâncias na forma cumulativa da distribuição (sensível a deformações de cauda e resoluções).
   - $p_{\text{KS}} \ge 0.05 \longrightarrow$ **`PASS`** (verde)
   - $0.01 \le p_{\text{KS}} < 0.05 \longrightarrow$ **`WARNING`** (amarelo)
   - $p_{\text{KS}} < 0.01 \longrightarrow$ **`FAIL`** (vermelho)
2. **Teste Chi-Quadrado ($\chi^2/\text{ndf}$)**:
   - Mede divergências bin-a-bin em contagens absolutas e normalizadas.
3. **Desvios de Média ($\Delta\mu$) e Dispersão ($\Delta\text{RMS}$)**:
   - Pull da média: $z_{\mu} = \frac{|\mu_{\text{test}} - \mu_{\text{ref}}|}{\sqrt{\sigma_{\mu,\text{test}}^2 + \sigma_{\mu,\text{ref}}^2}}$.
   - Variação percentual de RMS: $\delta_{\text{RMS}} = \frac{|\text{RMS}_{\text{test}} - \text{RMS}_{\text{ref}}|}{\text{RMS}_{\text{ref}}} \times 100\%$.

### 7.2. Layout dos Gráficos Gerados
Cada variável comparada gera uma figura composta por dois painéis:
- **Painel Superior**: Histograma de Teste (vermelho com marcadores e barras de erro) sobreposto ao Histograma de Referência (azul/cinza hachurado com linha contínua).
- **Painel Inferior (Ratio & Pull)**: Razão ponto-a-ponto $\text{Test} / \text{Ref}$, com faixa sombreada de tolerância de $\pm 5\%$ e linha de referência em $1.0$.

### 7.3. Exemplo do Script de Comparação

```python
#!/usr/bin/env python3
"""
Script: reco_monitoring_diff.py
Compara dois arquivos expert_monitoring.root e gera relatório estatístico HTML e PDF.
"""

from pathlib import Path
import base64
import io
from typing_extensions import Annotated
import typer
import ROOT
import matplotlib.pyplot as plt
import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(help="Compara dois arquivos de monitoramento expert do Lorenzetti.")


def compare_histograms(h_test, h_ref):
    """Executa testes estatísticos entre dois histogramas ROOT."""
    ks_pvalue = h_test.KolmogorovTest(h_ref)
    chi2_pvalue = h_test.Chi2Test(h_ref, "UW")
    
    mean_test, mean_ref = h_test.GetMean(), h_ref.GetMean()
    rms_test, rms_ref = h_test.GetRMS(), h_ref.GetRMS()
    
    status = "PASS"
    if ks_pvalue < 0.01 or chi2_pvalue < 0.001:
        status = "FAIL"
    elif ks_pvalue < 0.05 or chi2_pvalue < 0.01:
        status = "WARNING"

    return {
        "status": status,
        "ks_pvalue": ks_pvalue,
        "chi2_pvalue": chi2_pvalue,
        "mean_test": mean_test,
        "mean_ref": mean_ref,
        "rms_test": rms_test,
        "rms_ref": rms_ref,
    }


def render_plot(h_test, h_ref, title):
    """Gera plot matplotlib com painel superior (distribuição) e inferior (ratio)."""
    fig, (ax_main, ax_ratio) = plt.subplots(
        2, 1, figsize=(7, 6), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
    )

    nbins = h_test.GetNbinsX()
    bins = [h_test.GetBinLowEdge(i) for i in range(1, nbins + 2)]
    centers = [h_test.GetBinCenter(i) for i in range(1, nbins + 1)]
    
    vals_test = [h_test.GetBinContent(i) for i in range(1, nbins + 1)]
    errs_test = [h_test.GetBinError(i) for i in range(1, nbins + 1)]
    
    vals_ref = [h_ref.GetBinContent(i) for i in range(1, nbins + 1)]
    errs_ref = [h_ref.GetBinError(i) for i in range(1, nbins + 1)]

    # Painel Principal
    ax_main.step(bins[:-1], vals_ref, where="post", color="#1f77b4", label="Referência", lw=1.5)
    ax_main.fill_between(bins[:-1], vals_ref, step="post", alpha=0.15, color="#1f77b4")
    ax_main.errorbar(centers, vals_test, yerr=errs_test, fmt="o", color="#d62728", label="Atual", markersize=4, capsize=2)
    ax_main.set_ylabel("Contagens / Bin")
    ax_main.set_title(title, fontsize=11, fontweight="bold")
    ax_main.legend(frameon=False)
    ax_main.grid(True, linestyle=":", alpha=0.6)

    # Painel de Ratio
    ratios = []
    ratio_errs = []
    for vt, vr, et in zip(vals_test, vals_ref, errs_test):
        if vr > 0:
            ratios.append(vt / vr)
            ratio_errs.append(et / vr)
        else:
            ratios.append(np.nan)
            ratio_errs.append(0.0)

    ax_ratio.errorbar(centers, ratios, yerr=ratio_errs, fmt="o", color="black", markersize=3)
    ax_ratio.axhline(1.0, color="gray", linestyle="--", lw=1)
    ax_ratio.axhspan(0.95, 1.05, color="green", alpha=0.15)
    ax_ratio.set_ylim(0.7, 1.3)
    ax_ratio.set_ylabel("Atual / Ref")
    ax_ratio.set_xlabel(h_test.GetXaxis().GetTitle() or "Grandeza")
    ax_ratio.grid(True, linestyle=":", alpha=0.6)

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


@app.command()
def main(
    test_file: Annotated[Path, typer.Option("-t", "--test-file", help="Arquivo expert_monitoring.root atual")],
    ref_file: Annotated[Path, typer.Option("-r", "--ref-file", help="Arquivo expert_monitoring_ref.root de referência")],
    output_html: Annotated[Path, typer.Option("-o", "--output-html", help="Caminho do relatório HTML de saída")] = Path("monitoring_report.html"),
    output_pdf: Annotated[Optional[Path], typer.Option("--pdf", help="Caminho opcional do relatório em PDF")] = None,
):
    """Executa a validação cruzada entre arquivo atual e referência."""
    f_test = ROOT.TFile.Open(str(test_file))
    f_ref = ROOT.TFile.Open(str(ref_file))

    if not f_test or not f_ref:
        console.print("[red]Erro ao abrir os arquivos ROOT de entrada![/red]")
        raise typer.Exit(code=1)

    table = Table(title="Resultados da Validação de Qualidade (DQM)")
    table.add_column("Variável", justify="left")
    table.add_column("Status", justify="center")
    table.add_column("p-value KS", justify="right")
    table.add_column("p-value Chi2", justify="right")
    table.add_column("Média Atual (Ref)", justify="right")

    results = []

    # Leitura recursiva de diretórios
    for key in f_test.GetListOfKeys():
        obj = key.ReadObj()
        if obj.InheritsFrom("TDirectory"):
            dir_name = obj.GetName()
            d_test = f_test.Get(dir_name)
            d_ref = f_ref.Get(dir_name)
            if not d_ref:
                continue

            for hkey in d_test.GetListOfKeys():
                hname = hkey.GetName()
                h_test = d_test.Get(hname)
                h_ref = d_ref.Get(hname)

                if h_test and h_ref and h_test.InheritsFrom("TH1"):
                    metrics = compare_histograms(h_test, h_ref)
                    plot_b64 = render_plot(h_test, h_ref, f"{dir_name}/{hname}")
                    
                    full_name = f"{dir_name}/{hname}"
                    metrics["name"] = full_name
                    metrics["plot_b64"] = plot_b64
                    results.append(metrics)

                    color = "green" if metrics["status"] == "PASS" else ("yellow" if metrics["status"] == "WARNING" else "red")
                    table.add_row(
                        full_name,
                        f"[{color}]{metrics['status']}[/{color}]",
                        f"{metrics['ks_pvalue']:.4f}",
                        f"{metrics['chi2_pvalue']:.4f}",
                        f"{metrics['mean_test']:.3f} ({metrics['mean_ref']:.3f})"
                    )

    console.print(table)

    # Geração do HTML Standalone
    html_content = generate_html_report(results, str(test_file), str(ref_file))
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    console.print(f"[green]Relatório HTML gerado em: {output_html}[/green]")


def generate_html_report(results, test_file, ref_file):
    """Gera template HTML moderno, com cards, filtros de busca e badges de status."""
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warn_count = sum(1 for r in results if r["status"] == "WARNING")
    fail_count = sum(1 for r in results if r["status"] == "FAIL")

    cards_html = ""
    for r in results:
        badge_class = r["status"].lower()
        cards_html += f"""
        <div class="card {badge_class}" data-status="{r['status']}" data-name="{r['name']}">
            <div class="card-header">
                <span class="card-title">{r['name']}</span>
                <span class="badge {badge_class}">{r['status']}</span>
            </div>
            <div class="card-body">
                <p><strong>KS p-value:</strong> {r['ks_pvalue']:.4e} | <strong>Chi2 p-value:</strong> {r['chi2_pvalue']:.4e}</p>
                <p><strong>Média:</strong> Atual = {r['mean_test']:.4f}, Ref = {r['mean_ref']:.4f}</p>
                <img src="data:image/png;base64,{r['plot_b64']}" alt="{r['name']}" class="plot-img"/>
            </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Lorenzetti Data Quality Monitoring Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f8f9fa; color: #333; margin: 0; padding: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 25px; border-radius: 8px; margin-bottom: 20px; }}
        .summary {{ display: flex; gap: 15px; margin-bottom: 20px; }}
        .summary-card {{ flex: 1; padding: 15px; border-radius: 8px; text-align: center; color: white; font-weight: bold; font-size: 1.2em; }}
        .pass-bg {{ background: #27ae60; }}
        .warn-bg {{ background: #f39c12; }}
        .fail-bg {{ background: #e74c3c; }}
        .controls {{ display: flex; gap: 15px; margin-bottom: 20px; }}
        .controls input, .controls select {{ padding: 10px; font-size: 1em; border-radius: 6px; border: 1px solid #ccc; }}
        .cards-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(480px, 1fr)); gap: 20px; }}
        .card {{ background: white; border-radius: 8px; border-left: 6px solid #ccc; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }}
        .card.pass {{ border-left-color: #27ae60; }}
        .card.warning {{ border-left-color: #f39c12; }}
        .card.fail {{ border-left-color: #e74c3c; }}
        .card-header {{ padding: 12px 16px; background: #ecf0f1; display: flex; justify-content: space-between; align-items: center; }}
        .card-title {{ font-weight: bold; font-size: 1.05em; }}
        .badge {{ padding: 4px 10px; border-radius: 12px; color: white; font-size: 0.8em; text-transform: uppercase; font-weight: bold; }}
        .badge.pass {{ background: #27ae60; }}
        .badge.warning {{ background: #f39c12; }}
        .badge.fail {{ background: #e74c3c; }}
        .card-body {{ padding: 15px; }}
        .plot-img {{ width: 100%; border-radius: 4px; border: 1px solid #eee; margin-top: 10px; }}
    </style>
    <script>
        function filterCards() {{
            const filterText = document.getElementById("searchBox").value.toLowerCase();
            const filterStatus = document.getElementById("statusFilter").value;
            const cards = document.querySelectorAll(".card");
            cards.forEach(card => {{
                const name = card.getAttribute("data-name").toLowerCase();
                const status = card.getAttribute("data-status");
                const matchName = name.includes(filterText);
                const matchStatus = (filterStatus === "ALL" || status === filterStatus);
                card.style.display = (matchName && matchStatus) ? "block" : "none";
            }});
        }}
    </script>
</head>
<body>
    <div class="header">
        <h1>Lorenzetti - Relatório de Monitoramento Especialista (DQM)</h1>
        <p><strong>Arquivo de Teste:</strong> {test_file} | <strong>Referência:</strong> {ref_file}</p>
    </div>
    <div class="summary">
        <div class="summary-card pass-bg">PASS: {pass_count}</div>
        <div class="summary-card warn-bg">WARNING: {warn_count}</div>
        <div class="summary-card fail-bg">FAIL: {fail_count}</div>
    </div>
    <div class="controls">
        <input type="text" id="searchBox" placeholder="Filtrar por nome do histograma..." onkeyup="filterCards()" style="flex: 2;"/>
        <select id="statusFilter" onchange="filterCards()" style="flex: 1;">
            <option value="ALL">Todos os Status</option>
            <option value="FAIL">Apenas Falhas (FAIL)</option>
            <option value="WARNING">Apenas Alertas (WARNING)</option>
            <option value="PASS">Apenas Aprovados (PASS)</option>
        </select>
    </div>
    <div class="cards-grid">
        {cards_html}
    </div>
</body>
</html>
"""

if __name__ == "__main__":
    app()
```

---

## 8. Integração com o CMake e Build System

1. Em `reconstruction/monitoring/CMakeLists.txt`:
```cmake
file(GLOB SOURCES src/*.cxx)
file(GLOB_RECURSE HEADERS src/EgammaMonitoringAlg.h)

include_directories(${CMAKE_SOURCE_DIR} ${ROOT_INCLUDE_DIRS} ${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../events/EventInfo)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../events/CaloCluster)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../events/CaloCell)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../events/Egamma)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../events/CaloRings)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../kernel/GaugiKernel)
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../../kernel/G4Kernel)

ROOT_GENERATE_DICTIONARY(MonitoringDict ${HEADERS} LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/src/LinkDef.h MODULE Monitoring)

add_library(Monitoring OBJECT ${SOURCES} MonitoringDict.cxx)
install(FILES ${HEADERS} DESTINATION Monitoring)

gaugi_install_python_modules(${CMAKE_CURRENT_SOURCE_DIR}/python Monitoring)
```

2. No `CMakeLists.txt` raiz:
   - Adicionar `add_subdirectory(reconstruction/monitoring)`
   - Adicionar `$<TARGET_OBJECTS:Monitoring>` na lista de objetos de `add_library(lorenzetti SHARED ...)`.

---

## 9. Plano de Ação para Implementação

| Etapa | Ação | Entregáveis |
| :--- | :--- | :--- |
| **Fase 1** | Criação do pacote `reconstruction/monitoring` | `CMakeLists.txt`, `LinkDef.h`, `EgammaMonitoringAlg.h`, `EgammaMonitoringAlg.cxx` |
| **Fase 2** | Módulo de Configuração Python | `EgammaMonitoring.py` com `EgammaMonitoringCfg` (sem `kwargs`) |
| **Fase 3** | Script CLI de Validação de Regressão | `reco_monitoring_diff.py` com suporte a testes KS, $\chi^2$, relatórios HTML e PDF |
| **Fase 4** | Testes Unitários e Integração AOD | Testes unitários com mock/eventos sintéticos e integração em `reco_trf.py` |
