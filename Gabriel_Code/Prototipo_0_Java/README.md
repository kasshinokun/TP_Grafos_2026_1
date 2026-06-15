# Ferramenta de Análise de Grafos — PUC Minas
## Teoria de Grafos e Computabilidade 2025/2

---

## Arquitetura: Event-Driven Architecture (EDA) Monolítica

A aplicação segue uma arquitetura **EDA (Event-Driven Architecture)** totalmente
in-process, onde cada requisição de função é modelada como um evento que trafega
por um **EventBus** síncrono. Isso simula o padrão request/response de uma API
sem depender de qualquer servidor externo.

```
┌──────────────────────────────────────────────────────────────────────┐
│                         MONÓLITO EDA                                  │
│                                                                        │
│  ┌──────┐   Event    ┌───────────┐   dispatch   ┌──────────────────┐ │
│  │ CLI  │ ──────────▶│ EventBus  │─────────────▶│ GraphHandler     │ │
│  └──────┘            │           │              ├──────────────────┤ │
│                      │  (pub/sub │              │ AlgorithmHandler │ │
│                      │  síncrono)│              ├──────────────────┤ │
│                      │           │              │ MetricsHandler   │ │
│                      └───────────┘              ├──────────────────┤ │
│                            │                    │ MiningHandler    │ │
│                      GraphRegistry              └──────────────────┘ │
│                      (armazena grafos)                                │
└──────────────────────────────────────────────────────────────────────┘
```

### Componentes

| Pacote | Responsabilidade |
|--------|-----------------|
| `events/` | `Event`, `EventType`, `EventHandler` — envelope de mensagem |
| `core/` | `EventBus`, `GraphRegistry`, `Application` — infraestrutura EDA |
| `graph/` | `AbstractGraph`, `AdjacencyMatrixGraph`, `AdjacencyListGraph` |
| `handlers/` | `GraphHandler`, `AlgorithmHandler`, `MetricsHandler`, `MiningHandler` |
| `mining/` | `Interaction`, `CsvLoader` — mineração de dados |
| `cli/` | `CLI` — interface interativa |

---

## Compilação e Execução

### Pré-requisito: Java 17+ com JDK (javac)

```bash
# Ubuntu/Debian
sudo apt install default-jdk

# Verificar
javac --version   # javac 21.x
java  --version   # java 21.x
```

### Compilar

```bash
cd graph-tool
mkdir -p out
find src/main/java -name "*.java" | xargs javac -d out --release 17
```

### Executar testes

```bash
java -cp out br.pucminas.grafo.TestSuite
```

### Executar CLI interativo

```bash
java -cp out br.pucminas.grafo.Main
```

### Script automático

```bash
chmod +x build.sh
./build.sh          # compila + testes
./build.sh run      # compila + CLI
./build.sh tests    # compila + testes
```

---

## Guia rápido do CLI

### Criando e manipulando grafos

```
> create g1 10 list        # grafo com 10 vértices, lista de adjacência
> create g2 5 matrix       # grafo com 5 vértices, matriz de adjacência
> add-edge g1 0 1          # aresta 0→1 (peso padrão 1)
> add-edge g1 0 1 3.5      # aresta 0→1 com peso 3.5
> rem-edge g1 0 1          # remove aresta
> has-edge g1 0 1          # verifica aresta
> degree g1 0              # graus de entrada e saída
> connected g1             # conectividade fraca
> info g1                  # resumo do grafo
> show g1                  # exibe matriz/lista de adjacência
```

### Algoritmos

```
> bfs g1 0                 # BFS a partir do vértice 0
> dfs g1 0                 # DFS a partir do vértice 0
> shortest g1 0 4          # caminho mais curto (Dijkstra) 0→4
> topsort g1               # ordenação topológica (Kahn)
> scc g1                   # componentes fortemente conexos (Kosaraju)
```

### Métricas (Etapa 3)

```
> degree-centrality g1     # centralidade de grau
> betweenness g1           # betweenness centrality (Brandes)
> closeness g1             # closeness centrality
> pagerank g1              # PageRank (iterativo, d=0.85)
> density g1               # densidade da rede
> clustering g1            # coeficiente de aglomeração
> assortativity g1         # assortatividade (correlação de grau)
> communities g1           # detecção de comunidades (Label Propagation)
> bridging g1              # bridging ties
```

### Mineração de dados GitHub (Etapa 1)

```
# Gera CSV de exemplo (10 usuários, 120 interações)
> sample-csv /tmp/github_interactions.csv

# Carrega CSV real extraído do GitHub
> load-csv /caminho/para/interactions.csv

# Constrói os 4 grafos do trabalho de uma vez
> build-graphs /tmp/github_interactions.csv
```

Após `build-graphs`, os grafos `graph1`, `graph2`, `graph3` e
`graph_integrated` ficam disponíveis para análise.

### Análise completa e export

```
> full-analysis graph_integrated    # todas as métricas
> export graph_integrated /tmp/rede # exporta .gexf para o GEPHI
```

---

## Formato do CSV de Interações

```csv
actor,target,type
alice,bob,COMMENT_ON_ISSUE_OR_PR
carol,dave,PR_MERGE
eve,frank,PR_REVIEW_OR_APPROVAL
grace,hank,ISSUE_CLOSED_BY_OTHER
```

Tipos válidos (campo `type`):

| Tipo | Peso |
|------|------|
| `COMMENT_ON_ISSUE_OR_PR` | 2 |
| `ISSUE_CLOSED_BY_OTHER`  | 3 |
| `PR_REVIEW_OR_APPROVAL`  | 4 |
| `PR_MERGE`               | 5 |

Se a coluna `type` for omitida, assume `COMMENT_ON_ISSUE_OR_PR`.

---

## Grafos construídos (Etapa 1)

| ID | Conteúdo | Arestas |
|----|----------|---------|
| `graph1` | Comentários em issues/PRs | simples, não ponderado |
| `graph2` | Fechamento de issues por outro usuário | simples |
| `graph3` | Revisões, aprovações e merges de PRs | simples |
| `graph_integrated` | Todas as interações ponderadas | pesos acumulados |

---

## API de Eventos (equivalente a chamadas de API)

```java
// Criação
bus.publish(new Event(EventType.GRAPH_CREATE)
    .with("graphId", "g")
    .with("numVertices", 10)
    .with("impl", "list"));

// Operação
bus.publish(new Event(EventType.GRAPH_ADD_EDGE)
    .with("graphId", "g")
    .with("u", 0).with("v", 1));

// Consulta com resultado
Event ev = bus.publish(new Event(EventType.METRIC_PAGERANK)
    .with("graphId", "g"));
Map<Integer,Double> pr = ev.getResult();
```

---

## API Obrigatória Implementada (Etapa 2)

- `getVertexCount()` · `getEdgeCount()`
- `hasEdge(u, v)` · `addEdge(u, v)` · `removeEdge(u, v)`
- `isSuccessor(u, v)` · `isPredecessor(u, v)`
- `isDivergent(u1,v1,u2,v2)` · `isConvergent(u1,v1,u2,v2)`
- `isIncident(u, v, x)`
- `getVertexInDegree(u)` · `getVertexOutDegree(u)`
- `setVertexWeight(v,w)` · `getVertexWeight(v)`
- `setEdgeWeight(u,v,w)` · `getEdgeWeight(u,v)`
- `isConnected()` · `isEmptyGraph()` · `isCompleteGraph()`
- `exportToGEPHI(path)` → formato `.gexf`

Restrições atendidas:
- ✓ Grafos simples (sem laços, sem arestas múltiplas)
- ✓ `addEdge` idempotente
- ✓ Exceções para índices inválidos e operações inconsistentes
- ✓ Herança: `AbstractGraph` → `AdjacencyMatrixGraph` / `AdjacencyListGraph`
