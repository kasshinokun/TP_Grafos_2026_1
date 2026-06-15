# 🧪 Testes Unitários — Daniel

Suite de testes unitários para o pacote `graph_engine`, validando a API de grafos dirigidos ponderados e o módulo de análise de redes.

---

## 📁 Estrutura

```
Daniel/
└── tests/
    ├── test_graphs.py     # Contrato de operações de grafo (estrutura + topologia + exportação)
    └── test_analysis.py   # Métricas de análise de rede
```

---

## 🎯 O que é testado

### `test_graphs.py` — Contrato do Grafo

Implementa o padrão **Contract Testing**: a classe `GraphContract` define um conjunto de testes independente da implementação. As subclasses `TestAdjacencyList` e `TestAdjacencyMatrix` aplicam o mesmo contrato sobre as duas implementações concretas, garantindo comportamento equivalente.

| Teste | O que valida |
|---|---|
| `test_add_is_idempotent_and_remove` | `addEdge` duplicado não duplica aresta; `removeEdge` limpa o grafo |
| `test_simple_graph_rejects_loops` | `addEdge(u, u)` lança `GraphError` |
| `test_invalid_vertices_raise` | Índice negativo ou fora do intervalo lança `IndexError` |
| `test_relations_and_degrees` | `isSucessor`, `isPredessor`, `isDivergent`, `isConvergent`, `isIncident`, graus de entrada/saída |
| `test_weights_and_labels` | Pesos de vértice/aresta e rótulos; erro ao ponderar aresta inexistente |
| `test_connectivity_completeness_and_export` | `isConnected`, `isCompleteGraph` e exportação GEXF válida para o Gephi |

> Cada teste é executado **duas vezes**: uma para `AdjacencyListGraph` e outra para `AdjacencyMatrixGraph` → **10 casos no total**.

---

### `test_analysis.py` — Módulo de Análise

Testa todas as funções do `analysis.py` sobre um grafo de cadeia com 3 vértices (`0 → 1 → 2`).

| Função | Asserção |
|---|---|
| `density` | `≈ 1/3` para grafo com 2 arestas em 3 vértices |
| `degree_centrality` | O vértice central (1) tem centralidade maior do que o extremo (0) |
| `betweenness_centrality` | Vértice intermediário (1) tem betweenness > 0 |
| `closeness_centrality` | Vértice de origem (0) tem closeness > 0 |
| `pagerank` | A soma de todos os scores de PageRank converge para `1.0` |
| `clustering_coefficient` | Vértice central sem triângulos tem coeficiente = `0.0` |
| `assortativity` | Retorna um `float` (tipo correto, grafo não se degrada) |

---

## 🔧 Dependências

Os testes importam diretamente do pacote `graph_engine` (localizado na pasta-pai de `tests/`). O `sys.path` é ajustado automaticamente no início de cada arquivo.

```
Daniel/
├── graph_engine/          ← pacote que deve existir
│   ├── abstract_graph.py
│   ├── implementations.py
│   └── analysis.py
└── tests/                 ← esta pasta
    ├── test_graphs.py
    └── test_analysis.py
```

**Sem dependências externas** — apenas biblioteca padrão do Python 3.10+.

---

## ▶️ Como Executar

**Todos os testes de uma vez** (a partir da pasta `Daniel/`):

```bash
python -m unittest discover -s tests -v
```

**Um arquivo específico:**

```bash
python -m unittest tests.test_graphs -v
python -m unittest tests.test_analysis -v
```

**Diretamente pelo arquivo:**

```bash
python tests/test_graphs.py
python tests/test_analysis.py
```

---

## 📊 Resumo da Cobertura

| Arquivo | Classes de Teste | Casos de Teste | Asserções Notáveis |
|---|---|---|---|
| `test_graphs.py` | `TestAdjacencyList`, `TestAdjacencyMatrix` | 10 (5 × 2 impls.) | Idempotência, loops, índices, relações, pesos, conectividade, GEXF |
| `test_analysis.py` | `TestAnalysis` | 1 | 7 métricas (density, degree, betweenness, closeness, pagerank, clustering, assortativity) |
| **Total** | **3** | **11** | |

---

## 🔍 Notas

- A estratégia de contrato garante que qualquer nova implementação de `AbstractGraph` seja validada apenas adicionando uma subclasse de `GraphContract`.
- O teste de exportação GEXF usa `tempfile.TemporaryDirectory` — não deixa arquivos residuais após a execução.
- `test_analysis.py` usa `assertAlmostEqual` para métricas de ponto flutuante, evitando falhas por arredondamento.
