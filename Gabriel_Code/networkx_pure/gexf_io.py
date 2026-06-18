"""
Leitor e gravador minimalista de arquivos GEXF (Gephi Exchange Format).

Suporta o subconjunto suficiente para o TCC:
    - <graph defaultedgetype="directed|undirected">
    - <nodes><node id="..." label="..." /></nodes>
    - <edges><edge id="..." source="..." target="..." weight="..." /></edges>

Compatível com os arquivos exportados pelo método `export_to_gephi` do
`AbstractGraph`. Retorna um `AdjacencyListGraph` populado.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Tuple

from grafo.graph.adjacency_list_graph import AdjacencyListGraph
from grafo.graph.abstract_graph import AbstractGraph


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def read_gexf(path: str | Path) -> Tuple[AdjacencyListGraph, bool]:
    """Lê um .gexf e devolve (grafo, direcionado?)."""
    tree = ET.parse(str(path))
    root = tree.getroot()

    graph_elem = next((c for c in root.iter() if _strip_ns(c.tag) == "graph"), None)
    if graph_elem is None:
        raise ValueError("Arquivo GEXF inválido: <graph> ausente.")
    directed = graph_elem.attrib.get("defaultedgetype", "directed").lower() == "directed"

    id_to_idx: dict[str, int] = {}
    labels: list[str] = []
    for node in (c for c in graph_elem.iter() if _strip_ns(c.tag) == "node"):
        nid = node.attrib["id"]
        if nid in id_to_idx:
            continue
        id_to_idx[nid] = len(id_to_idx)
        labels.append(node.attrib.get("label", nid))

    if not id_to_idx:
        raise ValueError("GEXF sem nós.")

    g = AdjacencyListGraph(len(id_to_idx))
    for idx, lbl in enumerate(labels):
        g.set_vertex_label(idx, lbl)

    for edge in (c for c in graph_elem.iter() if _strip_ns(c.tag) == "edge"):
        src = id_to_idx[edge.attrib["source"]]
        dst = id_to_idx[edge.attrib["target"]]
        if src == dst:
            continue  # GEXF pode ter loops; AbstractGraph proíbe
        weight = float(edge.attrib.get("weight", 1.0))
        if not g.has_edge(src, dst):
            g.set_edge_weight(src, dst, weight)
        if not directed and not g.has_edge(dst, src):
            g.set_edge_weight(dst, src, weight)
    return g, directed


def write_gexf(graph: AbstractGraph, path: str | Path, directed: bool = True) -> None:
    """Escreve um `AbstractGraph` no formato GEXF (compatível com Gephi)."""
    n = graph.get_vertex_count()
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<gexf xmlns="http://www.gexf.net/1.3" version="1.3">',
        f'<graph mode="static" defaultedgetype="{"directed" if directed else "undirected"}">',
        "<nodes>",
    ]
    for v in range(n):
        lines.append(f'<node id="{v}" label="{graph.get_vertex_label(v)}" />')
    lines.append("</nodes><edges>")
    eid = 0
    for u in range(n):
        for v in range(n):
            if u == v or not graph.has_edge(u, v):
                continue
            w = graph.get_edge_weight(u, v)
            lines.append(f'<edge id="{eid}" source="{u}" target="{v}" weight="{w}" />')
            eid += 1
    lines.append("</edges></graph></gexf>")
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
