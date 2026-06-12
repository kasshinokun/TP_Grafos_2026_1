package br.pucminas.grafo.graph;

/**
 * Classe abstrata que define a API obrigatória do trabalho prático.
 *
 * <p>Implementa atributos compartilhados (rótulos e pesos de vértices)
 * e métodos auxiliares de validação de índice. As subclasses fornecem
 * a representação interna (matriz ou lista de adjacência).</p>
 */
public abstract class AbstractGraph {

    protected final int numVertices;
    protected final double[] vertexWeights;
    protected final String[] vertexLabels;

    /** Tipo de representação interna, para exibição e export. */
    public enum RepType { MATRIX, LIST }
    protected final RepType repType;

    // ── Construtor ─────────────────────────────────────────────────────────

    protected AbstractGraph(int numVertices, RepType repType) {
        if (numVertices <= 0)
            throw new IllegalArgumentException("numVertices deve ser > 0.");
        this.numVertices  = numVertices;
        this.repType      = repType;
        this.vertexWeights = new double[numVertices];
        this.vertexLabels  = new String[numVertices];
        for (int i = 0; i < numVertices; i++) {
            vertexWeights[i] = 1.0;
            vertexLabels[i]  = "v" + i;
        }
    }

    // ── Validação ──────────────────────────────────────────────────────────

    protected void checkVertex(int v) {
        if (v < 0 || v >= numVertices)
            throw new IndexOutOfBoundsException(
                "Vértice inválido: " + v + " (total=" + numVertices + ")");
    }

    protected void checkEdge(int u, int v) {
        checkVertex(u);
        checkVertex(v);
        if (u == v) throw new IllegalArgumentException("Laço não permitido: " + u);
    }

    // ── API obrigatória ────────────────────────────────────────────────────

    public int getVertexCount() { return numVertices; }

    public abstract int getEdgeCount();

    public abstract boolean hasEdge(int u, int v);

    public abstract void addEdge(int u, int v);

    public abstract void removeEdge(int u, int v);

    /** v é sucessor de u (existe aresta u→v)? */
    public boolean isSuccessor(int u, int v)   { return hasEdge(u, v); }

    /** v é predecessor de u (existe aresta v→u)? */
    public boolean isPredecessor(int u, int v) { return hasEdge(v, u); }

    /**
     * As arestas (u1,v1) e (u2,v2) são divergentes?
     * Dois arcos são divergentes quando partem do mesmo vértice.
     */
    public boolean isDivergent(int u1, int v1, int u2, int v2) {
        checkEdge(u1, v1); checkEdge(u2, v2);
        return u1 == u2 && hasEdge(u1, v1) && hasEdge(u2, v2);
    }

    /**
     * As arestas (u1,v1) e (u2,v2) são convergentes?
     * Dois arcos convergem quando chegam ao mesmo vértice.
     */
    public boolean isConvergent(int u1, int v1, int u2, int v2) {
        checkEdge(u1, v1); checkEdge(u2, v2);
        return v1 == v2 && hasEdge(u1, v1) && hasEdge(u2, v2);
    }

    /**
     * A aresta (u,v) é incidente ao vértice x?
     * (x == u ou x == v, e a aresta existe)
     */
    public boolean isIncident(int u, int v, int x) {
        checkEdge(u, v); checkVertex(x);
        return (x == u || x == v) && hasEdge(u, v);
    }

    public abstract int getVertexInDegree(int u);

    public abstract int getVertexOutDegree(int u);

    // ── Pesos ──────────────────────────────────────────────────────────────

    public void setVertexWeight(int v, double w) {
        checkVertex(v);
        vertexWeights[v] = w;
    }

    public double getVertexWeight(int v) {
        checkVertex(v);
        return vertexWeights[v];
    }

    public void setVertexLabel(int v, String label) {
        checkVertex(v);
        vertexLabels[v] = label;
    }

    public String getVertexLabel(int v) {
        checkVertex(v);
        return vertexLabels[v];
    }

    public abstract void   setEdgeWeight(int u, int v, double w);
    public abstract double getEdgeWeight(int u, int v);

    // ── Propriedades estruturais ────────────────────────────────────────────

    /**
     * Verifica conectividade fraca: ignora direção das arestas.
     * Usa BFS no grafo subjacente não-direcionado.
     */
    public boolean isConnected() {
        if (numVertices == 0) return true;
        boolean[] visited = new boolean[numVertices];
        java.util.Queue<Integer> queue = new java.util.LinkedList<>();
        queue.add(0);
        visited[0] = true;
        int count = 1;
        while (!queue.isEmpty()) {
            int cur = queue.poll();
            for (int w = 0; w < numVertices; w++) {
                if (!visited[w] && (hasEdge(cur, w) || hasEdge(w, cur))) {
                    visited[w] = true;
                    queue.add(w);
                    count++;
                }
            }
        }
        return count == numVertices;
    }

    /** Grafo vazio: sem arestas. */
    public boolean isEmptyGraph() { return getEdgeCount() == 0; }

    /**
     * Grafo completo (torneio completo para grafos direcionados):
     * para cada par (i,j) com i≠j existe aresta i→j e j→i.
     */
    public boolean isCompleteGraph() {
        for (int i = 0; i < numVertices; i++)
            for (int j = 0; j < numVertices; j++)
                if (i != j && !hasEdge(i, j)) return false;
        return true;
    }

    // ── Export ─────────────────────────────────────────────────────────────

    public abstract void exportToGEPHI(String path);

    // ── Utilitários ────────────────────────────────────────────────────────

    public RepType getRepType() { return repType; }

    @Override
    public String toString() {
        return getClass().getSimpleName() +
               "[V=" + numVertices + ", E=" + getEdgeCount() + "]";
    }
}
