package br.pucminas.grafo.events;

/**
 * Catálogo central de todos os tipos de eventos da arquitetura EDA.
 * Cada tipo representa uma "chamada de API" interna.
 */
public enum EventType {

    // ── Gerenciamento de Grafo ──────────────────────────────────────────────
    GRAPH_CREATE,
    GRAPH_ADD_VERTEX,
    GRAPH_ADD_EDGE,
    GRAPH_REMOVE_EDGE,
    GRAPH_HAS_EDGE,
    GRAPH_GET_VERTEX_COUNT,
    GRAPH_GET_EDGE_COUNT,
    GRAPH_SET_VERTEX_WEIGHT,
    GRAPH_GET_VERTEX_WEIGHT,
    GRAPH_SET_EDGE_WEIGHT,
    GRAPH_GET_EDGE_WEIGHT,
    GRAPH_IN_DEGREE,
    GRAPH_OUT_DEGREE,
    GRAPH_IS_SUCCESSOR,
    GRAPH_IS_PREDECESSOR,
    GRAPH_IS_DIVERGENT,
    GRAPH_IS_CONVERGENT,
    GRAPH_IS_INCIDENT,
    GRAPH_IS_CONNECTED,
    GRAPH_IS_EMPTY,
    GRAPH_IS_COMPLETE,
    GRAPH_EXPORT_GEPHI,

    // ── Algoritmos ─────────────────────────────────────────────────────────
    ALGO_BFS,
    ALGO_DFS,
    ALGO_SHORTEST_PATH,
    ALGO_TOPOLOGICAL_SORT,
    ALGO_STRONGLY_CONNECTED,

    // ── Métricas de Centralidade ────────────────────────────────────────────
    METRIC_DEGREE_CENTRALITY,
    METRIC_BETWEENNESS_CENTRALITY,
    METRIC_CLOSENESS_CENTRALITY,
    METRIC_PAGERANK,

    // ── Métricas de Estrutura ───────────────────────────────────────────────
    METRIC_DENSITY,
    METRIC_CLUSTERING_COEFFICIENT,
    METRIC_ASSORTATIVITY,

    // ── Métricas de Comunidade ──────────────────────────────────────────────
    METRIC_COMMUNITY_DETECTION,
    METRIC_BRIDGING_TIES,

    // ── Mineração de Dados (GitHub) ─────────────────────────────────────────
    MINING_LOAD_CSV,
    MINING_BUILD_GRAPH1_COMMENTS,
    MINING_BUILD_GRAPH2_CLOSURES,
    MINING_BUILD_GRAPH3_REVIEWS,
    MINING_BUILD_INTEGRATED_GRAPH,

    // ── Respostas ───────────────────────────────────────────────────────────
    RESPONSE_SUCCESS,
    RESPONSE_ERROR
}
