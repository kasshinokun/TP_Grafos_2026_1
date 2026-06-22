# ./grafo/graph/adjacency_list_graph.py

from .abstract_graph import AbstractGraph, RepType
from typing import Dict, Set, List


class AdjacencyListGraph(AbstractGraph):
    def __init__(self, num_vertices: int):
        super().__init__(num_vertices, RepType.LIST)
        self.adj: List[Dict[int, float]] = [{} for _ in range(num_vertices)]
        self.rev_adj: List[Dict[int, float]] = [{} for _ in range(num_vertices)] # Grafo Reverso
        self.in_degree_count: List[int] = [0] * num_vertices                     # Cache de In-Degree
        self.edge_count_val = 0

    def get_vertex_count(self) -> int: return self.num_vertices
    def get_edge_count(self) -> int: return self.edge_count_val

    def has_edge(self, u: int, v: int) -> bool:
        self.check_edge(u, v)
        return v in self.adj[u]

    def add_edge(self, u: int, v: int): # Idempotente
        self.check_edge(u, v)
        if v not in self.adj[u]:
            self.adj[u][v] = 1.0
            self.rev_adj[v][u] = 1.0
            self.in_degree_count[v] += 1
            self.edge_count_val += 1

    def remove_edge(self, u: int, v: int):
        self.check_edge(u, v)
        if v in self.adj[u]:
            del self.adj[u][v]
            del self.rev_adj[v][u]
            self.in_degree_count[v] -= 1
            self.edge_count_val -= 1

    def get_vertex_in_degree(self, u: int) -> int:
        self.check_vertex(u)
        return self.in_degree_count[u] # O(1)!

    def get_vertex_out_degree(self, u: int) -> int:
        self.check_vertex(u)
        return len(self.adj[u])

    def set_edge_weight(self, u: int, v: int, w: float):
        self.check_edge(u, v)
        if w == 0: raise ValueError("Peso 0 não é permitido.")
        is_new = v not in self.adj[u]
        self.adj[u][v] = w
        self.rev_adj[v][u] = w
        if is_new:
            self.in_degree_count[v] += 1
            self.edge_count_val += 1

    def get_edge_weight(self, u: int, v: int) -> float:
        self.check_edge(u, v)
        if v not in self.adj[u]: raise ValueError(f"Aresta ({u},{v}) não existe.")
        return self.adj[u][v]

    # Métodos auxiliares para o Adapter (Duck-Typing)
    def get_successors(self, u: int) -> Set[int]:
        self.check_vertex(u)
        return set(self.adj[u].keys())

    def get_predecessors(self, u: int) -> Set[int]:
        self.check_vertex(u)
        return set(self.rev_adj[u].keys())

    def is_connected(self) -> bool: # Verifica conectividade fraca
        if self.num_vertices == 0: return True
        visited = set([0])
        queue = [0]
        while queue:
            curr = queue.pop(0)
            neighbors = self.get_successors(curr) | self.get_predecessors(curr)
            for nb in neighbors:
                if nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        return len(visited) == self.num_vertices

    def export_to_gephi(self, path: str):
        # Função para escapar caracteres especiais do XML (&, <, >, ", ')
        # Substitui xml.sax.saxutils.escape por manipulação direta de strings
        def escape_xml(text):
            text = str(text)
            # A ordem importa: & sempre primeiro para não re-escapar os outros
            return (text.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace('"', "&quot;")
                        .replace("'", "&apos;"))

        # --- Monta os nós ---
        nodes = []
        for i in range(self.num_vertices):
            label_escaped = escape_xml(self.vertex_labels[i])
            nodes.append(f'<node id="{i}" label="{label_escaped}"/>')
        
        # --- Monta as arestas ---
        edges = []
        edge_id = 0
        for u in range(self.num_vertices):
            for v, w in self.adj[u].items():
                edges.append(f'<edge id="{edge_id}" source="{u}" target="{v}" weight="{w:.4f}"/>')
                edge_id += 1

        # --- Constrói o XML completo com indentação ---
        xml_content = f'''<?xml version="1.0" encoding="utf-8"?>
        <gexf xmlns="http://gexf.net/1.3" version="1.3">
        <graph defaultedgetype="directed">
            <nodes>
            {"\n      ".join(nodes)}
            </nodes>
            <edges>
            {"\n      ".join(edges)}
            </edges>
        </graph>
        </gexf>'''

        # --- Escreve no arquivo ---
        with open(path, "w", encoding="utf-8") as f:
            f.write(xml_content)
