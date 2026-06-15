from collections import defaultdict

from grafos import AdjacencyListGraph


INTERACTION_WEIGHTS = {"comment": 2.0, "issue_response": 3.0, "review": 4.0, "merge": 5.0, "issue_close": 4.0}


def build_graphs(interactions: list[dict]) -> tuple[dict[str, AdjacencyListGraph], dict[str, int]]:
    users = sorted({item[key] for item in interactions for key in ("source", "target") if item.get(key)})
    user_index = {user: index for index, user in enumerate(users)}
    categories = {"comments": {"comment", "issue_response"}, "issues": {"issue_close"}, "pull_requests": {"review", "merge"}}
    graphs = {name: AdjacencyListGraph(len(users)) for name in [*categories, "integrated"]}
    totals: defaultdict[tuple[int, int], float] = defaultdict(float)
    for graph in graphs.values():
        for user, index in user_index.items():
            graph.setVertexLabel(index, user)
    for item in interactions:
        if item.get("source") == item.get("target") or item.get("type") not in INTERACTION_WEIGHTS:
            continue
        u, v = user_index[item["source"]], user_index[item["target"]]
        for name, accepted in categories.items():
            if item["type"] in accepted:
                graphs[name].addEdge(u, v)
        graphs["integrated"].addEdge(u, v)
        totals[(u, v)] += INTERACTION_WEIGHTS[item["type"]]
    for (u, v), weight in totals.items():
        graphs["integrated"].setEdgeWeight(u, v, weight)
    return graphs, user_index