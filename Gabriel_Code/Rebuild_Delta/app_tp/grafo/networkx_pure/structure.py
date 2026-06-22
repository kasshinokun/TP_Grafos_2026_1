def density(adapter):
    n = adapter.number_of_nodes()
    max_edges = n * (n - 1)
    return adapter.number_of_edges() / max_edges if max_edges > 0 else 0

def clustering_coefficient(adapter):
    cc_values = {}
    for i in adapter.nodes():
        neighbors = set(adapter.neighbors(i))
        k = len(neighbors)
        if k < 2: cc_values[i] = 0.0; continue
        triangles = sum(1 for a in neighbors for b in neighbors if a < b and b in set(adapter.neighbors(a)))
        cc_values[i] = (2 * triangles) / (k * (k - 1))
    return cc_values

def average_clustering(adapter):
    cc = clustering_coefficient(adapter)
    return sum(cc.values()) / len(cc) if cc else 0

def assortativity(adapter):
    edges = adapter.edges()
    if not edges: return 0.0
    src_deg = [adapter.out_degree(u) for u, v in edges]
    tgt_deg = [adapter.in_degree(v) for u, v in edges]
    m = len(edges)
    mean_s, mean_t = sum(src_deg)/m, sum(tgt_deg)/m
    num = sum((src_deg[i]-mean_s)*(tgt_deg[i]-mean_t) for i in range(m))
    den = (sum((s-mean_s)**2 for s in src_deg)**0.5) * (sum((t-mean_t)**2 for t in tgt_deg)**0.5)
    return num / den if den > 0 else 0


# ----------------------------------------------------------------------
# Heurísticas estruturais (classificação qualitativa do grafo)
# ----------------------------------------------------------------------
# As funções abaixo não calculam uma métrica numérica isolada; aplicam
# pequenas heurísticas de teoria dos grafos para descrever, em termos
# qualitativos, "que tipo" de estrutura o grafo tem — úteis para uma
# inspeção rápida (ex.: botão "Mostrar estrutura" de uma GUI).

def isolated_vertices(adapter):
    """Vértices sem nenhuma aresta incidente (grau total 0) — nem
    sucessores, nem predecessores."""
    return [u for u in adapter.nodes()
            if adapter.in_degree(u) == 0 and adapter.out_degree(u) == 0]


def source_vertices(adapter):
    """Vértices "fonte": têm pelo menos uma aresta saindo, mas nenhuma
    entrando (grau de entrada 0). Em um grafo não direcionado, um
    vértice só é fonte se também estiver isolado (in_degree e
    out_degree são sempre iguais), então esta heurística é mais
    informativa em grafos direcionados."""
    return [u for u in adapter.nodes()
            if adapter.in_degree(u) == 0 and adapter.out_degree(u) > 0]


def sink_vertices(adapter):
    """Vértices "sorvedouro": têm pelo menos uma aresta entrando, mas
    nenhuma saindo (grau de saída 0)."""
    return [u for u in adapter.nodes()
            if adapter.out_degree(u) == 0 and adapter.in_degree(u) > 0]


def is_regular(adapter) -> bool:
    """Um grafo é regular se todos os vértices têm o mesmo grau total
    (entrada + saída). Grafo vazio (sem vértices) é considerado regular
    por convenção (vacuously true), assim como em teoria dos conjuntos."""
    nodes = adapter.nodes()
    if not nodes:
        return True
    degrees = {adapter.in_degree(u) + adapter.out_degree(u) for u in nodes}
    return len(degrees) == 1


def degree_extremes(adapter):
    """Retorna (vertice_max_grau, grau_max, vertice_min_grau, grau_min)
    considerando o grau total (entrada + saída) de cada vértice. Útil
    para identificar rapidamente "hubs" (alto grau) e vértices quase
    isolados (baixo grau) sem precisar inspecionar toda a sequência."""
    nodes = adapter.nodes()
    if not nodes:
        return None
    degrees = [(u, adapter.in_degree(u) + adapter.out_degree(u)) for u in nodes]
    max_v, max_d = max(degrees, key=lambda t: t[1])
    min_v, min_d = min(degrees, key=lambda t: t[1])
    return max_v, max_d, min_v, min_d


def classify_topology(adapter) -> str:
    """Heurística simples de classificação qualitativa da topologia do
    grafo, combinando densidade, regularidade e presença de vértices
    isolados. Não é uma classificação formal/exaustiva da literatura —
    é um resumo de leitura rápida para quem está inspecionando o grafo
    manualmente (ex.: na tela de API Primitiva).

    Ordem de prioridade das heurísticas (da mais específica à mais
    genérica): grafo vazio -> sem arestas -> completo -> regular ->
    com vértices isolados -> denso/esparso por limiar de densidade.
    """
    n = adapter.number_of_nodes()
    m = adapter.number_of_edges()

    if n == 0:
        return "Grafo vazio (sem vértices)."
    if m == 0:
        return "Grafo trivial: sem nenhuma aresta (todos os vértices isolados)."

    d = density(adapter)
    max_edges = n * (n - 1)
    if max_edges > 0 and m == max_edges:
        return "Grafo completo: toda dupla de vértices distintos está conectada."

    isolated = isolated_vertices(adapter)
    if is_regular(adapter):
        max_v, max_d, _, _ = degree_extremes(adapter)
        return f"Grafo regular: todos os vértices têm grau total {max_d}."
    if isolated:
        plural = "s" if len(isolated) != 1 else ""
        return (
            f"Grafo desconexo com {len(isolated)} vértice{plural} isolado{plural} "
            f"(densidade {d:.3f})."
        )
    if d >= 0.5:
        return f"Grafo denso (densidade {d:.3f}, próximo de um grafo completo)."
    return f"Grafo esparso (densidade {d:.3f}, poucas arestas em relação ao máximo possível)."


def structural_summary(adapter) -> dict:
    """Agrega as heurísticas acima num único dicionário, pronto para
    ser formatado por uma camada de apresentação (GUI, CLI, relatório).
    Não inclui a matriz/lista de adjacência completas (isso fica em
    `grafo.utils.graph_structure`, que opera sobre o AbstractGraph
    diretamente e lida melhor com a formatação tabular)."""
    n = adapter.number_of_nodes()
    extremes = degree_extremes(adapter)
    return {
        "num_vertices": n,
        "num_edges": adapter.number_of_edges(),
        "density": density(adapter),
        "is_regular": is_regular(adapter),
        "isolated_vertices": isolated_vertices(adapter),
        "source_vertices": source_vertices(adapter),
        "sink_vertices": sink_vertices(adapter),
        "max_degree_vertex": extremes[0] if extremes else None,
        "max_degree": extremes[1] if extremes else None,
        "min_degree_vertex": extremes[2] if extremes else None,
        "min_degree": extremes[3] if extremes else None,
        "topology_classification": classify_topology(adapter),
    }