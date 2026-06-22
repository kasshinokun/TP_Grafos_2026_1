"""
Apresentação Streamlit — Análise de Redes de Colaboração em
Repositórios GitHub usando Teoria dos Grafos.

Disciplina: Teoria de Grafos e Computabilidade — PUC Minas 2026/1
Orientador: Prof. Leonardo Vilela Cardoso
Equipe: Vinicius Cezar Pereira Menezes, Paulo Henrique Rodrigues Neves,
        Gabriel da Silva Cassino, Daniel Lucas Soares Madureira

Conteúdo alinhado à arquitetura REAL do código-fonte do projeto
(pacotes grafo/, event/, cli/, gui/, miner/) — não à nomenclatura de
um rascunho anterior. Estilo de apresentação (CSS, cards, métricas)
inspirado nos protótipos internos do grupo em Streamlit.
"""
import random

import pandas as pd
import streamlit as st

# ----------------------------------------------------------------------
# Configuração da página
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Redes de Colaboração GitHub — Teoria dos Grafos",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# CSS personalizado
# ----------------------------------------------------------------------
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        color: #0B3D2E;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 700;
    }
    .slide-title {
        font-size: 2rem;
        color: #0B3D2E;
        border-bottom: 3px solid #C9A227;
        padding-bottom: 0.5rem;
        margin-bottom: 1.5rem;
    }
    .category-box {
        background-color: #EAF3EC;
        border: 2px solid #0B3D2E;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .layer-box {
        background-color: #0B3D2E;
        color: #ffffff;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.4rem 0;
    }
    .layer-box code {
        color: #C9A227;
        background-color: rgba(255,255,255,0.08);
    }
    .metric-card {
        background: linear-gradient(135deg, #0B3D2E 0%, #155843 100%);
        color: white;
        padding: 1.4rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.4rem;
    }
    .team-member {
        background-color: #FBF3DC;
        border-left: 4px solid #C9A227;
        padding: 0.5rem 1rem;
        margin: 0.4rem 0;
    }
    .pill {
        display: inline-block;
        background-color: #0B3D2E;
        color: white;
        border-radius: 999px;
        padding: 0.2rem 0.9rem;
        margin: 0.15rem;
        font-size: 0.85rem;
    }
    .warn-box {
        background-color: #FFF4E0;
        border: 2px solid #C9A227;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


REPO_URL = "https://github.com/kasshinokun/TP_Grafos_2026_1"


# ----------------------------------------------------------------------
# Slide 1 — Capa
# ----------------------------------------------------------------------
def slide_capa():
    st.markdown('<p class="main-title">🕸️ Análise de Redes de Colaboração<br>em Repositórios GitHub</p>',
                unsafe_allow_html=True)
    st.markdown("### Usando Teoria dos Grafos")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("#### 📚 Disciplina")
        st.info("Teoria de Grafos e Computabilidade")
    with col2:
        st.markdown("#### 🎓 Instituição")
        st.info("Engenharia de Computação — PUC Minas — 2026/1")
    with col3:
        st.markdown("#### 👨‍🏫 Orientador")
        st.info("Prof. Leonardo Vilela Cardoso")

    st.markdown("---")
    st.markdown("### Equipe")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="team-member">👨‍💻 Vinicius Cezar Pereira Menezes</div>
        <div class="team-member">👨‍💻 Paulo Henrique Rodrigues Neves</div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="team-member">👨‍💻 Gabriel da Silva Cassino</div>
        <div class="team-member">👨‍💻 Daniel Lucas Soares Madureira</div>
        """, unsafe_allow_html=True)

    st.markdown(f"[📂 Repositório no GitHub]({REPO_URL})")


# ----------------------------------------------------------------------
# Slide 2 — Definição do problema
# ----------------------------------------------------------------------
def slide_problema():
    st.markdown('<p class="slide-title">❓ Definição do Problema</p>', unsafe_allow_html=True)

    st.markdown("### Pergunta Central")
    st.success(
        "Como quantificar e visualizar as relações de colaboração entre "
        "desenvolvedores em projetos open-source do GitHub?"
    )

    st.markdown("### Por que Importa?")
    st.markdown(
        "Identificar contribuidores-chave, detectar silos de comunicação e "
        "entender a saúde estrutural de projetos colaborativos de grande escala."
    )

    st.markdown("### Objetivos do Projeto")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - 🔧 Desenvolver API de grafos direcionados e ponderados (lista e matriz de adjacência)
        - ⛏️ Minerar interações reais em repositórios GitHub (issues, PRs, comentários, reviews)
        - 📐 Modelar colaborações como grafos com pesos diferenciados por tipo de interação
        """)
    with col2:
        st.markdown("""
        - 📊 Calcular métricas de centralidade, estrutura e comunidades
        - 🔍 Detectar comunidades e bridging ties entre colaboradores
        - 💻 Disponibilizar tudo via GUI, CLI e arquitetura orientada a eventos
        """)


# ----------------------------------------------------------------------
# Slide 3 — Arquitetura do sistema
# ----------------------------------------------------------------------
def slide_arquitetura():
    st.markdown('<p class="slide-title">🏗️ Arquitetura do Sistema</p>', unsafe_allow_html=True)

    st.markdown("### Camadas da Aplicação")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="layer-box">
        <strong>1. <code>grafo/</code></strong><br>
        Estruturas (<code>AbstractGraph</code>, <code>AdjacencyListGraph</code>,
        <code>AdjacencyMatrixGraph</code>, <code>UndirectedGraph</code>) e
        algoritmos puros em Python (<code>networkx_pure/</code>, <code>utils/</code>)
        </div>
        <div class="layer-box">
        <strong>2. <code>event/</code></strong><br>
        Arquitetura orientada a eventos (EDA): <code>EventBus</code> pub/sub
        híbrido (síncrono/assíncrono) + <code>EventOrchestrator</code>, que
        religa os comandos aos módulos reais de domínio
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="layer-box">
        <strong>3. <code>cli/</code></strong><br>
        Interpretador de comandos textuais sobre a EDA: parsing →
        validação → despacho → formatação de resposta
        </div>
        <div class="layer-box">
        <strong>4. <code>gui/</code> e <code>miner/</code></strong><br>
        Interface gráfica (CustomTkinter) com bridges para testes e
        visualização; mineração multithreaded da API do GitHub
        </div>
        """, unsafe_allow_html=True)

    st.markdown("### Fluxo de Integração")
    st.info(
        "⚡ O `EventOrchestrator` é o ponto único que conecta a GUI, o CLI e "
        "a EDA aos módulos reais de grafo, teste e mineração — nenhuma "
        "lógica de domínio é duplicada entre as camadas."
    )


# ----------------------------------------------------------------------
# Slide 4 — Estrutura de diretórios
# ----------------------------------------------------------------------
def slide_estrutura_diretorios():
    st.markdown('<p class="slide-title">📁 Estrutura de Diretórios e Arquivos</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.code("""
📁 TP_Grafos_2026_1/
├── 📁 grafo/
│   ├── 📁 graph/             # API obrigatória
│   │   ├── abstract_graph.py
│   │   ├── adjacency_list_graph.py
│   │   ├── adjacency_matrix_graph.py
│   │   └── undirected_graph.py
│   ├── 📁 networkx_pure/      # Algoritmos estilo NetworkX
│   │   ├── adapter.py
│   │   ├── transversal.py
│   │   ├── structure.py
│   │   ├── centrality.py
│   │   └── communities.py
│   └── 📁 utils/
│       ├── gexf_parser.py
│       └── graph_structure.py
├── 📁 event/                  # Arquitetura orientada a eventos
│   ├── event_type.py
│   ├── event.py
│   ├── event_bus.py
│   └── event_orchestrator.py
├── 📁 cli/                    # Interpretador de comandos
│   ├── cli_interpreter.py
│   ├── cli_cmd_validator.py
│   ├── cli_requester.py
│   ├── cli_responser.py
│   └── cli_orchestrator.py
├── 📁 gui/
│   ├── 📁 frames/             # Telas (Tkinter)
│   ├── 📁 bridges/            # test_orchestrator.py
│   └── 📁 utils/
├── 📁 miner/                  # Mineração GitHub
│   ├── hybrid_miner.py
│   ├── graph_builder.py
│   ├── qr_handler.py
│   └── rate_limiter.py
└── 📁 tests/                  # unittest (157+ casos)
        """, language="text")
    with col2:
        st.markdown("#### Destaques")
        st.markdown("""
        **`abstract_graph.py`**
        Define a API obrigatória: `add_edge`, `has_edge`, graus, pesos,
        `is_connected`, `export_to_gephi`...

        **`transversal.py`**
        Módulo de funções (não uma classe-fachada): BFS, DFS, Dijkstra,
        Kruskal, Ford-Fulkerson, ordenação topológica...

        **`event_bus.py`**
        Pub/sub híbrido: handlers síncronos por padrão, assíncronos via
        `threading.Thread` + `queue.Queue` quando necessário.

        **`hybrid_miner.py`**
        Mineração multithreaded da API do GitHub, com pool de tokens e
        checkpoint de progresso.
        """)


# ----------------------------------------------------------------------
# Slide 5 — Algoritmos implementados
# ----------------------------------------------------------------------
def slide_algoritmos():
    st.markdown('<p class="slide-title">🧮 Algoritmos de Grafos Implementados</p>', unsafe_allow_html=True)

    algoritmos = [
        ("🚶", "BFS", "Travessia", "Busca em largura — distâncias não ponderadas e closeness centrality."),
        ("🌲", "DFS", "Travessia", "Busca em profundidade — base para SCC (Kosaraju/Tarjan) e ordenação topológica."),
        ("🛤️", "Dijkstra", "Caminhos mínimos", "Menor caminho ponderado a partir de uma origem."),
        ("⚖️", "Bellman-Ford", "Caminhos mínimos", "Suporta pesos negativos; detecta ciclos negativos."),
        ("🔢", "Floyd-Warshall", "Caminhos mínimos", "Distâncias mínimas entre todos os pares de vértices."),
        ("🌳", "Kruskal / Prim", "Árvore geradora mínima", "Duas estratégias clássicas (união-busca / fronteira de custo mínimo)."),
        ("🌊", "Ford-Fulkerson / Edmonds-Karp", "Fluxo em redes", "Fluxo máximo entre fonte e sumidouro."),
        ("🧭", "Kosaraju / Tarjan", "Conectividade", "Componentes fortemente conexos em grafos direcionados."),
        ("📈", "PageRank", "Centralidade", "Importância iterativa por vizinhança; fator de amortecimento 0.85."),
        ("🎯", "Betweenness / Closeness", "Centralidade", "Intermediação e proximidade entre todos os pares."),
        ("🔗", "Clustering / Densidade", "Estrutura", "Coeficiente de agrupamento, densidade, vértices isolados/regulares."),
        ("👥", "Label Propagation", "Comunidades", "Detecção de comunidades + modularidade + bridging ties."),
    ]
    col1, col2 = st.columns(2)
    for i, (emoji, nome, categoria, desc) in enumerate(algoritmos):
        with col1 if i % 2 == 0 else col2:
            st.markdown(f"""
            <div class="category-box">
            <strong>{emoji} {nome}</strong> <span class="pill">{categoria}</span><br>
            <small>{desc}</small>
            </div>
            """, unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Slide 6 — Exemplo: caminhos mínimos (código real do projeto)
# ----------------------------------------------------------------------
def slide_exemplo_caminhos():
    st.markdown('<p class="slide-title">🛤️ Exemplo: Caminhos Mínimos</p>', unsafe_allow_html=True)

    st.markdown("### API real — `grafo/networkx_pure/transversal.py`")
    st.code("""
from grafo.networkx_pure import transversal as tv

# Dijkstra — distâncias e predecessores a partir da origem
dist, pred = tv.dijkstra(graph, source=0)

# Bellman-Ford — suporta pesos negativos
dist, pred, no_negative_cycle = tv.bellman_ford(graph, source=0)

# Floyd-Warshall — todos os pares de vértices
dist_matrix, pred_matrix = tv.floyd_warshall(graph)

# BFS/DFS com reconstrução de caminho
result = tv.bfs(graph, source=0)
caminho = result.path_to(target=12)
""", language="python")

    with st.expander("📊 Resultado simulado (Dijkstra a partir do vértice 0)"):
        df = pd.DataFrame({
            "Vértice": [0, 1, 2, 3, 4],
            "Distância": [0.0, 2.3, 4.1, 1.8, 3.5],
            "Predecessor": ["-", 0, 1, 0, 3],
        })
        st.table(df)
        st.caption("Grafo de exemplo com 5 vértices e arestas ponderadas.")

    st.markdown("### Via CLI (arquitetura orientada a eventos)")
    st.code("""
>_  load filename=graph1.gexf
✅ load_graph (0.003s) — vertex_count: 98, edge_count: 166

>_  dijkstra source=0
✅ run_dijkstra (0.001s) — distances: [...], predecessors: [...]
""", language="text")


# ----------------------------------------------------------------------
# Slide 7 — Exemplo: centralidade (com simulação interativa)
# ----------------------------------------------------------------------
def slide_centralidade():
    st.markdown('<p class="slide-title">🎯 Exemplo: Métricas de Centralidade</p>', unsafe_allow_html=True)

    st.markdown("### Identificando Colaboradores Influentes — `grafo/networkx_pure/centrality.py`")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Degree Centrality")
        st.code("centrality.degree_centrality(adapter)", language="python")
        st.caption("Baseada no número de conexões diretas")

        st.markdown("#### Closeness Centrality")
        st.code("centrality.closeness_centrality(adapter)", language="python")
        st.caption("Proximidade média a todos os outros vértices")
    with col2:
        st.markdown("#### Betweenness Centrality")
        st.code("centrality.betweenness_centrality(adapter)", language="python")
        st.caption("Frequência em caminhos mínimos entre todos os pares")

        st.markdown("#### PageRank")
        st.code("centrality.pagerank(adapter, damping=0.85)", language="python")
        st.caption("Algoritmo iterativo de importância por vizinhança")

    st.markdown("### 🧪 Simulação Interativa: PageRank em uma Rede Pequena")
    num_nodes = st.slider("Número de colaboradores", 5, 20, 10, key="pagerank_slider")
    if st.button("Calcular PageRank Simulado"):
        rng = random.Random(42)  # gerador local — não afeta outros widgets da página
        scores = {i: rng.random() for i in range(num_nodes)}
        total = sum(scores.values())
        scores = {k: v / total for k, v in scores.items()}
        df = pd.DataFrame(list(scores.items()), columns=["Colaborador", "PageRank"])
        df = df.sort_values("PageRank", ascending=False).reset_index(drop=True)
        st.dataframe(df, use_container_width=True)
        st.success(
            f"Colaborador mais influente: **{df.iloc[0]['Colaborador']}** "
            f"com PageRank {df.iloc[0]['PageRank']:.4f}"
        )


# ----------------------------------------------------------------------
# Slide 8 — Fluxo de dados (mineração → grafo → análise)
# ----------------------------------------------------------------------
def slide_fluxo_dados():
    st.markdown('<p class="slide-title">🔄 Fluxo de Dados — Da Coleta à Análise</p>', unsafe_allow_html=True)

    etapas = [
        ("1", "GitHub API", "issues, PRs, comentários, reviews"),
        ("2", "HybridMiner", "multithreading + pool de tokens"),
        ("3", "graph_builder", "filtragem e normalização do CSV"),
        ("4", "AdjacencyListGraph", "vértices e arestas ponderadas"),
        ("5", "networkx_pure", "métricas, centralidade, comunidades"),
    ]
    cols = st.columns(len(etapas))
    for col, (num, nome, desc) in zip(cols, etapas):
        with col:
            st.markdown(f"""
            <div class="metric-card">
            <h3>{num}️⃣</h3>
            <strong>{nome}</strong><br>
            <small>{desc}</small>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("### Saídas Geradas")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("📄 **CSV de interações**\n\nator → alvo, tipo, peso")
    with col2:
        st.markdown("🔗 **4 grafos `.gexf`**\n\nimportáveis no Gephi")
    with col3:
        st.markdown("📈 **Métricas e comunidades**\n\nvia `event/` + `cli/`")


# ----------------------------------------------------------------------
# Slide 9 — Arquitetura orientada a eventos (EDA) + CLI
# ----------------------------------------------------------------------
def slide_eda_cli():
    st.markdown('<p class="slide-title">⚡ Arquitetura Orientada a Eventos (EDA) + CLI</p>', unsafe_allow_html=True)

    st.warning(
        "Botões da GUI, comandos de CLI e (no futuro) uma API HTTP "
        "precisam acionar a **mesma** lógica de negócio sem duplicação. "
        "A solução: um barramento de eventos único."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Pipeline do CLI (`./cli`)")
        st.code("""
texto digitado
    │
    ▼
CliInterpreter.parse      # sintaxe
    │
    ▼
CliCmdValidator.validate  # forma
    │
    ▼
CliRequester.send         # despacha
    │
    ▼
EventOrchestrator.dispatch
    │
    ▼
cli_responser.format_*    # texto de saída
        """, language="text")
    with col2:
        st.markdown("#### `EventBus` híbrido (`./event`)")
        st.code("""
class EventBus:
    def dispatch(self, event, async_=None):
        # síncrono por padrão
        # async_=True roda em threading.Thread
        # + queue.Queue, sem travar a GUI
        ...
""", language="python")
        st.markdown("""
- **Síncrono**: BFS, DFS, info, estrutura
- **Assíncrono**: Floyd-Warshall, suíte de
  testes, construção de grafo via CSV
- **Medido**: ~2.4x de speedup com 5
  categorias de teste em paralelo
        """)

    st.markdown("### Exemplo real de uso")
    st.code("""
>_  load filename=graph1.gexf
✅ load_graph (0.003s, thread=MainThread)
   • vertex_count: 98   • edge_count: 166   • connected: False

>_  run_floyd_warshall
⏳ 'run_floyd_warshall' está rodando em segundo plano...
✅ run_floyd_warshall (0.046s, thread=EventBus-run_floyd_warshall-...)
""", language="text")


# ----------------------------------------------------------------------
# Slide 10 — GraphAdapter e formato GEXF
# ----------------------------------------------------------------------
def slide_adapter_gexf():
    st.markdown('<p class="slide-title">🔌 GraphAdapter e Formato GEXF</p>', unsafe_allow_html=True)

    st.markdown("### `GraphAdapter` — Ponte para Algoritmos Estilo NetworkX")
    st.code("""
from grafo.networkx_pure.adapter import GraphAdapter

adapter = GraphAdapter(adjacency_list_graph)
adapter.number_of_nodes()   # nodes()/successors()/in_degree()...
adapter.successors(0)       # usado por structure, centrality, communities
""", language="python")
    st.caption(
        "Os módulos de análise (structure, centrality, communities) operam "
        "sobre o adapter — nunca sobre a implementação concreta diretamente."
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Exportando (`export_to_gephi`)")
        st.code('graph.export_to_gephi("output.gexf")', language="python")
    with col2:
        st.markdown("#### Importando (`gexf_parser.load_gexf`)")
        st.code('graph = load_gexf("input.gexf")', language="python")

    st.markdown("### Estrutura do Arquivo GEXF")
    st.code("""
<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://gexf.net/1.3" version="1.3">
  <graph defaultedgetype="directed">
    <nodes><node id="0" label="dev_a"/><node id="1" label="dev_b"/></nodes>
    <edges><edge id="0" source="0" target="1" weight="1.5"/></edges>
  </graph>
</gexf>
""", language="xml")
    st.info(
        "`load_gexf` detecta `defaultedgetype` automaticamente e instancia "
        "`UndirectedGraph` quando apropriado — sem forçar sempre lista de adjacência direcionada."
    )


# ----------------------------------------------------------------------
# Slide 11 — Tecnologias utilizadas
# ----------------------------------------------------------------------
def slide_tecnologias():
    st.markdown('<p class="slide-title">🛠️ Tecnologias Utilizadas</p>', unsafe_allow_html=True)

    grupos = [
        ("🐍", "Linguagem", ["Python 3.12+", "ABC (classes abstratas)", "Type hints nativos", "threading / queue"]),
        ("⛏️", "Mineração", ["GitHub REST API v3", "urllib / requests", "ThreadPoolExecutor", "Pool de tokens + QR Code"]),
        ("🔗", "Grafos", ["Implementação própria", "Lista e matriz de adjacência", "GraphAdapter", "Export GEXF (Gephi)"]),
        ("🧪", "Testes", ["unittest (nativo)", "157+ casos de teste", "gui/bridges/test_orchestrator", "pytest (módulo opcional)"]),
        ("📊", "Visualização", ["Gephi (externo)", "GUI CustomTkinter", "Streamlit (esta apresentação)", "JSON / CSV export"]),
        ("📝", "Documentação", ["LaTeX (template SBC)", "Git + GitHub", "README por módulo", "CHANGELOG.md"]),
    ]
    cols = st.columns(3)
    for i, (emoji, titulo, itens) in enumerate(grupos):
        with cols[i % 3]:
            st.markdown(f"#### {emoji} {titulo}")
            st.markdown("\n".join(f"- {item}" for item in itens))


# ----------------------------------------------------------------------
# Slide 12 — Boas práticas de implementação
# ----------------------------------------------------------------------
def slide_boas_praticas():
    st.markdown('<p class="slide-title">✅ Boas Práticas de Implementação</p>', unsafe_allow_html=True)

    praticas = [
        ("📐", "Abstração & Contrato de API",
         ["AbstractGraph define o contrato via ABC",
          "Implementações substituíveis sem mudar clientes",
          "GraphAdapter isola convenções entre camadas"]),
        ("⚡", "Concorrência Segura",
         ["threading.Lock() em estado compartilhado do EventOrchestrator",
          "queue.Queue para resultados assíncronos do EventBus",
          "Pool de tokens rotacionado de forma thread-safe"]),
        ("🔌", "Desacoplamento via Eventos",
         ["EventBus pub/sub entre GUI, CLI e domínio",
          "Handlers religados sem reimplementar lógica",
          "Fácil extensão: novo EventType, novo handler"]),
        ("🔐", "Segurança de Credenciais",
         ["Token nunca em texto plano no código",
          "QR Code cifrado como veículo de transporte",
          "Leitura em memória, sem persistência em disco"]),
        ("🧪", "Validação & Testes",
         ["check_vertex / check_edge em todo acesso à API",
          "unittest por camada (grafo, event, cli, gui)",
          "157+ testes — suíte descoberta dinamicamente"]),
        ("📈", "Escalabilidade",
         ["Lista de adjacência para grafos esparsos",
          "Matriz de adjacência para grafos densos",
          "Despacho assíncrono para algoritmos custosos (Floyd-Warshall)"]),
    ]
    cols = st.columns(2)
    for i, (emoji, titulo, itens) in enumerate(praticas):
        with cols[i % 2]:
            st.markdown(f"#### {emoji} {titulo}")
            for item in itens:
                st.markdown(f"✓ {item}")
            st.markdown("")


# ----------------------------------------------------------------------
# Slide 13 — Testes unitários
# ----------------------------------------------------------------------
def slide_testes():
    st.markdown('<p class="slide-title">🧪 Testes Unitários</p>', unsafe_allow_html=True)

    st.markdown("### Suíte Descoberta Dinamicamente — `gui/bridges/test_orchestrator.py`")
    st.code("""
# TestOrchestrator descobre classes de teste por introspecção
# (inspect.getmembers + issubclass(..., unittest.TestCase))
# e organiza por categoria — sem hardcode de nomes de teste.

CATEGORIES = [
    "Algoritmos de grafos (BFS, DFS, Dijkstra...)",
    "API primitiva do grafo (AbstractGraph)",
    "Estrutura e heurísticas (matriz, lista, graus)",
    "Métricas de redes complexas",
    "Mineração de dados (GitHub miner)",
    "API GraphQL do GitHub (requer pytest)",
]
""", language="python")

    st.markdown("### Cobertura Atual")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Testes totais", "157+", "unittest")
    col2.metric("Categorias", "6", "descobertas dinamicamente")
    col3.metric("Camadas cobertas", "5", "grafo, event, cli, gui, miner")
    col4.metric("Backends", "3", "Lista, Matriz, Não-direcionado")

    st.markdown("### Exemplo de execução via GUI")
    st.code("""
✅ Algoritmos de grafos (BFS, DFS, Dijkstra...): 12/12 passou em 0.004s
✅ Estrutura e heurísticas (matriz, lista, graus): 23/23 passou em 0.011s
✅ API primitiva do grafo (AbstractGraph): 13/13 passou em 0.003s
""", language="text")


# ----------------------------------------------------------------------
# Slide 14 — Resultados esperados / entregáveis
# ----------------------------------------------------------------------
def slide_resultados():
    st.markdown('<p class="slide-title">📦 Resultados Esperados e Entregáveis</p>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(">900", "Issues mineradas")
    col2.metric("4", "Tipos de interação")
    col3.metric("6+", "Métricas calculadas")
    col4.metric("3", "Representações de grafo")

    st.markdown("### Entregáveis do Projeto")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **🔧 API de Grafos**
        Classe abstrata + 3 implementações (lista, matriz, não-direcionado),
        com todos os métodos do guião e export GEXF para Gephi.

        **⛏️ Minerador GitHub**
        Aplicação multithreaded que coleta interações reais (issues, PRs,
        comentários) de repositórios com >5.000 ⭐.
        """)
    with col2:
        st.markdown("""
        **📊 Análise Completa**
        Degree, Closeness, Betweenness, PageRank, Clustering,
        Assortatividade, Comunidades e Bridging Ties.

        **⚡ EDA + CLI**
        Arquitetura orientada a eventos com interpretador de comandos
        textual, testada com paralelismo real via threading.
        """)


# ----------------------------------------------------------------------
# Slide 15 — Contribuições
# ----------------------------------------------------------------------
def slide_contribuicoes():
    st.markdown('<p class="slide-title">🏆 Contribuições do Projeto</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.success(
            "**📚 API de grafos em Python puro**: sem dependências externas, "
            "com lista, matriz e versão não-direcionada compartilhando o "
            "mesmo contrato `AbstractGraph`."
        )
        st.success(
            "**🔌 GraphAdapter**: ponte estável entre a API obrigatória e os "
            "módulos de análise (structure, centrality, communities)."
        )
    with col2:
        st.success(
            "**⚡ Arquitetura orientada a eventos**: `EventBus` híbrido "
            "(síncrono/assíncrono) que religa GUI, CLI e domínio sem "
            "duplicação de lógica."
        )
        st.success(
            "**📈 Análise real**: aplicação em redes de colaboração GitHub, "
            "identificando influentes e comunidades de fato."
        )

    st.markdown("---")
    st.markdown("### 🎯 Resultados Alcançados")
    st.markdown("""
    - ✅ API completa de grafos (3 representações)
    - ✅ Algoritmos cobrindo as principais categorias da teoria dos grafos
    - ✅ Integração real com a API do GitHub
    - ✅ Arquitetura orientada a eventos com CLI próprio
    - ✅ Interface gráfica funcional (CustomTkinter)
    - ✅ 157+ testes unitários, descobertos dinamicamente
    """)


# ----------------------------------------------------------------------
# Slide 16 — Trabalhos futuros
# ----------------------------------------------------------------------
def slide_futuro():
    st.markdown('<p class="slide-title">🔮 Trabalhos Futuros</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 🚀 Otimizações")
        st.markdown("""
        - **multiprocessing**: isolar handlers CPU-bound (Floyd-Warshall
          em grafos muito grandes) do `EventBus`
        - **Cython**: compilação de métodos críticos
        - **GPU**: aceleração com CUDA/OpenCL
        """)
        st.markdown("### 📊 Novos Algoritmos")
        st.markdown("""
        - Coloração de grafos (Welsh-Powell, DSatur)
        - Emparelhamento (Hopcroft-Karp)
        - Detecção de pontes e articulações
        """)
    with col2:
        st.markdown("### 🌐 Integrações")
        st.markdown("""
        - API HTTP sobre o mesmo `EventOrchestrator`
        - Mais fontes: GitLab, Bitbucket
        - Banco de grafos: Neo4j
        """)
        st.markdown("### 🎨 Visualização")
        st.markdown("""
        - Zoom/scroll já implementado no `GraphCanvas`
        - Layouts interativos: D3.js, Plotly
        - Exportação de relatórios em PDF/Word
        """)


# ----------------------------------------------------------------------
# Slide 17 — Obrigado
# ----------------------------------------------------------------------
def slide_obrigado():
    st.markdown('<p class="main-title">🎉 Obrigado!</p>', unsafe_allow_html=True)
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(f"""
        <div style="text-align: center; padding: 2rem;">
        <h2 style="color: #0B3D2E;">Perguntas?</h2>
        <br>
        <p style="font-size: 1.2rem;">
        📂 <a href="{REPO_URL}" target="_blank">github.com/kasshinokun/TP_Grafos_2026_1</a>
        </p>
        <br>
        <p style="font-size: 1rem; color: #666;">
        Teoria de Grafos e Computabilidade<br>
        Engenharia de Computação — PUC Minas — 2026/1
        </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Equipe")
    col1, col2, col3, col4 = st.columns(4)
    col1.info("Vinicius Menezes")
    col2.info("Paulo Neves")
    col3.info("Gabriel Cassino")
    col4.info("Daniel Madureira")
    st.caption("Orientador: Prof. Leonardo Vilela Cardoso")


# ----------------------------------------------------------------------
# Navegação principal
# ----------------------------------------------------------------------
def main():
    st.sidebar.title("🕸️ Redes de Colaboração")
    st.sidebar.markdown("### Navegação")

    slides = {
        "🎬 Capa": slide_capa,
        "❓ Definição do Problema": slide_problema,
        "🏗️ Arquitetura do Sistema": slide_arquitetura,
        "📁 Estrutura de Diretórios": slide_estrutura_diretorios,
        "🧮 Algoritmos Implementados": slide_algoritmos,
        "🛤️ Caminhos Mínimos": slide_exemplo_caminhos,
        "🎯 Centralidade": slide_centralidade,
        "🔄 Fluxo de Dados": slide_fluxo_dados,
        "⚡ EDA + CLI": slide_eda_cli,
        "🔌 GraphAdapter + GEXF": slide_adapter_gexf,
        "🛠️ Tecnologias": slide_tecnologias,
        "✅ Boas Práticas": slide_boas_praticas,
        "🧪 Testes Unitários": slide_testes,
        "📦 Resultados e Entregáveis": slide_resultados,
        "🏆 Contribuições": slide_contribuicoes,
        "🔮 Trabalhos Futuros": slide_futuro,
        "🎉 Obrigado": slide_obrigado,
    }

    selecao = st.sidebar.radio("Selecione o slide:", list(slides.keys()))

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Sobre")
    st.sidebar.info(
        "Apresentação do projeto de Análise de Redes de Colaboração em "
        "Repositórios GitHub, para a disciplina de Teoria de Grafos e "
        "Computabilidade — PUC Minas 2026/1."
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"[📂 Repositório GitHub]({REPO_URL})")

    slides[selecao]()


if __name__ == "__main__":
    main()







