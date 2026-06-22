"""Testes das 11 métricas de redes complexas com grafos sintéticos."""
import unittest
from grafo.networkx_pure.adapter import GraphAdapter
from grafo.networkx_pure import centrality, structure, communities
from tests.fixtures import synthetic_graphs as sg
from tests.fixtures import expected_results as er


class TestDegreeCentrality(unittest.TestCase):
    def test_complete_graph_uniform_degree(self):
        """Em K_n, todos têm grau n-1."""
        n = 6
        G = sg.complete_graph(n)
        adapter = GraphAdapter(G)
        dc = centrality.degree_centrality(adapter)
        expected = er.complete_graph_expected(n)['degree_in']
        for node, metrics in dc.items():
            self.assertEqual(metrics['in'], expected)
            self.assertEqual(metrics['out'], expected)
    
    def test_star_graph_center_dominance(self):
        """No grafo estrela, o centro tem grau máximo."""
        n = 8
        G = sg.star_graph(n)
        adapter = GraphAdapter(G)
        dc = centrality.degree_centrality(adapter)
        expected = er.star_graph_expected(n)
        self.assertEqual(dc[0]['in'], expected['center_in_degree'])
        self.assertEqual(dc[0]['out'], expected['center_out_degree'])
        for i in range(1, n):
            self.assertEqual(dc[i]['in'], expected['leaf_in_degree'])


class TestBetweennessCentrality(unittest.TestCase):
    def test_complete_graph_zero_betweenness(self):
        """Em K_n, betweenness é 0 (todos caminhos são diretos)."""
        G = sg.complete_graph(5)
        adapter = GraphAdapter(G)
        bc = centrality.betweenness_centrality(adapter)
        for node, val in bc.items():
            self.assertAlmostEqual(val, 0.0, places=5)
    
    def test_star_graph_center_max_betweenness(self):
        """No grafo estrela, o centro tem betweenness máxima."""
        G = sg.star_graph(6)
        adapter = GraphAdapter(G)
        bc = centrality.betweenness_centrality(adapter)
        center_bc = bc[0]
        for i in range(1, 6):
            self.assertGreater(center_bc, bc[i])
    
    def test_bridge_node_top_rank(self):
        """Nó ponte entre dois cliques deve ter betweenness top-1."""
        G = sg.two_cliques_bridge(4)
        adapter = GraphAdapter(G)
        bc = centrality.betweenness_centrality(adapter)
        sorted_nodes = sorted(bc.items(), key=lambda x: x[1], reverse=True)
        self.assertEqual(sorted_nodes[0][0], 0)  # Nó 0 é a ponte


class TestClosenessCentrality(unittest.TestCase):
    def test_complete_graph_uniform_closeness(self):
        """Em K_n, todos têm mesma closeness = 1.0."""
        G = sg.complete_graph(5)
        adapter = GraphAdapter(G)
        cc = centrality.closeness_centrality(adapter)
        values = list(cc.values())
        for v in values:
            self.assertAlmostEqual(v, values[0], places=5)
    
    def test_star_graph_center_max_closeness(self):
        """Centro da estrela tem maior closeness."""
        G = sg.star_graph(6)
        adapter = GraphAdapter(G)
        cc = centrality.closeness_centrality(adapter)
        self.assertGreater(cc[0], max(cc[i] for i in range(1, 6)))


class TestPageRank(unittest.TestCase):
    def test_complete_graph_uniform_pagerank(self):
        """Em K_n, PageRank é uniforme."""
        G = sg.complete_graph(5)
        adapter = GraphAdapter(G)
        pr = centrality.pagerank(adapter)
        values = list(pr.values())
        for v in values:
            self.assertAlmostEqual(v, values[0], places=4)
    
    def test_pagerank_sums_to_one(self):
        """Soma dos PageRanks deve ser ~1.0."""
        G = sg.star_graph(8)
        adapter = GraphAdapter(G)
        pr = centrality.pagerank(adapter)
        self.assertAlmostEqual(sum(pr.values()), 1.0, places=4)


class TestDensity(unittest.TestCase):
    def test_complete_graph_density_one(self):
        G = sg.complete_graph(6)
        adapter = GraphAdapter(G)
        self.assertAlmostEqual(structure.density(adapter), 1.0, places=5)
    
    def test_cycle_graph_density(self):
        n = 10
        G = sg.cycle_graph(n)
        adapter = GraphAdapter(G)
        expected = n / (n * (n - 1))
        self.assertAlmostEqual(structure.density(adapter), expected, places=5)


class TestClusteringCoefficient(unittest.TestCase):
    def test_complete_graph_clustering_one(self):
        """Em K_n (n>=3), clustering = 1.0."""
        G = sg.complete_graph(5)
        adapter = GraphAdapter(G)
        self.assertAlmostEqual(structure.average_clustering(adapter), 1.0, places=5)
    
    def test_cycle_graph_clustering_zero(self):
        """Em C_n (n>=4), clustering = 0.0."""
        G = sg.cycle_graph(6)
        adapter = GraphAdapter(G)
        self.assertAlmostEqual(structure.average_clustering(adapter), 0.0, places=5)


class TestCommunities(unittest.TestCase):
    def test_two_cliques_detect_two_communities(self):
        """Dois cliques conectados por ponte → 2 comunidades."""
        G = sg.two_cliques_bridge(5)
        adapter = GraphAdapter(G)
        comms = communities.label_propagation_communities(adapter)
        # Deve detectar pelo menos 2 comunidades
        self.assertGreaterEqual(len(comms), 2)
    
    def test_complete_graph_single_community(self):
        """K_n deve formar uma única comunidade."""
        G = sg.complete_graph(6)
        adapter = GraphAdapter(G)
        comms = communities.label_propagation_communities(adapter)
        self.assertEqual(len(comms), 1)


class TestBridgingTies(unittest.TestCase):
    def test_bridge_node_connects_multiple_communities(self):
        """Nó ponte deve conectar mais comunidades que os outros."""
        G = sg.two_cliques_bridge(5)
        adapter = GraphAdapter(G)
        bt = communities.bridging_ties(adapter)
        # Nó 0 deve ter o maior bridging ties
        self.assertEqual(max(bt, key=bt.get), 0)


class TestDiameterAndPath(unittest.TestCase):
    def test_complete_graph_diameter_one(self):
        G = sg.complete_graph(5)
        adapter = GraphAdapter(G)
        # Usa método auxiliar de BFS
        from grafo.networkx_pure.centrality import _bfs_distances
        max_dist = 0
        for s in adapter.nodes():
            dist = _bfs_distances(adapter, s, directed=False)
            max_dist = max(max_dist, max(dist.values()))
        self.assertEqual(max_dist, 1)
    
    def test_path_graph_diameter(self):
        n = 7
        G = sg.path_graph(n)
        adapter = GraphAdapter(G)
        from grafo.networkx_pure.centrality import _bfs_distances
        max_dist = 0
        for s in adapter.nodes():
            dist = _bfs_distances(adapter, s, directed=False)
            max_dist = max(max_dist, max(dist.values()))
        self.assertEqual(max_dist, n - 1)


if __name__ == '__main__':
    unittest.main()