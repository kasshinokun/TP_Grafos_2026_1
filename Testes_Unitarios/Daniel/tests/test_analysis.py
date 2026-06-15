import unittest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_engine.analysis import assortativity, betweenness_centrality, closeness_centrality, clustering_coefficient, degree_centrality, density, pagerank
from graph_engine.implementations import AdjacencyListGraph

class TestAnalysis(unittest.TestCase):
    def setUp(self):
        self.graph = AdjacencyListGraph(3)
        self.graph.addEdge(0, 1)
        self.graph.addEdge(1, 2)

    def test_metrics(self):
        self.assertAlmostEqual(1 / 3, density(self.graph))
        self.assertGreater(degree_centrality(self.graph)[1], degree_centrality(self.graph)[0])
        self.assertGreater(betweenness_centrality(self.graph)[1], 0)
        self.assertGreater(closeness_centrality(self.graph)[0], 0)
        self.assertAlmostEqual(1.0, sum(pagerank(self.graph).values()), places=6)
        self.assertEqual(0.0, clustering_coefficient(self.graph)[1])
        self.assertIsInstance(assortativity(self.graph), float)

if __name__ == '__main__':
    unittest.main()