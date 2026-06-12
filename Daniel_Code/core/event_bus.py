# core/event_bus.py
from collections import defaultdict

class EventBus:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.subscribers = defaultdict(list)
        return cls._instance

    def subscribe(self, event_type, callback):
        """Registra uma função (callback) para escutar um evento específico."""
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, payload=None):
        """Dispara um evento, chamando todas as funções registradas para ele."""
        if payload is None:
            payload = {}
        print(f"[EventBus] Evento publicado: {event_type}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(event_type, payload)