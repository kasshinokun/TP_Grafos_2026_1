"""Testes unitários dos algoritmos de grafos."""
import unittest
from grafo.graph.adjacency_list_graph import AdjacencyListGraph
from grafo.networkx_pure.adapter import GraphAdapter
from grafo.networkx_pure.centrality import _bfs_distances
from tests.fixtures import synthetic_graphs as sg


class TestBFS(unittest.TestCase):
    """Testes de busca em largura."""
    
    def test_bfs_complete_graph(self):
        """BFS em grafo completo visita todos os nós."""
        G = sg.complete_graph(5)
        adapter = GraphAdapter(G)
        
        dist = _bfs_distances(adapter, 0, directed=False)
        
        self.assertEqual(len(dist), 5)
        for node in range(5):
            self.assertIn(node, dist)
    
    def test_bfs_disconnected_graph(self):
        """BFS em grafo desconexo não visita nós inalcançáveis."""
        G = AdjacencyListGraph(4)
        G.add_edge(0, 1)
        G.add_edge(1, 0)
        # Nós 2 e 3 estão desconectados
        
        adapter = GraphAdapter(G)
        dist = _bfs_distances(adapter, 0, directed=False)
        
        self.assertIn(0, dist)
        self.assertIn(1, dist)
        self.assertNotIn(2, dist)
        self.assertNotIn(3, dist)
    
    def test_bfs_path_graph_distances(self):
        """BFS em caminho calcula distâncias corretas."""
        G = sg.path_graph(5)
        adapter = GraphAdapter(G)
        
        dist = _bfs_distances(adapter, 0, directed=False)
        
        self.assertEqual(dist[0], 0)
        self.assertEqual(dist[1], 1)
        self.assertEqual(dist[2], 2)
        self.assertEqual(dist[3], 3)
        self.assertEqual(dist[4], 4)


class TestDFS(unittest.TestCase):
    """Testes de busca em profundidade."""
    
    def test_dfs_visits_all_reachable(self):
        """DFS visita todos os nós alcançáveis."""
        G = sg.star_graph(6)
        adapter = GraphAdapter(G)
        
        visited = set()
        stack = [0]
        
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                for neighbor in adapter.neighbors(node):
                    if neighbor not in visited:
                        stack.append(neighbor)
        
        self.assertEqual(len(visited), 6)


class TestDijkstra(unittest.TestCase):
    """Testes do algoritmo de Dijkstra."""
    
    def test_dijkstra_uniform_weights(self):
        """Dijkstra com pesos uniformes equivale a BFS."""
        G = sg.path_graph(5)
        adapter = GraphAdapter(G)
        
        # Define todos os pesos como 1.0
        for u in adapter.nodes():
            for v in adapter.successors(u):
                G.set_edge_weight(u, v, 1.0)
        
        # Dijkstra simplificado (BFS com pesos)
        import heapq
        dist = {0: 0}
        pq = [(0, 0)]
        
        while pq:
            d, u = heapq.heappop(pq)
            if d > dist.get(u, float('inf')):
                continue
            for v in adapter.successors(u):
                weight = G.get_edge_weight(u, v)
                new_dist = d + weight
                if new_dist < dist.get(v, float('inf')):
                    dist[v] = new_dist
                    heapq.heappush(pq, (new_dist, v))
        
        self.assertEqual(dist[4], 4)


class TestConnectivity(unittest.TestCase):
    """Testes de conectividade."""
    
    def test_is_connected_true(self):
        """Grafo conexo retorna True."""
        G = sg.cycle_graph(5)
        self.assertTrue(G.is_connected())
    
    def test_is_connected_false(self):
        """Grafo desconexo retorna False."""
        G = AdjacencyListGraph(4)
        G.add_edge(0, 1)
        G.add_edge(1, 0)
        G.add_edge(2, 3)
        G.add_edge(3, 2)
        
        self.assertFalse(G.is_connected())
    
    def test_weakly_connected_directed(self):
        """Grafo direcionado fracamente conexo."""
        G = AdjacencyListGraph(3)
        G.add_edge(0, 1)
        G.add_edge(1, 2)
        # Não há arestas reversas, mas é fracamente conexo
        
        self.assertTrue(G.is_connected())


class TestGraphProperties(unittest.TestCase):
    """Testes de propriedades do grafo."""
    
    def test_is_complete_graph(self):
        """Grafo completo retorna True."""
        G = sg.complete_graph(4)
        self.assertTrue(G.is_complete_graph())
    
    def test_is_not_complete_graph(self):
        """Grafo não completo retorna False."""
        G = sg.cycle_graph(4)
        self.assertFalse(G.is_complete_graph())
    
    def test_is_empty_graph(self):
        """Grafo vazio retorna True."""
        G = AdjacencyListGraph(0)
        self.assertTrue(G.is_empty_graph())
    
    def test_is_not_empty_graph(self):
        """Grafo não vazio retorna False."""
        G = AdjacencyListGraph(3)
        self.assertFalse(G.is_empty_graph())


if __name__ == '__main__':
    unittest.main()