# 🔬 Graph Engine — Daniel

Motor de grafos dirigidos ponderados em Python com foco em **análise de redes**. O pacote inclui uma API de grafo completa, duas implementações intercambiáveis (matriz e lista), um módulo de métricas avançadas (centralidade, PageRank, comunidades) e um processador de dados GitHub (`Lapidador`) para construção automática de grafos a partir de issues.

---

## 📁 Estrutura do Projeto

```
Daniel/
└── graph_engine/
    ├── abstract_graph.py    # Classe base abstrata + GraphError
    ├── implementations.py   # AdjacencyMatrixGraph e AdjacencyListGraph
    ├── analysis.py          # Módulo de métricas e análise de redes
    └── lapidador.py         # Processador de dados GitHub → grafo
```

---

## 🧩 Arquitetura

### `GraphError`

Exceção personalizada (herda de `ValueError`) lançada por todas as operações inválidas de domínio (laço, aresta inexistente, vértice inválido, etc.). Permite capturar erros de grafo de forma precisa:

```python
try:
    g.addEdge(0, 0)
except GraphError as e:
    print(e)  # "Grafos simples não permitem laços"
```

---

### `AbstractGraph` (Classe Base)

Contrato em **camelCase** que todas as implementações devem respeitar. Cada instância mantém internamente:

- `_num_vertices` — número de vértices (imutável após criação)
- `_edge_count` — contador de arestas
- `_vertex_labels` — rótulos (padrão: `"0"`, `"1"`, …)
- `_vertex_weights` — pesos dos vértices (padrão: `0.0`)
- `_edge_weights` — dicionário `{(u, v): float}` de pesos de arestas

#### API pública

| Método | Descrição |
|---|---|
| `getVertexCount()` | Número de vértices |
| `getEdgeCount()` | Número de arestas |
| `hasEdge(u, v)` | Verifica existência da aresta `u → v` |
| `addEdge(u, v)` | Adiciona aresta (sem laços) |
| `removeEdge(u, v)` | Remove aresta existente |
| `successors(u)` | Lista de vértices acessíveis a partir de `u` |
| `predecessors(v)` | Lista de vértices que apontam para `v` |
| `isSucessor(u, v)` / `isPredessor(u, v)` | Relações de sucessão |
| `isDivergent(u1,v1, u2,v2)` | Mesmo nó de origem |
| `isConvergent(u1,v1, u2,v2)` | Mesmo nó de destino |
| `isIncident(u, v, x)` | Vértice `x` pertence à aresta `(u,v)` |
| `getVertexInDegree(u)` / `getVertexOutDegree(u)` | Graus de entrada/saída |
| `setVertexLabel(v, label)` / `getVertexLabel(v)` | Rótulo do vértice |
| `setVertexWeight(v, w)` / `getVertexWeight(v)` | Peso do vértice |
| `setEdgeWeight(u, v, w)` / `getEdgeWeight(u, v)` | Peso da aresta (padrão `1.0`) |
| `isConnected()` | Conectividade via DFS bidirecional |
| `isEmptyGraph()` | Sem arestas? |
| `isCompleteGraph()` | Grafo completo? (`E == V*(V-1)`) |
| `exportToGEPHI(path)` | Exporta para GEXF (cria diretórios automaticamente) |

---

### `implementations.py` — Duas Implementações

#### `AdjacencyMatrixGraph`
- Matriz `V×V` de booleanos (`True` = aresta existe)
- `successors(u)` e `predecessors(v)` em O(V)
- Ideal para grafos densos

#### `AdjacencyListGraph`
- `list[set[int]]` — cada posição guarda o conjunto de vizinhos
- `successors(u)` retorna lista ordenada · `predecessors(v)` em O(V)
- Ideal para grafos esparsos

Ambas lançam `GraphError` para laços e operações em arestas inexistentes.

---

## 📐 Módulo de Análise (`analysis.py`)

Conjunto de funções que recebem qualquer instância de `AbstractGraph` e calculam métricas de rede.

### Centralidade

| Função | Descrição |
|---|---|
| `degree_centrality(graph)` | Grau normalizado pelo máximo possível `2(V-1)` |
| `closeness_centrality(graph)` | Inverso da soma das distâncias BFS |
| `betweenness_centrality(graph)` | Fração de caminhos mínimos que passam pelo vértice |

### Algoritmos Globais

| Função | Parâmetros | Descrição |
|---|---|---|
| `pagerank(graph, damping, iterations, tolerance)` | `d=0.85`, `iter=100`, `tol=1e-10` | PageRank com suporte a nós *dangling* e arestas ponderadas |
| `density(graph)` | — | `E / (V * (V-1))` |
| `clustering_coefficient(graph)` | — | Coeficiente de agrupamento por vértice |
| `assortativity(graph)` | — | Correlação de grau entre extremidades de arestas |
| `communities(graph)` | — | Detecção de comunidades por componentes fracamente conexas |
| `bridging_ties(graph, limit)` | `limit=10` | Top vértices por betweenness (pontes entre grupos) |

### Exemplo

```python
from graph_engine.implementations import AdjacencyListGraph
from graph_engine import analysis

g = AdjacencyListGraph(5)
g.addEdge(0, 1); g.addEdge(1, 2); g.addEdge(2, 0)
g.addEdge(3, 4)

print(analysis.degree_centrality(g))
print(analysis.pagerank(g))
print(analysis.communities(g))
# [{0, 1, 2}, {3, 4}]
```

---

## 🔧 Lapidador — Processador de Dados GitHub

A classe `Lapidador` transforma dados brutos de issues do GitHub (formato JSON) em estruturas de interação prontas a serem carregadas num grafo.

### Fluxo de processamento

```
github_dados_minerados.json
         │
         ▼
    Lapidador.lapidar()
         │  ├─ Lê issues (user + closed_by)
         │  ├─ Cria mapa de utilizadores → IDs
         │  ├─ Cria arestas: closer → opener (peso 3 por fecho)
         │  └─ Agrega pesos de arestas repetidas
         ▼
    dados_lapidados.json
    {
      "metadata": { "total_users": N },
      "users":    { "username": id, ... },
      "interactions": [ { "from", "to", "weight" }, ... ]
    }
```

### Regras de negócio

- Apenas interações onde `closed_by ≠ user` geram arestas.
- Utilizadores apagados (`null` no JSON) são ignorados com segurança.
- Cada fecho de issue vale **peso 3** (conforme especificação do guião).
- Arestas repetidas têm o peso acumulado.

### Uso

```python
from graph_engine.lapidador import Lapidador

worker = Lapidador.initialize_work()
output = worker.lapidar()
print(f"Ficheiro gerado: {output}")
```

> ⚠️ Requer o ficheiro `data/github_dados_minerados.json` (gerado pelo `main_miner.py`). Em alternativa, aceita `data/closed_issues_part_01.json` ou o ficheiro na raiz do projeto.

---

## 🚀 Início Rápido

```python
from graph_engine.implementations import AdjacencyMatrixGraph, AdjacencyListGraph

# Grafo simples
g = AdjacencyListGraph(4)
g.setVertexLabel(0, "Alice")
g.setVertexLabel(1, "Bob")

g.addEdge(0, 1)
g.addEdge(1, 2)
g.setEdgeWeight(0, 1, 5.0)

print(g.getEdgeCount())           # 2
print(g.successors(0))            # [1]
print(g.isConnected())            # False (vértice 3 isolado)
print(g.getEdgeWeight(0, 1))      # 5.0

g.exportToGEPHI("output/rede")    # cria output/rede (GEXF)
```

---

## ⚠️ Validações e Exceções

| Situação | Exceção |
|---|---|
| Vértice com índice inválido | `IndexError` |
| Laço (`addEdge(u, u)`) | `GraphError` |
| Remover/ponderar aresta inexistente | `GraphError` |
| `num_vertices < 0` | `GraphError` |

---

## 📤 Exportação para Gephi

```python
g.exportToGEPHI("grafos/rede_social")
# Cria o ficheiro GEXF com nós, pesos e arestas dirigidas
# Diretórios inexistentes são criados automaticamente
```

---

## 🐍 Requisitos

- Python **3.10+** (usa `dict[...]` e `list[...]` como tipos nativos)
- Sem dependências externas
- Módulo `json`, `os`, `collections`, `math` da biblioteca padrão
