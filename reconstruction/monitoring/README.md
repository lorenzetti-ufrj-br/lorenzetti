# Reconstruction Monitoring (`reconstruction/monitoring`)

Pacote responsável pelo monitoramento de qualidade de dados (Data Quality Monitoring - DQM) e validação técnica da reconstrução e física de elétrons e calorimetria no Lorenzetti.

Inspirado no sistema de monitoramento do ATLAS (`TrigEgammaMonitoring` / Athena DQ), o pacote fornece:
- **`EgammaMonitoringMaker`** (`C++` / `Gaugi::Algorithm`): Algoritmo de monitoramento que roda no final da sequência de reconstrução e produz um arquivo ROOT de auditoria independente (`expert_monitoring.root`).
- **`EgammaMonitoringMakerCfg` / `EgammaMonitoringCfg`** (`Python`): Interface de configuração para inserção na cadeia via `ComponentAccumulator`.
- **`reco_monitoring_diff.py`** (`CLI`): Utilitário de comparação estatística histograma-a-histograma entre o arquivo gerado e uma referência homologada, gerando relatórios em **HTML interativo** e **PDF**.

---

## Variáveis Monitoradas

1. **EventInfo / Pileup**: $\langle\mu\rangle$ (`avgmu`), $\mu_{\text{tot}}$, multiplicidade de clusters e elétrons por evento.
2. **Cinemática**: $E_T$, $E$, $\eta$, $\phi$ para clusters calorimétricos e elétrons reconstruídos.
3. **Shower Shapes**: $R_{\eta}$, $R_{\phi}$, $w_{\eta 2}$, $f_1$, $f_3$, $E_{\text{ratio}}$, $R_{\text{had}}$.
4. **Momentos de Cluster**: $\lambda_{\text{center}}$, $\langle\lambda^2\rangle$ (`secondLambda`), $\langle r^2\rangle$ (`secondR`), $f_{\max}$, momentos longitudinais e laterais.
5. **Identificação (PID)**: Contagem e fração de candidatos aceitos por Working Point (*Very Loose*, *Loose*, *Medium*, *Tight*).
6. **Perfis Ringer (Rings)**: Perfil médio de energia por anéis para todas as 6 topologias de anéis:
   - `rings_profile`: Anéis concêntricos padrão (*Standard*, 100 anéis)
   - `rings_asym_profile`: Anéis assimétricos por quadrantes (*Asym*, 277 anéis)
   - `rings_cross_profile`: Formato em cruz de 4 braços (*Cross*, 400 anéis)
   - `rings_corner_profile`: Formato em cantos diagonais (*Corner*, 400 anéis)
   - `rings_strips_profile`: Projeções 1D por camada/tiras (*Strips*, 338 anéis)
   - `rings_custom_profile`: Anéis customizados com deslocamentos (*Custom*, 100 anéis)
7. **Correlações 2D**: $R_{\eta}$ vs $\eta$, $w_{\eta 2}$ vs $E_T$, $R_{\text{had}}$ vs $\eta$.

---

## Uso na Reconstrução (`reco_trf.py`)

Para gerar o arquivo de monitoramento durante a etapa AOD:
```bash
reco_trf.py -i input.ESD.root -o output.AOD.root --enable-monitoring --monitoring-file expert_monitoring.root
```

---

## Comparação de Regressão e Validação Histograma a Histograma

Para auditar e comparar o arquivo gerado com uma referência anterior:
```bash
reco_monitoring_diff.py -t expert_monitoring.root -r expert_monitoring_ref.root -o monitoring_report.html --pdf monitoring_report.pdf
```
O script avalia:
- Testes de **Kolmogorov-Smirnov (KS)** e **Chi-Quadrado ($\chi^2$)**.
- Variações de média e dispersão (RMS).
- Gera o relatório em HTML standalone com gráficos de ratio bin-a-bin e filtros instantâneos.
