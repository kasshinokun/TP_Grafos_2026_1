from collections import defaultdict

class EventBus:
    """
    Sistema de Pub/Sub usando apenas Python nativo, sem PyQt6.
    Garante que todas as micro-aplicações conversem na mesma instância (Singleton).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.subscribers = defaultdict(list)
        return cls._instance

    def subscribe(self, event_type, callback):
        self.subscribers[event_type].append(callback)

    def publish(self, event_type, payload=None):
        if payload is None:
            payload = {}
        print(f"[EventBus] Evento publicado: {event_type}")
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(event_type, payload)