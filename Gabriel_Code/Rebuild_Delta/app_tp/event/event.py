# ./event/event.py
"""Estrutura de dados que circula no EventBus.

`Event` é deliberadamente "burro": carrega dados, não comportamento.
Quem decide o que fazer com um evento é o handler registrado no
`EventBus` para o `EventType` correspondente — o Event em si não sabe
nada sobre grafos, testes ou CLI.

`EventResult` é o que volta depois do despacho — sucesso/erro/dados,
mais o tempo de execução (útil tanto para depuração quanto para o CLI
mostrar "rodou em Xs", no mesmo espírito de
`gui/utils/test_formatting.RunReport`).
"""
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from event.event_type import EventType


@dataclass(frozen=True)
class Event:
    """Um evento/comando único, com payload livre (dict) — o handler
    registrado para `event_type` é quem sabe interpretar as chaves
    esperadas em `payload`.

    `event_id` é gerado automaticamente (UUID4) e serve para casar um
    `Event` com seu `EventResult` quando o despacho é assíncrono (o
    resultado pode chegar bem depois, em outra thread, então não dá
    para confiar só na ordem de chegada na fila).

    `source` identifica quem originou o evento (ex.: "gui:api_primitiva",
    "cli:terminal") — não é usado para nenhuma lógica de roteamento,
    apenas para depuração/log; o roteamento depende só de `event_type`.
    """
    event_type: EventType
    payload: dict = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    created_at: float = field(default_factory=time.monotonic)
    source: str = "unknown"

    def get(self, key: str, default: Any = None) -> Any:
        """Acesso conveniente a uma chave do payload, sem o chamador
        precisar escrever `event.payload.get(...)` repetidamente."""
        return self.payload.get(key, default)

    def require(self, key: str) -> Any:
        """Como `get`, mas levanta KeyError com mensagem clara se a
        chave obrigatória não estiver presente — usado por handlers
        que não têm um valor padrão sensato (ex.: "source" de um BFS:
        não existe origem padrão razoável)."""
        if key not in self.payload:
            raise KeyError(
                f"Evento '{self.event_type.value}' requer a chave "
                f"'{key}' no payload, mas ela não foi fornecida."
            )
        return self.payload[key]


@dataclass
class EventResult:
    """Resultado do despacho de um Event — sempre devolvido pelo
    EventBus, nunca lançado como exceção crua para quem chamou
    `dispatch()` (o EventBus captura exceções de handlers e as
    converte em EventResult com success=False, error=<mensagem>)."""
    event_id: str
    event_type: EventType
    success: bool
    data: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    handled_in_thread: str = field(default_factory=lambda: threading.current_thread().name)

    @classmethod
    def ok(cls, event: Event, data: Any, duration_seconds: float) -> "EventResult":
        return cls(
            event_id=event.event_id,
            event_type=event.event_type,
            success=True,
            data=data,
            duration_seconds=duration_seconds,
        )

    @classmethod
    def fail(cls, event: Event, error: str, duration_seconds: float = 0.0) -> "EventResult":
        return cls(
            event_id=event.event_id,
            event_type=event.event_type,
            success=False,
            error=error,
            duration_seconds=duration_seconds,
        )
