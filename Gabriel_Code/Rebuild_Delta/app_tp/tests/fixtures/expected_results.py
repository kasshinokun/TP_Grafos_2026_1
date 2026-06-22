"""Resultados analíticos conhecidos para validação."""
import math

def complete_graph_expected(n: int) -> dict:
    return {
        'edge_count': n * (n - 1),
        'density': 1.0,
        'diameter': 1 if n > 1 else 0,
        'avg_path': 1.0 if n > 1 else 0.0,
        'avg_clustering': 1.0 if n >= 3 else 0.0,
        'degree_in': n - 1,
        'degree_out': n - 1,
    }

def star_graph_expected(n: int) -> dict:
    # Centro (0): in=n-1, out=n-1. Folhas: in=1, out=1.
    return {
        'edge_count': 2 * (n - 1),
        'center_in_degree': n - 1,
        'center_out_degree': n - 1,
        'leaf_in_degree': 1,
        'leaf_out_degree': 1,
        'diameter': 2 if n > 2 else 1,
    }

def cycle_graph_expected(n: int) -> dict:
    return {
        'edge_count': n,
        'diameter': n // 2,
        'avg_path': (n // 2) if n % 2 == 1 else ((n // 2 - 1) * (n // 2) + n // 2) / (n - 1),
        'avg_clustering': 0.0 if n >= 4 else 1.0,
    }

def two_cliques_expected(clique_size: int) -> dict:
    # O nó ponte (0) deve ter betweenness máxima
    return {
        'num_communities': 2,
        'bridge_node': 0,
        'bridge_betweenness_rank': 1,  # Deve ser o top 1
    }

def path_graph_expected(n: int) -> dict:
    return {
        'edge_count': 2 * (n - 1),
        'diameter': n - 1,
    }