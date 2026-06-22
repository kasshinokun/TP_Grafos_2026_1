# ./event/event_orchestrator.py
"""Fachada de alto nível da arquitetura EDA.

`EventOrchestrator` é o que a GUI (ou o CLI, em `./cli`) realmente
importa e usa — ele:

1. Cria um `EventBus` e registra, para cada `EventType`, um handler
   "de verdade", religado aos módulos de domínio já existentes do
   projeto (`grafo.networkx_pure.transversal`, `grafo.utils.gexf_parser`,
   `grafo.utils.graph_structure`, `miner.graph_builder`,
   `gui.bridges.test_orchestrator`) — nenhuma lógica de grafo é
   reimplementada aqui, só roteamento e empacotamento de payload.

2. Mantém o estado de runtime que os handlers precisam compartilhar
   entre um evento e o próximo (o grafo atualmente carregado) — assim
   um evento "RUN_BFS" não precisa que o payload inclua o grafo
   inteiro, só os parâmetros do algoritmo (origem, destino).

3. Expõe `dispatch(event_type, payload, ...)` como atalho de
   conveniência sobre `EventBus.dispatch`, e `poll()` para a thread da
   GUI drenar resultados assíncronos periodicamente (via `after`).

Threading: ver `event/event_bus.py` para o modelo híbrido completo.
Em resumo, cada `EventType` aqui é registrado com um `default_async`
que reflete o custo esperado do handler — algoritmos sobre grafos
pequenos/médios (BFS, info, estrutura) são síncronos; operações que
podem ser lentas e dependem de E/S (rodar a suíte de testes inteira,
construir grafos a partir de um CSV grande) são assíncronas por
padrão. Qualquer chamada pode sobrescrever isso via `dispatch(...,
async_=True/False)`.
"""
import os
import threading
from typing import Any, Dict, List, Optional

from event.event import Event, EventResult
from event.event_bus import EventBus
from event.event_type import EventType

from grafo.utils.gexf_parser import load_gexf
from grafo.utils import graph_structure
from grafo.networkx_pure.adapter import GraphAdapter
from grafo.networkx_pure import structure as nx_structure
from grafo.networkx_pure import transversal as tv


class EventOrchestrator:
    """Veja o docstring do módulo. Uma instância tipicamente vive pelo
    tempo de vida de uma tela da GUI (ou do processo, se compartilhada
    entre telas) — `current_graph` é o único estado mutável guardado
    aqui."""

    def __init__(self, gexf_dir: str = "./gexf", csv_dir: str = "./csv"):
        self.bus = EventBus()
        self.current_graph = None
        self.current_graph_name: Optional[str] = None
        self.gexf_dir = gexf_dir
        self.csv_dir = csv_dir
        self._state_lock = threading.Lock()  # protege current_graph entre threads
        self._register_default_handlers()

    # ------------------------------------------------------------------
    # API pública (usada pela GUI e pelo CLI)
    # ------------------------------------------------------------------

    def dispatch(self, event_type: EventType, payload: Optional[dict] = None,
                 source: str = "orchestrator", async_: Optional[bool] = None) -> List[EventResult]:
        """Atalho sobre `EventBus.dispatch`: monta o `Event` e
        despacha. Veja `EventBus.dispatch` para a semântica completa
        de `async_`."""
        event = Event(event_type=event_type, payload=payload or {}, source=source)
        return self.bus.dispatch(event, async_=async_)

    def poll(self) -> List[EventResult]:
        """Drena resultados de despachos assíncronos pendentes. Deve
        ser chamado pela thread da GUI (ex.: dentro de
        `widget.after(100, orchestrator.poll)`), nunca de uma worker
        thread."""
        return self.bus.pop_results()

    # ------------------------------------------------------------------
    # Registro dos handlers reais
    # ------------------------------------------------------------------

    def _register_default_handlers(self):
        sync_handlers = {
            EventType.LOAD_GRAPH: self._handle_load_graph,
            EventType.SAVE_GRAPH: self._handle_save_graph,
            EventType.UNLOAD_GRAPH: self._handle_unload_graph,
            EventType.RUN_BFS: self._handle_bfs,
            EventType.RUN_DFS: self._handle_dfs,
            EventType.RUN_DIJKSTRA: self._handle_dijkstra,
            EventType.RUN_BELLMAN_FORD: self._handle_bellman_ford,
            EventType.RUN_KRUSKAL: self._handle_kruskal,
            EventType.RUN_PRIM: self._handle_prim,
            EventType.RUN_FORD_FULKERSON: self._handle_ford_fulkerson,
            EventType.RUN_EDMONDS_KARP: self._handle_edmonds_karp,
            EventType.RUN_TOPOLOGICAL_SORT: self._handle_topological_sort,
            EventType.RUN_CONNECTED_COMPONENTS: self._handle_connected_components,
            EventType.RUN_KOSARAJU: self._handle_kosaraju,
            EventType.RUN_TARJAN: self._handle_tarjan,
            EventType.SHOW_GRAPH_INFO: self._handle_show_graph_info,
            EventType.SHOW_STRUCTURE: self._handle_show_structure,
            EventType.LIST_TEST_CATEGORIES: self._handle_list_test_categories,
            EventType.LIST_TEST_RUNS: self._handle_list_test_runs,
            EventType.HELP: self._handle_help,
            EventType.ECHO: self._handle_echo,
        }
        for event_type, handler in sync_handlers.items():
            self.bus.subscribe(event_type, handler, default_async=False)

        # RUN_FLOYD_WARSHALL é O(n³) — pode ficar perceptível em
        # grafos maiores, então é o único algoritmo síncrono "comum"
        # que registramos como assíncrono por padrão.
        self.bus.subscribe(EventType.RUN_FLOYD_WARSHALL, self._handle_floyd_warshall, default_async=True)

        # Operações de E/S potencialmente lentas (rede de arquivos,
        # parsing de CSV grande, suíte de testes inteira): assíncronas
        # por padrão, para nunca travar a GUI que despachou o evento.
        self.bus.subscribe(EventType.BUILD_GRAPH_FROM_CSV, self._handle_build_graph_from_csv, default_async=True)
        self.bus.subscribe(EventType.RUN_TESTS, self._handle_run_tests, default_async=True)

    # ------------------------------------------------------------------
    # Handlers: ciclo de vida do grafo
    # ------------------------------------------------------------------

    def _handle_load_graph(self, event: Event) -> dict:
        filename = event.require("filename")
        path = filename if os.path.isabs(filename) else os.path.join(self.gexf_dir, filename)
        graph = load_gexf(path)
        with self._state_lock:
            self.current_graph = graph
            self.current_graph_name = os.path.basename(filename)
        return self._graph_info_payload()

    def _handle_save_graph(self, event: Event) -> dict:
        if self.current_graph is None:
            raise ValueError("Nenhum grafo carregado para salvar.")
        filename = event.get("filename") or self.current_graph_name or "grafo.gexf"
        path = filename if os.path.isabs(filename) else os.path.join(self.gexf_dir, filename)
        self.current_graph.export_to_gephi(path)
        with self._state_lock:
            self.current_graph_name = os.path.basename(filename)
        return {"saved_to": path}

    def _handle_unload_graph(self, event: Event) -> dict:
        with self._state_lock:
            self.current_graph = None
            self.current_graph_name = None
        return {"unloaded": True}

    # ------------------------------------------------------------------
    # Handlers: algoritmos de travessia/caminho
    # ------------------------------------------------------------------

    def _require_graph(self):
        if self.current_graph is None:
            raise ValueError("Nenhum grafo carregado. Use LOAD_GRAPH primeiro.")
        return self.current_graph

    def _handle_bfs(self, event: Event) -> dict:
        g = self._require_graph()
        source = int(event.require("source"))
        result = tv.bfs(g, source)
        target = event.get("target")
        path = result.path_to(int(target)) if target is not None else None
        return {"order": result.order, "path_to_target": path}

    def _handle_dfs(self, event: Event) -> dict:
        g = self._require_graph()
        source = int(event.require("source"))
        result = tv.dfs(g, source)
        target = event.get("target")
        path = result.path_to(int(target)) if target is not None else None
        return {"order": result.order, "path_to_target": path}

    def _handle_dijkstra(self, event: Event) -> dict:
        g = self._require_graph()
        source = int(event.require("source"))
        dist, pred = tv.dijkstra(g, source)
        return {"distances": dist, "predecessors": pred}

    def _handle_bellman_ford(self, event: Event) -> dict:
        g = self._require_graph()
        source = int(event.require("source"))
        dist, pred, no_negative_cycle = tv.bellman_ford(g, source)
        return {"distances": dist, "predecessors": pred, "no_negative_cycle": no_negative_cycle}

    def _handle_floyd_warshall(self, event: Event) -> dict:
        g = self._require_graph()
        dist, pred = tv.floyd_warshall(g)
        return {"distances": dist, "predecessors": pred}

    def _handle_kruskal(self, event: Event) -> dict:
        g = self._require_graph()
        mst = tv.kruskal(g)
        return {"mst_vertex_count": mst.get_vertex_count(), "mst_edge_count": mst.get_edge_count()}

    def _handle_prim(self, event: Event) -> dict:
        g = self._require_graph()
        start = int(event.get("source", 0))
        mst = tv.prim(g, start)
        return {"mst_vertex_count": mst.get_vertex_count(), "mst_edge_count": mst.get_edge_count()}

    def _handle_ford_fulkerson(self, event: Event) -> dict:
        g = self._require_graph()
        source = int(event.require("source"))
        sink = int(event.require("sink"))
        flow_value, flow_graph = tv.ford_fulkerson(g, source, sink)
        return {"max_flow": flow_value}

    def _handle_edmonds_karp(self, event: Event) -> dict:
        g = self._require_graph()
        source = int(event.require("source"))
        sink = int(event.require("sink"))
        flow_value, flow_graph = tv.edmonds_karp(g, source, sink)
        return {"max_flow": flow_value}

    def _handle_topological_sort(self, event: Event) -> dict:
        g = self._require_graph()
        order = tv.topological_sort(g)
        return {"order": order, "has_cycle": order is None}

    def _handle_connected_components(self, event: Event) -> dict:
        g = self._require_graph()
        comps = tv.connected_components(g)
        return {"components": comps, "count": len(comps)}

    def _handle_kosaraju(self, event: Event) -> dict:
        g = self._require_graph()
        sccs = tv.kosaraju_scc(g)
        return {"components": sccs, "count": len(sccs)}

    def _handle_tarjan(self, event: Event) -> dict:
        g = self._require_graph()
        sccs = tv.tarjan_scc(g)
        return {"components": sccs, "count": len(sccs)}

    # ------------------------------------------------------------------
    # Handlers: inspeção estrutural
    # ------------------------------------------------------------------

    def _graph_info_payload(self) -> dict:
        g = self.current_graph
        return {
            "name": self.current_graph_name,
            "vertex_count": g.get_vertex_count(),
            "edge_count": g.get_edge_count(),
            "connected": g.is_connected(),
            "complete": g.is_complete_graph(),
            "empty": g.is_empty_graph(),
        }

    def _handle_show_graph_info(self, event: Event) -> dict:
        self._require_graph()
        return self._graph_info_payload()

    def _handle_show_structure(self, event: Event) -> dict:
        g = self._require_graph()
        adapter = GraphAdapter(g)
        summary = nx_structure.structural_summary(adapter)
        summary["adjacency_list_text"] = graph_structure.format_adjacency_list(g)
        summary["degree_sequence_text"] = graph_structure.format_degree_sequence(g)
        return summary

    # ------------------------------------------------------------------
    # Handlers: construção de grafos a partir de CSV (./miner/graph_builder.py)
    # ------------------------------------------------------------------

    def _handle_build_graph_from_csv(self, event: Event) -> dict:
        from miner import graph_builder

        filename = event.require("filename")
        path = filename if os.path.isabs(filename) else os.path.join(self.csv_dir, filename)

        interactions = graph_builder.load_interactions_csv(path)
        graphs = graph_builder.build_all_graphs(interactions)

        saved = {}
        for name, g in graphs.items():
            out_path = os.path.join(self.gexf_dir, f"{name}.gexf")
            g.export_to_gephi(out_path)
            saved[name] = out_path
        return {"built_graphs": saved, "interaction_count": len(interactions)}

    # ------------------------------------------------------------------
    # Handlers: testes unitários (./gui/bridges/test_orchestrator.py)
    # ------------------------------------------------------------------

    def _handle_list_test_categories(self, event: Event) -> dict:
        from gui.bridges.test_orchestrator import TestOrchestrator
        orch = TestOrchestrator()
        return {"categories": [c.label for c in orch.list_categories()]}

    def _handle_list_test_runs(self, event: Event) -> dict:
        from gui.bridges.test_orchestrator import TestOrchestrator
        orch = TestOrchestrator()
        category_key = event.require("category")
        return {"runs": orch.list_runs(category_key)}

    def _handle_run_tests(self, event: Event) -> dict:
        from gui.bridges.test_orchestrator import TestOrchestrator, ALL_CLASSES_LABEL
        orch = TestOrchestrator()
        category_key = event.require("category")
        run_label = event.get("run", ALL_CLASSES_LABEL)
        report = orch.run(category_key, run_label)
        return {
            "label": report.label,
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "errors": report.errors,
            "success": report.success,
        }

    # ------------------------------------------------------------------
    # Handlers: meta-comandos do CLI
    # ------------------------------------------------------------------

    def _handle_help(self, event: Event) -> dict:
        return {"available_commands": [e.value for e in EventType]}

    def _handle_echo(self, event: Event) -> dict:
        return {"echo": event.get("text", "")}
