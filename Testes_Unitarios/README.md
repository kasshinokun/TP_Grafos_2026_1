# 🧪 Testes Unitários — Visão Geral do Projeto

Este documento consolida as suites de testes unitários desenvolvidas individualmente por **Gabriel**, **Paulo** e **Daniel**, cobrindo os principais módulos do projeto: infraestrutura assíncrona do Orchestrator Híbrido, API de Grafos orientada a eventos e o motor de grafos dirigidos ponderados.

---

## 👥 Contribuidores e Escopos

| Programador | Módulo Testado | Framework | Arquivos de Teste |
|---|---|---|---|
| Gabriel | Orchestrator Híbrido (EventBus, TokenManager, StorageWorker, GUI) | `unittest` + scripts de integração | `test_cli/` (6 arquivos) |
| Paulo | API de Grafos via EventBus (criação, travessia, mineração de CSV) | `unittest` | `test_suite.py` |
| Daniel | `graph_engine` (operações de grafo + métricas de análise de rede) | `unittest` | `tests/` (2 arquivos) |

---

## 📁 Estrutura de Diretórios

```
Testes_Unitarios/
├── Gabriel/
│   └── test_cli/
│       ├── run_all.py                        # Runner agregado
│       ├── test_event_bus.py                 # unittest — EventBus
│       ├── test_token_manager.py             # unittest — TokenManager
│       ├── test_storage_worker_isolation.py  # unittest — BufferedStorageWorker
│       ├── test_gui_smoke.py                 # unittest — importação da GUI
│       ├── test_cooldown.py                  # script — integração de cooldown
│       └── test_queue_separation.py          # script — separação de filas e concorrência
├── Paulo/
│   └── test_suite.py                         # unittest — API de grafos via eventos
└── Daniel/
    └── tests/
        ├── test_graphs.py                    # unittest — contrato de grafo (2 implementações)
        └── test_analysis.py                  # unittest — métricas de análise de rede
```

---

## 🧑‍💻 Gabriel — Orchestrator Híbrido

Suite de testes para o **Orchestrator Híbrido** (minerador de dados GitHub), cobrindo os componentes de infraestrutura assíncrona.

**Dependências:** `orchestrator_hibrido_alpha0e.py`, `orchestrator_hibrido_alpha0b.py`, `gui_ctk.py` na pasta-pai de `test_cli/`. Sem dependências externas além da biblioteca padrão.

### Casos de Teste

| Arquivo | Tipo | Casos | Componente |
|---|---|---|---|
| `test_event_bus.py` | `unittest` | 4 | `EventBus` — três filas independentes e isolamento entre elas |
| `test_token_manager.py` | `unittest` | 3 | `TokenManager` — aquisição, liberação e controle de cooldown |
| `test_storage_worker_isolation.py` | `unittest` | 1 | `BufferedStorageWorker` — não drena fila de notificações |
| `test_gui_smoke.py` | `unittest` | 1 | `gui_ctk` — módulo importável sem display |
| `test_queue_separation.py` | script | 3 funções | Separação de filas, produtores concorrentes, estado de tokens |
| `test_cooldown.py` | script | 1 fluxo | Notificação de cooldown com threads e encerramento limpo |
| **Total `unittest`** | | **9** | |

### Como Executar

```bash
# Todos os testes unittest via runner
cd Gabriel/
python test_cli/run_all.py

# Testes unittest individualmente
python -m unittest test_cli.test_event_bus -v
python -m unittest test_cli.test_token_manager -v
python -m unittest test_cli.test_storage_worker_isolation -v
python -m unittest test_cli.test_gui_smoke -v

# Scripts de integração (execução direta)
python test_cli/test_queue_separation.py
python test_cli/test_cooldown.py
```

> ⚠️ Os scripts `test_cooldown.py` e `test_queue_separation.py` **não usam `unittest.TestCase`** e não são incluídos na descoberta automática do `run_all.py`. Execute-os diretamente.

---

## 🧑‍💻 Paulo — API de Grafos por Eventos

Suite de testes para a **API de Grafos orientada a eventos**, validando operações de grafo, algoritmos de travessia e o pipeline de mineração via `EventBus`.

**Dependências:** pacote `grafo/` com os módulos `core/application.py`, `events/event.py`, `events/event_type.py` e `graph/abstract_graph.py`. Sem dependências externas.

### Casos de Teste

Todos os testes operam disparando `Events` no `EventBus` da `Application`, validando a integração end-to-end entre handlers e estrutura de grafo.

| Teste | Eventos Utilizados | O que valida |
|---|---|---|
| `test_create_graph` | `GRAPH_CREATE` | Grafo criado e registrado com `vertex_count == 5` e `rep_type == LIST` |
| `test_add_edge` | `GRAPH_CREATE`, `GRAPH_ADD_EDGE` | Aresta `0→1` adicionada; `has_edge(0,1) == True` e `edge_count == 1` |
| `test_bfs` | `GRAPH_CREATE`, `GRAPH_ADD_EDGE` ×2, `ALGO_BFS` | BFS a partir do vértice `0` retorna `[0, 1, 2]` na ordem correta |
| `test_shortest_path` | `GRAPH_CREATE`, `GRAPH_ADD_EDGE` ×2, `GRAPH_SET_EDGE_WEIGHT` ×2, `ALGO_SHORTEST_PATH` | Caminho mínimo `0→2` com distância `15.0` (pesos 10+5) |
| `test_csv_load_and_build` | `MINING_LOAD_CSV`, `MINING_BUILD_INTEGRATED_GRAPH` | CSV com 3 usuários gera grafo com pesos corretos por tipo de interação |
| **Total** | | **5** |

### Como Executar

```bash
# A partir da pasta Paulo/ (com o pacote grafo disponível no path)
python -m unittest test_suite -v

# Diretamente
python test_suite.py
```

> ⚠️ **Atenção:** o pacote importado é `grafo` (com "a"). Verifique se o pacote está disponível no `sys.path` antes de executar.

---

## 🧑‍💻 Daniel — Motor de Grafos (`graph_engine`)

Suite de testes para o pacote `graph_engine`, validando a API de grafos dirigidos ponderados e o módulo de análise de redes.

**Dependências:** pacote `graph_engine/` com `abstract_graph.py`, `implementations.py` e `analysis.py` na pasta-pai de `tests/`. Sem dependências externas.

### Casos de Teste

#### `test_graphs.py` — Contrato de Grafo (Contract Testing)

O padrão **Contract Testing** é aplicado: `GraphContract` define um conjunto de testes executados sobre `AdjacencyListGraph` e `AdjacencyMatrixGraph`, garantindo comportamento equivalente nas duas implementações.

| Teste | O que valida |
|---|---|
| `test_add_is_idempotent_and_remove` | `addEdge` duplicado não duplica aresta; `removeEdge` limpa o grafo |
| `test_simple_graph_rejects_loops` | `addEdge(u, u)` lança `GraphError` |
| `test_invalid_vertices_raise` | Índice negativo ou fora do intervalo lança `IndexError` |
| `test_relations_and_degrees` | `isSucessor`, `isPredessor`, `isDivergent`, `isConvergent`, `isIncident`, graus de entrada/saída |
| `test_weights_and_labels` | Pesos e rótulos de vértice/aresta; erro ao ponderar aresta inexistente |
| `test_connectivity_completeness_and_export` | `isConnected`, `isCompleteGraph` e exportação GEXF válida para Gephi |

> Cada teste roda **duas vezes** (List e Matrix) → **10 casos no total**.

#### `test_analysis.py` — Métricas de Análise de Rede

Testa todas as funções do `analysis.py` sobre um grafo de cadeia `0 → 1 → 2`.

| Métrica | Asserção |
|---|---|
| `density` | `≈ 1/3` para 2 arestas em 3 vértices |
| `degree_centrality` | Vértice central (1) > vértice extremo (0) |
| `betweenness_centrality` | Vértice intermediário (1) tem betweenness > 0 |
| `closeness_centrality` | Vértice de origem (0) tem closeness > 0 |
| `pagerank` | Soma de todos os scores converge para `1.0` |
| `clustering_coefficient` | Vértice central sem triângulos tem coeficiente `0.0` |
| `assortativity` | Retorna `float` válido |

| Arquivo | Classes de Teste | Casos |
|---|---|---|
| `test_graphs.py` | `TestAdjacencyList`, `TestAdjacencyMatrix` | 10 (5 × 2 implementações) |
| `test_analysis.py` | `TestAnalysis` | 1 (7 métricas) |
| **Total** | | **11** |

### Como Executar

```bash
# Todos os testes (a partir de Daniel/)
python -m unittest discover -s tests -v

# Arquivo específico
python -m unittest tests.test_graphs -v
python -m unittest tests.test_analysis -v

# Diretamente
python tests/test_graphs.py
python tests/test_analysis.py
```

---

## 📊 Resumo Consolidado

| Programador | Arquivos | Casos `unittest` | Scripts de Integração | Total de Verificações |
|---|---|---|---|---|
| Gabriel | 6 | 9 | 2 (4 funções) | 9 unittest + 4 fluxos |
| Paulo | 1 | 5 | — | 5 |
| Daniel | 2 | 11 | — | 11 |
| **Total** | **9** | **25** | **2** | **29+** |

---

## 🔧 Requisitos Globais

- **Python 3.10+** (todos os programadores)
- **Sem dependências externas** em nenhuma das suites — apenas biblioteca padrão do Python
- Cada suite depende do pacote principal do respectivo programador estar disponível no `sys.path` (ver seção de cada programador)

---

## 🔍 Observações Gerais

- **Gabriel** separa claramente testes `unittest` (descoberta automática via `run_all.py`) de scripts de integração com threads (execução direta).
- **Paulo** adota uma abordagem orientada a eventos para os testes, validando a integração entre handlers e lógica de negócio — indo além do teste unitário puro.
- **Daniel** usa o padrão **Contract Testing**, garantindo que qualquer nova implementação de `AbstractGraph` seja automaticamente validada ao herdar de `GraphContract`.
- Testes com métricas de ponto flutuante (Daniel) usam `assertAlmostEqual` para evitar falhas por arredondamento.
- Testes que geram arquivos temporários (Paulo — CSV; Daniel — GEXF) limpam os arquivos após a execução.
