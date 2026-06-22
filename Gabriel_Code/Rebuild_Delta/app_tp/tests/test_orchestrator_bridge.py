"""Testes para a infraestrutura de suporte à GUI de Testes Unitários:

- gui.bridges.test_orchestrator.TestOrchestrator: descoberta de
  categorias/execuções e execução de testes via unittest/pytest.
- gui.utils.test_formatting: formatação de RunReport para texto.

Não testa o *conteúdo* dos módulos de teste do projeto (isso já é
coberto por test_algorithms.py, test_metrics.py etc.) — testa que o
bridge consegue descobri-los, organizá-los e executá-los corretamente,
e que a formatação produz texto consistente com os números do relatório.
"""
import sys
import types
import unittest

from gui.bridges.test_orchestrator import (
    TestOrchestrator,
    TestCategory,
    ALL_CLASSES_LABEL,
    CATEGORIES,
)
from gui.utils.test_formatting import (
    RunReport,
    TestCaseResult,
    format_run_header,
    format_case_line,
    format_full_report,
    format_category_summary,
)


def _register_fake_module(module_name: str, source_code: str):
    """Cria e registra em sys.modules um módulo de teste sintético, a
    partir de código-fonte real (via exec/compile), simulando um
    arquivo .py de teste genuíno — necessário para exercitar
    cenários de falha/erro sem precisar quebrar um teste real do
    projeto. Usar `exec(compile(...))` (em vez de só atribuir classes
    a um módulo vazio) garante que `__module__`/`inspect.getsourcelines`
    se comportem como em um arquivo .py de verdade."""
    module = types.ModuleType(module_name)
    module.__file__ = f"<fake:{module_name}>"
    exec(compile(source_code, module.__file__, "exec"), module.__dict__)
    sys.modules[module_name] = module
    return module


_FAKE_MODULE_NAME = "tests.test_fake_for_orchestrator_validation"
_FAKE_SOURCE = """
import unittest

class TestFakeFirst(unittest.TestCase):
    def test_passes(self):
        self.assertEqual(1, 1)

    def test_fails(self):
        self.assertEqual(1, 2, "um não é igual a dois")

class TestFakeSecond(unittest.TestCase):
    def test_errors(self):
        raise RuntimeError("erro de propósito")

    def test_skips(self):
        self.skipTest("pulado de propósito")
"""


class OrchestratorTestCaseBase(unittest.TestCase):
    """Registra a categoria/módulo fake uma única vez para toda a
    classe de teste (setUpClass), e remove no tearDownClass — evita
    poluir CATEGORIES/sys.modules para o resto da suíte do projeto
    quando estes testes rodam junto com os demais."""

    @classmethod
    def setUpClass(cls):
        _register_fake_module(_FAKE_MODULE_NAME, _FAKE_SOURCE)
        cls.fake_category = TestCategory(
            "fake_for_tests", "Categoria de validação (fake)", _FAKE_MODULE_NAME
        )
        CATEGORIES.append(cls.fake_category)

    @classmethod
    def tearDownClass(cls):
        if cls.fake_category in CATEGORIES:
            CATEGORIES.remove(cls.fake_category)
        sys.modules.pop(_FAKE_MODULE_NAME, None)

    def setUp(self):
        self.orch = TestOrchestrator()


class TestCategoryDiscovery(unittest.TestCase):
    """Categorias reais do projeto — confere que a lista estática
    bate com os módulos reais em ./tests e que cada um é importável."""

    def setUp(self):
        self.orch = TestOrchestrator()

    def test_all_real_categories_listed(self):
        categories = self.orch.list_categories()
        keys = {c.key for c in categories}
        self.assertEqual(
            keys,
            {"algorithms", "graph_api", "structure", "metrics", "miner", "graphql_api"},
        )

    def test_get_category_unknown_key_raises(self):
        with self.assertRaises(KeyError):
            self.orch.get_category("categoria_inexistente")

    def test_non_pytest_categories_list_classes(self):
        """Toda categoria não-pytest deve listar 'Todos da categoria'
        seguido de ao menos uma classe real."""
        for cat in self.orch.list_categories():
            if cat.uses_pytest:
                continue
            runs = self.orch.list_runs(cat.key)
            self.assertEqual(runs[0], ALL_CLASSES_LABEL)
            self.assertGreater(len(runs), 1, f"{cat.key} deveria ter ao menos uma classe")

    def test_pytest_category_lists_only_all(self):
        runs = self.orch.list_runs("graphql_api")
        self.assertEqual(runs, [ALL_CLASSES_LABEL])


class TestRunningRealCategories(unittest.TestCase):
    """Executa as categorias reais (não-pytest) e confere que os
    totais batem com o que se espera (mesmos números já confirmados
    rodando a suíte via `python -m unittest` diretamente)."""

    def setUp(self):
        self.orch = TestOrchestrator()

    def test_total_tests_across_categories_matches_suite(self):
        expected_totals = {
            "algorithms": 12,
            "graph_api": 13,
            "structure": 23,
            "metrics": 18,
            "miner": 9,
        }
        for key, expected in expected_totals.items():
            report = self.orch.run(key, ALL_CLASSES_LABEL)
            self.assertEqual(report.total, expected, f"categoria '{key}'")
            self.assertTrue(report.success, f"categoria '{key}' deveria passar 100%")

    def test_running_single_class_subset_of_category(self):
        """Rodar uma classe específica deve produzir um total menor
        ou igual ao de 'Todos da categoria' (nunca maior)."""
        report_all = self.orch.run("algorithms", ALL_CLASSES_LABEL)
        report_one = self.orch.run("algorithms", "TestBFS")
        self.assertLessEqual(report_one.total, report_all.total)
        self.assertEqual(report_one.total, 3)

    def test_unknown_run_label_raises(self):
        with self.assertRaises(KeyError):
            self.orch.run("algorithms", "ClasseQueNaoExiste")

    def test_pytest_category_without_pytest_is_marked_unavailable(self):
        """Neste ambiente de validação não há pytest instalado — o
        relatório deve vir marcado como indisponível, nunca lançar
        exceção. Se pytest estiver instalado no ambiente que rodar
        este teste, ainda assim o relatório deve ser bem formado
        (success ligado ao resultado real, sem unavailable_reason)."""
        report = self.orch.run("graphql_api", ALL_CLASSES_LABEL)
        try:
            import pytest  # noqa: F401
            self.assertIsNone(report.unavailable_reason)
        except ImportError:
            self.assertIsNotNone(report.unavailable_reason)
            self.assertFalse(report.success)


class TestRunningFakeCategoryWithFailures(OrchestratorTestCaseBase):
    """Usa o módulo fake (com 1 passa, 1 falha, 1 erro, 1 pulado) para
    validar que o orchestrator reporta corretamente cada tipo de
    desfecho — cenário que não dá para exercitar com os testes reais
    do projeto (que devem sempre passar)."""

    def test_run_single_fake_class_with_failure(self):
        report = self.orch.run("fake_for_tests", "TestFakeFirst")
        self.assertEqual(report.total, 2)
        self.assertEqual(report.passed, 1)
        self.assertEqual(report.failed, 1)
        self.assertFalse(report.success)

    def test_run_single_fake_class_with_error_and_skip(self):
        report = self.orch.run("fake_for_tests", "TestFakeSecond")
        self.assertEqual(report.total, 2)
        self.assertEqual(report.errors, 1)
        self.assertEqual(report.skipped, 1)
        self.assertFalse(report.success)

    def test_run_all_fake_classes_aggregates_correctly(self):
        report = self.orch.run("fake_for_tests", ALL_CLASSES_LABEL)
        self.assertEqual(report.total, 4)
        self.assertEqual(report.passed, 1)
        self.assertEqual(report.failed, 1)
        self.assertEqual(report.errors, 1)
        self.assertEqual(report.skipped, 1)

    def test_case_results_preserve_failure_messages(self):
        report = self.orch.run("fake_for_tests", "TestFakeFirst")
        failing = [c for c in report.case_results if c.outcome == "failed"]
        self.assertEqual(len(failing), 1)
        self.assertIn("não é igual a dois", failing[0].message)

    def test_suite_is_reusable_after_run(self):
        """Regressão do bug encontrado durante o desenvolvimento:
        TextTestRunner.run() esvazia a TestSuite internamente — o
        orchestrator deve continuar funcionando corretamente em
        chamadas repetidas (cada chamada de `run` cria sua própria
        suíte do zero, então não deve haver acúmulo de estado)."""
        report1 = self.orch.run("fake_for_tests", "TestFakeFirst")
        report2 = self.orch.run("fake_for_tests", "TestFakeFirst")
        self.assertEqual(report1.total, report2.total)
        self.assertEqual(len(report1.case_results), len(report2.case_results))
        self.assertEqual(report1.case_results[0].test_id, report2.case_results[0].test_id)


class TestFormattingFunctions(unittest.TestCase):
    """Testa gui.utils.test_formatting isoladamente, com RunReport
    construídos manualmente (sem depender do orchestrator)."""

    def _make_report(self, **overrides):
        defaults = dict(
            label="Categoria X", total=3, passed=2, failed=1, errors=0,
            skipped=0, duration_seconds=0.123, raw_output="saida bruta",
            case_results=[
                TestCaseResult("A.test_um", "passed"),
                TestCaseResult("A.test_dois", "passed"),
                TestCaseResult("A.test_tres", "failed", "Traceback...\nAssertionError: x != y"),
            ],
        )
        defaults.update(overrides)
        return RunReport(**defaults)

    def test_success_property_true_when_no_failures_or_errors(self):
        report = self._make_report(failed=0, errors=0)
        self.assertTrue(report.success)

    def test_success_property_false_with_failures(self):
        report = self._make_report(failed=1)
        self.assertFalse(report.success)

    def test_success_property_false_when_unavailable(self):
        report = self._make_report(unavailable_reason="pytest ausente")
        self.assertFalse(report.success)

    def test_status_icon_matches_success(self):
        ok_report = self._make_report(failed=0, errors=0)
        bad_report = self._make_report(failed=1)
        self.assertEqual(ok_report.status_icon, "✅")
        self.assertEqual(bad_report.status_icon, "❌")

    def test_format_run_header_contains_counts(self):
        report = self._make_report()
        header = format_run_header(report)
        self.assertIn("2/3", header)
        self.assertIn("1 falha", header)

    def test_format_run_header_unavailable(self):
        report = self._make_report(unavailable_reason="motivo X")
        header = format_run_header(report)
        self.assertIn("indisponível", header)
        self.assertIn("motivo X", header)

    def test_format_case_line_extracts_useful_message(self):
        case = TestCaseResult("A.test_x", "failed", "Traceback (most recent call last):\nAssertionError: 1 != 2")
        line = format_case_line(case)
        self.assertIn("✗", line)
        self.assertIn("AssertionError", line)
        self.assertNotIn("Traceback", line.split("\n")[-1])

    def test_format_full_report_includes_raw_output_when_requested(self):
        report = self._make_report()
        with_raw = format_full_report(report, show_raw_output=True)
        without_raw = format_full_report(report, show_raw_output=False)
        self.assertIn("saida bruta", with_raw)
        self.assertNotIn("saida bruta", without_raw)

    def test_format_category_summary_aggregates_multiple_reports(self):
        r1 = self._make_report(label="Cat A", total=3, passed=2, failed=1)
        r2 = self._make_report(label="Cat B", total=5, passed=5, failed=0)
        summary = format_category_summary([r1, r2])
        self.assertIn("7/8", summary)  # passed total = 2+5, total = 3+5

    def test_format_category_summary_lists_unavailable_separately(self):
        r1 = self._make_report(label="Cat A", total=3, passed=3, failed=0)
        r2 = self._make_report(label="Cat B", unavailable_reason="sem pytest")
        summary = format_category_summary([r1, r2])
        self.assertIn("Cat B", summary)
        self.assertIn("indisponível", summary)


if __name__ == "__main__":
    unittest.main()
