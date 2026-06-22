# ./event/event_bus.py
"""Barramento de eventos (publish/subscribe) — o coração da EDA.

Modelo híbrido, conforme decidido para este projeto: despacho é
SÍNCRONO por padrão (o handler roda na própria thread que chamou
`dispatch`, e o `EventResult` volta como valor de retorno comum) — mas
qualquer chamada pode pedir execução ASSÍNCRONA (`async_=True`), que
roda o handler em uma `threading.Thread` separada e entrega o
`EventResult` futuramente através de uma `queue.Queue`, no mesmo
padrão já usado por `gui/workers.py` (`GraphWorker` + polling via
`after()`).

Por que híbrido, e não sempre uma coisa só:
- Handlers rápidos (validar um vértice, formatar um resumo, BFS em um
  grafo de algumas centenas de nós) ganham nada com assincronia além
  de complexidade — síncrono é mais simples de seguir e de testar.
- Handlers potencialmente lentos (Floyd-Warshall em grafo grande,
  mineração de dados via rede, a suíte de testes inteira) bloqueariam
  a interface Tkinter se rodassem na thread da GUI — para esses,
  `async_=True` é o que evita a tela congelar.

Threads em Tkinter: widgets só podem ser tocados pela thread principal
(Tkinter não é thread-safe). Por isso o EventBus NUNCA chama
diretamente um callback de UI a partir da worker thread — o resultado
assíncrono só é colocado em uma `queue.Queue`; é responsabilidade de
quem está do lado da GUI (ver `EventOrchestrator.poll`) drenar essa
fila a partir da thread principal, via `widget.after(...)`.
"""
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from event.event import Event, EventResult
from event.event_type import EventType

Handler = Callable[[Event], object]  # recebe o Event, devolve o "data" do EventResult


@dataclass
class _Subscription:
    handler: Handler
    default_async: bool = False


class EventBus:
    """Registra handlers por `EventType` e despacha eventos para eles.

    Um mesmo `EventType` pode ter múltiplos handlers inscritos (todos
    são chamados, na ordem de inscrição); `dispatch` retorna a lista
    de `EventResult`, um por handler síncrono. Isso permite, por
    exemplo, um handler "de negócio" (rodar o BFS) e um handler "de
    auditoria" (logar que o comando foi executado) inscritos para o
    mesmo evento, sem que um precise saber do outro.
    """

    def __init__(self):
        self._subscriptions: Dict[EventType, List[_Subscription]] = {}
        self._result_queue: "queue.Queue[EventResult]" = queue.Queue()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Inscrição
    # ------------------------------------------------------------------

    def subscribe(self, event_type: EventType, handler: Handler, default_async: bool = False) -> None:
        """Registra `handler` para `event_type`. `default_async`
        define o comportamento quando `dispatch` é chamado sem
        especificar `async_` explicitamente para este evento."""
        with self._lock:
            self._subscriptions.setdefault(event_type, []).append(
                _Subscription(handler=handler, default_async=default_async)
            )

    def unsubscribe(self, event_type: EventType, handler: Handler) -> bool:
        """Remove um handler específico. Retorna True se algo foi
        removido — útil em testes, para não deixar handlers de um
        teste "vazando" para o próximo."""
        with self._lock:
            subs = self._subscriptions.get(event_type, [])
            before = len(subs)
            self._subscriptions[event_type] = [s for s in subs if s.handler is not handler]
            return len(self._subscriptions[event_type]) != before

    def has_subscribers(self, event_type: EventType) -> bool:
        return bool(self._subscriptions.get(event_type))

    # ------------------------------------------------------------------
    # Despacho
    # ------------------------------------------------------------------

    def dispatch(self, event: Event, async_: Optional[bool] = None) -> List[EventResult]:
        """Despacha `event` para todos os handlers inscritos no seu
        `event_type`.

        - Se `async_` for None (padrão), cada handler usa o
          `default_async` definido na própria inscrição.
        - Se `async_` for True/False explicitamente, isso força o modo
          para TODOS os handlers deste despacho específico,
          independente do que foi definido na inscrição.

        Handlers síncronos têm seu `EventResult` incluído na lista
        retornada por esta chamada. Handlers assíncronos NÃO aparecem
        na lista de retorno (o resultado ainda não existe nesse
        momento) — eles chegam depois, via `pop_results()`.
        """
        subs = self._subscriptions.get(event.event_type, [])
        if not subs:
            return [EventResult.fail(
                event,
                f"Nenhum handler registrado para '{event.event_type.value}'.",
            )]

        results = []
        for sub in subs:
            run_async = sub.default_async if async_ is None else async_
            if run_async:
                self._dispatch_async(event, sub.handler)
            else:
                results.append(self._dispatch_sync(event, sub.handler))
        return results

    def _dispatch_sync(self, event: Event, handler: Handler) -> EventResult:
        start = time.perf_counter()
        try:
            data = handler(event)
            return EventResult.ok(event, data, time.perf_counter() - start)
        except Exception as ex:
            return EventResult.fail(event, str(ex), time.perf_counter() - start)

    def _dispatch_async(self, event: Event, handler: Handler) -> threading.Thread:
        def _run():
            result = self._dispatch_sync(event, handler)
            self._result_queue.put(result)

        thread = threading.Thread(
            target=_run,
            name=f"EventBus-{event.event_type.value}-{event.event_id[:8]}",
            daemon=True,
        )
        thread.start()
        return thread

    # ------------------------------------------------------------------
    # Drenagem de resultados assíncronos (chamado pela thread da GUI)
    # ------------------------------------------------------------------

    def pop_results(self) -> List[EventResult]:
        """Retira e devolve todos os `EventResult` assíncronos
        disponíveis até este momento, sem bloquear. Deve ser chamado
        periodicamente pela thread principal (ex.: dentro de um
        `widget.after(...)`) — nunca de uma worker thread, já que
        normalmente o chamador vai usar o resultado para atualizar a
        UI."""
        drained = []
        while True:
            try:
                drained.append(self._result_queue.get_nowait())
            except queue.Empty:
                break
        return drained
