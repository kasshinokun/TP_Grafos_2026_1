import random
from collections import defaultdict

def label_propagation_communities(adapter):
    labels = {i: i for i in adapter.nodes()}
    nodes = list(adapter.nodes())
    for _ in range(100):
        random.shuffle(nodes)
        changed = False
        for v in nodes:
            neighbors = adapter.neighbors(v)
            if not neighbors: continue
            freq = defaultdict(int)
            for nb in neighbors: freq[labels[nb]] += 1
            max_freq = max(freq.values())
            new_label = random.choice([l for l, c in freq.items() if c == max_freq])
            if labels[v] != new_label: labels[v] = new_label; changed = True
        if not changed: break
    comms = defaultdict(list)
    for i, lbl in labels.items(): comms[lbl].append(i)
    return list(comms.values())

def modularity(adapter, communities):
    m = adapter.number_of_edges()
    if m == 0: return 0.0
    node_to_comm = {node: c_idx for c_idx, comm in enumerate(communities) for node in comm}
    Q = sum(1 - ((adapter.out_degree(u)+adapter.in_degree(u)) * (adapter.out_degree(v)+adapter.in_degree(v))) / (2*m) 
            for u in adapter.nodes() for v in adapter.successors(u) if node_to_comm.get(u) == node_to_comm.get(v))
    return Q / (2 * m)

def bridging_ties(adapter):
    comms = label_propagation_communities(adapter)
    node_to_comm = {node: c_idx for c_idx, comm in enumerate(comms) for node in comm}
    return {i: len(set(node_to_comm[nb] for nb in adapter.neighbors(i) if nb in node_to_comm)) for i in adapter.nodes()}