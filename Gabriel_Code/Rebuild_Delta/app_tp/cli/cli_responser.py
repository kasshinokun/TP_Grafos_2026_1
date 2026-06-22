# ./cli/cli_responser.py
"""Lado de "entrada de volta" do CLI: formata um `EventResult` (ou uma
lista deles, quando múltiplos handlers estão inscritos no mesmo
evento) em texto legível para apresentação — pseudo-console da GUI ou
um terminal de fato.

Mesma filosofia de `gui/utils/test_formatting.py`: funções puras, sem
nenhum conhecimento de `tkinter`/widgets. Quem desenha na tela
(`gui/frames/api_primitiva.py`, ou um futuro terminal real) só chama
estas funções e injeta o texto resultante onde for apropriado.
"""
from typing import List

from event.event import EventResult


def format_result(result: EventResult) -> str:
    """Formata um único EventResult numa linha (ou poucas linhas) de
    saída, incluindo o tempo de execução para dar noção de custo —
    útil sobretudo para os comandos assíncronos (FLOYD_WARSHALL,
    BUILD_GRAPH_FROM_CSV, RUN_TESTS)."""
    icon = "✅" if result.success else "❌"
    header = (
        f"{icon} {result.event_type.value} "
        f"({result.duration_seconds:.3f}s, thread={result.handled_in_thread})"
    )
    if not result.success:
        return f"{header}\n   → erro: {result.error}"

    body = _format_data(result.data)
    return f"{header}\n{body}" if body else header


def format_results(results: List[EventResult]) -> str:
    """Formata uma lista de resultados (caso de múltiplos handlers
    inscritos para o mesmo EventType), um bloco por resultado. Lista
    vazia significa "despacho assíncrono, resultado ainda não chegou"
    — devolve uma mensagem explicando isso, em vez de uma string vazia
    que pareceria um bug silencioso."""
    if not results:
        return "⏳ Comando despachado de forma assíncrona — aguardando resultado."
    return "\n\n".join(format_result(r) for r in results)


def format_pending_notice(event_type_value: str) -> str:
    """Mensagem mostrada imediatamente após despachar um comando
    assíncrono, antes do polling trazer o resultado real — dá
    feedback imediato ao usuário do CLI de que o comando foi aceito e
    está em processamento."""
    return f"⏳ '{event_type_value}' está rodando em segundo plano..."


def _format_data(data) -> str:
    """Formata o payload de dados de um EventResult bem-sucedido.
    Dicionários são formatados como "chave: valor" linha a linha
    (achatando listas longas para não poluir o console); outros tipos
    usam repr direto."""
    if data is None:
        return ""
    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            lines.append(f"   • {key}: {_format_value(value)}")
        return "\n".join(lines)
    return f"   • {data}"


def _format_value(value, max_list_items: int = 10) -> str:
    if isinstance(value, list):
        if len(value) > max_list_items:
            shown = ", ".join(str(v) for v in value[:max_list_items])
            return f"[{shown}, ... mais {len(value) - max_list_items} item(ns)]"
        return str(value)
    if isinstance(value, str) and len(value) > 300:
        return value[:300] + "... (truncado)"
    return str(value)
