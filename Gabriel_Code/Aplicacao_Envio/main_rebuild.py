from lapidador_rebuild import Lapidador
import json
import os
import os.path as manager
from os.path import join as concat_path
from os.path import abspath as absoluto

from grafos.abstract_graph import AbstractGraph
from grafos.implementations import AdjacencyListGraph
from builder import build_graphs

from analysis import (
    degree_centrality, betweenness_centrality, closeness_centrality,
    pagerank, density, assortativity, clustering_coefficient, bridging_ties
)

# ============================
# FUNÇÕES AUXILIARES
# ============================
def get_absoluto(file: str):
    return manager.dirname(absoluto(file))

def get_diretory(name_diretory: str, condition: int = 2) -> str:
    APP_DIR = get_absoluto(__file__)
    if condition == 1:
        return concat_path(APP_DIR, name_diretory)
    else:
        DATA_DIR = concat_path(APP_DIR, name_diretory)
        os.makedirs(DATA_DIR, exist_ok=True)
        return DATA_DIR


def metrics_analysis(dados_path: str):
    """
    Carrega os dados lapidados, constrói os grafos usando as novas implementações
    e calcula métricas de análise de redes.
    """
    with open(dados_path, 'r', encoding='utf-8') as f:
        dados = json.load(f)

    interactions = dados['interactions']   # lista com source, target, type
    users_map = dados['users']             # login -> id

    print("\n--- Construindo grafos com a nova API ---")
    graphs, _ = build_graphs(interactions)   # retorna dicionário com 'integrated', etc.
    graph = graphs["integrated"]

    print(f"Vértices: {graph.getVertexCount()}")
    print(f"Arestas: {graph.getEdgeCount()}")
    print(f"Grafo vazio? {graph.isEmptyGraph()}")
    print(f"Grafo completo? {graph.isCompleteGraph()}")
    print(f"Conectado? {graph.isConnected()}")

    # Cálculo de métricas
    print("\n--- Métricas da Rede Integrada ---")
    deg_cent = degree_centrality(graph)
    bet_cent = betweenness_centrality(graph)
    clo_cent = closeness_centrality(graph)
    pr = pagerank(graph)
    dens = density(graph)
    assort = assortativity(graph)
    clust = clustering_coefficient(graph)
    avg_clust = sum(clust.values()) / max(1, graph.getVertexCount())
    bridges = bridging_ties(graph)

    # Exibe os top 5 para cada métrica
    def top(metric, n=5):
        return sorted(metric.items(), key=lambda x: x[1], reverse=True)[:n]

    print("\nTop 5 Grau (entrada+saída):")
    for v, val in top(deg_cent):
        print(f"  {graph.getVertexLabel(v)}: {val:.6f}")

    print("\nTop 5 Intermediação (Betweenness):")
    for v, val in top(bet_cent):
        print(f"  {graph.getVertexLabel(v)}: {val:.6f}")

    print("\nTop 5 Proximidade (Closeness):")
    for v, val in top(clo_cent):
        print(f"  {graph.getVertexLabel(v)}: {val:.6f}")

    print("\nTop 5 PageRank:")
    for v, val in top(pr):
        print(f"  {graph.getVertexLabel(v)}: {val:.6f}")

    print(f"\nDensidade: {dens:.6f}")
    print(f"Assortatividade: {assort:.6f}")
    print(f"Coeficiente de clustering médio: {avg_clust:.6f}")

    print("\nPontes (bridging ties):")
    for v, score in bridges[:5]:
        print(f"  {graph.getVertexLabel(v)}: {score:.6f}")

    # Exporta para Gephi (caminho absoluto para evitar ambiguidade com cwd)
    gephi_path = concat_path(get_diretory('work', 1), 'grafo_colaboracao.gexf')
    graph.exportToGEPHI(gephi_path)
    print(f"\nGrafo exportado para Gephi em: {gephi_path}")


def main():
    # 1. Lapidar os dados
    print("Iniciando lapidação dos dados...")
    lapidador = Lapidador.initialize_work()
    dados_path = lapidador.lapidar()
    print(f"Dados lapidados com sucesso em: {dados_path}")

    # 2. Análise de métricas usando as novas implementações
    metrics_analysis(dados_path)


if __name__ == "__main__":
    main()
