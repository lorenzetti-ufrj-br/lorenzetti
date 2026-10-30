# Fluxo de Energia e Sigma no Lorenzetti

Este documento detalha o ciclo de vida da energia depositada (`edep`) e do ruído eletrônico (`Sigma`) no framework Lorenzetti, mapeando desde a configuração da geometria até a reconstrução dos clusters. Este mapeamento atende aos critérios de aceite da **Issue #3** e estabelece o contrato técnico para a futura implementação do corte em sigma.

## 1. Diagrama de Fluxo (Pipeline de Dados)

O diagrama abaixo ilustra o caminho percorrido pelos dados da célula, destacando onde o sigma nasce e onde o novo corte deverá ser aplicado.

```mermaid
graph TD
    %% Nós do Python
    subgraph Inicialização (Python)
        GEO[Arquivos de Geometria<br/>ECAL.py, TILE.py, etc.]
        BUILD[CaloCellBuilder.py]
    end

    %% Nós do C++
    subgraph Digitalização (C++)
        PULSE[PulseGenerator.cxx]
        OF[Filtro Ótimo / CrossTalk]
    end

    %% Nós de Reconstrução
    subgraph Reconstrução e Merge (C++)
        MERGE{CaloCellMerge.cxx<br/>PONTO DE CORTE GLOBAL}
        CONT[Container Unificado<br/>de Células]
        CLUS[CaloClusterMaker]
        RING[CaloRingsMaker<br/>PONTO DE CORTE RINGS]
    end

    %% Fluxo de Ações
    GEO -->|Define 'Noise' fixo| BUILD
    BUILD -->|Inicializa com 'NoiseStd'| PULSE
    
    PULSE -->|Lê Hit do Geant4| A1(Gera pulso + Ruído Gaussiano)
    A1 -->|Salva na célula| A2(cell->setPulse<br/>cell->setSigma)
    
    A2 -->|CaloDetDescriptor| OF
    OF -->|Calcula E_reco| MERGE
    
    MERGE -->|Filtra e Agrupa| CONT
    
    CONT --> CLUS
    CONT --> RING
```

## 2. Rastreamento e Definição Técnica

### A Origem do Sigma
O ruído eletrônico não é calculado dinamicamente durante a colisão. Ele é uma constante física derivada do hardware do detector (ex: `Noise = 26*MeV` para a camada EMB1). 
Essa constante nasce nos scripts Python da pasta `geometry/python/v1/` e é entregue ao maestro de digitalização `CaloCellBuilder.py`.

### A Injeção no Objeto da Célula
O `CaloCellBuilder.py` repassa esse valor de ruído para o motor C++ `PulseGenerator.cxx` através da variável `m_noiseStd`. No método `execute()`, o gerador lê a energia real da simulação (`edep`), transforma num pulso elétrico, adiciona uma flutuação Gaussiana com base no sigma e, crucialmente, salva o sigma dentro do objeto descritor da célula:
`cell->setSigma( m_noiseStd );`

A partir deste momento, o `CaloDetDescriptor` carrega consigo o valor de energia reconstruída e a sua tolerância de ruído.

## 3. Ponto de Aplicação do Corte
O ponto arquitetural correto para implementar a exclusão de células ruidosas (corte em sigma) é no **`CaloCellMerge`**.
Nesta etapa, o sinal já passou pelo `PulseGenerator`, pelo `OptimalFilter` e pelo `CrossTalkMaker`. A energia (`E_reco`) já é o valor final reconstruído. Aplicar a lógica condicional no `CaloCellMerge` (que atua como o funil que recebe as coleções individuais `InputCollectionKeys` e as unifica no container global `OutputCellsKey`) garante que a célula ruidosa seja descartada antes mesmo de entrar no container global que alimenta os construtores de cluster.

## 4. Diferença: Corte Global vs. Corte nos Rings
Existem duas abordagens distintas para lidar com o corte de ruído, que impactam a reconstrução física de maneiras diferentes:

* **Corte Global (no CaloCellMerge):** Ao barrar a célula de entrar no container unificado, ela deixa de existir para todo o resto do framework. O `CaloClusterMaker` (TopoClusters) perderá essa energia da contabilidade total do evento (ele agrupa as células ao redor de sementes consumindo o `InputCellsKey` que é a saída do `CaloCellMerge`), o que pode impactar calibrações delicadas de energia faltante (MET). A implementação deste mecanismo será o foco central do novo desenvolvimento.
* **Corte apenas nos Rings (no CaloRingsMaker):** A célula sobrevive no container global, mas é explicitamente ignorada no momento de desenhar os anéis concêntricos (`Rings`). Atualmente, o script `CaloRingsMaker.py` já possui as propriedades legadas `DoSigmaCut = False` e `SigmaCut = 2.0`. A existência prévia destes parâmetros indica uma tentativa não documentada de aplicar a filtragem isoladamente nos anéis, evidenciando a necessidade de uma definição formal do limiar ideal (fator multiplicador do sigma) nas próximas etapas.