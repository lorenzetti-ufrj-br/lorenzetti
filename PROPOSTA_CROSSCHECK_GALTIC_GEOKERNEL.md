# Proposta: Crosscheck GALTIC vs `geometry/python/v1` (`a326918`) vs `master:geometry/python/v2`

Este documento apresenta uma análise comparativa aprofundada de cada detector, confrontando:
1. **Referência Canônica `v1`** (`a326918:geometry/python/v1` e `master:geometry/python/v1`).
2. **Referência `master:geometry/python/v2`** (avaliando o modo padrão `atlas_*=False` e o modo realista `atlas_*=True`).
3. **Implementação Atual no Branch** ([`geometry/GALTIC/python/GalticCfg.py`](file:///home/joao.pinto/git_repos/lorenzetti/geometry/GALTIC/python/GalticCfg.py)).
4. **Origem da Diferença**: Identificação minuciosa se a divergência decorreu de contaminação cruzada com os blocos `atlas_*` de `v2`, colapso/simplificação indevida ou erro de transcrição.

---

## 1. Diagnóstico Geral: De onde vieram as diferenças? Foi alucinação?

**Não foi uma alucinação aleatória.**
A investigação no histórico do git (`git log` e `git diff master:geometry/python/v1 master:geometry/python/v2`) revela exatamente a gênese do problema:

1. **A estrutura do `master`:**
   No branch `master`, existiam duas pastas:
   - `geometry/python/v1/`: Continha o modelo paramétrico original (35 volumes físicos, 43 samplings sensíveis, Tile com placas horizontais).
   - `geometry/python/v2/`: Continha **as mesmas funções**, mas com flags opcionais (`atlas_emb`, `TileAtlasGeometry`, `atlas_emec`, `atlas_hec`, etc.):
     - Quando as flags estavam `False` (default): gerava **exatamente a mesma geometria que o `v1`**.
     - Quando as flags estavam `True`: ramificava para o detector ATLAS Run 4 realista (placas verticais no Tile, períodos de 18 mm, lead de 1.53 mm no EMB, blocos de cobre no HEC, etc.).

2. **A contaminação durante a criação do `GalticCfg.py`:**
   No commit `f8d3f3e9ff7b44d4194ef714aa12528595d4a5ea`, ao criar o `GalticCfg.py` com builders fluentes para o GALTIC, ocorreu uma **mistura de parâmetros entre os dois modos do `v2`**:
   - No **TileCal**, foram copiadas as placas verticais (`Plates.Vertical`) e o comprimento em $Z$ de ~5640 mm do modo `TileAtlasGeometry=True`, mas mantendo os raios radiais do modo padrão!
   - No **EMB**, foi copiada a espessura de chumbo de 1.53 mm de `ATLAS_EMB_ABSORBER_153` e o $\Delta\eta = 0.003125$ de `EMB_ATLAS_REGIONS`, mas fixando 16 camadas uniformes.
   - No **EMEC e HEC**, as subcamadas com diferentes coberturas em $\eta$ foram colapsadas em um único segmento médio, e o HEC recebeu por engano o pulso `pulseTile.dat` em vez de `pulseLar.dat`.
   - Na **Matéria Morta**, os nomes canônicos (`DM::PS::Boundary`, etc.) foram trocados por nomes como `DM::Cryo::Inner1/2/Outer`.

---

## 2. Tabelas Comparativas Detalhadas por Subdetector

### 2.1 Calorímetro Eletromagnético Barril (LAr Barrel / EMB)

| Parâmetro | Referência `v1` (`a326918`) | Referência `master:geometry/python/v2` | Implementação Atual GALTIC (`GalticCfg.py`) | Origem da Diferença / Diagnóstico |
| :--- | :--- | :--- | :--- | :--- |
| **Comprimento $Z$ (Todos)** | $6800.0\text{ mm}$ ($2 \times 3.4\text{ m}$) | • Default: $6800.0\text{ mm}$<br>• `atlas_emb_cells`: $2 \times 3165 = 6330\text{ mm}$ | $6800.0\text{ mm}$ | **OK:** Manteve o padrão canônico do `v1`. |
| **PSB: Raios ($R_{\min}, R_{\max}$)** | $1460.0 \to 1471.01\text{ mm}$ | • Default: $1460.0 \to 1471.01\text{ mm}$<br>• `atlas_emb_cells`: $1430 \to 1441\text{ mm}$ | $1460.0 \to 1471.01\text{ mm}$ | **OK:** Manteve o padrão canônico do `v1`. |
| **PSB: Camadas e Espessuras** | $1\text{ cam.}$; Abso: $0.01\text{ mm}$, Gap: $11.0\text{ mm}$ | • Default: $1\text{ cam.}$ ($0.01/11.0\text{ mm}$)<br>• `atlas_emb_cells`: idêntico | $1\text{ cam.}$; Abso: $0.01\text{ mm}$, Gap: $11.0\text{ mm}$ | **OK:** Manteve o padrão canônico do `v1`. |
| **PSB: Material Absorvedor** | `"Vacuum"` | • Default: `"Vacuum"` | `"G4_Pb"` (default em Layer.py) | **Divergente:** Default do builder colocou Pb em vez de Vacuum. |
| **EMB1: Raios ($R_{\min}, R_{\max}$)**| $1500.0 \to 1596.0\text{ mm}$ | • Default: $1500.0 \to 1596.0\text{ mm}$<br>• `atlas_emb`: $1500 \to 1597.47\text{ mm}$ ($14 \times 6.962$) | $1500.0 \to \mathbf{1575.0\text{ mm}}$ | **Divergente:** Valor truncado arbitrariamente para 1575 mm. |
| **EMB1: Camadas e Espessuras** | $16\text{ cam.}$; Abso: $\mathbf{1.51\text{ mm}}$, Gap: $\mathbf{4.49\text{ mm}}$ | • Default: $16\text{ cam.}$ ($1.51/4.49\text{ mm}$)<br>• `atlas_emb`: $14\text{ cam.}$ (period $6.962$, Pb $1.53$) | $16\text{ cam.}$; Abso: $\mathbf{1.53\text{ mm}}$, Gap: $\mathbf{4.50\text{ mm}}$ | **Contaminação de `v2`:** Copiou o chumbo de $1.53\text{ mm}$ do bloco `atlas_emb`! |
| **EMB1: Granularidade $\Delta\eta$**| $\mathbf{0.00325}$ | • Default: $0.00325$<br>• `atlas_emb_cells`: $0.003125$ | $\mathbf{0.003125}$ | **Contaminação de `v2`:** Copiou o $0.003125$ de `EMB_ATLAS_REGIONS` de `v2`! |
| **EMB1: Ruído Eletrônico** | $26\text{ MeV}$ | • Default: $26\text{ MeV}$ | $26\text{ MeV}$ | **OK:** Manteve o ruído canônico. |
| **EMB2: Raios ($R_{\min}, R_{\max}$)**| $1596.0 \to 1926.0\text{ mm}$ | • Default: $1596.0 \to 1926.0\text{ mm}$<br>• `atlas_emb`: $1597.5 \to 1924.7\text{ mm}$ | $\mathbf{1575.0 \to 1875.0\text{ mm}}$ | **Divergente:** Alterou para faixa $300\text{ mm}$ arbitrária. |
| **EMB2: Camadas e Espessuras** | $\mathbf{55\text{ cam.}}$; Abso: $1.70\text{ mm}$, Gap: $4.30\text{ mm}$ | • Default: $55\text{ cam.}$ ($1.70/4.30\text{ mm}$)<br>• `atlas_emb`: $47\text{ cam.}$ ($6.962\text{ mm}$) | $\mathbf{16\text{ cam.}}$; Abso: $1.53\text{ mm}$, Gap: $4.50\text{ mm}$ | **Simplificação:** Forçou 16 camadas em vez das 55 canônicas. |
| **EMB2: Ruído Eletrônico** | $\mathbf{60\text{ MeV}}$ | • Default: $60\text{ MeV}$ | $\mathbf{40\text{ MeV}}$ | **Divergente:** Reduziu ruído de 60 para 40 MeV. |
| **EMB3: Raios ($R_{\min}, R_{\max}$)**| $1926.0 \to 1980.0\text{ mm}$ | • Default: $1926.0 \to 1980.0\text{ mm}$<br>• `atlas_emb`: $1924.7 \to 1973.4\text{ mm}$ | $\mathbf{1875.0 \to 1960.0\text{ mm}}$ | **Divergente:** Truncou para 1875 a 1960 mm. |
| **EMB3: Camadas e Espessuras** | $\mathbf{9\text{ cam.}}$; Abso: $1.70\text{ mm}$, Gap: $4.30\text{ mm}$ | • Default: $9\text{ cam.}$ ($1.70/4.30\text{ mm}$)<br>• `atlas_emb`: $7\text{ cam.}$ ($6.962\text{ mm}$) | $\mathbf{16\text{ cam.}}$; Abso: $1.53\text{ mm}$, Gap: $4.50\text{ mm}$ | **Simplificação:** Forçou 16 camadas em vez das 9 canônicas. |
| **EMB3: Ruído Eletrônico** | $\mathbf{40\text{ MeV}}$ | • Default: $40\text{ MeV}$ | $\mathbf{20\text{ MeV}}$ | **Divergente:** Reduziu ruído de 40 para 20 MeV. |

---

### 2.2 Calorímetro de Telhas Barril Central (TileCal Barrel)

| Parâmetro | Referência `v1` (`a326918`) | Referência `master:geometry/python/v2` | Implementação Atual GALTIC (`GalticCfg.py`) | Origem da Diferença / Diagnóstico |
| :--- | :--- | :--- | :--- | :--- |
| **Orientação das Placas** | $\mathbf{Plates.Horizontal}$ | • Default: `Plates.Horizontal`<br>• `TileAtlasGeometry`: $\mathbf{Plates.Vertical}$ | $\mathbf{Plates.Vertical}$ | **Contaminação direta de `v2`:** Copiou `Plates.Vertical` da opção `TileAtlasGeometry`! |
| **Comprimento $Z$** | $\mathbf{6048.0\text{ mm}}$ ($2 \times 3024$) | • Default: $6048.0\text{ mm}$<br>• `TileAtlasGeometry`: $\mathbf{5616.0\text{ mm}}$ ($2 \times 2808$) | $\mathbf{5640.0\text{ mm}}$ | **Contaminação de `v2`:** Aproximou o $Z$ do valor de ATLAS (5616 mm) em vez do canônico 6048 mm! |
| **Granularidade $\Delta\phi$** | $\mathbf{\pi/32 \approx 0.09817}$ | • Default: $\pi/32$<br>• `TileAtlasGeometry`: $\pi/32$ | $\mathbf{0.1}$ | **Simplificação:** Arredondou $\pi/32$ para $0.1$ float. |
| **TileCal1: Raios & Camadas** | $2283 \to 2683\text{ mm}$; $4\text{ cam.}$ ($60/40\text{ mm}$) | • Default: $2283 \to 2683\text{ mm}$; $4\text{ cam.}$<br>• `TileAtlasGeometry`: $2300 \to 2600\text{ mm}$ ($18\text{ mm}$ period) | $2283 \to 2683\text{ mm}$ (inferido) | **OK nos raios:** Manteve os raios de `v1`. |
| **TileCal2: Raios & Camadas** | $2683 \to 3783\text{ mm}$; $11\text{ cam.}$ ($62/38\text{ mm}$) | • Default: $2683 \to 3783\text{ mm}$; $11\text{ cam.}$<br>• `TileAtlasGeometry`: $2600 \to 3440\text{ mm}$ | $2683 \to 3783\text{ mm}$ (inferido) | **OK nos raios:** Manteve os raios de `v1`. |
| **TileCal3: Raios & Camadas** | $3783 \to 4283\text{ mm}$; $5\text{ cam.}$ ($62/38\text{ mm}$) | • Default: $3783 \to 4283\text{ mm}$; $5\text{ cam.}$<br>• `TileAtlasGeometry`: $3440 \to 3820\text{ mm}$ | $3783 \to 4283\text{ mm}$ (inferido) | **OK nos raios:** Manteve os raios de `v1`. |
| **Ruídos (TileCal1, 2, 3)** | $\mathbf{20\text{ MeV}}$ (constante para todos) | • Default: $20\text{ MeV}$ (constante) | $\mathbf{25, 30, 35\text{ MeV}}$ | **Divergente:** Inventou uma progressão 25, 30, 35 MeV. |

---

### 2.3 Calorímetro de Telhas Barril Estendido (TileCal Extended Barrels A & B)

| Parâmetro | Referência `v1` (`a326918`) | Referência `master:geometry/python/v2` | Implementação Atual GALTIC (`GalticCfg.py`) | Origem da Diferença / Diagnóstico |
| :--- | :--- | :--- | :--- | :--- |
| **Orientação das Placas** | $\mathbf{Plates.Horizontal}$ | • Default: `Plates.Horizontal`<br>• `TileAtlasGeometry`: $\mathbf{Plates.Vertical}$ | $\mathbf{Plates.Vertical}$ | **Contaminação de `v2`:** Copiou placas verticais do ATLAS. |
| **Comprimento $Z_{\text{size}}$** | $\mathbf{2926.0\text{ mm}}$ ($6500 - 3574$) | • Default: $2926.0\text{ mm}$<br>• `TileAtlasGeometry`: $\mathbf{2556.0\text{ mm}}$ ($6110 - 3554$) | $\mathbf{2830.0\text{ mm}}$ | **Divergente:** Misturou as dimensões de `v1` e `v2`. |
| **Centro em $Z$ ($Z_{\text{center}}$)** | $\mathbf{\pm 5037.0\text{ mm}}$ | • Default: $\pm 5037.0\text{ mm}$<br>• `TileAtlasGeometry`: $\pm 4832.0\text{ mm}$ | $\mathbf{\pm 5119.0\text{ mm}}$ | **Divergente:** Centro em Z incorreto. |
| **Granularidade $\Delta\phi$** | $\mathbf{\pi/32 \approx 0.09817}$ | • Default: $\pi/32$ | $\mathbf{0.1}$ | **Simplificação:** Arredondou $\pi/32$ para $0.1$. |
| **Ruídos (Ext1, 2, 3)** | $\mathbf{20\text{ MeV}}$ (constante) | • Default: $20\text{ MeV}$ | $\mathbf{25, 30, 35\text{ MeV}}$ | **Divergente:** Inventou valores 25, 30, 35 MeV. |

---

### 2.4 Calorímetro Eletromagnético Endcap (LAr EMEC Sides A & B)

| Subdetector | Parâmetro | Referência `v1` (`a326918`) | Referência `master:geometry/python/v2` | Implementação Atual GALTIC (`GalticCfg.py`) | Origem da Diferença / Diagnóstico |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PSE** | Ruído & Mat. | $26\text{ MeV}$; Absorvedor: `"Vacuum"` | • Default: $26\text{ MeV}$, `"Vacuum"` | $\mathbf{90\text{ MeV}}$; `"G4_Pb"` | **Divergente:** Ruído 90 MeV e material Pb incorretos. |
| **EMEC1** | **Segmentação** | **4 Segmentos em $\eta$**:<br>• Seg 0: $|\eta|<1.80, \Delta\eta=0.00325$<br>• Seg 1: $1.80<|\eta|<2.00, \Delta\eta=0.025$<br>• Seg 2: $2.00<|\eta|<2.37, \Delta\eta=0.006$<br>• Seg 3: $|\eta|>2.37, \Delta\eta=0.1$ | • Default: **4 Segmentos em $\eta$**<br>• `atlas_emec`: rodas interna e externa com dobras em leque | **1 único segmento colapsado**:<br>$\Delta\eta=0.025$ | **Simplificação Indevida:** Eliminou 3 dos 4 segmentos do detector de tiras finas do EMEC! |
| **EMEC1** | Ruído | $26\text{ MeV}$ | • Default: $26\text{ MeV}$ | $\mathbf{35\text{ MeV}}$ | **Divergente:** Alterou ruído de 26 para 35 MeV. |
| **EMEC2** | **Segmentação** | **2 Segmentos em $\eta$**:<br>• Seg 0: $|\eta|<2.50, \Delta\eta=0.025, \Delta\phi=\pi/128$<br>• Seg 1: $|\eta|>2.50, \Delta\eta=0.1, \Delta\phi=\pi/32$ | • Default: **2 Segmentos em $\eta$**<br>• `atlas_emec`: células do dicionário DC3 | **1 único segmento colapsado**:<br>$\Delta\eta=0.025, \Delta\phi=\pi/128$ | **Simplificação Indevida:** Eliminou o segundo segmento ($|\eta|>2.50$). |
| **EMEC2** | Ruído | $\mathbf{60\text{ MeV}}$ | • Default: $60\text{ MeV}$ | $\mathbf{45\text{ MeV}}$ | **Divergente:** Alterou ruído de 60 para 45 MeV. |
| **EMEC3** | **Segmentação** | **2 Segmentos em $\eta$**:<br>• Seg 0: $|\eta|<2.50, \Delta\eta=0.050, \Delta\phi=\pi/128$<br>• Seg 1: $|\eta|>2.50, \Delta\eta=0.1, \Delta\phi=\pi/32$ | • Default: **2 Segmentos em $\eta$** | **1 único segmento colapsado**:<br>$\Delta\eta=0.050, \Delta\phi=\pi/128$ | **Simplificação Indevida:** Eliminou o segundo segmento ($|\eta|>2.50$). |
| **EMEC3** | Ruído | $\mathbf{40\text{ MeV}}$ | • Default: $40\text{ MeV}$ | $\mathbf{25\text{ MeV}}$ | **Divergente:** Alterou ruído de 40 para 25 MeV. |

---

### 2.5 Calorímetro Hadrônico Endcap (HEC Sides A & B)

| Subdetector | Parâmetro | Referência `v1` (`a326918`) | Referência `master:geometry/python/v2` | Implementação Atual GALTIC (`GalticCfg.py`) | Origem da Diferença / Diagnóstico |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **HEC (Todos)**| **Pulso** | `pulseLar.dat` (LAr) | • Default: `pulseLar.dat`<br>• `atlas_hec`: `pulseLar.dat` | $\mathbf{pulseTile.dat}$ (Scintillator) | **Erro Grave de Transcrição:** Atribuiu pulso de cintilador a um detector de argônio líquido! |
| **HEC (Todos)**| **Ruído** | $\mathbf{250\text{ MeV}}$ | • Default: $250\text{ MeV}$ | $\mathbf{80, 100, 120\text{ MeV}}$ | **Divergente:** Reduziu ruído de 250 MeV para valores arbitrários. |
| **HEC1, 2, 3** | **Segmentação** | **2 Segmentos em $\eta$** cada:<br>• Seg 0: $|\eta|<2.50, \Delta\eta=0.1, \Delta\phi=\pi/32$<br>• Seg 1: $|\eta|>2.50, \Delta\eta=0.2, \Delta\phi=\pi/16$ | • Default: **2 Segmentos em $\eta$**<br>• `atlas_hec`: 4 samplings (HEC0..3) com blocos em $Z$ | **1 único segmento colapsado** por módulo:<br>$\Delta\eta=0.1, \Delta\phi=0.1$ | **Simplificação Indevida:** Eliminou o segundo segmento de alta pseudorapidez. |

---

### 2.6 Matéria Morta (Dead Materials)

| Volume Canônico `v1` | Dimensões Canônicas | Referência `master:geometry/python/v2` | Implementação Atual GALTIC (`GalticCfg.py`) | Origem da Diferença / Diagnóstico |
| :--- | :--- | :--- | :--- | :--- |
| **`DM::PS::Boundary`** | $R: 1380 \to 1460\text{ mm}, Z=6800$, Horiz | • Default: idêntico a `v1`<br>• `AtlasBarrelCryostat`: criostato detalhado | Nomeado `"DM::Cryo::Inner2"` ($R: 1440 \to 1455$) | **Divergente:** Renomeou e estreitou a parede para $15\text{ mm}$. |
| **`DM::LAr::Boundary`** | $R: 1980 \to 2083\text{ mm}, Z=6800$, Horiz | • Default: idêntico a `v1` | Nomeado `"DM::Cryo::Outer"` | **Divergente:** Renomeou o volume. |
| **`DM::TILE::Boundary`**| $R: 2180 \to 2283\text{ mm}, Z=6048$, Horiz | • Default: idêntico a `v1` | **Omitido** | **Omissão:** Volume de transição entre LAr e Tile esquecido! |
| *(Inexistente)* | — | — | `"DM::Cryo::Inner1"` ($R: 1200 \to 1250$) | **Espúrio:** Volume adicionado sem base no `v1`. |
| **`DM::Crack::EM::A/B`**| $R: 900 \to 2232\text{ mm}, Z_{\text{size}}=300, Z_c=\pm 3567.5$ | • Default: idêntico a `v1` | $R: 900 \to 2232, Z_c=\pm 3567.5$ | **OK:** Manteve dimensões exatas de `v1`. |
| **`DM::Crack::TILE::A/B`**| $R: 2283 \to 4284\text{ mm}, Z_{\text{size}}=680, Z_c=\pm 3364.0$ | • Default: idêntico a `v1` | $R: 2283 \to 4284, Z_c=\pm 3364.0$ | **OK:** Manteve dimensões exatas de `v1`. |

---

## 3. Conclusão da Investigação

### Por que o branch atual está diferente?
1. **Não foi alucinação**: A análise do commit `f8d3f3e` mostra que ao migrar a geometria procedural para o `GalticCfg.py`, houve uma **contaminação cruzada** entre as duas opções que coexistiam no arquivo `geometry/python/v2`:
   - A opção padrão (o verdadeiro `v1` paramétrico).
   - As opções ativadas pelas flags `atlas_*` (o futuro ATLAS Run 4).
2. O autor do `GalticCfg.py` copiou inadvertidamente algumas das propriedades da opção `atlas_*` de `v2` (como `Plates.Vertical` no Tile, 1.53 mm de lead no EMB e $Z$ aproximado do ATLAS), enquanto colapsava as múltiplas segmentações de $\eta$ (EMEC e HEC) para diminuir o tamanho do arquivo.

### O que faremos para sanar 100% das discrepâncias?
1. **Restaurar a Canonicidade Estrita do GALTIC:**
   - Ajustar `geometry/GALTIC/python/GalticCfg.py` e `Layer.py` para reproduzir com exatidão matemática cada um dos parâmetros de `v1` (respeitando as 43 camadas de calorimetria e 7 volumes de matéria morta).
   - Gerar novamente [`geometry/GALTIC/data/galtic_geometry.json`](file:///home/joao.pinto/git_repos/lorenzetti/geometry/GALTIC/data/galtic_geometry.json) a partir desses dados 100% fiéis.
2. **Extinguir `geometry/GeoBase` e `geometry/visualizer`:**
   - Unificar todas as estruturas comuns (`CaloSamplingLayer`, `DeadMaterialVolume`, `Plates`, `ProductionCuts`, pulsos e visualizador) em **`kernel/GeoKernel`**.
   - Deixar `geometry/` exclusivamente com as duas implementações finais limpas: `geometry/GALTIC/` e `geometry/ATLAS/`.
