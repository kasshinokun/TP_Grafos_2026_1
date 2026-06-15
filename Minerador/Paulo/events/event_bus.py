import logging
from typing import Dict, List, Callable, Any
from .event_type import EventType
from .event import Event

class EventBus:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.handlers: Dict[EventType, List[Callable[[Event], None]]] = {}

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        if event_type in self.handlers:
            self.handlers[event_type].remove(handler)

    def publish(self, event: Event) -> Event:
        handlers = self.handlers.get(event.type, [])
        if not handlers:
            self.logger.warning(f"Nenhum handler registrado para: {event.type}")
            event.set_error(f"Nenhum handler para o evento: {event.type}")
            return event

        for handler in handlers:
            try:
                handler(event)
                if not event.success:
                    break
            except Exception as e:
                event.set_error(str(e))
                self.logger.error(f"Handler falhou para {event.type}: {str(e)}")
                break
        return event

    def dispatch(self, event_type: EventType) -> Event:
        return self.publish(Event(event_type))
