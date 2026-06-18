"""
Camada PureNetworkX integrada ao projeto de TCC.

Este pacote conecta a biblioteca Python-puro `pure_networkx` (estilo NetworkX)
à hierarquia `AbstractGraph` / `AdjacencyListGraph` / `AdjacencyMatrixGraph`
já existente em `grafo.graph`, sem exigir nenhuma reescrita do núcleo do TCC.

Exporta:
    - PureNetworkX        : fachada com algoritmos das 11 categorias
    - GraphAdapter        : adaptador camelCase sobre AbstractGraph
    - read_gexf / write_gexf : I/O de arquivos .gexf
    - run_category_demo   : roda uma demo por categoria
    - CATEGORY_NAMES      : nomes das 11 categorias
"""
from .adapter import GraphAdapter, wrap
from .gexf_io import read_gexf, write_gexf
from .pure_networkx import PureNetworkX
from .categories_demo import run_category_demo, CATEGORY_NAMES

__all__ = [
    "GraphAdapter", "wrap",
    "read_gexf", "write_gexf",
    "PureNetworkX",
    "run_category_demo", "CATEGORY_NAMES",
]
