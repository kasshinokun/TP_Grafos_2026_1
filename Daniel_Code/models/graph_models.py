class AbstractGraph:
    def __init__(self, num_vertices: int):
        self.num_vertices = num_vertices
        self.vertex_weights = [0.0] * num_vertices
        self.edge_weights = {}  # (u, v) -> weight

    def add_edge(self, u: int, v: int):
        raise NotImplementedError

    def remove_edge(self, u: int, v: int):
        raise NotImplementedError

    def has_edge(self, u: int, v: int) -> bool:
        raise NotImplementedError

    def get_vertex_count(self) -> int:
        return self.num_vertices

    def set_vertex_weight(self, v: int, w: float):
        if 0 <= v < self.num_vertices:
            self.vertex_weights[v] = w

    def get_vertex_weight(self, v: int) -> float:
        if 0 <= v < self.num_vertices:
            return self.vertex_weights[v]
        return 0.0

    def set_edge_weight(self, u: int, v: int, w: float):
        if self.has_edge(u, v):
            self.edge_weights[(u, v)] = w

    def get_edge_weight(self, u: int, v: int) -> float:
        return self.edge_weights.get((u, v), 0.0)

class AdjacencyListGraph(AbstractGraph):
    def __init__(self, num_vertices: int):
        super().__init__(num_vertices)
        self.adj = [set() for _ in range(num_vertices)]

    def add_edge(self, u: int, v: int):
        if 0 <= u < self.num_vertices and 0 <= v < self.num_vertices:
            self.adj[u].add(v)

    def remove_edge(self, u: int, v: int):
        if 0 <= u < self.num_vertices and v in self.adj[u]:
            self.adj[u].remove(v)

    def has_edge(self, u: int, v: int) -> bool:
        return 0 <= u < self.num_vertices and v in self.adj[u]

    def get_edge_count(self) -> int:
        return sum(len(neighbors) for neighbors in self.adj)