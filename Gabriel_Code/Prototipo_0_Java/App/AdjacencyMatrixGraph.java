package br.pucminas.grafo.graph;

import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;

/**
 * Implementação de grafo simples e direcionado usando matriz de adjacência.
 *
 * <p>A matriz {@code adj[u][v]} armazena o peso da aresta u→v,
 * ou {@code 0} quando não há aresta. Como laços são proibidos,
 * a diagonal principal é sempre 0.</p>
 */
public class AdjacencyMatrixGraph extends AbstractGraph {

    /** adj[u][v] = peso da aresta u→v; 0 = sem aresta. */
    private final double[][] adj;
    private int edgeCount;

    // ── Construtor ─────────────────────────────────────────────────────────

    public AdjacencyMatrixGraph(int numVertices) {
        super(numVertices, RepType.MATRIX);
        this.adj       = new double[numVertices][numVertices];
        this.edgeCount = 0;
    }

    // ── API ────────────────────────────────────────────────────────────────

    @Override
    public int getEdgeCount() { return edgeCount; }

    @Override
    public boolean hasEdge(int u, int v) {
        checkVertex(u); checkVertex(v);
        return adj[u][v] != 0;
    }

    /** Idempotente: não duplica arestas. Peso padrão = 1. */
    @Override
    public void addEdge(int u, int v) {
        checkEdge(u, v);
        if (adj[u][v] == 0) {
            adj[u][v] = 1.0;
            edgeCount++;
        }
    }

    @Override
    public void removeEdge(int u, int v) {
        checkEdge(u, v);
        if (adj[u][v] != 0) {
            adj[u][v] = 0;
            edgeCount--;
        }
    }

    @Override
    public int getVertexInDegree(int u) {
        checkVertex(u);
        int deg = 0;
        for (int i = 0; i < numVertices; i++)
            if (adj[i][u] != 0) deg++;
        return deg;
    }

    @Override
    public int getVertexOutDegree(int u) {
        checkVertex(u);
        int deg = 0;
        for (int j = 0; j < numVertices; j++)
            if (adj[u][j] != 0) deg++;
        return deg;
    }

    @Override
    public void setEdgeWeight(int u, int v, double w) {
        checkEdge(u, v);
        if (w == 0) throw new IllegalArgumentException(
            "Peso 0 é reservado para 'sem aresta'. Use removeEdge para remover.");
        if (adj[u][v] == 0) edgeCount++; // cria a aresta ao definir peso
        adj[u][v] = w;
    }

    @Override
    public double getEdgeWeight(int u, int v) {
        checkEdge(u, v);
        if (adj[u][v] == 0)
            throw new IllegalStateException("Aresta (" + u + "," + v + ") não existe.");
        return adj[u][v];
    }

    // ── Acesso interno (para algoritmos) ───────────────────────────────────

    public double[][] getMatrix() { return adj; }

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
                for (int v = 0; v < numVertices; v++)
                    if (adj[u][v] != 0)
                        pw.printf("      <edge id=\"%d\" source=\"%d\" target=\"%d\" weight=\"%.4f\"/>%n",
                                  eid++, u, v, adj[u][v]);
            pw.println("    </edges>");
            pw.println("  </graph>");
            pw.println("</gexf>");
        } catch (IOException e) {
            throw new RuntimeException("Erro ao exportar GEPHI: " + e.getMessage(), e);
        }
    }

    // ── toString ───────────────────────────────────────────────────────────

    /** Exibe a matriz formatada para depuração (útil em grafos pequenos). */
    public String toMatrixString() {
        StringBuilder sb = new StringBuilder("Matriz de Adjacência:\n   ");
        for (int j = 0; j < numVertices; j++)
            sb.append(String.format("%6d", j));
        sb.append("\n");
        for (int i = 0; i < numVertices; i++) {
            sb.append(String.format("%3d", i));
            for (int j = 0; j < numVertices; j++)
                sb.append(String.format("%6.1f", adj[i][j]));
            sb.append("\n");
        }
        return sb.toString();
    }
}
