# 📊 Graph API — Paulo

Biblioteca Python para criação e manipulação de **grafos dirigidos ponderados**, com suporte a duas estratégias de representação interna: **Lista de Adjacência** e **Matriz de Adjacência**. A escolha da representação fica a cargo do utilizador no momento da instanciação.

---

## 📁 Estrutura do Projeto

```
Paulo/
└── graph/
    ├── abstract_graph.py         # Classe base abstrata + enum RepType
    ├── adjacency_list_graph.py   # Implementação via lista de adjacência
    └── adjacency_matrix_graph.py # Implementação via matriz de adjacência
```

---

## 🧩 Arquitetura

### `RepType` (Enum)

Define o tipo de representação interna do grafo:

| Valor          | Descrição                  |
|----------------|----------------------------|
| `RepType.LIST`   | Lista de adjacência        |
| `RepType.MATRIX` | Matriz de adjacência       |

---

### `AbstractGraph` (Classe Base)

Contrato comum partilhado pelas duas implementações. Cada instância mantém:

- `num_vertices` — número fixo de vértices (definido na criação, `> 0`)
- `vertex_labels` — rótulos textuais dos vértices (padrão: `"v0"`, `"v1"`, …)
- `vertex_weights` — pesos dos vértices (padrão: `1.0`)
- `rep_type` — tipo de representação (`RepType`)

#### Métodos concretos disponíveis em ambas as implementações

| Método | Descrição |
|---|---|
| `get_vertex_count()` | Retorna o número de vértices |
| `check_vertex(v)` | Valida se `v` é um índice legal |
| `check_edge(u, v)` | Valida `u`, `v` e proíbe laços |
| `is_successor(u, v)` | Verifica se existe aresta `u → v` |
| `is_predecessor(u, v)` | Verifica se existe aresta `v → u` |
| `is_divergent(u1,v1, u2,v2)` | Duas arestas com mesma origem |
| `is_convergent(u1,v1, u2,v2)` | Duas arestas com mesmo destino |
| `is_incident(u, v, x)` | Vértice `x` pertence à aresta `(u,v)` |
| `set/get_vertex_label(v, label)` | Rótulo textual do vértice |
| `set/get_vertex_weight(v, w)` | Peso do vértice |
| `is_connected()` | BFS não-dirigida — grafo é conexo? |
| `is_empty_graph()` | Sem arestas? |
| `is_complete_graph()` | Todas as arestas possíveis existem? |
| `__str__()` | Representação resumida: `ClassName[V=N, E=M]` |

#### Métodos abstratos (implementados pelas subclasses)

`get_edge_count()`, `has_edge()`, `add_edge()`, `remove_edge()`,
`get_vertex_in_degree()`, `get_vertex_out_degree()`,
`set_edge_weight()`, `get_edge_weight()`, `export_to_gephi()`

---

### `AdjacencyListGraph`

Representação interna: `list[dict[int, float]]` — cada posição `i` contém um dicionário `{vizinho: peso}`.

**Métodos adicionais:**

| Método | Descrição |
|---|---|
| `get_neighbors(u)` | Dicionário `{v: weight}` dos vizinhos de `u` |
| `get_successors(u)` | Conjunto dos vértices sucessores de `u` |
| `to_list_string()` | Representação textual da lista de adjacência |
| `export_to_gephi(path)` | Exporta para formato GEXF (Gephi) |

> **Complexidade:** `has_edge` em O(1) · `get_vertex_in_degree` em O(V)

---

### `AdjacencyMatrixGraph`

Representação interna: `list[list[float]]` — matriz V×V onde `0.0` representa ausência de aresta.

**Métodos adicionais:**

| Método | Descrição |
|---|---|
| `get_matrix()` | Retorna a matriz de adjacência completa |
| `to_matrix_string()` | Representação textual formatada da matriz |
| `export_to_gephi(path)` | Exporta para formato GEXF (Gephi) |

> **Complexidade:** `has_edge` em O(1) · `get_vertex_in_degree` em O(V) · uso de memória O(V²)

---

## 🚀 Exemplo de Uso

```python
from graph.adjacency_list_graph import AdjacencyListGraph
from graph.adjacency_matrix_graph import AdjacencyMatrixGraph

# --- Lista de Adjacência ---
g = AdjacencyListGraph(num_vertices=4)

g.set_vertex_label(0, "A")
g.set_vertex_label(1, "B")
g.set_vertex_label(2, "C")
g.set_vertex_label(3, "D")

g.add_edge(0, 1)
g.add_edge(0, 2)
g.add_edge(1, 3)
g.set_edge_weight(0, 1, 2.5)

print(g)                          # AdjacencyListGraph[V=4, E=3]
print(g.get_edge_count())         # 3
print(g.is_successor(0, 1))       # True
print(g.get_vertex_out_degree(0)) # 2
print(g.is_connected())           # True
print(g.to_list_string())

# Exportar para Gephi
g.export_to_gephi("output/meu_grafo")

# --- Matriz de Adjacência ---
m = AdjacencyMatrixGraph(num_vertices=3)
m.add_edge(0, 1)
m.add_edge(1, 2)
print(m.to_matrix_string())
```

---

## ⚠️ Regras e Validações

- O número de vértices deve ser **maior que zero** (`ValueError` caso contrário).
- **Laços são proibidos** — `check_edge(u, u)` lança `ValueError`.
- O peso `0.0` é reservado para indicar **ausência de aresta** na matriz; atribuí-lo via `set_edge_weight` lança `ValueError`.
- Índices de vértice fora do intervalo `[0, num_vertices)` lançam `IndexError`.

---

## 📤 Exportação para Gephi

Ambas as implementações exportam o grafo para o formato **GEXF 1.3**, compatível com o [Gephi](https://gephi.org/):

```python
g.export_to_gephi("grafos/rede")   # gera grafos/rede.gexf
```

O ficheiro gerado inclui nós (com rótulo e peso) e arestas dirigidas ponderadas.

---

## 🐍 Requisitos

- Python **3.10+**
- Sem dependências externas
