from graph_engine.abstract_graph import AbstractGraph, GraphError

class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, num_vertices: int):
        super().__init__(num_vertices)
        self._matrix = [[False] * num_vertices for _ in range(num_vertices)]

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_edge(u, v)
        return self._matrix[u][v]

    def addEdge(self, u: int, v: int) -> None:
        self._validate_edge(u, v)
        if u == v:
            raise GraphError("Grafos simples não permitem laços")
        if not self._matrix[u][v]:
            self._matrix[u][v] = True
            self._edge_count += 1

    def removeEdge(self, u: int, v: int) -> None:
        self._validate_edge(u, v)
        if not self._matrix[u][v]:
            raise GraphError("Aresta inexistente")
        self._matrix[u][v] = False
        self._edge_count -= 1
        self._edge_weights.pop((u, v), None)

    def successors(self, u: int) -> list[int]:
        self._validate_vertex(u)
        return [v for v, exists in enumerate(self._matrix[u]) if exists]

    def predecessors(self, v: int) -> list[int]:
        self._validate_vertex(v)
        return [u for u in range(self._num_vertices) if self._matrix[u][v]]


class AdjacencyListGraph(AbstractGraph):
    def __init__(self, num_vertices: int):
        super().__init__(num_vertices)
        self._adjacency = [set() for _ in range(num_vertices)]

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_edge(u, v)
        return v in self._adjacency[u]

    def addEdge(self, u: int, v: int) -> None:
        self._validate_edge(u, v)
        if u == v:
            raise GraphError("Grafos simples não permitem laços")
        if v not in self._adjacency[u]:
            self._adjacency[u].add(v)
            self._edge_count += 1

    def removeEdge(self, u: int, v: int) -> None:
        self._validate_edge(u, v)
        if v not in self._adjacency[u]:
            raise GraphError("Aresta inexistente")
        self._adjacency[u].remove(v)
        self._edge_count -= 1
        self._edge_weights.pop((u, v), None)

    def successors(self, u: int) -> list[int]:
        self._validate_vertex(u)
        return sorted(self._adjacency[u])

    def predecessors(self, v: int) -> list[int]:
        self._validate_vertex(v)
        return [u for u, neighbors in enumerate(self._adjacency) if v in neighbors]