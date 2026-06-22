# ./cli/cli_requester.py
"""Lado de "saída" do CLI: pega um `ValidatedCommand` (já garantido
sintática e estruturalmente correto pelo `cli_cmd_validator.py`) e o
entrega à arquitetura EDA (`event.event_orchestrator.EventOrchestrator`)
como uma requisição formal.

Separar isto de `cli_validator`/`cli_interpreter` existe para que o
CLI tenha um ponto único de acoplamento com o EventOrchestrator — se
no futuro o CLI precisar, por exemplo, anexar metadados de auditoria
(quem disparou o comando, de qual sessão) ou decidir dinamicamente se
um comando deve rodar síncrono ou assíncrono, é aqui que essa decisão
mora, sem misturar com a lógica de parsing ou validação.
"""
import uuid
from dataclasses import dataclass
from typing import List, Optional

from cli.cli_cmd_validator import ValidatedCommand
from event.event import EventResult
from event.event_orchestrator import EventOrchestrator


@dataclass
class CommandRequest:
    """Requisição formal — o que de fato cruza a fronteira entre "CLI"
    e "EDA". Guardamos `request_id` próprio (diferente do `event_id`
    gerado dentro do Event) para que múltiplas camadas de log possam
    correlacionar "isto veio da requisição X do CLI" independente de
    como o EventOrchestrator decidiu nomear o Event internamente."""
    request_id: str
    validated: ValidatedCommand
    source: str = "cli"


class CliRequester:
    """Constrói `CommandRequest` a partir de comandos validados, e os
    despacha através de um `EventOrchestrator` compartilhado.

    Uma instância de `CliRequester` é tipicamente de longa duração
    (criada uma vez, reaproveitada a cada comando digitado) porque o
    `EventOrchestrator` carrega estado de runtime (o grafo carregado)
    que precisa persistir entre comandos.
    """

    def __init__(self, orchestrator: EventOrchestrator):
        self.orchestrator = orchestrator

    def build_request(self, validated: ValidatedCommand, source: str = "cli") -> CommandRequest:
        return CommandRequest(
            request_id=uuid.uuid4().hex,
            validated=validated,
            source=source,
        )

    def send(self, request: CommandRequest, async_: Optional[bool] = None) -> List[EventResult]:
        """Despacha a requisição no EventOrchestrator e devolve a
        lista de `EventResult` (vazia se o despacho for assíncrono —
        ver `EventBus.dispatch`/`EventOrchestrator.poll`)."""
        return self.orchestrator.dispatch(
            request.validated.event_type,
            request.validated.payload,
            source=request.source,
            async_=async_,
        )
