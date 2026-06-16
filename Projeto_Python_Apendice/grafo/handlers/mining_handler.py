from ..events.event_type import EventType
from ..events.event import Event
from ..events.event_bus import EventBus
from ..core.graph_registry import GraphRegistry
from ..graph.mining.csv_loader import CsvLoader
from ..graph.mining.interaction import InteractionType
from ..graph.adjacency_list_graph import AdjacencyListGraph

class MiningHandler:
    def __init__(self, registry: GraphRegistry):
        self.registry = registry
        self.interactions = []

    def register_all(self, bus: EventBus):
        bus.subscribe(EventType.MINING_LOAD_CSV, self.on_load_csv)
        bus.subscribe(EventType.MINING_BUILD_GRAPH1_COMMENTS, self.on_build_graph1)
        bus.subscribe(EventType.MINING_BUILD_GRAPH2_CLOSURES, self.on_build_graph2)
        bus.subscribe(EventType.MINING_BUILD_GRAPH3_REVIEWS, self.on_build_graph3)
        bus.subscribe(EventType.MINING_BUILD_INTEGRATED_GRAPH, self.on_build_integrated)

    def on_load_csv(self, ev: Event):
        path = ev.get_string("path")
        self.interactions = CsvLoader.load(path)
        ev.set_result(len(self.interactions))

    def on_build_graph1(self, ev: Event):
        subset = [i for i in self.interactions if i.type == InteractionType.COMMENT_ON_ISSUE_OR_PR]
        self._build_simple_graph(ev, "graph1", subset)

    def on_build_graph2(self, ev: Event):
        subset = [i for i in self.interactions if i.type == InteractionType.ISSUE_CLOSED_BY_OTHER]
        self._build_simple_graph(ev, "graph2", subset)

    def on_build_graph3(self, ev: Event):
        subset = [i for i in self.interactions if i.type in [InteractionType.PR_REVIEW_OR_APPROVAL, InteractionType.PR_MERGE]]
        self._build_simple_graph(ev, "graph3", subset)

    def _build_simple_graph(self, ev: Event, gid: str, subset):
        if not subset:
            g = AdjacencyListGraph(1)
            self.registry.register(gid, g)
            ev.set_result(gid)
            return
            
        users = self._get_unique_users(subset)
        user_to_idx = {user: i for i, user in enumerate(users)}
        g = AdjacencyListGraph(len(users))
        for i, user in enumerate(users):
            g.set_vertex_label(i, user)
        
        for inter in subset:
            u, v = user_to_idx[inter.actor], user_to_idx[inter.target]
            g.add_edge(u, v)
        
        self.registry.register(gid, g)
        ev.set_result(gid)

    def on_build_integrated(self, ev: Event):
        if not self.interactions:
            ev.set_result("graph_integrated")
            return
            
        users = self._get_unique_users(self.interactions)
        user_to_idx = {user: i for i, user in enumerate(users)}
        g = AdjacencyListGraph(len(users))
        for i, user in enumerate(users):
            g.set_vertex_label(i, user)
            
        for inter in self.interactions:
            u, v = user_to_idx[inter.actor], user_to_idx[inter.target]
            if not g.has_edge(u, v):
                g.set_edge_weight(u, v, float(inter.type.weight))
            else:
                curr = g.get_edge_weight(u, v)
                g.set_edge_weight(u, v, curr + float(inter.type.weight))
                
        self.registry.register("graph_integrated", g)
        ev.set_result("graph_integrated")

    def _get_unique_users(self, interactions):
        users = []
        seen = set()
        for i in interactions:
            if i.actor not in seen:
                seen.add(i.actor)
                users.append(i.actor)
            if i.target not in seen:
                seen.add(i.target)
                users.append(i.target)
        return users
