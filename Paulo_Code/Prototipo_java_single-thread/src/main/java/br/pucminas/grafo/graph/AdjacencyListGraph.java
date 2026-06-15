package br.pucminas.grafo.graph;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/**
 * Implementação de grafo simples e direcionado usando listas de adjacência.
 *
 * <p>Cada vértice possui um {@code Map<Integer,Double>} que mapeia
 * destino → peso. Isso permite acesso O(1) a {@code hasEdge} e
 * {@code getEdgeWeight}, e iteração eficiente sobre vizinhos.</p>
 */
public class AdjacencyListGraph extends AbstractGraph {

    /** adj.get(u).get(v) = peso da aresta u→v. */
    private final Map<Integer, Double>[] adj;
    private int edgeCount;

    // ── Construtor ─────────────────────────────────────────────────────────

    @SuppressWarnings("unchecked")
    public AdjacencyListGraph(int numVertices) {
        super(numVertices, RepType.LIST);
        this.adj       = new HashMap[numVertices];
        this.edgeCount = 0;
        for (int i = 0; i < numVertices; i++)
            adj[i] = new HashMap<>();
    }

    // ── API ────────────────────────────────────────────────────────────────

    @Override
    public int getEdgeCount() { return edgeCount; }

    @Override
    public boolean hasEdge(int u, int v) {
        checkVertex(u); checkVertex(v);
        return adj[u].containsKey(v);
    }

    @Override
    public void addEdge(int u, int v) {
        checkEdge(u, v);
        if (!adj[u].containsKey(v)) {
            adj[u].put(v, 1.0);
            edgeCount++;
        }
    }

    @Override
    public void removeEdge(int u, int v) {
        checkEdge(u, v);
        if (adj[u].remove(v) != null) edgeCount--;
    }

    @Override
    public int getVertexInDegree(int u) {
        checkVertex(u);
        int deg = 0;
        for (int i = 0; i < numVertices; i++)
            if (adj[i].containsKey(u)) deg++;
        return deg;
    }

    @Override
    public int getVertexOutDegree(int u) {
        checkVertex(u);
        return adj[u].size();
    }

    @Override
    public void setEdgeWeight(int u, int v, double w) {
        checkEdge(u, v);
        if (w == 0) throw new IllegalArgumentException("Peso 0 reservado para 'sem aresta'.");
        if (!adj[u].containsKey(v)) edgeCount++;
        adj[u].put(v, w);
    }

    @Override
    public double getEdgeWeight(int u, int v) {
        checkEdge(u, v);
        Double w = adj[u].get(v);
        if (w == null)
            throw new IllegalStateException("Aresta (" + u + "," + v + ") não existe.");
        return w;
    }

    // ── Acesso interno ─────────────────────────────────────────────────────

    /** Retorna os destinos (sucessores) de u com seus pesos. */
    public Map<Integer, Double> getNeighbors(int u) {
        checkVertex(u);
        return adj[u];
    }

    /** Retorna todos os índices de destinos de u. */
    public Set<Integer> getSuccessors(int u) {
        checkVertex(u);
        return adj[u].keySet();
    }

    // ── Export GEPHI (formato GEXF) ────────────────────────────────────────

    @Override
    public void exportToGEPHI(String path) {
        String filePath = path.endsWith(".gexf") ? path : path + ".gexf";
        try (PrintWriter pw = new PrintWriter(new FileWriter(filePath))) {
            pw.println("<?xml version=\"1.0\" encoding=\"UTF-8\"?>");
            pw.println("<gexf xmlns=\"http://gexf.net/1.3\" version=\"1.3\">");
            pw.println("  <graph defaultedgetype=\"directed\">");
            pw.println("    <nodes>");
            for (int i = 0; i < numVertices; i++)
                pw.printf("      <node id=\"%d\" label=\"%s\" weight=\"%.4f\"/>%n",
                          i, vertexLabels[i], vertexWeights[i]);
            pw.println("    </nodes>");
            pw.println("    <edges>");
            int eid = 0;
            for (int u = 0; u < numVertices; u++)
                for (Map.Entry<Integer, Double> e : adj[u].entrySet())
                    pw.printf("      <edge id=\"%d\" source=\"%d\" target=\"%d\" weight=\"%.4f\"/>%n",
                              eid++, u, e.getKey(), e.getValue());
            pw.println("    </edges>");
            pw.println("  </graph>");
            pw.println("</gexf>");
        } catch (IOException e) {
            throw new RuntimeException("Erro ao exportar GEPHI: " + e.getMessage(), e);
        }
    }

    // ── toString ───────────────────────────────────────────────────────────

    public String toListString() {
        StringBuilder sb = new StringBuilder("Lista de Adjacência:\n");
        for (int i = 0; i < numVertices; i++) {
            sb.append(String.format("  [%d] %s → ", i, vertexLabels[i]));
            adj[i].forEach((dst, w) -> sb.append(dst).append("(w=").append(w).append(") "));
            sb.append("\n");
        }
        return sb.toString();
    }
}
