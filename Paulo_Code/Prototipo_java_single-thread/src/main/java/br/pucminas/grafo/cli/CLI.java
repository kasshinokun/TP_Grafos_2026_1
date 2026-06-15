package br.pucminas.grafo.cli;

import br.pucminas.grafo.core.Application;
import br.pucminas.grafo.core.GraphRegistry;
import br.pucminas.grafo.events.Event;
import br.pucminas.grafo.events.EventBus;
import br.pucminas.grafo.events.EventType;
import br.pucminas.grafo.graph.AbstractGraph;
import br.pucminas.grafo.graph.AdjacencyListGraph;
import br.pucminas.grafo.graph.AdjacencyMatrixGraph;
import br.pucminas.grafo.graph.mining.CsvLoader;
import br.pucminas.grafo.graph.mining.Interaction;

import java.util.*;

/**
 * Interface de linha de comando interativa.
 *
 * <p>
 * ,0
 * Cada comando emite um {@link Event} ao {@link EventBus}, tornando
 * o CLI uma camada puramente de entrada/saída sobre a arquitetura EDA.
 * </p>
 *
 * <h3>Comandos disponíveis:</h3>
 * 
 * <pre>
 *   help                                    — lista comandos
 *   create &lt;id&gt; &lt;n&gt; [matrix|list]          — cria grafo
 *   list                                    — lista grafos registrados
 *   info &lt;id&gt;                               — informações do grafo
 *   add-edge &lt;id&gt; &lt;u&gt; &lt;v&gt; [peso]           — adiciona aresta
 *   rem-edge &lt;id&gt; &lt;u&gt; &lt;v&gt;                  — remove aresta
 *   has-edge &lt;id&gt; &lt;u&gt; &lt;v&gt;                  — verifica aresta
 *   degree &lt;id&gt; &lt;v&gt;                         — graus de entrada/saída
 *   connected &lt;id&gt;                          — é conectado?
 *   bfs &lt;id&gt; &lt;src&gt;                          — BFS a partir de src
 *   dfs &lt;id&gt; &lt;src&gt;                          — DFS a partir de src
 *   shortest &lt;id&gt; &lt;src&gt; &lt;dst&gt;              — caminho mais curto (Dijkstra)
 *   topsort &lt;id&gt;                            — ordenação topológica
 *   scc &lt;id&gt;                                — componentes fortemente conexos
 *   degree-centrality &lt;id&gt;                  — centralidade de grau
 *   betweenness &lt;id&gt;                        — centralidade de intermediação
 *   closeness &lt;id&gt;                          — centralidade de proximidade
 *   pagerank &lt;id&gt;                           — PageRank
 *   density &lt;id&gt;                            — densidade da rede
 *   clustering &lt;id&gt;                         — coef. de aglomeração
 *   assortativity &lt;id&gt;                      — assortatividade
 *   communities &lt;id&gt;                        — detecção de comunidades
 *   bridging &lt;id&gt;                           — bridging ties
 *   export &lt;id&gt; &lt;path&gt;                      — exporta GEPHI (.gexf)
 *   load-csv &lt;path&gt;                         — carrega interações de CSV
 *   sample-csv &lt;path&gt;                       — gera CSV de exemplo
 *   build-graphs &lt;csvPath&gt;                  — constrói os 4 grafos do trabalho
 *   show &lt;id&gt;                               — exibe estrutura do grafo
 *   full-analysis &lt;id&gt;                      — análise completa
 *   exit                                    — encerra
 * </pre>
 */
public class CLI {

    private final EventBus bus;
    private final GraphRegistry registry;
    private final Scanner scanner;

    public CLI(Application app) {
        this.bus = app.getBus();
        this.registry = app.getRegistry();
        this.scanner = new Scanner(System.in);
    }

    // ── Loop principal ─────────────────────────────────────────────────────

    public void run() {
        printBanner();
        while (true) {
            System.out.print("\n> ");
            String line = scanner.nextLine().trim();
            if (line.isEmpty())
                continue;
            if (!processCommand(line))
                break;
        }
        System.out.println("Encerrando. Até logo!");
    }

    // ── Despacho de comandos ───────────────────────────────────────────────

    private boolean processCommand(String line) {
        String[] args = line.split("\\s+");
        String cmd = args[0].toLowerCase();
        try {
            switch (cmd) {
                case "help" -> printHelp();
                case "exit", "quit" -> {
                    return false;
                }
                case "create" -> cmdCreate(args);
                case "list" -> cmdList();
                case "info" -> cmdInfo(args);
                case "add-edge" -> cmdAddEdge(args);
                case "rem-edge" -> cmdRemEdge(args);
                case "has-edge" -> cmdHasEdge(args);
                case "degree" -> cmdDegree(args);
                case "connected" -> cmdConnected(args);
                case "bfs" -> cmdBfs(args);
                case "dfs" -> cmdDfs(args);
                case "shortest" -> cmdShortest(args);
                case "topsort" -> cmdTopSort(args);
                case "scc" -> cmdSCC(args);
                case "degree-centrality" -> cmdMetric(args, EventType.METRIC_DEGREE_CENTRALITY, "Centralidade de Grau");
                case "betweenness" ->
                    cmdMetric(args, EventType.METRIC_BETWEENNESS_CENTRALITY, "Betweenness Centrality");
                case "closeness" -> cmdMetric(args, EventType.METRIC_CLOSENESS_CENTRALITY, "Closeness Centrality");
                case "pagerank" -> cmdMetric(args, EventType.METRIC_PAGERANK, "PageRank");
                case "density" -> cmdScalarMetric(args, EventType.METRIC_DENSITY, "Densidade");
                case "clustering" -> cmdMetric(args, EventType.METRIC_CLUSTERING_COEFFICIENT, "Coef. Aglomeração");
                case "assortativity" -> cmdScalarMetric(args, EventType.METRIC_ASSORTATIVITY, "Assortatividade");
                case "communities" -> cmdCommunities(args);
                case "bridging" -> cmdBridging(args);
                case "export" -> cmdExport(args);
                case "load-csv" -> cmdLoadCsv(args);
                case "sample-csv" -> cmdSampleCsv(args);
                case "build-graphs" -> cmdBuildGraphs(args);
                case "show" -> cmdShow(args);
                case "full-analysis" -> cmdFullAnalysis(args);
                default -> println("Comando desconhecido: " + cmd + ". Digite 'help'.");
            }
        } catch (Exception e) {
            println("[ERRO] " + e.getMessage());
        }
        return true;
    }

    // ── Implementação dos comandos ─────────────────────────────────────────

    private void cmdCreate(String[] args) {
        requireArgs(args, 3);
        String id = args[1];
        int n = Integer.parseInt(args[2]);
        String impl = args.length > 3 ? args[3] : "list";
        Event ev = bus.publish(new Event(EventType.GRAPH_CREATE)
                .with("graphId", id).with("numVertices", n).with("impl", impl));
        checkAndPrint(ev, "Grafo '" + id + "' criado (" + impl + ", " + n + " vértices).");
    }

    private void cmdList() {
        Set<String> ids = registry.listIds();
        if (ids.isEmpty()) {
            println("Nenhum grafo registrado.");
            return;
        }
        println("Grafos registrados:");
        ids.forEach(id -> {
            AbstractGraph g = registry.get(id);
            println("  • " + id + " — " + g);
        });
    }

    private void cmdInfo(String[] args) {
        requireArgs(args, 2);
        AbstractGraph g = registry.get(args[1]);
        println("=== " + args[1] + " ===");
        println("  Implementação : " + g.getRepType());
        println("  Vértices      : " + g.getVertexCount());
        println("  Arestas       : " + g.getEdgeCount());
        println("  Conectado     : " + g.isConnected());
        println("  Grafo vazio   : " + g.isEmptyGraph());
        println("  Grafo completo: " + g.isCompleteGraph());
    }

    private void cmdAddEdge(String[] args) {
        requireArgs(args, 4);
        String id = args[1];
        int u = Integer.parseInt(args[2]);
        int v = Integer.parseInt(args[3]);
        Event ev = bus.publish(new Event(EventType.GRAPH_ADD_EDGE)
                .with("graphId", id).with("u", u).with("v", v));
        if (args.length > 4) {
            double w = Double.parseDouble(args[4]);
            bus.publish(new Event(EventType.GRAPH_SET_EDGE_WEIGHT)
                    .with("graphId", id).with("u", u).with("v", v).with("weight", w));
        }
        checkAndPrint(ev, "Aresta " + u + " → " + v + " adicionada.");
    }

    private void cmdRemEdge(String[] args) {
        requireArgs(args, 4);
        Event ev = bus.publish(new Event(EventType.GRAPH_REMOVE_EDGE)
                .with("graphId", args[1]).with("u", Integer.parseInt(args[2])).with("v", Integer.parseInt(args[3])));
        checkAndPrint(ev, "Aresta removida.");
    }

    private void cmdHasEdge(String[] args) {
        requireArgs(args, 4);
        Event ev = bus.publish(new Event(EventType.GRAPH_HAS_EDGE)
                .with("graphId", args[1]).with("u", Integer.parseInt(args[2])).with("v", Integer.parseInt(args[3])));
        if (ev.isSuccess())
            println("hasEdge(" + args[2] + "," + args[3] + ") = " + ev.getResult());
        else
            println("[ERRO] " + ev.getErrorMessage());
    }

    private void cmdDegree(String[] args) {
        requireArgs(args, 3);
        String id = args[1];
        int v = Integer.parseInt(args[2]);
        Event in = bus.publish(new Event(EventType.GRAPH_IN_DEGREE).with("graphId", id).with("v", v));
        Event out = bus.publish(new Event(EventType.GRAPH_OUT_DEGREE).with("graphId", id).with("v", v));
        println("Vértice " + v + " — in-degree: " + in.getResult() + ", out-degree: " + out.getResult());
    }

    private void cmdConnected(String[] args) {
        requireArgs(args, 2);
        Event ev = bus.publish(new Event(EventType.GRAPH_IS_CONNECTED).with("graphId", args[1]));
        checkAndPrint(ev, "Conectado: " + ev.getResult());
    }

    private void cmdBfs(String[] args) {
        requireArgs(args, 3);
        Event ev = bus.publish(new Event(EventType.ALGO_BFS)
                .with("graphId", args[1]).with("source", Integer.parseInt(args[2])));
        checkAndPrint(ev, "BFS: " + ev.getResult());
    }

    private void cmdDfs(String[] args) {
        requireArgs(args, 3);
        Event ev = bus.publish(new Event(EventType.ALGO_DFS)
                .with("graphId", args[1]).with("source", Integer.parseInt(args[2])));
        checkAndPrint(ev, "DFS: " + ev.getResult());
    }

    @SuppressWarnings("unchecked")
    private void cmdShortest(String[] args) {
        requireArgs(args, 4);
        Event ev = bus.publish(new Event(EventType.ALGO_SHORTEST_PATH)
                .with("graphId", args[1])
                .with("source", Integer.parseInt(args[2]))
                .with("target", Integer.parseInt(args[3])));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        Map<String, Object> res = ev.getResult();
        if (!(Boolean) res.get("reachable")) {
            println("Não há caminho de " + args[2] + " até " + args[3]);
        } else {
            println("Caminho: " + res.get("path"));
            println("Distância: " + res.get("dist"));
        }
    }

    private void cmdTopSort(String[] args) {
        requireArgs(args, 2);
        Event ev = bus.publish(new Event(EventType.ALGO_TOPOLOGICAL_SORT).with("graphId", args[1]));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        List<?> r = ev.getResult();
        if (r == null)
            println("Ordenação topológica impossível — o grafo contém ciclos.");
        else
            println("Ordenação topológica: " + r);
    }

    private void cmdSCC(String[] args) {
        requireArgs(args, 2);
        Event ev = bus.publish(new Event(EventType.ALGO_STRONGLY_CONNECTED).with("graphId", args[1]));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        List<?> sccs = ev.getResult();
        println("Componentes Fortemente Conexos (" + sccs.size() + "):");
        int i = 1;
        for (Object scc : sccs)
            println("  SCC " + i++ + ": " + scc);
    }

    @SuppressWarnings("unchecked")
    private void cmdMetric(String[] args, EventType type, String label) {
        requireArgs(args, 2);
        AbstractGraph g = registry.get(args[1]);
        Event ev = bus.publish(new Event(type).with("graphId", args[1]));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        Map<Integer, Double> result = ev.getResult();
        println("=== " + label + " — " + args[1] + " ===");
        result.entrySet().stream()
                .sorted(Map.Entry.<Integer, Double>comparingByValue().reversed())
                .limit(20)
                .forEach(e -> println(String.format("  %-20s (v%d): %.6f",
                        g.getVertexLabel(e.getKey()), e.getKey(), e.getValue())));
        if (result.size() > 20)
            println("  ... (" + (result.size() - 20) + " vértices omitidos)");
    }

    private void cmdScalarMetric(String[] args, EventType type, String label) {
        requireArgs(args, 2);
        Event ev = bus.publish(new Event(type).with("graphId", args[1]));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        println(label + " (" + args[1] + "): " + String.format("%.6f", (Double) ev.getResult()));
    }

    @SuppressWarnings("unchecked")
    private void cmdCommunities(String[] args) {
        requireArgs(args, 2);
        AbstractGraph g = registry.get(args[1]);
        Event ev = bus.publish(new Event(EventType.METRIC_COMMUNITY_DETECTION).with("graphId", args[1]));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        Map<Integer, Integer> result = ev.getResult();

        Map<Integer, List<String>> byCommunity = new TreeMap<>();
        result.forEach((v, c) -> byCommunity.computeIfAbsent(c, k -> new ArrayList<>())
                .add(g.getVertexLabel(v)));
        println("=== Comunidades Detectadas (" + args[1] + ") — " + byCommunity.size() + " grupos ===");
        byCommunity.forEach((c, members) -> println("  Comunidade " + c + ": " + members));
    }

    @SuppressWarnings("unchecked")
    private void cmdBridging(String[] args) {
        requireArgs(args, 2);
        AbstractGraph g = registry.get(args[1]);
        Event ev = bus.publish(new Event(EventType.METRIC_BRIDGING_TIES).with("graphId", args[1]));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        List<Integer> bridges = ev.getResult();
        println("=== Bridging Ties (" + args[1] + ") — " + bridges.size() + " vértices ===");
        bridges.forEach(v -> println("  • " + g.getVertexLabel(v) + " (v" + v + ")"));
    }

    private void cmdExport(String[] args) {
        requireArgs(args, 3);
        Event ev = bus.publish(new Event(EventType.GRAPH_EXPORT_GEPHI)
                .with("graphId", args[1]).with("path", args[2]));
        checkAndPrint(ev, "Exportado para: " + args[2] + ".gexf");
    }

    @SuppressWarnings("unchecked")
    private void cmdLoadCsv(String[] args) {
        requireArgs(args, 2);
        Event ev = bus.publish(new Event(EventType.MINING_LOAD_CSV).with("path", args[1]));
        if (!ev.isSuccess()) {
            println("[ERRO] " + ev.getErrorMessage());
            return;
        }
        List<Interaction> list = ev.getResult();
        println("CSV carregado: " + list.size() + " interações.");
    }

    private void cmdSampleCsv(String[] args) {
        requireArgs(args, 2);
        try {
            CsvLoader.generateSampleCsv(args[1]);
            println("CSV de exemplo gerado em: " + args[1]);
        } catch (Exception e) {
            println("[ERRO] " + e.getMessage());
        }
    }

    @SuppressWarnings("unchecked")
    private void cmdBuildGraphs(String[] args) {
        requireArgs(args, 2);
        // 1. Carrega CSV
        Event loadEv = bus.publish(new Event(EventType.MINING_LOAD_CSV).with("path", args[1]));
        if (!loadEv.isSuccess()) {
            println("[ERRO] " + loadEv.getErrorMessage());
            return;
        }
        List<Interaction> interactions = loadEv.getResult();
        println("Interações carregadas: " + interactions.size());

        // 2. Constrói os 4 grafos via eventos
        String[] graphIds = { "graph1", "graph2", "graph3", "graph_integrated" };
        EventType[] types = {
                EventType.MINING_BUILD_GRAPH1_COMMENTS,
                EventType.MINING_BUILD_GRAPH2_CLOSURES,
                EventType.MINING_BUILD_GRAPH3_REVIEWS,
                EventType.MINING_BUILD_INTEGRATED_GRAPH
        };
        String[] labels = {
                "Grafo 1 (comentários)", "Grafo 2 (fechamentos)",
                "Grafo 3 (revisões/merges)", "Grafo Integrado"
        };
        for (int i = 0; i < types.length; i++) {
            Event ev = bus.publish(new Event(types[i]).with("interactions", interactions));
            if (ev.isSuccess()) {
                AbstractGraph g = registry.get(graphIds[i]);
                println("  ✓ " + labels[i] + ": V=" + g.getVertexCount() + ", E=" + g.getEdgeCount());
            } else {
                println("  ✗ " + labels[i] + ": " + ev.getErrorMessage());
            }
        }
    }

    private void cmdShow(String[] args) {
        requireArgs(args, 2);
        AbstractGraph g = registry.get(args[1]);
        if (g instanceof AdjacencyMatrixGraph m)
            println(m.toMatrixString());
        else if (g instanceof AdjacencyListGraph l)
            println(l.toListString());
        else
            println(g.toString());
    }

    private void cmdFullAnalysis(String[] args) {
        requireArgs(args, 2);
        String id = args[1];
        println("\n╔══════════════════════════════════════════╗");
        println("║      ANÁLISE COMPLETA: " + id);
        println("╚══════════════════════════════════════════╝");
        cmdInfo(args);
        println("\n── Centralidade de Grau ─────────────────────");
        cmdMetric(args, EventType.METRIC_DEGREE_CENTRALITY, "Degree Centrality");
        println("\n── Betweenness ──────────────────────────────");
        cmdMetric(args, EventType.METRIC_BETWEENNESS_CENTRALITY, "Betweenness");
        println("\n── Closeness ────────────────────────────────");
        cmdMetric(args, EventType.METRIC_CLOSENESS_CENTRALITY, "Closeness");
        println("\n── PageRank ─────────────────────────────────");
        cmdMetric(args, EventType.METRIC_PAGERANK, "PageRank");
        println("\n── Densidade ────────────────────────────────");
        cmdScalarMetric(args, EventType.METRIC_DENSITY, "Densidade");
        println("\n── Assortatividade ──────────────────────────");
        cmdScalarMetric(args, EventType.METRIC_ASSORTATIVITY, "Assortatividade");
        println("\n── Coef. de Aglomeração ─────────────────────");
        cmdMetric(args, EventType.METRIC_CLUSTERING_COEFFICIENT, "Clustering");
        println("\n── Comunidades ──────────────────────────────");
        cmdCommunities(args);
        println("\n── Bridging Ties ────────────────────────────");
        cmdBridging(args);
    }

    // ── Utilidades de display ──────────────────────────────────────────────

    private void checkAndPrint(Event ev, String successMsg) {
        if (ev.isSuccess())
            println(successMsg);
        else
            println("[ERRO] " + ev.getErrorMessage());
    }

    private void println(String s) {
        System.out.println(s);
    }

    private void requireArgs(String[] args, int min) {
        if (args.length < min)
            throw new IllegalArgumentException("Argumentos insuficientes. Digite 'help'.");
    }

    private void printBanner() {
        System.out.println("""
                ╔══════════════════════════════════════════════════╗
                ║   Ferramenta de Análise de Grafos — PUC Minas   ║
                ║   Teoria de Grafos e Computabilidade  2025/2    ║
                ║   Arquitetura: Event-Driven (EDA)               ║
                ╚══════════════════════════════════════════════════╝
                Digite 'help' para ver os comandos disponíveis.
                """);
    }

    private void printHelp() {
        System.out.println("""
                ══ GERENCIAMENTO DE GRAFO ══════════════════════════════════════
                 create <id> <n> [matrix|list]    cria grafo com n vértices
                 list                             lista grafos registrados
                 info <id>                        informações do grafo
                 add-edge <id> <u> <v> [peso]     adiciona aresta u→v
                 rem-edge <id> <u> <v>            remove aresta u→v
                 has-edge <id> <u> <v>            verifica aresta u→v
                 degree <id> <v>                  graus de entrada/saída
                 connected <id>                   é fracamente conectado?
                 show <id>                        exibe matriz/lista de adj.

                ══ ALGORITMOS ══════════════════════════════════════════════════
                 bfs <id> <src>                   BFS a partir de src
                 dfs <id> <src>                   DFS a partir de src
                 shortest <id> <src> <dst>        caminho mais curto (Dijkstra)
                 topsort <id>                     ordenação topológica (Kahn)
                 scc <id>                         componentes fortemente conexos

                ══ MÉTRICAS DE CENTRALIDADE ════════════════════════════════════
                 degree-centrality <id>           centralidade de grau
                 betweenness <id>                 betweenness centrality
                 closeness <id>                   closeness centrality
                 pagerank <id>                    PageRank

                ══ MÉTRICAS DE ESTRUTURA ═══════════════════════════════════════
                 density <id>                     densidade da rede
                 clustering <id>                  coef. de aglomeração
                 assortativity <id>               assortatividade

                ══ MÉTRICAS DE COMUNIDADE ══════════════════════════════════════
                 communities <id>                 detecção de comunidades
                 bridging <id>                    bridging ties

                ══ EXPORTAÇÃO ══════════════════════════════════════════════════
                 export <id> <path>               exporta GEPHI (.gexf)

                ══ MINERAÇÃO DE DADOS ══════════════════════════════════════════
                 sample-csv <path>                gera CSV de exemplo
                 load-csv <path>                  carrega interações de CSV
                 build-graphs <csvPath>           constrói os 4 grafos do trabalho

                ══ ANÁLISE COMPLETA ════════════════════════════════════════════
                 full-analysis <id>               todas as métricas de uma vez

                 exit / quit                      encerra o programa
                """);
    }
}
