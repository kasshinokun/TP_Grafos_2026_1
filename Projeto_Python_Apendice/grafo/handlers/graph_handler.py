from ..events.event_type import EventType
from ..events.event import Event
from ..events.event_bus import EventBus
from ..core.graph_registry import GraphRegistry
from ..graph.adjacency_list_graph import AdjacencyListGraph
from ..graph.adjacency_matrix_graph import AdjacencyMatrixGraph

class GraphHandler:
    def __init__(self, registry: GraphRegistry):
        self.registry = registry

    def register_all(self, bus: EventBus):
        bus.subscribe(EventType.GRAPH_CREATE, self.on_create)
        bus.subscribe(EventType.GRAPH_ADD_VERTEX, self.on_add_vertex)
        bus.subscribe(EventType.GRAPH_ADD_EDGE, self.on_add_edge)
        bus.subscribe(EventType.GRAPH_REMOVE_EDGE, self.on_remove_edge)
        bus.subscribe(EventType.GRAPH_HAS_EDGE, self.on_has_edge)
        bus.subscribe(EventType.GRAPH_GET_VERTEX_COUNT, self.on_get_vertex_count)
        bus.subscribe(EventType.GRAPH_GET_EDGE_COUNT, self.on_get_edge_count)
        bus.subscribe(EventType.GRAPH_SET_VERTEX_WEIGHT, self.on_set_vertex_weight)
        bus.subscribe(EventType.GRAPH_GET_VERTEX_WEIGHT, self.on_get_vertex_weight)
        bus.subscribe(EventType.GRAPH_SET_EDGE_WEIGHT, self.on_set_edge_weight)
        bus.subscribe(EventType.GRAPH_GET_EDGE_WEIGHT, self.on_get_edge_weight)
        bus.subscribe(EventType.GRAPH_IN_DEGREE, self.on_in_degree)
        bus.subscribe(EventType.GRAPH_OUT_DEGREE, self.on_out_degree)
        bus.subscribe(EventType.GRAPH_IS_SUCCESSOR, self.on_is_successor)
        bus.subscribe(EventType.GRAPH_IS_PREDECESSOR, self.on_is_predecessor)
        bus.subscribe(EventType.GRAPH_IS_DIVERGENT, self.on_is_divergent)
        bus.subscribe(EventType.GRAPH_IS_CONVERGENT, self.on_is_convergent)
        bus.subscribe(EventType.GRAPH_IS_INCIDENT, self.on_is_incident)
        bus.subscribe(EventType.GRAPH_IS_CONNECTED, self.on_is_connected)
        bus.subscribe(EventType.GRAPH_IS_EMPTY, self.on_is_empty)
        bus.subscribe(EventType.GRAPH_IS_COMPLETE, self.on_is_complete)
        bus.subscribe(EventType.GRAPH_EXPORT_GEPHI, self.on_export_gephi)

    def on_create(self, ev: Event):
        gid = ev.get_string("graphId")
        n = ev.get_int("numVertices")
        impl = ev.get_string("impl")
        if self.registry.contains(gid):
            raise ValueError(f"Grafo já existe: {gid}")
        
        if impl == "matrix":
            g = AdjacencyMatrixGraph(n)
        else:
            g = AdjacencyListGraph(n)
        self.registry.register(gid, g)

    def on_add_vertex(self, ev: Event):
        gid = ev.get_string("graphId")
        label = ev.get_string("label")
        old_g = self.registry.get(gid)
        n = old_g.get_vertex_count()
        
        # Cria novo grafo com n+1 vértices
        from ..graph.abstract_graph import RepType
        if old_g.rep_type == RepType.MATRIX:
            new_g = AdjacencyMatrixGraph(n + 1)
        else:
            new_g = AdjacencyListGraph(n + 1)
            
        # Copia dados
        for i in range(n):
            new_g.set_vertex_label(i, old_g.get_vertex_label(i))
            new_g.set_vertex_weight(i, old_g.get_vertex_weight(i))
            for j in range(n):
                if old_g.has_edge(i, j):
                    new_g.set_edge_weight(i, j, old_g.get_edge_weight(i, j))
        
        if label:
            new_g.set_vertex_label(n, label)
        self.registry.register(gid, new_g)

    def on_add_edge(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        g.add_edge(ev.get_int("u"), ev.get_int("v"))

    def on_remove_edge(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        g.remove_edge(ev.get_int("u"), ev.get_int("v"))

    def on_has_edge(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.has_edge(ev.get_int("u"), ev.get_int("v")))

    def on_get_vertex_count(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.get_vertex_count())

    def on_get_edge_count(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.get_edge_count())

    def on_set_vertex_weight(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        g.set_vertex_weight(ev.get_int("v"), ev.get_double("weight"))

    def on_get_vertex_weight(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.get_vertex_weight(ev.get_int("v")))

    def on_set_edge_weight(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        g.set_edge_weight(ev.get_int("u"), ev.get_int("v"), ev.get_double("weight"))

    def on_get_edge_weight(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.get_edge_weight(ev.get_int("u"), ev.get_int("v")))

    def on_in_degree(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.get_vertex_in_degree(ev.get_int("v")))

    def on_out_degree(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.get_vertex_out_degree(ev.get_int("v")))

    def on_is_successor(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_successor(ev.get_int("u"), ev.get_int("v")))

    def on_is_predecessor(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_predecessor(ev.get_int("u"), ev.get_int("v")))

    def on_is_divergent(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_divergent(ev.get_int("u1"), ev.get_int("v1"), ev.get_int("u2"), ev.get_int("v2")))

    def on_is_convergent(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_convergent(ev.get_int("u1"), ev.get_int("v1"), ev.get_int("u2"), ev.get_int("v2")))

    def on_is_incident(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_incident(ev.get_int("u"), ev.get_int("v"), ev.get_int("x")))

    def on_is_connected(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_connected())

    def on_is_empty(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_empty_graph())

    def on_is_complete(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        ev.set_result(g.is_complete_graph())

    def on_export_gephi(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        g.export_to_gephi(ev.get_string("path"))
