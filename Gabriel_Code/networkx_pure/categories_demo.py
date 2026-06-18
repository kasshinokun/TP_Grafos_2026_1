"""
Demonstrações executáveis das 11 categorias do manual NetworkX.

Cada função `cat_XX_*` recebe um `AbstractGraph` do projeto, envolve-o
no `GraphAdapter` e devolve um dicionário plano e legível com os
resultados — pronto para ser apresentado na nova aba Tkinter do TCC.
"""
from __future__ import annotations

from typing import Any, Dict

from grafo.graph.abstract_graph import AbstractGraph

from .adapter import wrap
from .pure_networkx import PureNetworkX


CATEGORY_NAMES = [
    "0. Estado (Direcionado ↔ Não Direcionado)",
    "1. Caminhamentos (BFS, DFS, Topológica)",
    "2. Conectividade (SCC, Articulações, Pontes)",
    "3. Árvores Geradoras (Kruskal, Prim)",
    "4. Caminhos Mínimos (Dijkstra, Bellman-Ford, Floyd-Warshall)",
    "5. Fluxo em Redes (Edmonds-Karp, Corte Mínimo)",
    "6. Isomorfismo & Planaridade",
    "7. Centralidade (Degree, Closeness, Betweenness, PageRank)",
    "8. Clustering & Estrutura (Densidade, Diâmetro)",
    "9. Comunidades (Label Propagation, Modularidade)",
    "10. Geradores (Erdős-Rényi, Barabási-Albert, Watts-Strogatz)",
    "11. Álgebra Linear & Layouts",
]


def _safe(callable_, *args, **kw):
    try:
        return callable_(*args, **kw)
    except Exception as exc:  # noqa: BLE001
        return f"<n/a: {type(exc).__name__}: {exc}>"


def _dist_only(result):
    return result[0] if isinstance(result, tuple) else result


# ----------------------------------------------------------------------- 0
def cat_00_state(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    try:
        with PureNetworkX.undirected_context(a):
            n_undirected = a.getEdgeCount()
    except Exception as exc:  # noqa: BLE001
        n_undirected = f"<n/a: {exc}>"
    return {"vértices": a.getVertexCount(),
            "arestas (direcionado)": g.get_edge_count(),
            "arestas (visão não-direcionada)": n_undirected}


# ----------------------------------------------------------------------- 1
def cat_01_traversals(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"bfs(0)": PureNetworkX.bfs(a, 0),
            "dfs(0)": PureNetworkX.dfs(a, 0),
            "topological_sort": _safe(PureNetworkX.topological_sort, a)}


# ----------------------------------------------------------------------- 2
def cat_02_connectivity(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"tarjan_scc": PureNetworkX.tarjan_scc(a),
            "weakly_connected_components": _safe(PureNetworkX.connected_components, a),
            "articulation_points": _safe(PureNetworkX.articulation_points, a),
            "bridges": _safe(PureNetworkX.bridges, a)}


# ----------------------------------------------------------------------- 3
def cat_03_trees(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"is_tree": _safe(PureNetworkX.is_tree, a),
            "kruskal_mst": _safe(PureNetworkX.kruskal_mst, a),
            "prim_mst":   _safe(PureNetworkX.prim_mst, a, 0)}


# ----------------------------------------------------------------------- 4
def cat_04_shortest_paths(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"dijkstra(0) — distâncias": _safe(lambda: _dist_only(PureNetworkX.dijkstra(a, 0))),
            "bellman_ford(0) — distâncias": _safe(lambda: _dist_only(PureNetworkX.bellman_ford(a, 0))),
            "floyd_warshall[0]": _safe(lambda: PureNetworkX.floyd_warshall(a)[0])}


# ----------------------------------------------------------------------- 5
def cat_05_flow(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    n = a.getVertexCount()
    if n < 2:
        return {"info": "grafo com menos de 2 vértices"}
    s, t = 0, n - 1
    return {"edmonds_karp(0→n-1)": _safe(PureNetworkX.edmonds_karp, a, s, t),
            "min_cut(0→n-1)":      _safe(PureNetworkX.min_cut, a, s, t)}


# ----------------------------------------------------------------------- 6
def cat_06_iso_planarity(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"is_isomorphic(g, g)": _safe(PureNetworkX.is_isomorphic, a, a),
            "is_planar":           _safe(PureNetworkX.is_planar, a)}


# ----------------------------------------------------------------------- 7
def cat_07_centrality(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"degree_centrality":     PureNetworkX.degree_centrality(a),
            "closeness_centrality":  _safe(PureNetworkX.closeness_centrality, a),
            "betweenness_centrality":_safe(PureNetworkX.betweenness_centrality, a),
            "pagerank":              _safe(PureNetworkX.pagerank, a),
            "eigenvector":           _safe(PureNetworkX.eigenvector_centrality, a),
            "katz":                  _safe(PureNetworkX.katz_centrality, a)}


# ----------------------------------------------------------------------- 8
def cat_08_clustering(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"density":            PureNetworkX.density(a),
            "average_clustering": _safe(PureNetworkX.average_clustering, a),
            "transitivity":       _safe(PureNetworkX.transitivity, a),
            "diameter":           _safe(PureNetworkX.diameter, a),
            "radius":             _safe(PureNetworkX.radius, a)}


# ----------------------------------------------------------------------- 9
def cat_09_communities(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    comms = _safe(PureNetworkX.label_propagation_communities, a)
    mod = _safe(PureNetworkX.modularity, a, comms) if isinstance(comms, list) else "n/a"
    return {"label_propagation_communities": comms, "modularity": mod}


# ----------------------------------------------------------------------- 10
def cat_10_generators(_: AbstractGraph) -> Dict[str, Any]:
    er = PureNetworkX.erdos_renyi_graph(6, 0.4, seed=42)
    ba = PureNetworkX.barabasi_albert_graph(8, 2, seed=42)
    ws = PureNetworkX.watts_strogatz_graph(8, 2, 0.3, seed=42)
    cmp_ = PureNetworkX.complete_graph(4)
    return {"erdos_renyi_graph(6, 0.4) arestas":   er.getEdgeCount(),
            "barabasi_albert_graph(8, 2) arestas": ba.getEdgeCount(),
            "watts_strogatz_graph(8, 2, 0.3) arestas": ws.getEdgeCount(),
            "complete_graph(4) arestas":           cmp_.getEdgeCount()}


# ----------------------------------------------------------------------- 11
def cat_11_linalg_io(g: AbstractGraph) -> Dict[str, Any]:
    a = wrap(g)
    return {"adjacency_matrix": PureNetworkX.adjacency_matrix(a),
            "laplacian_matrix": _safe(PureNetworkX.laplacian_matrix, a),
            "incidence_matrix": _safe(PureNetworkX.incidence_matrix, a),
            "circular_layout":  PureNetworkX.circular_layout(a)}


DEMOS = [
    cat_00_state, cat_01_traversals, cat_02_connectivity, cat_03_trees,
    cat_04_shortest_paths, cat_05_flow, cat_06_iso_planarity,
    cat_07_centrality, cat_08_clustering, cat_09_communities,
    cat_10_generators, cat_11_linalg_io,
]


def run_category_demo(category_index: int, graph: AbstractGraph) -> Dict[str, Any]:
    """Executa a categoria `category_index` (0..11) sobre `graph`."""
    if not 0 <= category_index < len(DEMOS):
        raise IndexError(f"Categoria fora do intervalo: {category_index}")
    return DEMOS[category_index](graph)
