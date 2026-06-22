"""Testes para o CLI textual (`./cli`):

- cli.cli_interpreter.CliInterpreter: parsing de texto -> ParsedCommand.
- cli.cli_cmd_validator.CliCmdValidator: validação de forma.
- cli.cli_requester.CliRequester: empacotamento e despacho.
- cli.cli_responser: formatação de EventResult em texto.
- cli.cli_orchestrator.CliOrchestrator: pipeline completo texto->texto.
"""
import time
import unittest

from cli.cli_interpreter import CliInterpreter, ParseError
from cli.cli_cmd_validator import CliCmdValidator, ValidationError
from cli.cli_requester import CliRequester
from cli import cli_responser
from cli.cli_orchestrator import CliOrchestrator
from event.event import Event, EventResult
from event.event_orchestrator import EventOrchestrator
from event.event_type import EventType


class TestCliInterpreter(unittest.TestCase):
    def setUp(self):
        self.interp = CliInterpreter()

    def test_simple_command_no_args(self):
        parsed = self.interp.parse("help")
        self.assertEqual(parsed.command_token, "help")
        self.assertEqual(parsed.kwargs, {})

    def test_command_with_kwargs(self):
        parsed = self.interp.parse("bfs source=0 target=5")
        self.assertEqual(parsed.command_token, "bfs")
        self.assertEqual(parsed.kwargs, {"source": 0, "target": 5})

    def test_numeric_coercion_int_and_float(self):
        parsed = self.interp.parse("x a=3 b=3.5 c=-2")
        self.assertEqual(parsed.kwargs["a"], 3)
        self.assertIsInstance(parsed.kwargs["a"], int)
        self.assertEqual(parsed.kwargs["b"], 3.5)
        self.assertIsInstance(parsed.kwargs["b"], float)
        self.assertEqual(parsed.kwargs["c"], -2)

    def test_string_value_preserved(self):
        parsed = self.interp.parse("load filename=graph1.gexf")
        self.assertEqual(parsed.kwargs["filename"], "graph1.gexf")
        self.assertIsInstance(parsed.kwargs["filename"], str)

    def test_quoted_value_with_spaces(self):
        parsed = self.interp.parse('test run="Todos da categoria"')
        self.assertEqual(parsed.kwargs["run"], "Todos da categoria")

    def test_empty_input_raises_parse_error(self):
        with self.assertRaises(ParseError):
            self.interp.parse("")
        with self.assertRaises(ParseError):
            self.interp.parse("   ")

    def test_unclosed_quote_raises_parse_error(self):
        with self.assertRaises(ParseError):
            self.interp.parse('load filename="sem fechar')

    def test_token_without_equals_is_ignored(self):
        parsed = self.interp.parse("bfs source=0 algumacoisa")
        self.assertEqual(parsed.kwargs, {"source": 0})


class TestCliCmdValidator(unittest.TestCase):
    def setUp(self):
        self.interp = CliInterpreter()
        self.validator = CliCmdValidator()

    def test_valid_command_resolves_event_type(self):
        parsed = self.interp.parse("bfs source=0")
        validated = self.validator.validate(parsed)
        self.assertEqual(validated.event_type, EventType.RUN_BFS)
        self.assertEqual(validated.payload, {"source": 0})

    def test_alias_resolves_to_canonical_event_type(self):
        parsed = self.interp.parse("info")
        validated = self.validator.validate(parsed)
        self.assertEqual(validated.event_type, EventType.SHOW_GRAPH_INFO)

    def test_unknown_command_raises(self):
        parsed = self.interp.parse("comando_invalido")
        with self.assertRaises(ValidationError):
            self.validator.validate(parsed)

    def test_missing_required_argument_raises(self):
        parsed = self.interp.parse("bfs")
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(parsed)
        self.assertIn("source", str(ctx.exception))

    def test_unknown_argument_raises(self):
        parsed = self.interp.parse("bfs source=0 destino=5")
        with self.assertRaises(ValidationError) as ctx:
            self.validator.validate(parsed)
        self.assertIn("destino", str(ctx.exception))

    def test_command_with_no_spec_rejects_any_argument(self):
        """HELP não tem CommandSpec definida -> qualquer argumento
        deveria ser rejeitado como desconhecido."""
        parsed = self.interp.parse("help algo=1")
        with self.assertRaises(ValidationError):
            self.validator.validate(parsed)

    def test_optional_argument_is_accepted(self):
        parsed = self.interp.parse("bfs source=0 target=5")
        validated = self.validator.validate(parsed)
        self.assertEqual(validated.payload["target"], 5)

    def test_command_without_required_args_is_valid_when_omitted_optional(self):
        parsed = self.interp.parse("prim")
        validated = self.validator.validate(parsed)
        self.assertEqual(validated.event_type, EventType.RUN_PRIM)


class TestCliRequester(unittest.TestCase):
    def setUp(self):
        self.orchestrator = EventOrchestrator()
        self.requester = CliRequester(self.orchestrator)
        self.interp = CliInterpreter()
        self.validator = CliCmdValidator()

    def test_build_request_has_unique_id(self):
        parsed = self.interp.parse("help")
        validated = self.validator.validate(parsed)
        r1 = self.requester.build_request(validated)
        r2 = self.requester.build_request(validated)
        self.assertNotEqual(r1.request_id, r2.request_id)

    def test_send_dispatches_through_orchestrator(self):
        parsed = self.interp.parse("help")
        validated = self.validator.validate(parsed)
        request = self.requester.build_request(validated)
        results = self.requester.send(request)
        self.assertTrue(results[0].success)
        self.assertIn("available_commands", results[0].data)


class TestCliResponser(unittest.TestCase):
    def test_format_result_success(self):
        event = Event(EventType.ECHO, {"text": "x"})
        result = EventResult.ok(event, data={"echo": "x"}, duration_seconds=0.01)
        text = cli_responser.format_result(result)
        self.assertIn("✅", text)
        self.assertIn("echo", text)

    def test_format_result_failure(self):
        event = Event(EventType.RUN_BFS, {})
        result = EventResult.fail(event, error="origem ausente")
        text = cli_responser.format_result(result)
        self.assertIn("❌", text)
        self.assertIn("origem ausente", text)

    def test_format_results_empty_means_pending(self):
        text = cli_responser.format_results([])
        self.assertIn("assíncron", text.lower())

    def test_format_data_truncates_long_lists(self):
        event = Event(EventType.RUN_BFS, {"source": 0})
        result = EventResult.ok(event, data={"order": list(range(50))}, duration_seconds=0.0)
        text = cli_responser.format_result(result)
        self.assertIn("mais 40 item(ns)", text)


class TestCliOrchestratorEndToEnd(unittest.TestCase):
    def setUp(self):
        self.cli = CliOrchestrator()

    def test_execute_never_raises_on_malformed_input(self):
        output = self.cli.execute('load filename="sem fechar')
        self.assertIn("❌", output)

    def test_execute_never_raises_on_unknown_command(self):
        output = self.cli.execute("comando_que_nao_existe")
        self.assertIn("❌", output)

    def test_execute_never_raises_on_missing_argument(self):
        output = self.cli.execute("bfs")
        self.assertIn("❌", output)

    def test_full_pipeline_load_then_query(self):
        load_output = self.cli.execute("load filename=graph1.gexf")
        self.assertIn("✅", load_output)
        self.assertIn("vertex_count", load_output)

        info_output = self.cli.execute("info")
        self.assertIn("✅", info_output)
        self.assertIn("98", info_output)

    def test_state_persists_across_commands(self):
        """O grafo carregado em um comando deve estar disponível para
        o próximo (o CliOrchestrator reusa o mesmo EventOrchestrator)."""
        self.cli.execute("load filename=graph1.gexf")
        bfs_output = self.cli.execute("bfs source=0")
        self.assertIn("✅", bfs_output)
        self.assertNotIn("Nenhum grafo carregado", bfs_output)

    def test_async_command_returns_pending_notice_then_result_via_poll(self):
        self.cli.execute("load filename=graph1.gexf")
        immediate = self.cli.execute("run_floyd_warshall")
        self.assertIn("rodando em segundo plano", immediate)

        deadline = time.perf_counter() + 2.0
        polled = ""
        while time.perf_counter() < deadline:
            polled = self.cli.poll_async_results()
            if polled:
                break
            time.sleep(0.01)

        self.assertIn("✅", polled)
        self.assertIn("run_floyd_warshall", polled)

    def test_help_text_lists_all_event_types(self):
        text = self.cli.help_text()
        for event_type in EventType:
            self.assertIn(event_type.value, text)

    def test_alias_command_works_end_to_end(self):
        self.cli.execute("load filename=graph1.gexf")
        output = self.cli.execute("bfs source=0")  # "bfs" é alias de "run_bfs"
        self.assertIn("✅ run_bfs", output)


if __name__ == "__main__":
    unittest.main()
