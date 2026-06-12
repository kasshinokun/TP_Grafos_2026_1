package br.pucminas.grafo.core;

import br.pucminas.grafo.graph.AbstractGraph;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/**
 * Repositório em memória de instâncias de grafos nomeados.
 * Compartilhado entre todos os handlers via injeção no construtor.
 */
public class GraphRegistry {

    private final Map<String, AbstractGraph> store = new HashMap<>();

    public void register(String id, AbstractGraph graph) {
        store.put(id, graph);
    }

    public AbstractGraph get(String id) {
        AbstractGraph g = store.get(id);
        if (g == null) throw new IllegalArgumentException("Grafo não encontrado: " + id);
        return g;
    }

    public boolean contains(String id) {
        return store.containsKey(id);
    }

    public void remove(String id) {
        store.remove(id);
    }

    public Set<String> listIds() {
        return store.keySet();
    }
}
