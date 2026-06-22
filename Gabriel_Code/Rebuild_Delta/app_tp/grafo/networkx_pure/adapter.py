from grafo.graph.abstract_graph import AbstractGraph

class GraphAdapter:
    def __init__(self, graph: AbstractGraph):
        self._g = graph
        self._succ_cache = {}
        self._pred_cache = {}

    def _validate_vertex(self, u: int): self._g.check_vertex(u)

    def number_of_nodes(self): return self._g.get_vertex_count()
    def number_of_edges(self): return self._g.get_edge_count()
    def nodes(self): return list(range(self._g.get_vertex_count()))

    def successors(self, u: int):
        self._validate_vertex(u)
        if u in self._succ_cache: return list(self._succ_cache[u])
        
        # Otimização: Busca método O(1) se existir
        if hasattr(self._g, 'get_successors'):
            out = list(self._g.get_successors(u))
        else:
            n = self._g.get_vertex_count()
            out = [v for v in range(n) if v != u and self._g.has_edge(u, v)]
            
        self._succ_cache[u] = out
        return list(out)

    def predecessors(self, v: int):
        self._validate_vertex(v)
        if v in self._pred_cache: return list(self._pred_cache[v])
        
        if hasattr(self._g, 'get_predecessors'):
            out = list(self._g.get_predecessors(v))
        else:
            n = self._g.get_vertex_count()
            out = [u for u in range(n) if u != v and self._g.has_edge(u, v)]
            
        self._pred_cache[v] = out
        return list(out)

    def neighbors(self, u: int):
        return list(set(self.successors(u)) | set(self.predecessors(u)))

    def in_degree(self, u: int): return self._g.get_vertex_in_degree(u)
    def out_degree(self, u: int): return self._g.get_vertex_out_degree(u)
    
    def edges(self):
        return [(u, v) for u in self.nodes() for v in self.successors(u)]