# grafos_runner.py — REV A
# Varredura de ./json/ e construção de grafos com as implementações de v1d/grafos/.
# Estratégia mínima e tolerante: se o módulo v1d.grafos não estiver disponível,
# devolve um resumo sem falhar.
#
# Heurística de construção:
#   - Cada arquivo .json em ./json/ é lido como dict ou lista de dicts.
#   - Para cada registro com par (user, target) ou (author, repo) ou (from, to)
#     adicionamos uma aresta dirigida no AdjacencyListGraph (rotulando vértices
#     por hash incremental dos identificadores encontrados).
#   - Retornamos um sumário {arquivos, vertices, arestas}.

from __future__ import annotations

import os
import json
import logging
from typing import Iterable, Tuple, Optional

log = logging.getLogger(__name__)


def _iter_records(obj) -> Iterable[dict]:
    if isinstance(obj, dict):
        # tenta achaves comuns que aninham listas
        for k in ("items", "data", "events", "commits", "issues", "prs"):
            v = obj.get(k)
            if isinstance(v, list):
                yield from (r for r in v if isinstance(r, dict))
                return
        yield obj
    elif isinstance(obj, list):
        for r in obj:
            if isinstance(r, dict):
                yield r


def _extract_edge(rec: dict) -> Optional[Tuple[str, str]]:
    pairs = (
        ("user", "target"),
        ("author", "repo"),
        ("from", "to"),
        ("source", "target"),
        ("login", "repo_full_name"),
    )
    for a, b in pairs:
        if a in rec and b in rec and rec[a] and rec[b]:
            return str(rec[a]), str(rec[b])
    return None


def run_graphs(json_dir: str) -> dict:
    """Constrói um grafo (AdjacencyListGraph) varrendo ./json/. Retorna sumário."""
    try:
        from v1d.grafos import AdjacencyListGraph
    except Exception as e:
        log.warning(f"v1d.grafos indisponível: {e}")
        return {"files": 0, "vertices": 0, "edges": 0, "warning": str(e)}

    if not os.path.isdir(json_dir):
        return {"files": 0, "vertices": 0, "edges": 0, "warning": "json_dir ausente"}

    files = [f for f in os.listdir(json_dir) if f.endswith(".json")]
    edges: list[Tuple[str, str]] = []
    for fname in files:
        try:
            with open(os.path.join(json_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            log.warning(f"Falha ao ler {fname}: {e}")
            continue
        for rec in _iter_records(data):
            e = _extract_edge(rec)
            if e:
                edges.append(e)

    # mapeia rótulos para inteiros
    label_to_id: dict[str, int] = {}
    for u, v in edges:
        for x in (u, v):
            if x not in label_to_id:
                label_to_id[x] = len(label_to_id)

    n = max(len(label_to_id), 1)
    g = AdjacencyListGraph(n)
    added = 0
    for u, v in edges:
        iu, iv = label_to_id[u], label_to_id[v]
        if iu == iv:
            continue
        try:
            if not g.hasEdge(iu, iv):
                g.addEdge(iu, iv)
                added += 1
        except Exception:
            pass

    summary = {"files": len(files), "vertices": len(label_to_id), "edges": added}
    log.info(f"grafos_runner: {summary}")
    return summary


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    d = sys.argv[1] if len(sys.argv) > 1 else "./json"
    print(run_graphs(d))
