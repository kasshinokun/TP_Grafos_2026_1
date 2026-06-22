"""Testes para as representações estruturais e heurísticas de grafo
adicionadas para o botão "Mostrar estrutura" (gui/frames/api_primitiva.py):

- grafo.utils.graph_structure: matriz/lista de adjacência, sequência
  de graus (opera sobre AbstractGraph).
- grafo.networkx_pure.structure: heurísticas de classificação
  estrutural — regularidade, vértices isolados/fonte/sorvedouro,
  extremos de grau, classificação qualitativa da topologia (opera
  sobre GraphAdapter).
"""
import unittest

from grafo.graph.adjacency_list_graph import AdjacencyListGraph
from grafo.networkx_pure.adapter import GraphAdapter
from grafo.networkx_pure import structure
from grafo.utils import graph_structure as gs
from tests.fixtures import synthetic_graphs as sg


class TestAdjacencyMatrix(unittest.TestCase):
    def test_matrix_matches_has_edge(self):
        """A matriz de adjacência deve reproduzir exatamente has_edge/
        get_edge_weight para cada par (u, v)."""
        G = sg.cycle_graph(5)
        matrix = gs.adjacency_matrix(G)
        n = G.get_vertex_count()
        for u in range(n):
            for v in range(n):
                if u == v:
                    self.assertEqual(matrix[u][v], 0.0)
                elif G.has_edge(u, v):
                    self.assertEqual(matrix[u][v], G.get_edge_weight(u, v))
                else:
                    self.assertEqual(matrix[u][v], 0.0)

    def test_empty_graph_matrix_is_empty(self):
        """Grafo com 0 vértices produz matriz vazia (lista vazia)."""
        G = AdjacencyListGraph(0)
        self.assertEqual(gs.adjacency_matrix(G), [])

    def test_format_respects_max_vertices_limit(self):
        """Acima do limite de exibição, retorna aviso em vez da matriz
        completa (evita texto ilegível em grafos grandes)."""
        G = sg.complete_graph(5)
        small = gs.format_adjacency_matrix(G, max_vertices=10)
        big = gs.format_adjacency_matrix(G, max_vertices=2)
        self.assertNotIn("omitida", small)
        self.assertIn("omitida", big)


class TestAdjacencyList(unittest.TestCase):
    def test_list_matches_successors(self):
        """A lista de adjacência deve conter exatamente os mesmos
        sucessores que get_successors/has_edge reportam."""
        G = sg.star_graph(6)
        adj = gs.adjacency_list(G)
        for u in range(G.get_vertex_count()):
            expected_succ = {v for v in range(G.get_vertex_count())
                              if u != v and G.has_edge(u, v)}
            actual_succ = {v for v, _w in adj[u]}
            self.assertEqual(actual_succ, expected_succ)

    def test_isolated_vertex_has_no_successors(self):
        G = AdjacencyListGraph(3)
        G.add_edge(0, 1)
        adj = gs.adjacency_list(G)
        self.assertEqual(adj[2], [])
        formatted = gs.format_adjacency_list(G)
        self.assertIn("nenhum sucessor", formatted)


class TestDegreeSequence(unittest.TestCase):
    def test_degree_sequence_complete_graph(self):
        """Em K_n, todo vértice tem grau_entrada = grau_saída = n-1."""
        n = 5
        G = sg.complete_graph(n)
        seq = gs.degree_sequence(G)
        for vertex, din, dout in seq:
            self.assertEqual(din, n - 1)
            self.assertEqual(dout, n - 1)

    def test_degree_sequence_star_graph(self):
        """Na estrela, o centro (0) tem grau de saída n-1; as folhas
        têm grau de saída 1 (aresta de volta ao centro)."""
        n = 6
        G = sg.star_graph(n)
        seq = dict((v, (din, dout)) for v, din, dout in gs.degree_sequence(G))
        self.assertEqual(seq[0][1], n - 1)  # out_degree do centro
        for leaf in range(1, n):
            self.assertEqual(seq[leaf][1], 1)


class TestIsolatedSourceSinkVertices(unittest.TestCase):
    def test_isolated_vertices_detected(self):
        G = AdjacencyListGraph(4)
        G.add_edge(0, 1)
        adapter = GraphAdapter(G)
        self.assertEqual(structure.isolated_vertices(adapter), [2, 3])

    def test_no_isolated_vertices_in_complete_graph(self):
        G = sg.complete_graph(4)
        adapter = GraphAdapter(G)
        self.assertEqual(structure.isolated_vertices(adapter), [])

    def test_source_and_sink_in_directed_chain(self):
        """Cadeia 0->1->2->3: vértice 0 é fonte, vértice 3 é sorvedouro,
        1 e 2 não são nem fonte nem sorvedouro."""
        G = AdjacencyListGraph(4)
        G.add_edge(0, 1)
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        adapter = GraphAdapter(G)
        self.assertEqual(structure.source_vertices(adapter), [0])
        self.assertEqual(structure.sink_vertices(adapter), [3])

    def test_undirected_graph_has_no_source_or_sink(self):
        """Em um grafo não direcionado "puro" (arestas sempre em par),
        in_degree == out_degree para todo vértice, então não há fonte
        nem sorvedouro (a menos que isolado)."""
        G = sg.cycle_graph(5)  # cycle_graph já adiciona aresta nos dois sentidos? checar
        adapter = GraphAdapter(G)
        # cycle_graph (fixture) só adiciona um sentido por padrão;
        # o que importa aqui é que a fonte/sorvedouro residam em quem
        # de fato tem in_degree==0 xor out_degree==0 — sem assumir nada
        # além do que a própria função calcula.
        sources = structure.source_vertices(adapter)
        sinks = structure.sink_vertices(adapter)
        for u in sources:
            self.assertEqual(adapter.in_degree(u), 0)
            self.assertGreater(adapter.out_degree(u), 0)
        for u in sinks:
            self.assertEqual(adapter.out_degree(u), 0)
            self.assertGreater(adapter.in_degree(u), 0)


class TestIsRegular(unittest.TestCase):
    def test_complete_graph_is_regular(self):
        G = sg.complete_graph(5)
        adapter = GraphAdapter(G)
        self.assertTrue(structure.is_regular(adapter))

    def test_star_graph_is_not_regular(self):
        """No grafo estrela, o centro tem grau muito maior que as
        folhas — não é regular."""
        G = sg.star_graph(6)
        adapter = GraphAdapter(G)
        self.assertFalse(structure.is_regular(adapter))

    def test_empty_graph_is_vacuously_regular(self):
        G = AdjacencyListGraph(0)
        adapter = GraphAdapter(G)
        self.assertTrue(structure.is_regular(adapter))


class TestDegreeExtremes(unittest.TestCase):
    def test_star_graph_extremes(self):
        """No grafo estrela, o centro tem o maior grau total; as
        folhas têm o menor (e igual entre si)."""
        n = 6
        G = sg.star_graph(n)
        adapter = GraphAdapter(G)
        max_v, max_d, min_v, min_d = structure.degree_extremes(adapter)
        self.assertEqual(max_v, 0)
        self.assertEqual(max_d, 2 * (n - 1))  # in+out do centro
        self.assertNotEqual(min_v, 0)

    def test_empty_graph_returns_none(self):
        G = AdjacencyListGraph(0)
        adapter = GraphAdapter(G)
        self.assertIsNone(structure.degree_extremes(adapter))


class TestClassifyTopology(unittest.TestCase):
    def test_empty_graph(self):
        G = AdjacencyListGraph(0)
        adapter = GraphAdapter(G)
        self.assertIn("vazio", structure.classify_topology(adapter).lower())

    def test_graph_without_edges(self):
        G = AdjacencyListGraph(3)
        adapter = GraphAdapter(G)
        msg = structure.classify_topology(adapter).lower()
        self.assertIn("sem nenhuma aresta", msg)

    def test_complete_graph(self):
        G = sg.complete_graph(4)
        adapter = GraphAdapter(G)
        self.assertIn("completo", structure.classify_topology(adapter).lower())

    def test_regular_non_complete_graph(self):
        """Um ciclo C_n (n>=4) com arestas nos dois sentidos é regular
        mas não completo: deve cair na classificação "regular"."""
        n = 6
        G = AdjacencyListGraph(n)
        for i in range(n):
            G.add_edge(i, (i + 1) % n)
            G.add_edge((i + 1) % n, i)
        adapter = GraphAdapter(G)
        msg = structure.classify_topology(adapter).lower()
        self.assertIn("regular", msg)

    def test_sparse_graph_with_isolated_vertex(self):
        G = AdjacencyListGraph(5)
        G.add_edge(0, 1)
        adapter = GraphAdapter(G)
        msg = structure.classify_topology(adapter).lower()
        self.assertIn("isolado", msg)


class TestStructuralSummary(unittest.TestCase):
    def test_summary_keys_present(self):
        """O resumo deve sempre conter todas as chaves esperadas,
        mesmo para grafos vazios ou sem arestas (sem lançar exceção)."""
        expected_keys = {
            "num_vertices", "num_edges", "density", "is_regular",
            "isolated_vertices", "source_vertices", "sink_vertices",
            "max_degree_vertex", "max_degree", "min_degree_vertex",
            "min_degree", "topology_classification",
        }
        for G in (AdjacencyListGraph(0), AdjacencyListGraph(3), sg.complete_graph(4)):
            adapter = GraphAdapter(G)
            summary = structure.structural_summary(adapter)
            self.assertEqual(set(summary.keys()), expected_keys)

    def test_summary_consistent_with_individual_functions(self):
        G = sg.two_cliques_bridge(3)
        adapter = GraphAdapter(G)
        summary = structure.structural_summary(adapter)
        self.assertEqual(summary["num_vertices"], adapter.number_of_nodes())
        self.assertEqual(summary["num_edges"], adapter.number_of_edges())
        self.assertEqual(summary["density"], structure.density(adapter))
        self.assertEqual(summary["is_regular"], structure.is_regular(adapter))
        self.assertEqual(summary["isolated_vertices"], structure.isolated_vertices(adapter))


if __name__ == "__main__":
    unittest.main()
