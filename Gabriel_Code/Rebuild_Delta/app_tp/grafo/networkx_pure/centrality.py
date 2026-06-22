from collections import deque

def degree_centrality(adapter):
    n = adapter.number_of_nodes()
    if n <= 1: return {i: 0.0 for i in adapter.nodes()}
    return {i: {
        'in': adapter.in_degree(i), 'out': adapter.out_degree(i),
        'in_norm': adapter.in_degree(i) / (n - 1),
        'out_norm': adapter.out_degree(i) / (n - 1)
    } for i in adapter.nodes()}

def _bfs_distances(adapter, start, directed=True):
    dist = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        neighbors = adapter.successors(u) if directed else adapter.neighbors(u)
        for v in neighbors:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist

def closeness_centrality(adapter):
    n = adapter.number_of_nodes()
    result = {}
    for i in adapter.nodes():
        dist = _bfs_distances(adapter, i, directed=False)
        total = sum(d for d in dist.values() if d > 0)
        reachable = len(dist) - 1
        result[i] = (reachable / (n - 1)) * (reachable / total) if total > 0 and reachable > 0 else 0.0
    return result

def betweenness_centrality(adapter):
    n = adapter.number_of_nodes()
    betweenness = {i: 0.0 for i in adapter.nodes()}
    for s in adapter.nodes():
        stack, pred, sigma, dist = [], {i: [] for i in adapter.nodes()}, {i: 0 for i in adapter.nodes()}, {i: -1 for i in adapter.nodes()}
        sigma[s], dist[s], q = 1, 0, deque([s])
        while q:
            v = q.popleft(); stack.append(v)
            for w in adapter.successors(v):
                if dist[w] < 0: q.append(w); dist[w] = dist[v] + 1
                if dist[w] == dist[v] + 1: sigma[w] += sigma[v]; pred[w].append(v)
        delta = {i: 0.0 for i in adapter.nodes()}
        while stack:
            w = stack.pop()
            for v in pred[w]: delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s: betweenness[w] += delta[w]
    norm = (n - 1) * (n - 2)
    return {i: betweenness[i] / norm if norm > 0 else 0 for i in adapter.nodes()}

def pagerank(adapter, damping=0.85, max_iter=100, tol=1e-6):
    n = adapter.number_of_nodes()
    nodes = adapter.nodes()
    pr = {i: 1.0 / n for i in nodes}
    for _ in range(max_iter):
        new_pr = {i: (1 - damping) / n for i in nodes}
        for i in nodes:
            out_deg = adapter.out_degree(i)
            if out_deg > 0:
                share = damping * pr[i] / out_deg
                for j in adapter.successors(i): new_pr[j] += share
            else:
                for j in nodes: new_pr[j] += damping * pr[i] / n
        if sum(abs(new_pr[i] - pr[i]) for i in nodes) < tol: break
        pr = new_pr
    return pr