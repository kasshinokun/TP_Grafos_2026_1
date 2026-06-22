# ./grafo/networkx_pure/transversal.py

"""
Algoritmos clássicos de teoria dos grafos – implementação nativa em Python,
sem dependências externas.

Inclui:
  - Travessias: BFS, DFS
  - Conectividade: componentes conexos (não direcionado), componentes fortemente
    conexos (Kosaraju, Tarjan)
  - Árvore geradora mínima: Kruskal, Prim (retornam AdjacencyListGraph)
  - Caminhos mínimos: Dijkstra, Bellman-Ford, Floyd-Warshall
  - Fluxo máximo: Ford-Fulkerson (DFS), Edmonds-Karp (BFS) – retornam (fluxo, AdjacencyListGraph)
  - Ordenação topológica
  - Ciclos: detecção de ciclo (direcionado e não direcionado)
  - Propriedades: verificação de conectividade, bipartição, etc.
"""

from collections import deque, defaultdict
from typing import List, Dict, Optional, Set, Tuple, Any
from grafo.graph.abstract_graph import AbstractGraph
from grafo.graph.undirected_graph import UndirectedGraph
from grafo.graph.adjacency_list_graph import AdjacencyListGraph


# ---------------------------------------------------------------------------
#  1. Travessias (BFS / DFS)
# ---------------------------------------------------------------------------

class TraversalResult:
    """Resultado de BFS/DFS."""
    def __init__(self, order: List[int], predecessor: Dict[int, Optional[int]]):
        self.order = order
        self.predecessor = predecessor
        self.visited = set(order)

    def path_to(self, target: int) -> Optional[List[int]]:
        if target not in self.visited:
            return None
        path = [target]
        node = target
        while self.predecessor.get(node) is not None:
            node = self.predecessor[node]
            path.append(node)
        path.reverse()
        return path


def _successors(graph, u: int) -> Set[int]:
    """Retorna os sucessores de u (arestas u -> v)."""
    if hasattr(graph, "get_successors"):
        return graph.get_successors(u)
    return {v for v in range(graph.get_vertex_count()) if v != u and graph.has_edge(u, v)}


def bfs(graph: AbstractGraph, source: int) -> TraversalResult:
    graph.check_vertex(source)
    order = []
    pred = {source: None}
    visited = {source}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        order.append(u)
        for v in sorted(_successors(graph, u)):
            if v not in visited:
                visited.add(v)
                pred[v] = u
                queue.append(v)
    return TraversalResult(order, pred)


def dfs(graph: AbstractGraph, source: int) -> TraversalResult:
    graph.check_vertex(source)
    order = []
    pred = {source: None}
    visited = {source}
    stack = [source]
    while stack:
        u = stack.pop()
        order.append(u)
        for v in sorted(_successors(graph, u), reverse=True):
            if v not in visited:
                visited.add(v)
                pred[v] = u
                stack.append(v)
    return TraversalResult(order, pred)


def dfs_forest(graph: AbstractGraph) -> List["TraversalResult"]:
    """Executa DFS a partir de todo vértice ainda não visitado, na
    ordem 0, 1, 2, ..., formando a "floresta" de busca em profundidade
    que cobre o grafo inteiro (necessário quando o grafo não é
    fortemente conexo a partir de um único vértice — ex.: para depois
    alimentar algoritmos de SCC como Kosaraju/Tarjan).

    Retorna uma lista de TraversalResult, uma por árvore/componente.
    """
    visited_global = set()
    forest: List[TraversalResult] = []

    for start in range(graph.get_vertex_count()):
        if start in visited_global:
            continue
        result = dfs(graph, start)
        visited_global |= result.visited
        forest.append(result)

    return forest


# ---------------------------------------------------------------------------
#  2. Conectividade
# ---------------------------------------------------------------------------

def _to_undirected(graph: AbstractGraph) -> UndirectedGraph:
    """Converte qualquer grafo (direcionado ou não) para UndirectedGraph."""
    ug = UndirectedGraph(graph.get_vertex_count())
    ug.get_subjacente(graph)
    return ug


def connected_components(graph: AbstractGraph) -> List[List[int]]:
    """Componentes conexos (para grafos não direcionados)."""
    if graph.get_vertex_count() == 0:
        return []
    ug = _to_undirected(graph) if not isinstance(graph, UndirectedGraph) else graph
    visited = set()
    comps = []
    for v in range(ug.get_vertex_count()):
        if v not in visited:
            comp = []
            queue = deque([v])
            visited.add(v)
            while queue:
                u = queue.popleft()
                comp.append(u)
                for nb in ug.get_successors(u):
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            comps.append(comp)
    return comps


# --- Kosaraju (SCC) ---

def _dfs_order(graph, start, visited, order):
    visited.add(start)
    for v in _successors(graph, start):
        if v not in visited:
            _dfs_order(graph, v, visited, order)
    order.append(start)


def _dfs_scc(graph, start, visited, comp):
    visited.add(start)
    comp.append(start)
    for v in _successors(graph, start):
        if v not in visited:
            _dfs_scc(graph, v, visited, comp)


def kosaraju_scc(graph: AbstractGraph) -> List[List[int]]:
    """Componentes fortemente conexos via Kosaraju."""
    n = graph.get_vertex_count()
    visited = set()
    order = []
    for v in range(n):
        if v not in visited:
            _dfs_order(graph, v, visited, order)

    # Grafo reverso (predecessores)
    rev_succ = {v: set() for v in range(n)}
    for u in range(n):
        for v in _successors(graph, u):
            rev_succ[v].add(u)

    def rev_successors(u):
        return rev_succ[u]

    visited.clear()
    sccs = []
    while order:
        v = order.pop()
        if v not in visited:
            comp = []
            stack = [v]
            visited.add(v)
            while stack:
                x = stack.pop()
                comp.append(x)
                for y in rev_successors(x):
                    if y not in visited:
                        visited.add(y)
                        stack.append(y)
            sccs.append(comp)
    return sccs


# --- Tarjan (SCC) ---

def tarjan_scc(graph: AbstractGraph) -> List[List[int]]:
    """Componentes fortemente conexos via Tarjan (iterativo)."""
    n = graph.get_vertex_count()
    index = 0
    indices = [-1] * n
    lowlink = [0] * n
    onstack = [False] * n
    stack = []
    sccs = []

    def strongconnect(v):
        nonlocal index
        indices[v] = index
        lowlink[v] = index
        index += 1
        stack.append(v)
        onstack[v] = True

        for w in _successors(graph, v):
            if indices[w] == -1:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif onstack[w]:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            comp = []
            while True:
                w = stack.pop()
                onstack[w] = False
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in range(n):
        if indices[v] == -1:
            strongconnect(v)
    return sccs


# ---------------------------------------------------------------------------
#  3. Árvore Geradora Mínima (Kruskal e Prim) – retornam AdjacencyListGraph
# ---------------------------------------------------------------------------

def kruskal(graph: AbstractGraph) -> AdjacencyListGraph:
    """
    Árvore geradora mínima – Kruskal.
    Retorna um AdjacencyListGraph contendo apenas as arestas da MST.
    """
    ug = _to_undirected(graph)
    n = ug.get_vertex_count()
    edges = []
    for u in range(n):
        for v, w in ug.adj[u].items():
            if u < v:  # cada aresta uma única vez (não direcionada)
                edges.append((w, u, v))
    edges.sort()

    parent = list(range(n))
    rank = [0] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False
        if rank[rx] < rank[ry]:
            parent[rx] = ry
        elif rank[rx] > rank[ry]:
            parent[ry] = rx
        else:
            parent[ry] = rx
            rank[rx] += 1
        return True

    result = AdjacencyListGraph(n)
    result.vertex_labels = dict(ug.vertex_labels)
    result.vertex_weights = list(ug.vertex_weights)

    mst_edges = 0
    for w, u, v in edges:
        if union(u, v):
            result.add_edge(u, v)
            result.set_edge_weight(u, v, w)
            mst_edges += 1
            if mst_edges == n - 1:
                break
    return result


def prim(graph: AbstractGraph, start: int = 0) -> AdjacencyListGraph:
    """
    Árvore geradora mínima – Prim.
    Retorna um AdjacencyListGraph com as arestas da MST.
    """
    ug = _to_undirected(graph)
    n = ug.get_vertex_count()
    if n == 0:
        return AdjacencyListGraph(0)

    visited = [False] * n
    min_weight = [float('inf')] * n
    parent = [-1] * n
    min_weight[start] = 0

    for _ in range(n):
        u = -1
        best = float('inf')
        for i in range(n):
            if not visited[i] and min_weight[i] < best:
                best = min_weight[i]
                u = i
        if u == -1:
            break
        visited[u] = True
        for v, w in ug.adj[u].items():
            if not visited[v] and w < min_weight[v]:
                min_weight[v] = w
                parent[v] = u

    result = AdjacencyListGraph(n)
    result.vertex_labels = dict(ug.vertex_labels)
    result.vertex_weights = list(ug.vertex_weights)

    for v in range(n):
        if parent[v] != -1:
            u = parent[v]
            w = min_weight[v]
            result.add_edge(u, v)
            result.set_edge_weight(u, v, w)
    return result


# ---------------------------------------------------------------------------
#  4. Caminhos mínimos
# ---------------------------------------------------------------------------

def dijkstra(graph: AbstractGraph, source: int) -> Tuple[List[float], List[Optional[int]]]:
    """Dijkstra – retorna (distâncias, predecessores)."""
    n = graph.get_vertex_count()
    dist = [float('inf')] * n
    pred = [None] * n
    dist[source] = 0
    visited = [False] * n

    for _ in range(n):
        u = -1
        best = float('inf')
        for i in range(n):
            if not visited[i] and dist[i] < best:
                best = dist[i]
                u = i
        if u == -1:
            break
        visited[u] = True
        for v in _successors(graph, u):
            w = graph.get_edge_weight(u, v)
            alt = dist[u] + w
            if alt < dist[v]:
                dist[v] = alt
                pred[v] = u
    return dist, pred


def bellman_ford(graph: AbstractGraph, source: int) -> Tuple[List[float], List[Optional[int]], bool]:
    """Bellman-Ford – retorna (distâncias, predecessores, sem_ciclo_negativo)."""
    n = graph.get_vertex_count()
    dist = [float('inf')] * n
    pred = [None] * n
    dist[source] = 0

    for _ in range(n - 1):
        updated = False
        for u in range(n):
            for v in _successors(graph, u):
                w = graph.get_edge_weight(u, v)
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    pred[v] = u
                    updated = True
        if not updated:
            break

    # Detecção de ciclo negativo
    for u in range(n):
        for v in _successors(graph, u):
            w = graph.get_edge_weight(u, v)
            if dist[u] + w < dist[v]:
                return dist, pred, False
    return dist, pred, True


def floyd_warshall(graph: AbstractGraph) -> Tuple[List[List[float]], List[List[Optional[int]]]]:
    """Floyd-Warshall – retorna matriz de distâncias e matriz de predecessores."""
    n = graph.get_vertex_count()
    dist = [[float('inf')] * n for _ in range(n)]
    pred = [[None] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
        for j in _successors(graph, i):
            dist[i][j] = graph.get_edge_weight(i, j)
            pred[i][j] = i

    for k in range(n):
        for i in range(n):
            for j in range(n):
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    pred[i][j] = pred[k][j] if pred[k][j] is not None else k
    return dist, pred


# ---------------------------------------------------------------------------
#  5. Fluxo máximo (Ford-Fulkerson / Edmonds-Karp) – retornam (fluxo, AdjacencyListGraph)
# ---------------------------------------------------------------------------

def _build_residual(graph: AbstractGraph) -> Dict[Tuple[int, int], float]:
    """Constrói rede residual (capacidades residuais)."""
    res = {}
    n = graph.get_vertex_count()
    for u in range(n):
        for v in _successors(graph, u):
            cap = graph.get_edge_weight(u, v)
            res[(u, v)] = cap
            if (v, u) not in res:
                res[(v, u)] = 0.0
    return res


def _dfs_flow(res: Dict[Tuple[int, int], float], source: int, sink: int,
              visited: Set[int], path: List[int]) -> bool:
    if source == sink:
        return True
    visited.add(source)
    for (u, v), cap in res.items():
        if u == source and cap > 0 and v not in visited:
            path.append(v)
            if _dfs_flow(res, v, sink, visited, path):
                return True
            path.pop()
    return False


def ford_fulkerson(graph: AbstractGraph, source: int, sink: int) -> Tuple[float, AdjacencyListGraph]:
    """
    Ford-Fulkerson (DFS para caminhos aumentantes).
    Retorna (fluxo_maximo, AdjacencyListGraph com arestas que possuem fluxo > 0).
    """
    res = _build_residual(graph)
    flow = 0.0
    while True:
        visited = set()
        path = [source]
        if not _dfs_flow(res, source, sink, visited, path):
            break
        path_edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        min_cap = min(res[(u, v)] for u, v in path_edges)
        for u, v in path_edges:
            res[(u, v)] -= min_cap
            res[(v, u)] = res.get((v, u), 0.0) + min_cap
        flow += min_cap

    # Constrói grafo resultado (apenas arestas com fluxo > 0)
    n = graph.get_vertex_count()
    result = AdjacencyListGraph(n)
    result.vertex_labels = dict(graph.vertex_labels)
    result.vertex_weights = list(graph.vertex_weights)

    for u in range(n):
        for v in _successors(graph, u):
            cap_orig = graph.get_edge_weight(u, v)
            fluxo_aresta = cap_orig - res.get((u, v), 0.0)
            if fluxo_aresta > 1e-9:
                result.add_edge(u, v)
                result.set_edge_weight(u, v, fluxo_aresta)
    return flow, result


def edmonds_karp(graph: AbstractGraph, source: int, sink: int) -> Tuple[float, AdjacencyListGraph]:
    """
    Edmonds-Karp (BFS para caminhos aumentantes).
    Retorna (fluxo_maximo, AdjacencyListGraph com arestas que possuem fluxo > 0).
    """
    res = _build_residual(graph)
    flow = 0.0
    n = graph.get_vertex_count()
    while True:
        parent = [-1] * n
        parent[source] = source
        queue = deque([source])
        while queue and parent[sink] == -1:
            u = queue.popleft()
            for (x, y), cap in res.items():
                if x == u and cap > 0 and parent[y] == -1:
                    parent[y] = u
                    queue.append(y)
        if parent[sink] == -1:
            break

        path = []
        v = sink
        while v != source:
            path.append((parent[v], v))
            v = parent[v]
        min_cap = min(res[(u, v)] for u, v in path)
        for u, v in path:
            res[(u, v)] -= min_cap
            res[(v, u)] = res.get((v, u), 0.0) + min_cap
        flow += min_cap

    # Constrói grafo resultado
    result = AdjacencyListGraph(n)
    result.vertex_labels = dict(graph.vertex_labels)
    result.vertex_weights = list(graph.vertex_weights)

    for u in range(n):
        for v in _successors(graph, u):
            cap_orig = graph.get_edge_weight(u, v)
            fluxo_aresta = cap_orig - res.get((u, v), 0.0)
            if fluxo_aresta > 1e-9:
                result.add_edge(u, v)
                result.set_edge_weight(u, v, fluxo_aresta)
    return flow, result


# ---------------------------------------------------------------------------
#  6. Ordenação topológica
# ---------------------------------------------------------------------------

def topological_sort(graph: AbstractGraph) -> Optional[List[int]]:
    """Retorna ordenação topológica se DAG, senão None."""
    n = graph.get_vertex_count()
    in_degree = [0] * n
    for u in range(n):
        for v in _successors(graph, u):
            in_degree[v] += 1

    queue = deque([i for i in range(n) if in_degree[i] == 0])
    result = []
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in _successors(graph, u):
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
    if len(result) != n:
        return None
    return result


# ---------------------------------------------------------------------------
#  7. Detecção de ciclos
# ---------------------------------------------------------------------------

def has_cycle_directed(graph: AbstractGraph) -> bool:
    """Verifica se o grafo direcionado possui ciclo."""
    n = graph.get_vertex_count()
    visited = [False] * n
    rec_stack = [False] * n

    def dfs_cycle(v):
        visited[v] = True
        rec_stack[v] = True
        for w in _successors(graph, v):
            if not visited[w]:
                if dfs_cycle(w):
                    return True
            elif rec_stack[w]:
                return True
        rec_stack[v] = False
        return False

    for v in range(n):
        if not visited[v]:
            if dfs_cycle(v):
                return True
    return False


def has_cycle_undirected(graph: AbstractGraph) -> bool:
    """Verifica se o grafo não direcionado possui ciclo (usando DFS)."""
    ug = _to_undirected(graph)
    n = ug.get_vertex_count()
    visited = [False] * n

    def dfs_cycle(u, p):
        visited[u] = True
        for v in ug.get_successors(u):
            if not visited[v]:
                if dfs_cycle(v, u):
                    return True
            elif v != p:
                return True
        return False

    for v in range(n):
        if not visited[v]:
            if dfs_cycle(v, -1):
                return True
    return False


# ---------------------------------------------------------------------------
#  8. Propriedades adicionais
# ---------------------------------------------------------------------------

def is_bipartite(graph: AbstractGraph) -> Tuple[bool, Optional[List[int]]]:
    """Verifica se o grafo (não direcionado) é bipartido. Retorna (bool, coloracao)."""
    ug = _to_undirected(graph)
    n = ug.get_vertex_count()
    color = [-1] * n
    for start in range(n):
        if color[start] == -1:
            color[start] = 0
            queue = deque([start])
            while queue:
                u = queue.popleft()
                for v in ug.get_successors(u):
                    if color[v] == -1:
                        color[v] = color[u] ^ 1
                        queue.append(v)
                    elif color[v] == color[u]:
                        return False, None
    return True, color


def is_connected(graph: AbstractGraph) -> bool:
    """Verifica se o grafo (não direcionado) é conexo."""
    if graph.get_vertex_count() == 0:
        return True
    ug = _to_undirected(graph) if not isinstance(graph, UndirectedGraph) else graph
    visited = set()
    queue = deque([0])
    visited.add(0)
    while queue:
        u = queue.popleft()
        for v in ug.get_successors(u):
            if v not in visited:
                visited.add(v)
                queue.append(v)
    return len(visited) == ug.get_vertex_count()
