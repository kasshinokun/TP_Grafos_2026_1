# 👤 Daniel — Implementação Individual (Python)

Implementação individual de **Daniel Lucas Soares Madureira** para o Trabalho Prático de
*Teoria dos Grafos e Computabilidade* — PUC Minas, 2026/1.

Esta pasta reúne, de forma autocontida, todos os módulos desenvolvidos por Daniel:
**API de Grafos**, **Minerador GitHub**, **Interface Gráfica (CustomTkinter)**,
**Cifrador de Token via QR Code** e **Suite de Testes Unitários**.

---

## 📁 Estrutura da Pasta

```
Daniel_Code/
├── core/
│   ├── event_bus.py        # Barramento de eventos Singleton (Pub/Sub)
│   ├── miner_app.py        # Minerador GitHub multi-thread (1 token por thread)
│   └── cypher_token.py     # QRCodeJSONHandler — leitura/escrita de tokens em QR Code
├── graph_engine/
│   ├── abstract_graph.py   # AbstractGraph + GraphError
│   ├── implementations.py  # AdjacencyMatrixGraph e AdjacencyListGraph
│   ├── analysis.py         # Centralidade, PageRank, comunidades, assortatividade
│   └── lapidador.py        # Lapidador — JSON do GitHub → arestas ponderadas
├── tests/
│   ├── test_graphs.py      # Contract testing das duas implementações
│   └── test_analysis.py    # Métricas de análise de rede
├── Documentacao/           # Relatório SBC (.tex/.pdf) e captura da interface
├── data.example.json       # Exemplo de dados de entrada (formato esperado)
├── main_miner.py           # Entry-point do minerador (dispara START_MINING)
└── main_gui.py             # Entry-point da interface gráfica (CustomTkinter)
```

---

## 🧩 Componentes

### 1. API de Grafos — `graph_engine/`
- `AbstractGraph` define o contrato em **camelCase** com todos os métodos exigidos pela especificação:
  `addEdge`, `removeEdge`, `hasEdge`, `successors`, `predecessors`,
  `isSucessor` / `isPredessor`, `isDivergent`, `isConvergent`, `isIncident`,
  `getVertexInDegree` / `getVertexOutDegree`, `getEdgeWeight` / `setEdgeWeight`,
  `getVertexWeight` / `setVertexWeight`, `getVertexLabel` / `setVertexLabel`,
  `isConnected`, `isEmptyGraph`, `isCompleteGraph` e `exportToGEPHI`.
- Duas implementações intercambiáveis: `AdjacencyMatrixGraph` (matriz `V×V`) e
  `AdjacencyListGraph` (`list[set[int]]`).
- Erros de domínio (laço, aresta inexistente, vértice inválido) lançam `GraphError`
  (herda de `ValueError`).

### 2. Módulo de Análise — `graph_engine/analysis.py`
Funções que operam sobre qualquer `AbstractGraph`:

| Categoria | Funções |
|---|---|
| Centralidade | `degree_centrality`, `closeness_centrality`, `betweenness_centrality` |
| Globais | `pagerank` (damping, dangling, pesos), `density`, `clustering_coefficient`, `assortativity` |
| Comunidade | `communities` (componentes fracamente conexas), `bridging_ties` |

### 3. Minerador — `core/miner_app.py` + `main_miner.py`
- Arquitetura **EDA** (Event-Driven) via `EventBus` Singleton.
- `MinerApp` assina o evento `START_MINING` e baixa todas as páginas de *issues*
  em paralelo: **uma thread por token GitHub**, agregando resultados via `Lock`.
- Tokens lidos a partir de um **QR Code** (`token_qr.png`), evitando segredos
  em texto plano no repositório.
- Saída: `data/github_dados_minerados.json` contendo apenas issues onde
  `closed_by ≠ opened_by`.

### 4. Lapidador — `graph_engine/lapidador.py`
Transforma o JSON minerado em estrutura pronta para grafo:
- Cria mapa `username → id`.
- Cada fecho de issue gera aresta `closer → opener` com **peso 3**
  (conforme guião da disciplina).
- Arestas repetidas têm pesos acumulados.
- Saída: `data/dados_lapidados.json`.

### 5. Cifrador de Token — `core/cypher_token.py`
Classe `QRCodeJSONHandler` (versão base) com `gerar_qr_code()` e
`ler_qr_code()`, usada pelo minerador para carregar tokens em memória.

### 6. Interface Gráfica — `main_gui.py`
GUI em **CustomTkinter** (tema dark, 950×650) com painel guiado de 4 etapas:

1. **Lapidar JSONs Brutos** → executa o `Lapidador`.
2. **Construir Grafo** → carrega `dados_lapidados.json` em `AdjacencyListGraph`.
3. **Calcular Centralidade** → exibe Top 5 por *degree centrality*.
4. **Exportar para GEPHI** → grava `data/grafo_github.gexf`.

Layout: painel de controle à esquerda, terminal de execução à direita.

### 7. Suite de Testes — `tests/`
Padrão **Contract Testing**: `GraphContract` define os casos; `TestAdjacencyList`
e `TestAdjacencyMatrix` aplicam o mesmo contrato às duas implementações.

| Arquivo | Casos | Cobertura |
|---|---|---|
| `test_graphs.py` | 10 (5 × 2 impls.) | Idempotência, laços, índices, relações, pesos, conectividade, GEXF |
| `test_analysis.py` | 7 asserções | density, degree, betweenness, closeness, pagerank, clustering, assortativity |

---

## 🚀 Como Executar

### Pré-requisitos
- Python **3.10+** (a API usa `dict[...]`/`list[...]` como tipos nativos)
- Dependências da GUI e do minerador:
  ```bash
  pip install customtkinter requests qrcode pyzbar Pillow
  ```

### Fluxo completo
```bash
# 1. Minerar o repositório alvo (definido em main_miner.py)
python main_miner.py

# 2. Abrir a GUI e executar Lapidar → Construir → Métricas → Gephi
python main_gui.py
```

### Executar os testes
```bash
python -m unittest discover -s tests -v
```

---

## 📤 Saídas Geradas

| Arquivo | Origem | Conteúdo |
|---|---|---|
| `data/github_dados_minerados.json` | `main_miner.py` | Issues com `opened_by` e `closed_by` distintos |
| `data/dados_lapidados.json` | Lapidador | Usuários indexados + arestas ponderadas |
| `data/grafo_github.gexf` | GUI / `exportToGEPHI` | Grafo pronto para visualização no Gephi |

---

## 📚 Documentação

A pasta `Documentacao/` contém o relatório técnico no template **SBC**
(`Documentacao.tex` e PDF gerado) e uma captura da interface (`Interface.png`).

---

## 👤 Autor

**Daniel Lucas Soares Madureira** — PUC Minas, Engenharia de Computação
Disciplina: *Teoria de Grafos e Computabilidade* — Prof. Leonardo Vilela Cardoso — 2026/1
