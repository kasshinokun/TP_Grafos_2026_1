from abc import ABC, abstractmethod
from pathlib import Path


class GraphError(ValueError):
    """Erro de domínio para operações inválidas em grafos."""


class AbstractGraph(ABC):
    def __init__(self, num_vertices: int):
        if num_vertices < 0:
            raise GraphError("O número de vértices não pode ser negativo")
        self._num_vertices = num_vertices
        self._edge_count = 0
        self._vertex_labels = [str(i) for i in range(num_vertices)]
        self._vertex_weights = [0.0] * num_vertices
        self._edge_weights: dict[tuple[int, int], float] = {}

    def _validate_vertex(self, vertex: int) -> None:
        if not isinstance(vertex, int) or not 0 <= vertex < self._num_vertices:
            raise IndexError(f"Vértice inválido: {vertex}")

    def _validate_edge(self, u: int, v: int) -> None:
        self._validate_vertex(u)
        self._validate_vertex(v)

    def getVertexCount(self) -> int:
        return self._num_vertices

    def getEdgeCount(self) -> int:
        return self._edge_count

    @abstractmethod
    def hasEdge(self, u: int, v: int) -> bool: ...

    @abstractmethod
    def addEdge(self, u: int, v: int) -> None: ...

    @abstractmethod
    def removeEdge(self, u: int, v: int) -> None: ...

    @abstractmethod
    def successors(self, u: int) -> list[int]: ...

    @abstractmethod
    def predecessors(self, v: int) -> list[int]: ...

    def isSucessor(self, u: int, v: int) -> bool:
        return self.hasEdge(u, v)

    def isPredessor(self, u: int, v: int) -> bool:
        return self.hasEdge(v, u)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._validate_edge(u1, v1)
        self._validate_edge(u2, v2)
        return self.hasEdge(u1, v1) and self.hasEdge(u2, v2) and u1 == u2 and v1 != v2

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._validate_edge(u1, v1)
        self._validate_edge(u2, v2)
        return self.hasEdge(u1, v1) and self.hasEdge(u2, v2) and v1 == v2 and u1 != u2

    def isIncident(self, u: int, v: int, x: int) -> bool:
        self._validate_edge(u, v)
        self._validate_vertex(x)
        return self.hasEdge(u, v) and x in (u, v)

    def getVertexInDegree(self, u: int) -> int:
        self._validate_vertex(u)
        return len(self.predecessors(u))

    def getVertexOutDegree(self, u: int) -> int:
        self._validate_vertex(u)
        return len(self.successors(u))

    def setVertexLabel(self, v: int, label: str) -> None:
        self._validate_vertex(v)
        self._vertex_labels[v] = label

    def getVertexLabel(self, v: int) -> str:
        self._validate_vertex(v)
        return self._vertex_labels[v]

    def setVertexWeight(self, v: int, w: float) -> None:
        self._validate_vertex(v)
        self._vertex_weights[v] = float(w)

    def getVertexWeight(self, v: int) -> float:
        self._validate_vertex(v)
        return self._vertex_weights[v]

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._validate_edge(u, v)
        if not self.hasEdge(u, v):
            raise GraphError("Não é possível ponderar uma aresta inexistente")
        self._edge_weights[(u, v)] = float(w)

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._validate_edge(u, v)
        if not self.hasEdge(u, v):
            raise GraphError("Aresta inexistente")
        return self._edge_weights.get((u, v), 1.0)

    def isConnected(self) -> bool:
        if self._num_vertices <= 1:
            return True
        visited = {0}
        stack = [0]
        while stack:
            u = stack.pop()
            neighbors = set(self.successors(u)) | set(self.predecessors(u))
            for v in neighbors - visited:
                visited.add(v)
                stack.append(v)
        return len(visited) == self._num_vertices

    def isEmptyGraph(self) -> bool:
        return self._edge_count == 0

    def isCompleteGraph(self) -> bool:
        return self._edge_count == self._num_vertices * (self._num_vertices - 1)

    def exportToGEPHI(self, path: str) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        lines = ["<?xml version=\"1.0\" encoding=\"UTF-8\"?>", '<gexf xmlns="http://www.gexf.net/1.3" version="1.3">', '<graph mode="static" defaultedgetype="directed">', "<nodes>"]
        lines.extend(f'<node id="{v}" label="{self._vertex_labels[v]}" weight="{self._vertex_weights[v]}" />' for v in range(self._num_vertices))
        lines.append("</nodes><edges>")
        edge_id = 0
        for u in range(self._num_vertices):
            for v in self.successors(u):
                lines.append(f'<edge id="{edge_id}" source="{u}" target="{v}" weight="{self.getEdgeWeight(u, v)}" />')
                edge_id += 1
        lines.extend(["</edges></graph></gexf>"])
        target.write_text("\n".join(lines), encoding="utf-8")
        
        # Adições para cumprir a API do Guião e integrar com analysis.py
    def getVertexInDegree(self, u: int) -> int:
        return len(self.predecessors(u))

    def getVertexOutDegree(self, u: int) -> int:
        return len(self.successors(u))

    def isSucessor(self, u: int, v: int) -> bool:
        return self.hasEdge(u, v)

    def isPredessor(self, u: int, v: int) -> bool:
        return self.hasEdge(v, u)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        return u1 == u2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        return v1 == v2 and self.hasEdge(u1, v1) and self.hasEdge(u2, v2)

    def isIncident(self, u: int, v: int, x: int) -> bool:
        return (u == x or v == x) and self.hasEdge(u, v)