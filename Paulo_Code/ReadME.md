# 👤 Paulo — Implementação Individual (Python + Java)

Implementação individual de **Paulo Henrique Rodrigues Neves** para o Trabalho Prático
de *Teoria dos Grafos e Computabilidade* — PUC Minas, 2026/1.

Esta pasta reúne a versão **principal em Python com GUI Streamlit**, um
**protótipo Java single-thread** e a documentação do trabalho.

---

## 📁 Estrutura da Pasta

```
Paulo_Code/
├── minerador.py                       # Minerador GitHub standalone (CLI)
├── Projeto_Python_com_GUI/
│   ├── app.py / app1.py / main.py     # Entradas alternativas da aplicação
│   ├── test_suite.py                  # Suite de testes unitários
│   ├── sample_github.csv              # Dataset de exemplo
│   ├── temp_mining.csv                # Buffer de mineração corrente
│   ├── streamlit.log                  # Log de execução
│   ├── lib/                           # vis.js, tom-select (visualização web)
│   └── grafo/
│       ├── cli/cli.py                 # Interface por linha de comando
│       ├── core/                      # Application + GraphRegistry
│       ├── events/                    # Event, EventBus, EventType (Pub/Sub)
│       ├── graph/
│       │   ├── abstract_graph.py
│       │   ├── adjacency_list_graph.py
│       │   ├── adjacency_matrix_graph.py
│       │   └── mining/                # Conector de mineração
│       └── handlers/
│           ├── mining_handler.py      # Lida com extração GitHub
│           ├── graph_handler.py       # Constrói grafos a partir do dataset
│           ├── algorithm_handler.py   # Algoritmos clássicos (BFS, DFS, …)
│           └── metrics_handler.py     # Centralidade, densidade, comunidades
├── Prototipo_java_single-thread/      # Protótipo Java (referência histórica)
│   ├── src/                           # Código-fonte Java
│   ├── script's/                      # Scripts auxiliares de build/execução
│   └── README.md
└── Documentacao/Documentacao.tex      # Relatório técnico (template SBC)
```

---

## 🧩 Componentes

### 1. API de Grafos — `grafo/graph/`
- `AbstractGraph` (Python) define o contrato com **enum `RepType`**
  (`LIST` ou `MATRIX`) escolhido na instanciação.
- Atributos compartilhados: `num_vertices` (fixo, `> 0`), `vertex_labels`
  (padrão `"v0"`, `"v1"`, …), `vertex_weights` (padrão `1.0`).
- Implementações concretas:
  - `AdjacencyListGraph` — lista de adjacência (esparsos).
  - `AdjacencyMatrixGraph` — matriz `V×V` (densos).
- API exposta: `add_edge`, `remove_edge`, `has_edge`, `is_successor` /
  `is_predecessor`, `in_degree` / `out_degree`, pesos de vértices e arestas,
  rótulos, verificações de grafo (conectividade, completude, vazio) e
  exportação para Gephi.

### 2. Minerador — `minerador.py` + `grafo/graph/mining/`
- Script standalone que consulta a **API REST do GitHub** e materializa
  *issues*, *comentários* e *pull requests* em CSV/JSON.
- Saídas de trabalho ficam em `sample_github.csv` (referência) e
  `temp_mining.csv` (corrente).

### 3. Handlers — `grafo/handlers/`
Cada handler encapsula uma responsabilidade da aplicação:

| Handler | Responsabilidade |
|---|---|
| `mining_handler.py` | Orquestra a mineração e a persistência em disco |
| `graph_handler.py` | Constrói grafos a partir de CSV/JSON (usuários ↔ interações) |
| `algorithm_handler.py` | BFS, DFS, caminhos mínimos e travessias |
| `metrics_handler.py` | Densidade, centralidade, *clustering*, comunidades |

### 4. Core — `grafo/core/`
- `Application` — coordena o ciclo de vida da aplicação.
- `GraphRegistry` — registro central de grafos ativos, evitando duplicação
  em memória entre handlers.

### 5. Eventos — `grafo/events/`
Implementação **Pub/Sub** própria: `EventBus` distribui `Event` por
`EventType` para handlers inscritos, desacoplando GUI/CLI da lógica de
grafos e mineração.

### 6. Interface Gráfica (Web) — `app.py` / `main.py`
GUI baseada em **Streamlit** com visualização interativa via
**vis.js** (`lib/vis-9.1.2/`) e seletores **tom-select**. Permite:
- Carregar dataset minerado ou de exemplo.
- Construir grafo em lista ou matriz.
- Executar algoritmos e métricas.
- Visualizar a rede e exportar para Gephi.

### 7. Interface por Linha de Comando — `grafo/cli/cli.py`
Equivalente CLI da GUI: aceita comandos para mineração, construção de
grafo, execução de algoritmos e exportação.

### 8. Suite de Testes — `test_suite.py`
Cobertura unitária da API de grafos (ambas as representações), handlers
e ciclo de mineração (mocks da API GitHub). Executável via:
```bash
python -m unittest test_suite -v
```

### 9. Protótipo Java — `Prototipo_java_single-thread/`
Versão histórica em Java single-thread mantida para referência
arquitetural; ver `Prototipo_java_single-thread/README.md`.

---

## 🚀 Como Executar

### Pré-requisitos
- Python **3.10+**
- `pip install streamlit requests pandas`

### Executar a GUI (Streamlit)
```bash
cd Projeto_Python_com_GUI
streamlit run app.py
```

### Executar via CLI
```bash
cd Projeto_Python_com_GUI
python -m grafo.cli.cli --help
```

### Executar mineração isolada
```bash
python minerador.py
```

### Rodar testes
```bash
cd Projeto_Python_com_GUI
python -m unittest test_suite -v
```

---

## 📚 Documentação

`Documentacao/Documentacao.tex` — relatório técnico no template SBC.

---

## 👤 Autor

**Paulo Henrique Rodrigues Neves** — PUC Minas, Engenharia de Computação
Disciplina: *Teoria de Grafos e Computabilidade* — Prof. Leonardo Vilela Cardoso — 2026/1
