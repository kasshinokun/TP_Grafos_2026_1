# ./cli/cli_orchestrator.py
"""Fachada de alto nível do CLI — o que a GUI (ou um terminal real)
realmente chama.

Une as quatro peças do pipeline (`cli_interpreter` → `cli_cmd_validator`
→ `cli_requester` → `cli_responser`) num único método `execute(texto)
-> texto`, e mantém um `EventOrchestrator` (a fachada da EDA, em
`./event`) compartilhado entre comandos sucessivos, já que o estado de
runtime (grafo carregado) precisa persistir de um comando para o
próximo.

    texto digitado
        |
        v
    CliInterpreter.parse        - sintaxe: separa comando de argumentos
        |
        v
    CliCmdValidator.validate    - forma: comando existe? args corretos?
        |
        v
    CliRequester.send           - despacha no EventBus (via EventOrchestrator)
        |
        v
    cli_responser.format_*      - formata o EventResult de volta em texto
        |
        v
    texto de saida

Qualquer falha em qualquer estágio (parsing malformado, comando
desconhecido, argumento faltando, exceção dentro do handler de
domínio) é capturada e devolvida como texto de erro — `execute` nunca
lança exceção para quem o chamou; é seguro chamá-lo direto de um
callback de botão da GUI.
"""
from typing import Optional

from cli.cli_interpreter import CliInterpreter, ParseError
from cli.cli_cmd_validator import CliCmdValidator, ValidationError
from cli.cli_requester import CliRequester
from cli import cli_responser
from event.event_orchestrator import EventOrchestrator


class CliOrchestrator:
    """Ponto de entrada único do CLI. Uma instância é tipicamente
    criada uma vez por tela/sessão (ela guarda o `EventOrchestrator`,
    que guarda o grafo carregado em runtime)."""

    def __init__(self, orchestrator: Optional[EventOrchestrator] = None):
        self.event_orchestrator = orchestrator or EventOrchestrator()
        self.interpreter = CliInterpreter()
        self.validator = CliCmdValidator()
        self.requester = CliRequester(self.event_orchestrator)

    def execute(self, raw_text: str, source: str = "cli") -> str:
        """Executa uma linha de comando completa, do texto bruto ao
        texto de resposta formatado. Nunca lança exceção."""
        try:
            parsed = self.interpreter.parse(raw_text)
        except ParseError as ex:
            return f"❌ Erro de sintaxe: {ex}"

        try:
            validated = self.validator.validate(parsed)
        except ValidationError as ex:
            return f"❌ Comando inválido: {ex}"

        request = self.requester.build_request(validated, source=source)
        try:
            results = self.requester.send(request)
        except Exception as ex:
            # Salvaguarda final: mesmo uma falha totalmente inesperada
            # no despacho (não no handler — isso já é capturado dentro
            # do EventBus — mas algo na própria infraestrutura) não
            # deve propagar para quem chamou `execute`.
            return f"❌ Erro inesperado ao despachar o comando: {ex}"

        if not results:
            # Despacho assíncrono: o resultado real ainda vai chegar
            # via `self.event_orchestrator.poll()` — quem integra este
            # orchestrator com uma UI deve chamar `poll()`
            # periodicamente e usar `cli_responser.format_results` nos
            # itens recebidos.
            return cli_responser.format_pending_notice(validated.event_type.value)

        return cli_responser.format_results(results)

    def poll_async_results(self) -> str:
        """Drena resultados assíncronos pendentes (de comandos
        despachados anteriormente) e devolve o texto formatado, ou
        string vazia se nada estiver pronto ainda. Deve ser chamado
        periodicamente pela thread da UI (ex.: `widget.after(...)`),
        nunca de uma worker thread."""
        pending = self.event_orchestrator.poll()
        if not pending:
            return ""
        return cli_responser.format_results(pending)

    def help_text(self) -> str:
        """Texto de ajuda: lista todos os comandos disponíveis (todos
        os valores de EventType), para o usuário do CLI saber o que
        pode digitar."""
        from event.event_type import EventType
        lines = ["Comandos disponíveis:"]
        for event_type in EventType:
            lines.append(f"  • {event_type.value}")
        return "\n".join(lines)
