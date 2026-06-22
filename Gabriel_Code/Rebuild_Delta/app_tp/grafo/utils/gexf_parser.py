# ./grafo/utils/gexf_parser.py

"""Parser nativo XML para arquivos GEXF, com detecção de tipo de grafo."""
import xml.etree.ElementTree as ET
from grafo.graph.adjacency_list_graph import AdjacencyListGraph
from grafo.graph.undirected_graph import UndirectedGraph
from grafo.graph.abstract_graph import AbstractGraph
from typing import Type, Optional


def load_gexf(filepath: str, force_type: Optional[str] = None) -> AbstractGraph:
    """
    Carrega um arquivo .gexf e retorna um grafo (AbstractGraph).

    Parâmetros:
        filepath: caminho para o arquivo .gexf.
        force_type: se fornecido, pode ser 'list' (AdjacencyListGraph) ou
                    'undirected' (UndirectedGraph). Caso contrário, o tipo
                    é inferido a partir do atributo defaultedgetype do GEXF.

    Retorna:
        Uma instância de AbstractGraph (AdjacencyListGraph ou UndirectedGraph).
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Detecta namespace
    ns_uri = None
    for possible in ('http://gexf.net/1.3', 'http://gexf.net/1.2'):
        if root.find(f'{{{possible}}}graph') is not None:
            ns_uri = possible
            break
    if ns_uri is None:
        ns_uri = ''

    ns = {'gexf': ns_uri} if ns_uri else {}
    tag = lambda t: f'gexf:{t}' if ns_uri else t

    # Obtém o elemento graph
    graph_elem = root.find(f'.//{tag("graph")}', ns) if ns else root.find('.//graph')
    default_edge_type = graph_elem.get('defaultedgetype', 'directed') if graph_elem is not None else 'directed'

    # Determina o tipo de grafo
    if force_type == 'undirected' or (force_type is None and default_edge_type.lower() == 'undirected'):
        graph_class = UndirectedGraph
    else:
        graph_class = AdjacencyListGraph  # padrão direcionado

    nodes = root.findall(f'.//{tag("node")}', ns) if ns else root.findall('.//node')
    edges = root.findall(f'.//{tag("edge")}', ns) if ns else root.findall('.//edge')

    gexf_id_to_idx = {node.get('id'): idx for idx, node in enumerate(nodes)}

    G = graph_class(len(nodes))

    for idx, node in enumerate(nodes):
        label = node.get('label', node.get('id', str(idx)))
        G.vertex_labels[idx] = label

    # Adiciona arestas
    for edge in edges:
        src_raw = edge.get('source')
        tgt_raw = edge.get('target')
        src = gexf_id_to_idx.get(src_raw)
        tgt = gexf_id_to_idx.get(tgt_raw)
        if src is not None and tgt is not None and src != tgt:
            G.add_edge(src, tgt)
            weight = edge.get('weight')
            if weight is not None:
                try:
                    G.set_edge_weight(src, tgt, float(weight))
                except Exception:
                    pass

    return G
