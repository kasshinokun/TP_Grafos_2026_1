# ./grafo/utils/graph_structure.py
"""Representações estruturais "didáticas" de um grafo (API Obrigatória).

Diferente de `grafo/networkx_pure/structure.py` (que opera sobre
`GraphAdapter` e calcula métricas agregadas como densidade/clustering),
este módulo trabalha diretamente sobre `AbstractGraph` — a mesma
camada usada por `grafo/utils/gexf_parser.py` — e produz as
representações estruturais "clássicas" de teoria dos grafos usadas
para inspeção manual: matriz de adjacência, lista de adjacência e
sequência de graus.

Usa apenas a API pública de `AbstractGraph` (has_edge, get_edge_weight,
get_vertex_in_degree/out_degree, get_vertex_count) — nenhuma destas
funções acessa atributos internos de uma implementação concreta (como
`adj`/`rev_adj` de `AdjacencyListGraph`), então funcionam igualmente
sobre lista de adjacência, matriz de adjacência ou grafo não
direcionado.
"""
from typing import Dict, List, Tuple

from grafo.graph.abstract_graph import AbstractGraph


def adjacency_matrix(graph: AbstractGraph) -> List[List[float]]:
    """Monta a matriz de adjacência N x N do grafo.

    matrix[u][v] é o peso da aresta u -> v, ou 0.0 se a aresta não
    existir (ou se u == v, já que grafos simples não têm laços).
    """
    n = graph.get_vertex_count()
    matrix = [[0.0] * n for _ in range(n)]
    for u in range(n):
        for v in range(n):
            if u == v:
                continue
            if graph.has_edge(u, v):
                matrix[u][v] = graph.get_edge_weight(u, v)
    return matrix


def adjacency_list(graph: AbstractGraph) -> Dict[int, List[Tuple[int, float]]]:
    """Monta a lista de adjacência: para cada vértice u, a lista de
    pares (v, peso) tal que existe a aresta u -> v."""
    n = graph.get_vertex_count()
    result: Dict[int, List[Tuple[int, float]]] = {}
    for u in range(n):
        succ = []
        for v in range(n):
            if u != v and graph.has_edge(u, v):
                succ.append((v, graph.get_edge_weight(u, v)))
        result[u] = succ
    return result


def degree_sequence(graph: AbstractGraph) -> List[Tuple[int, int, int]]:
    """Sequência de graus: lista de (vértice, grau_entrada, grau_saída),
    ordenada por índice do vértice."""
    n = graph.get_vertex_count()
    return [
        (u, graph.get_vertex_in_degree(u), graph.get_vertex_out_degree(u))
        for u in range(n)
    ]


def format_adjacency_matrix(graph: AbstractGraph, max_vertices: int = 25) -> str:
    """Formata a matriz de adjacência como texto tabular monoespaçado,
    usando os rótulos dos vértices (truncados) como cabeçalho de linha
    e coluna.

    `max_vertices` evita gerar uma matriz gigantesca e ilegível para
    grafos grandes (a matriz cresce O(n²) em área impressa); acima
    desse limite, retorna um aviso sugerindo a lista de adjacência.
    """
    n = graph.get_vertex_count()
    if n == 0:
        return "(grafo vazio — sem vértices)"
    if n > max_vertices:
        return (
            f"Matriz de adjacência omitida: o grafo tem {n} vértices "
            f"(limite de exibição: {max_vertices}). Para grafos grandes, "
            f"a lista de adjacência abaixo é mais legível."
        )

    matrix = adjacency_matrix(graph)
    short_labels = [_short_label(graph, i) for i in range(n)]
    col_width = max(4, max(len(lbl) for lbl in short_labels) + 1)

    header = " " * (col_width + 1) + "".join(
        lbl.rjust(col_width) for lbl in short_labels
    )
    lines = [header]
    for i in range(n):
        row_cells = []
        for j in range(n):
            w = matrix[i][j]
            cell = "·" if w == 0.0 else (f"{w:g}" if w != 1.0 else "1")
            row_cells.append(cell.rjust(col_width))
        lines.append(short_labels[i].rjust(col_width) + " " + "".join(row_cells))
    return "\n".join(lines)


def format_adjacency_list(graph: AbstractGraph, max_vertices: int = 200) -> str:
    """Formata a lista de adjacência como texto, uma linha por vértice,
    no formato `rotulo (idx) -> rotulo2 (idx2) [peso], ...`."""
    n = graph.get_vertex_count()
    if n == 0:
        return "(grafo vazio — sem vértices)"
    if n > max_vertices:
        return (
            f"Lista de adjacência omitida: o grafo tem {n} vértices "
            f"(limite de exibição: {max_vertices})."
        )

    adj = adjacency_list(graph)
    lines = []
    for u in range(n):
        label_u = graph.vertex_labels.get(u, str(u))
        succ = adj[u]
        if not succ:
            lines.append(f"  {label_u} ({u}) -> (nenhum sucessor)")
            continue
        succ_str = ", ".join(
            f"{graph.vertex_labels.get(v, str(v))} ({v})"
            + ("" if w == 1.0 else f" [peso {w:g}]")
            for v, w in succ
        )
        lines.append(f"  {label_u} ({u}) -> {succ_str}")
    return "\n".join(lines)


def format_degree_sequence(graph: AbstractGraph, max_vertices: int = 200) -> str:
    """Formata a sequência de graus como texto, uma linha por vértice."""
    n = graph.get_vertex_count()
    if n == 0:
        return "(grafo vazio — sem vértices)"
    if n > max_vertices:
        return (
            f"Sequência de graus omitida: o grafo tem {n} vértices "
            f"(limite de exibição: {max_vertices})."
        )
    lines = []
    for u, din, dout in degree_sequence(graph):
        label_u = graph.vertex_labels.get(u, str(u))
        lines.append(f"  {label_u} ({u}): grau_entrada={din}, grau_saída={dout}, grau_total={din + dout}")
    return "\n".join(lines)


def _short_label(graph: AbstractGraph, idx: int, max_len: int = 6) -> str:
    """Rótulo curto de um vértice, usado como cabeçalho da matriz de
    adjacência (a matriz precisa de colunas estreitas para caber em
    tela/console)."""
    label = str(graph.vertex_labels.get(idx, idx))
    if len(label) > max_len:
        return label[: max_len - 1] + "…"
    return label
