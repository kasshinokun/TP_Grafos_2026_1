# ./grafo/graph/adjacency_matrix_graph.py

"""Implementação de grafo por Matriz de Adjacência com in_degree O(1)."""
from .abstract_graph import AbstractGraph, RepType
from typing import Set


class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, num_vertices: int):
        super().__init__(num_vertices, RepType.MATRIX)
        self.adj = [[0.0] * num_vertices for _ in range(num_vertices)]
        # BUG FIX: mantém in_degree_count para O(1) (como na lista de adjacência)
        self.in_degree_count = [0] * num_vertices
        self.edge_count = 0

    def get_vertex_count(self) -> int:
        return self.num_vertices

    def get_edge_count(self) -> int:
        return self.edge_count

    def has_edge(self, u: int, v: int) -> bool:
        self.check_vertex(u)
        self.check_vertex(v)
        return self.adj[u][v] != 0.0

    def add_edge(self, u: int, v: int):  # Idempotente
        self.check_edge(u, v)
        if self.adj[u][v] == 0.0:
            self.adj[u][v] = 1.0
            self.in_degree_count[v] += 1
            self.edge_count += 1

    def remove_edge(self, u: int, v: int):
        self.check_edge(u, v)
        if self.adj[u][v] != 0.0:
            self.adj[u][v] = 0.0
            self.in_degree_count[v] -= 1
            self.edge_count -= 1

    def get_vertex_in_degree(self, u: int) -> int:
        self.check_vertex(u)
        return self.in_degree_count[u]  # O(1) - OTIMIZADO

    def get_vertex_out_degree(self, u: int) -> int:
        self.check_vertex(u)
        return sum(1 for j in range(self.num_vertices) if self.adj[u][j] != 0.0)

    def set_edge_weight(self, u: int, v: int, w: float):
        self.check_edge(u, v)
        if w == 0:
            raise ValueError("Peso 0 reservado para 'sem aresta'.")
        is_new = self.adj[u][v] == 0.0
        self.adj[u][v] = w
        if is_new:
            self.in_degree_count[v] += 1
            self.edge_count += 1

    def get_edge_weight(self, u: int, v: int) -> float:
        self.check_edge(u, v)
        if self.adj[u][v] == 0.0:
            raise ValueError(f"Aresta ({u},{v}) não existe.")
        return self.adj[u][v]

    # Duck-typing para o Adapter
    def get_successors(self, u: int) -> Set[int]:
        self.check_vertex(u)
        return {v for v in range(self.num_vertices) if self.adj[u][v] != 0.0}

    def get_predecessors(self, u: int) -> Set[int]:
        self.check_vertex(u)
        return {v for v in range(self.num_vertices) if self.adj[v][u] != 0.0}

    def is_connected(self) -> bool:
        """Conectividade fraca via BFS."""
        if self.num_vertices == 0:
            return True
        visited = {0}
        queue = [0]
        while queue:
            curr = queue.pop(0)
            for nb in self.get_successors(curr) | self.get_predecessors(curr):
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return len(visited) == self.num_vertices

    def get_matrix(self):
        return self.adj

    def export_to_gephi(self, path: str):
        file_path = path if path.endswith(".gexf") else path + ".gexf"
        def escape_xml(text):
            text = str(text)
            return (text.replace("&", "&amp;").replace("<", "&lt;")
                        .replace(">", "&gt;").replace('"', "&quot;"))
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<gexf xmlns="http://gexf.net/1.3" version="1.3">\n')
            f.write('  <graph defaultedgetype="directed">\n')
            f.write('    <nodes>\n')
            for i in range(self.num_vertices):
                f.write(f'      <node id="{i}" label="{escape_xml(self.vertex_labels[i])}"/>\n')
            f.write('    </nodes>\n')
            f.write('    <edges>\n')
            eid = 0
            for u in range(self.num_vertices):
                for v in range(self.num_vertices):
                    if self.adj[u][v] != 0.0:
                        f.write(f'      <edge id="{eid}" source="{u}" target="{v}" weight="{self.adj[u][v]:.4f}"/>\n')
                        eid += 1
            f.write('    </edges>\n')
            f.write('  </graph>\n')
            f.write('</gexf>\n')

    def to_matrix_string(self) -> str:
        lines = ["Matriz de Adjacência:"]
        for row in self.adj:
            lines.append("  " + " ".join(f"{val:4.1f}" for val in row))
        return "\n".join(lines)
