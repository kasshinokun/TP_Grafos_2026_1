package br.pucminas.grafo.handlers;

import br.pucminas.grafo.core.GraphRegistry;
import br.pucminas.grafo.events.Event;
import br.pucminas.grafo.events.EventBus;
import br.pucminas.grafo.events.EventType;
import br.pucminas.grafo.graph.AbstractGraph;

import java.util.*;

/**
 * Handler de métricas de redes complexas (Etapa 3 do trabalho).
 *
 * <h3>Métricas de Centralidade:</h3>
 * <ul>
 * <li>METRIC_DEGREE_CENTRALITY → result: Map(vertexIdx → double)</li>
 * <li>METRIC_BETWEENNESS_CENTRALITY → result: Map(vertexIdx → double)</li>
 * <li>METRIC_CLOSENESS_CENTRALITY → result: Map(vertexIdx → double)</li>
 * <li>METRIC_PAGERANK → result: Map(vertexIdx → double)</li>
 * </ul>
 * <h3>Métricas de Estrutura:</h3>
 * <ul>
 * <li>METRIC_DENSITY → result: Double</li>
 * <li>METRIC_CLUSTERING_COEFFICIENT → result: Map(vertexIdx → double)</li>
 * <li>METRIC_ASSORTATIVITY → result: Double</li>
 * </ul>
 * <h3>Métricas de Comunidade:</h3>
 * <ul>
 * <li>METRIC_COMMUNITY_DETECTION → result: Map(vertexIdx → communityId)</li>
 * <li>METRIC_BRIDGING_TIES → result: List(vertexIdx) pontes entre
 * comunidades</li>
 * </ul>
 * Todos os eventos exigem payload: graphId.
 */
public class MetricsHandler {

    private final GraphRegistry registry;

    public MetricsHandler(GraphRegistry registry) {
        this.registry = registry;
    }

    public void registerAll(EventBus bus) {
        bus.subscribe(EventType.METRIC_DEGREE_CENTRALITY, this::onDegreeCentrality);
        bus.subscribe(EventType.METRIC_BETWEENNESS_CENTRALITY, this::onBetweenness);
        bus.subscribe(EventType.METRIC_CLOSENESS_CENTRALITY, this::onCloseness);
        bus.subscribe(EventType.METRIC_PAGERANK, this::onPageRank);
        bus.subscribe(EventType.METRIC_DENSITY, this::onDensity);
        bus.subscribe(EventType.METRIC_CLUSTERING_COEFFICIENT, this::onClustering);
        bus.subscribe(EventType.METRIC_ASSORTATIVITY, this::onAssortativity);
        bus.subscribe(EventType.METRIC_COMMUNITY_DETECTION, this::onCommunityDetection);
        bus.subscribe(EventType.METRIC_BRIDGING_TIES, this::onBridgingTies);
    }

    // ── Grau (degree centrality) ────────────────────────────────────────────

    private void onDegreeCentrality(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        Map<Integer, Double> result = new LinkedHashMap<>();
        double norm = n > 1 ? (n - 1.0) : 1.0;
        for (int v = 0; v < n; v++) {
            double deg = g.getVertexInDegree(v) + g.getVertexOutDegree(v);
            result.put(v, deg / norm);
        }
        ev.setResult(result);
    }

    // ── Betweenness (Brandes O(VE)) ────────────────────────────────────────

    private void onBetweenness(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        double[] cb = new double[n];

        for (int s = 0; s < n; s++) {
            Deque<Integer> stack = new ArrayDeque<>();
            List<List<Integer>> pred = new ArrayList<>();
            for (int i = 0; i < n; i++)
                pred.add(new ArrayList<>());

            double[] sigma = new double[n];
            double[] dist = new double[n];
            Arrays.fill(sigma, 0);
            Arrays.fill(dist, -1);
            sigma[s] = 1;
            dist[s] = 0;

            Queue<Integer> queue = new LinkedList<>();
            queue.add(s);
            while (!queue.isEmpty()) {
                int v = queue.poll();
                stack.push(v);
                for (int w = 0; w < n; w++) {
                    if (!g.hasEdge(v, w))
                        continue;
                    if (dist[w] < 0) {
                        queue.add(w);
                        dist[w] = dist[v] + 1;
                    }
                    if (dist[w] == dist[v] + 1) {
                        sigma[w] += sigma[v];
                        pred.get(w).add(v);
                    }
                }
            }
            double[] delta = new double[n];
            while (!stack.isEmpty()) {
                int w = stack.pop();
                for (int v : pred.get(w))
                    delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w]);
                if (w != s)
                    cb[w] += delta[w];
            }
        }

        double norm = (n > 2) ? ((n - 1.0) * (n - 2.0)) : 1.0;
        Map<Integer, Double> result = new LinkedHashMap<>();
        for (int v = 0; v < n; v++)
            result.put(v, cb[v] / norm);
        ev.setResult(result);
    }

    // ── Closeness ──────────────────────────────────────────────────────────

    private void onCloseness(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        Map<Integer, Double> result = new LinkedHashMap<>();

        for (int src = 0; src < n; src++) {
            double[] dist = bfsDistances(g, src);
            double sum = 0;
            int reachable = 0;
            for (int v = 0; v < n; v++)
                if (v != src && dist[v] < Double.MAX_VALUE) {
                    sum += dist[v];
                    reachable++;
                }
            result.put(src, reachable > 0 ? reachable / sum : 0.0);
        }
        ev.setResult(result);
    }

    private double[] bfsDistances(AbstractGraph g, int src) {
        int n = g.getVertexCount();
        double[] dist = new double[n];
        Arrays.fill(dist, Double.MAX_VALUE);
        dist[src] = 0;
        Queue<Integer> q = new LinkedList<>();
        q.add(src);
        while (!q.isEmpty()) {
            int u = q.poll();
            for (int v = 0; v < n; v++)
                if (g.hasEdge(u, v) && dist[v] == Double.MAX_VALUE) {
                    dist[v] = dist[u] + 1;
                    q.add(v);
                }
        }
        return dist;
    }

    // ── PageRank ───────────────────────────────────────────────────────────

    private void onPageRank(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        double d = 0.85; // fator de amortecimento
        int iter = 100; // iterações
        double eps = 1e-6;

        double[] pr = new double[n];
        double[] nxt = new double[n];
        Arrays.fill(pr, 1.0 / n);

        for (int it = 0; it < iter; it++) {
            Arrays.fill(nxt, (1 - d) / n);
            for (int u = 0; u < n; u++) {
                int out = g.getVertexOutDegree(u);
                if (out == 0) { // dangling node — distribui para todos
                    double share = pr[u] / n;
                    for (int v = 0; v < n; v++)
                        nxt[v] += d * share;
                } else {
                    for (int v = 0; v < n; v++)
                        if (g.hasEdge(u, v))
                            nxt[v] += d * pr[u] / out;
                }
            }
            double diff = 0;
            for (int v = 0; v < n; v++)
                diff += Math.abs(nxt[v] - pr[v]);
            System.arraycopy(nxt, 0, pr, 0, n);
            if (diff < eps)
                break;
        }

        Map<Integer, Double> result = new LinkedHashMap<>();
        for (int v = 0; v < n; v++)
            result.put(v, pr[v]);
        ev.setResult(result);
    }

    // ── Densidade ─────────────────────────────────────────────────────────

    private void onDensity(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        int e = g.getEdgeCount();
        double maxEdges = (double) n * (n - 1); // direcionado sem laços
        ev.setResult(maxEdges == 0 ? 0.0 : e / maxEdges);
    }

    // ── Coeficiente de Aglomeração ─────────────────────────────────────────

    private void onClustering(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        Map<Integer, Double> result = new LinkedHashMap<>();

        for (int v = 0; v < n; v++) {
            List<Integer> neighbors = new ArrayList<>();
            for (int u = 0; u < n; u++)
                if (g.hasEdge(v, u) || g.hasEdge(u, v))
                    neighbors.add(u);

            int k = neighbors.size();
            if (k < 2) {
                result.put(v, 0.0);
                continue;
            }

            int triangles = 0;
            for (int i = 0; i < k; i++)
                for (int j = i + 1; j < k; j++) {
                    int a = neighbors.get(i), b = neighbors.get(j);
                    if (g.hasEdge(a, b) || g.hasEdge(b, a))
                        triangles++;
                }
            result.put(v, 2.0 * triangles / (k * (k - 1)));
        }
        ev.setResult(result);
    }

    // ── Assortatividade (correlação de grau) ───────────────────────────────

    private void onAssortativity(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();

        List<double[]> edges = new ArrayList<>();
        for (int u = 0; u < n; u++)
            for (int v = 0; v < n; v++)
                if (g.hasEdge(u, v))
                    edges.add(new double[] { g.getVertexOutDegree(u), g.getVertexInDegree(v) });

        int m = edges.size();
        if (m == 0) {
            ev.setResult(0.0);
            return;
        }

        double sumXY = 0, sumX = 0, sumY = 0, sumX2 = 0, sumY2 = 0;
        for (double[] e : edges) {
            sumXY += e[0] * e[1];
            sumX += e[0];
            sumY += e[1];
            sumX2 += e[0] * e[0];
            sumY2 += e[1] * e[1];
        }
        double num = m * sumXY - sumX * sumY;
        double den = Math.sqrt((m * sumX2 - sumX * sumX) * (m * sumY2 - sumY * sumY));
        ev.setResult(den == 0 ? 0.0 : num / den);
    }

    // ── Detecção de Comunidades (Louvain simplificado – Label Propagation) ─

    private void onCommunityDetection(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        int[] community = new int[n];
        for (int i = 0; i < n; i++)
            community[i] = i;

        boolean changed = true;
        int maxIter = 100;
        while (changed && maxIter-- > 0) {
            changed = false;
            int[] order = shuffledOrder(n);
            for (int idx : order) {
                Map<Integer, Integer> freq = new HashMap<>();
                for (int j = 0; j < n; j++) {
                    if (g.hasEdge(idx, j) || g.hasEdge(j, idx)) {
                        freq.merge(community[j], 1, Integer::sum);
                    }
                }
                if (freq.isEmpty())
                    continue;
                int best = freq.entrySet().stream()
                        .max(Map.Entry.comparingByValue())
                        .get().getKey();
                if (best != community[idx]) {
                    community[idx] = best;
                    changed = true;
                }
            }
        }
        // normaliza IDs de comunidade
        Map<Integer, Integer> remap = new HashMap<>();
        int nextId = 0;
        Map<Integer, Integer> result = new LinkedHashMap<>();
        for (int v = 0; v < n; v++) {
            int cid = remap.computeIfAbsent(community[v], k -> nextId + remap.size() - (remap.isEmpty() ? 0 : 0));
            result.put(v, community[v]);
        }
        ev.setResult(result);
    }

    private int[] shuffledOrder(int n) {
        int[] a = new int[n];
        for (int i = 0; i < n; i++)
            a[i] = i;
        Random rnd = new Random();
        for (int i = n - 1; i > 0; i--) {
            int j = rnd.nextInt(i + 1);
            int t = a[i];
            a[i] = a[j];
            a[j] = t;
        }
        return a;
    }

    // ── Bridging Ties ──────────────────────────────────────────────────────

    @SuppressWarnings("unchecked")
    private void onBridgingTies(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();

        // Executa detecção de comunidade internamente
        Event commEv = new Event(EventType.METRIC_COMMUNITY_DETECTION)
                .with("graphId", ev.getString("graphId"));
        onCommunityDetection(commEv);
        Map<Integer, Integer> community = (Map<Integer, Integer>) commEv.getResult();

        // Identifica vértices que conectam comunidades diferentes
        Set<Integer> bridges = new LinkedHashSet<>();
        for (int u = 0; u < n; u++)
            for (int v = 0; v < n; v++)
                if (g.hasEdge(u, v) && !community.get(u).equals(community.get(v))) {
                    bridges.add(u);
                    bridges.add(v);
                }
        ev.setResult(new ArrayList<>(bridges));
    }
}
