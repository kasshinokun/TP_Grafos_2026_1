from enum import Enum, auto

class EventType(Enum):
    # Gerenciamento de Grafo
    GRAPH_CREATE = auto()
    GRAPH_ADD_VERTEX = auto()
    GRAPH_ADD_EDGE = auto()
    GRAPH_REMOVE_EDGE = auto()
    GRAPH_HAS_EDGE = auto()
    GRAPH_GET_VERTEX_COUNT = auto()
    GRAPH_GET_EDGE_COUNT = auto()
    GRAPH_SET_VERTEX_WEIGHT = auto()
    GRAPH_GET_VERTEX_WEIGHT = auto()
    GRAPH_SET_EDGE_WEIGHT = auto()
    GRAPH_GET_EDGE_WEIGHT = auto()
    GRAPH_IN_DEGREE = auto()
    GRAPH_OUT_DEGREE = auto()
    GRAPH_IS_SUCCESSOR = auto()
    GRAPH_IS_PREDECESSOR = auto()
    GRAPH_IS_DIVERGENT = auto()
    GRAPH_IS_CONVERGENT = auto()
    GRAPH_IS_INCIDENT = auto()
    GRAPH_IS_CONNECTED = auto()
    GRAPH_IS_EMPTY = auto()
    GRAPH_IS_COMPLETE = auto()
    GRAPH_EXPORT_GEPHI = auto()

    # Algoritmos
    ALGO_BFS = auto()
    ALGO_DFS = auto()
    ALGO_SHORTEST_PATH = auto()
    ALGO_TOPOLOGICAL_SORT = auto()
    ALGO_STRONGLY_CONNECTED = auto()

    # Métricas de Centralidade
    METRIC_DEGREE_CENTRALITY = auto()
    METRIC_BETWEENNESS_CENTRALITY = auto()
    METRIC_CLOSENESS_CENTRALITY = auto()
    METRIC_PAGERANK = auto()

    # Métricas de Estrutura
    METRIC_DENSITY = auto()
    METRIC_CLUSTERING_COEFFICIENT = auto()
    METRIC_ASSORTATIVITY = auto()

    # Métricas de Comunidade
    METRIC_COMMUNITY_DETECTION = auto()
    METRIC_BRIDGING_TIES = auto()

    # Mineração de Dados (GitHub)
    MINING_LOAD_CSV = auto()
    MINING_BUILD_GRAPH1_COMMENTS = auto()
    MINING_BUILD_GRAPH2_CLOSURES = auto()
    MINING_BUILD_GRAPH3_REVIEWS = auto()
    MINING_BUILD_INTEGRATED_GRAPH = auto()

    # Respostas
    RESPONSE_SUCCESS = auto()
    RESPONSE_ERROR = auto()
