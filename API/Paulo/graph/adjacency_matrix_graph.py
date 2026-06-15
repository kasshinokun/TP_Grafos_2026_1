from .abstract_graph import AbstractGraph, RepType

class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, num_vertices: int):
        super().__init__(num_vertices, RepType.MATRIX)
        self.adj = [[0.0 for _ in range(num_vertices)] for _ in range(num_vertices)]
        self.edge_count = 0

    def get_edge_count(self) -> int:
        return self.edge_count

    def has_edge(self, u: int, v: int) -> bool:
        self.check_vertex(u)
        self.check_vertex(v)
        return self.adj[u][v] != 0.0

    def add_edge(self, u: int, v: int):
        self.check_edge(u, v)
        if self.adj[u][v] == 0.0:
            self.adj[u][v] = 1.0
            self.edge_count += 1

    def remove_edge(self, u: int, v: int):
        self.check_edge(u, v)
        if self.adj[u][v] != 0.0:
            self.adj[u][v] = 0.0
            self.edge_count -= 1

    def get_vertex_in_degree(self, u: int) -> int:
        self.check_vertex(u)
        deg = 0
        for i in range(self.num_vertices):
            if self.adj[i][u] != 0.0:
                deg += 1
        return deg

    def get_vertex_out_degree(self, u: int) -> int:
        self.check_vertex(u)
        deg = 0
        for j in range(self.num_vertices):
            if self.adj[u][j] != 0.0:
                deg += 1
        return deg

    def set_edge_weight(self, u: int, v: int, w: float):
        self.check_edge(u, v)
        if w == 0:
            raise ValueError("Peso 0 reservado para 'sem aresta'.")
        if self.adj[u][v] == 0.0:
            self.edge_count += 1
        self.adj[u][v] = w

    def get_edge_weight(self, u: int, v: int) -> float:
        self.check_edge(u, v)
        if self.adj[u][v] == 0.0:
            raise ValueError(f"Aresta ({u},{v}) não existe.")
        return self.adj[u][v]

    def get_matrix(self):
        return self.adj

    def export_to_gephi(self, path: str):
        file_path = path if path.endswith(".gexf") else path + ".gexf"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write('<gexf xmlns="http://gexf.net/1.3" version="1.3">\n')
            f.write('  <graph defaultedgetype="directed">\n')
            f.write('    <nodes>\n')
            for i in range(self.num_vertices):
                f.write(f'      <node id="{i}" label="{self.vertex_labels[i]}" weight="{self.vertex_weights[i]:.4f}"/>\n')
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
