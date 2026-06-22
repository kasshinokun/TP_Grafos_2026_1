"""Construção dos 4 grafos exigidos pela Etapa 1 do trabalho prático
(ver tp-es_Atualizado.pdf), a partir da lista de interações minerada:

    Grafo 1 — comentários em issues ou pull requests        (tipo 'comment')
    Grafo 2 — fechamento de issue por outro usuário          (tipo 'issue_commented')
    Grafo 3 — revisões/aprovações e merges de pull requests  (tipos 'review' e 'merge')
    Grafo integrado — combinação ponderada de todas as interações
        (pesos conforme o PDF: comment=2, issue_commented=3, review=4, merge=5)

Equivalente, no estágio v2b, ao `grafo/handlers/mining_handler.py` do
estágio beta — porém como funções simples, sem barramento de eventos.
"""
import csv
import os
from typing import Any, Dict, List

from grafo.graph.adjacency_list_graph import AdjacencyListGraph

# Pesos das interações conforme o PDF do trabalho prático
WEIGHTS = {
    'comment': 2,
    'issue_commented': 3,
    'review': 4,
    'merge': 5,
}

# Quais tipos de interação compõem cada um dos 3 grafos separados
GRAPH1_TYPES = {'comment'}
GRAPH2_TYPES = {'issue_commented'}
GRAPH3_TYPES = {'review', 'merge'}

# Colunas obrigatórias do CSV de interações (formato exportado por
# MinerScreen._export_result_csv: actor,target,type)
CSV_REQUIRED_COLUMNS = ("actor", "target", "type")

# Mapeamento de normalização de 'type': aceita tanto o vocabulário atual
# (minúsculo, usado por graph_builder/common_miner) quanto o vocabulário
# legado de uma versão anterior do minerador (maiúsculo, com nomes mais
# descritivos) — comparação sempre case-insensitive.
_LEGACY_TYPE_ALIASES = {
    'comment': 'comment',
    'comment_on_issue_or_pr': 'comment',
    'issue_commented': 'issue_commented',
    'issue_closed_by_other': 'issue_commented',
    'review': 'review',
    'pr_review_or_approval': 'review',
    'merge': 'merge',
    'pr_merge': 'merge',
}


def normalize_interaction_type(raw_type: str):
    """Normaliza um valor de 'type' (de qualquer um dos dois vocabulários
    suportados, em qualquer combinação de maiúsculas/minúsculas) para um
    dos 4 tipos canônicos usados por WEIGHTS/GRAPH*_TYPES. Retorna None se
    o valor não for reconhecido em nenhum dos dois vocabulários."""
    if not raw_type:
        return None
    return _LEGACY_TYPE_ALIASES.get(raw_type.strip().lower())


class CSVValidationError(ValueError):
    """Erro de validação do arquivo .csv de interações (estrutura ou
    conteúdo inválido) — pensado para ser exibido diretamente ao usuário
    na GUI, por isso a mensagem já vem pronta para leitura humana."""
    pass


def load_interactions_csv(path: str) -> List[Dict[str, Any]]:
    """Lê e valida um arquivo .csv de interações no formato
    'actor,target,type' (uma linha por interação autor→mencionado),
    aceito tanto no vocabulário de 'type' atual quanto no legado (ver
    `normalize_interaction_type`), e retorna a lista de interações no
    formato esperado por `build_all_graphs`.

    Levanta CSVValidationError com uma mensagem amigável caso o arquivo
    não exista, esteja vazio, tenha colunas faltando, ou não contenha
    nenhuma linha válida após a normalização.
    """
    if not path or not os.path.isfile(path):
        raise CSVValidationError(f"Arquivo não encontrado: {path}")

    try:
        with open(path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = [h.strip().lower() for h in (reader.fieldnames or [])]
            missing = [c for c in CSV_REQUIRED_COLUMNS if c not in fieldnames]
            if missing:
                raise CSVValidationError(
                    "Cabeçalho do CSV inválido. Colunas obrigatórias ausentes: "
                    + ", ".join(missing) +
                    f"\nEsperado: {','.join(CSV_REQUIRED_COLUMNS)}"
                )

            # DictReader usa exatamente as chaves do cabeçalho original
            # (preserva maiúsculas/minúsculas) — mapeamos para as colunas
            # normalizadas para poder ler de forma robusta.
            col_map = {h.strip().lower(): h for h in (reader.fieldnames or [])}

            interactions: List[Dict[str, Any]] = []
            skipped_rows = 0
            unknown_types = set()

            for row_num, row in enumerate(reader, start=2):  # linha 1 = cabeçalho
                actor = (row.get(col_map["actor"]) or "").strip()
                target = (row.get(col_map["target"]) or "").strip()
                raw_type = (row.get(col_map["type"]) or "").strip()

                if not actor or not target:
                    skipped_rows += 1
                    continue

                norm_type = normalize_interaction_type(raw_type)
                if norm_type is None:
                    unknown_types.add(raw_type)
                    skipped_rows += 1
                    continue

                interactions.append({
                    "author": actor,
                    "mentions": [target],
                    "type": norm_type,
                })

        if not interactions:
            detail = ""
            if unknown_types:
                detail = (
                    "\nValores de 'type' não reconhecidos: "
                    + ", ".join(sorted(unknown_types))
                )
            raise CSVValidationError(
                f"Nenhuma interação válida encontrada em '{os.path.basename(path)}'."
                + detail
            )

        return interactions

    except CSVValidationError:
        raise
    except (OSError, UnicodeDecodeError, csv.Error) as ex:
        raise CSVValidationError(f"Falha ao ler '{os.path.basename(path)}': {ex}")


def _unique_users(interactions: List[Dict[str, Any]]) -> List[str]:
    """Lista de usuários únicos (autor + menções), em ordem de aparição
    para evitar reembaralhar nomes a cada chamada."""
    users: List[str] = []
    seen = set()
    for inter in interactions:
        for user in [inter.get('author')] + list(inter.get('mentions', [])):
            if user and user not in seen:
                seen.add(user)
                users.append(user)
    return users


def _build_simple_graph(interactions: List[Dict[str, Any]]) -> AdjacencyListGraph:
    """Grafo simples (sem peso) a partir de um subconjunto de interações:
    uma aresta autor->mencionado por interação (idempotente, sem laços)."""
    users = _unique_users(interactions)
    if not users:
        return AdjacencyListGraph(0)

    user_to_idx = {u: i for i, u in enumerate(users)}
    g = AdjacencyListGraph(len(users))
    for i, u in enumerate(users):
        g.vertex_labels[i] = u

    for inter in interactions:
        src = user_to_idx.get(inter.get('author'))
        if src is None:
            continue
        for mention in inter.get('mentions', []):
            tgt = user_to_idx.get(mention)
            if tgt is None or src == tgt:
                continue
            g.add_edge(src, tgt)

    return g


def _build_weighted_graph(interactions: List[Dict[str, Any]]) -> AdjacencyListGraph:
    """Grafo integrado: combinação ponderada de todas as interações,
    somando pesos quando já existe aresta entre o mesmo par de usuários."""
    users = _unique_users(interactions)
    if not users:
        return AdjacencyListGraph(0)

    user_to_idx = {u: i for i, u in enumerate(users)}
    g = AdjacencyListGraph(len(users))
    for i, u in enumerate(users):
        g.vertex_labels[i] = u

    for inter in interactions:
        src = user_to_idx.get(inter.get('author'))
        if src is None:
            continue
        weight = WEIGHTS.get(inter.get('type'), 1)
        for mention in inter.get('mentions', []):
            tgt = user_to_idx.get(mention)
            if tgt is None or src == tgt:
                continue
            if g.has_edge(src, tgt):
                current = g.get_edge_weight(src, tgt)
                g.set_edge_weight(src, tgt, current + weight)
            else:
                g.add_edge(src, tgt)
                g.set_edge_weight(src, tgt, weight)

    return g


def build_all_graphs(interactions: List[Dict[str, Any]]) -> Dict[str, AdjacencyListGraph]:
    """Constrói os 4 grafos exigidos pela Etapa 1 a partir da lista bruta
    de interações mineradas. Retorna um dicionário:

        {'graph1': ..., 'graph2': ..., 'graph3': ..., 'graph_integrado': ...}
    """
    graph1 = [i for i in interactions if i.get('type') in GRAPH1_TYPES]
    graph2 = [i for i in interactions if i.get('type') in GRAPH2_TYPES]
    graph3 = [i for i in interactions if i.get('type') in GRAPH3_TYPES]

    return {
        'graph1': _build_simple_graph(graph1),
        'graph2': _build_simple_graph(graph2),
        'graph3': _build_simple_graph(graph3),
        'graph_integrado': _build_weighted_graph(interactions),
    }
