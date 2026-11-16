# Referência Quantitativa (Baseline) - Lorenzetti Showers

Este documento registra as configurações, comandos e tolerâncias utilizados para gerar a amostra pequena de referência (baseline) para os testes de regressão.

## 1. Configuração da Geração
* **Semente (Seed):** 413654000
* **Número de eventos:** 10
* **Processo:** Z -> e+ e- (colisões p+p a 14 TeV)

## 2. Comandos de Execução
Para garantir a reprodutibilidade por outros integrantes da equipe, o pipeline completo foi executado a partir de um checkout limpo com os seguintes comandos sequenciais:

1. **Geração:**
   `gen_zee.py --nov 10 -o Zee.EVT.root`
2. **Simulação:**
   `simu_trf.py -i Zee.EVT.root -o Zee.HIT.root -nt 10`
3. **Digitalização:**
   `digit_trf.py -i Zee.HIT.root -o Zee.ESD.root`
4. **Reconstrução:**
   `reco_trf.py -i Zee.ESD.root -o Zee.AOD.root`
5. **Ntuple:**
   `ntuple_trf.py -i Zee.AOD.root -o Zee.NTUPLE.root`

## 3. Tolerâncias Numéricas Iniciais
Para os testes de regressão em integrações contínuas ou alterações futuras no código, os dados extraídos no arquivo `tabela_baseline.csv` devem respeitar as seguintes tolerâncias matemáticas:

* **Tolerância Zero (Identidade estrita):** Variáveis discretas e booleanas.
  * Número de Células (Reco e Truth).
  * Multiplicidade de Clusters.
  * Variáveis booleanas (ex: PID_Tight).
* **Tolerância Absoluta de 10⁻⁴:** Variáveis contínuas (pontos flutuantes).
  * Energia reconstruída e gerada (MeV).
  * Variáveis de Shower Shapes (eRatio, weta2, Reta).
  * Variáveis de Anéis (Ring_0).
  * *Justificativa:* Flutuações mínimas de ponto flutuante podem ocorrer entre diferentes compilações ou arquiteturas (ex: ordem das somas no fast math), sendo uma margem de $10^{-4}$ suficiente para evitar falhas falsas no teste de regressão sem mascarar erros reais na física.