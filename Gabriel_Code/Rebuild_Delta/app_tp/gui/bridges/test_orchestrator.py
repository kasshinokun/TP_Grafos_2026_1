# ./gui/bridges/test_orchestrator.py
"""Bridge entre a suíte de testes do projeto (`./tests`) e a GUI de
Testes Unitários (`gui/frames/testes_unitarios.py`).

`TestOrchestrator` é a peça central: descobre as classes de teste de
cada módulo via introspecção nativa de `unittest` (sem reimplementar
nem duplicar a lógica de nenhum teste), organiza-as em categorias
(mapeamento semântico — "que assunto cada módulo testa" — que não dá
para inferir automaticamente do código, então é uma tabela estática
mantida aqui), e oferece um único ponto de entrada para executar
qualquer combinação (uma classe, ou "Todos" de uma categoria),
devolvendo um relatório pronto para a camada de apresentação
(`gui/utils/test_formatting.py`).

Um módulo (`tests/test_graphql_api.py`) usa pytest puro (fixtures
`@pytest.fixture`), incompatível com `unittest.TestLoader` — por isso
é tratado como uma categoria própria, executada via subprocess/`pytest.main`
quando disponível, e marcada como indisponível (com motivo explícito)
quando não estiver instalado no ambiente, em vez de quebrar a
descoberta das demais categorias.
"""
import importlib
import inspect
import io
import time
import unittest
from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from gui.utils.test_formatting import RunReport, TestCaseResult

# Disponibilidade de pytest precisa ser detectada já no carregamento
# do módulo (e não recalculada a cada execução), porque importlib
# fica fazendo cache de módulos parcialmente importados em caso de
# falha repetida — checar uma vez é suficiente e mais previsível.
try:
    import pytest  # noqa: F401
    _PYTEST_AVAILABLE = True
except ImportError:
    _PYTEST_AVAILABLE = False


ALL_CLASSES_LABEL = "Todos da categoria"


@dataclass(frozen=True)
class TestCategory:
    """Uma categoria exibida no primeiro combobox. `module_path` é o
    caminho de import (ex.: "tests.test_algorithms"); `uses_pytest`
    sinaliza módulos que não podem ser carregados via
    unittest.TestLoader."""
    key: str
    label: str
    module_path: str
    uses_pytest: bool = False


# Mapeamento estático categoria -> módulo. A ordem aqui é a ordem de
# exibição no primeiro combobox. Adicionar uma nova categoria no
# futuro é só adicionar uma linha nesta lista — o resto do
# orchestrator (descoberta de classes, execução, formatação) já
# funciona genericamente para qualquer módulo baseado em
# unittest.TestCase.
CATEGORIES: List[TestCategory] = [
    TestCategory("algorithms", "Algoritmos de grafos (BFS, DFS, Dijkstra...)", "tests.test_algorithms"),
    TestCategory("graph_api", "API primitiva do grafo (AbstractGraph)", "tests.test_graph_api"),
    TestCategory("structure", "Estrutura e heurísticas (matriz, lista, graus)", "tests.test_structure_extra"),
    TestCategory("metrics", "Métricas de redes complexas", "tests.test_metrics"),
    TestCategory("miner", "Mineração de dados (GitHub miner)", "tests.test_miner"),
    TestCategory("graphql_api", "API GraphQL do GitHub (requer pytest)", "tests.test_graphql_api", uses_pytest=True),
]


class TestOrchestrator:
    """Organiza, combina e executa os testes do projeto para a GUI.

    Uso típico:
        orch = TestOrchestrator()
        categories = orch.list_categories()                  # 1º combobox
        runs = orch.list_runs(categories[0].key)              # 2º combobox
        report = orch.run(categories[0].key, runs[0])         # botão "Rodar"
    """

    def __init__(self):
        self._class_cache: Dict[str, Dict[str, Type[unittest.TestCase]]] = {}

    # ------------------------------------------------------------------
    # Descoberta (alimenta os comboboxes)
    # ------------------------------------------------------------------

    def list_categories(self) -> List[TestCategory]:
        """Categorias disponíveis, na ordem fixa de `CATEGORIES`."""
        return list(CATEGORIES)

    def get_category(self, key: str) -> TestCategory:
        for cat in CATEGORIES:
            if cat.key == key:
                return cat
        raise KeyError(f"Categoria desconhecida: {key}")

    def list_runs(self, category_key: str) -> List[str]:
        """Lista as "execuções" disponíveis dentro de uma categoria:
        cada classe de teste descoberta no módulo, mais
        `ALL_CLASSES_LABEL` no topo para rodar todas de uma vez.

        Para a categoria baseada em pytest, não há classes
        unittest.TestCase para descobrir (o módulo nem chega a ser
        importado por aqui, pois isso já falharia sem pytest
        instalado) — a única opção listada é `ALL_CLASSES_LABEL`,
        que dispara a sessão pytest inteira do arquivo.
        """
        category = self.get_category(category_key)
        if category.uses_pytest:
            return [ALL_CLASSES_LABEL]

        classes = self._discover_classes(category)
        return [ALL_CLASSES_LABEL] + list(classes.keys())

    def _discover_classes(self, category: TestCategory) -> Dict[str, Type[unittest.TestCase]]:
        """Importa o módulo da categoria e extrai, por introspecção
        (`inspect.getmembers`), todas as classes que herdam de
        `unittest.TestCase` e foram *definidas* nesse módulo (exclui
        classes importadas de outro lugar, ex.: `unittest.TestCase`
        em si, caso apareça no namespace do módulo).

        Resultado é cacheado por categoria: o conjunto de classes de
        um módulo de teste não muda durante a vida do processo (não
        há hot-reload de código de teste nesta GUI), então recalcular
        a cada chamada só repetiria trabalho de import.
        """
        if category.key in self._class_cache:
            return self._class_cache[category.key]

        module = importlib.import_module(category.module_path)
        classes: Dict[str, Type[unittest.TestCase]] = {}
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, unittest.TestCase)
                    and obj is not unittest.TestCase
                    and obj.__module__ == category.module_path):
                classes[name] = obj

        # Ordena pela ordem de definição no arquivo fonte (mais
        # previsível para quem está lendo a GUI do que ordem
        # alfabética, que embaralharia a sequência didática do
        # arquivo original). `inspect.getsourcelines` pode falhar em
        # cenários sem acesso ao arquivo-fonte original (ex.: módulo
        # carregado dinamicamente, bytecode puro) — nesse caso, cai
        # para a ordem em que `inspect.getmembers` já devolveu
        # (alfabética), em vez de propagar a exceção e quebrar a
        # descoberta da categoria inteira.
        def _source_line(cls):
            try:
                return inspect.getsourcelines(cls)[1]
            except (OSError, TypeError):
                return float("inf")

        ordered = dict(sorted(classes.items(), key=lambda kv: _source_line(kv[1])))
        self._class_cache[category.key] = ordered
        return ordered

    def list_test_methods(self, category_key: str, run_label: str) -> List[str]:
        """Lista os métodos de teste individuais que uma execução
        (classe específica, ou "Todos da categoria") efetivamente
        contém — usado para popular a árvore de resultados ou
        apenas para exibir "o que vai ser rodado" antes de clicar em
        Rodar, se a GUI quiser mostrar isso."""
        category = self.get_category(category_key)
        if category.uses_pytest:
            return []  # descoberta de testes pytest fica a cargo do próprio pytest

        classes = self._discover_classes(category)
        if run_label == ALL_CLASSES_LABEL:
            target_classes = list(classes.values())
        else:
            target_classes = [classes[run_label]]

        loader = unittest.TestLoader()
        methods = []
        for cls in target_classes:
            for test in loader.loadTestsFromTestCase(cls):
                methods.append(test.id().split(".")[-1])
        return methods

    # ------------------------------------------------------------------
    # Execução (botão "Rodar testes")
    # ------------------------------------------------------------------

    def run(self, category_key: str, run_label: str) -> RunReport:
        """Executa a combinação (categoria, execução) e retorna um
        `RunReport` pronto para a camada de apresentação.

        Por trás, delega para `_run_unittest` ou `_run_pytest`
        dependendo de `category.uses_pytest` — o chamador (a GUI) não
        precisa saber qual executor foi usado."""
        category = self.get_category(category_key)
        if category.uses_pytest:
            return self._run_pytest(category)
        return self._run_unittest(category, run_label)

    def _run_unittest(self, category: TestCategory, run_label: str) -> RunReport:
        classes = self._discover_classes(category)

        if run_label == ALL_CLASSES_LABEL:
            target_classes = list(classes.values())
            label = category.label
        else:
            if run_label not in classes:
                raise KeyError(
                    f"Classe '{run_label}' não encontrada na categoria "
                    f"'{category.label}'."
                )
            target_classes = [classes[run_label]]
            label = run_label

        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        for cls in target_classes:
            suite.addTests(loader.loadTestsFromTestCase(cls))

        # IMPORTANTE: TextTestRunner.run() esvazia a TestSuite conforme
        # executa cada teste (libera referências internamente) — por
        # isso a lista de testes precisa ser capturada ANTES de rodar,
        # não depois. Iterar `suite` após `runner.run(suite)` retornaria
        # apenas `None`.
        ordered_tests = list(_iter_suite(suite))

        stream = io.StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        start = time.perf_counter()
        result = runner.run(suite)
        duration = time.perf_counter() - start

        case_results = self._build_case_results(result, ordered_tests)

        return RunReport(
            label=label,
            total=result.testsRun,
            passed=result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
            failed=len(result.failures),
            errors=len(result.errors),
            skipped=len(result.skipped),
            duration_seconds=duration,
            raw_output=stream.getvalue(),
            case_results=case_results,
        )

    @staticmethod
    def _build_case_results(result: unittest.TestResult, ordered_tests: List[unittest.TestCase]) -> List[TestCaseResult]:
        """Converte o resultado bruto do unittest (listas separadas de
        failures/errors/skipped, mais a contagem total) numa lista
        única de `TestCaseResult` — um item por teste que de fato
        rodou, na ordem original em que apareceram na suíte.

        Recebe `ordered_tests` (lista já achatada, capturada ANTES da
        execução) em vez da TestSuite, porque TextTestRunner.run()
        esvazia a suíte conforme executa cada teste."""
        failure_ids = {test.id(): msg for test, msg in result.failures}
        error_ids = {test.id(): msg for test, msg in result.errors}
        skipped_ids = {test.id(): reason for test, reason in result.skipped}

        cases = []
        for test in ordered_tests:
            test_id = test.id()
            short_id = ".".join(test_id.split(".")[-2:])  # Classe.metodo
            if test_id in failure_ids:
                cases.append(TestCaseResult(short_id, "failed", failure_ids[test_id]))
            elif test_id in error_ids:
                cases.append(TestCaseResult(short_id, "error", error_ids[test_id]))
            elif test_id in skipped_ids:
                cases.append(TestCaseResult(short_id, "skipped", skipped_ids[test_id]))
            else:
                cases.append(TestCaseResult(short_id, "passed"))
        return cases

    def _run_pytest(self, category: TestCategory) -> RunReport:
        """Executa o módulo pytest da categoria via `pytest.main`,
        capturando a saída. Se pytest não estiver instalado, retorna
        um RunReport marcado como indisponível em vez de lançar
        exceção — a GUI deve exibir isso de forma amigável, não
        travar."""
        if not _PYTEST_AVAILABLE:
            return RunReport(
                label=category.label,
                total=0, passed=0, failed=0, errors=0, skipped=0,
                duration_seconds=0.0, raw_output="", case_results=[],
                unavailable_reason=(
                    "o pacote 'pytest' não está instalado neste ambiente. "
                    "Instale com 'pip install pytest' para habilitar esta categoria."
                ),
            )

        # Import local: só precisa existir de fato quando pytest está
        # instalado (o bloco try/except no topo do módulo já cobre a
        # ausência; aqui só reaproveitamos a referência já validada).
        import pytest as _pytest

        module_file = category.module_path.replace(".", "/") + ".py"

        stream = io.StringIO()
        start = time.perf_counter()
        try:
            # `-p no:cacheprovider` evita escrever .pytest_cache no
            # projeto a cada execução disparada pela GUI.
            _pytest.main(
                [module_file, "-v", "-p", "no:cacheprovider"],
                plugins=[_CapturePlugin(stream)],
            )
        except Exception as ex:
            # A API de plugins/hooks do pytest pode variar entre
            # versões instaladas no ambiente do usuário — se a
            # integração com o plugin falhar por incompatibilidade,
            # o relatório deve indicar isso claramente em vez de
            # propagar a exceção e travar a GUI.
            duration = time.perf_counter() - start
            return RunReport(
                label=category.label,
                total=0, passed=0, failed=0, errors=0, skipped=0,
                duration_seconds=duration, raw_output=stream.getvalue(),
                case_results=[],
                unavailable_reason=(
                    f"falha ao executar via pytest (possível incompatibilidade "
                    f"de versão do plugin de captura): {ex}"
                ),
            )
        duration = time.perf_counter() - start
        raw_output = stream.getvalue()

        total, passed, failed, errors, skipped, case_results = _parse_pytest_output(raw_output)

        return RunReport(
            label=category.label,
            total=total, passed=passed, failed=failed, errors=errors, skipped=skipped,
            duration_seconds=duration, raw_output=raw_output,
            case_results=case_results,
        )


def _iter_suite(suite: unittest.TestSuite):
    """Achata um TestSuite (que pode conter outras suítes aninhadas)
    numa sequência plana de TestCase, na ordem original."""
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from _iter_suite(item)
        else:
            yield item


class _CapturePlugin:
    """Plugin mínimo de pytest que apenas espelha a saída do terminal
    para um stream em memória, para podermos exibi-la no pseudo-console
    sem depender de redirecionar sys.stdout globalmente (o que poderia
    interferir em saída de outras partes da GUI rodando na mesma
    sessão)."""
    def __init__(self, stream: io.StringIO):
        self._stream = stream

    def pytest_runtest_logreport(self, report):
        if report.when == "call" or (report.when == "setup" and report.skipped):
            outcome = report.outcome
            self._stream.write(f"{report.nodeid} {outcome.upper()}\n")
            if report.failed and report.longrepr:
                self._stream.write(f"{report.longreprtext}\n")

    def pytest_terminal_summary(self, terminalreporter):
        stats = terminalreporter.stats
        for key in ("passed", "failed", "error", "skipped"):
            count = len(stats.get(key, []))
            if count:
                self._stream.write(f"{key}: {count}\n")


def _parse_pytest_output(raw_output: str):
    """Extrai contagens agregadas e uma lista de TestCaseResult a
    partir do texto produzido por `_CapturePlugin`. Parsing simples
    baseado no formato fixo que o próprio plugin escreve (não tenta
    interpretar a saída padrão do pytest, que é mais livre de
    formato)."""
    case_results: List[TestCaseResult] = []
    passed = failed = errors = skipped = 0

    for line in raw_output.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[1] in ("PASSED", "FAILED", "SKIPPED"):
            node_id, outcome_word = parts
            outcome = {"PASSED": "passed", "FAILED": "failed", "SKIPPED": "skipped"}[outcome_word]
            short_id = node_id.split("::")[-1]
            case_results.append(TestCaseResult(short_id, outcome))
            if outcome == "passed":
                passed += 1
            elif outcome == "failed":
                failed += 1
            elif outcome == "skipped":
                skipped += 1

    total = passed + failed + errors + skipped
    return total, passed, failed, errors, skipped, case_results
