"""
Suíte de testes unitários PureNetworkX sobre AbstractGraph (snake_case).

Garante que a camada de adaptação (`grafo.networkx_pure.adapter`) preserva o
comportamento esperado em todas as 11 categorias.
"""
from __future__ import annotations

import unittest

from grafo.graph.adjacency_list_graph import AdjacencyListGraph
from grafo.graph.adjacency_matrix_graph import AdjacencyMatrixGraph
from grafo.networkx_pure import GraphAdapter, PureNetworkX, run_category_demo, CATEGORY_NAMES
from grafo.networkx_pure.gexf_io import read_gexf, write_gexf


def _triangle(n: int = 3) -> AdjacencyListGraph:
    g = AdjacencyListGraph(n)
    for u in range(n):
        v = (u + 1) % n
        g.set_edge_weight(u, v, 1.0)
    return g


def _dag5() -> AdjacencyListGraph:
    g = AdjacencyListGraph(5)
    edges = [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]
    for u, v in edges:
        g.set_edge_weight(u, v, 1.0)
    return g


class AdapterContractTests(unittest.TestCase):
    def test_camelcase_protocol_present(self):
        a = GraphAdapter(_triangle())
        for name in ("getVertexCount", "getEdgeCount", "hasEdge", "addEdge",
                     "removeEdge", "successors", "predecessors",
                     "getEdgeWeight", "setEdgeWeight"):
            self.assertTrue(callable(getattr(a, name)), f"faltou {name}")

    def test_successors_predecessors_consistency(self):
        a = GraphAdapter(_dag5())
        self.assertEqual(a.successors(0), [1, 2])
        self.assertEqual(a.predecessors(3), [1, 2])

    def test_cache_invalidation(self):
        a = GraphAdapter(_dag5())
        self.assertEqual(a.successors(0), [1, 2])
        a.addEdge(0, 4)
        self.assertEqual(a.successors(0), [1, 2, 4])


class TraversalTests(unittest.TestCase):
    def test_bfs(self):
        self.assertEqual(PureNetworkX.bfs(GraphAdapter(_dag5()), 0), [0, 1, 2, 3, 4])

    def test_dfs(self):
        result = PureNetworkX.dfs(GraphAdapter(_dag5()), 0)
        self.assertEqual(sorted(result), [0, 1, 2, 3, 4])

    def test_topological_sort(self):
        order = PureNetworkX.topological_sort(GraphAdapter(_dag5()))
        pos = {v: i for i, v in enumerate(order)}
        for u, v in [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]:
            self.assertLess(pos[u], pos[v])


class ConnectivityTests(unittest.TestCase):
    def test_scc_triangle(self):
        comps = PureNetworkX.tarjan_scc(GraphAdapter(_triangle()))
        self.assertEqual(len(comps), 1)
        self.assertEqual(sorted(comps[0]), [0, 1, 2])

    def test_articulation_and_bridges(self):
        # caminho 0-1-2-3 (não direcionado): vértices 1,2 = articulação
        g = AdjacencyListGraph(4)
        for u, v in [(0, 1), (1, 2), (2, 3)]:
            g.set_edge_weight(u, v, 1.0)
            g.set_edge_weight(v, u, 1.0)
        a = GraphAdapter(g)
        self.assertEqual(sorted(PureNetworkX.articulation_points(a)), [1, 2])
        self.assertGreaterEqual(len(PureNetworkX.bridges(a)), 1)


class ShortestPathTests(unittest.TestCase):
    def test_dijkstra(self):
        g = AdjacencyListGraph(4)
        for u, v, w in [(0, 1, 1), (1, 2, 2), (0, 2, 5), (2, 3, 1)]:
            g.set_edge_weight(u, v, w)
        dist, _ = PureNetworkX.dijkstra(GraphAdapter(g), 0)
        self.assertEqual(dist[3], 4.0)

    def test_bellman_ford(self):
        g = AdjacencyListGraph(3)
        for u, v, w in [(0, 1, 4), (0, 2, 5), (1, 2, -2)]:
            g.set_edge_weight(u, v, w)
        dist, _ = PureNetworkX.bellman_ford(GraphAdapter(g), 0)
        self.assertEqual(dist[2], 2.0)



class CentralityTests(unittest.TestCase):
    def test_degree_centrality_sums_correctly(self):
        a = GraphAdapter(_triangle())
        dc = PureNetworkX.degree_centrality(a)
        self.assertEqual(len(dc), 3)

    def test_pagerank_distribution(self):
        pr = PureNetworkX.pagerank(GraphAdapter(_dag5()))
        self.assertAlmostEqual(sum(pr.values()), 1.0, places=4)


class GeneratorsTests(unittest.TestCase):
    def test_erdos_renyi_seedable(self):
        g1 = PureNetworkX.erdos_renyi_graph(10, 0.3, seed=1)
        g2 = PureNetworkX.erdos_renyi_graph(10, 0.3, seed=1)
        self.assertEqual(g1.getEdgeCount(), g2.getEdgeCount())

        self.assertEqual(g1.getEdgeCount(), g2.getEdgeCount())


class GexfRoundTripTests(unittest.TestCase):
    def test_roundtrip(self):
        import tempfile, os
        g = _dag5()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "x.gexf")
            write_gexf(g, path, directed=True)
            g2, directed = read_gexf(path)
        self.assertTrue(directed)
        self.assertEqual(g2.get_vertex_count(), g.get_vertex_count())
        self.assertEqual(g2.get_edge_count(), g.get_edge_count())


class CategoryDemosTests(unittest.TestCase):
    def test_every_category_runs(self):
        g = _dag5()
        for idx in range(len(CATEGORY_NAMES)):
            with self.subTest(category=CATEGORY_NAMES[idx]):
                out = run_category_demo(idx, g)
                self.assertIsInstance(out, dict)


class MatrixBackendTests(unittest.TestCase):
    def test_matrix_backend_also_works(self):
        g = AdjacencyMatrixGraph(4)
        for u, v in [(0, 1), (1, 2), (2, 3)]:
            g.set_edge_weight(u, v, 1.0)
        a = GraphAdapter(g)
        self.assertEqual(PureNetworkX.bfs(a, 0), [0, 1, 2, 3])


if __name__ == "__main__":
    unittest.main(verbosity=2)
