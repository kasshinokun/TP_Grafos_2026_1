import random
import collections
from ..events.event_type import EventType
from ..events.event import Event
from ..events.event_bus import EventBus
from ..core.graph_registry import GraphRegistry

class MetricsHandler:
    def __init__(self, registry: GraphRegistry):
        self.registry = registry

    def register_all(self, bus: EventBus):
        bus.subscribe(EventType.METRIC_DEGREE_CENTRALITY, self.on_degree_centrality)
        bus.subscribe(EventType.METRIC_BETWEENNESS_CENTRALITY, self.on_betweenness)
        bus.subscribe(EventType.METRIC_CLOSENESS_CENTRALITY, self.on_closeness)
        bus.subscribe(EventType.METRIC_PAGERANK, self.on_pagerank)
        bus.subscribe(EventType.METRIC_DENSITY, self.on_density)
        bus.subscribe(EventType.METRIC_CLUSTERING_COEFFICIENT, self.on_clustering)
        bus.subscribe(EventType.METRIC_ASSORTATIVITY, self.on_assortativity)
        bus.subscribe(EventType.METRIC_COMMUNITY_DETECTION, self.on_community_detection)
        bus.subscribe(EventType.METRIC_BRIDGING_TIES, self.on_bridging_ties)

    def on_degree_centrality(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        results = {}
        denom = n - 1 if n > 1 else 1.0
        for i in range(n):
            deg = g.get_vertex_in_degree(i) + g.get_vertex_out_degree(i)
            results[i] = deg / denom
        ev.set_result(results)

    def on_betweenness(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        cb = {i: 0.0 for i in range(n)}
        for s in range(n):
            stack = []
            p = [[] for _ in range(n)]
            sigma = [0.0] * n
            sigma[s] = 1.0
            d = [-1] * n
            d[s] = 0
            queue = collections.deque([s])
            while queue:
                v = queue.popleft()
                stack.append(v)
                for w in range(n):
                    if g.has_edge(v, w):
                        if d[w] < 0:
                            queue.append(w)
                            d[w] = d[v] + 1
                        if d[w] == d[v] + 1:
                            sigma[w] += sigma[v]
                            p[w].append(v)
            delta = [0.0] * n
            while stack:
                w = stack.pop()
                for v in p[w]:
                    delta[v] += (sigma[v] / sigma[w]) * (1.0 + delta[w])
                if w != s:
                    cb[w] += delta[w]
        
        denom = (n - 1) * (n - 2) if n > 2 else 1.0
        for i in range(n):
            cb[i] /= denom
        ev.set_result(cb)

    def on_closeness(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        results = {}
        for i in range(n):
            dists = self._bfs_distances(g, i)
            total_dist = sum(d for d in dists if d > 0)
            reachable = sum(1 for d in dists if d > 0)
            results[i] = (reachable / total_dist) if total_dist > 0 else 0.0
        ev.set_result(results)

    def _bfs_distances(self, g, src):
        n = g.get_vertex_count()
        dists = [-1] * n
        dists[src] = 0
        queue = collections.deque([src])
        while queue:
            u = queue.popleft()
            for v in range(n):
                if g.has_edge(u, v) and dists[v] < 0:
                    dists[v] = dists[u] + 1
                    queue.append(v)
        return dists

    def on_pagerank(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        d = 0.85
        pr = [1.0 / n] * n
        for _ in range(100):
            new_pr = [(1.0 - d) / n] * n
            # Redistribui PageRank de dangling nodes (out-degree 0)
            dangling_sum = sum(pr[i] for i in range(n) if g.get_vertex_out_degree(i) == 0)
            for i in range(n):
                new_pr[i] += d * (dangling_sum / n)
            
            for u in range(n):
                out_deg = g.get_vertex_out_degree(u)
                if out_deg > 0:
                    for v in range(n):
                        if g.has_edge(u, v):
                            new_pr[v] += d * (pr[u] / out_deg)
            
            diff = sum(abs(new_pr[i] - pr[i]) for i in range(n))
            pr = new_pr
            if diff < 1e-6:
                break
        ev.set_result({i: pr[i] for i in range(n)})

    def on_density(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        e = g.get_edge_count()
        denom = n * (n - 1) if n > 1 else 1.0
        ev.set_result(float(e) / denom)

    def on_clustering(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        results = {}
        for i in range(n):
            neighbors = []
            for j in range(n):
                if i != j and (g.has_edge(i, j) or g.has_edge(j, i)):
                    neighbors.append(j)
            
            k = len(neighbors)
            if k < 2:
                results[i] = 0.0
                continue
            
            links = 0
            for idx1 in range(k):
                for idx2 in range(idx1 + 1, k):
                    u, v = neighbors[idx1], neighbors[idx2]
                    if g.has_edge(u, v) or g.has_edge(v, u):
                        links += 1
            results[i] = (2.0 * links) / (k * (k - 1))
        ev.set_result(results)

    def on_assortativity(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        edges = []
        for u in range(n):
            for v in range(n):
                if g.has_edge(u, v):
                    edges.append((u, v))
        
        if not edges:
            ev.set_result(0.0)
            return

        m = len(edges)
        k_in = [g.get_vertex_in_degree(i) for i in range(n)]
        k_out = [g.get_vertex_out_degree(i) for i in range(n)]
        
        sum_xy = sum(k_out[u] * k_in[v] for u, v in edges)
        sum_x = sum(k_out[u] for u, v in edges)
        sum_y = sum(k_in[v] for u, v in edges)
        sum_x2 = sum(k_out[u]**2 for u, v in edges)
        sum_y2 = sum(k_in[v]**2 for u, v in edges)
        
        num = (m * sum_xy) - (sum_x * sum_y)
        den = ((m * sum_x2 - sum_x**2) * (m * sum_y2 - sum_y**2))**0.5
        ev.set_result(num / den if den != 0 else 0.0)

    def on_community_detection(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        community = list(range(n))
        nodes = list(range(n))
        
        for _ in range(20):
            random.shuffle(nodes)
            changed = False
            for u in nodes:
                counts = collections.defaultdict(int)
                for v in range(n):
                    if g.has_edge(u, v) or g.has_edge(v, u):
                        counts[community[v]] += 1
                if counts:
                    max_count = max(counts.values())
                    best_comm = [c for c, count in counts.items() if count == max_count]
                    new_c = random.choice(best_comm)
                    if community[u] != new_c:
                        community[u] = new_c
                        changed = True
            if not changed:
                break
        
        # Mantendo o comportamento original do Java (mesmo com a anomalia de normalização)
        ev.set_result({i: community[i] for i in range(n)})

    def on_bridging_ties(self, ev: Event):
        # Primeiro detecta comunidades
        self.on_community_detection(ev)
        communities = ev.result
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        bridging = set()
        for u in range(n):
            for v in range(n):
                if g.has_edge(u, v) and communities[u] != communities[v]:
                    bridging.add(u)
                    bridging.add(v)
        ev.set_result(sorted(list(bridging)))
