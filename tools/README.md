# Tools

Este diretório contém componentes e ferramentas especializadas (`Gaugi::Tool`) do framework Lorenzetti, desacopladas dos algoritmos orquestradores de reconstrução.

## Estrutura de Diretórios

### `calorimeter/`
Contém as ferramentas de calorimetria utilizadas pelo pipeline de formação de hits (`CaloHitMaker`):

1. **`CaloHitBuilderTools`**:
   - Ferramentas universais e detector-agnósticas (utilizadas em geometrias padrão como `GeoV1` e detectores cilíndricos regulares).
   - Componentes:
     - `CaloGridCellTool`: Mapeamento em grade regular $(\eta, \phi)$ por busca binária.
     - `CaloBirksLawTool`: Correção de saturação de Birks para cintiladores e argônio líquido.
     - `CaloTofCorrectionTool`: Correção de tempo de voo padrão ($r/c$).
     - `CaloStandardHitRecorderTool`: Gravação e acumulação em contêineres `xAOD::CaloHit`.

2. **`AtlasCaloHitBuilderTools`**:
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
