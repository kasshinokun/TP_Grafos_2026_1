# Interface Gráfica — Daniel

## Descrição

Interface desktop desenvolvida com **CustomTkinter** para análise de grafos aplicada à Teoria dos Grafos. A aplicação oferece um painel de controle com fluxo de trabalho sequencial e um terminal de execução integrado para exibir logs em tempo real.

## Arquivo

| Arquivo | Descrição |
|---|---|
| `main_gui.py` | Arquivo único da aplicação |

## Tecnologias

- **Python 3**
- **CustomTkinter** — interface moderna com tema escuro
- Módulos internos do projeto: `graph_engine.lapidador`, `graph_engine.implementations`, `graph_engine.analysis`

## Funcionalidades

O painel lateral guia o usuário em quatro etapas sequenciais:

1. **Lapidar JSONs Brutos** — aciona o `Lapidador` para extrair e processar os dados brutos coletados
2. **Construir Grafo** — lê o arquivo `dados_lapidados.json` e constrói um grafo de lista de adjacência com os usuários e interações
3. **Calcular Centralidade** — calcula métricas de centralidade de grau e exibe o Top 5 de usuários mais influentes
4. **Exportar para GEPHI** — gera o arquivo `.gexf` em `data/grafo_github.gexf` para visualização no Gephi

## Como Executar

```bash
pip install customtkinter
python main_gui.py
```

## Dependências Internas

O script espera encontrar os seguintes módulos no `PYTHONPATH` ou na mesma pasta raiz do projeto:

```
graph_engine/
├── lapidador.py     (classe Lapidador)
├── implementations.py (AdjacencyListGraph)
└── analysis.py      (degree_centrality)
```

O arquivo de dados processados é buscado automaticamente em `data/dados_lapidados.json` ou na raiz do projeto.

## Layout

```
┌─────────────────┬──────────────────────────────────────┐
│  Painel de      │                                      │
│  Controle       │       Terminal de Execução           │
│                 │                                      │
│  [1. Lapidar]   │  > Sistemas iniciados...             │
│  [2. Construir] │  > Grafo construído com sucesso!     │
│  [3. Métricas]  │  > Top 5 usuários: ...               │
│  [4. Gephi]     │                                      │
└─────────────────┴──────────────────────────────────────┘
```

## Tema Visual

- Aparência: **Dark** (fixo)
- Paleta: **Blue** (CustomTkinter padrão)
- Resolução inicial: 950 × 650 px
