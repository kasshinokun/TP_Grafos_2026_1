"""
My_NetworkX — Pure Python NetworkX
==================================

Implementação nativa em Python puro dos principais algoritmos da teoria dos
grafos, mapeada nas 11 categorias do manual NetworkX e totalmente compatível
com a interface :class:`AbstractGraph`.

Categorias:
    0.  Gerenciamento de estado (Direcionado <-> Não Direcionado)
    1.  Caminhamentos / Traversals          (BFS, DFS, ordem topológica)
    2.  Conectividade                       (componentes, SCC, articulações,
                                             pontes, conectividade k-vértices)
    3.  Árvores e Árvores Geradoras         (is_tree, Kruskal, Prim)
    4.  Caminhos Mínimos                    (Dijkstra, Bellman-Ford,
                                             Floyd-Warshall, A*, reconstrução)
    5.  Fluxo em Redes                      (Edmonds-Karp, corte mínimo)
    6.  Isomorfismo e Planaridade           (backtracking + heurística)
    7.  Centralidade                        (degree, closeness, betweenness,
                                             PageRank, eigenvector, Katz)
    8.  Clustering & Estrutura              (coef. local/médio, densidade,
                                             transitividade, diâmetro/raio)
    9.  Comunidades                         (label propagation, Girvan-Newman,
                                             modularidade)
    10. Geradores                           (complete, path, cycle, star,
                                             Erdős–Rényi, Barabási–Albert,
                                             Watts–Strogatz)
    11. Álgebra Linear, I/O e Layouts       (adjacência, laplaciana, incidência,
                                             edgelist, layouts circular/spring)

Padrões: clean code, métodos estáticos puros, defaults imutáveis, e
desempenho mantido próximo ao da versão otimizada anterior.
"""
from __future__ import annotations

import heapq
import math
import random
from collections import defaultdict, deque
from contextlib import contextmanager
from typing import Callable, Dict, Iterable, List, Optional, Set, Tuple

# Tipo "AbstractGraph" aqui é apenas um *protocol* informal — qualquer objeto
# que exponha o protocolo camelCase (via GraphAdapter ou nativo) serve. Para
# manter as anotações, definimos um alias e um GraphError local.
from typing import Any as AbstractGraph  # noqa: N814  (alias proposital)


class GraphError(ValueError):
    """Erro de domínio para operações inválidas em grafos."""


class AdjacencyListGraph:
    """Implementação interna mínima usada pelos geradores de PureNetworkX.

    Expõe o protocolo camelCase consumido pelos algoritmos. Não substitui
    a classe homônima do pacote `grafo.graph` — é apenas um *backing store*
    leve para gerar grafos a partir de modelos teóricos (Erdős-Rényi etc.).
    """

    def __init__(self, num_vertices: int) -> None:
        self._n = int(num_vertices)
        self._adj: list[set[int]] = [set() for _ in range(self._n)]
        self._rev: list[set[int]] = [set() for _ in range(self._n)]
        self._w: dict[tuple[int, int], float] = {}
        self._edges = 0

    # ------------ contratos camelCase -----------------------------------
    def getVertexCount(self) -> int: return self._n                       # noqa: N802
    def getEdgeCount(self) -> int: return self._edges                     # noqa: N802

    def _vv(self, v: int) -> None:
        if not 0 <= v < self._n:
            raise IndexError(f"Vértice inválido: {v}")

    def _validate_vertex(self, v: int) -> None: self._vv(v)

    def hasEdge(self, u: int, v: int) -> bool:                           # noqa: N802
        self._vv(u); self._vv(v); return v in self._adj[u]

    def addEdge(self, u: int, v: int) -> None:                           # noqa: N802
        self._vv(u); self._vv(v)
        if u == v: raise ValueError("Laços não permitidos")
        if v not in self._adj[u]:
            self._adj[u].add(v); self._rev[v].add(u); self._edges += 1

    def removeEdge(self, u: int, v: int) -> None:                        # noqa: N802
        self._vv(u); self._vv(v)
        if v in self._adj[u]:
            self._adj[u].remove(v); self._rev[v].discard(u); self._edges -= 1
            self._w.pop((u, v), None)

    def successors(self, u: int) -> list[int]: self._vv(u); return sorted(self._adj[u])
    def predecessors(self, v: int) -> list[int]: self._vv(v); return sorted(self._rev[v])

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:           # noqa: N802
        if v not in self._adj[u]:
            self.addEdge(u, v)
        self._w[(u, v)] = float(w)

    def getEdgeWeight(self, u: int, v: int) -> float:                    # noqa: N802
        if v not in self._adj[u]:
            raise ValueError(f"Aresta inexistente: {u}->{v}")
        return self._w.get((u, v), 1.0)

    def getVertexInDegree(self, v: int) -> int: self._vv(v); return len(self._rev[v])  # noqa: N802
    def getVertexOutDegree(self, v: int) -> int: self._vv(v); return len(self._adj[v])  # noqa: N802


Number = float
Path = List[int]
DistMap = Dict[int, float]
PrevMap = Dict[int, Optional[int]]


# ---------------------------------------------------------------------------
# Estruturas auxiliares (módulo-privadas)
# ---------------------------------------------------------------------------
class _UnionFind:
    """Disjoint-Set Union com union-by-rank e path compression."""

    __slots__ = ("parent", "rank")

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        root = x
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[x] != root:
            self.parent[x], x = root, self.parent[x]
        return root

    def union(self, a: int, b: int) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def _neighbors_undirected(graph: AbstractGraph, u: int) -> Set[int]:
    """Vizinhança ignorando direção (sucessores ∪ predecessores)."""
    return set(graph.successors(u)) | set(graph.predecessors(u))


def _iter_edges_undirected(graph: AbstractGraph):
    """Itera arestas únicas (u < v) com seu peso (qualquer direção)."""
    seen: Set[Tuple[int, int]] = set()
    for u in range(graph.getVertexCount()):
        for v in graph.successors(u):
            key = (u, v) if u < v else (v, u)
            if key in seen:
                continue
            seen.add(key)
            yield key[0], key[1], graph.getEdgeWeight(u, v)


# ===========================================================================
# CLASSE PRINCIPAL
# ===========================================================================
class PureNetworkX:
    """Coleção estática de algoritmos da NetworkX em Python puro."""

    # =======================================================================
    # 0. GERENCIAMENTO DE ESTADO
    # =======================================================================
    @staticmethod
    def change_subjacente(graph: AbstractGraph) -> dict:
        """Transforma temporariamente um grafo direcionado em seu subjacente."""
        backup: dict = {"original_edges": {}}
        for u in range(graph.getVertexCount()):
            for v in graph.successors(u):
                backup["original_edges"][(u, v)] = graph.getEdgeWeight(u, v)

        to_add: List[Tuple[int, int, float]] = []
        for (u, v), w in backup["original_edges"].items():
            if not graph.hasEdge(v, u):
                to_add.append((v, u, w))
        for v, u, w in to_add:
            graph.addEdge(v, u)
            graph.setEdgeWeight(v, u, w)
        return backup

    @staticmethod
    def back_from_subjacente(graph: AbstractGraph, backup: dict) -> None:
        """Restaura o estado direcionado original exatamente."""
        for u in range(graph.getVertexCount()):
            for v in list(graph.successors(u)):
                graph.removeEdge(u, v)
        for (u, v), w in backup["original_edges"].items():
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, w)

    @staticmethod
    @contextmanager
    def undirected_context(graph: AbstractGraph):
        """Context manager seguro a exceções para uso não direcionado."""
        backup = PureNetworkX.change_subjacente(graph)
        try:
            yield graph
        finally:
            PureNetworkX.back_from_subjacente(graph, backup)

    # =======================================================================
    # 1. CAMINHAMENTOS (TRAVERSALS)
    # =======================================================================
    @staticmethod
    def bfs(graph: AbstractGraph, start: int) -> List[int]:
        """Busca em largura — ordem de descoberta."""
        graph._validate_vertex(start)
        visited, queue, order = {start}, deque([start]), []
        while queue:
            u = queue.popleft()
            order.append(u)
            for v in graph.successors(u):
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
        return order

    @staticmethod
    def dfs(graph: AbstractGraph, start: int) -> List[int]:
        """Busca em profundidade iterativa — ordem de descoberta."""
        graph._validate_vertex(start)
        visited: Set[int] = set()
        stack, order = [start], []
        while stack:
            u = stack.pop()
            if u in visited:
                continue
            visited.add(u)
            order.append(u)
            for v in sorted(graph.successors(u), reverse=True):
                if v not in visited:
                    stack.append(v)
        return order

    @staticmethod
    def topological_sort(graph: AbstractGraph) -> List[int]:
        """Ordenação topológica (Kahn). Falha se houver ciclo."""
        n = graph.getVertexCount()
        in_deg = [graph.getVertexInDegree(v) for v in range(n)]
        queue = deque(v for v in range(n) if in_deg[v] == 0)
        order: List[int] = []
        while queue:
            u = queue.popleft()
            order.append(u)
            for v in graph.successors(u):
                in_deg[v] -= 1
                if in_deg[v] == 0:
                    queue.append(v)
        if len(order) != n:
            raise GraphError("Grafo possui ciclo: ordenação topológica indefinida.")
        return order

    # =======================================================================
    # 2. CONECTIVIDADE
    # =======================================================================
    @staticmethod
    def is_weakly_connected(graph: AbstractGraph) -> bool:
        n = graph.getVertexCount()
        if n == 0:
            return True
        visited, queue = {0}, deque([0])
        while queue:
            u = queue.popleft()
            for v in _neighbors_undirected(graph, u):
                if v not in visited:
                    visited.add(v)
                    queue.append(v)
        return len(visited) == n

    @staticmethod
    def is_strongly_connected(graph: AbstractGraph) -> bool:
        if graph.getVertexCount() == 0:
            return True
        return len(PureNetworkX.tarjan_scc(graph)) == 1

    @staticmethod
    def connected_components(graph: AbstractGraph) -> List[List[int]]:
        visited: Set[int] = set()
        components: List[List[int]] = []
        for start in range(graph.getVertexCount()):
            if start in visited:
                continue
            comp: List[int] = []
            queue = deque([start])
            visited.add(start)
            while queue:
                u = queue.popleft()
                comp.append(u)
                for v in _neighbors_undirected(graph, u):
                    if v not in visited:
                        visited.add(v)
                        queue.append(v)
            components.append(comp)
        return components

    @staticmethod
    def tarjan_scc(graph: AbstractGraph) -> List[List[int]]:
        """Componentes fortemente conexas (Tarjan, iterativo)."""
        n = graph.getVertexCount()
        index_of: Dict[int, int] = {}
        lowlink: Dict[int, int] = {}
        on_stack: Dict[int, bool] = {}
        stack: List[int] = []
        sccs: List[List[int]] = []
        counter = 0

        for root in range(n):
            if root in index_of:
                continue
            call_stack: List[Tuple[int, Iterable[int]]] = [(root, iter(graph.successors(root)))]
            index_of[root] = lowlink[root] = counter
            counter += 1
            stack.append(root); on_stack[root] = True
            while call_stack:
                v, it = call_stack[-1]
                try:
                    w = next(it)
                    if w not in index_of:
                        index_of[w] = lowlink[w] = counter
                        counter += 1
                        stack.append(w); on_stack[w] = True
                        call_stack.append((w, iter(graph.successors(w))))
                    elif on_stack.get(w, False):
                        lowlink[v] = min(lowlink[v], index_of[w])
                except StopIteration:
                    call_stack.pop()
                    if lowlink[v] == index_of[v]:
                        scc = []
                        while True:
                            w = stack.pop()
                            on_stack[w] = False
                            scc.append(w)
                            if w == v:
                                break
                        sccs.append(scc)
                    if call_stack:
                        lowlink[call_stack[-1][0]] = min(lowlink[call_stack[-1][0]], lowlink[v])
        return sccs

    @staticmethod
    def articulation_points(graph: AbstractGraph) -> Set[int]:
        """Pontos de articulação (DFS de Hopcroft–Tarjan)."""
        n = graph.getVertexCount()
        disc = [-1] * n
        low = [0] * n
        parent = [-1] * n
        ap: Set[int] = set()
        timer = 0

        def dfs(u: int) -> None:
            nonlocal timer
            children = 0
            disc[u] = low[u] = timer; timer += 1
            for v in _neighbors_undirected(graph, u):
                if disc[v] == -1:
                    parent[v] = u; children += 1
                    dfs(v)
                    low[u] = min(low[u], low[v])
                    if parent[u] == -1 and children > 1:
                        ap.add(u)
                    if parent[u] != -1 and low[v] >= disc[u]:
                        ap.add(u)
                elif v != parent[u]:
                    low[u] = min(low[u], disc[v])

        for i in range(n):
            if disc[i] == -1:
                dfs(i)
        return ap

    @staticmethod
    def bridges(graph: AbstractGraph) -> List[Tuple[int, int]]:
        """Arestas-ponte (definição não-direcionada)."""
        n = graph.getVertexCount()
        disc = [-1] * n
        low = [0] * n
        parent = [-1] * n
        result: List[Tuple[int, int]] = []
        timer = 0

        def dfs(u: int) -> None:
            nonlocal timer
            disc[u] = low[u] = timer; timer += 1
            for v in _neighbors_undirected(graph, u):
                if disc[v] == -1:
                    parent[v] = u
                    dfs(v)
                    low[u] = min(low[u], low[v])
                    if low[v] > disc[u]:
                        result.append((min(u, v), max(u, v)))
                elif v != parent[u]:
                    low[u] = min(low[u], disc[v])

        for i in range(n):
            if disc[i] == -1:
                dfs(i)
        return result

    # =======================================================================
    # 3. ÁRVORES E ÁRVORES GERADORAS
    # =======================================================================
    @staticmethod
    def is_tree(graph: AbstractGraph) -> bool:
        n = graph.getVertexCount()
        # Conta arestas únicas como não-direcionadas
        e = sum(1 for _ in _iter_edges_undirected(graph))
        return e == n - 1 and PureNetworkX.is_weakly_connected(graph)

    @staticmethod
    def kruskal_mst(graph: AbstractGraph) -> List[Tuple[int, int, float]]:
        n = graph.getVertexCount()
        if n == 0:
            return []
        uf = _UnionFind(n)
        edges = sorted(_iter_edges_undirected(graph), key=lambda e: e[2])
        mst: List[Tuple[int, int, float]] = []
        for u, v, w in edges:
            if uf.union(u, v):
                mst.append((u, v, w))
                if len(mst) == n - 1:
                    break
        if len(mst) != n - 1:
            raise GraphError("O grafo não é conexo, MST inexistente.")
        return mst

    @staticmethod
    def prim_mst(graph: AbstractGraph, start: int = 0) -> List[Tuple[int, int, float]]:
        """Árvore geradora mínima (Prim, heap)."""
        n = graph.getVertexCount()
        if n == 0:
            return []
        graph._validate_vertex(start)
        in_tree = {start}
        heap: List[Tuple[float, int, int]] = []
        for v in _neighbors_undirected(graph, start):
            w = graph.getEdgeWeight(start, v) if graph.hasEdge(start, v) else graph.getEdgeWeight(v, start)
            heapq.heappush(heap, (w, start, v))
        mst: List[Tuple[int, int, float]] = []
        while heap and len(in_tree) < n:
            w, u, v = heapq.heappop(heap)
            if v in in_tree:
                continue
            in_tree.add(v); mst.append((u, v, w))
            for nxt in _neighbors_undirected(graph, v):
                if nxt not in in_tree:
                    wt = graph.getEdgeWeight(v, nxt) if graph.hasEdge(v, nxt) else graph.getEdgeWeight(nxt, v)
                    heapq.heappush(heap, (wt, v, nxt))
        if len(in_tree) != n:
            raise GraphError("O grafo não é conexo, MST inexistente.")
        return mst

    # =======================================================================
    # 4. CAMINHOS MÍNIMOS
    # =======================================================================
    @staticmethod
    def dijkstra(graph: AbstractGraph, start: int) -> Tuple[DistMap, PrevMap]:
        graph._validate_vertex(start)
        n = graph.getVertexCount()
        dist: DistMap = {v: math.inf for v in range(n)}
        prev: PrevMap = {v: None for v in range(n)}
        dist[start] = 0.0
        heap: List[Tuple[float, int]] = [(0.0, start)]
        visited: Set[int] = set()
        while heap:
            d, u = heapq.heappop(heap)
            if u in visited:
                continue
            visited.add(u)
            for v in graph.successors(u):
                w = graph.getEdgeWeight(u, v)
                if w < 0:
                    raise GraphError("Dijkstra não aceita pesos negativos.")
                alt = d + w
                if alt < dist[v]:
                    dist[v] = alt; prev[v] = u
                    heapq.heappush(heap, (alt, v))
        return dist, prev

    @staticmethod
    def shortest_path(graph: AbstractGraph, start: int, end: int) -> Path:
        dist, prev = PureNetworkX.dijkstra(graph, start)
        if dist[end] == math.inf:
            raise GraphError(f"Não há caminho de {start} para {end}")
        path: Path = []
        cur: Optional[int] = end
        while cur is not None:
            path.append(cur); cur = prev[cur]
        path.reverse()
        return path

    @staticmethod
    def bellman_ford(graph: AbstractGraph, start: int) -> Tuple[DistMap, PrevMap]:
        """Bellman-Ford — aceita pesos negativos; detecta ciclo negativo."""
        graph._validate_vertex(start)
        n = graph.getVertexCount()
        dist: DistMap = {v: math.inf for v in range(n)}
        prev: PrevMap = {v: None for v in range(n)}
        dist[start] = 0.0
        edges = [(u, v, graph.getEdgeWeight(u, v))
                 for u in range(n) for v in graph.successors(u)]
        for _ in range(n - 1):
            updated = False
            for u, v, w in edges:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w; prev[v] = u; updated = True
            if not updated:
                break
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                raise GraphError("Ciclo negativo detectado.")
        return dist, prev

    @staticmethod
    def floyd_warshall(graph: AbstractGraph) -> List[List[float]]:
        n = graph.getVertexCount()
        D = [[math.inf] * n for _ in range(n)]
        for i in range(n):
            D[i][i] = 0.0
        for u in range(n):
            for v in graph.successors(u):
                D[u][v] = graph.getEdgeWeight(u, v)
        for k in range(n):
            Dk = D[k]
            for i in range(n):
                Di = D[i]; dik = Di[k]
                if dik == math.inf:
                    continue
                for j in range(n):
                    nd = dik + Dk[j]
                    if nd < Di[j]:
                        Di[j] = nd
        return D

    @staticmethod
    def a_star(graph: AbstractGraph, start: int, goal: int,
               heuristic: Optional[Callable[[int, int], float]] = None) -> Path:
        """A* com heurística admissível opcional (default = 0 → Dijkstra)."""
        graph._validate_vertex(start); graph._validate_vertex(goal)
        h = heuristic or (lambda a, b: 0.0)
        g_score: DistMap = {start: 0.0}
        prev: PrevMap = {start: None}
        open_heap: List[Tuple[float, int]] = [(h(start, goal), start)]
        closed: Set[int] = set()
        while open_heap:
            _, u = heapq.heappop(open_heap)
            if u == goal:
                path: Path = []
                while u is not None:
                    path.append(u); u = prev[u]
                path.reverse()
                return path
            if u in closed:
                continue
            closed.add(u)
            for v in graph.successors(u):
                tentative = g_score[u] + graph.getEdgeWeight(u, v)
                if tentative < g_score.get(v, math.inf):
                    g_score[v] = tentative; prev[v] = u
                    heapq.heappush(open_heap, (tentative + h(v, goal), v))
        raise GraphError(f"A* não encontrou caminho {start}→{goal}")

    # =======================================================================
    # 5. FLUXO EM REDE
    # =======================================================================
    @staticmethod
    def edmonds_karp(graph: AbstractGraph, source: int, sink: int) -> float:
        graph._validate_vertex(source); graph._validate_vertex(sink)
        if source == sink:
            return 0.0
        n = graph.getVertexCount()
        residual: List[Dict[int, float]] = [defaultdict(float) for _ in range(n)]
        for u in range(n):
            for v in graph.successors(u):
                residual[u][v] += graph.getEdgeWeight(u, v)

        def bfs_path() -> Optional[Dict[int, Optional[int]]]:
            parent: Dict[int, Optional[int]] = {source: None}
            queue = deque([source])
            while queue:
                u = queue.popleft()
                if u == sink:
                    return parent
                for v, cap in residual[u].items():
                    if cap > 0 and v not in parent:
                        parent[v] = u
                        queue.append(v)
            return None

        flow = 0.0
        while True:
            parent = bfs_path()
            if parent is None or sink not in parent:
                return flow
            bottleneck = math.inf
            v = sink
            while v != source:
                u = parent[v]; bottleneck = min(bottleneck, residual[u][v]); v = u
            v = sink
            while v != source:
                u = parent[v]
                residual[u][v] -= bottleneck
                residual[v][u] += bottleneck
                v = u
            flow += bottleneck

    @staticmethod
    def min_cut(graph: AbstractGraph, source: int, sink: int) -> Tuple[float, Set[int], Set[int]]:
        """Corte mínimo s–t (max-flow / min-cut)."""
        n = graph.getVertexCount()
        residual: List[Dict[int, float]] = [defaultdict(float) for _ in range(n)]
        for u in range(n):
            for v in graph.successors(u):
                residual[u][v] += graph.getEdgeWeight(u, v)
        # Executa Edmonds–Karp sobre 'residual' local
        def bfs_path():
            parent = {source: None}; queue = deque([source])
            while queue:
                u = queue.popleft()
                if u == sink:
                    return parent
                for v, cap in residual[u].items():
                    if cap > 0 and v not in parent:
                        parent[v] = u; queue.append(v)
            return None
        flow = 0.0
        while True:
            parent = bfs_path()
            if parent is None or sink not in parent:
                break
            bn = math.inf; v = sink
            while v != source:
                u = parent[v]; bn = min(bn, residual[u][v]); v = u
            v = sink
            while v != source:
                u = parent[v]; residual[u][v] -= bn; residual[v][u] += bn; v = u
            flow += bn
        # Lado-S: alcançável de source no grafo residual
        reachable: Set[int] = {source}; queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, cap in residual[u].items():
                if cap > 0 and v not in reachable:
                    reachable.add(v); queue.append(v)
        other = set(range(n)) - reachable
        return flow, reachable, other

    # =======================================================================
    # 6. ISOMORFISMO E PLANARIDADE
    # =======================================================================
    @staticmethod
    def is_isomorphic(g1: AbstractGraph, g2: AbstractGraph) -> bool:
        if g1.getVertexCount() != g2.getVertexCount():
            return False
        if g1.getEdgeCount() != g2.getEdgeCount():
            return False
        n = g1.getVertexCount()
        if n == 0:
            return True

        def deg_seq(g):
            return sorted((len(g.successors(i)) + len(g.predecessors(i))) for i in range(g.getVertexCount()))

        if deg_seq(g1) != deg_seq(g2):
            return False

        deg_of = lambda g, v: len(g.successors(v)) + len(g.predecessors(v))
        order = sorted(range(n), key=lambda v: -deg_of(g1, v))
        by_deg: Dict[int, List[int]] = defaultdict(list)
        for v in range(n):
            by_deg[deg_of(g2, v)].append(v)
        mapping: Dict[int, int] = {}
        used: Set[int] = set()

        def consistent(u1: int, u2: int) -> bool:
            for v1, v2 in mapping.items():
                if g1.hasEdge(u1, v1) != g2.hasEdge(u2, v2):
                    return False
                if g1.hasEdge(v1, u1) != g2.hasEdge(v2, u2):
                    return False
            return True

        def backtrack(i: int) -> bool:
            if i == n:
                return True
            u1 = order[i]; deg = deg_of(g1, u1)
            for u2 in by_deg[deg]:
                if u2 in used or not consistent(u1, u2):
                    continue
                mapping[u1] = u2; used.add(u2)
                if backtrack(i + 1):
                    return True
                del mapping[u1]; used.discard(u2)
            return False

        return backtrack(0)

    @staticmethod
    def is_planar(graph: AbstractGraph) -> bool:
        """Heurística estrutural (Euler + casos K5/K3,3)."""
        n = graph.getVertexCount()
        if n <= 4:
            return True
        e = sum(1 for _ in _iter_edges_undirected(graph))
        if e > 3 * n - 6:
            return False
        if n == 5 and e == 10:
            return False
        if n == 6 and e == 9:
            degs = [len(_neighbors_undirected(graph, i)) for i in range(n)]
            if all(d == 3 for d in degs):
                has_triangle = any(
                    bool(_neighbors_undirected(graph, i) & _neighbors_undirected(graph, j))
                    for i in range(n) for j in _neighbors_undirected(graph, i) if j > i
                )
                if not has_triangle:
                    return False
        return True

    # =======================================================================
    # 7. CENTRALIDADE
    # =======================================================================
    @staticmethod
    def degree_centrality(graph: AbstractGraph) -> Dict[int, float]:
        n = graph.getVertexCount()
        if n <= 1:
            return {v: 0.0 for v in range(n)}
        scale = 1.0 / (n - 1)
        return {v: len(_neighbors_undirected(graph, v)) * scale for v in range(n)}

    @staticmethod
    def closeness_centrality(graph: AbstractGraph) -> Dict[int, float]:
        n = graph.getVertexCount()
        out: Dict[int, float] = {}
        for s in range(n):
            dist = {s: 0}; queue = deque([s])
            while queue:
                u = queue.popleft()
                for v in graph.successors(u):
                    if v not in dist:
                        dist[v] = dist[u] + 1; queue.append(v)
            reachable = [d for d in dist.values() if d > 0]
            out[s] = (len(reachable) / sum(reachable)) if reachable else 0.0
        return out

    @staticmethod
    def betweenness_centrality(graph: AbstractGraph) -> Dict[int, float]:
        """Algoritmo de Brandes O(VE)."""
        n = graph.getVertexCount()
        bc = {v: 0.0 for v in range(n)}
        for s in range(n):
            S: List[int] = []
            P: Dict[int, List[int]] = {w: [] for w in range(n)}
            sigma = {w: 0 for w in range(n)}; sigma[s] = 1
            dist = {w: -1 for w in range(n)}; dist[s] = 0
            queue = deque([s])
            while queue:
                v = queue.popleft(); S.append(v)
                for w in graph.successors(v):
                    if dist[w] < 0:
                        dist[w] = dist[v] + 1; queue.append(w)
                    if dist[w] == dist[v] + 1:
                        sigma[w] += sigma[v]; P[w].append(v)
            delta = {w: 0.0 for w in range(n)}
            while S:
                w = S.pop()
                for v in P[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != s:
                    bc[w] += delta[w]
        if n > 2:
            scale = 1.0 / ((n - 1) * (n - 2))
            for v in bc:
                bc[v] *= scale
        return bc

    @staticmethod
    def pagerank(graph: AbstractGraph, alpha: float = 0.85,
                 max_iter: int = 100, tol: float = 1e-6) -> Dict[int, float]:
        n = graph.getVertexCount()
        if n == 0:
            return {}
        pr = {v: 1.0 / n for v in range(n)}
        out_deg = [len(graph.successors(v)) for v in range(n)]
        teleport = (1 - alpha) / n
        for _ in range(max_iter):
            dangling = sum(pr[v] for v in range(n) if out_deg[v] == 0) / n
            new = {v: teleport + alpha * dangling for v in range(n)}
            for u in range(n):
                if out_deg[u] == 0:
                    continue
                share = alpha * pr[u] / out_deg[u]
                for v in graph.successors(u):
                    new[v] += share
            if sum(abs(new[v] - pr[v]) for v in range(n)) < tol:
                pr = new; break
            pr = new
        return pr

    @staticmethod
    def eigenvector_centrality(graph: AbstractGraph,
                               max_iter: int = 100, tol: float = 1e-6) -> Dict[int, float]:
        """Centralidade do autovetor por iteração de potência."""
        n = graph.getVertexCount()
        if n == 0:
            return {}
        x = {v: 1.0 / n for v in range(n)}
        for _ in range(max_iter):
            x_new = {v: 0.0 for v in range(n)}
            for u in range(n):
                for v in _neighbors_undirected(graph, u):
                    x_new[u] += x[v]
            norm = math.sqrt(sum(val * val for val in x_new.values())) or 1.0
            x_new = {v: x_new[v] / norm for v in range(n)}
            if sum(abs(x_new[v] - x[v]) for v in range(n)) < tol:
                return x_new
            x = x_new
        return x

    @staticmethod
    def katz_centrality(graph: AbstractGraph, alpha: float = 0.1, beta: float = 1.0,
                        max_iter: int = 100, tol: float = 1e-6) -> Dict[int, float]:
        n = graph.getVertexCount()
        if n == 0:
            return {}
        x = {v: 0.0 for v in range(n)}
        for _ in range(max_iter):
            x_new = {v: beta for v in range(n)}
            for u in range(n):
                for v in graph.successors(u):
                    x_new[v] += alpha * x[u]
            if sum(abs(x_new[v] - x[v]) for v in range(n)) < tol:
                return x_new
            x = x_new
        return x

    # =======================================================================
    # 8. CLUSTERING & ESTRUTURA
    # =======================================================================
    @staticmethod
    def clustering(graph: AbstractGraph) -> Dict[int, float]:
        coef: Dict[int, float] = {}
        for v in range(graph.getVertexCount()):
            nbrs = _neighbors_undirected(graph, v); nbrs.discard(v)
            k = len(nbrs)
            if k < 2:
                coef[v] = 0.0; continue
            nbrs_list = list(nbrs); triangles = 0
            for i in range(k):
                ni = nbrs_list[i]
                for j in range(i + 1, k):
                    nj = nbrs_list[j]
                    if graph.hasEdge(ni, nj) or graph.hasEdge(nj, ni):
                        triangles += 1
            coef[v] = (2 * triangles) / (k * (k - 1))
        return coef

    @staticmethod
    def average_clustering(graph: AbstractGraph) -> float:
        c = PureNetworkX.clustering(graph)
        return sum(c.values()) / len(c) if c else 0.0

    @staticmethod
    def density(graph: AbstractGraph) -> float:
        n = graph.getVertexCount()
        if n <= 1:
            return 0.0
        e = sum(1 for _ in _iter_edges_undirected(graph))
        return (2 * e) / (n * (n - 1))

    @staticmethod
    def transitivity(graph: AbstractGraph) -> float:
        """3 × triângulos / triplas conexas."""
        n = graph.getVertexCount(); triangles = 0; triples = 0
        for v in range(n):
            nbrs = _neighbors_undirected(graph, v); nbrs.discard(v)
            k = len(nbrs); triples += k * (k - 1) // 2
            nbrs_list = list(nbrs)
            for i in range(k):
                for j in range(i + 1, k):
                    if graph.hasEdge(nbrs_list[i], nbrs_list[j]) or graph.hasEdge(nbrs_list[j], nbrs_list[i]):
                        triangles += 1
        # Triangles foram contados 3× (uma vez por vértice)
        return (3 * (triangles / 3)) / triples if triples else 0.0

    @staticmethod
    def eccentricity(graph: AbstractGraph) -> Dict[int, float]:
        n = graph.getVertexCount(); out: Dict[int, float] = {}
        for s in range(n):
            dist = {s: 0}; queue = deque([s])
            while queue:
                u = queue.popleft()
                for v in _neighbors_undirected(graph, u):
                    if v not in dist:
                        dist[v] = dist[u] + 1; queue.append(v)
            if len(dist) != n:
                out[s] = math.inf
            else:
                out[s] = max(dist.values())
        return out

    @staticmethod
    def diameter(graph: AbstractGraph) -> float:
        ecc = PureNetworkX.eccentricity(graph)
        return max(ecc.values()) if ecc else 0.0

    @staticmethod
    def radius(graph: AbstractGraph) -> float:
        ecc = PureNetworkX.eccentricity(graph)
        return min(ecc.values()) if ecc else 0.0

    # =======================================================================
    # 9. COMUNIDADES
    # =======================================================================
    @staticmethod
    def label_propagation_communities(graph: AbstractGraph,
                                      max_iter: int = 50,
                                      seed: Optional[int] = None) -> List[Set[int]]:
        rng = random.Random(seed)
        nodes = list(range(graph.getVertexCount()))
        if not nodes:
            return []
        labels = {v: v for v in nodes}
        for _ in range(max_iter):
            rng.shuffle(nodes); changed = False
            for v in nodes:
                nbrs = _neighbors_undirected(graph, v)
                if not nbrs:
                    continue
                counts: Dict[int, int] = defaultdict(int)
                for n in nbrs:
                    counts[labels[n]] += 1
                top = max(counts.values())
                best = [lbl for lbl, c in counts.items() if c == top]
                pick = rng.choice(best)
                if labels[v] != pick:
                    labels[v] = pick; changed = True
            if not changed:
                break
        groups: Dict[int, Set[int]] = defaultdict(set)
        for v, lbl in labels.items():
            groups[lbl].add(v)
        return list(groups.values())

    @staticmethod
    def modularity(graph: AbstractGraph, communities: List[Set[int]]) -> float:
        """Q de Newman para comunidades (vista não direcionada, pesos = 1)."""
        m2 = sum(1 for _ in _iter_edges_undirected(graph)) * 2  # 2m
        if m2 == 0:
            return 0.0
        deg = {v: len(_neighbors_undirected(graph, v)) for v in range(graph.getVertexCount())}
        q = 0.0
        for comm in communities:
            for i in comm:
                for j in comm:
                    a_ij = 1.0 if (graph.hasEdge(i, j) or graph.hasEdge(j, i)) else 0.0
                    q += a_ij - (deg[i] * deg[j]) / m2
        return q / m2

    @staticmethod
    def girvan_newman(graph: AbstractGraph, k: int = 2) -> List[Set[int]]:
        """Encontra k comunidades removendo iterativamente arestas de maior
        edge-betweenness (versão simplificada). Trabalha em cópia subjacente."""
        if k < 1:
            raise GraphError("k deve ser ≥ 1")
        # Trabalhar em uma cópia não direcionada
        n = graph.getVertexCount()
        work = AdjacencyListGraph(n)
        for u, v, w in _iter_edges_undirected(graph):
            work.addEdge(u, v); work.setEdgeWeight(u, v, w)
            work.addEdge(v, u); work.setEdgeWeight(v, u, w)

        def components(g):
            return [set(c) for c in PureNetworkX.connected_components(g)]

        comps = components(work)
        while len(comps) < k and work.getEdgeCount() > 0:
            # edge-betweenness via Brandes adaptado (contagem em arestas)
            eb: Dict[Tuple[int, int], float] = defaultdict(float)
            for s in range(n):
                S, P, sigma, dist = [], {w: [] for w in range(n)}, {w: 0 for w in range(n)}, {w: -1 for w in range(n)}
                sigma[s] = 1; dist[s] = 0; queue = deque([s])
                while queue:
                    v = queue.popleft(); S.append(v)
                    for w in work.successors(v):
                        if dist[w] < 0:
                            dist[w] = dist[v] + 1; queue.append(w)
                        if dist[w] == dist[v] + 1:
                            sigma[w] += sigma[v]; P[w].append(v)
                delta = {w: 0.0 for w in range(n)}
                while S:
                    w = S.pop()
                    for v in P[w]:
                        c = (sigma[v] / sigma[w]) * (1 + delta[w])
                        key = (min(v, w), max(v, w))
                        eb[key] += c
                        delta[v] += c
            if not eb:
                break
            top_edge = max(eb, key=eb.get)
            u, v = top_edge
            if work.hasEdge(u, v): work.removeEdge(u, v)
            if work.hasEdge(v, u): work.removeEdge(v, u)
            comps = components(work)
        return comps

    # =======================================================================
    # 10. GERADORES
    # =======================================================================
    @staticmethod
    def empty_graph(n: int) -> AdjacencyListGraph:
        return AdjacencyListGraph(n)

    @staticmethod
    def complete_graph(n: int) -> AdjacencyListGraph:
        g = AdjacencyListGraph(n)
        for i in range(n):
            for j in range(n):
                if i != j:
                    g.addEdge(i, j)
        return g

    @staticmethod
    def path_graph(n: int) -> AdjacencyListGraph:
        g = AdjacencyListGraph(n)
        for i in range(n - 1):
            g.addEdge(i, i + 1); g.addEdge(i + 1, i)
        return g

    @staticmethod
    def cycle_graph(n: int) -> AdjacencyListGraph:
        g = PureNetworkX.path_graph(n)
        if n > 2:
            g.addEdge(n - 1, 0); g.addEdge(0, n - 1)
        return g

    @staticmethod
    def star_graph(n: int) -> AdjacencyListGraph:
        """Estrela com n folhas (n+1 vértices, centro = 0)."""
        g = AdjacencyListGraph(n + 1)
        for i in range(1, n + 1):
            g.addEdge(0, i); g.addEdge(i, 0)
        return g

    @staticmethod
    def erdos_renyi_graph(n: int, p: float, seed: Optional[int] = None) -> AdjacencyListGraph:
        rng = random.Random(seed)
        g = AdjacencyListGraph(n)
        for i in range(n):
            for j in range(i + 1, n):
                if rng.random() < p:
                    g.addEdge(i, j); g.addEdge(j, i)
        return g

    @staticmethod
    def barabasi_albert_graph(n: int, m: int, seed: Optional[int] = None) -> AdjacencyListGraph:
        if m < 1 or m >= n:
            raise GraphError("Necessário 1 ≤ m < n")
        rng = random.Random(seed)
        g = AdjacencyListGraph(n)
        # Núcleo inicial: m+1 vértices conectados como caminho
        for i in range(m):
            g.addEdge(i, i + 1); g.addEdge(i + 1, i)
        repeated = [v for v in range(m + 1) for _ in range(len(_neighbors_undirected(g, v)))]
        for new in range(m + 1, n):
            targets: Set[int] = set()
            while len(targets) < m:
                targets.add(rng.choice(repeated))
            for t in targets:
                g.addEdge(new, t); g.addEdge(t, new)
                repeated.append(t); repeated.append(new)
        return g

    @staticmethod
    def watts_strogatz_graph(n: int, k: int, p: float,
                             seed: Optional[int] = None) -> AdjacencyListGraph:
        if k % 2 or k >= n:
            raise GraphError("k deve ser par e < n")
        rng = random.Random(seed)
        g = AdjacencyListGraph(n)
        for i in range(n):
            for j in range(1, k // 2 + 1):
                a, b = i, (i + j) % n
                g.addEdge(a, b); g.addEdge(b, a)
        # Reconexão
        for i in range(n):
            for j in range(1, k // 2 + 1):
                if rng.random() < p:
                    new = rng.randrange(n)
                    while new == i or g.hasEdge(i, new):
                        new = rng.randrange(n)
                    old = (i + j) % n
                    if g.hasEdge(i, old): g.removeEdge(i, old)
                    if g.hasEdge(old, i): g.removeEdge(old, i)
                    g.addEdge(i, new); g.addEdge(new, i)
        return g

    # =======================================================================
    # 11. ÁLGEBRA LINEAR, I/O E LAYOUTS
    # =======================================================================
    @staticmethod
    def adjacency_matrix(graph: AbstractGraph) -> List[List[float]]:
        n = graph.getVertexCount()
        M = [[0.0] * n for _ in range(n)]
        for u in range(n):
            for v in graph.successors(u):
                M[u][v] = graph.getEdgeWeight(u, v)
        return M

    @staticmethod
    def laplacian_matrix(graph: AbstractGraph) -> List[List[float]]:
        n = graph.getVertexCount()
        L = [[0.0] * n for _ in range(n)]
        for u in range(n):
            d = 0.0
            for v in graph.successors(u):
                w = graph.getEdgeWeight(u, v)
                L[u][v] = -w; d += w
            L[u][u] = d
        return L

    @staticmethod
    def incidence_matrix(graph: AbstractGraph) -> List[List[float]]:
        edges = list(_iter_edges_undirected(graph))
        n = graph.getVertexCount(); m = len(edges)
        I = [[0.0] * m for _ in range(n)]
        for idx, (u, v, _) in enumerate(edges):
            I[u][idx] = 1.0; I[v][idx] = 1.0
        return I

    @staticmethod
    def write_edgelist(graph: AbstractGraph, path: str, delimiter: str = " ") -> None:
        with open(path, "w", encoding="utf-8") as f:
            for u, v, w in _iter_edges_undirected(graph):
                f.write(f"{u}{delimiter}{v}{delimiter}{w}\n")

    @staticmethod
    def read_edgelist(path: str, delimiter: str = " ", directed: bool = False) -> AdjacencyListGraph:
        edges: List[Tuple[int, int, float]] = []; mx = -1
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(delimiter)
                if len(parts) < 2:
                    continue
                u, v = int(parts[0]), int(parts[1])
                w = float(parts[2]) if len(parts) >= 3 else 1.0
                edges.append((u, v, w)); mx = max(mx, u, v)
        g = AdjacencyListGraph(mx + 1 if mx >= 0 else 0)
        for u, v, w in edges:
            g.addEdge(u, v); g.setEdgeWeight(u, v, w)
            if not directed:
                g.addEdge(v, u); g.setEdgeWeight(v, u, w)
        return g

    @staticmethod
    def circular_layout(graph: AbstractGraph) -> Dict[int, Tuple[float, float]]:
        n = graph.getVertexCount()
        if n == 0:
            return {}
        return {i: (math.cos(2 * math.pi * i / n), math.sin(2 * math.pi * i / n)) for i in range(n)}

    @staticmethod
    def spring_layout(graph: AbstractGraph, iterations: int = 50,
                      k: Optional[float] = None,
                      seed: Optional[int] = None) -> Dict[int, Tuple[float, float]]:
        rng = random.Random(seed)
        n = graph.getVertexCount()
        if n == 0:
            return {}
        if k is None:
            k = 1.0 / math.sqrt(n)
        pos = {i: [rng.uniform(-1, 1), rng.uniform(-1, 1)] for i in range(n)}
        for it in range(iterations):
            disp = {i: [0.0, 0.0] for i in range(n)}
            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue
                    dx = pos[i][0] - pos[j][0]; dy = pos[i][1] - pos[j][1]
                    d = math.hypot(dx, dy) + 1e-9
                    f = (k * k) / d
                    disp[i][0] += (dx / d) * f; disp[i][1] += (dy / d) * f
            for u in range(n):
                for v in graph.successors(u):
                    dx = pos[u][0] - pos[v][0]; dy = pos[u][1] - pos[v][1]
                    d = math.hypot(dx, dy) + 1e-9
                    f = (d * d) / k
                    disp[u][0] -= (dx / d) * f; disp[u][1] -= (dy / d) * f
                    disp[v][0] += (dx / d) * f; disp[v][1] += (dy / d) * f
            t = 0.1 * (1 - it / iterations)
            for i in range(n):
                dx, dy = disp[i]; d = math.hypot(dx, dy) + 1e-9
                step = min(d, t)
                pos[i][0] += (dx / d) * step; pos[i][1] += (dy / d) * step
        return {i: (pos[i][0], pos[i][1]) for i in range(n)}
