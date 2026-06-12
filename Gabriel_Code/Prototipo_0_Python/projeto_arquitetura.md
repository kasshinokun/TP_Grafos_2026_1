# Arquitetura do Projeto: GraphAnalyzer EDA

O projeto será estruturado seguindo uma **Event-Driven Architecture (EDA)**, onde cada componente principal funciona como uma micro-aplicação independente que se comunica através de um barramento de eventos centralizado, simulando requisições de API (GET/POST).

## Componentes Principais

| Micro-aplicação | Responsabilidade |
| :--- | :--- |
| **Event Bus** | O núcleo da arquitetura. Gerencia o registro de eventos e a distribuição de mensagens entre as micro-aplicações. |
| **Data Micro-App** | Responsável pela extração de dados do GitHub e armazenamento temporário. Simula o "Backend". |
| **Graph Micro-App** | Implementa a lógica de grafos (`AdjacencyMatrixGraph`, `AdjacencyListGraph`) e cálculos de métricas. |
| **UI Micro-App** | Interface principal em PyQt6 que exibe os resultados e permite a interação do usuário. |

## Fluxo de Comunicação (Simulação de API)

As micro-aplicações não se chamam diretamente. Elas emitem eventos que o **Event Bus** captura e redireciona.

1.  **POST Request (Simulado):** A UI emite um evento `REQUEST_GRAPH_BUILD`. O Event Bus encaminha para o Graph Micro-App.
2.  **GET Request (Simulado):** A UI emite um evento `REQUEST_METRICS_DATA`. O Graph Micro-App processa e emite um evento `RESPONSE_METRICS_DATA` com o payload.

## Estrutura de Diretórios

```text
/home/ubuntu/graph_analyzer/
├── main.py                 # Ponto de entrada
├── core/
│   ├── event_bus.py        # Barramento de eventos central
│   └── base_app.py         # Classe base para micro-aplicações
├── apps/
│   ├── data_app.py         # Micro-app de dados
│   ├── graph_app.py        # Micro-app de lógica de grafos
│   └── ui_app.py           # Micro-app de interface
└── models/
    ├── graph_models.py     # Implementação das classes de grafos
    └── student_models.py   # Dados dos alunos
```
