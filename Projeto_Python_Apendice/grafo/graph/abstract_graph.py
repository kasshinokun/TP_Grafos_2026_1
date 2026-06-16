from abc import ABC, abstractmethod
from enum import Enum, auto
import collections

class RepType(Enum):
    MATRIX = auto()
    LIST = auto()

class AbstractGraph(ABC):
    def __init__(self, num_vertices: int, rep_type: RepType):
        if num_vertices <= 0:
            raise ValueError("num_vertices deve ser > 0.")
        self.num_vertices = num_vertices
        self.rep_type = rep_type
        self.vertex_weights = [1.0] * num_vertices
        self.vertex_labels = [f"v{i}" for i in range(num_vertices)]

    def check_vertex(self, v: int):
        if v < 0 or v >= self.num_vertices:
            raise IndexError(f"Vértice inválido: {v} (total={self.num_vertices})")

    def check_edge(self, u: int, v: int):
        self.check_vertex(u)
        self.check_vertex(v)
        if u == v:
            raise ValueError(f"Laço não permitido: {u}")

    def get_vertex_count(self) -> int:
        return self.num_vertices

    @abstractmethod
    def get_edge_count(self) -> int:
        pass

    @abstractmethod
    def has_edge(self, u: int, v: int) -> bool:
        pass

    @abstractmethod
    def add_edge(self, u: int, v: int):
        pass

    @abstractmethod
    def remove_edge(self, u: int, v: int):
        pass

    def is_successor(self, u: int, v: int) -> bool:
        return self.has_edge(u, v)

    def is_predecessor(self, u: int, v: int) -> bool:
        return self.has_edge(v, u)

    def is_divergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self.check_edge(u1, v1)
        self.check_edge(u2, v2)
        return u1 == u2 and self.has_edge(u1, v1) and self.has_edge(u2, v2)

    def is_convergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self.check_edge(u1, v1)
        self.check_edge(u2, v2)
        return v1 == v2 and self.has_edge(u1, v1) and self.has_edge(u2, v2)

    def is_incident(self, u: int, v: int, x: int) -> bool:
        self.check_edge(u, v)
        self.check_vertex(x)
        return (x == u or x == v) and self.has_edge(u, v)

    @abstractmethod
    def get_vertex_in_degree(self, u: int) -> int:
        pass

    @abstractmethod
    def get_vertex_out_degree(self, u: int) -> int:
        pass

    def set_vertex_weight(self, v: int, w: float):
        self.check_vertex(v)
        self.vertex_weights[v] = w

    def get_vertex_weight(self, v: int) -> float:
        self.check_vertex(v)
        return self.vertex_weights[v]

    def set_vertex_label(self, v: int, label: str):
        self.check_vertex(v)
        self.vertex_labels[v] = label

    def get_vertex_label(self, v: int) -> str:
        self.check_vertex(v)
        return self.vertex_labels[v]

    @abstractmethod
    def set_edge_weight(self, u: int, v: int, w: float):
        pass

    @abstractmethod
    def get_edge_weight(self, u: int, v: int) -> float:
        pass

    def is_connected(self) -> bool:
        if self.num_vertices == 0:
            return True
        visited = [False] * self.num_vertices
        queue = collections.deque([0])
        visited[0] = True
        count = 1
        while queue:
            cur = queue.popleft()
            for w in range(self.num_vertices):
                if not visited[w] and (self.has_edge(cur, w) or self.has_edge(w, cur)):
                    visited[w] = True
                    queue.append(w)
                    count += 1
        return count == self.num_vertices

    def is_empty_graph(self) -> bool:
        return self.get_edge_count() == 0

    def is_complete_graph(self) -> bool:
        for i in range(self.num_vertices):
            for j in range(self.num_vertices):
                if i != j and not self.has_edge(i, j):
                    return False
        return True

    @abstractmethod
    def export_to_gephi(self, path: str):
        pass

    def __str__(self):
        return f"{self.__class__.__name__}[V={self.num_vertices}, E={self.get_edge_count()}]"
