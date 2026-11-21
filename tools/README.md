# Tools

Este diretório contém componentes e ferramentas especializadas (`Gaugi::Tool`) do framework Lorenzetti, desacopladas dos algoritmos orquestradores de reconstrução.

## Estrutura de Diretórios

### `calorimeter/`
Contém as ferramentas de calorimetria utilizadas pelo pipeline de formação de hits, digitalização de células e agrupamento em clusters:

1. **`CaloHitTools`**:
   - Ferramentas universais e detector-agnósticas (utilizadas em geometrias padrão como `GeoV1` e detectores cilíndricos regulares).
   - Componentes:
     - `CaloGridCellTool`: Mapeamento em grade regular $(\eta, \phi)$ por busca binária.
     - `CaloBirksLawTool`: Correção de saturação de Birks para cintiladores e argônio líquido.
     - `CaloTofCorrectionTool`: Correção de tempo de voo padrão ($r/c$).
     - `CaloStandardHitRecorderTool`: Gravação e acumulação em contêineres `xAOD::CaloHit`.

2. **`AtlasCaloHitTools`**:
   - Ferramentas especialistas e modelos físicos do ATLAS Run 4 (`GeoV2`).
   - Componentes Tile:
     - `TileBoxCellTool`: Células Tile em caixas $(r, z)$, canais especiais e reposição D4 $\rightarrow$ D5.
     - `TileDualReadoutSplitTool`: Partição de energia entre PMTs (perfil empírico U-shape ou linear).
     - `TilePmtPropagationTimeTool`: Atraso temporal de propagação óptica em telhas e fibras.
   - Componentes LAr (EMB, EMEC, HEC):
     - `LArAccordionTool`: Geometria do acordeão do barril EMB, rotina `SampSeg` e presampler.
     - `LArEmecCompartmentTool`: 11 compartimentos do EMEC com planos divisores em $Z$.
     - `LArHecModuleTool`: Projeção nos 32 módulos em cunha do HEC ($r \cos(\phi - \phi_c)$).
     - `LArEmecChargeCollectionTool`: Resposta Ramo usando mapas de campo elétrico e alta tensão.
   - Componentes FCAL e Free-Running:
     - `LArFCalElectrodeTool`: Associação de gaps de eletrodos tubulares e matriz de *frozen showers*.
     - `CaloFreeRunningHitRecorderTool`: Gravação de hits em formato de 64 bits do Athena.
     - `freerunning/CaloFreeRunningHitList`: Contêiner StoreGate de depósitos de tempo livre.
     - `freerunning/CaloFreeRunningHitWriter`: Gravador de ntuplas HITS no formato oficial Athena.

3. **`CaloCellTools`**:
   - Ferramentas de modelagem eletrônica e injeção de defeitos em células de calorímetro.
   - Componentes:
     - `PulseGeneratorTool`: Convolução de depósito de energia com pulso de referência (shaper), adição de pedestal e ruído eletrônico gaussiano.
     - `OptimalFilterTool`: Reconstrução de amplitude (energia) e tempo ($\tau$) via pesos de filtro ótimo pré-calculados.
     - `ConstrainedOptimalFilterTool`: Reconstrução de sinal por filtro ótimo com vínculos analíticos (ex: pedestal nulo).
     - `PulsePerturberTool`: Injeção de perturbações, anomalias e canais mortos a partir de mapas e arquivos BRL (Bad Run List).

4. **`CaloClusterTools`**:
   - Ferramentas de caracterização física, variáveis discriminantes e momentos espaciais de clusters.
   - Componentes:
     - `ShowerShapeTool`: Cálculo das grandezas de forma do chuveiro nas camadas do calorímetro ($E_0..E_3, E_{had1..3}, f_0..f_3, R_\eta, R_\phi, w_{\eta2}, E_{ratio}, R_{had}, R_{had1}, E, E_T, E_{tot}$).
     - `MomentsTool`: Cálculo do eixo principal 3D via PCA (autovetores da matriz de covariância espacial) e momentos de segunda ordem ($2^{nd} R, \lambda_{center}, 2^{nd} \lambda, FracMax, LateralMom, LongitudinalMom$).
