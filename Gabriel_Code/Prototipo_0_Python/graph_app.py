from core.base_app import MicroApp
from models.graph_models import AdjacencyListGraph

class GraphMicroApp(MicroApp):
    def __init__(self):
        super().__init__("GraphApp")
        self.graph = None

    def _handle_event(self, event_type: str, payload: dict):
        if event_type == "API_POST_CREATE_GRAPH":
            num_nodes = payload.get("num_nodes", 0)
            print(f"[{self.name}] Criando grafo com {num_nodes} nós")
            self.graph = AdjacencyListGraph(num_nodes)
            self.bus.publish("RESPONSE_POST_CREATE_GRAPH", {"status": "created"})

        elif event_type == "API_GET_GRAPH_STATS":
            if self.graph:
                stats = {
                    "vertices": self.graph.get_vertex_count(),
                    "edges": self.graph.get_edge_count()
                }
                self.bus.publish("RESPONSE_GET_GRAPH_STATS", stats)
            else:
                self.bus.publish("RESPONSE_GET_GRAPH_STATS", {"error": "Graph not initialized"})
