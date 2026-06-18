"""
GraphAdapter
============
Wrapper que expõe o protocolo camelCase esperado pela `PureNetworkX`
(`addEdge`, `successors`, `predecessors`, `getVertexCount`, etc.) por
cima da hierarquia snake_case do projeto (`AbstractGraph`).

Esta é uma camada de adaptação puramente declarativa: cada chamada é
delegada ao grafo subjacente, mantendo a *single source of truth* na
classe `AbstractGraph` do TCC.
"""
from __future__ import annotations

from typing import List

from grafo.graph.abstract_graph import AbstractGraph


class GraphAdapter:
    """Adapta um `AbstractGraph` (snake_case) para o protocolo camelCase."""

    __slots__ = ("_g", "_succ_cache", "_pred_cache", "_dirty")

    def __init__(self, graph: AbstractGraph) -> None:
        self._g = graph
        self._succ_cache: dict[int, list[int]] = {}
        self._pred_cache: dict[int, list[int]] = {}
        self._dirty = True

    # ----------------------------- núcleo ---------------------------------
    @property
    def inner(self) -> AbstractGraph:
        return self._g

    def _invalidate(self) -> None:
        self._dirty = True
        self._succ_cache.clear()
        self._pred_cache.clear()

    def _validate_vertex(self, v: int) -> None:
        self._g.check_vertex(v)

    # ----------------------------- contagem -------------------------------
    def getVertexCount(self) -> int:                  # noqa: N802
        return self._g.get_vertex_count()

    def getEdgeCount(self) -> int:                    # noqa: N802
        return self._g.get_edge_count()

    # ----------------------------- arestas --------------------------------
    def hasEdge(self, u: int, v: int) -> bool:        # noqa: N802
        return self._g.has_edge(u, v)

    def addEdge(self, u: int, v: int) -> None:       # noqa: N802
        self._g.add_edge(u, v)
        self._invalidate()

    def removeEdge(self, u: int, v: int) -> None:    # noqa: N802
        self._g.remove_edge(u, v)
        self._invalidate()

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:  # noqa: N802
        self._g.set_edge_weight(u, v, w)

    def getEdgeWeight(self, u: int, v: int) -> float:  # noqa: N802
        return self._g.get_edge_weight(u, v)

    # ----------------------------- vértices -------------------------------
    def getVertexInDegree(self, v: int) -> int:       # noqa: N802
        return self._g.get_vertex_in_degree(v)

    def getVertexOutDegree(self, v: int) -> int:      # noqa: N802
        return self._g.get_vertex_out_degree(v)

    def setVertexWeight(self, v: int, w: float) -> None:  # noqa: N802
        self._g.set_vertex_weight(v, w)

    def getVertexWeight(self, v: int) -> float:       # noqa: N802
        return self._g.get_vertex_weight(v)

    def setVertexLabel(self, v: int, label: str) -> None:  # noqa: N802
        self._g.set_vertex_label(v, label)

    def getVertexLabel(self, v: int) -> str:          # noqa: N802
        return self._g.get_vertex_label(v)

    # --------------------- vizinhanças (cacheadas) ------------------------
    def successors(self, u: int) -> List[int]:
        self._validate_vertex(u)
        if u in self._succ_cache:
            return list(self._succ_cache[u])
        n = self._g.get_vertex_count()
        out = [v for v in range(n) if v != u and self._g.has_edge(u, v)]
        self._succ_cache[u] = out
        return list(out)

    def predecessors(self, v: int) -> List[int]:
        self._validate_vertex(v)
        if v in self._pred_cache:
            return list(self._pred_cache[v])
        n = self._g.get_vertex_count()
        out = [u for u in range(n) if u != v and self._g.has_edge(u, v)]
        self._pred_cache[v] = out
        return list(out)


def wrap(graph: AbstractGraph) -> GraphAdapter:
    """Atalho semântico: `wrap(g)` retorna um `GraphAdapter`."""
    return GraphAdapter(graph)
