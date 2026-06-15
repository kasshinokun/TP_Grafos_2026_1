# Interface Gráfica — Paulo

## Descrição

Interface web desenvolvida com **Streamlit** para análise interativa de grafos. Diferente das demais implementações do projeto, esta solução roda no navegador e oferece um dashboard com visualização dinâmica de grafos, execução de algoritmos clássicos, cálculo de métricas de rede e mineração de dados do GitHub — tudo integrado à arquitetura orientada a eventos (EDA) do projeto.

## Estrutura dos Arquivos

```
Paulo/
├── app.py                          # Aplicação Streamlit principal
└── lib/
    ├── bindings/
    │   └── utils.js                # Utilitários JS para o Vis.js
    ├── tom-select/
    │   ├── tom-select.complete.min.js
    │   └── tom-select.css          # Componente de seleção avançada
    └── vis-9.1.2/
        ├── vis-network.min.js      # Biblioteca de visualização de redes
        └── vis-network.css
```

## Tecnologias

- **Python 3**
- **Streamlit** — framework de interface web para dados
- **PyVis** — geração de visualizações interativas de grafos (renderiza via Vis.js)
- **Pandas** — exibição de tabelas e métricas
- **Vis.js 9.1.2** — biblioteca de visualização de redes (bundled em `lib/`)
- **Tom Select** — componente de seleção avançada (bundled em `lib/`)
- Módulos internos do projeto: `grafo.core.application`, `grafo.events.*`, `grafo.graph.*`

## Funcionalidades

A navegação é feita por um menu lateral com cinco seções:

### 📊 Dashboard
- Seleção de grafo carregado na sessão
- Exibição de métricas rápidas: número de vértices, arestas e tipo de representação
- Visualização interativa do grafo via PyVis (arrastar, zoom, hover com peso)

### 📂 Gerenciar Grafos
- Criação de novos grafos com ID, número de vértices e implementação (`list` ou `matrix`)
- Adição e remoção de arestas com pesos configuráveis
- Operações publicadas no barramento de eventos (EDA)

### 🧩 Algoritmos
- **BFS** e **DFS** com vértice de origem configurável
- **Dijkstra** — caminho mais curto entre dois vértices (exibe caminho e distância)
- **Ordenação Topológica** — detecta ciclos automaticamente
- **Componentes Fortemente Conexos (SCC)** — lista todos os SCCs com seus vértices

### 📈 Métricas e Análise de Redes
- Centralidade de Grau (tabela Top 10)
- Betweenness Centrality (gráfico de barras)
- Closeness Centrality
- PageRank
- Densidade e Assortatividade (correlação de grau)
- Detecção de Comunidades (agrupamento por JSON)
- Bridging Ties — vértices que conectam comunidades diferentes
- Exportação do grafo para GEPHI (`.gexf`)

### 🐙 Mineração GitHub
- Geração de CSV de exemplo para testes
- Upload de CSV de interações reais
- Construção automática de quatro grafos:
  - `graph1` — interações por comentários
  - `graph2` — interações por fechamento de issues
  - `graph3` — interações por revisões de PR
  - `graph_integrated` — grafo consolidado

## Como Executar

```bash
pip install streamlit pandas pyvis
streamlit run app.py
```

A interface abrirá automaticamente no navegador em `http://localhost:8501`.

## Arquitetura

A aplicação usa o padrão **Event-Driven Architecture (EDA)** do projeto. Toda operação (criar grafo, adicionar aresta, rodar algoritmo, calcular métrica) é emitida como um `Event` no barramento (`bus.publish()`), mantendo a lógica de negócio completamente desacoplada da interface.

```
Streamlit UI
     │
     ▼
bus.publish(Event(EventType.X).with_payload(...))
     │
     ▼
Application / Registry (estado da sessão via st.session_state)
```

## Dependências Internas

```
grafo/
├── core/
│   └── application.py    (Application, Registry)
├── events/
│   ├── event.py
│   └── event_type.py     (EventType com todos os comandos)
└── graph/
    ├── abstract_graph.py  (RepType)
    └── mining/
        └── csv_loader.py  (CsvLoader)
```
