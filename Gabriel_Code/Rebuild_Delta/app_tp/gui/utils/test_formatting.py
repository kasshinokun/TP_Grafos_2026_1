# ./gui/utils/test_formatting.py
"""Funções utilitárias puras para apresentar resultados de testes no
pseudo-console da GUI de Testes Unitários (`gui/frames/testes_unitarios.py`).

Este módulo não sabe nada sobre `unittest`/`pytest` nem sobre como os
testes são descobertos ou executados — isso é responsabilidade do
bridge (`gui/bridges/test_orchestrator.py`). Aqui só há formatação de
texto e pequenos cálculos sobre números já prontos (contagens, tempos),
o que torna estas funções fáceis de testar isoladamente e reutilizáveis
por qualquer outra tela que precise apresentar um resumo de execução.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TestCaseResult:
    """Resultado de um único método de teste, já resolvido (sem
    depender de objetos do unittest) — o bridge converte para isto
    antes de entregar à camada de apresentação."""
    test_id: str          # ex.: "TestBFS.test_bfs_complete_graph"
    outcome: str          # "passed" | "failed" | "error" | "skipped"
    message: str = ""     # mensagem curta de falha/erro (se houver)


@dataclass
class RunReport:
    """Resumo agregado de uma execução (de uma classe, de uma
    categoria inteira, ou de "Todos")."""
    label: str                       # nome da execução (ex.: "TestBFS")
    total: int
    passed: int
    failed: int
    errors: int
    skipped: int
    duration_seconds: float
    raw_output: str                  # saída textual completa do runner
    case_results: List[TestCaseResult]
    unavailable_reason: Optional[str] = None  # ex.: pytest não instalado

    @property
    def success(self) -> bool:
        return self.unavailable_reason is None and self.failed == 0 and self.errors == 0

    @property
    def status_icon(self) -> str:
        if self.unavailable_reason:
            return "⚠️"
        return "✅" if self.success else "❌"


def format_run_header(report: RunReport) -> str:
    """Cabeçalho curto de uma execução, para a primeira linha do
    pseudo-console (resumo rápido antes do log detalhado)."""
    if report.unavailable_reason:
        return f"⚠️ {report.label}: indisponível — {report.unavailable_reason}"

    return (
        f"{report.status_icon} {report.label}: "
        f"{report.passed}/{report.total} passou "
        f"({report.failed} falha(s), {report.errors} erro(s), "
        f"{report.skipped} pulado(s)) em {report.duration_seconds:.3f}s"
    )


def format_case_line(case: TestCaseResult) -> str:
    """Uma linha por teste individual, com ícone de status."""
    icons = {"passed": "✓", "failed": "✗", "error": "‼", "skipped": "○"}
    icon = icons.get(case.outcome, "?")
    line = f"   {icon} {case.test_id}"
    if case.message:
        # A primeira linha de uma falha/erro do unittest é sempre
        # "Traceback (most recent call last):" — pouco informativa
        # por si só. A linha mais útil para um resumo de uma linha é
        # tipicamente a última não vazia (a mensagem de
        # AssertionError ou da exceção levantada). O traceback
        # completo continua disponível em report.raw_output.
        msg_lines = [l.strip() for l in case.message.splitlines() if l.strip()]
        useful_line = next(
            (l for l in reversed(msg_lines) if not l.startswith("Traceback")),
            None,
        )
        if useful_line:
            line += f"\n        → {useful_line}"
    return line


def format_full_report(report: RunReport, show_raw_output: bool = True) -> str:
    """Monta o texto completo a ser inserido no pseudo-console: cabeçalho
    + lista de casos + (opcionalmente) a saída bruta do runner, que
    contém os tracebacks completos de falhas/erros."""
    lines = [format_run_header(report)]

    if report.unavailable_reason:
        return "\n".join(lines)

    if report.case_results:
        lines.append("")
        for case in report.case_results:
            lines.append(format_case_line(case))

    if show_raw_output and report.raw_output.strip():
        lines.append("")
        lines.append("— Saída do executor —")
        lines.append(report.raw_output.rstrip())

    return "\n".join(lines)


def format_category_summary(reports: List[RunReport]) -> str:
    """Quando "Todos" de uma categoria é executado, várias classes
    geram um RunReport cada — esta função resume o conjunto antes dos
    relatórios individuais."""
    available = [r for r in reports if r.unavailable_reason is None]
    total = sum(r.total for r in available)
    passed = sum(r.passed for r in available)
    failed = sum(r.failed for r in available)
    errors = sum(r.errors for r in available)
    skipped = sum(r.skipped for r in available)
    duration = sum(r.duration_seconds for r in available)
    unavailable = [r for r in reports if r.unavailable_reason is not None]

    icon = "✅" if (failed == 0 and errors == 0 and not unavailable) else (
        "⚠️" if (failed == 0 and errors == 0) else "❌"
    )
    lines = [
        f"{icon} Resumo da categoria: {passed}/{total} passou "
        f"({failed} falha(s), {errors} erro(s), {skipped} pulado(s)) "
        f"em {duration:.3f}s"
    ]
    for r in unavailable:
        lines.append(f"   ⚠️ {r.label}: indisponível — {r.unavailable_reason}")
    return "\n".join(lines)
