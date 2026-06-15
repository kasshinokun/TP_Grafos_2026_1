import collections
import heapq
from ..events.event_type import EventType
from ..events.event import Event
from ..events.event_bus import EventBus
from ..core.graph_registry import GraphRegistry

class AlgorithmHandler:
    def __init__(self, registry: GraphRegistry):
        self.registry = registry

    def register_all(self, bus: EventBus):
        bus.subscribe(EventType.ALGO_BFS, self.on_bfs)
        bus.subscribe(EventType.ALGO_DFS, self.on_dfs)
        bus.subscribe(EventType.ALGO_SHORTEST_PATH, self.on_shortest_path)
        bus.subscribe(EventType.ALGO_TOPOLOGICAL_SORT, self.on_topological_sort)
        bus.subscribe(EventType.ALGO_STRONGLY_CONNECTED, self.on_scc)

    def on_bfs(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        src = ev.get_int("source")
        g.check_vertex(src)
        n = g.get_vertex_count()
        visited = [False] * n
        order = []
        queue = collections.deque([src])
        visited[src] = True
        while queue:
            cur = queue.popleft()
            order.append(cur)
            for j in range(n):
                if not visited[j] and g.has_edge(cur, j):
                    visited[j] = True
                    queue.append(j)
        ev.set_result(order)

    def on_dfs(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        src = ev.get_int("source")
        g.check_vertex(src)
        n = g.get_vertex_count()
        visited = [False] * n
        order = []
        self._dfs_recursive(g, src, visited, order)
        ev.set_result(order)

    def _dfs_recursive(self, g, v, visited, order):
        visited[v] = True
        order.append(v)
        for j in range(g.get_vertex_count()):
            if not visited[j] and g.has_edge(v, j):
                self._dfs_recursive(g, j, visited, order)

    def on_shortest_path(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        src = ev.get_int("source")
        target = ev.get_int("target")
        n = g.get_vertex_count()
        g.check_vertex(src)
        g.check_vertex(target)
        
        dist = [float('inf')] * n
        prev = [-1] * n
        done = [False] * n
        dist[src] = 0.0
        
        pq = [(0.0, src)]
        while pq:
            d, u = heapq.heappop(pq)
            if done[u]: continue
            done[u] = True
            if u == target: break
            
            for v in range(n):
                if g.has_edge(u, v):
                    w = g.get_edge_weight(u, v)
                    if dist[u] + w < dist[v]:
                        dist[v] = dist[u] + w
                        prev[v] = u
                        heapq.heappush(pq, (dist[v], v))
        
        path = []
        if dist[target] == float('inf'):
            ev.set_result({"path": path, "dist": float('inf'), "reachable": False})
            return
        
        curr = target
        while curr != -1:
            path.insert(0, curr)
            curr = prev[curr]
        ev.set_result({"path": path, "dist": dist[target], "reachable": True})

    def on_topological_sort(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        in_deg = [0] * n
        for u in range(n):
            for v in range(n):
                if g.has_edge(u, v):
                    in_deg[v] += 1
        
        queue = collections.deque([i for i in range(n) if in_deg[i] == 0])
        sorted_nodes = []
        while queue:
            u = queue.popleft()
            sorted_nodes.append(u)
            for v in range(n):
                if g.has_edge(u, v):
                    in_deg[v] -= 1
                    if in_deg[v] == 0:
                        queue.append(v)
        ev.set_result(sorted_nodes if len(sorted_nodes) == n else None)

    def on_scc(self, ev: Event):
        g = self.registry.get(ev.get_string("graphId"))
        n = g.get_vertex_count()
        visited = [False] * n
        stack = []
        
        for i in range(n):
            if not visited[i]:
                self._fill_order(g, i, visited, stack)
        
        visited = [False] * n
        sccs = []
        while stack:
            v = stack.pop()
            if not visited[v]:
                comp = []
                self._dfs_transposed(g, v, visited, comp)
                sccs.append(comp)
        ev.set_result(sccs)

    def _fill_order(self, g, v, visited, stack):
        visited[v] = True
        for j in range(g.get_vertex_count()):
            if not visited[j] and g.has_edge(v, j):
                self._fill_order(g, j, visited, stack)
        stack.append(v)

    def _dfs_transposed(self, g, v, visited, comp):
        visited[v] = True
        comp.append(v)
        for j in range(g.get_vertex_count()):
            if not visited[j] and g.has_edge(j, v):
                self._dfs_transposed(g, j, visited, comp)
