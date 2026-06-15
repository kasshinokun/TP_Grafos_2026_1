package br.pucminas.grafo.handlers;

import br.pucminas.grafo.core.EventBus;
import br.pucminas.grafo.core.GraphRegistry;
import br.pucminas.grafo.events.Event;
import br.pucminas.grafo.events.EventType;
import br.pucminas.grafo.graph.AdjacencyListGraph;
import br.pucminas.grafo.mining.CsvLoader;
import br.pucminas.grafo.mining.Interaction;

import java.util.*;

/**
 * Handler de mineração de dados: constrói os 4 grafos exigidos no trabalho
 * a partir de uma lista de interações (carregada de CSV ou gerada in-memory).
 *
 * <h3>Eventos atendidos:</h3>
 * <ul>
 *   <li>MINING_LOAD_CSV              → payload: path → result: List(Interaction)</li>
 *   <li>MINING_BUILD_GRAPH1_COMMENTS → payload: interactions (List) → result: graphId "graph1"</li>
 *   <li>MINING_BUILD_GRAPH2_CLOSURES → payload: interactions (List) → result: graphId "graph2"</li>
 *   <li>MINING_BUILD_GRAPH3_REVIEWS  → payload: interactions (List) → result: graphId "graph3"</li>
 *   <li>MINING_BUILD_INTEGRATED_GRAPH → payload: interactions (List) → result: graphId "graph_integrated"</li>
 * </ul>
 */
public class MiningHandler {

    private final GraphRegistry registry;

    public MiningHandler(GraphRegistry registry) {
        this.registry = registry;
    }

    public void registerAll(EventBus bus) {
        bus.subscribe(EventType.MINING_LOAD_CSV,               this::onLoadCsv);
        bus.subscribe(EventType.MINING_BUILD_GRAPH1_COMMENTS,  this::onBuildGraph1);
        bus.subscribe(EventType.MINING_BUILD_GRAPH2_CLOSURES,  this::onBuildGraph2);
        bus.subscribe(EventType.MINING_BUILD_GRAPH3_REVIEWS,   this::onBuildGraph3);
        bus.subscribe(EventType.MINING_BUILD_INTEGRATED_GRAPH, this::onBuildIntegrated);
    }

    // ── Carregamento ───────────────────────────────────────────────────────

    private void onLoadCsv(Event ev) {
        try {
            String path = ev.getString("path");
            List<Interaction> interactions = CsvLoader.load(path);
            ev.setResult(interactions);
        } catch (Exception e) {
            ev.setError("Erro ao carregar CSV: " + e.getMessage());
        }
    }

    // ── Grafo 1: Comentários em issues ou pull requests ────────────────────

    private void onBuildGraph1(Event ev) {
        List<Interaction> interactions = ev.get("interactions");
        List<Interaction> filtered = interactions.stream()
            .filter(i -> i.type == Interaction.InteractionType.COMMENT_ON_ISSUE_OR_PR)
            .toList();
        String id = buildGraph(filtered, "graph1");
        ev.setResult(id);
    }

    // ── Grafo 2: Fechamento de issue por outro usuário ─────────────────────

    private void onBuildGraph2(Event ev) {
        List<Interaction> interactions = ev.get("interactions");
        List<Interaction> filtered = interactions.stream()
            .filter(i -> i.type == Interaction.InteractionType.ISSUE_CLOSED_BY_OTHER)
            .toList();
        String id = buildGraph(filtered, "graph2");
        ev.setResult(id);
    }

    // ── Grafo 3: Revisões, aprovações e merges de PRs ─────────────────────

    private void onBuildGraph3(Event ev) {
        List<Interaction> interactions = ev.get("interactions");
        List<Interaction> filtered = interactions.stream()
            .filter(i -> i.type == Interaction.InteractionType.PR_REVIEW_OR_APPROVAL
                      || i.type == Interaction.InteractionType.PR_MERGE)
            .toList();
        String id = buildGraph(filtered, "graph3");
        ev.setResult(id);
    }

    // ── Grafo Integrado (ponderado) ────────────────────────────────────────

    private void onBuildIntegrated(Event ev) {
        List<Interaction> interactions = ev.get("interactions");

        // Indexa usuários
        Map<String, Integer> userIndex = buildUserIndex(interactions);
        int n = userIndex.size();
        if (n == 0) { ev.setResult("graph_integrated"); return; }

        AdjacencyListGraph g = new AdjacencyListGraph(n);
        applyLabels(g, userIndex);

        // Acumula pesos das arestas combinando todas as interações
        for (Interaction inter : interactions) {
            if (inter.actor.equals(inter.target)) continue;
            int u = userIndex.get(inter.actor);
            int v = userIndex.get(inter.target);
            double cur = g.hasEdge(u, v) ? g.getEdgeWeight(u, v) : 0.0;
            g.setEdgeWeight(u, v, cur + inter.type.weight);
        }

        String graphId = "graph_integrated";
        registry.remove(graphId);
        registry.register(graphId, g);
        ev.setResult(graphId);
    }

    // ── Utilitários ────────────────────────────────────────────────────────

    /**
     * Constrói um grafo simples (sem pesos acumulados) para um subconjunto
     * de interações, registrando-o no registry com o id fornecido.
     */
    private String buildGraph(List<Interaction> interactions, String graphId) {
        Map<String, Integer> userIndex = buildUserIndex(interactions);
        int n = userIndex.size();
        if (n == 0) {
            // grafo vazio com 1 nó
            AdjacencyListGraph empty = new AdjacencyListGraph(1);
            registry.remove(graphId);
            registry.register(graphId, empty);
            return graphId;
        }
        AdjacencyListGraph g = new AdjacencyListGraph(n);
        applyLabels(g, userIndex);
        for (Interaction inter : interactions) {
            if (inter.actor.equals(inter.target)) continue;
            g.addEdge(userIndex.get(inter.actor), userIndex.get(inter.target));
        }
        registry.remove(graphId);
        registry.register(graphId, g);
        return graphId;
    }

    /**
     * Extrai todos os usuários únicos e atribui índices consecutivos.
     */
    private Map<String, Integer> buildUserIndex(List<Interaction> interactions) {
        Map<String, Integer> map = new LinkedHashMap<>();
        for (Interaction i : interactions) {
            map.computeIfAbsent(i.actor,  k -> map.size());
            map.computeIfAbsent(i.target, k -> map.size());
        }
        return map;
    }

    private void applyLabels(AdjacencyListGraph g, Map<String, Integer> index) {
        index.forEach((name, idx) -> g.setVertexLabel(idx, name));
    }
}
