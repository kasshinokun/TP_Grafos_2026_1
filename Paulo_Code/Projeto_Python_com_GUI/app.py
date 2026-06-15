import streamlit as st
import pandas as pd
import os
import tempfile
from pyvis.network import Network
import streamlit.components.v1 as components

from grafo.core.application import Application
from grafo.events.event import Event
from grafo.events.event_type import EventType
from grafo.graph.abstract_graph import RepType

# Configuração da Página
st.set_page_config(page_title="Analisador de Grafos - PUC Minas", layout="wide")

# Inicialização da Aplicação (Singleton no estado da sessão)
if 'app' not in st.session_state:
    st.session_state.app = Application()
    st.session_state.bus = st.session_state.app.get_bus()
    st.session_state.registry = st.session_state.app.get_registry()

app = st.session_state.app
bus = st.session_state.bus
registry = st.session_state.registry

def render_graph_viz(graph_id):
    g = registry.get(graph_id)
    net = Network(height="500px", width="100%", directed=True, bgcolor="#ffffff", font_color="black")
    
    n = g.get_vertex_count()
    for i in range(n):
        label = g.get_vertex_label(i)
        weight = g.get_vertex_weight(i)
        net.add_node(i, label=f"{label} (v{i})", title=f"Peso: {weight}", size=15 + weight*2)
    
    for u in range(n):
        for v in range(n):
            if g.has_edge(u, v):
                w = g.get_edge_weight(u, v)
                net.add_edge(u, v, weight=w, title=f"Peso: {w}", label=str(w) if w != 1.0 else "")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
        net.save_graph(tmp.name)
        with open(tmp.name, 'r', encoding='utf-8') as f:
            html = f.read()
    os.unlink(tmp.name)
    components.html(html, height=550)

# Sidebar - Gerenciamento de Grafos
st.sidebar.title("🛠️ Ferramentas")

menu = st.sidebar.selectbox("Navegação", [
    "Dashboard", 
    "Gerenciar Grafos", 
    "Algoritmos", 
    "Métricas", 
    "Mineração GitHub"
])

if menu == "Dashboard":
    st.title("📊 Dashboard de Análise de Grafos")
    st.markdown("""
    Bem-vindo à ferramenta de análise de grafos desenvolvida para a disciplina de **Teoria de Grafos e Computabilidade**.
    Esta interface integra o motor EDA (Event-Driven Architecture) convertido para Python.
    """)
    
    ids = registry.list_ids()
    if not ids:
        st.info("Nenhum grafo carregado. Vá em 'Gerenciar Grafos' ou 'Mineração GitHub' para começar.")
    else:
        selected_id = st.selectbox("Selecione um grafo para visualizar", sorted(list(ids)))
        g = registry.get(selected_id)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Vértices", g.get_vertex_count())
        col2.metric("Arestas", g.get_edge_count())
        col3.metric("Tipo", g.rep_type.name)
        
        render_graph_viz(selected_id)

elif menu == "Gerenciar Grafos":
    st.title("📂 Gerenciamento de Grafos")
    
    with st.expander("➕ Criar Novo Grafo", expanded=True):
        c1, c2, c3 = st.columns(3)
        new_id = c1.text_input("ID do Grafo", "g1")
        n_vertices = c2.number_input("Número de Vértices", min_value=1, value=5)
        impl = c3.selectbox("Implementação", ["list", "matrix"])
        
        if st.button("Criar Grafo"):
            ev = bus.publish(Event(EventType.GRAPH_CREATE)
                            .with_payload("graphId", new_id)
                            .with_payload("numVertices", n_vertices)
                            .with_payload("impl", impl))
            if ev.success: st.success(f"Grafo '{new_id}' criado!")
            else: st.error(ev.error_message)

    with st.expander("🔗 Adicionar/Remover Arestas"):
        ids = sorted(list(registry.list_ids()))
        if ids:
            sel_id = st.selectbox("Grafo", ids, key="edge_sel")
            g = registry.get(sel_id)
            n = g.get_vertex_count()
            
            c1, c2, c3 = st.columns(3)
            u = c1.number_input("Origem (u)", 0, n-1, 0)
            v = c2.number_input("Destino (v)", 0, n-1, 1)
            w = c3.number_input("Peso", value=1.0)
            
            col_a, col_b = st.columns(2)
            if col_a.button("Adicionar Aresta"):
                bus.publish(Event(EventType.GRAPH_ADD_EDGE).with_payload("graphId", sel_id).with_payload("u", u).with_payload("v", v))
                bus.publish(Event(EventType.GRAPH_SET_EDGE_WEIGHT).with_payload("graphId", sel_id).with_payload("u", u).with_payload("v", v).with_payload("weight", w))
                st.rerun()
            
            if col_b.button("Remover Aresta"):
                bus.publish(Event(EventType.GRAPH_REMOVE_EDGE).with_payload("graphId", sel_id).with_payload("u", u).with_payload("v", v))
                st.rerun()
        else:
            st.warning("Crie um grafo primeiro.")

elif menu == "Algoritmos":
    st.title("🧩 Algoritmos de Grafos")
    ids = sorted(list(registry.list_ids()))
    if not ids:
        st.warning("Nenhum grafo disponível.")
    else:
        sel_id = st.selectbox("Selecione o Grafo", ids)
        g = registry.get(sel_id)
        n = g.get_vertex_count()
        
        algo = st.radio("Selecione o Algoritmo", ["BFS", "DFS", "Caminho Mais Curto (Dijkstra)", "Ordenação Topológica", "Componentes Fortemente Conexos (SCC)"])
        
        if algo in ["BFS", "DFS"]:
            src = st.number_input("Vértice de Origem", 0, n-1, 0)
            if st.button("Executar"):
                etype = EventType.ALGO_BFS if algo == "BFS" else EventType.ALGO_DFS
                ev = bus.publish(Event(etype).with_payload("graphId", sel_id).with_payload("source", src))
                st.write(f"Ordem de visita: {ev.result}")
                
        elif algo == "Caminho Mais Curto (Dijkstra)":
            c1, c2 = st.columns(2)
            src = c1.number_input("Origem", 0, n-1, 0)
            dst = c2.number_input("Destino", 0, n-1, n-1)
            if st.button("Calcular"):
                ev = bus.publish(Event(EventType.ALGO_SHORTEST_PATH).with_payload("graphId", sel_id).with_payload("source", src).with_payload("target", dst))
                res = ev.result
                if res["reachable"]:
                    st.success(f"Caminho: {res['path']} | Distância: {res['dist']}")
                else:
                    st.error("Destino inalcançável.")
                    
        elif algo == "Ordenação Topológica":
            if st.button("Executar"):
                ev = bus.publish(Event(EventType.ALGO_TOPOLOGICAL_SORT).with_payload("graphId", sel_id))
                if ev.result is None: st.error("O grafo contém ciclos!")
                else: st.write(f"Sequência: {ev.result}")
                
        elif algo == "Componentes Fortemente Conexos (SCC)":
            if st.button("Executar"):
                ev = bus.publish(Event(EventType.ALGO_STRONGLY_CONNECTED).with_payload("graphId", sel_id))
                st.write(f"Total de SCCs: {len(ev.result)}")
                for i, scc in enumerate(ev.result, 1):
                    st.text(f"SCC {i}: {scc}")

elif menu == "Métricas":
    st.title("📈 Métricas e Análise de Redes")
    ids = sorted(list(registry.list_ids()))
    if not ids:
        st.warning("Nenhum grafo disponível.")
    else:
        sel_id = st.selectbox("Selecione o Grafo", ids)
        g = registry.get(sel_id)
        
        m_type = st.selectbox("Tipo de Métrica", [
            "Centralidade de Grau", 
            "Betweenness Centrality", 
            "Closeness Centrality", 
            "PageRank",
            "Densidade e Assortatividade",
            "Detecção de Comunidades",
            "Bridging Ties"
        ])
        
        if m_type == "Centralidade de Grau":
            ev = bus.publish(Event(EventType.METRIC_DEGREE_CENTRALITY).with_payload("graphId", sel_id))
            df = pd.DataFrame(ev.result.items(), columns=["Vértice", "Valor"]).sort_values("Valor", ascending=False)
            st.table(df.head(10))
            
        elif m_type == "Betweenness Centrality":
            ev = bus.publish(Event(EventType.METRIC_BETWEENNESS_CENTRALITY).with_payload("graphId", sel_id))
            df = pd.DataFrame(ev.result.items(), columns=["Vértice", "Valor"]).sort_values("Valor", ascending=False)
            st.bar_chart(df.set_index("Vértice"))
            
        elif m_type == "PageRank":
            ev = bus.publish(Event(EventType.METRIC_PAGERANK).with_payload("graphId", sel_id))
            df = pd.DataFrame(ev.result.items(), columns=["Vértice", "Rank"]).sort_values("Rank", ascending=False)
            st.write(df)

        elif m_type == "Densidade e Assortatividade":
            ev_d = bus.publish(Event(EventType.METRIC_DENSITY).with_payload("graphId", sel_id))
            ev_a = bus.publish(Event(EventType.METRIC_ASSORTATIVITY).with_payload("graphId", sel_id))
            st.metric("Densidade da Rede", f"{ev_d.result:.4f}")
            st.metric("Assortatividade (Correlação de Grau)", f"{ev_a.result:.4f}")

        elif m_type == "Detecção de Comunidades":
            ev = bus.publish(Event(EventType.METRIC_COMMUNITY_DETECTION).with_payload("graphId", sel_id))
            res = ev.result
            by_comm = {}
            for v, c in res.items():
                if c not in by_comm: by_comm[c] = []
                by_comm[c].append(g.get_vertex_label(v))
            st.write(f"Encontradas {len(by_comm)} comunidades.")
            st.json(by_comm)
            
        elif m_type == "Bridging Ties":
            ev = bus.publish(Event(EventType.METRIC_BRIDGING_TIES).with_payload("graphId", sel_id))
            st.write(f"Vértices que conectam comunidades diferentes: {ev.result}")

        st.divider()
        with st.expander("📤 Exportar para GEPHI"):
            export_path = st.text_input("Caminho do arquivo (.gexf)", f"{sel_id}.gexf")
            if st.button("Exportar"):
                ev = bus.publish(Event(EventType.GRAPH_EXPORT_GEPHI).with_payload("graphId", sel_id).with_payload("path", export_path))
                if ev.success: st.success(f"Exportado com sucesso para {export_path}")
                else: st.error(ev.error_message)

elif menu == "Mineração GitHub":
    st.title("🐙 Mineração de Dados GitHub")
    st.markdown("Carregue interações reais ou gere dados de exemplo para construir os grafos do trabalho.")
    
    c1, c2 = st.columns(2)
    if c1.button("Gerar CSV de Exemplo"):
        path = "sample_github.csv"
        from grafo.graph.mining.csv_loader import CsvLoader
        CsvLoader.generate_sample_csv(path)
        st.success(f"Gerado em {path}")
        
    uploaded_file = st.file_uploader("Ou faça upload de um CSV de interações", type="csv")
    
    if uploaded_file:
        with open("temp_mining.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        if st.button("🚀 Construir Grafos (Etapa 1)"):
            bus.publish(Event(EventType.MINING_LOAD_CSV).with_payload("path", "temp_mining.csv"))
            bus.publish(Event(EventType.MINING_BUILD_GRAPH1_COMMENTS))
            bus.publish(Event(EventType.MINING_BUILD_GRAPH2_CLOSURES))
            bus.publish(Event(EventType.MINING_BUILD_GRAPH3_REVIEWS))
            bus.publish(Event(EventType.MINING_BUILD_INTEGRATED_GRAPH))
            st.success("Grafos 'graph1', 'graph2', 'graph3' e 'graph_integrated' prontos no Dashboard!")
            st.balloons()
