"""Grafos sintéticos com resultados analíticos conhecidos."""
from grafo.graph.adjacency_list_graph import AdjacencyListGraph

def complete_graph(n: int) -> AdjacencyListGraph:
    """Grafo completo K_n. Entrene: n*(n-1), densidade: 1.0"""
    G = AdjacencyListGraph(n)
    for i in range(n):
        for j in range(n):
            if i != j:
                G.add_edge(i, j)
    return G

def star_graph(n: int) -> AdjacencyListGraph:
    """Estrela: nó 0 conectado a todos. Centro tem betweenness máximo."""
    G = AdjacencyListGraph(n)
    for i in range(1, n):
        G.add_edge(0, i)
        G.add_edge(i, 0)
    return G

def cycle_graph(n: int) -> AdjacencyListGraph:
    """Ciclo C_n. Closeness uniforme, clustering 0 para n>=4."""
    G = AdjacencyListGraph(n)
    for i in range(n):
        G.add_edge(i, (i + 1) % n)
    return G

def two_cliques_bridge(clique_size: int) -> AdjacencyListGraph:
    """Dois cliques conectados por um nó ponte (bridging tie)."""
    n = 2 * clique_size + 1
    G = AdjacencyListGraph(n)
    bridge = 0
    # Clique 1: bridge + nós 1..clique_size
    for i in range(1, clique_size + 1):
        G.add_edge(bridge, i)
        G.add_edge(i, bridge)
        for j in range(i + 1, clique_size + 1):
            G.add_edge(i, j)
            G.add_edge(j, i)
    # Clique 2: bridge + nós clique_size+1..2*clique_size
    offset = clique_size
    for i in range(1, clique_size + 1):
        u = offset + i
        G.add_edge(bridge, u)
        G.add_edge(u, bridge)
        for j in range(i + 1, clique_size + 1):
            v = offset + j
            G.add_edge(u, v)
            G.add_edge(v, u)
    return G

def path_graph(n: int) -> AdjacencyListGraph:
    """Caminho P_n. Diâmetro = n-1."""
    G = AdjacencyListGraph(n)
    for i in range(n - 1):
        G.add_edge(i, i + 1)
        G.add_edge(i + 1, i)
    return G