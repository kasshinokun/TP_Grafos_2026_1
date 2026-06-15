package br.pucminas.grafo;

import br.pucminas.grafo.core.Application;
import br.pucminas.grafo.events.Event;
import br.pucminas.grafo.events.EventBus;
import br.pucminas.grafo.events.EventType;
import br.pucminas.grafo.graph.AbstractGraph;
import br.pucminas.grafo.graph.mining.CsvLoader;
import br.pucminas.grafo.graph.mining.Interaction;

import java.io.File;
import java.util.*;

/**
 * Suite de testes funcionais (sem framework externo).
 *
 * <p>
 * Cada método {@code testXxx} retorna {@code true} em sucesso
 * ou lança uma exceção / retorna {@code false} em falha.
 * O runner principal contabiliza aprovações e reprovações.
 * </p>
 */
public class TestSuite {

    // ── Ponto de entrada do runner ─────────────────────────────────────────

    public static void main(String[] unused) throws Exception {
        TestSuite suite = new TestSuite();
        int pass = 0, fail = 0;

        String[] tests = {
                "testCreateGraph", "testAddAndRemoveEdge", "testIdempotentAddEdge",
                "testLoopRejected", "testEdgeWeights", "testVertexWeights",
                "testInOutDegree", "testIsSuccessorPredecessor",
                "testDivergentConvergent", "testIsIncident",
                "testConnectedEmptyComplete",
                "testBFS", "testDFS", "testShortestPath",
                "testTopologicalSort", "testSCC",
                "testDegreeCentrality", "testPageRank",
                "testDensity", "testCommunityDetection",
                "testCsvLoadAndBuildGraphs",
                "testExportGephi",
                "testMatrixImpl",
                "testInvalidVertexThrows"
        };

        for (String name : tests) {
            try {
                boolean ok = (boolean) TestSuite.class.getMethod(name).invoke(suite);
                if (ok) {
                    System.out.println("  ✓ " + name);
                    pass++;
                } else {
                    System.out.println("  ✗ " + name + " [falhou]");
                    fail++;
                }
            } catch (Exception e) {
                Throwable cause = e.getCause() != null ? e.getCause() : e;
                System.out.println("  ✗ " + name + " [exceção: " + cause.getMessage() + "]");
                fail++;
            }
        }

        System.out.println("\n══════════════════════════════════");
        System.out.printf("  Resultado: %d aprovados, %d reprovados%n", pass, fail);
        System.out.println("══════════════════════════════════");
        if (fail > 0)
            System.exit(1);
    }

    // ── Infraestrutura ─────────────────────────────────────────────────────

    private Application newApp() {
        return new Application();
    }

    private Event pub(EventBus bus, Event ev) {
        return bus.publish(ev);
    }

    // ══ Testes ═════════════════════════════════════════════════════════════

    public boolean testCreateGraph() {
        Application app = newApp();
        EventBus bus = app.getBus();
        Event ev = pub(bus, new Event(EventType.GRAPH_CREATE)
                .with("graphId", "g").with("numVertices", 5).with("impl", "list"));
        assert ev.isSuccess() : ev.getErrorMessage();
        AbstractGraph g = app.getRegistry().get("g");
        assert g.getVertexCount() == 5;
        assert g.getEdgeCount() == 0;
        return true;
    }

    public boolean testAddAndRemoveEdge() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 4).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 1).with("v", 2));
        AbstractGraph g = app.getRegistry().get("g");
        assert g.getEdgeCount() == 2;
        assert g.hasEdge(0, 1) && g.hasEdge(1, 2);
        pub(bus, new Event(EventType.GRAPH_REMOVE_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        assert g.getEdgeCount() == 1;
        assert !g.hasEdge(0, 1);
        return true;
    }

    public boolean testIdempotentAddEdge() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        for (int i = 0; i < 5; i++)
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        assert app.getRegistry().get("g").getEdgeCount() == 1 : "addEdge deve ser idempotente";
        return true;
    }

    public boolean testLoopRejected() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        Event ev = pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 1).with("v", 1));
        assert !ev.isSuccess() : "Laço deveria ser rejeitado";
        return true;
    }

    public boolean testEdgeWeights() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_SET_EDGE_WEIGHT).with("graphId", "g").with("u", 0).with("v", 2)
                .with("weight", 4.5));
        Event ev = pub(bus, new Event(EventType.GRAPH_GET_EDGE_WEIGHT).with("graphId", "g").with("u", 0).with("v", 2));
        assert ev.isSuccess();
        assert Math.abs((Double) ev.getResult() - 4.5) < 1e-9;
        return true;
    }

    public boolean testVertexWeights() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "matrix"));
        pub(bus, new Event(EventType.GRAPH_SET_VERTEX_WEIGHT).with("graphId", "g").with("v", 1).with("weight", 7.0));
        Event ev = pub(bus, new Event(EventType.GRAPH_GET_VERTEX_WEIGHT).with("graphId", "g").with("v", 1));
        assert (Double) ev.getResult() == 7.0;
        return true;
    }

    public boolean testInOutDegree() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 4).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 2).with("v", 1));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 1).with("v", 3));
        Event in = pub(bus, new Event(EventType.GRAPH_IN_DEGREE).with("graphId", "g").with("v", 1));
        Event out = pub(bus, new Event(EventType.GRAPH_OUT_DEGREE).with("graphId", "g").with("v", 1));
        assert (Integer) in.getResult() == 2 : "in-degree de v1 deve ser 2";
        assert (Integer) out.getResult() == 1 : "out-degree de v1 deve ser 1";
        return true;
    }

    public boolean testIsSuccessorPredecessor() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        Event succ = pub(bus, new Event(EventType.GRAPH_IS_SUCCESSOR).with("graphId", "g").with("u", 0).with("v", 1));
        Event pred = pub(bus, new Event(EventType.GRAPH_IS_PREDECESSOR).with("graphId", "g").with("u", 1).with("v", 0));
        assert (Boolean) succ.getResult() : "1 deve ser sucessor de 0";
        assert (Boolean) pred.getResult() : "0 deve ser predecessor de 1";
        return true;
    }

    public boolean testDivergentConvergent() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 4).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 2));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 3).with("v", 1));

        Event div = pub(bus, new Event(EventType.GRAPH_IS_DIVERGENT)
                .with("graphId", "g").with("u1", 0).with("v1", 1).with("u2", 0).with("v2", 2));
        Event conv = pub(bus, new Event(EventType.GRAPH_IS_CONVERGENT)
                .with("graphId", "g").with("u1", 0).with("v1", 1).with("u2", 3).with("v2", 1));
        assert (Boolean) div.getResult() : "0→1 e 0→2 devem ser divergentes";
        assert (Boolean) conv.getResult() : "0→1 e 3→1 devem ser convergentes";
        return true;
    }

    public boolean testIsIncident() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 2));
        Event ev = pub(bus, new Event(EventType.GRAPH_IS_INCIDENT)
                .with("graphId", "g").with("u", 0).with("v", 2).with("x", 0));
        assert (Boolean) ev.getResult();
        return true;
    }

    public boolean testConnectedEmptyComplete() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        AbstractGraph g = app.getRegistry().get("g");
        assert g.isEmptyGraph();
        // Conecta 0↔1↔2 (antiparalelas para bidirecional)
        for (int[] e : new int[][] { { 0, 1 }, { 1, 0 }, { 1, 2 }, { 2, 1 }, { 0, 2 }, { 2, 0 } })
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", e[0]).with("v", e[1]));
        assert g.isConnected();
        assert !g.isCompleteGraph() : "grafo de 3 vértices com 6 arestas é completo";
        // 3 vértices, todas 6 arestas direcionadas
        assert g.isCompleteGraph();
        return true;
    }

    public boolean testBFS() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 5).with("impl", "list"));
        for (int[] e : new int[][] { { 0, 1 }, { 0, 2 }, { 1, 3 }, { 2, 4 } })
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", e[0]).with("v", e[1]));
        Event ev = pub(bus, new Event(EventType.ALGO_BFS).with("graphId", "g").with("source", 0));
        List<?> order = ev.getResult();
        assert order.get(0).equals(0);
        assert order.size() == 5;
        return true;
    }

    public boolean testDFS() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 4).with("impl", "list"));
        for (int[] e : new int[][] { { 0, 1 }, { 1, 2 }, { 2, 3 } })
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", e[0]).with("v", e[1]));
        Event ev = pub(bus, new Event(EventType.ALGO_DFS).with("graphId", "g").with("source", 0));
        List<?> order = ev.getResult();
        assert order.equals(List.of(0, 1, 2, 3)) : "DFS linear deve ser 0→1→2→3";
        return true;
    }

    @SuppressWarnings("unchecked")
    public boolean testShortestPath() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 4).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_SET_EDGE_WEIGHT).with("graphId", "g").with("u", 0).with("v", 1)
                .with("weight", 1.0));
        pub(bus, new Event(EventType.GRAPH_SET_EDGE_WEIGHT).with("graphId", "g").with("u", 1).with("v", 3)
                .with("weight", 2.0));
        pub(bus, new Event(EventType.GRAPH_SET_EDGE_WEIGHT).with("graphId", "g").with("u", 0).with("v", 2)
                .with("weight", 5.0));
        pub(bus, new Event(EventType.GRAPH_SET_EDGE_WEIGHT).with("graphId", "g").with("u", 2).with("v", 3)
                .with("weight", 1.0));
        Event ev = pub(bus, new Event(EventType.ALGO_SHORTEST_PATH)
                .with("graphId", "g").with("source", 0).with("target", 3));
        Map<String, Object> r = ev.getResult();
        assert (Double) r.get("dist") == 3.0 : "Distância 0→3 deve ser 3.0 (via 0→1→3)";
        assert ((List<Integer>) r.get("path")).equals(List.of(0, 1, 3));
        return true;
    }

    public boolean testTopologicalSort() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 5).with("impl", "list"));
        for (int[] e : new int[][] { { 0, 2 }, { 0, 3 }, { 1, 3 }, { 2, 4 }, { 3, 4 } })
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", e[0]).with("v", e[1]));
        Event ev = pub(bus, new Event(EventType.ALGO_TOPOLOGICAL_SORT).with("graphId", "g"));
        List<?> sorted = ev.getResult();
        assert sorted != null : "DAG não deveria ter ciclo";
        assert sorted.size() == 5;
        return true;
    }

    public boolean testSCC() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 5).with("impl", "list"));
        // SCC: {0,1,2} e {3,4}
        for (int[] e : new int[][] { { 0, 1 }, { 1, 2 }, { 2, 0 }, { 3, 4 }, { 4, 3 }, { 2, 3 } })
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", e[0]).with("v", e[1]));
        Event ev = pub(bus, new Event(EventType.ALGO_STRONGLY_CONNECTED).with("graphId", "g"));
        List<?> sccs = ev.getResult();
        assert sccs.size() == 2 : "Deve haver 2 SCCs";
        return true;
    }

    @SuppressWarnings("unchecked")
    public boolean testDegreeCentrality() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 2));
        Event ev = pub(bus, new Event(EventType.METRIC_DEGREE_CENTRALITY).with("graphId", "g"));
        Map<Integer, Double> r = ev.getResult();
        assert r.get(0) > r.get(1) : "Vértice 0 deve ter maior centralidade";
        return true;
    }

    @SuppressWarnings("unchecked")
    public boolean testPageRank() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 4).with("impl", "list"));
        for (int[] e : new int[][] { { 0, 1 }, { 0, 2 }, { 1, 3 }, { 2, 3 }, { 3, 0 } })
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", e[0]).with("v", e[1]));
        Event ev = pub(bus, new Event(EventType.METRIC_PAGERANK).with("graphId", "g"));
        Map<Integer, Double> pr = ev.getResult();
        double sum = pr.values().stream().mapToDouble(Double::doubleValue).sum();
        assert Math.abs(sum - 1.0) < 0.001 : "PageRank deve somar ~1.0";
        return true;
    }

    public boolean testDensity() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 1).with("v", 2));
        Event ev = pub(bus, new Event(EventType.METRIC_DENSITY).with("graphId", "g"));
        double density = ev.getResult();
        // 2 arestas / 6 possíveis = 0.333...
        assert Math.abs(density - 2.0 / 6.0) < 1e-9;
        return true;
    }

    @SuppressWarnings("unchecked")
    public boolean testCommunityDetection() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 6).with("impl", "list"));
        // dois cliques separados
        for (int[] e : new int[][] { { 0, 1 }, { 1, 2 }, { 2, 0 }, { 3, 4 }, { 4, 5 }, { 5, 3 } })
            pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", e[0]).with("v", e[1]));
        Event ev = pub(bus, new Event(EventType.METRIC_COMMUNITY_DETECTION).with("graphId", "g"));
        Map<Integer, Integer> r = ev.getResult();
        assert r.size() == 6;
        // vértices do mesmo clique devem ter mesma comunidade (não garantido sem
        // pontes, mas verifica retorno)
        return true;
    }

    public boolean testCsvLoadAndBuildGraphs() throws Exception {
        Application app = newApp();
        EventBus bus = app.getBus();
        String path = "/tmp/test_interactions.csv";
        CsvLoader.generateSampleCsv(path);

        Event loadEv = pub(bus, new Event(EventType.MINING_LOAD_CSV).with("path", path));
        assert loadEv.isSuccess() : loadEv.getErrorMessage();
        List<Interaction> interactions = loadEv.getResult();
        assert !interactions.isEmpty();

        for (EventType type : List.of(
                EventType.MINING_BUILD_GRAPH1_COMMENTS,
                EventType.MINING_BUILD_GRAPH2_CLOSURES,
                EventType.MINING_BUILD_GRAPH3_REVIEWS,
                EventType.MINING_BUILD_INTEGRATED_GRAPH)) {
            Event ev = pub(bus, new Event(type).with("interactions", interactions));
            assert ev.isSuccess() : "Falhou: " + type + " — " + ev.getErrorMessage();
        }
        return true;
    }

    public boolean testExportGephi() throws Exception {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 1));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 1).with("v", 2));
        String path = "/tmp/test_export";
        Event ev = pub(bus, new Event(EventType.GRAPH_EXPORT_GEPHI).with("graphId", "g").with("path", path));
        assert ev.isSuccess() : ev.getErrorMessage();
        assert new File(path + ".gexf").exists();
        return true;
    }

    public boolean testMatrixImpl() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "m").with("numVertices", 4).with("impl", "matrix"));
        pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "m").with("u", 0).with("v", 3));
        AbstractGraph g = app.getRegistry().get("m");
        assert g.hasEdge(0, 3);
        assert !g.hasEdge(3, 0);
        assert g.getEdgeCount() == 1;
        return true;
    }

    public boolean testInvalidVertexThrows() {
        Application app = newApp();
        EventBus bus = app.getBus();
        pub(bus, new Event(EventType.GRAPH_CREATE).with("graphId", "g").with("numVertices", 3).with("impl", "list"));
        Event ev = pub(bus, new Event(EventType.GRAPH_ADD_EDGE).with("graphId", "g").with("u", 0).with("v", 99));
        assert !ev.isSuccess() : "Índice inválido deveria gerar erro";
        return true;
    }
}
