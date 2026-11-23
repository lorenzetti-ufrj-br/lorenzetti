# Proposta Arquitetural: Reestruturação do Detector ATLAS (v1 e v2)

> **Documento de Decisão Técnica e Proposta de Implementação**  
> **Status:** Em Revisão / Proposta Detalhada com Análise de Flags e Exemplos de Código  
> **Objetivo:** Estabelecer a coexistência de `v1` (estável, imperativo atual) e `v2` (declarativo, orientado a JSON) no subsistema ATLAS em Python e C++, espelhando o sucesso arquitetural obtido no GALTIC e permitindo uma migração progressiva, limpa e segura.

---

## 1. Sumário Executivo e Motivação

Após a refatoração do subsistema **GALTIC**, obteve-se um ganho drástico de legibilidade, desempenho e manutenibilidade:
1. O orquestrador Python foi consolidado e desacoplado dos detalhes imperativos de baixo nível.
2. A geometria foi formalizada em um arquivo declarativo canônico (`json`), eliminando 34 chamadas RPC via PyROOT.
3. O C++ passou a realizar o parsing nativo em ~1 ms através de `LoadGeometryFile`.
4. Obteve-se integração nativa imediata com o `visualizer` (WebGL 3D interativo e desenhos técnicos em PDF 100% vetoriais).

Atualmente, o detector **ATLAS** em `geometry/ATLAS`:
- Possui um orquestrador Python com centenas de linhas e 10 módulos de detectores em `detectors/` (`ECAL.py`, `TILE.py`, `EMEC.py`, `HEC.py`, `FCAL.py`, `DeadMaterials.py`, etc.).
- Carrega mais de 20 flags booleanas (`AtlasGeometryFlags`) cujo propósito original era alternar, peça por peça, entre um modelo "genérico/simplificado" (antigo toy detector) e o detector real do ATLAS.
- Realiza dezenas de chamadas imperativas via PyROOT chamando `AddVolume`, `SetPolycone`, `AddMixture`, etc.
- No C++, a classe atual é `DetectorConstruction_v2`, que contém a lógica do ATLAS (incluindo o suporte a dumps SQLite GeoModel do Run 4).

### O Ponto de Inflexão Arquitetural
Com o isolamento completo do modelo simplificado no **GALTIC**, **o detector ATLAS não precisa mais de flags para decidir se ele é ou não o ATLAS**. O ATLAS em `v2` nasce sendo 100% a geometria realista do ATLAS, definida de forma declarativa no arquivo canônico `atlas_geometry.json`.

---

## 2. Análise Crítica de Todas as Flags do Modelo Atual (`v1`) e Diagnóstico para o `v2`

No modelo atual (`AtlasGeometryFlags.py`), existem 24 flags e parâmetros de arquivo. Abaixo analisamos a origem de cada uma e sua necessidade real no novo modelo `v2`:

### 2.1. Flags de Subdetectores Calorimétricos

| Flag Atual (`v1`) | Finalidade Original no Modelo Antigo | Necessária no `v2`? | Justificativa Técnica para o `v2` |
| :--- | :--- | :---: | :--- |
| `TileAtlasGeometry` | Se `False`, constrói um Tile genérico com cilindros concêntricos. Se `True`, usa o período ATLAS (14 mm aço, 3 mm telha). | **NÃO** | O modelo genérico agora é o **GALTIC**. No ATLAS `v2`, o Tile é *sempre* construído com a geometria periódica real do ATLAS definida no JSON. |
| `TileAtlasCells` | Se `True`, mapeia as células nominais A1-A16, BC1-BC8, D0-D6 do ATLAS em vez de uma grade $\Delta\eta \times \Delta\phi$ genérica. | **NÃO** | No ATLAS `v2`, todas as células nominais já estão mapeadas no bloco `readout` de cada amostragem no `atlas_geometry.json`. |
| `TileAtlasItc` | Insere o plug de alumínio e cabos do ITC (Intermediate Tile Calorimeter). | **NÃO** | Em `v2`, o bloco ITC é formalizado diretamente como volume passivo permanente no JSON. |
| `TileAtlasGap` | Ativa cintiladores de crack E1-E4 e células ativas C10/D4. | **NÃO** | Em `v2`, as amostragens do gap/crack são camadas padrão registradas no JSON. |
| `TileAtlasRun4` | Desloca o barril estendido e crack nas coordenadas da simulação do Run 4 (+40 mm lado A, -30 mm C). | **NÃO** | Em `v2`, as coordenadas canônicas já incorporam o posicionamento oficial do ATLAS. |
| `AtlasEmb` | Se `False`, usa chumbo genérico. Se `True`, usa composição acordeão do ATLAS (1.53 mm chumbo abaixo de $\|\eta\|=0.8$, 1.13 mm acima). | **NÃO** | Em `v2`, as camadas do EMB já possuem as espessuras e materiais oficiais do ATLAS no JSON. |
| `AtlasEmbCells` | Faz o EMB terminar em $\|z\| = 3165\text{ mm}$ com granularidade de tiras finas ($\Delta\eta = 0.003125$). | **NÃO** | Em `v2`, a granularidade fina de tiras e o comprimento de 3165 mm são propriedades nativas das camadas EMB1-3. |
| `AtlasEmec` | Se `False`, EMEC em anéis simples. Se `True`, duas rodas concêntricas acordeão do ATLAS ($1.375 < \|\eta\| < 3.2$). | **NÃO** | Em `v2`, o EMEC é modelado com as dimensões radiais e limites exatos das duas rodas no JSON. |
| `AtlasEmecArgonFraction` | Ajusta a fração de LAr nas faixas radiais do acordeão do end-cap. | **NÃO** | O valor nominal de fração de árgon já vem pré-calculado nas densidades e espessuras do JSON. |
| `AtlasHec` | Se `False`, HEC genérico. Se `True`, 4 amostragens com placas de cobre (25/50 mm) e células do ATLAS. | **NÃO** | Em `v2`, HEC0-HEC3 são definidos no JSON diretamente com suas placas de cobre de 25 mm e 50 mm. |
| `AtlasFcal` | Insere o calorímetro para frente (FCal) como meio homogêneo cobre/tungstênio + LAr. | **NÃO** | Em `v2`, o FCal é uma amostragem canônica definida no JSON. |
| `AtlasFcalCells` | Constrói os módulos tubulares detalhados do FCal com eletrodos lidos de arquivo CSV. | **Opcional** | Em `v2`, a geometria dos 3 módulos FCal reside no JSON. O mapeamento fino de eletrodos pode ser ativado caso se use a simulação detalhada. |

### 2.2. Flags de Materiais Passivos, Criostatos e Blindagens

| Flag Atual (`v1`) | Finalidade Original no Modelo Antigo | Necessária no `v2`? | Justificativa Técnica para o `v2` |
| :--- | :--- | :---: | :--- |
| `AtlasMaterialInFront` | Injeta o solenoide ($0.66\ X_0$) e a parede do criostato ($0.76\ X_0$) na frente do barril eletromagnético. | **NÃO** | Em `v2`, o solenoide e as paredes frontais do criostato são volumes passivos explícitos (`dead_materials`) no JSON. |
| `AtlasEndcapCryostat` | Vasos de alumínio quente (20 mm) e frio (35 mm) dos criostatos do end-cap com LAr morto. | **NÃO** | Em `v2`, já integram a lista canônica de `dead_materials` do JSON. |
| `AtlasBarrelCryostat` | Vasos externos de alumínio (30 mm) do criostato do barril e LAr inativo. | **NÃO** | Em `v2`, já constam no JSON como materiais passivos do barril. |
| `AtlasForwardShielding` | Blindagens externas JD/JT/JF em polietileno borado e toroides. | **NÃO** | Podem ser incluídas diretamente no JSON ou desabilitadas se não houver interesse em rastrear fora do calorímetro. |
| `AtlasBarrelGapServices` | Serviços de cabos e eletrônica no gap entre barril e barril estendido. | **NÃO** | Formalizados como volumes passivos no JSON. |

### 2.3. Flags Operacionais, de Física e Simulação no Geant4

| Flag Atual (`v1`) | Finalidade Técnica | Necessária no `v2`? | Comportamento no `v2` |
| :--- | :--- | :---: | :--- |
| `UseMagneticField` | Ativa campo magnético global de 2 T no Geant4. | **SIM** | Mantida como propriedade padrão de simulação. |
| `UseSolenoidField` | Restringe o campo magnético de 2 T apenas ao interior do solenoide ($R < 1.23\text{ m}, \|z\| < 2.9\text{ m}$). | **SIM** | Mantida como propriedade fundamental do ATLAS. |
| `CutOnPhi` | Aplica corte em cunha azimutal (usado para depuração visual e testes rápidos). | **SIM** | Mantida como propriedade para o `visualizer` e testes rápidos. |
| `AtlasFcalFrozenShowers` | Ativa o modelo de Fast Simulation com bibliotecas de chuveiros congelados no FCAL (`MC23_v1`). | **SIM (Opcional)** | Flag de otimização de física Geant4 (não afeta os volumes do JSON). |
| `AtlasRun4Geometry` / `AtlasRun4` | Caminho para banco SQLite do GeoModel para importar o Inner Tracker (ITk), HGTD e beam pipe. | **SIM (Opcional)** | Mantida como recurso avançado para importar volumes do ITk via SQLite sem interferir no calorímetro do JSON. |
| `AtlasFieldMap` | Mapa de campo 3D detalhado do ATLAS. | **SIM (Opcional)** | Parâmetro do serviço de campo magnético. |

---

## 3. Síntese: As Flags do `v2`

No **`ATLAS.v2`**, as mais de 20 flags de "ativa/desativa detector ATLAS" são **totalmente eliminadas**.  
Restam apenas parâmetros operacionais de simulação Geant4:

```python
class AtlasDetectorConstruction(Configurable):
    def __init__(
        self,
        name: str = "ATLAS",
        geometry_file: Optional[str] = None,       # Caminho para atlas_geometry.json
        UseMagneticField: bool = False,             # Campo magnético 2T uniforme
        UseSolenoidField: bool = True,              # Campo 2T no solenoide central (padrão ATLAS)
        CutOnPhi: bool = False,                     # Corte azimutal para visualização
        FastSimulation: bool = False,               # Chuveiros congelados no FCAL
        AtlasRun4Geometry: str = "",                # SQLite opcional para ITk/HGTD
    ) -> None:
        ...
```

Toda a física das 24 camadas, criostatos, eletrodos e materiais passivos reside declarativamente no arquivo:
[`geometry/ATLAS/data/atlas_geometry.json`](file:///home/joao.pinto/git_repos/lorenzetti/geometry/ATLAS/data/atlas_geometry.json).

---

## 4. Nova Estrutura de Diretórios (`geometry/ATLAS/`)

```
geometry/ATLAS/
├── CMakeLists.txt                         # Compila DetectorConstruction_v1 e DetectorConstruction_v2
├── README.md                              # Documentação atualizada do subsistema ATLAS
├── data/
│   ├── atlas_geometry.json                # [NOVO] Especificação canônica declarativa do ATLAS para v2
│   ├── pulseLar.dat                       # Calibração de resposta de pulso LAr
│   ├── pulseTile.dat                      # Calibração de resposta de pulso Tile
│   ├── LArFCalElectrodes-06.csv           # Parâmetros de eletrodos FCal
│   ├── EmecTables-ATLAS-P2-RUN4-01-01-00.csv
│   ├── HVEMECMap_v02.dat
│   └── LArG4ShowerLibData/
│
├── ATLAS/                                 # Headers C++ públicos
│   ├── DetectorConstruction_v1.h         # [C++ v1] Motor atual imperativo com AddVolume e GeoModel Run 4
│   ├── DetectorConstruction_v2.h         # [C++ v2] Novo motor declarativo rápido orientado a JSON
│   ├── json.hpp                          # nlohmann/json para parsing nativo em C++
│   ├── AtlasGeoModelImport.h              # Suporte a GeoModel do Run 4
│   └── ... (demais headers de suporte: LArWheelCalculator, FCal, BirksLaw, etc.)
│
├── src/                                   # Implementação C++
│   ├── DetectorConstruction_v1.cxx       # Implementação imperativa atual com AddVolume (ex-v2)
│   ├── DetectorConstruction_v2.cxx       # [NOVO] Implementação baseada em LoadGeometryFile
│   ├── LinkDef.h                         # Exporta DetectorConstruction_v1+ e DetectorConstruction_v2+
│   └── ... (demais arquivos de física e cálculo de carga)
│
├── python/                                # Pacote Python ATLAS
│   ├── __init__.py                        # Ponto único de entrada, exporta v1, v2 e flags
│   ├── AtlasGeometryFlags.py              # Container de flags do ATLAS (para v1)
│   │
│   ├── v1/                                # [CÓDIGO ATUAL COMPLETO MIGRADO]
│   │   ├── __init__.py                    # Exporta AtlasDetectorConstruction (v1)
│   │   ├── DetectorConstruction.py        # Orquestrador v1 (instancia ROOT.DetectorConstruction_v1)
│   │   ├── detectors/                     # Módulos de construção imperativa atuais
│   │   │   ├── __init__.py
│   │   │   ├── ECAL.py
│   │   │   ├── TILE.py
│   │   │   ├── EMEC.py
│   │   │   ├── HEC.py
│   │   │   ├── FCAL.py
│   │   │   ├── AtlasFCal.py
│   │   │   ├── AtlasBarrelFront.py
│   │   │   ├── AtlasBarrelCryostat.py
│   │   │   ├── AtlasRun4.py
│   │   │   └── DeadMaterials.py
│   │   └── legacy/                        # Módulos legados do ATLAS
│   │       ├── __init__.py
│   │       ├── Calorimeter.py
│   │       ├── PhysicalVolume.py
│   │       ├── SensitiveDetector.py
│   │       └── Tracking.py
│   │
│   └── v2/                                # [NOVO MÓDULO PYTHONICO ORIENTADO A JSON]
│       ├── __init__.py                    # Exporta AtlasDetectorConstruction (v2) e builders
│       ├── Layer.py                       # CaloSamplingLayer, DeadMaterialVolume e Fluent Builders
│       ├── AtlasCfg.py                    # Registro consolidado de todas as amostragens do ATLAS
│       └── DetectorConstruction.py        # Orquestrador v2 (load, save, compile via JSON)
│
└── scripts/
    ├── generate_atlas_geometry.py         # [NOVO] Script CLI para gerar/inspecionar atlas_geometry.json
    └── ... (scripts de validação de eletrodos, dumpgeo e tabelas EMEC)
```

---

## 5. Exemplos de Código: Como Ficará o Lado Python no `v2`

### 5.1. Fluent Builders Especializados (`geometry/ATLAS/python/v2/Layer.py`)

A criação e manipulação programática de volumes passa a utilizar classes limpas com validação de tipos:

```python
"""
Layer.py - Definições de camadas e builders para o ATLAS v2.
"""
from typing import Any, Dict, List, Optional
from enum import IntEnum
from CaloCell.CaloDefs import CaloSampling

class Plates(IntEnum):
    Horizontal = 0
    Vertical = 1
    Polycone = 2

class CaloSamplingLayer:
    """Representa uma camada de amostragem ativa do calorímetro ATLAS."""
    def __init__(
        self,
        name: str,
        sampling: int,
        detector: int,
        rmin: float,
        rmax: float,
        zmin: float,
        zmax: float,
        nof_layers: int,
        absorber_material: str,
        gap_material: str,
        absorber_thickness: float,
        gap_thickness: float,
        delta_eta: float,
        delta_phi: float,
        noise_mev: float,
        pulse_file: str,
        plates: Plates = Plates.Horizontal,
        ...
    ) -> None:
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Serialização para o formato JSON canônico."""
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CaloSamplingLayer":
        """Reconstrução exata a partir de dicionário JSON."""
        ...
```

Exemplo do builder fluente para o Barril Eletromagnético (EMB):
```python
class AtlasEmbBuilder:
    """Builder fluente para camadas de amostragem do EMB do ATLAS."""
    def __init__(self, name: str, sampling: CaloSampling) -> None:
        self._name = name
        self._sampling = int(sampling)
        self._rmin = 0.0
        self._rmax = 0.0
        self._z_size = 6330.0
        self._lead_th = 1.53
        self._lar_gap = 4.5
        self._n_layers = 16
        self._delta_eta = 0.025
        self._delta_phi = 0.02454
        self._noise = 40.0
        self._pulse_file = "pulseLar.dat"

    def radii(self, rmin: float, rmax: float) -> "AtlasEmbBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        return self

    def accordion(self, lead_th: float, lar_gap: float, n_layers: int) -> "AtlasEmbBuilder":
        self._lead_th = float(lead_th)
        self._lar_gap = float(lar_gap)
        self._n_layers = int(n_layers)
        return self

    def granularity(self, d_eta: float, d_phi: float) -> "AtlasEmbBuilder":
        self._delta_eta = float(d_eta)
        self._delta_phi = float(d_phi)
        return self

    def electronics(self, noise_mev: float, pulse_file: str) -> "AtlasEmbBuilder":
        self._noise = float(noise_mev)
        self._pulse_file = str(pulse_file)
        return self

    def build(self) -> CaloSamplingLayer:
        return CaloSamplingLayer(
            name=self._name,
            sampling=self._sampling,
            detector=2, # LAr
            rmin=self._rmin,
            rmax=self._rmax,
            zmin=-self._z_size / 2.0,
            zmax=self._z_size / 2.0,
            nof_layers=self._n_layers,
            absorber_material="G4_Pb",
            gap_material="liquidArgon",
            absorber_thickness=self._lead_th,
            gap_thickness=self._lar_gap,
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_mev=self._noise,
            pulse_file=self._pulse_file,
            plates=Plates.Horizontal,
        )
```

Exemplo do builder fluente para o Calorímetro Hadronico de Telhas (Tile):
```python
class AtlasTileBuilder:
    """Builder fluente para camadas de amostragem do Tile do ATLAS."""
    def __init__(self, name: str, sampling: CaloSampling) -> None:
        self._name = name
        self._sampling = int(sampling)
        self._steel_th = 14.0
        self._tile_th = 3.0
        self._wrap_th = 1.0

    def radii(self, rmin: float, rmax: float) -> "AtlasTileBuilder":
        self._rmin = float(rmin)
        self._rmax = float(rmax)
        return self

    def z_span(self, zmin: float, zmax: float) -> "AtlasTileBuilder":
        self._zmin = float(zmin)
        self._zmax = float(zmax)
        return self

    def cells(self, d_eta: float, d_phi: float) -> "AtlasTileBuilder":
        self._delta_eta = float(d_eta)
        self._delta_phi = float(d_phi)
        return self

    def build(self) -> CaloSamplingLayer:
        return CaloSamplingLayer(
            name=self._name,
            sampling=self._sampling,
            detector=1, # Tile
            rmin=self._rmin,
            rmax=self._rmax,
            zmin=self._zmin,
            zmax=self._zmax,
            nof_layers=int((self._zmax - self._zmin) / (self._steel_th + self._tile_th + self._wrap_th)),
            absorber_material="G4_Fe",
            gap_material="Scintillator",
            absorber_thickness=self._steel_th,
            gap_thickness=self._tile_th,
            delta_eta=self._delta_eta,
            delta_phi=self._delta_phi,
            noise_mev=30.0,
            pulse_file="pulseTile.dat",
            plates=Plates.Vertical,
        )
```

---

### 5.2. Configuração Centralizada (`geometry/ATLAS/python/v2/AtlasCfg.py`)

Substitui os 10 arquivos dispersos em `detectors/` por uma especificação declarativa imutável e concisa:

```python
"""
AtlasCfg.py - Registro consolidado das 24 amostragens canônicas do ATLAS e seus materiais passivos.
"""
from typing import List
from CaloCell.CaloDefs import CaloSampling
from ATLAS.v2.Layer import (
    CaloSamplingLayer,
    DeadMaterialVolume,
    AtlasEmbBuilder,
    AtlasTileBuilder,
    AtlasEmecBuilder,
    AtlasHecBuilder,
    AtlasDeadMaterialBuilder,
)

def getAtlasAllSamplings() -> List[CaloSamplingLayer]:
    """Retorna todas as 24 camadas de amostragem ativas do ATLAS com parâmetros oficiais."""
    return [
        # Presampler Barril (PSB)
        AtlasEmbBuilder("LAr::PSB", CaloSampling.PreSamplerB)
        .radii(1430.0, 1441.0)
        .accordion(lead_th=0.01, lar_gap=11.0, n_layers=1)
        .granularity(d_eta=0.025, d_phi=0.09817)
        .electronics(noise_mev=90.0, pulse_file="pulseLar.dat")
        .build(),

        # Barril EM: Amostragens 1, 2 e 3
        AtlasEmbBuilder("LAr::EMB1", CaloSampling.EMB1)
        .radii(1500.0, 1580.0)
        .accordion(lead_th=1.53, lar_gap=4.5, n_layers=16)
        .granularity(d_eta=0.003125, d_phi=0.02454) # Tiras finas
        .electronics(noise_mev=40.0, pulse_file="pulseLar.dat")
        .build(),

        AtlasEmbBuilder("LAr::EMB2", CaloSampling.EMB2)
        .radii(1590.0, 1860.0)
        .accordion(lead_th=1.53, lar_gap=4.5, n_layers=16)
        .granularity(d_eta=0.025, d_phi=0.02454)
        .electronics(noise_mev=30.0, pulse_file="pulseLar.dat")
        .build(),

        AtlasEmbBuilder("LAr::EMB3", CaloSampling.EMB3)
        .radii(1870.0, 1960.0)
        .accordion(lead_th=1.13, lar_gap=4.5, n_layers=16)
        .granularity(d_eta=0.05, d_phi=0.02454)
        .electronics(noise_mev=25.0, pulse_file="pulseLar.dat")
        .build(),

        # Tile Barril: Amostragens 0, 1 e 2
        AtlasTileBuilder("Tile::Bar0", CaloSampling.TileBar0)
        .radii(2280.0, 2600.0)
        .z_span(-2820.0, 2820.0)
        .cells(d_eta=0.1, d_phi=0.1)
        .build(),

        AtlasTileBuilder("Tile::Bar1", CaloSampling.TileBar1)
        .radii(2600.0, 3140.0)
        .z_span(-2820.0, 2820.0)
        .cells(d_eta=0.1, d_phi=0.1)
        .build(),

        AtlasTileBuilder("Tile::Bar2", CaloSampling.TileBar2)
        .radii(3140.0, 3820.0)
        .z_span(-2820.0, 2820.0)
        .cells(d_eta=0.2, d_phi=0.1)
        .build(),

        # ... (Camadas do EMEC1-3, HEC0-3, FCal1-3, TileExt e Gap Scintillators)
    ]

def getAtlasAllDeadMaterials() -> List[DeadMaterialVolume]:
    """Retorna os materiais passivos oficiais do ATLAS (criostatos, solenoide e suportes)."""
    return [
        AtlasDeadMaterialBuilder("DM::Solenoid")
        .polycone(z_planes=[-2900.0, 2900.0], r_min=[1229.0, 1229.0], r_max=[1275.0, 1275.0])
        .material("G4_Al")
        .in_solenoid_field(True)
        .build(),

        AtlasDeadMaterialBuilder("DM::Cryo::Barrel::InnerWarm")
        .tubular(rmin=1250.0, rmax=1260.0, z_size=6800.0, material="G4_Al")
        .build(),

        # ... (Paredes frias, vasos externos e suportes de crack)
    ]
```

---

### 5.3. Orquestrador Pythonico Moderno (`geometry/ATLAS/python/v2/DetectorConstruction.py`)

A classe `AtlasDetectorConstruction` do `v2` fica extremamente concisa, elegante e orientada a dados:

```python
"""
DetectorConstruction.py - Orquestrador de alto nível para o ATLAS v2.
"""
import os
import json
from typing import Any, Dict, List, Optional
import ROOT
from prettytable import PrettyTable
from GaugiKernel import Configurable

from ATLAS.v2.Layer import CaloSamplingLayer, DeadMaterialVolume
from ATLAS.v2.AtlasCfg import getAtlasAllSamplings, getAtlasAllDeadMaterials

class AtlasDetectorConstruction(Configurable):
    """
    Orquestrador moderno do detector ATLAS (v2).
    Orientado a arquivo JSON declarativo, sem overhead de RPCs PyROOT.
    """
    def __init__(
        self,
        name: str = "ATLAS",
        geometry_file: Optional[str] = None,
        UseMagneticField: bool = False,
        UseSolenoidField: bool = True,
        CutOnPhi: bool = False,
    ) -> None:
        if geometry_file is None:
            geometry_file = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data",
                "atlas_geometry.json"
            )
        self.geometry_file: str = os.path.abspath(geometry_file)

        # Inicializa o C++ DetectorConstruction_v2
        super().__init__(
            ROOT.DetectorConstruction_v2,
            name,
            UseMagneticField=UseMagneticField,
            UseSolenoidField=UseSolenoidField,
            CutOnPhi=CutOnPhi,
            GeometryFile=self.geometry_file if os.path.isfile(self.geometry_file) else "",
        )

        self.samplings: List[CaloSamplingLayer] = []
        self.dead_materials: List[DeadMaterialVolume] = []

        if os.path.isfile(self.geometry_file):
            self.load(self.geometry_file)
        else:
            self.samplings.extend(getAtlasAllSamplings())
            self.dead_materials.extend(getAtlasAllDeadMaterials())

    @property
    def layers(self) -> List[CaloSamplingLayer]:
        """Acesso à lista de camadas de amostragem ativas."""
        return self.samplings

    def load(self, filepath: str) -> None:
        """Carrega a geometria a partir de um arquivo JSON."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.samplings = [CaloSamplingLayer.from_dict(v) for v in data.get("volumes", []) if "readout" in v]
        self.dead_materials = [DeadMaterialVolume.from_dict(v) for v in data.get("volumes", []) if "readout" not in v]
        self.geometry_file = filepath

    def save(self, filepath: str) -> None:
        """Exporta o estado atual para o JSON canônico."""
        data = {
            "metadata": {
                "version": "2.0",
                "detector": "ATLAS",
                "description": "ATLAS Calorimeter official canonical geometry specification",
            },
            "volumes": [s.to_dict() for s in self.samplings] + [dm.to_dict() for dm in self.dead_materials],
        }
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.geometry_file = filepath

    def compile(self) -> None:
        """
        Prepara a geometria para simulação Geant4.
        Injeta o caminho do JSON no C++ em ~1 ms; zero chamadas de AddVolume via PyROOT.
        """
        if not os.path.isfile(self.geometry_file):
            self.save(self.geometry_file)
        self._c_ptr.setProperty("GeometryFile", self.geometry_file)

    def view(self, port: int = 8080) -> None:
        """Abre o visualizador 3D WebGL do ATLAS no navegador."""
        from visualizer import launch_visualizer
        if not os.path.isfile(self.geometry_file):
            self.save(self.geometry_file)
        launch_visualizer(self.geometry_file, port=port)

    def export_vector_pdf(self, output_filepath: str, view: str = "rz") -> None:
        """Exporta planta técnica 100% vetorial em PDF do ATLAS."""
        from visualizer import export_vector_pdf
        if not os.path.isfile(self.geometry_file):
            self.save(self.geometry_file)
        export_vector_pdf(self.geometry_file, output_filepath, view=view)

    def summary(self) -> None:
        """Exibe tabela das amostragens do ATLAS no terminal."""
        table = PrettyTable(["Sampling", "Detector", "Rmin (mm)", "Rmax (mm)", "Z span (mm)", "dEta x dPhi", "Noise (MeV)"])
        for s in self.samplings:
            table.add_row([s.name, s.detector_name, f"{s.rmin:.1f}", f"{s.rmax:.1f}", f"{s.zmin:.0f}..{s.zmax:.0f}", f"{s.delta_eta:.4f} x {s.delta_phi:.4f}", f"{s.noise_mev:.1f}"])
        print("\n=== ATLAS Calorimeter Summary (v2) ===")
        print(table)
```

---

### 5.4. Exemplo de Uso pelo Usuário no Dia a Dia

O usuário ganha uma interface extremamente intuitiva e poderosa:

```python
from geometry import DetectorConstructionCfg

# 1. Instanciar o ATLAS moderno (v2)
det = DetectorConstructionCfg("ATLAS", detector="ATLAS", atlas_version="v2")

# 2. Inspecionar a tabela de camadas no terminal
det.summary()

# 3. Visualizar em 3D no navegador via WebGL (FastAPI + Three.js)
det.view(port=8080)

# 4. Gerar corte técnico longitudinal R-Z vetorial em PDF para publicação
det.export_vector_pdf("atlas_run4_geometry.pdf", view="rz")

# 5. Customização rápida em memória sem mexer em código C++
# Exemplo: testar o impacto de aumentar o ruído no EMB1 para estudo de trigger
det.layers[1].noise_mev = 60.0
det.save("atlas_noisy_trigger_study.json")

# 6. Compilação para Geant4 (ultra-rápida, em 1 ms)
det.compile()
```

---

## 6. Plano de Implementação em Fases

| Fase | Etapa | Descrição | Impacto |
| :---: | :--- | :--- | :--- |
| **1** | **C++ `DetectorConstruction_v1` & `v1/` Python** | Renomear o atual `DetectorConstruction_v2` (.h e .cxx) para `DetectorConstruction_v1`. Mover todo o código Python atual com suas flags para `geometry/ATLAS/python/v1/`. Atualizar `LinkDef.h` e `CMakeLists.txt`. | Não-regressão garantida; simulação existente permanece 100% operacional. |
| **2** | **C++ `DetectorConstruction_v2` Nativo** | Criar novo `DetectorConstruction_v2.h` e `src/DetectorConstruction_v2.cxx` com método `LoadGeometryFile` utilizando `nlohmann/json`. Ambos compilados no `liblorenzetti.so`. | Disponibilização do motor rápido orientado a dados no C++. |
| **3** | **Modelagem `v2/` Python** | Criar `geometry/ATLAS/python/v2/` contendo `Layer.py`, `AtlasCfg.py`, `DetectorConstruction.py` e gerar o primeiro `atlas_geometry.json`. | Disponibilização da nova API pythônica limpa e fluente. |
| **4** | **Integração com `visualizer` e Factory** | Conectar `v2` com `launch_visualizer` e `export_vector_pdf`. Atualizar `geometry/__init__.py` com suporte transparente a `atlas_version="v1"|"v2"`. | Inspeção 3D do ATLAS no navegador e desenhos vetoriais PDF. |
| **5** | **Bateria de Testes e Validação** | Testes de unidade comparativos entre `v1` e `v2`, validação de carregamento de volumes e verificação no container Singularity. | Garantia de robustez e estabilidade completa. |
