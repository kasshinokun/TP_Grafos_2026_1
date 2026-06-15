# 🔍 Minerador — Paulo

Minerador orientado a eventos com arquitetura limpa e tipada, baseado em um `EventBus` fortemente tipado (`EventType` enum), `GraphRegistry` para gerenciamento de grafos em memória e um pipeline de construção de grafos a partir de arquivos CSV.

---

## 📁 Estrutura

```
Paulo/
├── core/
│   └── graph_registry.py          # Registro centralizado de grafos em memória
├── events/
│   ├── event.py                   # Objeto de evento com resultado e estado de erro
│   ├── event_bus.py               # Barramento de eventos tipado (Pub/Sub)
│   └── event_type.py              # Enum com todos os tipos de evento do sistema
├── graph/
│   └── mining/
│       ├── csv_loader.py          # Carrega interações a partir de arquivo CSV
│       └── interaction.py         # Tipos de interação com pesos embutidos (Enum)
└── handler/
    └── mining_handler.py          # Handler que constrói grafos a partir das interações
```

---

## 🏗️ Arquitetura

### `EventBus` (`events/event_bus.py`)

Barramento de eventos com tipagem forte via `EventType` enum. Diferente de strings livres, cada evento é uma constante tipada — reduz erros de digitação e facilita refatoração.

| Método | Descrição |
|---|---|
| `subscribe(event_type, handler)` | Registra um handler para um `EventType` |
| `unsubscribe(event_type, handler)` | Remove um handler específico |
| `publish(event)` | Dispara um `Event` e retorna o mesmo objeto com resultado ou erro |
| `dispatch(event_type)` | Atalho para publicar um evento sem payload |

### `EventType` (`events/event_type.py`)

Enum centralizado com todos os eventos do sistema, organizado por domínio:

| Domínio | Exemplos |
|---|---|
| Gerenciamento de Grafo | `GRAPH_CREATE`, `GRAPH_ADD_EDGE`, `GRAPH_EXPORT_GEPHI` |
| Algoritmos | `ALGO_BFS`, `ALGO_DFS`, `ALGO_SHORTEST_PATH` |
| Métricas de Centralidade | `METRIC_PAGERANK`, `METRIC_BETWEENNESS_CENTRALITY` |
| Métricas de Estrutura | `METRIC_DENSITY`, `METRIC_CLUSTERING_COEFFICIENT` |
| Métricas de Comunidade | `METRIC_COMMUNITY_DETECTION`, `METRIC_BRIDGING_TIES` |
| Mineração de Dados | `MINING_LOAD_CSV`, `MINING_BUILD_GRAPH1_COMMENTS`, `MINING_BUILD_INTEGRATED_GRAPH` |

### `GraphRegistry` (`core/graph_registry.py`)

Registro em memória que mapeia IDs textuais para instâncias de grafo. Permite que diferentes handlers acessem o mesmo grafo sem acoplamento direto.

```python
registry = GraphRegistry()
registry.register("graph1", g)
g = registry.get("graph1")
registry.list_ids()  # {'graph1', 'graph_integrated', ...}
```

---

## 📊 Pipeline de Mineração

### `Interaction` e `InteractionType` (`graph/mining/interaction.py`)

Cada interação entre usuários carrega seu **peso embutido no enum**, alinhado com a especificação do projeto:

| Tipo | Peso |
|---|---|
| `COMMENT_ON_ISSUE_OR_PR` | 2 |
| `ISSUE_CLOSED_BY_OTHER` | 3 |
| `PR_REVIEW_OR_APPROVAL` | 4 |
| `PR_MERGE` | 5 |

### `CsvLoader` (`graph/mining/csv_loader.py`)

Carrega interações de um arquivo CSV com colunas `actor`, `target` e `type`. Ignora laços (`actor == target`) e tipos desconhecidos (usa `COMMENT_ON_ISSUE_OR_PR` como fallback).

Formato esperado do CSV:
```csv
actor,target,type
alice,bob,ISSUE_CLOSED_BY_OTHER
carol,alice,PR_REVIEW_OR_APPROVAL
```

Utilitário para gerar CSV de amostra (útil em testes):
```python
CsvLoader.generate_sample_csv("amostra.csv")  # 120 interações aleatórias, seed=42
```

### `MiningHandler` (`handler/mining_handler.py`)

Handler principal que responde a eventos de mineração e constrói grafos separados por categoria:

| Evento | Grafo gerado | Interações incluídas |
|---|---|---|
| `MINING_LOAD_CSV` | — | Carrega e armazena as interações |
| `MINING_BUILD_GRAPH1_COMMENTS` | `graph1` | Apenas comentários |
| `MINING_BUILD_GRAPH2_CLOSURES` | `graph2` | Apenas fechamentos de issues |
| `MINING_BUILD_GRAPH3_REVIEWS` | `graph3` | Reviews e merges de PR |
| `MINING_BUILD_INTEGRATED_GRAPH` | `graph_integrated` | Todas as interações (peso acumulado) |

No grafo integrado, se a mesma aresta já existe, o peso é **somado** ao existente.

---

## 🚀 Exemplo de Uso

```python
from events.event_bus import EventBus
from events.event_type import EventType
from events.event import Event
from core.graph_registry import GraphRegistry
from handler.mining_handler import MiningHandler

registry = GraphRegistry()
bus = EventBus()

handler = MiningHandler(registry)
handler.register_all(bus)

# Carrega o CSV
ev = Event(EventType.MINING_LOAD_CSV)
ev.set_string("path", "dados/interacoes.csv")
result = bus.publish(ev)
print(f"Interações carregadas: {result.get_result()}")

# Constrói os grafos
bus.dispatch(EventType.MINING_BUILD_GRAPH1_COMMENTS)
bus.dispatch(EventType.MINING_BUILD_GRAPH2_CLOSURES)
bus.dispatch(EventType.MINING_BUILD_INTEGRATED_GRAPH)

g = registry.get("graph_integrated")
print(g)
```

---

## ⚙️ Requisitos

- Python **3.10+**
- Sem dependências externas (apenas biblioteca padrão)
- A implementação de grafo (`AdjacencyListGraph`) vem da **API de Grafos — Paulo** (`graph/adjacency_list_graph.py`)
