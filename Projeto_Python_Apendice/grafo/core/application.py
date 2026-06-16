from .graph_registry import GraphRegistry
from ..events.event_bus import EventBus
from ..handlers.graph_handler import GraphHandler
from ..handlers.algorithm_handler import AlgorithmHandler
from ..handlers.metrics_handler import MetricsHandler
from ..handlers.mining_handler import MiningHandler

class Application:
    def __init__(self):
        self.registry = GraphRegistry()
        self.bus = EventBus()
        
        self.graph_handler = GraphHandler(self.registry)
        self.algo_handler = AlgorithmHandler(self.registry)
        self.metrics_handler = MetricsHandler(self.registry)
        self.mining_handler = MiningHandler(self.registry)
        
        self.graph_handler.register_all(self.bus)
        self.algo_handler.register_all(self.bus)
        self.metrics_handler.register_all(self.bus)
        self.mining_handler.register_all(self.bus)

    def get_bus(self) -> EventBus:
        return self.bus

    def get_registry(self) -> GraphRegistry:
        return self.registry
