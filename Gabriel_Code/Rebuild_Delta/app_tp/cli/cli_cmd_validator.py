# ./cli/cli_cmd_validator.py
"""Validador de comandos do CLI.

Recebe um `ParsedCommand` (saída de `cli_interpreter.py`) e confere:

1. O token de comando resolve para um `EventType` válido (usando
   `EventType.from_value`, que já cobre os aliases curtos).
2. Os argumentos obrigatórios de cada comando estão presentes.
3. Não sobrou nenhum argumento desconhecido (proteção contra erro de
   digitação silenciosa: `bfs sorce=0` deveria ser rejeitado, não
   silenciosamente interpretado como "sem origem").

Esta é a "primeira linha de defesa" antes de qualquer coisa ser
despachada para o EventBus — um comando que passa pelo validador tem
garantia de virar um `Event` bem formado; um comando que falha aqui
nunca chega a tocar `EventOrchestrator`/`EventBus`.

Deliberadamente não faz nenhuma validação *semântica* mais profunda
(ex.: "este índice de vértice existe no grafo carregado?") — isso
exigiria acesso ao estado do grafo, que é responsabilidade do handler
em `EventOrchestrator`. O validador só confere a *forma* do comando,
não seu significado.
"""
from dataclasses import dataclass
from typing import Any, Dict, FrozenSet

from event.event_type import EventType
from cli.cli_interpreter import ParsedCommand


@dataclass(frozen=True)
class CommandSpec:
    """Assinatura esperada de um comando: quais chaves são
    obrigatórias e quais são opcionais. Qualquer chave fora dessas
    duas listas é considerada erro de digitação."""
    required: FrozenSet[str] = frozenset()
    optional: FrozenSet[str] = frozenset()

    @property
    def allowed(self) -> FrozenSet[str]:
        return self.required | self.optional


# Especificação de argumentos por EventType. Comandos não listados
# aqui são tratados como "sem argumentos esperados" (required vazio,
# optional vazio) — qualquer kwarg viraria erro de "argumento
# desconhecido", o que é o comportamento correto para, por exemplo,
# HELP ou UNLOAD_GRAPH.
_SPECS: Dict[EventType, CommandSpec] = {
    EventType.LOAD_GRAPH: CommandSpec(required=frozenset({"filename"})),
    EventType.SAVE_GRAPH: CommandSpec(optional=frozenset({"filename"})),
    EventType.BUILD_GRAPH_FROM_CSV: CommandSpec(required=frozenset({"filename"})),

    EventType.RUN_BFS: CommandSpec(required=frozenset({"source"}), optional=frozenset({"target"})),
    EventType.RUN_DFS: CommandSpec(required=frozenset({"source"}), optional=frozenset({"target"})),
    EventType.RUN_DIJKSTRA: CommandSpec(required=frozenset({"source"})),
    EventType.RUN_BELLMAN_FORD: CommandSpec(required=frozenset({"source"})),
    EventType.RUN_PRIM: CommandSpec(optional=frozenset({"source"})),
    EventType.RUN_FORD_FULKERSON: CommandSpec(required=frozenset({"source", "sink"})),
    EventType.RUN_EDMONDS_KARP: CommandSpec(required=frozenset({"source", "sink"})),

    EventType.LIST_TEST_RUNS: CommandSpec(required=frozenset({"category"})),
    EventType.RUN_TESTS: CommandSpec(required=frozenset({"category"}), optional=frozenset({"run"})),

    EventType.ECHO: CommandSpec(optional=frozenset({"text"})),
}

_EMPTY_SPEC = CommandSpec()


class ValidationError(Exception):
    """Comando sintaticamente parseável, mas semanticamente inválido
    para o CLI (comando desconhecido, argumento obrigatório faltando,
    ou argumento desconhecido)."""


@dataclass
class ValidatedCommand:
    """Saída do validador — um comando que já sabemos que pode ser
    despachado com segurança."""
    event_type: EventType
    payload: Dict[str, Any]
    raw_text: str


class CliCmdValidator:
    """Sem estado — assim como o interpretador, pode ser reutilizado
    livremente entre chamadas/threads."""

    def validate(self, parsed: ParsedCommand) -> ValidatedCommand:
        event_type = self._resolve_event_type(parsed.command_token)
        spec = _SPECS.get(event_type, _EMPTY_SPEC)

        missing = spec.required - parsed.kwargs.keys()
        unknown = parsed.kwargs.keys() - spec.allowed

        if missing or unknown:
            problems = []
            if missing:
                problems.append(f"faltando argumento(s) obrigatório(s): {', '.join(sorted(missing))}")
            if unknown:
                problems.append(
                    f"argumento(s) desconhecido(s): {', '.join(sorted(unknown))} "
                    f"(aceitos: {', '.join(sorted(spec.allowed)) or '(nenhum)'})"
                )
            raise ValidationError(
                f"Comando '{parsed.command_token}' inválido — " + "; ".join(problems) + "."
            )

        return ValidatedCommand(
            event_type=event_type,
            payload=dict(parsed.kwargs),
            raw_text=parsed.raw_text,
        )

    @staticmethod
    def _resolve_event_type(command_token: str) -> EventType:
        try:
            return EventType.from_value(command_token)
        except ValueError as ex:
            raise ValidationError(str(ex)) from ex
