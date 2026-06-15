import tempfile
import unittest
import sys
import os
from pathlib import Path

# Adiciona a raiz do projeto ao path para que o Python encontre a pasta graph_engine
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from graph_engine.implementations import AdjacencyListGraph, AdjacencyMatrixGraph
from graph_engine.abstract_graph import GraphError

class GraphContract(unittest.TestCase):
    graph_type = AdjacencyListGraph

    def setUp(self):
        self.graph = self.graph_type(4)

    def test_add_is_idempotent_and_remove(self):
        self.graph.addEdge(0, 1)
        self.graph.addEdge(0, 1)
        self.assertEqual(1, self.graph.getEdgeCount())
        self.assertTrue(self.graph.hasEdge(0, 1))
        self.graph.removeEdge(0, 1)
        self.assertTrue(self.graph.isEmptyGraph())

    def test_simple_graph_rejects_loops(self):
        with self.assertRaises(GraphError):
            self.graph.addEdge(0, 0)

    def test_invalid_vertices_raise(self):
        with self.assertRaises(IndexError):
            self.graph.hasEdge(-1, 0)
        with self.assertRaises(IndexError):
            self.graph.addEdge(0, 9)

    def test_relations_and_degrees(self):
        self.graph.addEdge(0, 2)
        self.graph.addEdge(0, 3)
        self.graph.addEdge(1, 2)
        self.assertTrue(self.graph.isSucessor(0, 2))
        self.assertTrue(self.graph.isPredessor(2, 0))
        self.assertTrue(self.graph.isDivergent(0, 2, 0, 3))
        self.assertTrue(self.graph.isConvergent(0, 2, 1, 2))
        self.assertTrue(self.graph.isIncident(0, 2, 0))
        self.assertEqual(2, self.graph.getVertexOutDegree(0))
        self.assertEqual(2, self.graph.getVertexInDegree(2))

    def test_weights_and_labels(self):
        self.graph.addEdge(0, 1)
        self.graph.setVertexWeight(0, 2.5)
        self.graph.setEdgeWeight(0, 1, 5)
        self.graph.setVertexLabel(0, "tiangolo")
        self.assertEqual(2.5, self.graph.getVertexWeight(0))
        self.assertEqual(5, self.graph.getEdgeWeight(0, 1))
        self.assertEqual("tiangolo", self.graph.getVertexLabel(0))
        with self.assertRaises(GraphError):
            self.graph.setEdgeWeight(1, 0, 2)

    def test_connectivity_completeness_and_export(self):
        self.graph.addEdge(0, 1)
        self.graph.addEdge(1, 2)
        self.graph.addEdge(2, 3)
        self.assertTrue(self.graph.isConnected())
        complete = self.graph_type(3)
        for u in range(3):
            for v in range(3):
                if u != v:
                    complete.addEdge(u, v)
        self.assertTrue(complete.isCompleteGraph())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph.gexf"
            complete.exportToGEPHI(str(path))
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('defaultedgetype="directed"', content)

class TestAdjacencyList(GraphContract):
    graph_type = AdjacencyListGraph

class TestAdjacencyMatrix(GraphContract):
    graph_type = AdjacencyMatrixGraph

if __name__ == '__main__':
    unittest.main()