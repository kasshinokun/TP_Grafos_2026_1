"""Testes da API obrigatória do PDF."""
import unittest
from grafo.graph.adjacency_list_graph import AdjacencyListGraph


class TestAbstractGraphAPI(unittest.TestCase):
    def setUp(self):
        self.G = AdjacencyListGraph(5)
    
    def test_add_edge_idempotent(self):
        """addEdge(u,v) não deve duplicar arestas."""
        self.G.add_edge(0, 1)
        self.G.add_edge(0, 1)
        self.assertEqual(self.G.get_edge_count(), 1)
    
    def test_self_loop_rejected(self):
        """Grafos simples não permitem laços."""
        with self.assertRaises(ValueError):
            self.G.add_edge(0, 0)
    
    def test_invalid_vertex_raises(self):
        """Índices inválidos devem lançar exceção."""
        with self.assertRaises(IndexError):
            self.G.add_edge(0, 10)
        with self.assertRaises(IndexError):
            self.G.has_edge(-1, 0)
    
    def test_has_edge(self):
        self.G.add_edge(0, 1)
        self.assertTrue(self.G.has_edge(0, 1))
        self.assertFalse(self.G.has_edge(1, 0))  # Direcionado
    
    def test_remove_edge(self):
        self.G.add_edge(0, 1)
        self.G.remove_edge(0, 1)
        self.assertFalse(self.G.has_edge(0, 1))
        self.assertEqual(self.G.get_edge_count(), 0)
    
    def test_in_degree_out_degree(self):
        self.G.add_edge(0, 1)
        self.G.add_edge(0, 2)
        self.G.add_edge(3, 1)
        self.assertEqual(self.G.get_vertex_out_degree(0), 2)
        self.assertEqual(self.G.get_vertex_in_degree(1), 2)
    
    def test_is_successor_predecessor(self):
        self.G.add_edge(0, 1)
        # is_sucessor(u,v) = True se existe aresta u->v
        self.assertTrue(self.G.is_sucessor(0, 1))
        self.assertFalse(self.G.is_sucessor(1, 0))
        # is_predessor(u,v) = True se u é predecessor de v, i.e. existe v->u
        # Logo is_predessor(1, 0) verifica aresta 0->1 (0 precede 1)
        self.assertTrue(self.G.is_predessor(1, 0))
        self.assertFalse(self.G.is_predessor(0, 1))
    
    def test_is_divergent_convergent(self):
        self.G.add_edge(0, 1)
        self.G.add_edge(0, 2)
        self.G.add_edge(3, 1)
        self.assertTrue(self.G.is_divergent(0, 1, 0, 2))
        self.assertTrue(self.G.is_convergent(0, 1, 3, 1))
    
    def test_is_incident(self):
        self.G.add_edge(0, 1)
        self.assertTrue(self.G.is_incident(0, 1, 0))
        self.assertTrue(self.G.is_incident(0, 1, 1))
        self.assertFalse(self.G.is_incident(0, 1, 2))
    
    def test_is_empty_complete(self):
        self.assertTrue(self.G.is_empty_graph() == False)
        empty = AdjacencyListGraph(0)
        self.assertTrue(empty.is_empty_graph())
        
        K3 = AdjacencyListGraph(3)
        for i in range(3):
            for j in range(3):
                if i != j:
                    K3.add_edge(i, j)
        self.assertTrue(K3.is_complete_graph())
    
    def test_edge_weight(self):
        self.G.add_edge(0, 1)
        self.G.set_edge_weight(0, 1, 3.5)
        self.assertEqual(self.G.get_edge_weight(0, 1), 3.5)
    
    def test_vertex_weight(self):
        self.G.set_vertex_weight(0, 2.5)
        self.assertEqual(self.G.get_vertex_weight(0), 2.5)
    
    def test_is_connected_weak(self):
        # Grafo desconexo
        self.G.add_edge(0, 1)
        self.G.add_edge(2, 3)
        self.assertFalse(self.G.is_connected())
        
        # Grafo conexo
        self.G.add_edge(1, 2)
        self.G.add_edge(3, 4)
        self.assertTrue(self.G.is_connected())


if __name__ == '__main__':
    unittest.main()