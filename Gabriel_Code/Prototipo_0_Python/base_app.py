from core.event_bus import EventBus

class MicroApp:
    """
    Classe base para todas as micro-aplicações.
    Cada micro-app tem acesso ao EventBus para enviar e receber mensagens.
    """
    def __init__(self, name: str):
        self.name = name
        self.bus = EventBus.instance()
        self.bus.subscribe(self._handle_event)

    def _handle_event(self, event_type: str, payload: dict):
        # Método a ser sobrescrito pelas subclasses
        pass

    def send_request(self, method: str, endpoint: str, data: dict = None):
        """
        Simula uma requisição HTTP (GET/POST) via eventos.
        """
        event_type = f"API_{method}_{endpoint}"
        self.bus.publish(event_type, data)
