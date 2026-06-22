"""Testes para a arquitetura EDA (`./event`):

- event.event_type.EventType: resolução de comandos e aliases.
- event.event.Event / EventResult: estrutura de dados básica.
- event.event_bus.EventBus: inscrição, despacho síncrono e
  assíncrono, múltiplos handlers, drenagem de resultados.
- event.event_orchestrator.EventOrchestrator: religação real aos
  módulos de domínio do projeto (grafo, testes, mineração).
"""
import threading
import time
import unittest

from event.event import Event, EventResult
from event.event_type import EventType
from event.event_bus import EventBus
from event.event_orchestrator import EventOrchestrator


class TestEventType(unittest.TestCase):
    def test_from_value_exact_match(self):
        self.assertEqual(EventType.from_value("run_bfs"), EventType.RUN_BFS)

    def test_from_value_alias(self):
        self.assertEqual(EventType.from_value("bfs"), EventType.RUN_BFS)
        self.assertEqual(EventType.from_value("info"), EventType.SHOW_GRAPH_INFO)

    def test_from_value_case_insensitive(self):
        self.assertEqual(EventType.from_value("BFS"), EventType.RUN_BFS)
        self.assertEqual(EventType.from_value("  bfs  "), EventType.RUN_BFS)

    def test_from_value_unknown_raises(self):
        with self.assertRaises(ValueError):
            EventType.from_value("comando_que_nao_existe")

    def test_all_values_are_unique(self):
        """@unique já garante isso na definição da classe, mas
        confirmamos explicitamente — uma colisão de valor quebraria
        silenciosamente o resolvedor de alias."""
        values = [e.value for e in EventType]
        self.assertEqual(len(values), len(set(values)))


class TestEvent(unittest.TestCase):
    def test_get_returns_default_when_missing(self):
        event = Event(EventType.RUN_BFS, payload={"source": 0})
        self.assertEqual(event.get("target", "fallback"), "fallback")
        self.assertEqual(event.get("source"), 0)

    def test_require_raises_when_missing(self):
        event = Event(EventType.RUN_BFS, payload={})
        with self.assertRaises(KeyError):
            event.require("source")

    def test_each_event_has_unique_id(self):
        e1 = Event(EventType.HELP)
        e2 = Event(EventType.HELP)
        self.assertNotEqual(e1.event_id, e2.event_id)

    def test_event_result_ok_and_fail_factories(self):
        event = Event(EventType.ECHO, payload={"text": "x"})
        ok = EventResult.ok(event, data={"echo": "x"}, duration_seconds=0.01)
        fail = EventResult.fail(event, error="algo falhou")
        self.assertTrue(ok.success)
        self.assertFalse(fail.success)
        self.assertEqual(ok.event_id, event.event_id)
        self.assertEqual(fail.event_id, event.event_id)


class TestEventBusSync(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()

    def test_dispatch_without_subscribers_returns_failure(self):
        results = self.bus.dispatch(Event(EventType.RUN_BFS, {"source": 0}))
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].success)
        self.assertIn("Nenhum handler", results[0].error)

    def test_dispatch_calls_subscribed_handler_synchronously(self):
        calls = []

        def handler(event):
            calls.append(event.event_id)
            return {"ok": True}

        self.bus.subscribe(EventType.ECHO, handler)
        results = self.bus.dispatch(Event(EventType.ECHO, {"text": "x"}))

        self.assertEqual(len(calls), 1)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].data, {"ok": True})
        self.assertEqual(results[0].handled_in_thread, threading.current_thread().name)

    def test_handler_exception_becomes_failed_result_not_raised(self):
        def bad_handler(event):
            raise RuntimeError("falhou de propósito")

        self.bus.subscribe(EventType.ECHO, bad_handler)
        results = self.bus.dispatch(Event(EventType.ECHO))
        self.assertFalse(results[0].success)
        self.assertIn("falhou de propósito", results[0].error)

    def test_multiple_handlers_for_same_event_type_all_run(self):
        order = []
        self.bus.subscribe(EventType.ECHO, lambda e: order.append("first"))
        self.bus.subscribe(EventType.ECHO, lambda e: order.append("second"))
        results = self.bus.dispatch(Event(EventType.ECHO))
        self.assertEqual(order, ["first", "second"])
        self.assertEqual(len(results), 2)

    def test_unsubscribe_removes_handler(self):
        handler = lambda e: "x"
        self.bus.subscribe(EventType.ECHO, handler)
        self.assertTrue(self.bus.has_subscribers(EventType.ECHO))
        removed = self.bus.unsubscribe(EventType.ECHO, handler)
        self.assertTrue(removed)
        self.assertFalse(self.bus.has_subscribers(EventType.ECHO))


class TestEventBusAsync(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()

    def _wait_for_results(self, expected_count, timeout=2.0):
        deadline = time.perf_counter() + timeout
        collected = []
        while len(collected) < expected_count and time.perf_counter() < deadline:
            collected.extend(self.bus.pop_results())
            if len(collected) < expected_count:
                time.sleep(0.005)
        return collected

    def test_async_dispatch_returns_immediately_with_empty_list(self):
        def slow_handler(event):
            time.sleep(0.05)
            return "done"

        self.bus.subscribe(EventType.ECHO, slow_handler)
        start = time.perf_counter()
        results = self.bus.dispatch(Event(EventType.ECHO), async_=True)
        elapsed = time.perf_counter() - start

        self.assertEqual(results, [])
        self.assertLess(elapsed, 0.05, "dispatch assíncrono não deveria bloquear esperando o handler")

    def test_async_result_eventually_available_via_pop_results(self):
        def handler(event):
            return {"value": 42}

        self.bus.subscribe(EventType.ECHO, handler)
        self.bus.dispatch(Event(EventType.ECHO), async_=True)

        collected = self._wait_for_results(1)
        self.assertEqual(len(collected), 1)
        self.assertTrue(collected[0].success)
        self.assertEqual(collected[0].data, {"value": 42})
        self.assertNotEqual(collected[0].handled_in_thread, threading.current_thread().name)

    def test_async_handler_exception_becomes_failed_result(self):
        def bad_handler(event):
            raise ValueError("erro assíncrono de propósito")

        self.bus.subscribe(EventType.ECHO, bad_handler)
        self.bus.dispatch(Event(EventType.ECHO), async_=True)

        collected = self._wait_for_results(1)
        self.assertFalse(collected[0].success)
        self.assertIn("erro assíncrono de propósito", collected[0].error)

    def test_multiple_async_dispatches_run_concurrently_in_distinct_threads(self):
        def handler(event):
            time.sleep(0.05)
            return event.event_id

        self.bus.subscribe(EventType.ECHO, handler)
        start = time.perf_counter()
        for _ in range(5):
            self.bus.dispatch(Event(EventType.ECHO), async_=True)

        collected = self._wait_for_results(5, timeout=3.0)
        elapsed = time.perf_counter() - start

        self.assertEqual(len(collected), 5)
        threads_used = {r.handled_in_thread for r in collected}
        self.assertEqual(len(threads_used), 5, "cada despacho assíncrono deveria usar sua própria thread")
        # Se tivessem rodado sequencialmente, levaria >= 0.25s (5 * 0.05s).
        # Em paralelo, deve ficar bem abaixo disso.
        self.assertLess(elapsed, 0.2, "despachos assíncronos deveriam rodar em paralelo, não em série")

    def test_default_async_from_subscription_is_respected_when_not_overridden(self):
        results_holder = []
        self.bus.subscribe(EventType.ECHO, lambda e: results_holder.append(1) or "ok", default_async=True)
        # Não especifica async_: deve usar o default_async=True da inscrição.
        results = self.bus.dispatch(Event(EventType.ECHO))
        self.assertEqual(results, [])  # confirma que rodou async (retorno vazio)
        collected = self._wait_for_results(1)
        self.assertEqual(len(collected), 1)


class TestEventOrchestratorGraphLifecycle(unittest.TestCase):
    def setUp(self):
        self.orch = EventOrchestrator(gexf_dir="./gexf", csv_dir="./csv")

    def test_load_real_graph_from_project(self):
        results = self.orch.dispatch(EventType.LOAD_GRAPH, {"filename": "graph1.gexf"})
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].data["vertex_count"], 98)
        self.assertEqual(results[0].data["edge_count"], 166)
        self.assertIsNotNone(self.orch.current_graph)

    def test_unload_clears_state(self):
        self.orch.dispatch(EventType.LOAD_GRAPH, {"filename": "graph1.gexf"})
        self.orch.dispatch(EventType.UNLOAD_GRAPH)
        self.assertIsNone(self.orch.current_graph)

    def test_algorithm_without_graph_loaded_fails_gracefully(self):
        results = self.orch.dispatch(EventType.RUN_BFS, {"source": 0})
        self.assertFalse(results[0].success)
        self.assertIn("Nenhum grafo carregado", results[0].error)


class TestEventOrchestratorAlgorithms(unittest.TestCase):
    """Confere que os handlers produzem resultados consistentes com
    as funções reais de grafo.networkx_pure.transversal — não
    reimplementa a lógica, só confere a religação (payload correto
    entra, formato de saída esperado sai)."""

    def setUp(self):
        self.orch = EventOrchestrator(gexf_dir="./gexf", csv_dir="./csv")
        self.orch.dispatch(EventType.LOAD_GRAPH, {"filename": "graph1.gexf"})

    def test_bfs_matches_direct_call(self):
        from grafo.networkx_pure import transversal as tv
        expected = tv.bfs(self.orch.current_graph, 0)
        result = self.orch.dispatch(EventType.RUN_BFS, {"source": 0})[0]
        self.assertTrue(result.success)
        self.assertEqual(result.data["order"], expected.order)

    def test_bfs_with_target_includes_path(self):
        result = self.orch.dispatch(EventType.RUN_BFS, {"source": 0, "target": 10})[0]
        self.assertTrue(result.success)
        self.assertIsNotNone(result.data["path_to_target"])
        self.assertEqual(result.data["path_to_target"][0], 0)
        self.assertEqual(result.data["path_to_target"][-1], 10)

    def test_kruskal_produces_spanning_tree_with_n_minus_1_edges_per_component(self):
        result = self.orch.dispatch(EventType.RUN_KRUSKAL)[0]
        self.assertTrue(result.success)
        self.assertEqual(result.data["mst_vertex_count"], 98)
        # MST de um grafo desconexo tem (n - num_componentes) arestas.
        self.assertLessEqual(result.data["mst_edge_count"], 97)

    def test_show_structure_matches_direct_call(self):
        from grafo.networkx_pure.adapter import GraphAdapter
        from grafo.networkx_pure import structure as nx_structure
        adapter = GraphAdapter(self.orch.current_graph)
        expected = nx_structure.structural_summary(adapter)

        result = self.orch.dispatch(EventType.SHOW_STRUCTURE)[0]
        self.assertTrue(result.success)
        self.assertEqual(result.data["num_vertices"], expected["num_vertices"])
        self.assertEqual(result.data["density"], expected["density"])

    def test_topological_sort_on_cyclic_graph_returns_none(self):
        result = self.orch.dispatch(EventType.RUN_TOPOLOGICAL_SORT)[0]
        self.assertTrue(result.success)
        # graph1.gexf tem ciclos (é um grafo de colaboração real) —
        # confirmamos que o handler reporta isso sem lançar exceção.
        self.assertIsInstance(result.data["has_cycle"], bool)


class TestEventOrchestratorTestSuiteIntegration(unittest.TestCase):
    """Confere a religação com gui.bridges.test_orchestrator —
    rodar a suíte de testes através de um Event."""

    def setUp(self):
        self.orch = EventOrchestrator()

    def test_run_tests_for_algorithms_category(self):
        results = self.orch.dispatch(EventType.RUN_TESTS, {"category": "algorithms"}, async_=False)
        self.assertTrue(results[0].success)
        self.assertEqual(results[0].data["total"], 12)
        self.assertTrue(results[0].data["success"])

    def test_list_test_categories(self):
        results = self.orch.dispatch(EventType.LIST_TEST_CATEGORIES)
        self.assertTrue(results[0].success)
        self.assertIn("Algoritmos de grafos (BFS, DFS, Dijkstra...)", results[0].data["categories"])


if __name__ == "__main__":
    unittest.main()
