package br.pucminas.grafo.handlers;

import br.pucminas.grafo.core.EventBus;
import br.pucminas.grafo.core.GraphRegistry;
import br.pucminas.grafo.events.Event;
import br.pucminas.grafo.events.EventType;
import br.pucminas.grafo.graph.AbstractGraph;
import br.pucminas.grafo.graph.AdjacencyListGraph;
import br.pucminas.grafo.graph.AdjacencyMatrixGraph;

/**
 * Handler responsável por toda operação estrutural sobre grafos.
 *
 * <p>Cada método é registrado como um handler no EventBus, respondendo
 * a um EventType específico — equivalente a um endpoint de API.</p>
 *
 * <h3>Eventos atendidos:</h3>
 * <ul>
 *   <li>GRAPH_CREATE        → payload: graphId, numVertices, impl ("matrix"|"list")</li>
 *   <li>GRAPH_ADD_EDGE      → payload: graphId, u, v</li>
 *   <li>GRAPH_REMOVE_EDGE   → payload: graphId, u, v</li>
 *   <li>GRAPH_HAS_EDGE      → payload: graphId, u, v → result: Boolean</li>
 *   <li>GRAPH_GET_VERTEX_COUNT → payload: graphId  → result: Integer</li>
 *   <li>GRAPH_GET_EDGE_COUNT   → payload: graphId  → result: Integer</li>
 *   <li>GRAPH_SET_VERTEX_WEIGHT → payload: graphId, v, weight</li>
 *   <li>GRAPH_GET_VERTEX_WEIGHT → payload: graphId, v → result: Double</li>
 *   <li>GRAPH_SET_EDGE_WEIGHT   → payload: graphId, u, v, weight</li>
 *   <li>GRAPH_GET_EDGE_WEIGHT   → payload: graphId, u, v → result: Double</li>
 *   <li>GRAPH_IN_DEGREE     → payload: graphId, v → result: Integer</li>
 *   <li>GRAPH_OUT_DEGREE    → payload: graphId, v → result: Integer</li>
 *   <li>GRAPH_IS_SUCCESSOR  → payload: graphId, u, v → result: Boolean</li>
 *   <li>GRAPH_IS_PREDECESSOR → payload: graphId, u, v → result: Boolean</li>
 *   <li>GRAPH_IS_DIVERGENT  → payload: graphId, u1,v1,u2,v2 → result: Boolean</li>
 *   <li>GRAPH_IS_CONVERGENT → payload: graphId, u1,v1,u2,v2 → result: Boolean</li>
 *   <li>GRAPH_IS_INCIDENT   → payload: graphId, u, v, x → result: Boolean</li>
 *   <li>GRAPH_IS_CONNECTED  → payload: graphId → result: Boolean</li>
 *   <li>GRAPH_IS_EMPTY      → payload: graphId → result: Boolean</li>
 *   <li>GRAPH_IS_COMPLETE   → payload: graphId → result: Boolean</li>
 *   <li>GRAPH_EXPORT_GEPHI  → payload: graphId, path</li>
 * </ul>
 */
public class GraphHandler {

    private final GraphRegistry registry;

    public GraphHandler(GraphRegistry registry) {
        this.registry = registry;
    }

    // ── Registro de handlers no bus ────────────────────────────────────────

    public void registerAll(EventBus bus) {
        bus.subscribe(EventType.GRAPH_CREATE,           this::onCreate);
        bus.subscribe(EventType.GRAPH_ADD_EDGE,         this::onAddEdge);
        bus.subscribe(EventType.GRAPH_REMOVE_EDGE,      this::onRemoveEdge);
        bus.subscribe(EventType.GRAPH_HAS_EDGE,         this::onHasEdge);
        bus.subscribe(EventType.GRAPH_GET_VERTEX_COUNT, this::onGetVertexCount);
        bus.subscribe(EventType.GRAPH_GET_EDGE_COUNT,   this::onGetEdgeCount);
        bus.subscribe(EventType.GRAPH_SET_VERTEX_WEIGHT,this::onSetVertexWeight);
        bus.subscribe(EventType.GRAPH_GET_VERTEX_WEIGHT,this::onGetVertexWeight);
        bus.subscribe(EventType.GRAPH_SET_EDGE_WEIGHT,  this::onSetEdgeWeight);
        bus.subscribe(EventType.GRAPH_GET_EDGE_WEIGHT,  this::onGetEdgeWeight);
        bus.subscribe(EventType.GRAPH_IN_DEGREE,        this::onInDegree);
        bus.subscribe(EventType.GRAPH_OUT_DEGREE,       this::onOutDegree);
        bus.subscribe(EventType.GRAPH_IS_SUCCESSOR,     this::onIsSuccessor);
        bus.subscribe(EventType.GRAPH_IS_PREDECESSOR,   this::onIsPredecessor);
        bus.subscribe(EventType.GRAPH_IS_DIVERGENT,     this::onIsDivergent);
        bus.subscribe(EventType.GRAPH_IS_CONVERGENT,    this::onIsConvergent);
        bus.subscribe(EventType.GRAPH_IS_INCIDENT,      this::onIsIncident);
        bus.subscribe(EventType.GRAPH_IS_CONNECTED,     this::onIsConnected);
        bus.subscribe(EventType.GRAPH_IS_EMPTY,         this::onIsEmpty);
        bus.subscribe(EventType.GRAPH_IS_COMPLETE,      this::onIsComplete);
        bus.subscribe(EventType.GRAPH_ADD_VERTEX,       this::onAddVertex);
        bus.subscribe(EventType.GRAPH_EXPORT_GEPHI,     this::onExportGephi);
    }

    // ── Handlers ───────────────────────────────────────────────────────────

    private void onCreate(Event ev) {
        String id   = ev.getString("graphId");
        int    n    = ev.getInt("numVertices");
        String impl = ev.getString("impl");

        if (registry.contains(id)) {
            ev.setError("Grafo já existe: " + id);
            return;
        }
        AbstractGraph g = "matrix".equalsIgnoreCase(impl)
                ? new AdjacencyMatrixGraph(n)
                : new AdjacencyListGraph(n);
        registry.register(id, g);
        ev.setResult(g);
    }

    /** Evento GRAPH_ADD_VERTEX: expande o grafo existente criando um novo com +1 vértice.
     *  Payload: graphId, label (opcional). Result: novo índice do vértice. */
    private void onAddVertex(Event ev) {
        String id    = ev.getString("graphId");
        String label = ev.getString("label");
        AbstractGraph old = registry.get(id);
        int newSize = old.getVertexCount() + 1;
        AbstractGraph neo;
        if (old.getRepType() == AbstractGraph.RepType.MATRIX)
            neo = new AdjacencyMatrixGraph(newSize);
        else
            neo = new AdjacencyListGraph(newSize);

        // copia rótulos, pesos e arestas
        for (int i = 0; i < old.getVertexCount(); i++) {
            neo.setVertexLabel(i, old.getVertexLabel(i));
            neo.setVertexWeight(i, old.getVertexWeight(i));
        }
        int newIdx = newSize - 1;
        neo.setVertexLabel(newIdx, label != null ? label : "v" + newIdx);
        // copia arestas
        for (int u = 0; u < old.getVertexCount(); u++)
            for (int v = 0; v < old.getVertexCount(); v++)
                if (old.hasEdge(u, v)) {
                    neo.addEdge(u, v);
                    neo.setEdgeWeight(u, v, old.getEdgeWeight(u, v));
                }
        registry.remove(id);
        registry.register(id, neo);
        ev.setResult(newIdx);
    }

    private void onAddEdge(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        g.addEdge(ev.getInt("u"), ev.getInt("v"));
        ev.setResult(true);
    }

    private void onRemoveEdge(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        g.removeEdge(ev.getInt("u"), ev.getInt("v"));
        ev.setResult(true);
    }

    private void onHasEdge(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.hasEdge(ev.getInt("u"), ev.getInt("v")));
    }

    private void onGetVertexCount(Event ev) {
        ev.setResult(registry.get(ev.getString("graphId")).getVertexCount());
    }

    private void onGetEdgeCount(Event ev) {
        ev.setResult(registry.get(ev.getString("graphId")).getEdgeCount());
    }

    private void onSetVertexWeight(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        g.setVertexWeight(ev.getInt("v"), ev.getDouble("weight"));
        ev.setResult(true);
    }

    private void onGetVertexWeight(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.getVertexWeight(ev.getInt("v")));
    }

    private void onSetEdgeWeight(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        g.setEdgeWeight(ev.getInt("u"), ev.getInt("v"), ev.getDouble("weight"));
        ev.setResult(true);
    }

    private void onGetEdgeWeight(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.getEdgeWeight(ev.getInt("u"), ev.getInt("v")));
    }

    private void onInDegree(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.getVertexInDegree(ev.getInt("v")));
    }

    private void onOutDegree(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.getVertexOutDegree(ev.getInt("v")));
    }

    private void onIsSuccessor(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.isSuccessor(ev.getInt("u"), ev.getInt("v")));
    }

    private void onIsPredecessor(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.isPredecessor(ev.getInt("u"), ev.getInt("v")));
    }

    private void onIsDivergent(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.isDivergent(
            ev.getInt("u1"), ev.getInt("v1"),
            ev.getInt("u2"), ev.getInt("v2")));
    }

    private void onIsConvergent(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.isConvergent(
            ev.getInt("u1"), ev.getInt("v1"),
            ev.getInt("u2"), ev.getInt("v2")));
    }

    private void onIsIncident(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        ev.setResult(g.isIncident(ev.getInt("u"), ev.getInt("v"), ev.getInt("x")));
    }

    private void onIsConnected(Event ev) {
        ev.setResult(registry.get(ev.getString("graphId")).isConnected());
    }

    private void onIsEmpty(Event ev) {
        ev.setResult(registry.get(ev.getString("graphId")).isEmptyGraph());
    }

    private void onIsComplete(Event ev) {
        ev.setResult(registry.get(ev.getString("graphId")).isCompleteGraph());
    }

    private void onExportGephi(Event ev) {
        AbstractGraph g = registry.get(ev.getString("graphId"));
        g.exportToGEPHI(ev.getString("path"));
        ev.setResult(true);
    }
}
