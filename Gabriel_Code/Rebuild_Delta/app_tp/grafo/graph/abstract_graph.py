# ./grafo/graph/abstract_graph.py


from abc import ABC, abstractmethod
from enum import Enum

class RepType(Enum):
    MATRIX = 1
    LIST = 2

class AbstractGraph(ABC):
    def __init__(self, num_vertices: int, rep_type: RepType):
        if num_vertices < 0: raise ValueError("Número de vértices não pode ser negativo.")
        self.num_vertices = num_vertices
        self.rep_type = rep_type
        self.vertex_weights = [1.0] * num_vertices
        self.vertex_labels = {i: str(i) for i in range(num_vertices)}

    def check_vertex(self, u: int):
        if not (0 <= u < self.num_vertices):
            raise IndexError(f"Vértice {u} fora dos limites [0, {self.num_vertices-1}].")

    def check_edge(self, u: int, v: int):
        self.check_vertex(u)
        self.check_vertex(v)
        if u == v:
            raise ValueError("Grafos simples não permitem laços (self-loops).")

    # --- API Obrigatória (PDF) ---
    @abstractmethod
    def get_vertex_count(self) -> int: pass
    @abstractmethod
    def get_edge_count(self) -> int: pass
    @abstractmethod
    def has_edge(self, u: int, v: int) -> bool: pass
    @abstractmethod
    def add_edge(self, u: int, v: int): pass
    @abstractmethod
    def remove_edge(self, u: int, v: int): pass
    
    def is_sucessor(self, u: int, v: int) -> bool: return self.has_edge(u, v)
    def is_predessor(self, u: int, v: int) -> bool: return self.has_edge(v, u)
    
    def is_divergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        return u1 == u2 and v1 != v2 and self.has_edge(u1, v1) and self.has_edge(u2, v2)
    
    def is_convergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        return v1 == v2 and u1 != u2 and self.has_edge(u1, v1) and self.has_edge(u2, v2)
    
    def is_incident(self, u: int, v: int, x: int) -> bool:
        return self.has_edge(u, v) and (u == x or v == x)

    @abstractmethod
    def get_vertex_in_degree(self, u: int) -> int: pass
    @abstractmethod
    def get_vertex_out_degree(self, u: int) -> int: pass
    
    def set_vertex_weight(self, v: int, w: float):
        self.check_vertex(v); self.vertex_weights[v] = w
        
    def get_vertex_weight(self, v: int) -> float:
        self.check_vertex(v); return self.vertex_weights[v]
        
    @abstractmethod
    def set_edge_weight(self, u: int, v: int, w: float): pass
    @abstractmethod
    def get_edge_weight(self, u: int, v: int) -> float: pass
    
    @abstractmethod
    def is_connected(self) -> bool: pass
    
    def is_empty_graph(self) -> bool: return self.num_vertices == 0
    def is_complete_graph(self) -> bool: return self.get_edge_count() == self.num_vertices * (self.num_vertices - 1)
    
    @abstractmethod
    def export_to_gephi(self, path: str): pass
