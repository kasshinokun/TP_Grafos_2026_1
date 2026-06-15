import unittest
import os
from grafo.core.application import Application
from grafo.events.event_type import EventType
from grafo.events.event import Event
from grafo.graph.abstract_graph import RepType

class TestGrafo(unittest.TestCase):
    def setUp(self):
        self.app = Application()
        self.bus = self.app.get_bus()
        self.registry = self.app.get_registry()

    def test_create_graph(self):
        ev = self.bus.publish(Event(EventType.GRAPH_CREATE).with_payload("graphId", "g1").with_payload("numVertices", 5).with_payload("impl", "list"))
        self.assertTrue(ev.success)
        self.assertTrue(self.registry.contains("g1"))
        g = self.registry.get("g1")
        self.assertEqual(g.get_vertex_count(), 5)
        self.assertEqual(g.rep_type, RepType.LIST)

    def test_add_edge(self):
        self.bus.publish(Event(EventType.GRAPH_CREATE).with_payload("graphId", "g1").with_payload("numVertices", 5).with_payload("impl", "list"))
        ev = self.bus.publish(Event(EventType.GRAPH_ADD_EDGE).with_payload("graphId", "g1").with_payload("u", 0).with_payload("v", 1))
        self.assertTrue(ev.success)
        g = self.registry.get("g1")
        self.assertTrue(g.has_edge(0, 1))
        self.assertEqual(g.get_edge_count(), 1)

    def test_bfs(self):
        self.bus.publish(Event(EventType.GRAPH_CREATE).with_payload("graphId", "g1").with_payload("numVertices", 3).with_payload("impl", "list"))
        self.bus.publish(Event(EventType.GRAPH_ADD_EDGE).with_payload("graphId", "g1").with_payload("u", 0).with_payload("v", 1))
        self.bus.publish(Event(EventType.GRAPH_ADD_EDGE).with_payload("graphId", "g1").with_payload("u", 1).with_payload("v", 2))
        ev = self.bus.publish(Event(EventType.ALGO_BFS).with_payload("graphId", "g1").with_payload("source", 0))
        self.assertEqual(ev.result, [0, 1, 2])

    def test_shortest_path(self):
        self.bus.publish(Event(EventType.GRAPH_CREATE).with_payload("graphId", "g1").with_payload("numVertices", 3).with_payload("impl", "list"))
        self.bus.publish(Event(EventType.GRAPH_ADD_EDGE).with_payload("graphId", "g1").with_payload("u", 0).with_payload("v", 1))
        self.bus.publish(Event(EventType.GRAPH_SET_EDGE_WEIGHT).with_payload("graphId", "g1").with_payload("u", 0).with_payload("v", 1).with_payload("weight", 10.0))
        self.bus.publish(Event(EventType.GRAPH_ADD_EDGE).with_payload("graphId", "g1").with_payload("u", 1).with_payload("v", 2))
        self.bus.publish(Event(EventType.GRAPH_SET_EDGE_WEIGHT).with_payload("graphId", "g1").with_payload("u", 1).with_payload("v", 2).with_payload("weight", 5.0))
        
        ev = self.bus.publish(Event(EventType.ALGO_SHORTEST_PATH).with_payload("graphId", "g1").with_payload("source", 0).with_payload("target", 2))
        self.assertEqual(ev.result["path"], [0, 1, 2])
        self.assertEqual(ev.result["dist"], 15.0)

    def test_csv_load_and_build(self):
        csv_path = "test_interactions.csv"
        with open(csv_path, 'w') as f:
            f.write("actor,target,type\n")
            f.write("alice,bob,COMMENT_ON_ISSUE_OR_PR\n")
            f.write("bob,charlie,PR_MERGE\n")
        
        self.bus.publish(Event(EventType.MINING_LOAD_CSV).with_payload("path", csv_path))
        self.bus.publish(Event(EventType.MINING_BUILD_INTEGRATED_GRAPH))
        
        self.assertTrue(self.registry.contains("graph_integrated"))
        g = self.registry.get("graph_integrated")
        self.assertEqual(g.get_vertex_count(), 3)
        # alice -> bob (peso 2), bob -> charlie (peso 5)
        self.assertEqual(g.get_edge_weight(0, 1), 2.0)
        self.assertEqual(g.get_edge_weight(1, 2), 5.0)
        
        os.remove(csv_path)

if __name__ == "__main__":
    unittest.main()
