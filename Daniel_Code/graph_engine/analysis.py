from collections import deque
from math import sqrt

from graph_engine.abstract_graph import AbstractGraph


def degree_centrality(graph: AbstractGraph) -> dict[int, float]:
    n = graph.getVertexCount()
    denominator = max(1, 2 * (n - 1))
    return {v: (graph.getVertexInDegree(v) + graph.getVertexOutDegree(v)) / denominator for v in range(n)}


def _distances(graph: AbstractGraph, source: int) -> dict[int, int]:
    distance = {source: 0}
    queue = deque([source])
    while queue:
        u = queue.popleft()
        for v in graph.successors(u):
            if v not in distance:
                distance[v] = distance[u] + 1
                queue.append(v)
    return distance


def closeness_centrality(graph: AbstractGraph) -> dict[int, float]:
    n = graph.getVertexCount()
    result = {}
    for source in range(n):
        distances = _distances(graph, source)
        total = sum(distances.values())
        reachable = len(distances) - 1
        result[source] = 0.0 if total == 0 else (reachable / total) * (reachable / max(1, n - 1))
    return result


def betweenness_centrality(graph: AbstractGraph) -> dict[int, float]:
    n = graph.getVertexCount()
    centrality = dict.fromkeys(range(n), 0.0)
    for source in range(n):
        stack, predecessors = [], [[] for _ in range(n)]
        paths, distance = [0.0] * n, [-1] * n
        paths[source], distance[source] = 1.0, 0
        queue = deque([source])
        while queue:
            u = queue.popleft()
            stack.append(u)
            for v in graph.successors(u):
                if distance[v] < 0:
                    distance[v] = distance[u] + 1
                    queue.append(v)
                if distance[v] == distance[u] + 1:
                    paths[v] += paths[u]
                    predecessors[v].append(u)
        dependency = [0.0] * n
        while stack:
            v = stack.pop()
            for u in predecessors[v]:
                dependency[u] += (paths[u] / paths[v]) * (1 + dependency[v])
            if v != source:
                centrality[v] += dependency[v]
    scale = 1 / max(1, (n - 1) * (n - 2))
    return {v: value * scale for v, value in centrality.items()}


def pagerank(graph: AbstractGraph, damping: float = 0.85, iterations: int = 100, tolerance: float = 1e-10) -> dict[int, float]:
    n = graph.getVertexCount()
    if n == 0:
        return {}
    rank = [1 / n] * n
    for _ in range(iterations):
        dangling = sum(rank[u] for u in range(n) if not graph.successors(u))
        updated = [(1 - damping) / n + damping * dangling / n for _ in range(n)]
        for u in range(n):
            successors = graph.successors(u)
            total_weight = sum(graph.getEdgeWeight(u, v) for v in successors)
            for v in successors:
                updated[v] += damping * rank[u] * graph.getEdgeWeight(u, v) / total_weight
        if sum(abs(updated[i] - rank[i]) for i in range(n)) < tolerance:
            rank = updated
            break
        rank = updated
    return dict(enumerate(rank))


def density(graph: AbstractGraph) -> float:
    n = graph.getVertexCount()
    return 0.0 if n < 2 else graph.getEdgeCount() / (n * (n - 1))


def clustering_coefficient(graph: AbstractGraph) -> dict[int, float]:
    result = {}
    for vertex in range(graph.getVertexCount()):
        neighbors = set(graph.successors(vertex)) | set(graph.predecessors(vertex))
        possible = len(neighbors) * (len(neighbors) - 1)
        links = sum(graph.hasEdge(u, v) for u in neighbors for v in neighbors if u != v)
        result[vertex] = 0.0 if possible == 0 else links / possible
    return result


def assortativity(graph: AbstractGraph) -> float:
    pairs = []
    for u in range(graph.getVertexCount()):
        degree_u = graph.getVertexInDegree(u) + graph.getVertexOutDegree(u)
        for v in graph.successors(u):
            pairs.append((degree_u, graph.getVertexInDegree(v) + graph.getVertexOutDegree(v)))
    if not pairs:
        return 0.0
    mean_x = sum(x for x, _ in pairs) / len(pairs)
    mean_y = sum(y for _, y in pairs) / len(pairs)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in pairs)
    denominator = sqrt(sum((x - mean_x) ** 2 for x, _ in pairs) * sum((y - mean_y) ** 2 for _, y in pairs))
    return 0.0 if denominator == 0 else numerator / denominator


def communities(graph: AbstractGraph) -> list[set[int]]:
    remaining = set(range(graph.getVertexCount()))
    groups = []
    while remaining:
        start = min(remaining)
        group, stack = {start}, [start]
        remaining.remove(start)
        while stack:
            u = stack.pop()
            neighbors = (set(graph.successors(u)) | set(graph.predecessors(u))) & remaining
            group.update(neighbors)
            remaining -= neighbors
            stack.extend(neighbors)
        groups.append(group)
    return groups


def bridging_ties(graph: AbstractGraph, limit: int = 10) -> list[tuple[int, float]]:
    return sorted(betweenness_centrality(graph).items(), key=lambda item: item[1], reverse=True)[:limit]