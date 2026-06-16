import sys
from ..events.event_type import EventType
from ..events.event import Event
from ..graph.mining.csv_loader import CsvLoader

class CLI:
    def __init__(self, app):
        self.bus = app.get_bus()
        self.registry = app.get_registry()

    def run(self):
        self.print_banner()
        while True:
            try:
                line = input("\n> ").strip()
                if not line:
                    continue
                if not self.process_command(line):
                    break
            except EOFError:
                break
            except Exception as e:
                print(f"[ERRO] {str(e)}")
        print("Encerrando. Até logo!")

    def print_banner(self):
        print("═══════════════════════════════════════════════")
        print("  Ferramenta de Análise de Grafos — PUC Minas  ")
        print("  Versão Python (EDA Monolítico)               ")
        print("═══════════════════════════════════════════════")
        print("digite help para lista de comandos")

    def process_command(self, line):
        args = line.split()
        cmd = args[0].lower()
        
        try:
            if cmd == "help": self.print_help()
            elif cmd in ["exit", "quit"]: return False
            elif cmd == "create": self.cmd_create(args)
            elif cmd == "list": self.cmd_list()
            elif cmd == "info": self.cmd_info(args)
            elif cmd == "add-edge": self.cmd_add_edge(args)
            elif cmd == "rem-edge": self.cmd_rem_edge(args)
            elif cmd == "has-edge": self.cmd_has_edge(args)
            elif cmd == "degree": self.cmd_degree(args)
            elif cmd == "connected": self.cmd_connected(args)
            elif cmd == "bfs": self.cmd_bfs(args)
            elif cmd == "dfs": self.cmd_dfs(args)
            elif cmd == "shortest": self.cmd_shortest(args)
            elif cmd == "topsort": self.cmd_topsort(args)
            elif cmd == "scc": self.cmd_scc(args)
            elif cmd == "degree-centrality": self.cmd_metric(args, EventType.METRIC_DEGREE_CENTRALITY, "Centralidade de Grau")
            elif cmd == "betweenness": self.cmd_metric(args, EventType.METRIC_BETWEENNESS_CENTRALITY, "Betweenness Centrality")
            elif cmd == "closeness": self.cmd_metric(args, EventType.METRIC_CLOSENESS_CENTRALITY, "Closeness Centrality")
            elif cmd == "pagerank": self.cmd_metric(args, EventType.METRIC_PAGERANK, "PageRank")
            elif cmd == "density": self.cmd_scalar_metric(args, EventType.METRIC_DENSITY, "Densidade")
            elif cmd == "clustering": self.cmd_metric(args, EventType.METRIC_CLUSTERING_COEFFICIENT, "Coef. Aglomeração")
            elif cmd == "assortativity": self.cmd_scalar_metric(args, EventType.METRIC_ASSORTATIVITY, "Assortatividade")
            elif cmd == "communities": self.cmd_communities(args)
            elif cmd == "bridging": self.cmd_bridging(args)
            elif cmd == "export": self.cmd_export(args)
            elif cmd == "load-csv": self.cmd_load_csv(args)
            elif cmd == "sample-csv": self.cmd_sample_csv(args)
            elif cmd == "build-graphs": self.cmd_build_graphs(args)
            elif cmd == "show": self.cmd_show(args)
            elif cmd == "full-analysis": self.cmd_full_analysis(args)
            else: print(f"Comando desconhecido: {cmd}. Digite 'help'.")
        except Exception as e:
            print(f"[ERRO] {str(e)}")
        return True

    def print_help(self):
        print("Comandos disponíveis:")
        print("  create <id> <n> [matrix|list]          — cria grafo")
        print("  list                                    — lista grafos registrados")
        print("  info <id>                               — informações do grafo")
        print("  add-edge <id> <u> <v> [peso]           — adiciona aresta")
        print("  rem-edge <id> <u> <v>                  — remove aresta")
        print("  has-edge <id> <u> <v>                  — verifica aresta")
        print("  degree <id> <v>                         — graus de entrada/saída")
        print("  connected <id>                          — é conectado?")
        print("  bfs <id> <src>                          — BFS a partir de src")
        print("  dfs <id> <src>                          — DFS a partir de src")
        print("  shortest <id> <src> <dst>              — caminho mais curto (Dijkstra)")
        print("  topsort <id>                            — ordenação topológica")
        print("  scc <id>                                — componentes fortemente conexos")
        print("  degree-centrality <id>                  — centralidade de grau")
        print("  betweenness <id>                        — centralidade de intermediação")
        print("  closeness <id>                          — centralidade de proximidade")
        print("  pagerank <id>                           — PageRank")
        print("  density <id>                            — densidade da rede")
        print("  clustering <id>                         — coef. de aglomeração")
        print("  assortativity <id>                      — assortatividade")
        print("  communities <id>                        — detecção de comunidades")
        print("  bridging <id>                           — bridging ties")
        print("  export <id> <path>                      — exporta GEPHI (.gexf)")
        print("  load-csv <path>                         — carrega interações de CSV")
        print("  sample-csv <path>                       — gera CSV de exemplo")
        print("  build-graphs <csvPath>                  — constrói os 4 grafos do trabalho")
        print("  show <id>                               — exibe estrutura do grafo")
        print("  full-analysis <id>                      — análise completa")
        print("  exit                                    — encerra")

    def cmd_create(self, args):
        if len(args) < 3: raise ValueError("Uso: create <id> <n> [impl]")
        gid, n = args[1], int(args[2])
        impl = args[3] if len(args) > 3 else "list"
        ev = self.bus.publish(Event(EventType.GRAPH_CREATE).with_payload("graphId", gid).with_payload("numVertices", n).with_payload("impl", impl))
        self.check_and_print(ev, f"Grafo '{gid}' criado ({impl}, {n} vértices).")

    def cmd_list(self):
        ids = self.registry.list_ids()
        if not ids:
            print("Nenhum grafo registrado.")
            return
        print("Grafos registrados:")
        for gid in sorted(list(ids)):
            g = self.registry.get(gid)
            print(f"  • {gid} — {g}")

    def cmd_info(self, args):
        if len(args) < 2: raise ValueError("Uso: info <id>")
        g = self.registry.get(args[1])
        print(f"=== {args[1]} ===")
        print(f"  Implementação : {g.rep_type.name}")
        print(f"  Vértices      : {g.get_vertex_count()}")
        print(f"  Arestas       : {g.get_edge_count()}")
        print(f"  Conectado     : {g.is_connected()}")
        print(f"  Grafo vazio   : {g.is_empty_graph()}")
        print(f"  Grafo completo: {g.is_complete_graph()}")

    def cmd_add_edge(self, args):
        if len(args) < 4: raise ValueError("Uso: add-edge <id> <u> <v> [peso]")
        gid, u, v = args[1], int(args[2]), int(args[3])
        ev = self.bus.publish(Event(EventType.GRAPH_ADD_EDGE).with_payload("graphId", gid).with_payload("u", u).with_payload("v", v))
        if len(args) > 4:
            w = float(args[4])
            self.bus.publish(Event(EventType.GRAPH_SET_EDGE_WEIGHT).with_payload("graphId", gid).with_payload("u", u).with_payload("v", v).with_payload("weight", w))
        self.check_and_print(ev, f"Aresta {u} → {v} adicionada.")

    def cmd_rem_edge(self, args):
        if len(args) < 4: raise ValueError("Uso: rem-edge <id> <u> <v>")
        ev = self.bus.publish(Event(EventType.GRAPH_REMOVE_EDGE).with_payload("graphId", args[1]).with_payload("u", int(args[2])).with_payload("v", int(args[3])))
        self.check_and_print(ev, "Aresta removida.")

    def cmd_has_edge(self, args):
        if len(args) < 4: raise ValueError("Uso: has-edge <id> <u> <v>")
        ev = self.bus.publish(Event(EventType.GRAPH_HAS_EDGE).with_payload("graphId", args[1]).with_payload("u", int(args[2])).with_payload("v", int(args[3])))
        if ev.success:
            print(f"hasEdge({args[2]},{args[3]}) = {ev.result}")
        else:
            print(f"[ERRO] {ev.error_message}")

    def cmd_degree(self, args):
        if len(args) < 3: raise ValueError("Uso: degree <id> <v>")
        gid, v = args[1], int(args[2])
        ev_in = self.bus.publish(Event(EventType.GRAPH_IN_DEGREE).with_payload("graphId", gid).with_payload("v", v))
        ev_out = self.bus.publish(Event(EventType.GRAPH_OUT_DEGREE).with_payload("graphId", gid).with_payload("v", v))
        print(f"Vértice {v} — in-degree: {ev_in.result}, out-degree: {ev_out.result}")

    def cmd_connected(self, args):
        if len(args) < 2: raise ValueError("Uso: connected <id>")
        ev = self.bus.publish(Event(EventType.GRAPH_IS_CONNECTED).with_payload("graphId", args[1]))
        self.check_and_print(ev, f"Conectado: {ev.result}")

    def cmd_bfs(self, args):
        if len(args) < 3: raise ValueError("Uso: bfs <id> <src>")
        ev = self.bus.publish(Event(EventType.ALGO_BFS).with_payload("graphId", args[1]).with_payload("source", int(args[2])))
        self.check_and_print(ev, f"BFS: {ev.result}")

    def cmd_dfs(self, args):
        if len(args) < 3: raise ValueError("Uso: dfs <id> <src>")
        ev = self.bus.publish(Event(EventType.ALGO_DFS).with_payload("graphId", args[1]).with_payload("source", int(args[2])))
        self.check_and_print(ev, f"DFS: {ev.result}")

    def cmd_shortest(self, args):
        if len(args) < 4: raise ValueError("Uso: shortest <id> <src> <dst>")
        ev = self.bus.publish(Event(EventType.ALGO_SHORTEST_PATH).with_payload("graphId", args[1]).with_payload("source", int(args[2])).with_payload("target", int(args[3])))
        if not ev.success:
            print(f"[ERRO] {ev.error_message}")
            return
        res = ev.result
        if not res["reachable"]:
            print(f"Não há caminho de {args[2]} até {args[3]}")
        else:
            print(f"Caminho: {res['path']}")
            print(f"Distância: {res['dist']}")

    def cmd_topsort(self, args):
        if len(args) < 2: raise ValueError("Uso: topsort <id>")
        ev = self.bus.publish(Event(EventType.ALGO_TOPOLOGICAL_SORT).with_payload("graphId", args[1]))
        if not ev.success:
            print(f"[ERRO] {ev.error_message}")
            return
        if ev.result is None:
            print("Ordenação topológica impossível — o grafo contém ciclos.")
        else:
            print(f"Ordenação topológica: {ev.result}")

    def cmd_scc(self, args):
        if len(args) < 2: raise ValueError("Uso: scc <id>")
        ev = self.bus.publish(Event(EventType.ALGO_STRONGLY_CONNECTED).with_payload("graphId", args[1]))
        if not ev.success:
            print(f"[ERRO] {ev.error_message}")
            return
        sccs = ev.result
        print(f"Componentes Fortemente Conexos ({len(sccs)}):")
        for i, scc in enumerate(sccs, 1):
            print(f"  SCC {i}: {scc}")

    def cmd_metric(self, args, etype, label):
        if len(args) < 2: raise ValueError(f"Uso: {args[0]} <id>")
        gid = args[1]
        g = self.registry.get(gid)
        ev = self.bus.publish(Event(etype).with_payload("graphId", gid))
        if not ev.success:
            print(f"[ERRO] {ev.error_message}")
            return
        result = ev.result
        print(f"=== {label} — {gid} ===")
        sorted_res = sorted(result.items(), key=lambda x: x[1], reverse=True)
        for i, (v, val) in enumerate(sorted_res[:20]):
            print(f"  {g.get_vertex_label(v):<20} (v{v}): {val:.6f}")
        if len(sorted_res) > 20:
            print(f"  ... ({len(sorted_res) - 20} vértices omitidos)")

    def cmd_scalar_metric(self, args, etype, label):
        if len(args) < 2: raise ValueError(f"Uso: {args[0]} <id>")
        ev = self.bus.publish(Event(etype).with_payload("graphId", args[1]))
        if not ev.success:
            print(f"[ERRO] {ev.error_message}")
            return
        print(f"{label} ({args[1]}): {ev.result:.6f}")

    def cmd_communities(self, args):
        if len(args) < 2: raise ValueError("Uso: communities <id>")
        gid = args[1]
        g = self.registry.get(gid)
        ev = self.bus.publish(Event(EventType.METRIC_COMMUNITY_DETECTION).with_payload("graphId", gid))
        if not ev.success:
            print(f"[ERRO] {ev.error_message}")
            return
        result = ev.result
        by_comm = {}
        for v, c in result.items():
            if c not in by_comm: by_comm[c] = []
            by_comm[c].append(g.get_vertex_label(v))
        print(f"=== Comunidades Detectadas ({gid}) — {len(by_comm)} grupos ===")
        for c in sorted(by_comm.keys()):
            print(f"  Comunidade {c}: {by_comm[c]}")

    def cmd_bridging(self, args):
        if len(args) < 2: raise ValueError("Uso: bridging <id>")
        ev = self.bus.publish(Event(EventType.METRIC_BRIDGING_TIES).with_payload("graphId", args[1]))
        self.check_and_print(ev, f"Bridging Ties: {ev.result}")

    def cmd_export(self, args):
        if len(args) < 3: raise ValueError("Uso: export <id> <path>")
        ev = self.bus.publish(Event(EventType.GRAPH_EXPORT_GEPHI).with_payload("graphId", args[1]).with_payload("path", args[2]))
        self.check_and_print(ev, f"Exportado para {args[2]}")

    def cmd_load_csv(self, args):
        if len(args) < 2: raise ValueError("Uso: load-csv <path>")
        ev = self.bus.publish(Event(EventType.MINING_LOAD_CSV).with_payload("path", args[1]))
        self.check_and_print(ev, f"Carregadas {ev.result} interações.")

    def cmd_sample_csv(self, args):
        if len(args) < 2: raise ValueError("Uso: sample-csv <path>")
        CsvLoader.generate_sample_csv(args[1])
        print(f"CSV de exemplo gerado em: {args[1]}")

    def cmd_build_graphs(self, args):
        if len(args) < 2: raise ValueError("Uso: build-graphs <csvPath>")
        path = args[1]
        self.bus.publish(Event(EventType.MINING_LOAD_CSV).with_payload("path", path))
        self.bus.publish(Event(EventType.MINING_BUILD_GRAPH1_COMMENTS))
        self.bus.publish(Event(EventType.MINING_BUILD_GRAPH2_CLOSURES))
        self.bus.publish(Event(EventType.MINING_BUILD_GRAPH3_REVIEWS))
        self.bus.publish(Event(EventType.MINING_BUILD_INTEGRATED_GRAPH))
        print("Grafos 'graph1', 'graph2', 'graph3' e 'graph_integrated' construídos.")

    def cmd_show(self, args):
        if len(args) < 2: raise ValueError("Uso: show <id>")
        g = self.registry.get(args[1])
        from ..graph.abstract_graph import RepType
        if g.rep_type == RepType.LIST:
            print(g.to_list_string())
        else:
            print(g.to_matrix_string())

    def cmd_full_analysis(self, args):
        if len(args) < 2: raise ValueError("Uso: full-analysis <id>")
        gid = args[1]
        print(f"--- Análise Completa: {gid} ---")
        self.cmd_info(["info", gid])
        self.cmd_scalar_metric(["density", gid], EventType.METRIC_DENSITY, "Densidade")
        self.cmd_scalar_metric(["assortativity", gid], EventType.METRIC_ASSORTATIVITY, "Assortatividade")
        self.cmd_metric(["pagerank", gid], EventType.METRIC_PAGERANK, "PageRank (Top 5)")
        self.cmd_communities(["communities", gid])

    def check_and_print(self, ev, success_msg):
        if ev.success:
            print(success_msg)
        else:
            print(f"[ERRO] {ev.error_message}")
