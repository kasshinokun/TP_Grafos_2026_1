package br.pucminas.grafo.handlers;

import br.pucminas.grafo.core.EventBus;
import br.pucminas.grafo.core.GraphRegistry;
import br.pucminas.grafo.events.Event;
import br.pucminas.grafo.events.EventType;
import br.pucminas.grafo.graph.AbstractGraph;

import java.util.*;

/**
 * Handler de algoritmos clássicos em grafos.
 *
 * <h3>Eventos atendidos:</h3>
 * <ul>
 *   <li>ALGO_BFS              → payload: graphId, source → result: List(Integer) ordem de visita</li>
 *   <li>ALGO_DFS              → payload: graphId, source → result: List(Integer) ordem de visita</li>
 *   <li>ALGO_SHORTEST_PATH    → payload: graphId, source, target → result: Map{path,dist}</li>
 *   <li>ALGO_TOPOLOGICAL_SORT → payload: graphId → result: List(Integer) ou null se há ciclo</li>
 *   <li>ALGO_STRONGLY_CONNECTED → payload: graphId → result: List(List(Integer)) SCCs (Kosaraju)</li>
 * </ul>
 */
public class AlgorithmHandler {

    private final GraphRegistry registry;

    public AlgorithmHandler(GraphRegistry registry) {
        this.registry = registry;
    }

    public void registerAll(EventBus bus) {
        bus.subscribe(EventType.ALGO_BFS,               this::onBFS);
        bus.subscribe(EventType.ALGO_DFS,               this::onDFS);
        bus.subscribe(EventType.ALGO_SHORTEST_PATH,     this::onShortestPath);
        bus.subscribe(EventType.ALGO_TOPOLOGICAL_SORT,  this::onTopologicalSort);
        bus.subscribe(EventType.ALGO_STRONGLY_CONNECTED,this::onSCC);
    }

    // ── BFS ────────────────────────────────────────────────────────────────

    private void onBFS(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int src = ev.getInt("source");
        g.checkVertex(src);

        boolean[] visited = new boolean[g.getVertexCount()];
        List<Integer> order = new ArrayList<>();
        Queue<Integer> queue = new LinkedList<>();

        visited[src] = true;
        queue.add(src);
        while (!queue.isEmpty()) {
            int cur = queue.poll();
            order.add(cur);
            for (int j = 0; j < g.getVertexCount(); j++)
                if (!visited[j] && g.hasEdge(cur, j)) {
                    visited[j] = true;
                    queue.add(j);
                }
        }
        ev.setResult(order);
    }

    // ── DFS ────────────────────────────────────────────────────────────────

    private void onDFS(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int src = ev.getInt("source");
        g.checkVertex(src);

        boolean[] visited = new boolean[g.getVertexCount()];
        List<Integer> order = new ArrayList<>();
        dfsRecursive(g, src, visited, order);
        ev.setResult(order);
    }

    private void dfsRecursive(AbstractGraph g, int v, boolean[] visited, List<Integer> order) {
        visited[v] = true;
        order.add(v);
        for (int j = 0; j < g.getVertexCount(); j++)
            if (!visited[j] && g.hasEdge(v, j))
                dfsRecursive(g, j, visited, order);
    }

    // ── Dijkstra (caminho mais curto) ──────────────────────────────────────

    private void onShortestPath(Event ev) {
        AbstractGraph g      = registry.get(ev.getString("graphId"));
        int           src    = ev.getInt("source");
        int           target = ev.getInt("target");
        int           n      = g.getVertexCount();
        g.checkVertex(src); g.checkVertex(target);

        double[] dist  = new double[n];
        int[]    prev  = new int[n];
        boolean[] done = new boolean[n];
        Arrays.fill(dist, Double.MAX_VALUE);
        Arrays.fill(prev, -1);
        dist[src] = 0;

        // Min-heap: (distância, vértice)
        PriorityQueue<int[]> pq = new PriorityQueue<>(Comparator.comparingDouble(a -> dist[a[0]]));
        pq.offer(new int[]{src});

        while (!pq.isEmpty()) {
            int u = pq.poll()[0];
            if (done[u]) continue;
            done[u] = true;
            for (int v = 0; v < n; v++) {
                if (g.hasEdge(u, v)) {
                    double w = g.getEdgeWeight(u, v);
                    if (dist[u] + w < dist[v]) {
                        dist[v] = dist[u] + w;
                        prev[v] = u;
                        pq.offer(new int[]{v});
                    }
                }
            }
        }

        List<Integer> path = new ArrayList<>();
        if (dist[target] == Double.MAX_VALUE) {
            ev.setResult(Map.of("path", path, "dist", Double.MAX_VALUE,
                                "reachable", false));
            return;
        }
        for (int v = target; v != -1; v = prev[v]) path.add(0, v);
        ev.setResult(Map.of("path", path, "dist", dist[target], "reachable", true));
    }

    // ── Ordenação Topológica (Kahn) ────────────────────────────────────────

    private void onTopologicalSort(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        int[] inDeg = new int[n];
        for (int u = 0; u < n; u++)
            for (int v = 0; v < n; v++)
                if (g.hasEdge(u, v)) inDeg[v]++;

        Queue<Integer> queue = new LinkedList<>();
        for (int i = 0; i < n; i++) if (inDeg[i] == 0) queue.add(i);

        List<Integer> sorted = new ArrayList<>();
        while (!queue.isEmpty()) {
            int u = queue.poll();
            sorted.add(u);
            for (int v = 0; v < n; v++)
                if (g.hasEdge(u, v) && --inDeg[v] == 0)
                    queue.add(v);
        }
        ev.setResult(sorted.size() == n ? sorted : null); // null = ciclo detectado
    }

    // ── Componentes Fortemente Conexos – Kosaraju ──────────────────────────

    private void onSCC(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        int n = g.getVertexCount();
        boolean[] visited = new boolean[n];
        Deque<Integer> finishStack = new ArrayDeque<>();

        // 1ª passagem DFS no grafo original
        for (int i = 0; i < n; i++)
            if (!visited[i]) fillOrder(g, i, visited, finishStack);

        // 2ª passagem DFS no grafo transposto
        visited = new boolean[n];
        List<List<Integer>> sccs = new ArrayList<>();
        while (!finishStack.isEmpty()) {
            int v = finishStack.pop();
            if (!visited[v]) {
                List<Integer> comp = new ArrayList<>();
                dfsTransposed(g, v, visited, comp);
                sccs.add(comp);
            }
        }
        ev.setResult(sccs);
    }

    private void fillOrder(AbstractGraph g, int v, boolean[] visited, Deque<Integer> stack) {
        visited[v] = true;
        for (int j = 0; j < g.getVertexCount(); j++)
            if (!visited[j] && g.hasEdge(v, j))
                fillOrder(g, j, visited, stack);
        stack.push(v);
    }

    private void dfsTransposed(AbstractGraph g, int v, boolean[] visited, List<Integer> comp) {
        visited[v] = true;
        comp.add(v);
        for (int j = 0; j < g.getVertexCount(); j++)
            if (!visited[j] && g.hasEdge(j, v)) // aresta transposta
                dfsTransposed(g, j, visited, comp);
    }
}
