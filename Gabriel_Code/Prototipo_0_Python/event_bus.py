from PyQt6.QtCore import QObject, pyqtSignal

class EventBus(QObject):
    """
    O EventBus é o mediador central da arquitetura baseada em eventos.
    Ele permite que micro-aplicações se comuniquem sem acoplamento direto.
    """
    # Sinal genérico para eventos: (event_type, payload)
    event_signal = pyqtSignal(str, dict)

    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def publish(self, event_type: str, payload: dict = None):
        if payload is None:
            payload = {}
        print(f"[EventBus] Publicando: {event_type} com payload: {payload}")
        self.event_signal.emit(event_type, payload)

    def subscribe(self, callback):
        self.event_signal.connect(callback)
