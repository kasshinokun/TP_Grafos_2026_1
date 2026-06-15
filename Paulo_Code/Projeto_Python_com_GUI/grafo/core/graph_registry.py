from typing import Dict, Set, Optional

class GraphRegistry:
    def __init__(self):
        self.store = {}

    def register(self, graph_id: str, graph):
        self.store[graph_id] = graph

    def get(self, graph_id: str):
        graph = self.store.get(graph_id)
        if graph is None:
            raise ValueError(f"Grafo não encontrado: {graph_id}")
        return graph

    def contains(self, graph_id: str) -> bool:
        return graph_id in self.store

    def remove(self, graph_id: str):
        if graph_id in self.store:
            del self.store[graph_id]

    def list_ids(self) -> Set[str]:
        return set(self.store.keys())
